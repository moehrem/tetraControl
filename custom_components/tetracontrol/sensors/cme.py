"""Sensor for CME data in TetraControl integration."""

from .base import TetraBaseSensor


class CMESensor(TetraBaseSensor):
    def __init__(self, coordinator, key, data):
        self.attr_name = data.get("sds_command_desc", "Unknown")
        self.attr_unique_id = data.get("sds_command_desc", "Unknown")
        # self.data = data
        super().__init__(coordinator, self.attr_name, self.attr_unique_id, data)

    @property
    def state(self):
        return self._data.get("sds_command_desc", "Unknown")

    @property
    def extra_state_attributes(self):
        return self._data
