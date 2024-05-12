"""The ITS Katowice integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .api.api import KtwItsApi
from .api.camera import CameraApi
from .api.http_client import HttpClient
from .api.traffic import TrafficApi
from .api.weather import WeatherApi
from .const import DOMAIN
from .coordinator import KtwItsDataUpdateCoordinator
import logging
from homeassistant import config_entries, core
from homeassistant.const import Platform

PLATFORMS: list[Platform] = [
    Platform.IMAGE,
    Platform.SENSOR
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    http_client = HttpClient(logger=_LOGGER)
    ktw_its_coordinator = KtwItsDataUpdateCoordinator(
        hass=hass,
        api=KtwItsApi(
            weather_api=WeatherApi(http_client=http_client, logger=_LOGGER),
            traffic_api=TrafficApi(http_client=http_client, logger=_LOGGER),
            camera_api=CameraApi(http_client=http_client, logger=_LOGGER)
        ),
        logger=_LOGGER
    )
    await ktw_its_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = ktw_its_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def options_update_listener(
        hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    return True


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True
