"""Entity for connection status in tetraHAconnect integration."""

from homeassistant.helpers.entity import EntityCategory

from .base import TetraBaseSensor


class ConnectionStatusSensor(TetraBaseSensor):
    """Sensor for connection status in tetraHAconnect integration."""

    def __init__(self, coordinator, key, data) -> None:
        """Initialize the connection status sensor."""

        super().__init__(coordinator, key, data)

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = data["connection_status"]
        self._attr_extra_state_attributes = data
        self._attr_icon = "mdi:lan-connect"

    def update_entities(self, data) -> None:
        """Handle updated data from the coordinator. Overwrites the base method."""
        self._attr_native_value = data["connection_status"]

        # update icon
        if data["connection_status"] == "connected":
            self._attr_icon = "mdi:lan-connect"
        else:
            self._attr_icon = "mdi:lan-disconnect"

        self.async_write_ha_state()
