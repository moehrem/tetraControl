"""Sensor for connection status in TetraControl integration."""

from .base import TetraBaseSensor


class ConnectionStatusSensor(TetraBaseSensor):
    def __init__(self, coordinator, key, data):
        self.attr_name = (
            f"{key}_{coordinator.config_entry.data.get('device_id', 'unknown')}"
        )
        self.attr_unique_id = (
            f"{key}_{coordinator.config_entry.data.get('device_id', 'unknown')}"
        )
        # self.data = data
        super().__init__(coordinator, self.attr_name, self.attr_unique_id, data)

    @property
    def state(self):
        return self._data

    @property
    def extra_state_attributes(self):
        return {"connection_status": self._data}
