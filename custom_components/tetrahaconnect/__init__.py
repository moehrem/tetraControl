"""tetraHAconnect integration for Home Assistant."""

# import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN
from .coordinator import TetrahaconnectCoordinator

# _LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up tetraHAconnect from a config entry."""
    coordinator = TetrahaconnectCoordinator(hass, config_entry)
    # await coordinator.async_config_entry_first_refresh()
    await coordinator.async_start()
    hass.data[DOMAIN] = coordinator
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: TetrahaconnectCoordinator = hass.data[DOMAIN]
    await coordinator.async_stop()
    await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    return True
