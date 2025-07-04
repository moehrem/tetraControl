# custom_components/tetracontrol/com_manager.py

import asyncio
import logging
import serial
import serial_asyncio

from homeassistant.exceptions import ConfigEntryNotReady

from .com_data_handler import com_data_handler


_LOGGER = logging.getLogger(__name__)


class COMManager:
    """Manages serial COM connection lifecycle."""

    def __init__(self, coordinator, com_port: str, baudrate: int = 9600):
        self.coordinator = coordinator
        self.com_port = com_port
        self.baudrate = baudrate
        self.transport = None
        self.protocol = None
        self._connection_check_task = None

    async def start(self, hass):
        """Establish connection and start monitoring."""
        await self._connect()

        # Start periodic connection check
        self._connection_check_task = hass.loop.create_task(
            self._periodic_connection_check(hass)
        )

    async def stop(self):
        """Stop connection and monitoring."""
        if self.transport:
            self.transport.close()
            self.transport = None
            self.protocol = None
        if self._connection_check_task:
            self._connection_check_task.cancel()
            try:
                await self._connection_check_task
            except asyncio.CancelledError:
                pass

    async def _connect(self):
        """Try to establish the serial connection."""
        try:
            loop = asyncio.get_running_loop()
            (
                self.transport,
                self.protocol,
            ) = await serial_asyncio.create_serial_connection(
                loop,
                lambda: com_data_handler(self.coordinator),
                self.com_port,
                baudrate=self.baudrate,
            )
            _LOGGER.info("Serial connection established on %s", self.com_port)
            await self._tetra_initialize()

        except (serial.SerialException, OSError, ValueError) as e:
            _LOGGER.error("Failed to establish serial connection: %s", e)
            raise ConfigEntryNotReady(f"Serial connection failed: {e}") from e

    async def _periodic_connection_check(self, hass):
        """Check and re-establish connection if necessary."""
        while True:
            await asyncio.sleep(10)
            if self.transport is None or self.transport.is_closing():
                _LOGGER.warning("Serial connection lost. Reconnecting...")
                await self.stop()
                await self._connect()

                if self.transport and not self.transport.is_closing():
                    self.coordinator.async_set_updated_data(
                        {"connection_status": "connected"}
                    )
                    continue

                for attempt in range(1, 11):
                    await asyncio.sleep(5)
                    await self.stop()
                    await self._connect()
                    if self.transport and not self.transport.is_closing():
                        self.coordinator.async_set_updated_data(
                            {"connection_status": "connected"}
                        )
                        _LOGGER.info("Reconnected successfully on attempt %d", attempt)
                        break
                else:
                    self.coordinator.async_set_updated_data(
                        {"connection_status": "disconnected"}
                    )
                    _LOGGER.error("Failed to reconnect after 10 attempts.")

    async def _tetra_initialize(self):
        """Initialize TETRA device for specific CTSP-Services."""
        # these commands are standard TETRA commands, which every device should respond to
        if not self.transport:
            _LOGGER.warning("No serial connection available, initializing failed.")
            return

        _LOGGER.info("Initializing TETRA device on %s", self.com_port)

        device_commands = ["ATZ\r\n", "AT+GMI?\r\n", "AT+GMM?\r\n", "AT+GMR?\r\n"]
        service_commands = [
            # "AT+CTSP=1,2,20\r\n",  # Status TE
            "AT+CTSP=2,2,20\r\n",  # Status MT & TE
            "AT+CTSP=1,3,130\r\n",  # Textnachrichten einschalten
            "AT+CTSP=1,3,131\r\n",  # GPS einschalten
            "AT+CTSP=1,3,10\r\n",  # Status GPS
            "AT+CTSP=1,3,137\r\n",  # Immediate Text
            "AT+CTSP=1,3,138\r\n",  # Alarm
        ]
        # +CTSP=<service profile>, <service layer1>, [<service layer2>], [<AI mode>], [<link identifier>]

        for cmd in device_commands:
            _LOGGER.debug("Sending init command: %s", cmd.strip())
            self.transport.write(cmd.encode())
            await asyncio.sleep(0.1)

        for cmd in service_commands:
            _LOGGER.debug("Sending service command: %s", cmd.strip())
            self.transport.write(cmd.encode())
            await asyncio.sleep(0.1)

        _LOGGER.info("TETRA device initialized successfully on %s", self.com_port)
