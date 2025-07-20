"""Several unils and tool helping handling of tetraconnect."""

import logging

_LOGGER = logging.getLogger(__name__)


class TetraconnectHelpers:
    """Class for any helper method, that is not needed for a specific purpose only."""

    def __init__(self, coordinator) -> None:
        """Initialize tetraconnectHelpers."""
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
        data_dict: dict[str, str],
    ) -> None:
        """Create a message based on the given dictionary.

        The first key will be the key of the message, and the rest will be the content. Finally
        a HA entity will be created or updated with the message. The first key will be used as the entity ID.

        Args:
            data_dict (dict[str, str]): Dictionary containing variables to compose to a HA entity message.

        Raises:
            TypeError: If data_dict is not a dictionary.
            ValueError: If data_dict is empty or does not contain valid keys.

        """
        if not isinstance(data_dict, dict):
            _LOGGER.error("Data must be a dictionary, got %s", type(data_dict))
            raise TypeError("Data must be a dictionary")

        if not data_dict:
            _LOGGER.error("Data dictionary is empty")
            raise ValueError("Data dictionary cannot be empty")

        try:
            # Only include keys with non-empty, non-None, non-zero values
            # message: dict[str, str] = {
            #     k: v for k, v in data_dict.items() if v not in ("", 0, None)
            # }

            message: dict[str, str] = dict(data_dict)

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
