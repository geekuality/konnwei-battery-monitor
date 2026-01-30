"""DataUpdateCoordinator for Konnwei Battery Monitor."""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Optional

from bleak import BleakClient
from bleak.exc import BleakError

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    BLE_RESPONSE_TIMEOUT,
    CHAR_NOTIFY_UUID,
    CHAR_WRITE_UUID,
    CMD_DEVICE_INFO,
    CMD_STATUS_POLL,
    DOMAIN,
)
from .protocol import parse_device_info_response, parse_status_response

_LOGGER = logging.getLogger(__name__)


class KonnweiCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for polling Konnwei battery monitor."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        poll_interval: int,
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance
            address: BLE MAC address of device
            poll_interval: Polling interval in seconds
        """
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{address}",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.address = address
        self._device_info: Optional[dict[str, str]] = None
        self._response_data: Optional[bytes] = None
        self._response_event: Optional[asyncio.Event] = None

    @property
    def device_info(self) -> dict[str, str]:
        """Return cached device info."""
        return self._device_info or {}

    def _notification_handler(self, sender: int, data: bytes) -> None:
        """Handle BLE notification callback.

        Args:
            sender: Characteristic handle
            data: Notification data
        """
        self._response_data = data
        if self._response_event:
            self._response_event.set()

    async def _fetch_device_info(self, client: BleakClient) -> None:
        """Fetch device information (model, firmware).

        Args:
            client: Connected BLE client

        Raises:
            UpdateFailed: If device info query fails
        """
        if self._device_info:
            return

        self._response_data = None
        self._response_event = asyncio.Event()

        await client.write_gatt_char(CHAR_WRITE_UUID, CMD_DEVICE_INFO)

        try:
            await asyncio.wait_for(self._response_event.wait(), timeout=BLE_RESPONSE_TIMEOUT)
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Device info query timeout") from err

        if not self._response_data:
            raise UpdateFailed("No device info response")

        info = parse_device_info_response(self._response_data)
        if not info:
            raise UpdateFailed("Invalid device info response")

        self._device_info = info
        _LOGGER.debug(
            "Device info: model=%s, hw=%s, fw=%s",
            info.get("model"),
            info.get("hw_version"),
            info.get("fw_version"),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll device for current status.

        Returns:
            Dict with voltage, battery_ok, and charging fields

        Raises:
            UpdateFailed: If device is unreachable or response is invalid
        """
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )

        if not ble_device:
            raise UpdateFailed(f"Device {self.address} not found")

        try:
            async with BleakClient(ble_device) as client:
                await client.start_notify(CHAR_NOTIFY_UUID, self._notification_handler)

                await self._fetch_device_info(client)

                self._response_data = None
                self._response_event = asyncio.Event()

                await client.write_gatt_char(CHAR_WRITE_UUID, CMD_STATUS_POLL)

                try:
                    await asyncio.wait_for(
                        self._response_event.wait(), timeout=BLE_RESPONSE_TIMEOUT
                    )
                except asyncio.TimeoutError as err:
                    raise UpdateFailed("Status poll timeout") from err

                if not self._response_data:
                    raise UpdateFailed("No status response")

                status = parse_status_response(self._response_data)
                if not status:
                    raise UpdateFailed("Invalid status response")

                _LOGGER.debug("Status: %s", status)
                return status

        except BleakError as err:
            raise UpdateFailed(f"BLE error: {err}") from err
        finally:
            self._response_event = None
