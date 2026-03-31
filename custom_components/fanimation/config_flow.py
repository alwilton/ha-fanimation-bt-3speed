"""Config flow for Fanimation BLE fan integration.

Supports two setup paths:
1. Automatic BLE discovery (HA detects the fan advertising service 0xE000)
2. Manual MAC address entry
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)


class FanimationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fanimation fan."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._address: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle Bluetooth discovery of a Fanimation fan."""
        _LOGGER.debug(
            "Bluetooth discovery: %s (%s)",
            discovery_info.name,
            discovery_info.address,
        )

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info
        self._address = discovery_info.address

        self.context["title_placeholders"] = {
            "name": discovery_info.name or "Fanimation Fan"
        }

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm Bluetooth discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.context.get("title_placeholders", {}).get(
                    "name", "Fanimation Fan"
                ),
                data={CONF_ADDRESS: self._address},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovery_info.name
                if self._discovery_info
                else "Fanimation Fan"
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual setup - user enters MAC address."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS].strip().upper()

            # Basic MAC format validation
            if not self._validate_mac(address):
                errors["base"] = "invalid_mac"
            else:
                # Check if already configured
                await self.async_set_unique_id(address)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Fanimation Fan ({address[-8:]})",
                    data={CONF_ADDRESS: address},
                )

        # Check if any Fanimation fans are already visible via BLE
        discovered = self._get_discovered_fans()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "discovered": ", ".join(discovered) if discovered else "none"
            },
        )

    def _get_discovered_fans(self) -> list[str]:
        """Get list of Fanimation fans currently visible via BLE."""
        fans = []
        for info in async_discovered_service_info(self.hass):
            if SERVICE_UUID.lower() in [
                str(u).lower() for u in info.service_uuids
            ]:
                label = f"{info.name or 'Unknown'} ({info.address})"
                fans.append(label)
        return fans

    @staticmethod
    def _validate_mac(mac: str) -> bool:
        """Validate a MAC address format (AA:BB:CC:DD:EE:FF)."""
        parts = mac.replace("-", ":").split(":")
        if len(parts) != 6:
            return False
        try:
            for part in parts:
                if len(part) != 2:
                    return False
                int(part, 16)
            return True
        except ValueError:
            return False
