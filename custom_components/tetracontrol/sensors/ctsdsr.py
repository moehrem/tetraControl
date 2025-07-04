"""Sensor for CTSDRS data in TetraControl integration."""

from .base import TetraBaseSensor


class CTSDRSSensor(TetraBaseSensor):
    def __init__(self, coordinator, key, data):
        self.attr_name = key
        self.attr_unique_id = key
        # self.data = data
        super().__init__(coordinator, self.attr_name, self.attr_unique_id, data)

    @property
    def state(self):
        return self._data.get("sds_type_desc", "Unknown")

    @property
    def extra_state_attributes(self):
        return self._data
