"""Fan entity for Fanimation BLE integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import (
    DOMAIN,
    PRESET_HIGH,
    PRESET_LOW,
    PRESET_MEDIUM,
    PRESET_MODES,
    PRESET_TO_SPEED,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_OFF,
    SPEED_TO_PRESET,
)
from .device import FanimationDevice
from .protocol import FanState, build_control_command, build_status_request

_LOGGER = logging.getLogger(__name__)

ORDERED_SPEEDS = [PRESET_LOW, PRESET_MEDIUM, PRESET_HIGH]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fanimation fan entity from a config entry."""
    device: FanimationDevice = hass.data[DOMAIN][entry.entry_id]["device"]
    async_add_entities([FanimationFan(device, entry)])


class FanimationFan(FanEntity):
    """Representation of a Fanimation BLE ceiling fan."""

    _attr_has_entity_name = True
    _attr_name = "Fan"
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_preset_modes = PRESET_MODES
    _attr_speed_count = 3

    def __init__(
        self, device: FanimationDevice, entry: ConfigEntry
    ) -> None:
        """Initialize the fan entity."""
        self._device = device
        self._address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{self._address}_fan"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._address)},
            "name": f"Fanimation Fan ({self._address[-8:]})",
            "manufacturer": "Fanimation",
            "model": "BLE Ceiling Fan",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the fan is on."""
        state = self._device.state
        return state.is_on if state else None

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        state = self._device.state
        if state is None:
            return None
        if state.speed == SPEED_OFF:
            return 0
        preset = SPEED_TO_PRESET.get(state.speed)
        if preset:
            return ordered_list_item_to_percentage(ORDERED_SPEEDS, preset)
        return None

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        state = self._device.state
        if state is None or state.speed == SPEED_OFF:
            return None
        return SPEED_TO_PRESET.get(state.speed)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        # Default: turn on at low speed
        await self._set_speed(SPEED_LOW)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        await self._set_speed(SPEED_OFF)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed as a percentage."""
        if percentage == 0:
            await self._set_speed(SPEED_OFF)
            return
        preset = percentage_to_ordered_list_item(ORDERED_SPEEDS, percentage)
        speed = PRESET_TO_SPEED[preset]
        await self._set_speed(speed)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the fan to a preset speed mode."""
        speed = PRESET_TO_SPEED.get(preset_mode)
        if speed is None:
            _LOGGER.error("Unknown preset mode: %s", preset_mode)
            return
        await self._set_speed(speed)

    async def _set_speed(self, speed: int) -> None:
        """Send a speed command to the fan."""
        current = self._device.state or FanState(0, 0, 0, 0)
        command = build_control_command(current, speed=speed)
        state = await self._device.send_with_retry(
            command,
            expected_check=lambda s: s.speed == speed,
        )
        if state:
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Poll the fan for current state."""
        await self._device.get_status()
