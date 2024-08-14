import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import DeviceType
from .base import ToyamaBaseEntity
from .const import DOMAIN
from .controller import ToyamaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Toyama switches."""
    controller = hass.data.get(DOMAIN)
    if not controller:
        _LOGGER.error("Toyama controller not found.")
        return
    devices = controller.devices
    switches = [ToyamaSwitch(device)
                for device in devices if device.type == DeviceType.SWITCH]
    async_add_entities(switches, update_before_add=True)


class ToyamaSwitch(SwitchEntity, ToyamaBaseEntity):
    """Representation of a Toyama Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, device: ToyamaDevice):
        """Initialize the switch."""
        self._device = device
        self._device.set_callback(self._handle_update)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._device.state > 0

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        try:
            await self._device.on()
        except Exception as e:
            _LOGGER.error(f"Failed to turn on switch {self._device.name}: {e}")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        try:
            await self._device.off()
        except Exception as e:
            _LOGGER.error(f"Failed to turn off switch {
                          self._device.name}: {e}")

    def _handle_update(self, new_state):
        """Handle state updates from the device."""
        self._device.state = new_state
        _LOGGER.debug(f"{self._device.name} changed state to {new_state}")
        self.async_write_ha_state()
