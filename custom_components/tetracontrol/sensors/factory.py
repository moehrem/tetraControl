"""Contain factory function to create sensor instances for TetraControl integration."""

from .base import TetraBaseSensor
from .cme import CMESensor
from .connection import ConnectionStatusSensor
from .ctsdsr import CTSDRSSensor
from .gmi import GMISensor
from .gmm import GMMSensor
from .gmr import GMRSensor


def sensor_factory(coordinator, key, value) -> TetraBaseSensor:
    """Return sensor instances based on the key."""
    if key.startswith("+CTSDSR"):
        return CTSDRSSensor(coordinator, key, value)
    if key.startswith("+GMI"):
        return GMISensor(coordinator, key, value)
    if key.startswith("+GMR"):
        return GMRSensor(coordinator, key, value)
    if key.startswith("+GMM"):
        return GMMSensor(coordinator, key, value)
    if key.startswith(("+CME ERROR", "+CMEE")):
        return CMESensor(coordinator, key, value)
    if key == "connection_status":
        return ConnectionStatusSensor(coordinator, key, value)

    # fallback handler
    # If no matching tetra command found, return base class sensor
    return TetraBaseSensor(coordinator, key, key, value)
