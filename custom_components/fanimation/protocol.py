"""Fanimation BLE protocol - packet building and parsing.

Ported from FanimationProtocol.cs. The fan uses 10-byte packets:
[0x53, CmdType, Speed, Dir, Uplight, Downlight, TimerLo, TimerHi, FanType, Checksum]
"""

from __future__ import annotations

from dataclasses import dataclass

from .const import (
    CMD_CONTROL,
    CMD_GET_STATUS,
    FAN_TYPE_AC,
    START_BYTE,
)


@dataclass
class FanState:
    """Current state of the fan as reported by the device."""

    speed: int
    direction: int
    uplight: int
    downlight: int
    fan_type: int = 0

    @property
    def speed_name(self) -> str:
        """Human-readable speed name."""
        return {0: "Off", 1: "Low", 2: "Medium", 3: "High"}.get(
            self.speed, f"Speed {self.speed}"
        )

    @property
    def is_on(self) -> bool:
        """Whether the fan motor is running."""
        return self.speed > 0

    @property
    def light_is_on(self) -> bool:
        """Whether the downlight is on."""
        return self.downlight > 0


def _checksum(cmd: bytes | bytearray) -> int:
    """Calculate checksum: sum of bytes 0-8, masked to 0xFF."""
    return sum(cmd[:9]) & 0xFF


def build_command(
    cmd_type: int,
    speed: int = 0,
    direction: int = 0,
    uplight: int = 0,
    downlight: int = 0,
    timer_lo: int = 0,
    timer_hi: int = 0,
    fan_type: int = FAN_TYPE_AC,
) -> bytes:
    """Build a 10-byte Fanimation command packet."""
    cmd = bytearray(10)
    cmd[0] = START_BYTE
    cmd[1] = cmd_type
    cmd[2] = speed
    cmd[3] = direction
    cmd[4] = uplight
    cmd[5] = downlight
    cmd[6] = timer_lo
    cmd[7] = timer_hi
    cmd[8] = fan_type
    cmd[9] = _checksum(cmd)
    return bytes(cmd)


def build_status_request() -> bytes:
    """Build a GetFanStatus request packet."""
    return build_command(CMD_GET_STATUS)


def build_control_command(
    current: FanState,
    speed: int | None = None,
    direction: int | None = None,
    uplight: int | None = None,
    downlight: int | None = None,
) -> bytes:
    """Build a ControlFanStatus command, preserving current state for unchanged fields."""
    return build_command(
        CMD_CONTROL,
        speed=speed if speed is not None else current.speed,
        direction=direction if direction is not None else current.direction,
        uplight=uplight if uplight is not None else current.uplight,
        downlight=downlight if downlight is not None else current.downlight,
        fan_type=current.fan_type,
    )


def parse_response(data: bytes | bytearray) -> FanState | None:
    """Parse a 10-byte response from the fan. Returns None if invalid."""
    if len(data) < 10 or data[0] != START_BYTE:
        return None
    return FanState(
        speed=data[2],
        direction=data[3],
        uplight=data[4],
        downlight=data[5],
        fan_type=data[8],
    )
