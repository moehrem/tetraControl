"""Sensor setup for TetraControl integration."""

import logging

from homeassistant.core import HomeAssistant, callback

from homeassistant.config_entries import ConfigEntry

from collections.abc import Callable
from typing import Any
from .const import DOMAIN
from .entities.base import TetraBaseSensor
from .entities.cme import CMESensor
from .entities.connection import ConnectionStatusSensor
from .entities.ctsdsr import CTSDRSSensor
from .entities.gmi import GMISensor
from .entities.gmm import GMMSensor
from .entities.gmr import GMRSensor
from .entities.invalid import TetraInvalid

# Mapping from TETRA command to sensor class
# add any new command-sensorclass-combo here
# DO NOT remove or change entries "connection_status" or "default"!
SENSOR_CLASS_MAP: dict[str, type[TetraBaseSensor]] = {
    "+CTSDSR": CTSDRSSensor,
    "+CMEE": CMESensor,
    "+CME ERROR": CMESensor,
    "+GMI": GMISensor,
    "+GMM": GMMSensor,
    "+GMR": GMRSensor,
    "connection_status": ConnectionStatusSensor,
    "default": TetraBaseSensor,  # Fallback for unknown commands
    "Invalid": TetraInvalid,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable[[list[Any]], None],
) -> None:
    """Set up TetraControl sensors based on a config entry."""
    coordinator = hass.data[DOMAIN]
    entities = {}

    @callback
    def update_entities():
        messages: dict[str, dict[str, Any]] = coordinator.data or {}
        new_entities: list[TetraBaseSensor] = []

        for key, data in messages.items():
            if key in entities:
                entities[key].update_entities(data)
            else:
                try:
                    # special case: invalid messages
                    if data["validity"] == "invalid":
                        sensor_cls = SENSOR_CLASS_MAP.get("invalid", TetraBaseSensor)
                        entity = sensor_cls(coordinator, key, data)

                    # Check if the key is in the SENSOR_CLASS_MAP
                    else:
                        sensor_cls = SENSOR_CLASS_MAP.get(key, TetraBaseSensor)
                        entity = sensor_cls(coordinator, key, data)

                except (KeyError, TypeError, AttributeError):
                    # If the key is not found, use the default sensor class
                    sensor_cls = SENSOR_CLASS_MAP.get("default", TetraBaseSensor)
                    entity = sensor_cls(coordinator, key, data)

                # entity = sensor_factory(coordinator, key, data)
                entities[key] = entity
                new_entities.append(entity)

        if new_entities:
            async_add_entities(new_entities)

    update_entities()
    coordinator.async_add_listener(update_entities)
