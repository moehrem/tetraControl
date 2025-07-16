"""Coordinator for tetraconnect integration."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryNotReady
from .const import DOMAIN
from .com_manager import COMManager

_LOGGER = logging.getLogger(__name__)


class TetraconnectCoordinator(DataUpdateCoordinator):
    """Coordinator to manage COM data for tetraconnect."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN} Coordinator", update_interval=None
        )
        # self.config_entry = config_entry
        self.manufacturer: str = config_entry.data["manufacturer"]
        self.serial_port: str = config_entry.data["serial_port"]
        self.baudrate: int = config_entry.data["baudrate"]

        self._com_manager = COMManager(self, self.serial_port, self.baudrate)

    async def async_start(self):
        """Start the COM manager."""
        try:
            await self._com_manager.serial_initialize(self.hass)
            await self._com_manager.tetra_initialize()
        except Exception as e:
            _LOGGER.error(f"Failed to initialize COM manager: {e}")
            raise ConfigEntryNotReady from e

    async def async_stop(self):
        """Stop the COM manager."""
        await self._com_manager.serial_stop()
