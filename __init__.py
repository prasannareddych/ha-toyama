"""Toyama World Integration"""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS
from .controller import ToyamaController

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Toyama component."""
    _LOGGER.debug("Setting up Toyama component.")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Toyama from a config entry."""
    controller = ToyamaController(hass, entry)
    hass.data[DOMAIN] = controller

    async def stop_toyama_controller(event):
        """Stop the Toyama controller on Home Assistant shutdown."""
        await controller.stop()

    hass.bus.async_listen_once("homeassistant_stop", stop_toyama_controller)
    await controller.setup_devices()

    # Forward the entry setup to the platforms defined in const.PLATFORMS
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Start listening for device updates in the background
    hass.loop.create_task(controller.listen_device_updates())

    # Update the states in HA
    await controller.api.request_all_devices_status()

    _LOGGER.debug("Toyama component setup complete.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    controller = hass.data.get(DOMAIN)
    await controller.stop()
    hass.data.pop(DOMAIN)

    unload_success = True
    for platform in PLATFORMS:
        if not await hass.config_entries.async_forward_entry_unload(entry, platform):
            unload_success = False

    _LOGGER.debug("Toyama component unloaded.")
    return unload_success
