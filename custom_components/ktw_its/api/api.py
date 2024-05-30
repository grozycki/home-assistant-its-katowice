# coding=utf-8
import logging

from homeassistant.core import EventStateChangedData, Event

from custom_components.ktw_its.api.camera import CameraApi
from custom_components.ktw_its.api.parking_zones import ParkingZonesApi
from custom_components.ktw_its.api.traffic import TrafficApi
from custom_components.ktw_its.api.weather import WeatherApi
from custom_components.ktw_its.dto import KtwItsCameraImageDto, KtwItsSensorDto

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ktw_its"


class KtwItsApi:
    def __init__(self,
                 weather_api: WeatherApi,
                 traffic_api: TrafficApi,
                 camera_api: CameraApi,
                 parking_zones_api: ParkingZonesApi
                 ) -> None:
        self.__weather_api: WeatherApi = weather_api
        self.__traffic_api: TrafficApi = traffic_api
        self.__camera_api: CameraApi = camera_api
        self.__parking_zones_api: ParkingZonesApi = parking_zones_api

    async def fetch_data(self, groups: set | None = None) -> dict[str, KtwItsSensorDto | KtwItsCameraImageDto]:
        data: dict[str, KtwItsSensorDto | KtwItsCameraImageDto] = {}
        data.update(await self.__weather_api.fetch_data())
        data.update(await self.__traffic_api.fetch_data())
        data.update(await self.__camera_api.fetch_data())
        await self.__parking_zones_api.fetch_data()

        return data

    async def get_camera_image(self, camera_id: int, image_id: int) -> bytes | None:
        return await self.__camera_api.get_camera_image(camera_id, image_id)

    def on_entity_state_change(self, event: Event[EventStateChangedData]):
        self.__parking_zones_api.on_entity_state_change(event)
