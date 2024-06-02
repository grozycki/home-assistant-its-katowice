
from datetime import timedelta
from logging import Logger

from homeassistant.core import HomeAssistant, Event, EventStateChangedData, callback
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .api.api import KtwItsApi
from .dto import KtwItsCameraImageDto, KtwItsSensorDto


class KtwItsDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, api: KtwItsApi, logger: Logger) -> None:
        super().__init__(
            hass=hass,
            logger=logger,
            name="ITS Katowice",
            update_interval=timedelta(seconds=60),
        )
        self.__api = api

    async def fetch_data(self) -> dict[str, KtwItsSensorDto | KtwItsCameraImageDto]:
        return await self.__api.fetch_data()

    async def _async_update_data(self) -> dict:
        return await self.__api.fetch_data(set(self.async_contexts()))

    async def get_camera_image(self, camera_id: int, image_id: int) -> bytes | None:
        return await self.__api.get_camera_image(camera_id, image_id)

    @callback
    def on_entity_state_change(self, event: Event[EventStateChangedData]) -> None:
        self.__api.on_entity_state_change(event)
