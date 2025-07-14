"""Handle communication with Motorola devices."""

import logging
import re

from .const import MOTOROLA_VARIABLES_DEFAULTS
from .helpers import TetrahaconnectHelpers
from .tetra_mappings import Mappings

_LOGGER = logging.getLogger(__name__)


class Motorola:
    """Class to handle Motorola communication."""

    def __init__(self, coordinator) -> None:
        """Initialize the Motorola communication handler."""
        self.coordinator = coordinator
        self.raw_returns: bytes = b""
        self._decoded_data: str = ""
        self._complete_messages: list[str] = []
        self._incomplete_messages: list[str] = []
        self._invalid_messages: list[str] = []
        self._buffer: list[str] = []
        self._motorola_variables: dict = MOTOROLA_VARIABLES_DEFAULTS.copy()

        self.mappings = Mappings()
        self.helpers = TetrahaconnectHelpers(coordinator)

    def data_handler(self, raw_data) -> bytes:
        """Handle incoming serial data from Motorola devices.

        Steps:
        - decoding
        - parsing into lines while cleaning up
        - organizing messages into complete and incomplete messages
        - checking correct message length to separate invalid messages from complete messages
        - handling complete messages by setting sds_commands, sds_types and creating messages
        - handling incomplete messages by setting sds_commands, sds_types and creating messages
        - handling invalid messages by setting sds_commands, sds_types and creating messages

        """

        # initialize variables to avoid multiplication of data
        # self.sds_messages = []
        self.raw_returns = b""
        self._decoded_data = ""
        self._complete_messages = []
        self._incomplete_messages = []
        self._invalid_messages = []

        # decode raw data
        try:
            self._decoded_data = raw_data.decode("utf-8", errors="ignore")
            _LOGGER.debug("Decoded raw data: %s", self._decoded_data)
        except UnicodeDecodeError as e:
            _LOGGER.error("Failed to decode raw data: %s, thus ignoring data", e)
            return self.raw_returns

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
                return self.raw_returns

        # handle complete messages
        if self._complete_messages:
            _LOGGER.debug("##### Start processing complete messages #####")
            for msg in self._complete_messages:
                try:
                    self._process_sds_command(msg)
                    self._process_sds_type()
                    self.helpers.update_entities(self._motorola_variables)
                    _LOGGER.debug("##### End processing complete messages #####")

                except (AttributeError, TypeError, IndexError) as err:
                    _LOGGER.error("Error processing complete messages: %s", err)
                    continue

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
                    continue

        # handle invalid messages
        if self._invalid_messages:
            _LOGGER.debug("##### Start processing invalid messages #####")
            for msg in self._invalid_messages:
                try:
                    self._process_invalid_message(msg)
                    self.helpers.update_entities(self._motorola_variables)
                    _LOGGER.debug("##### End processing invalid messages #####")

                except (AttributeError, TypeError, IndexError) as err:
                    _LOGGER.error("Error processing invalid messages: %s", err)
                    continue

        return self.raw_returns

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
            line = line.replace(":", ",")
            # line = line.replace(" ", "")
            # line = re.sub(r",+", ",", line)
            line = line.replace(", ", ",")
            self._buffer[i] = line

        # remove empty lines and 'OK' messages
        self._buffer = [line for line in self._buffer if line and line != "OK"]

    def _organize_messages(self):
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
                    # add all following lines that does not start with '+' to the current message
                    combined_line = line
                    j = i + 1
                    while j < len(self._buffer) and not self._buffer[j].startswith("+"):
                        combined_line += "," + self._buffer[j]
                        j += 1
                    self._complete_messages.append(combined_line)
                    _LOGGER.debug("Received multi-line message: %s", combined_line)
                    i = j

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
        """Check the user data length in complete messages.

        Check for user data.
        If expected length differs from actual length, expect invalid message.
        Do not ignore/remove messages!

        """
        for message in self._complete_messages[:]:
            if message.startswith("+CTSDSR"):
                try:
                    parts = message.split(",")
                    hex_length = len(parts[7])
                    bit_length = hex_length * 4
                    expected_bit_length = int(parts[6])

                except (IndexError, ValueError) as err:
                    _LOGGER.error(
                        "Error checking user data length in message: %s, error: %s; expecting invalid message",
                        message,
                        err,
                    )
                    self._invalid_messages.append(message)
                    self._complete_messages.remove(message)
                    continue

                if bit_length != expected_bit_length:
                    _LOGGER.warning(
                        "Unexpected SDS content length: %s bits, expected length is %s bits; expecting invalid message",
                        bit_length,
                        expected_bit_length,
                    )
                    self._invalid_messages.append(message)
                    self._complete_messages.remove(message)
                    continue

                if bit_length % 8 != 0:
                    _LOGGER.warning(
                        "SDS content bit length (%s) is not a multiple of 8 (i.e. not byte-aligned); expecting invalid message",
                        bit_length,
                    )
                    self._invalid_messages.append(message)
                    self._complete_messages.remove(message)

    def _process_sds_command(self, raw_message):
        """Initialize SDS variables from the raw message."""

        # clear SDS variables to avoid data confusion
        for key, default in MOTOROLA_VARIABLES_DEFAULTS.items():
            self._motorola_variables[key] = default

        # split message
        message = raw_message.split(",")

        try:
            self._motorola_variables["sds_command"] = message[0]
            self._motorola_variables["sds_command_desc"] = self.mappings.sds_command(
                self._motorola_variables["sds_command"]
            )

            match self._motorola_variables["sds_command"]:
                # +CTSDSR: short data service command
                case "+CTSDSR":
                    try:
                        self._motorola_variables["ai_service"] = message[1]
                        self._motorola_variables["issi_sen"] = message[2]
                        self._motorola_variables["issi_sen_type"] = message[3]
                        self._motorola_variables["issi_rec"] = message[4]
                        self._motorola_variables["issi_rec_type"] = message[5]
                        self._motorola_variables["sds_lenght_bits"] = message[6]
                        self._motorola_variables["sds_type"] = int(message[7][0:2], 16)
                        self._motorola_variables["sds_content"] = message[7]

                        self._motorola_variables["sds_type_desc"] = (
                            self.mappings.sds_type(self._motorola_variables["sds_type"])
                        )

                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected CTSDSR SDS format: %s",
                            message,
                        )

                # generic MT protocol: model identification
                case "+GMM":
                    try:
                        self._motorola_variables["device_status"] = str(message[1])
                        self._motorola_variables["device_id"] = str(message[2])
                        self._motorola_variables["sw_version"] = str(message[3])
                        self._motorola_variables["device_status"] = str(
                            self.mappings.motorola_status(
                                self._motorola_variables["device_status"]
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
                        self._motorola_variables["manufacturer"] = str(message[1])
                        _LOGGER.debug("Received generic MT control command: +GMI")
                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected GMI SDS format: %s",
                            message,
                        )

                # generic MT protocol: revision identification
                case "+GMR":
                    try:
                        self._motorola_variables["revision"] = str(message[1])
                        _LOGGER.debug("Received generic MT control command: +GMR")
                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected GMR SDS format: %s",
                            message,
                        )
                # +CMEE: <extended error report> or +CME ERROR: <extended error report code>
                case "+CMEE" | "+CME ERROR":
                    try:
                        self._motorola_variables["cme_error_code"] = message[1]
                        self._motorola_variables["cme_error_message"] = (
                            self.mappings.cme_error(
                                self._motorola_variables["cme_error_code"]
                            )
                        )
                        _LOGGER.debug(
                            "Received generic MT error command: %s",
                            self._motorola_variables["sds_command"],
                        )
                    except IndexError:
                        _LOGGER.warning(
                            "Unexpected CMEE SDS format: %s",
                            message,
                        )

                # all other SDS commands
                case _:
                    self._motorola_variables["unknown_command_message"] = raw_message
                    _LOGGER.warning(
                        "Received SDS command: %s, message %s. No handling implemented yet, please report this to the developer via https://github.com/moehrem/tetraHAconnect/issues",
                        self._motorola_variables["sds_command"],
                        message,
                    )

        except AttributeError as err:
            _LOGGER.error(
                "Error initializing SDS data from message: %s, error: %s",
                message,
                err,
            )

    def _process_sds_type(self):
        """Create messages based on the SDS command and type."""
        if self._motorola_variables["sds_command"] == "+CTSDSR":
            # check for sds status and process data
            match self._motorola_variables["sds_type"]:
                # SDS short location report / location information protocol, sds type 10
                case 10:
                    _LOGGER.debug(
                        "Starting short location report message handling for message: %s",
                        self._motorola_variables["sds_content"],
                    )
                    self._handle_sds_type_10()

                # SDS status message, sds type 128
                case 128:
                    _LOGGER.debug(
                        "Starting status message handling for message: %s",
                        self._motorola_variables["sds_content"],
                    )
                    self._motorola_variables["tetra_status"] = (
                        int(self._motorola_variables["sds_content"][2:4], 16) - 2
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
                        "Received unknown sds type %s for command %s, abort message handling for message: %s",
                        self._motorola_variables["ai_service"],
                        self._motorola_variables["sds_command"],
                        self._motorola_variables["sds_content"],
                    )

            # delete sds_content to avoid data confusion
            self._motorola_variables["sds_content"] = ""

    def _process_invalid_message(self, raw_message):
        """Prepare invalid messages for sensor handling."""

        # reset sds_variables to avoid data multiplication
        for key, default in MOTOROLA_VARIABLES_DEFAULTS.items():
            self._motorola_variables[key] = default

        message = raw_message.split(",")

        try:
            self._motorola_variables["sds_command"] = message[0]

            if self._motorola_variables["sds_command"] == "+CTSDSR":
                self._motorola_variables["sds_command_desc"] = (
                    self.mappings.sds_command(self._motorola_variables["sds_command"])
                )
            else:
                self._motorola_variables["sds_command_desc"] = "unknown"

            self._motorola_variables["sds_command"] = "unknown"
            self._motorola_variables["validity"] = "invalid"
            self._motorola_variables["invalid_message"] = message

        except AttributeError:
            _LOGGER.error(
                "Error processing invalid message: %s",
                message,
            )

    def _handle_sds_type_10(self) -> None:
        """Handle SDS short location report / location information protocol '10'."""

        # Convert hex to bin
        try:
            bin_string = self._motorola_variables["sds_content"][2:]
            bin_string = bin(int(bin_string, 16))[2:].zfill(4 * len(bin_string))
        except (ValueError, IndexError) as err:
            _LOGGER.error(
                "Error converting SDS content for short location report: %s, error: %s",
                self._motorola_variables.get("sds_content", ""),
                err,
            )
            self._motorola_variables["lng"] = None
            self._motorola_variables["lat"] = None
            self._motorola_variables["velocity"] = "unknown"
            self._motorola_variables["direction"] = "unknown"
            self._motorola_variables["position_error"] = "unknown"
            self._motorola_variables["reason_sending_desc"] = "unknown"
            self._motorola_variables["user_defined_data"] = None
            return

        # Extract data
        try:
            pdu_type_bin = bin_string[0:2]
            time_elapsed_bin = bin_string[2:4]
            lng_bin = bin_string[4:29]
            lat_bin = bin_string[29:53]
            position_error_bin = bin_string[53:56]
            horizontal_velocity_bin = bin_string[56:63]
            travel_direction_bin = bin_string[63:67]
            type_add_data_bin = bin_string[67:68]
            reason_sending_bin = bin_string[68:76]
            user_def_data_bin = bin_string[76:84]
        except IndexError as err:
            _LOGGER.error(
                "Error extracting data from SDS content: %s, error: %s",
                self._motorola_variables.get("sds_content", ""),
                err,
            )
            self._motorola_variables["lng"] = None
            self._motorola_variables["lat"] = None
            self._motorola_variables["velocity"] = "unknown"
            self._motorola_variables["direction"] = "unknown"
            self._motorola_variables["position_error"] = "unknown"
            self._motorola_variables["reason_sending_desc"] = "unknown"
            self._motorola_variables["user_defined_data"] = None
            return

        # Conversion and calculating (jeweils mit try/except, falls nötig)
        try:
            self._motorola_variables["pdu_type"] = int(pdu_type_bin, 2)
        except ValueError:
            self._motorola_variables["pdu_type"] = None

        try:
            self._motorola_variables["time_elapsed"] = self.mappings.time_elapsed(
                int(time_elapsed_bin, 2)
            )
        except ValueError:
            self._motorola_variables["time_elapsed"] = None

        # Longitude
        try:
            lng = int(lng_bin, 2)
            if lng >= 2**24:
                lng -= 2**25
            self._motorola_variables["lng"] = lng * (360 / 2**25)
        except ValueError:
            self._motorola_variables["lng"] = None

        # Latitude
        try:
            lat = int(lat_bin, 2)
            if lat >= 2**23:
                lat -= 2**24
            self._motorola_variables["lat"] = lat * (180 / 2**24)
        except ValueError:
            self._motorola_variables["lat"] = None

        # Position Error
        try:
            self._motorola_variables["position_error"] = self.mappings.position_error(
                position_error_bin
            )
        except Exception:
            self._motorola_variables["position_error"] = "unknown"

        # Horizontal Velocity
        try:
            horizontal_velocity = int(horizontal_velocity_bin, 2)
            if horizontal_velocity < 28:
                self._motorola_variables["velocity"] = horizontal_velocity
            elif 28 <= horizontal_velocity < 127:
                self._motorola_variables["velocity"] = round(
                    16 * (1 + 0.038) ** (horizontal_velocity - 13)
                )
            else:
                self._motorola_variables["velocity"] = "unknown"
        except ValueError:
            self._motorola_variables["velocity"] = "unknown"

        # Travel Direction
        try:
            self._motorola_variables["direction"] = self.mappings.direction(
                travel_direction_bin
            )
        except Exception:
            self._motorola_variables["direction"] = "unknown"

        # Type of Additional Data
        try:
            type_additional_data = int(type_add_data_bin, 2)
            self._motorola_variables["type_additional_data_desc"] = (
                self.mappings.sds_type_add_data(type_additional_data)
            )
        except ValueError:
            self._motorola_variables["type_additional_data_desc"] = "unknown"

        # Reason for Sending
        try:
            reason_sending = int(reason_sending_bin, 2)
            self._motorola_variables["reason_sending_desc"] = (
                self.mappings.reason_for_sending(reason_sending)
            )
        except ValueError:
            self._motorola_variables["reason_sending_desc"] = "unknown"

        # User Defined Data
        try:
            self._motorola_variables["user_defined_data"] = int(user_def_data_bin, 2)
        except ValueError:
            self._motorola_variables["user_defined_data"] = None
