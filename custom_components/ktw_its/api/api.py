import logging

from custom_components.ktw_its.api.camera import CameraApi
from custom_components.ktw_its.api.traffic import TrafficApi
from custom_components.ktw_its.api.weather import WeatherApi
from custom_components.ktw_its.dto import KtwItsCameraImageDto, KtwItsSensorDto

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ktw_its"


class KtwItsApi:
    def __init__(self, weather_api: WeatherApi, traffic_api: TrafficApi, camera_api: CameraApi) -> None:
        self.__weather_api: WeatherApi = weather_api
        self.__traffic_api: TrafficApi = traffic_api
        self.__camera_api: CameraApi = camera_api

    async def fetch_data(self, groups: set | None = None) -> dict[str, KtwItsSensorDto | KtwItsCameraImageDto]:
        data: dict[str, KtwItsSensorDto | KtwItsCameraImageDto] = {}
        data.update(await self.__weather_api.fetch_data())
        data.update(await self.__traffic_api.fetch_data())
        data.update(await self.__camera_api.fetch_data())

        return data

    async def get_camera_image(self, camera_id: int, image_id: int) -> bytes | None:
        return await self.__camera_api.get_camera_image(camera_id, image_id)
