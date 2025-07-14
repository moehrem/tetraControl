"""Sensor for invalid data in tetraHAconnect integration."""

from homeassistant.helpers.entity import EntityCategory

from .base import TetraBaseSensor


class TetraInvalid(TetraBaseSensor):
    """Sensor for invalid data in tetraHAconnect integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the GMM sensor."""

        super().__init__(coordinator, key, data)

        self._attr_name = key
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = "message"
        self._attr_icon = "mdi:message-question"

    def update_entities(self, data) -> None:
        """Handle updated data from the coordinator. Overwrites the base method."""
        self._attr_native_value = "message"
        self._attr_extra_state_attributes = data

        self.async_write_ha_state()
