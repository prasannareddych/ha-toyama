import asyncio
import logging
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from toyama_api.gateway import GatewayDevice, GatewayHandler

_LOGGER = logging.getLogger(__name__)


class ToyamaController:
    """Setup the devices and manage them"""
    gateway_handler: GatewayHandler
    devices: List[GatewayDevice] = []
    device_dict: Dict[str, GatewayDevice] = {}

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.hass = hass
        self.config_data = config_entry.data
        self.tasks: asyncio.Task[Any] = []

    async def setup_devices(self):
        host_ip = self.config_data.get("host")
        self.gateway_handler = GatewayHandler(
            gateway_ip=host_ip,
            callback_func=self.handle_state_updates
        )
        self.tasks.append(
            self.hass.loop.create_task(
                self.gateway_handler.listen_device_updates()
            )
        )
        self.tasks.append(
            self.hass.loop.create_task(
                self.gateway_handler.ping_gateway()
            )
        )
        self.clear_devices()
        _LOGGER.info("starting device setup")
        for device in self.config_data.get("device_data"):
            gateway_device = GatewayDevice(**device)
            gateway_device.set_gateway_handler(self.gateway_handler)
            unique_id = f"{gateway_device.board_id}_{gateway_device.parsed_button_id}"
            self.device_dict[unique_id] = gateway_device
            self.devices.append(gateway_device)
        _LOGGER.debug(f"{len(self.devices)} devices found")

    def clear_devices(self):
        """Clear existing devices to avoid duplication."""
        self.devices = []
        self.device_dict = {}

    async def stop(self):
        """Stop the Toyama controller and clean up resources."""
        self.clear_devices()
        for task in self.tasks:
            task.cancel()

    def handle_state_updates(self, board_id: str, button_id: int, state: int) -> None:
        """Handle the device update."""
        unique_id = f"{board_id}_{button_id}"
        gateway_device = self.device_dict.get(unique_id)
        if gateway_device and gateway_device.callback:
            gateway_device.callback(state)
