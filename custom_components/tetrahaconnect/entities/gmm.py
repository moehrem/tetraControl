"""Sensor for "+GMM" / model identification data in TetraHAConnect integration."""

from homeassistant.helpers.entity import EntityCategory

from .base import TetraBaseSensor


class GMMSensor(TetraBaseSensor):
    """Sensor for "+GMM" data in TetraHAConnect integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the GMM sensor."""

        super().__init__(coordinator, key, data)

        self._attr_name = "Model"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = data["device_id"]
        self._attr_icon = "mdi:radio-handheld"

    def update_entities(self, data) -> None:
        """Handle updated data from the coordinator. Overwrites the base method."""
        self._attr_native_value = data["device_id"]
        self._attr_extra_state_attributes = data

        self.async_write_ha_state()
