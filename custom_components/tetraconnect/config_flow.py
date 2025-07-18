"""Config flow to configure the tetraconnect integration."""

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

import serial
import serial_asyncio  # type: ignore
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, MANUFACTURERS_LIST, VERSION, MINOR_VERSION, PATCH_VERSION

_LOGGER = logging.getLogger(__name__)


@dataclass
class TetraconnectConfigEntry:
    """Data class to hold device information."""

    manufacturer: str = "unknown"
    serial_port: str = ""
    baudrate: int = 0
    device_id: str = "unknown"
    model: str = "unknown"
    revision: str = "unknown"


class TetraconnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tetraconnect."""

    VERSION = VERSION
    MINOR_VERSION = MINOR_VERSION
    PATCH_VERSION = PATCH_VERSION

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.config_entry = TetraconnectConfigEntry()
        self.errors: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, object] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step of the config flow."""

        if user_input is not None:
            # init error buffer
            self.errors = {}

            # set user input variables
            self.config_entry.manufacturer = str(user_input["manufacturer"])
            self.config_entry.serial_port = str(user_input["serial_port"])
            self.config_entry.baudrate = int(str(user_input["baudrate"]))

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
        devices: list[str] = []

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

    async def _request_device_data(self, config_entry: TetraconnectConfigEntry):
        """Request serial port and request device data.

        Request manufacturer, model and revision identification from the device.
        Wait for an answer for each command.
        This will not create any entities, its just for device setup.

        Service commands will be initialized in com_manager.

        """
        device_commands = [
            "ATZ\r\n",
            "AT+GMI?\r\n",
            "AT+GMM?\r\n",
            "AT+GMR?\r\n",
        ]

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
            await asyncio.sleep(0.1)

        await writer.drain()
        response = b""
        response = await asyncio.wait_for(reader.read(1024), timeout=5)

        writer.close()
        await writer.wait_closed()

        # parse response
        self._parse_init_data(response)

    def _parse_init_data(self, response) -> None:
        """Parse the initial response to extract manufacturer, and device ID."""

        device_manufacturer = "Unknown"
        device_id = "Unknown"
        device_revision = "Unknown"

        response = response.decode("utf-8").strip()
        _LOGGER.debug("Config: Raw response: %s", response)

        response_lines = response.split("\r\n")

        for line in response_lines:
            if line.startswith("+GMI") and ":" in line:
                device_manufacturer = line.split(":", 1)[1].strip()
                self._check_manufacturer(device_manufacturer)
            elif line.startswith("+GMM") and ":" in line:
                parts = line.split(":", 1)[1].strip().split(",")
                if len(parts) > 1:
                    device_id = parts[1]
            elif line.startswith("+GMR") and ":" in line:
                device_revision = line.split(":", 1)[1].strip()
            # elif line.startswith("AT+CTSP"):
            #     message = line.split(":", 1)
            #     if message[1].strip() != "OK":
            #         _LOGGER.warning(
            #             "Service profile command %s failed with response: %s",
            #             line,
            #             message[1].strip(),
            #         )

        # for cmd, resp in parsed_data.items():
        #     _LOGGER.debug("Config: Command: %s, Response: %s", cmd, resp)
        #     if cmd == "AT+GMI?":
        #         device_manufacturer = resp.split(":")[1].strip()
        #         # check manufacturer
        #         self._check_manufacturer(device_manufacturer)
        #     elif cmd == "AT+GMM?":
        #         device_id = resp.split(":")[1].strip().split(",")[1]
        #     elif cmd == "AT+GMR?":
        #         device_revision = resp.split(":")[1].strip()
        #     elif cmd.startswith("AT+CTSP"):
        #         if resp != "OK":
        #             _LOGGER.warning(
        #                 "Service profile command %s failed with response: %s",
        #                 cmd,
        #                 resp,
        #             )
        #         _LOGGER.debug(
        #             "Service profile command %s sucessful for device %s (%s)",
        #             cmd,
        #             device_id,
        #             device_manufacturer,
        #         )

        self.config_entry.model = device_id
        self.config_entry.device_id = device_id
        self.config_entry.revision = device_revision

    def _check_manufacturer(self, manufacturer: str):
        """Check if the user manufacturer matches the device manufacturer."""

        device_manufacturer = manufacturer.strip().lower()
        user_manufacturer = self.config_entry.manufacturer.strip().lower()

        if device_manufacturer.lower() != user_manufacturer.lower():
            _LOGGER.error(
                "Manufacturer mismatch! device confirms: %s, user has entered: %s",
                device_manufacturer,
                user_manufacturer,
            )
            raise ValueError(
                f"Manufacturer mismatch: {device_manufacturer} != {user_manufacturer}"
            )
