import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL, VERSION
from toyama_api.gateway import SPEED_MAP, GatewayDevice

_LOGGER = logging.getLogger(__name__)


SPEED_MAP_REVERSED = {v: k for k, v in SPEED_MAP.items()}


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Toyama fans."""
    controller = hass.data.get(DOMAIN)
    if not controller:
        _LOGGER.error("Toyama controller not found.")
        return
    devices = controller.devices
    fans = [
        ToyamaFan(device) for device in devices if device.is_fan
    ]
    async_add_entities(fans, update_before_add=True)


class ToyamaFan(FanEntity):
    """Representation of a Toyama Fan."""

    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )

    def __init__(self, device: GatewayDevice):
        """Initialize the fan."""
        self._device = device
        self._device.set_callback(self._handle_update)
        self.last_state = None
        self.entity_id = f"fan.{device.room}.{device.name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self._device.name,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=VERSION,
            suggested_area=self._device.room,
            identifiers={
                (
                    DOMAIN,
                    self._device.room,
                    self._device.name,
                )
            },
        )

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return self._device.unique_id

    @property
    def name(self) -> str:
        """Return the name of the fan."""
        return self._device.name

    @property
    def available(self) -> bool:
        """Return if the fan entity is available."""
        return self._device.gateway_handler.connected

    @property
    def is_on(self) -> bool:
        """Return true if the fan is on."""
        return self._device.state > 0

    @property
    def percentage(self) -> int:
        """Return the current speed percentage of the fan."""
        # Assuming the state is a value from 0-100 representing speed percentage
        return self._device.state

    async def async_turn_on(self, preset_mode: str = None, percentage: int = None, **kwargs):
        """Turn the fan on."""
        updated = False
        if percentage:
            updated = await self.async_set_percentage(percentage)
        elif self.last_state:
            updated = await self._device.set_speed(self.last_state)
        else:
            updated = await self._device.on()
        if not updated:
            _LOGGER.error(f"Failed to turn on fan {self._device.name}")

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        self.last_state = self._device.state
        if not await self._device.off():
            _LOGGER.error(f"Failed to turn off fan {self._device.name}")

    async def async_set_percentage(self, percentage: int):
        """Set the speed percentage of the fan."""
        value = max(
            (key for key in SPEED_MAP if key <= percentage), default=0)
        if not await self._device.set_speed(value):
            _LOGGER.error(f"Failed to set speed for fan {self._device.name}")

    def _handle_update(self, new_state):
        """Handle state updates from the device."""
        new_state = SPEED_MAP_REVERSED[new_state]
        if self._device.state != new_state:
            self._device.state = new_state
            _LOGGER.debug(f"{self._device.name} changed state to {self._device.state}")
            self.async_write_ha_state()
