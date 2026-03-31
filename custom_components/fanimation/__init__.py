"""Fanimation BLE Fan integration for Home Assistant.

Controls Fanimation ceiling fans via Bluetooth Low Energy.
Provides fan speed (Off/Low/Med/High) and downlight brightness (0-100%).
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .device import FanimationDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.FAN, Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fanimation from a config entry."""
    address = entry.data[CONF_ADDRESS]
    device = FanimationDevice(address)

    # Try to get initial state (non-critical if it fails)
    try:
        await device.get_status()
    except Exception:
        _LOGGER.warning(
            "Could not get initial status from %s; will retry on first command",
            address,
        )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"device": device}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Fanimation config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
