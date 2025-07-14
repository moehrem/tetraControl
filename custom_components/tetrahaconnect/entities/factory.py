# """Contain factory function to create sensor instances for TetraHAConnect integration."""

# from .base import TetraBaseSensor
# from .cme import CMESensor
# from .connection import ConnectionStatusSensor
# from .ctsdsr import CTSDRSSensor
# from .gmi import GMISensor
# from .gmm import GMMSensor
# from .gmr import GMRSensor

# # Mapping from TETRA command to sensor class
# # add any new command-sensorclass-combo here
# # sensor_factory will use this mapping to create sensor instances
# # DO NOT remove or change entries "connection_status" and "default"!
# SENSOR_CLASS_MAP = {
#     "+CTSDSR": CTSDRSSensor,
#     "+GMI": GMISensor,
#     "+GMR": GMRSensor,
#     "+GMM": GMMSensor,
#     "+CME ERROR": CMESensor,
#     "+CMEE": CMESensor,
#     "connection_status": ConnectionStatusSensor,
# }


# def sensor_factory(coordinator, key, value) -> TetraBaseSensor:
#     """Return sensor instances based on the key."""
#     try:
#         sensor_cls = SENSOR_CLASS_MAP.get(key, TetraBaseSensor)
#         return sensor_cls(coordinator, key, value)
#     except (KeyError, TypeError, AttributeError):
#         return TetraBaseSensor(coordinator, key, value)
