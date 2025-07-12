# """Sensor for any unknown data in TetraControl integration."""

# from homeassistant.helpers.entity import EntityCategory

# from .base import TetraBaseSensor


# class UnknownSensor(TetraBaseSensor):
#     """Sensor for unknown data in TetraControl integration."""

#     def __init__(self, coordinator, key, data) -> None:
#         """Initialize the CTSDRS sensor."""
#         # attr_name = key
#         # attr_unique_id = key
#         super().__init__(coordinator, key, data)

#         # self._attr_name = attr_name
#         # self._attr_unique_id = attr_unique_id
#         self._attr_native_value = data.get("sds_type_desc", "Unknown")
#         self._attr_icon = "mdi:message-question"

#     def update_entities(self, data) -> None:
#         """Handle updated data from the coordinator. Overwrites the base method."""
#         self._attr_native_value = data.get("sds_type_desc", "Unknown")
#         self._attr_extra_state_attributes = data

#         self.async_write_ha_state()
