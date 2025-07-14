"""Sensor for CTSDRS data in TetraHAConnect integration."""

from homeassistant.helpers.entity import EntityCategory

from .base import TetraBaseSensor


class CTSDRSSensor(TetraBaseSensor):
    """Sensor for CTSDRS data in TetraHAConnect integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the CTSDRS sensor."""

        super().__init__(coordinator, key, data)

        self._attr_native_value = data["sds_type_desc"]
        self._attr_icon = "mdi:message-check"

    def update_entities(self, data) -> None:
        """Handle updated data from the coordinator. Overwrites the base method."""
        self._attr_native_value = data["sds_type_desc"]
        self._attr_extra_state_attributes = data

        self.async_write_ha_state()
