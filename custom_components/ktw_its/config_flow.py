"""Config flow for ITS Katowice integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.exceptions import HomeAssistantError

from homeassistant import config_entries
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema({})


class KtwItsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 0
    MINOR_VERSION = 1

    async def async_step_user(self, info):
        return self.async_create_entry(title="ITS Katowice", data={})


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
