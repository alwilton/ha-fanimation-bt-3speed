"""Light entity for Fanimation BLE integration (downlight)."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.color import (
    brightness_to_value,
    value_to_brightness,
)

from .const import DOMAIN
from .device import FanimationDevice
from .protocol import FanState, build_control_command

_LOGGER = logging.getLogger(__name__)

# Fan uses 0-100 for downlight brightness; HA uses 1-255
BRIGHTNESS_RANGE = (1, 100)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fanimation light entity from a config entry."""
    device: FanimationDevice = hass.data[DOMAIN][entry.entry_id]["device"]
    async_add_entities([FanimationLight(device, entry)])


class FanimationLight(LightEntity):
    """Representation of the Fanimation fan's downlight."""

    _attr_has_entity_name = True
    _attr_name = "Light"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(
        self, device: FanimationDevice, entry: ConfigEntry
    ) -> None:
        """Initialize the light entity."""
        self._device = device
        self._address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{self._address}_light"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._address)},
            "name": f"Fanimation Fan ({self._address[-8:]})",
            "manufacturer": "Fanimation",
            "model": "BLE Ceiling Fan",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the light is on."""
        state = self._device.state
        return state.light_is_on if state else None

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the light (HA scale: 1-255)."""
        state = self._device.state
        if state is None or state.downlight == 0:
            return None
        return value_to_brightness(BRIGHTNESS_RANGE, state.downlight)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light, optionally setting brightness."""
        if ATTR_BRIGHTNESS in kwargs:
            ha_brightness = kwargs[ATTR_BRIGHTNESS]
            device_brightness = round(
                brightness_to_value(BRIGHTNESS_RANGE, ha_brightness)
            )
        else:
            # If turning on without brightness, use 100% or restore last level
            state = self._device.state
            if state and state.downlight > 0:
                device_brightness = state.downlight
            else:
                device_brightness = 100

        await self._set_brightness(device_brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self._set_brightness(0)

    async def _set_brightness(self, level: int) -> None:
        """Send a downlight brightness command to the fan."""
        level = max(0, min(100, level))
        current = self._device.state or FanState(0, 0, 0, 0)
        command = build_control_command(current, downlight=level)
        state = await self._device.send_with_retry(
            command,
            expected_check=lambda s: s.downlight == level,
        )
        if state:
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Poll the fan for current state."""
        await self._device.get_status()
