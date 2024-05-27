# coding=utf-8
from __future__ import annotations

import random
from datetime import timedelta

from homeassistant.components.device_tracker import TrackerEntity, SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from . import KtwItsDataUpdateCoordinator
from .const import (
    DOMAIN
)

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: KtwItsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [KtwItsTrackerEntity(coordinator=coordinator)]
    async_add_entities(entities)


class KtwItsTrackerEntity(CoordinatorEntity, TrackerEntity):
    _attr_has_entity_name = True
    _attr_name = "Ktw Its Tracker"
    _attr_unique_id = "ktw_its_tracker"
    _attr_should_poll = True

    latitudes = [50.258911, 50.264892, 50.265354]

    longitudes = [19.014115, 19.023892, 19.024354]

    @property
    def source_type(self) -> SourceType | str:
        """Return the source type, eg gps or router, of the device."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        # Return a random latitude from the list
        return random.choice(self.latitudes)

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        # Return a random latitude from the list
        return random.choice(self.longitudes)
