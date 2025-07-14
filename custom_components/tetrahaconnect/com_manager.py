# custom_components/TetraHAConnect/com_manager.py

import asyncio
import contextlib
import logging

import serial
import serial_asyncio

from .const import MAX_RETRY_ATTEMPTS, SLEEP_TIME_CONNECTION_CHECK, SLEEP_TIME_RETRY
from .helpers import TetraControlHelpers
from .motorola import Motorola

_LOGGER = logging.getLogger(__name__)


class COMManager:
    """Manages serial COM connection lifecycle."""

    def __init__(self, coordinator, com_port: str, baudrate: int) -> None:
        """Initialize the COMManager."""
        self.coordinator = coordinator
        self.com_port = com_port
        self.baudrate = baudrate
        self.transport = None
        self.protocol = None
        self._connection_check_task = None

        self.helpers = TetraControlHelpers(coordinator)

    async def start(self, hass):
        """Start monitoring and connection loop."""
        self._connection_check_task = hass.loop.create_task(
            self._periodic_connection_check()
        )

    async def stop(self):
        """Stop connection and monitoring."""
        if self.transport:
            self.transport.close()
            self.transport = None
            self.protocol = None
        if self._connection_check_task:
            self._connection_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._connection_check_task

    async def _connect(self):
        """Try to establish the serial connection.

        This is handled in a loop of _periodic_connection_check, which also serves
        as watchdog for the serial connection.

        """
        loop = asyncio.get_running_loop()
        (
            self.transport,
            self.protocol,
        ) = await serial_asyncio.create_serial_connection(
            loop,
            lambda: serial_handler(self.coordinator),
            self.com_port,
            baudrate=self.baudrate,
        )
        _LOGGER.info("Serial connection established on %s", self.com_port)
        await self._tetra_initialize()

    async def _periodic_connection_check(self):
        """Continuously ensure serial connection.

        Permanently checking the serial connection every SLEEP_TIME_CONNECTION_CHECK seconds.
        If the connection is lost, it will try to reconnect.
        Reconnect attempts are made every SLEEP_TIME_RETRY seconds, up to MAX_RETRY_ATTEMPTS times.

        """
        while True:
            if self.transport is None or self.transport.is_closing():
                self.helpers.update_connection_status(2)
                if MAX_RETRY_ATTEMPTS == 0:
                    await self._retry_connect_infinite()
                else:
                    await self._retry_connect_limited()
                    break
            await asyncio.sleep(SLEEP_TIME_CONNECTION_CHECK)

    async def _retry_connect_infinite(self):
        """Retry connection infinitely until successful."""
        attempt = 0
        while True:
            try:
                await self._connect()
                if self.transport and not self.transport.is_closing():
                    self.helpers.update_connection_status(1)
                    break
            except (serial.SerialException, OSError, ValueError) as e:
                _LOGGER.warning("Connection attempt %d failed: %s", attempt, e)
            attempt += 1
            await asyncio.sleep(SLEEP_TIME_RETRY)

    async def _retry_connect_limited(self):
        """Retry connection up to MAX_RETRY_ATTEMPTS times."""
        for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
            try:
                await self._connect()
                if self.transport and not self.transport.is_closing():
                    self.helpers.update_connection_status(1)
                    return
            except (serial.SerialException, OSError, ValueError) as e:
                _LOGGER.warning("Connection attempt %d failed: %s", attempt, e)
            await asyncio.sleep(SLEEP_TIME_RETRY)
        self.helpers.update_connection_status(3)
        _LOGGER.error(
            "Abort reconnecting after %s retries and %s seconds, please check the connection",
            MAX_RETRY_ATTEMPTS,
            MAX_RETRY_ATTEMPTS * SLEEP_TIME_RETRY,
        )

    async def _tetra_initialize(self):
        """Initialize TETRA device for specific CTSP-Services."""
        # these commands are standard TETRA commands, which every device should respond to
        if not self.transport:
            _LOGGER.warning(
                "No serial connection available, initializing TETRA device failed"
            )
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


class serial_handler(asyncio.Protocol):
    """Handles serial connection incl incoming data."""

    def __init__(self, coordinator) -> None:
        """Initialize the data handler."""
        self.coordinator = coordinator
        self.raw_data = b""

        self.motorola = Motorola(coordinator)
        self.helpers = TetraControlHelpers(coordinator)

    def connection_made(self, transport):
        """Handle the connection being made."""
        self.transport = transport
        _LOGGER.debug("Serial connection opened")
        self.helpers.update_connection_status(1)

    def data_received(self, data):
        """Handle incoming data."""
        self.raw_data += data
        _LOGGER.debug("Raw data received: %s", data)

        remaining = b""

        try:
            if self.coordinator.manufacturer == "Motorola":
                remaining = self.motorola.data_handler(self.raw_data)

            #################################################
            ### Add other manufacturers data handler here ###
            #################################################

            else:
                _LOGGER.error(
                    "Unsupported manufacturer: %s", self.coordinator.manufacturer
                )
                return

            # put remaining data back into raw_data
            self.raw_data = remaining

            # TODO
            # add MQTT publish here and check if mqtt publishing or entity creation is needed

        except (ValueError, TypeError, serial.SerialException) as e:
            _LOGGER.error("Error processing incoming data: %s", e)

    def connection_lost(self, exc):
        """Handle the connection being lost."""
        _LOGGER.warning("Serial connection lost: %s", exc)
        self.helpers.update_connection_status(3)
