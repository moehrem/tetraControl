"""Sensor for CME / error data in TetraControl integration."""

from homeassistant.helpers.entity import EntityCategory

from .base import TetraBaseSensor


class CMESensor(TetraBaseSensor):
    """Sensor for CME data in TetraControl integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the CME sensor."""

        super().__init__(coordinator, key, data)

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = data.get("cme_error_message", "unknown")
        self._attr_icon = "mdi:alert-decagram"

    def update_entities(self, data) -> None:
        """Handle updated data from the coordinator. Overwrites the base method."""
        self._attr_native_value = data.get("cme_error_message", "unknown")
        self._attr_extra_state_attributes = data

        self.async_write_ha_state()
