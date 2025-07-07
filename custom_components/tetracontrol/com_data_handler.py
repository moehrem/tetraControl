# """Handle serial data communication for tetraControl."""

# import asyncio
# import logging
# from .motorola import Motorola

# _LOGGER = logging.getLogger(__name__)


# class serial_handler(asyncio.Protocol):
#     """Handles incoming serial data."""

#     def __init__(self, coordinator) -> None:
#         """Initialize the data handler."""
#         self.coordinator = coordinator
#         self.raw_data = b""
#         self.motorola = Motorola(coordinator)

#     def connection_made(self, transport):
#         """Handle the connection being made."""
#         self.transport = transport
#         _LOGGER.debug("Serial connection opened")
#         self.coordinator.async_set_updated_data({"connection_status": "connected"})

#     def data_received(self, data):
#         """Handle incoming data."""
#         self.raw_data += data

#         try:
#             if self.coordinator.manufacturer == "Motorola":
#                 messages, remaining = self.motorola.data_handler(self.raw_data)

#             ################################################
#             ### Add other manufacturers data parser here ###
#             ################################################

#             else:
#                 _LOGGER.error(
#                     "Unsupported manufacturer: %s", self.coordinator.manufacturer
#                 )
#                 return

#             # put remaining data back into raw_data
#             self.raw_data = remaining

#             # update coordinator and trigger sensor updates
#             self.coordinator.async_set_updated_data(messages)

#         except Exception as e:
#             _LOGGER.error("Error decoding serial data: %s", e)

#     def connection_lost(self, exc):
#         """Handle the connection being lost."""
#         _LOGGER.warning("Serial connection lost: %s", exc)
#         self.coordinator.async_set_updated_data({"connection_status": "disconnected"})
