"""Contain base class for tetraControl sensors."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class TetraBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for TetraControl sensors."""

    def __init__(self, coordinator, name, unique_id, data) -> None:
        """Initialize the TetraControl sensor.

        This class also serves as fallback handler for any messages with unknown tetra-commands. It will not handle messages without command!

        """
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._data = data
        cfg = coordinator.config_entry.data
        self._manufacturer = cfg.get("manufacturer", "unknown")
        self._device_id = cfg.get("device_id", "unknown")
        self._model = cfg.get("model", "unknown")
        self._revision = cfg.get("revision", "unknown")

    @property
    def device_info(self):  # type: ignore
        """Return device information for the sensor."""
        return {
            "identifiers": {
                ("tetraControl", f"{self._manufacturer}_{self._device_id}")
            },
            "name": f"{self._manufacturer} {self._device_id}",
            "manufacturer": self._manufacturer,
            "model": self._model,
            "sw_version": self._revision,
        }

    @property
    def native_value(self) -> str:  # type: ignore
        """Return the current value of the sensor."""
        return self._data.get("sds_command_desc", "Unknown Command")

    @property
    def extra_state_attributes(self):  # type: ignore
        """Return the state attributes of the sensor."""
        return self._data

    def update_data(self, data):
        """Update the sensor data."""
        self._data = data
        self.async_write_ha_state()
