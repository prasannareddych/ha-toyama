import logging

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ToyamaBaseEntity:

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
                    self._device.unique_id,
                )
            },
        )

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        return self._device.unique_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._device.name
