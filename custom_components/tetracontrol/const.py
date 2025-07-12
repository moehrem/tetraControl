"""Constants for the tetraControl integration."""

# general constants
DOMAIN = "tetracontrol"
VERSION = "0.3"
MANUFACTURERS_LIST = ["Motorola"]
SLEEP_TIME_CONNECTION_CHECK = 10  # Sleep time in seconds between connection checks
MAX_RETRY_ATTEMPTS = 5  # Maximum number of attempts to connect to the device
SLEEP_TIME_RETRY = 5  # Sleep time in seconds between retries

# Motorola specific constants
BAUDRATE = 38400
MOTOROLA_VARIABLES_DEFAULTS = {
    # general
    "sds_command": "",
    "sds_command_desc": "",
    "sds_content": "",
    "validity": "valid",
    "unknown_command_message": "",
    "invalid_message": "",
    # +CTSDSR
    "sds_type": 0,
    "sds_type_desc": "",
    "sds_lenght_bits": 0,
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
    "user_defined_data": 0,
    # +GMM
    "device_status": "",
    "device_id": "",
    "sw_version": 0,
    # +GMR
    "revision": "",
    # +GMI
    "manufacturer": "",
    # +CMEE & +CME ERROR & +CMEERROR
    "cme_error_code": 0,
    "cme_error_message": "",
}
