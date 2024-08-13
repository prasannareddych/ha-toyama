import asyncio
import json
import logging
import socket
from typing import Callable, Dict, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import ClientAPI, Device, DeviceType
from .discovery import discover

_LOGGER = logging.getLogger(__name__)


class ToyamaDevice(Device):
    api: ClientAPI = None
    callback: Callable[[int], None] = None

    def set_api(self, api: ClientAPI) -> None:
        self.api = api

    def set_callback(self, callback: Callable[[int], None]) -> None:
        self.callback = callback

    async def update_state(self, new_state: int) -> bool:
        if self.state == new_state:
            return True
        return await self.api.update_device_state(self, new_state)

    async def on(self) -> None:
        await self.update_state(100 if self.device_type == DeviceType.FAN else 1)

    async def off(self) -> None:
        await self.update_state(0)

    async def set(self, value: int) -> None:
        if self.device_type == DeviceType.FAN and value <= 4:
            _map = {0: 0, 1: 35, 2: 50, 3: 55, 4: 100}
            value = _map.get(value, value)
        elif value not in [0, 1] or value > 4:
            raise ValueError(f"Invalid value: {value}")
        await self.update_state(value)


class ToyamaController:
    """Setup the devices and manage them"""
    api: ClientAPI
    devices: List[ToyamaDevice] = []
    device_dict: Dict[str, Dict[int, ToyamaDevice]] = {}
    mesh_ip: str

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        device_info = config_entry.data['device_data']
        for zone in device_info:
            for room in zone.get('rooms', []):
                for board in room.get('boards', []):
                    for toggle in board['toggles']:
                        self.devices.append(
                            ToyamaDevice(
                                id=toggle[0],
                                name=toggle[2],
                                mac_id=board['mac_id'],
                                room=room['room_name'],
                                unique_id=f"{room['room_name']}_{
                                    board['mac_id']}_{toggle[0]}",
                                type=toggle[4],
                                state=0
                            )
                        )
        _LOGGER.debug(f"{len(self.devices)} devices found")

    async def setup_devices(self):
        self.mesh_ip = await discover()
        self.api = ClientAPI(self.mesh_ip)
        for device in self.devices:
            if device.mac_id not in self.device_dict:
                self.device_dict[device.mac_id] = {}
            self.device_dict[device.mac_id][device.id] = device
            device.set_api(self.api)

    async def listen_device_updates(self) -> None:
        loop = asyncio.get_running_loop()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(('0.0.0.0', 56000))
        self._socket.setblocking(False)
        self._stop_event = asyncio.Event()

        while not self._stop_event.is_set():
            try:
                data = await loop.sock_recv(self._socket, 1024)
                _LOGGER.debug(f"Received data: {data}")
                update = json.loads(data)
                await self.handle_update(update)
            except BlockingIOError:
                await asyncio.sleep(1)
            except Exception as e:
                _LOGGER.error(f"Failed to receive update: {e}")

        self._socket.close()
        _LOGGER.debug("Socket closed.")

    async def handle_update(self, update: dict) -> None:
        """Handle the device update."""
        try:
            mac_id = update['addr']
            update_type = update['data']['stype']
            if update_type == 'single':
                device_id = update['data']['subid']
                state = update['data']['status']
                device = self.device_dict.get(mac_id, {}).get(device_id)
                if device and asyncio.iscoroutine(device.callback):
                    await device.callback(state)
            elif update_type == 'all':
                device_list = dict(
                    enumerate(update['data']['status'], start=17))
                for device_id, state in device_list.items():
                    device = self.device_dict.get(mac_id, {}).get(device_id)
                    if device and asyncio.iscoroutine(device.callback):
                        await device.callback(state)
        except Exception as e:
            _LOGGER.error(f"State update failed: {e}, update: {update}")

    async def stop(self) -> None:
        """Gracefully stop the listener and clean up resources."""
        if hasattr(self, '_stop_event'):
            _LOGGER.debug("Stopping listener...")
            self._stop_event.set()
            # Wait for the listener to stop
            await asyncio.sleep(1)
            _LOGGER.debug("Listener stopped.")
