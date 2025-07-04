"""Contain base class for tetraControl sensors."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class TetraBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for TetraControl sensors."""

    def __init__(self, coordinator, name, unique_id, data):
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
    def device_info(self):
        return {
            "identifiers": {
                ("tetraControl", f"{self._manufacturer}_{self._device_id}")
            },
            "name": f"{self._manufacturer} {self._device_id}",
            "manufacturer": self._manufacturer,
            "model": self._model,
            "sw_version": self._revision,
        }

    def update_data(self, data):
        self._data = data
        self.async_write_ha_state()
