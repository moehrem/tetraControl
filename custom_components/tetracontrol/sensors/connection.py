"""Sensor for connection status in TetraControl integration."""

from .base import TetraBaseSensor


class ConnectionStatusSensor(TetraBaseSensor):
    """Sensor for connection status in TetraControl integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the connection status sensor."""
        self.device_id = coordinator.config_entry.data.get("device_id")
        self.attr_name = f"{key} {self.device_id}"
        self.attr_unique_id = f"{key}_{self.device_id}"
        super().__init__(coordinator, self.attr_name, self.attr_unique_id, data)

    @property
    def state(self):
        return self._data

    @property
    def extra_state_attributes(self):
        return {"connection_status": self._data}
