"""BLE communication with Fanimation fan devices.

Uses bleak for BLE and follows a connect-per-command pattern:
connect → subscribe → write → wait for response → disconnect.
This matches how the real fanSync app works and avoids locking
out other controllers (iPhone app, etc.).
"""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak_retry_connector import establish_connection, BleakNotFoundError

from .const import (
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    NOTIFY_CHAR_UUID,
    RETRY_DELAY,
    SERVICE_UUID,
    WRITE_CHAR_UUID,
)
from .protocol import FanState, build_status_request, parse_response

_LOGGER = logging.getLogger(__name__)


class FanimationDevice:
    """Manages BLE communication with a single Fanimation fan."""

    def __init__(self, address: str) -> None:
        """Initialize with the fan's BLE MAC address."""
        self.address = address
        self._state: FanState | None = None
        self._lock = asyncio.Lock()

    @property
    def state(self) -> FanState | None:
        """Last known fan state."""
        return self._state

    async def send_command(
        self,
        command: bytes,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> FanState | None:
        """Connect to the fan, send a command, wait for response, disconnect.

        Returns the parsed FanState from the response, or None on failure.
        """
        async with self._lock:
            return await self._send_command_locked(command, timeout)

    async def _send_command_locked(
        self,
        command: bytes,
        timeout: float,
    ) -> FanState | None:
        """Send command while holding the lock."""
        response_event = asyncio.Event()
        response_data: bytearray | None = None

        def on_notify(_char, data: bytearray) -> None:
            nonlocal response_data
            response_data = data
            response_event.set()

        client: BleakClient | None = None
        try:
            client = BleakClient(self.address)
            await client.connect(timeout=timeout)

            # Verify the fan service exists
            services = client.services
            if not services or not services.get_service(SERVICE_UUID):
                _LOGGER.warning(
                    "Service %s not found on %s", SERVICE_UUID, self.address
                )
                return None

            # Subscribe to notifications
            await client.start_notify(NOTIFY_CHAR_UUID, on_notify)

            # Send command
            await client.write_gatt_char(
                WRITE_CHAR_UUID, command, response=True
            )

            # Wait for response
            try:
                await asyncio.wait_for(response_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "Response timeout (%ss) from %s", timeout, self.address
                )
                return None

            if response_data is None:
                return None

            state = parse_response(response_data)
            if state is not None:
                self._state = state
                _LOGGER.debug(
                    "Fan %s: speed=%s downlight=%d%%",
                    self.address,
                    state.speed_name,
                    state.downlight,
                )
            return state

        except BleakNotFoundError:
            _LOGGER.warning("Fan %s not found (BLE)", self.address)
            return None
        except Exception:
            _LOGGER.exception("BLE error communicating with %s", self.address)
            return None
        finally:
            if client and client.is_connected:
                try:
                    await client.disconnect()
                except Exception:
                    _LOGGER.debug("Error disconnecting from %s", self.address)

    async def send_with_retry(
        self,
        command: bytes,
        expected_check: callable | None = None,
        retries: int = DEFAULT_RETRIES,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> FanState | None:
        """Send a command with retries. Optionally verify the response matches expectations.

        Args:
            command: The 10-byte command packet.
            expected_check: Optional callable(FanState) -> bool to verify response.
            retries: Max number of attempts.
            timeout: Per-attempt timeout in seconds.

        Returns:
            The confirmed FanState, or None if all attempts failed.
        """
        for attempt in range(retries):
            state = await self.send_command(command, timeout=timeout)
            if state is not None:
                if expected_check is None or expected_check(state):
                    return state
                _LOGGER.debug(
                    "Attempt %d: response didn't match expected state",
                    attempt + 1,
                )
            if attempt < retries - 1:
                await asyncio.sleep(RETRY_DELAY)

        _LOGGER.warning(
            "All %d attempts failed for %s", retries, self.address
        )
        return None

    async def get_status(self) -> FanState | None:
        """Query the fan's current state."""
        return await self.send_command(build_status_request())
