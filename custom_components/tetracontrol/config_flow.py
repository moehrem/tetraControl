"""Config flow to configure the tetraControl."""

# Konzept:
# - Nutzer kann Gerätehersteller und Port auswählen
# - Gerätehersteller ist eine Liste aus Konstanten
# - Port muss vorab ermittelt und per DropDown bereitgestellt werden

from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, MANUFACTURERS_LIST, VERSION


class tetraControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Radio Control."""

    VERSION = VERSION

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Option wurde ausgewählt – speichern
            return self.async_create_entry(
                title=user_input["manufacturer"],
                data=user_input,
            )

        # Dropdown-Feld anzeigen
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("manufacturer"): vol.In(MANUFACTURERS_LIST)}
            ),
            errors=errors,
        )
