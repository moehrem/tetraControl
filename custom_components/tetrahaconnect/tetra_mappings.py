"""Contain all mapping methods and mapping data for TETRA message handling in tetraHAconnect integration."""


class Mappings:
    """Class to hold all mappings for TETRA data handling."""

    def time_elapsed(self, time_elapsed) -> str:
        """Get the mapping for time elapsed."""
        time_elapsed_mapping = {
            0: "<5s",
            1: "<5min",
            2: "<30min",
            3: "unknown or not applicable",
        }
        return time_elapsed_mapping.get(time_elapsed, "unknown")

    def position_error(self, error_code: str) -> str:
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
        return position_error_mapping.get(error_code, "unknown")

    def direction(self, direction) -> str:
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
        return direction_mapping.get(direction, "unknown")

    def sds_type_add_data(self, type_add_data) -> str:
        """Get the mapping for SDS type and additional data."""
        type_add_data_mapping = {
            0: "Reason for sending",
            1: "User defined data",
        }
        return type_add_data_mapping.get(type_add_data, "unknown")

    def reason_for_sending(self, reason_sending: int) -> str:
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
        return reason_for_sending_mapping.get(reason_sending, "unknown")

    def sds_type(self, ai_service: int) -> str:
        """Get the description of the SDS type."""
        type_mapping = {
            10: "Short Location Report",
            128: "Status Report",
            130: "Long Location Report",
            131: "Position Request Reply",
            137: "Text Message",
            138: "Segmented Message",
        }
        return type_mapping.get(ai_service, "unknown")

    def sds_command(self, sds_command: str) -> str:
        """Get the description of the SDS command."""
        command_mapping = {
            "+CTSDSR": "CT Short Data Service",
            "+GMM": "Model Identification",
            "+GMI": "Manufacturer Identification",
            "+GMR": "Revision Identification",
            "+CMEE": "Error Report",
            "+CME ERROR": "Error Report",
            "+ENCR": "Encryption Status",
        }
        return command_mapping.get(sds_command, "unknown")

    def cme_error(self, error_code):
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
        return error_map.get(error_code, "unknown")

    def motorola_status(self, status_code: str) -> str:
        """Get the Motorola device status based on the status code."""
        status_map = {
            "54000": "Power on, no network",
            "54001": "Scanning / searching for network",
            "54008": "Registered in network",
            "54009": "Registered in TMO, active",
            "54010": "DMO mode",
            "54020": "Network change / cell reselection",
        }
        return status_map.get(status_code, "unknown")
