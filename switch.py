import logging

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .api import DeviceType
from .const import DOMAIN
from .controller import ToyamaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Toyama switches."""
    controller = hass.data.get(DOMAIN)
    if not controller:
        _LOGGER.error("Toyama controller not found.")
        return
    devices = controller.devices
    switches = [ToyamaSwitch(device)
                for device in devices if device.type == DeviceType.SWITCH]
    async_add_entities(switches, update_before_add=True)


class ToyamaSwitch(SwitchEntity):
    """Representation of a Toyama Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, device: ToyamaDevice):
        """Initialize the switch."""
        self._device = device
        self._device.set_callback(self._handle_update)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            name=self._device.name,

            manufacturer="Toyama World",
            model="115",
            sw_version="0.0.1",
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
        """Return the name of the switch."""
        return self._device.name

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
