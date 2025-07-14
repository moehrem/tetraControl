"""Sensor for "+GMI" / manufacturer identification data in tetraHAconnect integration."""

from homeassistant.helpers.entity import EntityCategory

from .base import TetraBaseSensor


class GMISensor(TetraBaseSensor):
    """Sensor for "+GMI" data in tetraHAconnect integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the GMI sensor."""

        super().__init__(coordinator, key, data)

        self._attr_name = "Manufacturer"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = data["manufacturer"]
        self._attr_icon = "mdi:cogs"

    def update_entities(self, data) -> None:
        """Handle updated data from the coordinator. Overwrites the base method."""
        self._attr_native_value = data["manufacturer"]
        self._attr_extra_state_attributes = data

        self.async_write_ha_state()
