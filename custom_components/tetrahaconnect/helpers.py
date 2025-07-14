"""Several unils and tool helping handling of tetraHAconnect."""

import logging

_LOGGER = logging.getLogger(__name__)


class TetrahaconnectHelpers:
    """Class for any helper method, that is not needed for a specific purpose only."""

    def __init__(self, coordinator) -> None:
        """Initialize tetraHAconnectHelpers."""
        self.coordinator = coordinator

    def update_connection_status(self, status):
        "Set connection status."
        status_mapping = {
            1: "connected",
            2: "reconnecting",
            3: "disconnected",
        }

        status_text = status_mapping.get(status, "unknown")

        message = {
            "connection_status": {
                "connection_status": status_text,
                "validity": "valid",
            }
        }

        # sds_message = self.create_message(variables, messages)

        self.coordinator.async_set_updated_data(message)

    def update_entities(
        self,
        tetra_variables: dict[str, str],
    ) -> None:
        """Create a message based on the current SDS variables.

        The returned dictionary uses the first key from the message as its key,
        and the rest of the message as its value.
        """
        tetra_variables["sds_content"] = ""

        try:
            # Only include keys with non-empty, non-None, non-zero values
            message: dict[str, str] = {
                k: v for k, v in tetra_variables.items() if v not in ("", 0, None)
            }

            if next(iter(message), None) != "sds_command":
                first_key = next(iter(message), None)
            else:
                first_key = message["sds_command"]

            if first_key is not None:
                new_message = {first_key: message}
                self.coordinator.async_set_updated_data(new_message)

                _LOGGER.debug(
                    "Updated entity with message %s for key %s",
                    message,
                    first_key,
                )
            else:
                _LOGGER.error("No valid key found in message")
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.error(
                "Error updating entity: %s",
                err,
            )
