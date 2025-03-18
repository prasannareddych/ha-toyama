"""Toyama World Integration"""
from __future__ import annotations
import asyncio
import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, PLATFORMS, DISCOVERY_SERVICE_NAME
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
    try:
        await controller.gateway_handler.request_all_devices_status()
    except asyncio.TimeoutError:
        _LOGGER.error("Toyama devices status request failed.")
        
    _LOGGER.debug("Toyama component setup complete.")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    controller = hass.data.get(DOMAIN)
    await controller.stop()
    controller.cancel_ip_check()
    hass.data.pop(DOMAIN)

    unload_success = True
    for platform in PLATFORMS:
        if not await hass.config_entries.async_forward_entry_unload(entry, platform):
            unload_success = False

    _LOGGER.debug("Toyama component unloaded.")
    return unload_success


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    _LOGGER.error("Reloading the entry")
    await hass.config_entries.async_reload(entry.entry_id)
