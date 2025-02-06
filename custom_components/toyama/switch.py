import logging
from typing import List

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from toyama_api.gateway import GatewayDevice

from .const import DOMAIN, MANUFACTURER, MODEL, VERSION

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Toyama switches."""
    controller = hass.data.get(DOMAIN)
    if not controller:
        _LOGGER.error("Toyama controller not found.")
        return
    devices: List[GatewayDevice] = controller.devices
    switches = [
        ToyamaSwitch(device) for device in devices if device.is_switch
    ]
    async_add_entities(switches, update_before_add=True)


class ToyamaSwitch(SwitchEntity):
    """Representation of a Toyama Switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, device: GatewayDevice):
        """Initialize the switch."""
        self._device = device
        self._device.set_callback(self._handle_update)
        self._attr_unique_id = device.unique_id
        self.entity_id = f"switch.{device.room}.{device.name}"

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
        """Return the name of the switch."""
        return self._device.name

    @property
    def available(self) -> bool:
        """Return if the switch entity is available."""
        return self._device.gateway_handler.connected

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._device.state > 0

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        if not await self._device.on():
            _LOGGER.error(f"Failed to turn on switch {self._device.name}")

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        if not await self._device.off():
            _LOGGER.error(f"Failed to turn off switch {self._device.name}")

    def _handle_update(self, new_state):
        """Handle state updates from the device."""
        if self._device.state != new_state:
            self._device.state = new_state
            _LOGGER.debug(f"{self._device.name} changed state to {new_state}")
            self.async_write_ha_state()
