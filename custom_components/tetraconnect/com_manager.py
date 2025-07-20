# custom_components/tetraconnectom_manager.py

import asyncio
import contextlib
import logging

import serial
import serial_asyncio

from .const import (
    MAX_RETRY_ATTEMPTS,
    SLEEP_TIME_CONNECTION_CHECK,
    SLEEP_TIME_RETRY,
    TETRA_DEFAULTS,
)
from .helpers import TetraconnectHelpers
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
        self._tetra_defaults = TETRA_DEFAULTS.copy()
        self._connection_check_task = None

        self.helpers = TetraconnectHelpers(coordinator)

    async def serial_initialize(self, hass):
        """Start monitoring and connection loop."""
        self._connection_check_task = hass.loop.create_task(
            self._periodic_connection_check()
        )

    async def serial_stop(self):
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
            lambda: SerialHandler(self.coordinator),
            self.com_port,
            baudrate=self.baudrate,
        )
        self.helpers.update_connection_status(1)
        _LOGGER.info("Serial connection established on %s", self.com_port)
        # await self._tetra_initialize()

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

    async def tetra_initialize(self):
        """Initialize TETRA device for specific CTSP-Services.

        Initialize the device for TETRA services by sending standard AT commands.
        Wait for the answer on each command and log an error if the command fails.
        This will not create any entities, its just for device initialization.

        Device information like model, sw-version, revision, manufacturer were
        already requested in the config flow, so we do not request them again here.

        """
        # these commands are standard TETRA commands, which every device should respond to

        _LOGGER.info("##### Initializing TETRA services on %s #####", self.com_port)

        if not self.transport:
            for _ in range(5):
                await asyncio.sleep(0.2)
                if self.transport:
                    break
            else:
                _LOGGER.warning(
                    "No serial connection available, initializing TETRA device failed"
                )
                return

        raw_data = {}

        # +CTSP=<service profile>, <service layer1>, [<service layer2>], [<AI mode>], [<link identifier>]
        service_commands = [
            # "AT+CTSP=1,2,20\r\n",  # Status TE
            "AT+CTSP=2,2,20\r\n",  # Status MT & TE
            "AT+CTSP=1,3,130\r\n",  # Textnachrichten einschalten
            "AT+CTSP=1,3,131\r\n",  # GPS einschalten
            "AT+CTSP=1,3,10\r\n",  # Status GPS
            "AT+CTSP=1,3,137\r\n",  # Immediate Text
            "AT+CTSP=1,3,138\r\n",  # Alarm
            # "AT+CTSP=2,0\r\n",
            # "AT+CTSP=2,1\r\n",
            # "AT+CTSP=2,2\r\n",
            # "AT+CTSP=2,3\r\n",
            # "AT+CTSP=2,4\r\n",
        ]

        for cmd in service_commands:
            _LOGGER.debug("Sending service profile command: %s", cmd.strip())
            if self.protocol is not None:
                self.protocol.expect_response = True
                self.protocol.response_future = (
                    asyncio.get_running_loop().create_future()
                )
                self.transport.write(cmd.encode())
                await asyncio.sleep(0.1)
                _LOGGER.debug("Waiting for response to command: %s", cmd.strip())
                try:
                    response = await asyncio.wait_for(
                        self.protocol.response_future, timeout=5
                    )
                    self.protocol.expect_response = False
                    raw_data[cmd] = response
                except asyncio.TimeoutError:
                    _LOGGER.error(
                        "Timeout while waiting for response to command: %s", cmd.strip()
                    )
                    raw_data[cmd] = b"CME ERROR: response timeout"
            else:
                _LOGGER.warning(
                    "Service profile not initialized, cannot send command: %s",
                    cmd.strip(),
                )

        # check responses
        for cmd, resp in raw_data.items():
            if resp != b"\r\nOK\r\n":
                _LOGGER.warning(
                    "Service profile command '%s' failed with response: %s",
                    cmd.strip().replace("\r\n", ""),
                    resp.decode("utf-8").strip().replace("\r\n", ""),
                )

        _LOGGER.info(
            "##### TETRA services initialized successfully on %s #####", self.com_port
        )


class SerialHandler(asyncio.Protocol):
    """Handles serial connection incl incoming data."""

    def __init__(self, coordinator) -> None:
        """Initialize the data handler."""
        self.coordinator = coordinator
        self.raw_data = b""

        self.motorola = Motorola(coordinator)
        self.helpers = TetraconnectHelpers(coordinator)
        self.expect_response = False
        self.response_future = None

    def connection_made(self, transport):
        """Handle the connection being made."""
        self.transport = transport
        _LOGGER.debug("Serial connection opened")

    def data_received(self, data):
        """Handle incoming data."""
        self.raw_data += data
        _LOGGER.debug("Raw data received: %s", data)

        remaining = b""

        # check if expected response is set
        if self.expect_response:
            # Set result only if not already done
            if self.response_future is not None and not self.response_future.done():
                self.response_future.set_result(data)
        else:
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
                _LOGGER.debug("Remaining data after processing: %s", remaining)

                # TODO
                # add MQTT publish here and check if mqtt publishing or entity creation is needed

            except (ValueError, TypeError, serial.SerialException) as e:
                _LOGGER.error("Error processing incoming data: %s", e)

    def connection_lost(self, exc):
        """Handle the connection being lost."""
        _LOGGER.warning("Serial connection lost: %s", exc)
        self.helpers.update_connection_status(3)
