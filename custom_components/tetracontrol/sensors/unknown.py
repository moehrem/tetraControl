"""Sensor for any unknown data in TetraControl integration."""

from .base import TetraBaseSensor


class UnknownSensor(TetraBaseSensor):
    """Sensor for unknown data in TetraControl integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the CTSDRS sensor."""
        self.attr_name = key
        self.attr_unique_id = key
        super().__init__(coordinator, self.attr_name, self.attr_unique_id, data)

    @property
    def native_value(self) -> str:  # type: ignore
        """Return the current value of the sensor."""
        return self._data.get("sds_type_desc", "Unknown")

    @property
    def extra_state_attributes(self):  # type: ignore
        """Return the state attributes of the sensor."""
        return self._data
