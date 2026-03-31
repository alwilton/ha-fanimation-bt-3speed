# Fanimation BLE Fan Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Control your Fanimation Bluetooth ceiling fan from Home Assistant.

## Features

- **Fan speed control**: Off, Low, Medium, High (preset modes + percentage slider)
- **Downlight brightness**: 0-100% dimming
- **BLE auto-discovery**: Automatically detects Fanimation fans advertising service UUID `0xE000`
- **Connect-per-command**: Connects briefly to send commands, then disconnects — won't lock out the fanSync phone app
- **Retry with verification**: Commands are verified against the fan's response and retried if needed

## Requirements

- Home Assistant 2024.1.0 or later
- Bluetooth adapter on the HA machine (built-in on most Raspberry Pi models)
- HA machine within BLE range (~10m) of the fan

## Installation via HACS

1. Open HACS in your Home Assistant
2. Click the **three dots menu** (top right) → **Custom repositories**
3. Add repository URL: `https://github.com/alwilton/ha-fanimation`
4. Category: **Integration**
5. Click **Add**, then find "Fanimation Fan" in HACS and click **Download**
6. **Restart Home Assistant**

## Setup

After restart:

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **"Fanimation Fan"**
3. Either:
   - **Auto-discovered**: If HA detected the fan via BLE, confirm the setup
   - **Manual**: Enter the fan's BLE MAC address (e.g., `E0:E5:CF:28:81:30`)

## Entities Created

| Entity | Type | Controls |
|--------|------|----------|
| Fan | `fan` | On/Off, Speed (Low/Medium/High), Percentage slider |
| Light | `light` | On/Off, Brightness (0-100%) |

Both entities appear under a single device in HA.

## Protocol

This integration communicates with Fanimation fans using their BLE GATT protocol:

- **Service UUID**: `0000e000-0000-1000-8000-00805f9b34fb`
- **Write characteristic**: `0000e001-...` (commands to fan)
- **Notify characteristic**: `0000e002-...` (responses from fan)
- **Packet format**: 10 bytes `[0x53, CmdType, Speed, Dir, Uplight, Downlight, TimerLo, TimerHi, FanType, Checksum]`

Protocol was reverse-engineered from the fanSync Android APK.

## Supported Fans

Tested with AC Standard (3-speed) Fanimation fans with a downlight. Other Fanimation BLE fans using the same `0xE000` service should also work.

## Troubleshooting

- **Fan not discovered**: Ensure the HA machine has Bluetooth and is within range. Check HA logs for BLE errors.
- **Commands fail intermittently**: BLE can be flaky. The integration retries commands automatically. Make sure no other device (phone app) is connected to the fan at the same time.
- **"Cannot connect" during setup**: Power-cycle the fan, then try again. The fan's BLE radio may need a reset.
