"""Contain base class for tetraconnect sensors."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class TetraBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for tetraconnect sensors."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the tetraconnect sensor.

        This class also serves as fallback handler for any messages with unknown tetra-commands. It will not handle messages without command!

        """
        super().__init__(coordinator)

        # device details
        cfg = coordinator.config_entry.data
        self._manufacturer = cfg.get("manufacturer", "unknown")
        self._device_id = cfg.get("device_id", "unknown")
        self._model = cfg.get("model", "unknown")
        self._revision = cfg.get("revision", "unknown")
        self.device_id = cfg.get("device_id", "unknown")

        self._attr_device_info = {
            "identifiers": {
                ("tetraconnect", f"{self._manufacturer}_{self._device_id}")
            },
            "name": f"{self._manufacturer} {self._device_id}",
            "manufacturer": self._manufacturer,
            "model": self._model,
            "sw_version": self._revision,
        }

        # entity details
        self.key = key

        self._attr_name = key
        self._attr_unique_id = f"{key}_{self.device_id}"
        self._attr_native_value = data.get("sds_command_desc", "Unknown")
        self._attr_extra_state_attributes = data
        self._attr_should_poll = False
        self._attr_icon = "mdi:message-question"

    def update_entities(self, data):
        """Update the sensor data."""
        self._attr_native_value = self.key
        self._attr_extra_state_attributes = data

        self.async_write_ha_state()
