from dataclasses import dataclass
from datetime import timedelta
import logging
from datetime import datetime
from functools import cached_property

import async_timeout

from homeassistant.components.light import LightEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from .const import (
    DOMAIN,
    TEMPERATURE_DATA,
    HUMIDITY_DATA
)
from .sensor import KtwItsSensorEntity, KtwItsSensorEntityDescription

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class KtwItsCameraImageDto:
    filename: str
    last_updated: datetime


@dataclass(frozen=True)
class KtwItsSensorDto:
    state: int | float | datetime
    entity_description: KtwItsSensorEntityDescription
    state_attributes: dict[str, str | float | datetime] | None = None


class KtwItsDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api):
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="My sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.api = api

    async def _async_update_data(self):
        return await self.api.fetch_data(set(self.async_contexts()))

    async def get_cameras(self):
        return await self.api.get_cameras()

    async def get_camera_image(self, camera_id: int, image_id: int) -> bytes | None:
        print('get_camera_image in coordinator')
        return await self.api.get_camera_image(camera_id, image_id)

    async def get_camera_image_data(self, camera_id: int, image_id: int) -> KtwItsCameraImageDto:
        print('get_camera_image_data in coordinator')
        return await self.api.get_camera_image_data(camera_id, image_id)
