"""Config flow to configure the tetraControl."""

import asyncio
from dataclasses import dataclass
from pathlib import Path
import os

import serial
import serial_asyncio
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    ConfigEntryNotReady,
)

from .const import DOMAIN, MANUFACTURERS_LIST, VERSION, MINOR_VERSION, PATCH_VERSION


@dataclass
class tetraControlConfigEntry:
    """Data class to hold device information."""

    manufacturer: str = "unknown"
    serial_port: str = ""
    baudrate: int = 0
    device_id: str = "unknown"
    model: str = "unknown"
    revision: str = "unknown"


class tetraControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for tetraControl."""

    VERSION = VERSION
    MINOR_VERSION = MINOR_VERSION
    PATCH_VERSION = PATCH_VERSION

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.config_entry = tetraControlConfigEntry()
        self.errors: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, object] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of the config flow."""

        if user_input is not None:
            # init error buffer
            self.errors = {}

            # set user input variables
            self.config_entry.manufacturer = user_input["manufacturer"]
            self.config_entry.serial_port = user_input["serial_port"]
            self.config_entry.baudrate = user_input["baudrate"]

            try:
                await self._request_device_data(self.config_entry)
            except TimeoutError:
                self.errors["base"] = "timeout_error"
                return await self._async_show_form_user()

            except (serial.SerialException, OSError):
                self.errors["base"] = "serial_error"
                return await self._async_show_form_user()

            except ValueError:
                self.errors["base"] = "manufacturer_mismatch"
                return await self._async_show_form_user()

            # create config entry
            return self.async_create_entry(
                title=f"{self.config_entry.manufacturer} {self.config_entry.device_id}",
                data=self.config_entry.__dict__,
            )

        return await self._async_show_form_user()

    async def _async_show_form_user(self) -> ConfigFlowResult:
        """Show the user input form."""

        ports = await self.hass.async_add_executor_job(self._get_serial_ports)

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
            errors=self.errors,
        )

    def _get_serial_ports(self) -> list[str]:
        """Return a filtered list of usable serial ports on the system."""
        devices = []

        # patterns to match serial devices
        serial_patterns = [
            "/dev/ttyUSB*",
            "/dev/ttyACM*",
            "/dev/ttyS*",
            "/dev/ttyAMA*",
            "/dev/serial/by-id/*",
            "/dev/pts/[0-9]*",
        ]

        # check each pattern and collect devices
        for pattern in serial_patterns:
            devices.extend(str(p) for p in Path("/").glob(pattern.lstrip("/")))

        # filter devices that are readable and writable
        usable_devices = [
            dev
            for dev in devices
            if Path(dev).exists() and os.access(dev, os.R_OK | os.W_OK)
        ]

        return sorted(set(usable_devices))

    async def _request_device_data(self, config_entry: tetraControlConfigEntry):
        """Request serial port and request device data."""
        device_commands = ["ATZ\r\n", "AT+GMI?\r\n", "AT+GMM?\r\n", "AT+GMR?\r\n"]

        try:
            reader, writer = await asyncio.wait_for(
                serial_asyncio.open_serial_connection(
                    url=config_entry.serial_port, baudrate=config_entry.baudrate
                ),
                timeout=5,
            )
        except (serial.SerialException, OSError) as e:
            raise ConfigEntryNotReady(
                f"Failed to connect to serial port {config_entry.serial_port}: {e}"
            ) from e

        # send initial commands to the device
        for cmd in device_commands:
            writer.write(cmd.encode("utf-8"))

        await asyncio.sleep(1)
        await writer.drain()

        # wait for the response from the device
        try:
            response = await asyncio.wait_for(reader.read(1024), timeout=5)
        except TimeoutError:
            writer.close()
            await writer.wait_closed()
            raise TimeoutError from None

        # parse response
        self._parse_init_data(response)
        writer.close()
        await writer.wait_closed()

    def _parse_init_data(self, response) -> None:
        """Parse the initial response to extract manufacturer, and device ID."""
        lines = response.decode("utf-8").splitlines()
        device_manufacturer = "Unknown"
        device_id = "Unknown"
        device_revision = "Unknown"

        for line in lines:
            if "+GMI:" in line:
                device_manufacturer = line.split(":")[1].strip()
            elif "+GMM:" in line:
                device_id = line.split(":")[1].strip().split(",")[1]
            elif "+GMR:" in line:
                device_revision = line.split(":")[1].strip()

        # check manufacturer
        self._check_manufacturer(device_manufacturer)

        self.config_entry.model = device_id
        self.config_entry.device_id = device_id
        self.config_entry.revision = device_revision

    def _check_manufacturer(self, manufacturer: str):
        """Check if the user manufacturer matches the device manufacturer."""

        device_manufacturer = manufacturer.strip().lower()
        user_manufacturer = self.config_entry.manufacturer.strip().lower()

        if device_manufacturer.lower() != user_manufacturer.lower():
            raise ValueError(
                f"Manufacturer mismatch: {device_manufacturer} != {user_manufacturer}"
            )
