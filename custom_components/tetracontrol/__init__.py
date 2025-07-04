"""tetraControl integration for Home Assistant."""

# import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import tetraControlCoordinator

# _LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    coordinator = tetraControlCoordinator(hass, config_entry)
    await coordinator.async_start()
    hass.data[DOMAIN] = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    coordinator: tetraControlCoordinator = hass.data[DOMAIN]
    await coordinator.async_stop()
    await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    return True
