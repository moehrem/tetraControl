"""Sensor for "+GMM" data in TetraControl integration."""

from .base import TetraBaseSensor


class GMMSensor(TetraBaseSensor):
    """Sensor for "+GMM" data in TetraControl integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the GMM sensor."""
        self.device_id = coordinator.config_entry.data.get("device_id")
        self.attr_name = data.get("sds_command_desc", "Unknown")
        self.attr_unique_id = (
            f"{data.get('sds_command_desc', 'Unknown')}_{self.device_id}"
        )
        # self.data = data
        super().__init__(coordinator, self.attr_name, self.attr_unique_id, data)

    @property
    def state(self):
        return self._data["device_id"]

    @property
    def extra_state_attributes(self):
        return self._data
