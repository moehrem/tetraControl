"""Handle communication with Motorola devices."""

import logging
import re

_LOGGER = logging.getLogger(__name__)

_SDS_VARIABLES_DEFAULTS = {
    # +CTSDSR
    "sds_command": "",
    "sds_command_desc": "",
    "sds_type": 0,
    "sds_type_desc": "",
    "sds_lenght_bits": 0,
    "sds_content": "",
    "ai_service": 0,
    "issi_sen": 0,
    "issi_sen_type": 0,
    "issi_rec": 0,
    "issi_rec_type": 0,
    "lat": 0.0,
    "lng": 0.0,
    "velocity": 0,
    "direction": "",
    "position_error": "",
    "tetra_status": 0,
    "time_elapsed": "",
    "pdu_type": 0,
    "type_additional_data_desc": "",
    "reason_sending_desc": "",
    "user_def_data": 0,
    # +GMM
    "device_status": "",
    "device_id": "",
    "sw_version": 0,
    # +GMR
    "revision": "",
    # +GMI
    "manufacturer": "",
    # +CMEE & +CME ERROR
    "cme_error": 0,
    "cme_error_message": "",
    # unknown commands
    "unknown_command_message": "",
}


class Motorola:
    """Class to handle Motorola communication."""

    def __init__(self, coordinator) -> None:
        """Initialize the Motorola communication handler."""
        self.coordinator = coordinator
        self.sds_messages: dict = {}
        self.raw_returns: bytes = b""
        self._decoded_data: str = ""
        self._complete_messages: list[str] = []
        self._incomplete_messages: list[str] = []
        self._buffer: list[str] = []
        self._sds_variables: dict = _SDS_VARIABLES_DEFAULTS.copy()

    def data_handler(self, raw_data) -> tuple[dict[str, str], bytes]:
        """Parse the raw data from Motorola devices.

        Receives raw_data as bytes, decodes and processes it to extract relevant information.
        """

        # initialize variables to avoid multiplication of data
        self.sds_messages = {}
        self.raw_returns = b""
        self._decoded_data = ""
        self._complete_messages = []
        self._incomplete_messages = []

        # decode raw data
        try:
            self._decoded_data = raw_data.decode("utf-8", errors="ignore")
            _LOGGER.debug("Decoded raw data: %s", self._decoded_data)
        except UnicodeDecodeError as e:
            _LOGGER.error("Failed to decode raw data: %s, thus ignoring data", e)
            return self.sds_messages, self.raw_returns

        # parse decoded data
        if self._decoded_data:
            _LOGGER.debug("##### Start parsing decoded data #####")
            try:
                self._parse_decoded_data()
                self._organize_messages()
                self._check_user_data_length()
                _LOGGER.debug("##### End parsing decoded data #####")
            except (
                AttributeError,
                TypeError,
                IndexError,
                UnicodeEncodeError,
                re.error,
            ) as err:
                _LOGGER.error("Error parsing decoded data: %s", err)
                _LOGGER.debug("##### Aborted parsing and data handling #####")
                return (
                    self.sds_messages,
                    self.raw_returns,
                )  # return as without data further handling is not possible

        # handle complete messages
        if self._complete_messages:
            _LOGGER.debug("##### Start processing complete messages #####")
            for msg in self._complete_messages:
                try:
                    self._process_sds_commands(msg)
                    self._process_sds_types()
                    self._create_message()
                    _LOGGER.debug("##### End processing complete messages #####")

                except (AttributeError, TypeError, IndexError) as err:
                    _LOGGER.error("Error processing complete messages: %s", err)

        # handle incomplete messages
        if self._incomplete_messages:
            _LOGGER.debug("##### Start processing incomplete messages #####")
            for msg in self._incomplete_messages:
                try:
                    self.raw_returns += msg.encode("utf-8") + b"\r\n"
                    _LOGGER.debug("Added incomplete message to raw returns: %s", msg)
                    _LOGGER.debug("##### End processing incomplete messages #####")

                except (AttributeError, TypeError, IndexError) as err:
                    _LOGGER.error("Error processing incomplete messages: %s", err)

        return self.sds_messages, self.raw_returns

    def _parse_decoded_data(self):
        """Parse the decoded data into complete and incomplete messages."""

        # reinit buffer to avoid multiplcation of data
        self._buffer = []

        # split decoded data into lines
        self._buffer = [
            line.strip() for line in self._decoded_data.split("\r\n") if line.strip()
        ]

        # clean up messages
        for i, line in enumerate(self._buffer):
            line = line.strip()
            line = line.replace("\r", "").replace("\n", "")
            line = line.replace(" ", ",")
            line = line.replace(":", "")
            line = re.sub(r",+", ",", line)
            self._buffer[i] = line

        # remove empty lines and 'OK' messages
        self._buffer = [line for line in self._buffer if line and line != "OK"]

    def _organize_messages(self):
        if self._buffer:
            i = 0
            while i < len(self._buffer):
                try:
                    line = self._buffer[i]
                    # special case: first line without message header
                    if i == 0 and not line.startswith("+"):
                        self._incomplete_messages.append(line)
                        _LOGGER.debug(
                            "Received first line without message header: %s, treating as incomplete message",
                            line,
                        )
                        i += 1

                    # new message - check if single or multiline message
                    elif line.startswith("+"):
                        # if the next line does not start with a '+', this is a multi-line message -> concatenate both lines and add to complete messages
                        if i + 1 < len(self._buffer) and not self._buffer[
                            i + 1
                        ].startswith("+"):
                            line = line + "," + self._buffer[i + 1]
                            self._complete_messages.append(line)
                            i += 2
                            _LOGGER.debug("Received multi-line message: %s", line)

                        # if the next line does start with a '+', this is a single-line message -> add to complete messages
                        else:
                            self._complete_messages.append(line)
                            i += 1
                            _LOGGER.debug("Received single line message: %s", line)

                    # incomplete message
                    else:
                        self._incomplete_messages.append(line)
                        i += 1
                        _LOGGER.debug(
                            "Received user data without message header: %s, treating as incomplete message",
                            line,
                        )
                except IndexError as err:
                    _LOGGER.error(
                        "Error while separating messages: %s, error: %s",
                        self._buffer,
                        err,
                    )

    def _check_user_data_length(self):
        """Check the user data length in complete messages."""
        for message in self._complete_messages:
            if message.startswith("+CTSDSR"):
                try:
                    parts = message.split(",")
                    hex_length = len(parts[7])
                    bit_length = hex_length * 4
                    expected_bit_length = int(parts[6])

                except (IndexError, ValueError) as err:
                    _LOGGER.error(
                        "Error checking user data length in message: %s, error: %s",
                        message,
                        err,
                    )
                    self._complete_messages.remove(message)
                    continue

                if bit_length != expected_bit_length:
                    _LOGGER.warning(
                        "Unexpected SDS content length: %s bits, expected length is %s bits, thus ignoring message",
                        bit_length,
                        expected_bit_length,
                    )
                    self._complete_messages.remove(message)
                    continue

                if bit_length % 8 != 0:
                    _LOGGER.warning(
                        "SDS content bit length (%s) is not a multiple of 8 (i.e. not byte-aligned), thus ignoring message",
                        bit_length,
                    )
                    self._complete_messages.remove(message)

    def _process_sds_commands(self, raw_message):
        """Initialize SDS variables from the raw message."""

        # reinit SDS variables to avoid data confusion
        for key, default in _SDS_VARIABLES_DEFAULTS.items():
            self._sds_variables[key] = default

        # split message
        message = raw_message.split(",")

        try:
            self._sds_variables["sds_command"] = message[0]
            self._sds_variables["sds_command_desc"] = str(
                self.get_sds_command_description(self._sds_variables["sds_command"])
            )

            match self._sds_variables["sds_command"]:
                # +CTSDSR: short data service command
                case "+CTSDSR":
                    try:
                        self._sds_variables["ai_service"] = int(message[1])
                        self._sds_variables["issi_sen"] = int(message[2])
                        self._sds_variables["issi_sen_type"] = int(message[3])
                        self._sds_variables["issi_rec"] = int(message[4])
                        self._sds_variables["issi_rec_type"] = int(message[5])
                        self._sds_variables["sds_lenght_bits"] = int(message[6])
                        self._sds_variables["sds_type"] = int(message[7][0:2], 16)
                        self._sds_variables["sds_content"] = str(message[7])

                        self._sds_variables["sds_type_desc"] = str(
                            self.get_sds_type_description(
                                self._sds_variables["sds_type"]
                            )
                        )

                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected CTSDSR SDS format: %s",
                            message,
                        )

                # generic MT protocol: model identification
                case "+GMM":
                    try:
                        self._sds_variables["device_status"] = str(message[1])
                        self._sds_variables["device_id"] = str(message[2])
                        self._sds_variables["sw_version"] = str(message[3])
                        self._sds_variables["device_status"] = str(
                            self.get_motorola_device_status(
                                self._sds_variables["device_status"]
                            )
                        )
                        _LOGGER.debug("Received generic MT control command: +GMM")

                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected GMM SDS format: %s",
                            message,
                        )

                # generic MT protocol: manufacturer identification
                case "+GMI":
                    try:
                        self._sds_variables["manufacturer"] = str(message[1])
                        _LOGGER.debug("Received generic MT control command: +GMI")
                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected GMI SDS format: %s",
                            message,
                        )

                # generic MT protocol: revision identification
                case "+GMR":
                    try:
                        self._sds_variables["revision"] = str(message[1])
                        _LOGGER.debug("Received generic MT control command: +GMR")
                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected GMR SDS format: %s",
                            message,
                        )
                # +CMEE: <extended error report> or +CME ERROR: <extended error report code>
                case "+CMEE" | "+CME ERROR":
                    try:
                        self._sds_variables["cme_error"] = int(message[1])
                        self._sds_variables["error_message"] = str(
                            self.get_cme_error_message(self._sds_variables["cme_error"])
                        )
                        _LOGGER.debug(
                            "Received generic MT error command: %s",
                            self._sds_variables["sds_command"],
                        )
                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected CMEE SDS format: %s",
                            message,
                        )

                # all other SDS commands
                case _:
                    self._sds_variables["unknown_command_message"] = raw_message
                    _LOGGER.warning(
                        "Received SDS command: %s, message %s. No handling implemented yet, please report this to the developer via https://github.com/moehrem/tetraControl/issues",
                        self._sds_variables["sds_command"],
                        message,
                    )

        except AttributeError as err:
            _LOGGER.error(
                "Error initializing SDS data from message: %s, error: %s",
                message,
                err,
            )

    def _process_sds_types(self):
        """Create messages based on the SDS command and type."""
        if self._sds_variables["sds_command"] == "+CTSDSR":
            # check for sds status and process data
            match self._sds_variables["sds_type"]:
                # SDS short location report / location information protocol, sds type 10
                case 10:
                    _LOGGER.debug("Starting short location report message handling")
                    self._handle_sds_type_10()

                # SDS status message, sds type 128
                case 128:
                    _LOGGER.debug("Starting status message handling")
                    self._sds_variables["tetra_status"] = (
                        int(self._sds_variables["sds_content"][2:4], 16) - 2
                    )

                # SDS long location report / location information protocol, sds type 130
                case 130:
                    _LOGGER.debug(
                        "Received long location report message - handling not yet implemented"
                    )

                # SDS position request reply, sds type 131
                case 131:
                    _LOGGER.debug(
                        "Received position request reply message - handling not yet implemented"
                    )

                # SDS text message, sds type 137
                case 137:
                    _LOGGER.debug(
                        "Received text message - handling not yet implemented"
                    )

                # SDS segmented message, sds type 138
                case 138:
                    _LOGGER.debug(
                        "Received segmented message - handling not yet implemented"
                    )

                # all other/unknown message types
                case _:
                    _LOGGER.warning(
                        "Received unknown message type %s, abort message handling for message: %s",
                        self._sds_variables["ai_service"],
                        self._sds_variables["sds_content"],
                    )

    def _handle_sds_type_10(self) -> None:
        """Handle SDS short location report / location information protocol "10"."""
        # convert hex to bin
        bin_string = self._sds_variables["sds_content"][2:]
        bin_string = bin(int(bin_string, 16))[2:].zfill(4 * len(bin_string))

        # exctract data
        pdu_type_bin = bin_string[0:2]  # PDU-Type: 2 Bits
        time_elapsed_bin = bin_string[2:4]  # Time Elapsed: 2 Bits
        lng_bin = bin_string[4:29]  # Longitude: 25 Bits
        lat_bin = bin_string[29:53]  # Latitude: 24 Bits
        position_error_bin = bin_string[53:56]  # Position Error: 3 Bits
        horizontal_velocity_bin = bin_string[56:63]  # Horizontal Velocity: 7 Bits
        travel_direction_bin = bin_string[63:67]  # Direction of Travel: 4 Bits
        type_add_data_bin = bin_string[67:68]  # Type of Additional Data: 1 Bit
        reason_sending_bin = bin_string[68:76]  # Reason for Sending: 8 Bits
        user_def_data_bin = bin_string[76:84]  # User Defined Data: 8 Bits

        # conversion and calculating
        self._sds_variables["pdu_type"] = int(pdu_type_bin, 2)
        self._sds_variables["time_elapsed"] = self.get_time_elapsed_mapping(
            int(time_elapsed_bin, 2)
        )

        # Longitude
        lng = int(lng_bin, 2)
        if lng >= 2**24:
            lng -= 2**25
        self._sds_variables["lng"] = float(lng * (360 / 2**25))

        # Latitude
        lat = int(lat_bin, 2)
        if lat >= 2**23:
            lat -= 2**24
        self._sds_variables["lat"] = float(lat * (180 / 2**24))

        # Position Error
        self._sds_variables["position_error"] = str(
            self.get_position_error_mapping(position_error_bin)
        )

        # Horizontal Velocity
        horizontal_velocity = int(horizontal_velocity_bin, 2)
        if horizontal_velocity < 28:
            self._sds_variables["velocity"] = int(horizontal_velocity)
        elif 28 <= horizontal_velocity < 127:
            self._sds_variables["velocity"] = int(
                round(16 * (1 + 0.038) ** (horizontal_velocity - 13))
            )
        else:
            self._sds_variables["velocity"] = "unknown"

        # Travel Direction
        self._sds_variables["direction"] = str(
            self.get_direction_mapping(travel_direction_bin)
        )

        # Type of Additional Data
        type_additional_data = int(type_add_data_bin, 2)
        self._sds_variables["type_additional_data_desc"] = str(
            self.get_sds_type_add_data_mapping(type_additional_data)
        )

        # Reason for Sending
        reason_sending = int(reason_sending_bin, 2)
        self._sds_variables["reason_sending_desc"] = str(
            self.get_reason_for_sending_mapping(reason_sending)
        )

        # User Defined Data
        self._sds_variables["user_def_data"] = int(user_def_data_bin, 2)

    def _create_message(self) -> None:
        """Create a message based on the current SDS variables."""

        # init sds_content as its working data only
        self._sds_variables["sds_content"] = None

        try:
            message = {
                k: v
                for k, v in self._sds_variables.items()
                if k != "sds_command" and v not in ("", 0, None)
            }
            if "sds_type" in message:
                self.sds_messages[
                    f"{self._sds_variables['sds_command']}_{self._sds_variables['sds_type']}_{self._sds_variables['issi_sen']}"
                ] = message
            else:
                self.sds_messages[self._sds_variables["sds_command"]] = message

            _LOGGER.debug(
                "Created message for SDS command %s: %s",
                self._sds_variables["sds_command"],
                message,
            )
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.error(
                "Error creating message for SDS command %s: %s",
                self._sds_variables["sds_command"],
                err,
            )
            return

    def get_time_elapsed_mapping(self, time_elapsed) -> str:
        """Get the mapping for time elapsed."""
        time_elapsed_mapping = {
            0: "<5s",
            1: "<5min",
            2: "<30min",
            3: "unknown or not applicable",
        }
        return time_elapsed_mapping.get(time_elapsed, "unknown")

    def get_position_error_mapping(self, position_error: str) -> str:
        """Get position error based on binary data."""
        position_error_mapping = {
            "000": "<2m",
            "001": "<20m",
            "010": "<200m",
            "011": "<2km",
            "100": "<20km",
            "101": "<=200km",
            "110": ">200km",
            "111": "error or unknown",
        }
        return position_error_mapping.get(position_error, "error or unknown")

    def get_direction_mapping(self, direction) -> str:
        """Get travel direction value based on binary-data."""
        direction_mapping = {
            "0000": "N",
            "0001": "NNE",
            "0010": "NE",
            "0011": "ENE",
            "0100": "E",
            "0101": "ESE",
            "0110": "SE",
            "0111": "SSE",
            "1000": "S",
            "1001": "SSW",
            "1010": "SW",
            "1011": "WSW",
            "1100": "W",
            "1101": "WNW",
            "1110": "NW",
            "1111": "NNW",
        }
        return direction_mapping.get(direction, "Unknown")

    def get_sds_type_add_data_mapping(self, type_add_data) -> str:
        """Get the mapping for SDS type and additional data."""
        type_add_data_mapping = {0: "Reason for sending", 1: "User defined data"}
        return type_add_data_mapping.get(type_add_data, "Unknown")

    def get_reason_for_sending_mapping(self, reason_sending: int) -> str:
        """Get the reason for sending based on the reason_sending value."""
        reason_for_sending_mapping = {
            0: "Subscriber unit is powered ON",
            1: "Subscriber unit is powered OFF",
            2: "Emergency condition is detected",
            3: "Push-to-talk condition is detected",
            4: "Status",
            5: "Transmit inhibit mode ON",
            6: "Transmit inhibit mode OFF",
            7: "System access (TMO ON)",
            8: "DMO ON",
            9: "Enter service (after being out of service)",
            10: "Service loss",
            11: "Cell reselection or change of serving cell",
            12: "Low battery",
            13: "Subscriber unit is connected to a car kit",
            14: "Subscriber unit is disconnected from a car kit",
            15: "Subscriber unit asks for transfer initialization configuration",
            16: "Arrival at destination",
            17: "Arrival at a defined location",
            18: "Approaching a defined location",
            19: "SDS type-1 entered",
            20: "User application initiated",
            21: "Lost ability to determine location",
            22: "Regained ability to determine location",
            23: "Leaving point",
            24: "Ambience Listening call is detected",
            25: "Start of temporary reporting",
            26: "Return to normal reporting",
            27: "Call setup type 1 detected",
            28: "Call setup type 2 detected",
            29: "Positioning device in MS ON",
            30: "Positioning device in MS OFF",
            32: "Response to an immediate location request",
            129: "Maximum reporting interval exceeded since the last location information report",
            130: "Maximum reporting distance limit travelled since last location information report",
        }
        return reason_for_sending_mapping.get(reason_sending, "Unknown")

    def get_sds_type_description(self, ai_service: int) -> str:
        """Get the description of the SDS type."""
        type_mapping = {
            10: "Short Location Report",
            128: "Status Report",
            130: "Long Location Report",
            131: "Position Request Reply",
            137: "Text Message",
            138: "Segmented Message",
        }
        return type_mapping.get(ai_service, "Unknown SDS Type")

    def get_sds_command_description(self, sds_command: str) -> str:
        """Get the description of the SDS command."""
        command_mapping = {
            "+CTSDSR": "CT Short Data Service",
            "+GMM": "Model Identification",
            "+GMI": "Manufacturer Identification",
            "+GMR": "Revision Identification",
            "+CMEE": "Error Report",
            "+CME ERROR": "Error Report",
        }
        return command_mapping.get(sds_command, "Unknown Command")

    def get_cme_error_message(self, error_code):
        """Get the error message for a given CME error code."""
        error_map = {
            "3": "Operation not allowed",
            "4": "Operation not supported",
            "25": "Invalid characters in text string",
            "33": "Parameter wrong type",
            "34": "Parameter value out of range",
            "35": "Syntax error",
            "44": "Unknown parameter",
        }
        return error_map.get(error_code, "Unknown Errorcode")

    def get_motorola_device_status(self, status_code: str) -> str:
        """Get the Motorola device status based on the status code."""
        status_map = {
            "54000": "Power on, no network",
            "54001": "Scanning / searching for network",
            "54008": "Registered in network",
            "54009": "Registered in TMO, active",
            "54010": "DMO mode",
            "54020": "Network change / cell reselection",
        }
        return status_map.get(status_code, "Unknown Status Code")
