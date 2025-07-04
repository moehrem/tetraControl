"""Config flow to configure the tetraControl."""

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
import serial_asyncio
import serial
import asyncio
import voluptuous as vol
import glob
import os
import time

from .const import DOMAIN, MANUFACTURERS_LIST, VERSION


class tetraControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for tetraControl."""

    VERSION = VERSION

    async def async_step_user(self, user_input=None):
        errors = {}
        ports = await self.hass.async_add_executor_job(self._get_serial_ports)

        if user_input is not None:
            user_manufacturer = user_input.get("manufacturer", "unknown")
            serial_port = user_input.get("serial_port")
            baudrate = user_input.get("baudrate", 38400)
            device_commands = ["ATZ\r\n", "AT+GMI?\r\n", "AT+GMM?\r\n", "AT+GMR?\r\n"]

            try:
                reader, writer = await asyncio.wait_for(
                    serial_asyncio.open_serial_connection(
                        url=serial_port, baudrate=baudrate
                    ),
                    timeout=5,
                )
                # send initial commands to the device
                for cmd in device_commands:
                    writer.write(cmd.encode("utf-8"))

                await asyncio.sleep(1)
                await writer.drain()
                response = await reader.read(1024)
                # parse response
                device_manufacturer, model, device_id, revision = self._parse_init_data(
                    response
                )
                writer.close()
                await writer.wait_closed()
            except TimeoutError:
                errors["base"] = "timeout_error"
                return self.async_show_form(step_id="user", errors=errors)

            except (serial.SerialException, OSError, ValueError):
                errors["base"] = "serial_error"
                return self.async_show_form(step_id="user", errors=errors)

            if device_manufacturer.lower() != user_manufacturer.lower():
                errors["base"] = "manufacturer_mismatch"
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema(
                        {
                            vol.Required("manufacturer"): vol.In(MANUFACTURERS_LIST),
                            vol.Required("serial_port"): vol.In(ports),
                            vol.Required("baudrate", default=38400): vol.All(
                                vol.Coerce(int), vol.Range(min=300, max=115200)
                            ),
                        }
                    ),
                    errors=errors,
                )

            # Im config_entry speichern
            return self.async_create_entry(
                title=f"{user_manufacturer} {device_id}",
                data={
                    "serial_port": user_input["serial_port"],
                    "baudrate": user_input["baudrate"],
                    "model": model,
                    "manufacturer": user_manufacturer,
                    "device_id": device_id,
                    "revision": revision,
                },
            )

        # Blocking call in Thread auslagern
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("manufacturer"): vol.In(MANUFACTURERS_LIST),
                    vol.Required("serial_port"): vol.In(ports),
                    vol.Required("baudrate", default=38400): vol.All(
                        vol.Coerce(int), vol.Range(min=300, max=115200)
                    ),
                }
            ),
            errors=errors,
        )

    def _get_serial_ports(self):
        """Return a filtered list of usable serial ports on the system."""
        devices = []

        # Bekannte serielle Geräteklassen
        serial_patterns = [
            "/dev/ttyUSB*",  # USB-Seriell
            "/dev/ttyACM*",  # USB CDC ACM
            "/dev/ttyS*",  # Serielle Onboard- oder PCI-Ports
            "/dev/ttyAMA*",  # ARM UART
            "/dev/serial/by-id/*",  # Symbolische Links (z. B. mit Gerätename)
            "/dev/pts/[0-9]*",  # Pseudoterminals, z. B. von socat
        ]

        # Geräte einsammeln
        for pattern in serial_patterns:
            devices.extend(glob.glob(pattern))

        # Nur Geräte zurückgeben, die les- und schreibbar sind
        usable_devices = [
            dev
            for dev in devices
            if os.path.exists(dev) and os.access(dev, os.R_OK | os.W_OK)
        ]

        return sorted(set(usable_devices))

    def _parse_init_data(self, response):
        """Parse the initial response to extract manufacturer, model, and device ID."""
        # Beispielhafte Parsing-Logik, abhängig vom tatsächlichen Format der Antwort
        lines = response.decode("utf-8").splitlines()
        manufacturer = "Unknown"
        model = "Unknown"
        device_id = "Unknown"
        revision = "Unknown"

        for line in lines:
            if "+GMI:" in line:
                manufacturer = line.split(":")[1].strip()
            elif "+GMM:" in line:
                model = line.split(":")[1].strip().split(",")[0]
                device_id = line.split(":")[1].strip().split(",")[1]
            elif "+GMR:" in line:
                revision = line.split(":")[1].strip()

        return manufacturer, model, device_id, revision
