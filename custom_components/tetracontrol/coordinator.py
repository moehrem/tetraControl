"""Coordinator for TetraControl integration."""

import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN
from .com_manager import COMManager

_LOGGER = logging.getLogger(__name__)


class tetraControlCoordinator(DataUpdateCoordinator):
    """Coordinator to manage COM data for TetraControl."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        super().__init__(
            hass, _LOGGER, name=f"{DOMAIN} Coordinator", update_interval=None
        )
        self.config_entry = config_entry
        self.manufacturer = config_entry.data["manufacturer"]
        self.serial_port: str = config_entry.data["serial_port"]

        self._com_manager = COMManager(self, self.serial_port)

    async def async_start(self):
        await self._com_manager.start(self.hass)

    async def async_stop(self):
        await self._com_manager.stop()
