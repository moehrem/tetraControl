"""Handle communication with Motorola devices."""

import logging
import re

from typing import List, Tuple, Dict, Any

_LOGGER = logging.getLogger(__name__)


class Motorola:
    """Class to handle Motorola communication."""

    def __init__(self, coordinator) -> None:
        """Initialize the Motorola communication handler."""
        self.coordinator = coordinator
        self.messages = {}
        self.variables = {
            "issi_sen": "",
            "issi_rec": "",
            "Tetra_Status": 0,
            "Latitude": 0,
            "Longitude": 0,
            "Velocity": 0,
            "Direction": "",
            "PositionError": "",
        }

        self.sds = {
            "SDS_Message": "",
            "SDS_Command": "",
            "SDS_Type": 0,
            # "SDS_Header": "",
            "SDS_Content": "",
            # "SDS_InternalNumber": "",
            # "SDS_MessageID": "",
            # "SDS_MessageParts": "",
            # "SDS_MessagePartID": "",
        }

    def parser(self, raw_data) -> tuple[dict[str, str], bytes]:
        """Parse the raw data from Motorola devices.

        Receives raw_data as bytes, decodes and processes it to extract relevant information.
        """

        _complete_messages = []
        _raw_messages = []
        _incomplete_messages = b""
        _single_line_messages = ["+ENCR", "+GMM", "+GMI", "+GMR"]
        self.messages = {}

        try:
            decoded_data = raw_data.decode("utf-8", errors="ignore")
        except UnicodeDecodeError as e:
            _LOGGER.error("Failed to decode raw data: %s", e)
            return self.messages, raw_data

        # Split and strip lines
        lines = [line.strip() for line in decoded_data.split("\r\n") if line.strip()]

        # Split, strip and remove empty lines
        lines = [line for line in lines if line != "OK"]

        for line in lines:
            if line.startswith("+"):
                # new message
                _raw_messages.append(line)
            elif _raw_messages:
                # add to message line before, if any
                _raw_messages[-1] += "\r\n" + line
            else:
                # if no message line yet, consider it an incomplete message
                _incomplete_messages += line.encode("utf-8") + b"\r\n"
                _LOGGER.debug("Message received before any message start: %s", line)

        # check and handle incomplete messages
        for msg in _raw_messages:
            message_segments = msg.split("\r\n", 1)
            if len(message_segments) == 1 and not any(
                message_segments[0].startswith(cmd) for cmd in _single_line_messages
            ):
                _LOGGER.debug("Incomplete message found: %s", msg)
                _incomplete_messages += msg.encode("utf-8") + b"\r\n"
            else:
                _complete_messages.append(msg)

        # handle complete messages
        for msg in _complete_messages:
            self._init_sds_data(msg)
            self._process_sds_data()

        return self.messages, _incomplete_messages

    def _init_sds_data(self, message):
        # Reset
        for key in self.sds:
            self.sds[key] = ""

        for key in self.variables:
            self.variables[key] = ""

        # init sds-message
        self.sds["SDS_Message"] = message.strip(
            "\r\n"
        )  # delete "\r\n" at start and end
        self.sds["SDS_Message"] = self.sds[
            "SDS_Message"
        ].strip()  # delete spaces at start and end
        self.sds["SDS_Message"] = self.sds["SDS_Message"].replace(
            "\r\n", ","
        )  # replace "\r\n" within the string with ","
        self.sds["SDS_Message"] = self.sds["SDS_Message"].replace(
            " ,", ","
        )  # delete additional spaces
        self.sds["SDS_Message"] = self.sds["SDS_Message"].replace(
            ",,", ","
        )  # delete additional commas
        self.sds["SDS_Message"] = self.sds["SDS_Message"].strip(
            ","
        )  # delete commata at start and end
        self.sds["SDS_Message"] = self.sds["SDS_Message"].split(",")  # split at comma

        # sometimes sender issi is split by comma - if so merge it again
        if len(self.sds["SDS_Message"]) > 7:
            try:
                self.sds["SDS_Message"][1] += self.sds["SDS_Message"][2]
                del self.sds["SDS_Message"][2]
            except IndexError:
                _LOGGER.warning(
                    "Unexpected SDS message format: %s", self.sds["SDS_Message"]
                )

        # set
        try:
            if match := re.search(r"(\+.*?)(?=[:])", self.sds["SDS_Message"][0]):
                self.sds["SDS_Command"] = match.group(1)
            else:
                self.sds["SDS_Command"] = ""

            match self.sds["SDS_Command"]:
                case "+CTSDSR":
                    try:
                        self.sds["SDS_Type"] = self.sds["SDS_Message"][6][0:2]
                        self.sds["SDS_Content"] = self.sds["SDS_Message"][6]
                        self.variables["issi_sen"] = self.sds["SDS_Message"][1]
                        self.variables["issi_rec"] = self.sds["SDS_Message"][3]
                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected CTSDSR SDS format: %s", self.sds["SDS_Message"]
                        )
                        return

                    # convert SDS_Type to decimal
                    self.sds["SDS_Type"] = int(self.sds["SDS_Type"], 16)

                case "+GMM":
                    self.sds["SDS_Content"] = (
                        self.sds["SDS_Message"][1] + ", " + self.sds["SDS_Message"][2]
                    )

                case "+GMI":
                    self.sds["SDS_Content"] = (
                        self.sds["SDS_Message"][0].split(":", 1)[1].strip()
                    )

                case "+GMR":
                    self.sds["SDS_Content"] = (
                        self.sds["SDS_Message"][0].split(":", 1)[1].strip()
                    )

                case "+CMEE":
                    # +CMEE=<extended error report>
                    pass

                case "+CME ERROR":
                    # +CME ERROR: <extended error report code>
                    pass

                case _:
                    self.sds["SDS_Content"] = ", ".join(self.sds["SDS_Message"])

        except Exception as e:
            _LOGGER.error("Error processing SDS command: %s", e)
            self.sds["SDS_Command"] = ""
            self.sds["SDS_Content"] = ", ".join(self.sds["SDS_Message"])

    def _process_sds_data(self):
        """Handle SDS data."""
        if self.sds["SDS_Command"] == "+CTSDSR":
            # check for sds status and process data
            match self.sds["SDS_Type"]:
                # SDS short location report / location information protocol "10"
                case 10:
                    _LOGGER.debug("Starting short location report message handling")
                    self.handle_tetra_10()

                # SDS status message "128"
                case 128:
                    _LOGGER.debug("Starting status message handling")
                    self.handle_tetra_128()

                # SDS long location report / location information protocol "130"
                case 130:
                    _LOGGER.debug(
                        "Received long location report message - handling not yet implemented"
                    )

                # SDS position request reply "131"
                case 131:
                    _LOGGER.debug(
                        "Received position request reply message - handling not yet implemented"
                    )

                # SDS text message "137"
                case 137:
                    _LOGGER.debug(
                        "Received text message - handling not yet implemented"
                    )

                # SDS segmented message "138"
                case 138:
                    _LOGGER.debug(
                        "Received segmented message - handling not yet implemented"
                    )

                # all other/unknown message types
                case _:
                    _LOGGER.warning(
                        "Received unknown message type %s, abort message handling for message: %s",
                        self.sds["SDS_Type"],
                        self.sds["SDS_Content"],
                    )

        # command generic MT control: +GMM, +GMR, +GMI
        elif (
            self.sds["SDS_Command"] == "+GMR"
            or self.sds["SDS_Command"] == "+GMI"
            or self.sds["SDS_Command"] == "+GMM"
        ):
            _message = {
                "sds_command": self.sds["SDS_Command"],
                "sds_command_desc": self.get_sds_command_description(
                    self.sds["SDS_Command"]
                ),
                "content": self.sds["SDS_Content"],
            }

            self.messages[str(self.sds["SDS_Command"])] = _message

        # comamnd generic MT error: +CME ERROR, +CMEE
        elif (
            self.sds["SDS_Command"] == "+CMEE"
            or self.sds["SDS_Command"] == "+CME ERROR"
        ):
            error_code = re.sub(r"\D", "", ", ".join(self.sds["SDS_Message"]))
            error_message = self.get_cme_error_message(error_code)

            _message = {
                "sds_command": self.sds["SDS_Command"],
                "sds_command_desc": self.get_sds_command_description(
                    self.sds["SDS_Command"]
                ),
                "error_code": error_code,
                "error_message": error_message,
            }

            self.messages[str(self.sds["SDS_Command"])] = _message

        else:
            _LOGGER.debug(
                "Received unkown SDS-command %s, abort message handling",
                self.sds["SDS_Command"],
            )

    def get_cme_error_message(self, error_code):
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

    # handle SDS short location report / location information protocol "10"
    def handle_tetra_10(self):
        """Handle SDS short location report / location information protocol "10"."""
        # convert hex to bin
        bin_string = self.sds["SDS_Content"][2:]
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

        # mapping
        time_elapsed_mapping = {
            0: "<5s",
            1: "<5min",
            2: "<30min",
            3: "unknown or not applicable",
        }

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

        type_add_data_mapping = {0: "Reason for sending", 1: "User defined data"}

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

        # conversion and calculating
        pdu_type = int(pdu_type_bin, 2)
        time_elapsed = time_elapsed_mapping.get(int(time_elapsed_bin, 2), "Unknown")

        # Longitude
        lng = int(lng_bin, 2)
        if lng >= 2**24:
            lng -= 2**25
        longitude = lng * (360 / 2**25)

        # Latitude
        lat = int(lat_bin, 2)
        if lat >= 2**23:
            lat -= 2**24
        latitude = lat * (180 / 2**24)

        # Position Error
        position_error = position_error_mapping.get(position_error_bin, "Unknown")

        # Horizontal Velocity
        horizontal_velocity = int(horizontal_velocity_bin, 2)
        if horizontal_velocity < 28:
            velocity = horizontal_velocity
        elif 28 <= horizontal_velocity < 127:
            velocity = round(16 * (1 + 0.038) ** (horizontal_velocity - 13))
        else:
            velocity = "unknown"

        # Travel Direction
        travel_direction = direction_mapping.get(travel_direction_bin, "Unknown")

        # Type of Additional Data
        type_add_data = int(type_add_data_bin, 2)
        type_add_data_desc = type_add_data_mapping.get(type_add_data, "Unknown")

        # Reason for Sending
        reason_sending = int(reason_sending_bin, 2)
        reason_sending_desc = reason_for_sending_mapping.get(reason_sending, "Unknown")

        # User Defined Data
        user_def_data = int(user_def_data_bin, 2)

        # Speichern der Ergebnisse in self.variables
        self.variables["Latitude"] = latitude
        self.variables["Longitude"] = longitude
        self.variables["Velocity"] = velocity
        self.variables["Direction"] = travel_direction
        self.variables["PositionError"] = position_error

        # build message for HomeAssistant Sensor
        _message = {
            "sds_command": self.sds["SDS_Command"],
            "sds_command_desc": self.get_sds_command_description(
                self.sds["SDS_Command"]
            ),
            "sds_type": self.sds["SDS_Type"],
            "sds_type_desc": self.get_sds_type_description(self.sds["SDS_Type"]),
            "issi_sender": self.variables["issi_sen"],
            "lat": self.variables["Latitude"],
            "lng": self.variables["Longitude"],
            "velocity": self.variables["Velocity"],
            "direction": self.variables["Direction"],
            "position_error": self.variables["PositionError"],
        }

        self.messages[
            str(self.sds["SDS_Command"])
            + "_"
            + str(self.sds["SDS_Type"])
            + "_"
            + str(self.variables["issi_sen"])
        ] = _message

    # handle SDS status message "128"
    def handle_tetra_128(self):
        """Handle SDS status message "128"."""

        # mapping
        status_map = {
            "8002": "0",
            "8003": "1",
            "8004": "2",
            "8005": "3",
            "8006": "4",
            "8007": "5",
            "8008": "6",
            "8009": "7",
            "800A": "8",
            "800B": "9",
            "80F7": "",
            "80F4": "",
        }

        self.variables["Tetra_Status"] = status_map.get(self.sds["SDS_Content"])

        # build message for HomeAssistant Sensor
        _message = {
            "sds_command": self.sds["SDS_Command"],
            "sds_command_desc": self.get_sds_command_description(
                self.sds["SDS_Command"]
            ),
            "sds_type": self.sds["SDS_Type"],
            "sds_type_desc": self.get_sds_type_description(self.sds["SDS_Type"]),
            "issi": self.variables["issi_sen"],
            "status": self.variables["Tetra_Status"],
        }

        self.messages[
            str(self.sds["SDS_Command"])
            + "_"
            + str(self.sds["SDS_Type"])
            + "_"
            + str(self.variables["issi_sen"])
        ] = _message

    def get_sds_type_description(self, sds_type: int) -> str:
        """Get the description of the SDS type."""
        type_mapping = {
            10: "Short Location Report",
            128: "Status Report",
            130: "Long Location Report",
            131: "Position Request Reply",
            137: "Text Message",
            138: "Segmented Message",
        }
        return type_mapping.get(sds_type, "Unknown SDS Type")

    def get_sds_command_description(self, sds_command: str) -> str:
        """Get the description of the SDS command."""
        command_mapping = {
            "+CTSDSR": "CTS Data Service Report",
            "+GMM": "Model Information",
            "+GMI": "Manufacturer Information",
            "+GMR": "Revision Information",
            "+CMEE": "Extended Error Report",
            "+CME ERROR": "CME Error Report",
        }
        return command_mapping.get(sds_command, "Unknown Command")
