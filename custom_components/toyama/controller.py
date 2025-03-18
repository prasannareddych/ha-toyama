import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta

from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.components.zeroconf import async_get_instance
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change

from toyama_api.gateway import GatewayDevice, GatewayHandler

from .const import DISCOVERY_SERVICE_NAME

_LOGGER = logging.getLogger(__name__)

class ToyamaController:
    """Setup the devices and manage them"""
    gateway_handler: GatewayHandler
    devices: List[GatewayDevice] = []
    device_dict: Dict[str, GatewayDevice] = {}

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        self.hass = hass
        self.config_entry = config_entry
        self.tasks: List[asyncio.Task[Any]] = []
        self.cancel_ip_check = async_track_time_interval(self.hass, self.periodic_ip_check, timedelta(minutes=1))

    async def setup_devices(self):
        host_ip = self.config_entry.data.get("host")
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
        for device in self.config_entry.data.get("device_data"):
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

    async def periodic_ip_check(self, now):
        """Periodically check and update the device IP if necessary."""
        _LOGGER.debug("Checking for IP address change.")
        toyama_ip = await self._get_toyama_ip()

        if toyama_ip and toyama_ip != self.config_entry.data.get("host"):
            _LOGGER.info(f"IP address has changed to {toyama_ip}. Reconfiguring.")
            updated_data = dict(self.config_entry.data)
            updated_data["host"] = toyama_ip
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=updated_data
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            await self.stop()
            await self.setup_devices()
            await self.gateway_handler.request_all_devices_status()

    async def _get_toyama_ip(self) -> Optional[str]:
        """Detect the IP address using Zeroconf."""
        _LOGGER.debug("Searching for device IP using Zeroconf")
        service_type = DISCOVERY_SERVICE_NAME
        service_name = ""
        try:
            zeroconf = await async_get_instance(self.hass)
            discovery_data = self.config_entry.discovery_keys["zeroconf"]
            for discovery_key in discovery_data:
                for key in discovery_key.key:
                    if key != service_type:
                        service_name = key
            if not discovery_data:
                _LOGGER.debug("No zeroconf discovery keys found in config entry")
                return None
            info = await self.hass.async_add_executor_job(
                zeroconf.get_service_info,
                service_type,
                service_name
            )
            if info:
                if info.addresses:
                    ip_address = info.addresses[0]
                    ip_str = ".".join(str(b) for b in ip_address)
                    _LOGGER.debug(f"Found device with IP: {ip_str}")
                    return ip_str
                else:
                    _LOGGER.debug("Device found but no IP address available")
            else:
                _LOGGER.debug("No devices found for service type: %s", service_type)
        except Exception as e:
            _LOGGER.error(f"Error discovering device IP: {e}")
        return None
