"""Contain factory function to create sensor instances for TetraControl integration."""

from .base import TetraBaseSensor
from .connection import ConnectionStatusSensor
from .ctsdsr import CTSDRSSensor
from .gm import GMSensor
from .cme import CMESensor


def sensor_factory(coordinator, key, value):
    """Return sensor instances based on the key."""
    if key.startswith("+CTSDSR"):
        return CTSDRSSensor(coordinator, key, value)
    if key.startswith(("+GMI", "+GMM", "+GMR")):
        return GMSensor(coordinator, key, value)
    if key.startswith(("+CME ERROR", "+CMEE")):
        return CMESensor(coordinator, key, value)
    if key == "connection_status":
        return ConnectionStatusSensor(coordinator, key, value)

    # Fallback-Handler
    return TetraBaseSensor(coordinator, key, key, value)
