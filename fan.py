import logging

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import DeviceType
from .base import ToyamaBaseEntity
from .const import DOMAIN, SPEED_MAP
from .controller import ToyamaDevice

_LOGGER = logging.getLogger(__name__)


SPEED_MAP_REVERSED = {v: k for k, v in SPEED_MAP.items()}


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Toyama fans."""
    controller = hass.data.get(DOMAIN)
    if not controller:
        _LOGGER.error("Toyama controller not found.")
        return
    devices = controller.devices
    fans = [ToyamaFan(device)
            for device in devices if device.type == DeviceType.FAN]
    async_add_entities(fans, update_before_add=True)


class ToyamaFan(FanEntity, ToyamaBaseEntity):
    """Representation of a Toyama Fan."""

    _attr_supported_features = FanEntityFeature.SET_SPEED

    def __init__(self, device: ToyamaDevice):
        """Initialize the fan."""
        self._device = device
        self._device.set_callback(self._handle_update)
        self.last_state = None

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
        try:
            if percentage:
                await self.async_set_percentage(percentage)
            elif self.last_state:
                await self._device.set_speed(self.last_state)
            else:
                await self._device.on()
        except Exception as e:
            _LOGGER.error(f"Failed to turn on fan {self._device.name}: {e}")

    async def async_turn_off(self, **kwargs):
        """Turn the fan off."""
        try:
            self.last_state = self._device.state
            await self._device.off()
        except Exception as e:
            _LOGGER.error(f"Failed to turn off fan {self._device.name}: {e}")

    async def async_set_percentage(self, percentage: int):
        """Set the speed percentage of the fan."""
        value = max(
            (key for key in SPEED_MAP if key <= percentage), default=0)
        try:
            await self._device.set_speed(value)
        except Exception as e:
            _LOGGER.error(f"Failed to set speed for fan {
                          self._device.name}: {e}")

    def _handle_update(self, new_state):
        """Handle state updates from the device."""
        self._device.state = SPEED_MAP_REVERSED[new_state]
        _LOGGER.debug(f"{self._device.name} changed state to {
                      self._device.state}")
        self.async_write_ha_state()