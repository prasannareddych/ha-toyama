from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import aiohttp
import asyncio
import json
import logging
import socket

_LOGGER = logging.getLogger(__name__)

TOYAMA_API_HOST = 'https://api.toyamaworld.com'

class DeviceType(StrEnum):
    FAN = "dimmer"
    SWITCH = "onoff"

@dataclass
class Device:
    """API device."""
    id: int
    mac_id: str
    room: str
    unique_id: str
    type: DeviceType
    name: str
    state: int | bool

class Toyama:
    def __init__(self, username, password, access_token = None):
        self.username = username
        self.password = password
        self.access_token = access_token
        self.headers = ({
            "User-Agent": "Dart/3.2 (dart:io)",
            'Authorization': f"Bearer {self.access_token}"
        })
    async def initialize(self) -> None:
        """check access token validity and login if it is expired."""
        if not await self.is_token_valid():
            try:
                await self.login()
            except Exception as e:
                _LOGGER.error(f"initialize: {e}")
                raise

    async def is_token_valid(self) -> bool:
        """check access token validity."""

        try:
            url = f"{TOYAMA_API_HOST}/api/v1/gateways/list"
            async with aiohttp.ClientSession() as session:
                async with session.get(url = url, headers = self.headers) as response:
                    if response.status == 200:
                        return True
                    return False
        except Exception as e:
            _LOGGER.debug(f"check_access_token: {e}")
            return False

    async def login(self) -> None:
        """login to WizHom"""

        login_url = f"{TOYAMA_API_HOST}/oauth/token"
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        multipart_data = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="email"\r\n\r\n{self.username}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="password"\r\n\r\n{self.password}\r\n'
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="grant_type"\r\n\r\npassword\r\n'
            f'--{boundary}--\r\n'
        )

        headers = {
            "User-Agent": "Dart/3.2 (dart:io)",
            "Accept-Encoding": "gzip",
            "Content-Type": f'multipart/form-data; boundary={boundary}',
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, headers=headers, data=multipart_data) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        self.access_token = response_data.get('access_token')
                        self.headers.update({
                            'Authorization': f"Bearer {self.access_token}"
                        })
                    else:
                        raise APIAuthError("Error connecting to api. Invalid username or password.")
        except Exception as e:
            _LOGGER.error(f"login: {e}")
            raise
            
    async def fetch_gateways(self) -> list:
        """fetch gateways in your account."""

        url = f"{TOYAMA_API_HOST}/api/v1/gateways/list"
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        gateways = []
                        for gateway in data:
                            gateways.append({
                                "id": gateway["id"],
                                "serial": gateway["serial_number"],
                            })
                        return gateways
                    else:
                        raise APIError(f"Error! response {response.status}")
        except Exception as e:
            _LOGGER.error(f"fetch_gateways: {e}")
            raise

    async def fetch_gateway_info(self, serial_id: str) -> dict:
        """fetch gateway information"""

        url = f"{TOYAMA_API_HOST}/api/v1/gateways/single"
        try:
            json_data = {
                "gateway": {
                    "serial_number": serial_id
                }
            }
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(url=url, json=json_data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise APIError(f"Error! response {response.status}")
        except Exception as e:
            _LOGGER.error(f"fetch_gateway_info: {e}")
            raise

    async def fetch_devices(self) -> dict:
        try:
            gateways = await self.fetch_gateways()
            my_devices = []
            for gateway in gateways:
                data = await self.fetch_gateway_info(gateway['serial'])
                for zone in data[0]['zones']:
                    zone_data = {
                        "zone_id": zone['id'],
                        "zone_name": zone['name']
                    }
                    zone_data['rooms'] = []
                    for room in zone['rooms']:
                        room_data = {
                            'room_id': room['id'],
                            'room_name': room['name']
                        }
                        room_data['boards'] = []
                        for boards in room['legacy_devices']:
                            device_data = {
                                "id": boards['id'],
                                "mac_id": boards['mac_id'],
                            }
                            toggles = []
                            for b in boards['legacy_device_buttons']:
                                toggles.append(
                                    [
                                        int(b['button_number'])+16,
                                        b['id'],
                                        b['name'],
                                        b['percentage'],
                                        b['variant']
                                    ]
                                )
                            device_data['toggles'] = sorted(toggles)
                            room_data['boards'].append(device_data)
                        zone_data['rooms'].append(room_data)
                    my_devices.append(zone_data)
            return my_devices
        except Exception as e:
            raise APIError(f"Failed to fetch device info: {e}")

    async def get_my_devices(self):
        try:
            gateways = await self.fetch_gateways()
            my_devices = []
            for gateway in gateways:
                data = await self.fetch_gateway_info(gateway['serial'])
                for zone in data[0]['zones']:
                    for room in zone['rooms']:
                        room_name = room['name'].replace(" ","_")
                        for boards in room['legacy_devices']:
                            mac_id = boards['mac_id']
                            for b in boards['legacy_device_buttons']:
                                device_id = int(b['button_number'])+16
                                my_devices.append(
                                    Device(
                                        id = device_id,
                                        mac_id = mac_id,
                                        room = room_name,
                                        unique_id = f"{room_name}_{mac_id}_{device_id}",
                                        type = b['variant'],
                                        name = b['name'],
                                        state = b['percentage']
                                    )
                                )
            return my_devices
        except Exception as e:
            raise APIError(f"Failed to get device list: {e}")

class APIAuthError(Exception):
    """Exception class for auth error."""

class APIError(Exception):
    """Exception class for API error."""


class ClientAPI:
    def __init__(self, ip_address: str, message_callback: Callable = None) -> None:
        self.ip_address = ip_address
        self.message_callback = message_callback
        self._task: asyncio.Task = None

    async def initialize(self):
        if self.message_callback:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self.listen_device_updates())
            await self.request_all_devices_status()


    async def send_request(self, payload: dict) -> bool:
        async with aiohttp.ClientSession() as session:
            resp = await session.post(f"http://{self.ip_address}:8900/operate", json=payload)
            result = await resp.text()
            return result == 'ok'

    async def update_device_state(self, device: Device, new_state: int) -> bool:
        payload = {
            "type": "swcmd",
            "data": [
                {
                    "addr": [device.mac_id],
                    "nodedata": {
                        "cmdtype": "operate",
                        "subid": device.id,
                        "cmd": new_state
                    }
                }
            ]
        }
        try:
            _LOGGER.debug(f"updating: {device.id}, {new_state}")
            return await self.send_request(payload)
        except Exception as e:
            _LOGGER.error(f"Failed to update the state for {device}: {e}")
        return False

    async def request_all_devices_status(self) -> bool:
        payload = {
            "type": "swcmd",
            "data": [
                {
                    "addr": [
                        "ffffffffffff"
                    ],
                    "nodedata": {
                        "cmdtype": "getstatus"
                    }
                }
            ]
        }
        try:
            return await self.send_request(payload) == 'ok'
        except Exception as e:
            _LOGGER.error(f"request_all_devices_status: FAIL! {e}")
            return False
        
    async def listen_device_updates(self):
        loop = asyncio.get_running_loop()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 56000))
        sock.setblocking(False)
        while True:
            try:
                data = await loop.sock_recv(sock, 1024)
                _LOGGER.debug(f"received data: f{data}")
                update = json.loads(data)
                if asyncio.iscoroutinefunction(self.message_callback):
                    await self.message_callback(update)
            except BlockingIOError:
                await asyncio.sleep(1)
            except Exception as e:
                _LOGGER.error(f"Failed to receive update: {e}")

