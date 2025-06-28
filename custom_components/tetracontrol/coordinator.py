"""Coordinator for tetraControl integration."""

import logging
from datetime import timedelta

from aiohttp import ClientSession, ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class RCCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching WebIO data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ):
        """Initialize the tetraControl coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} Coordinator",
            update_interval=timedelta(seconds=5),
        )

        self.config_entry = config_entry
