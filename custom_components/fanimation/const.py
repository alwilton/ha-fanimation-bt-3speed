"""Constants for the Fanimation BLE fan integration."""

DOMAIN = "fanimation"

# BLE Service and Characteristic UUIDs
SERVICE_UUID = "0000e000-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID = "0000e001-0000-1000-8000-00805f9b34fb"
NOTIFY_CHAR_UUID = "0000e002-0000-1000-8000-00805f9b34fb"

# Protocol constants
START_BYTE = 0x53  # 'S'

# Command types
CMD_GET_STATUS = 0x30
CMD_CONTROL = 0x31
CMD_RETURN_STATUS = 0x32

# Fan speed values
SPEED_OFF = 0
SPEED_LOW = 1
SPEED_MED = 2
SPEED_HIGH = 3

# Preset mode names (matching HA convention)
PRESET_LOW = "Low"
PRESET_MEDIUM = "Medium"
PRESET_HIGH = "High"
PRESET_MODES = [PRESET_LOW, PRESET_MEDIUM, PRESET_HIGH]

# Speed <-> preset mapping
SPEED_TO_PRESET = {
    SPEED_LOW: PRESET_LOW,
    SPEED_MED: PRESET_MEDIUM,
    SPEED_HIGH: PRESET_HIGH,
}
PRESET_TO_SPEED = {v: k for k, v in SPEED_TO_PRESET.items()}

# BLE communication
DEFAULT_TIMEOUT = 3.0  # seconds
DEFAULT_RETRIES = 2
RETRY_DELAY = 0.3  # seconds between retries

# Fan type (AC standard)
FAN_TYPE_AC = 0
