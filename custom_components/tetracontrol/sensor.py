"""Sensor setup for TetraControl integration."""

import logging

from homeassistant.core import callback

from .const import DOMAIN
from .sensors.factory import sensor_factory

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up TetraControl sensors based on a config entry."""
    coordinator = hass.data[DOMAIN]
    entities = {}

    @callback
    def update_entities():
        messages = coordinator.data or {}
        new_entities = []
        for key, data in messages.items():
            if key in entities:
                entities[key].update_data(data)
            else:
                entity = sensor_factory(coordinator, key, data)
                entities[key] = entity
                new_entities.append(entity)
        if new_entities:
            async_add_entities(new_entities)

    update_entities()
    coordinator.async_add_listener(update_entities)
