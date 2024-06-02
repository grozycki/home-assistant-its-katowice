"""Config flow for ITS Katowice integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol  # type: ignore
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow, ConfigFlowResult
from homeassistant.const import Platform
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from custom_components.ktw_its.const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE_TRACKERS = "device_trackers"

STEP_USER_DATA_SCHEMA = vol.Schema({})


class KtwItsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 0
    MINOR_VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> KtwItsOptionsFlow:
        return KtwItsOptionsFlow(config_entry)

    async def async_step_user(self, info):
        return self.async_create_entry(title="ITS Katowice", data={})


class KtwItsOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry
        self._config: dict[str, Any] = {}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            print(user_input)
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    "device_trackers",
                    default=self.config_entry.options.get("device_trackers"),
                    msg="some message",
                    description="some description",
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=Platform.DEVICE_TRACKER, multiple=True),
                )
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            last_step=True
        )



class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
