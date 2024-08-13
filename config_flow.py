from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .api import APIAuthError, Toyama
from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ToyamaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle Toyama Config Flow"""
    VERSION = 1
    _input_data: dict[str | Any]
    _title: str

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step.
        This is called when we initiate adding integration via the UI
        """
        errors: dict[str, str] = {}
        self._title = "Toyama Integration"
        if user_input is not None:
            # The form has been filled in and submitted, so process the data provided.
            data = None
            try:
                api = Toyama(
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD]
                )
                await api.login()
                data = await api.fetch_devices()
            except Exception as e:
                errors['base'] = str(e)

            if 'base' not in errors:
                await self.async_set_unique_id(self._title)
                self._abort_if_unique_id_configured()
                self._input_data = user_input
                self._input_data['device_data'] = data
                return self.async_create_entry(title=self._title, data=self._input_data)

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
