import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant.components import onboarding
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from toyama_api.api import AuthorizationError, Toyama
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ToyamaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Toyama Config Flow"""

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.data: Dict[str, Any] = {}
        self.title: str = "Toyama HomeAssistant Integration"

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """
        Handle zeroconf discovery.
        """
        self.data[CONF_HOST] = host = discovery_info.host

        await self.async_set_unique_id(discovery_info.properties["Serial"])
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        _LOGGER.info(f"Discovered IP: {discovery_info.host}")

        return await self.async_step_user()

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> ConfigFlowResult:
        """
        Handle Toyama Login and devices setup
        """
        errors: Dict[str, str] = {}
        if user_input is not None:
            devices = None
            try:
                api = Toyama(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD]
                )
                await api.login()
                devices = await api.get_devices()
            except AuthorizationError:
                errors["base"] = "Login failed due to autorization error."
            except Exception as e:
                errors["base"] = str(e)
            if "base" not in errors and devices:
                self.data["device_data"] = [
                    device.__dict__ for device in devices]
                return self.async_create_entry(
                    title=self.title,
                    data=self.data
                )

            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
                last_step=False
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA
        )
