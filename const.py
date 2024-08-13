from dataclasses import dataclass
from enum import StrEnum


class DeviceType(StrEnum):
    SWITCH = "onoff"
    FAN = "dimmer"

@dataclass
class Device:
    """API device."""
    device_id: int
    mac_id: str
    room: str
    device_unique_id: str
    device_type: DeviceType
    name: str
    state: int | bool

DOMAIN = "toyama"
TOYAMA_API_HOST = "https://api.toyamaworld.com"

PLATFORMS = [
    "switch",
    "fan"
]