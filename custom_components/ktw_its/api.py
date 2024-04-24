import aiohttp
import asyncio
import ssl
import certifi

from .const import WEATHER_DATA, DOMAIN, DEFAULT_NAME
from datetime import datetime, timedelta, timezone
import logging
from .coordinator import KtwItsCameraImageDto, KtwItsSensorDto
from collections.abc import Iterable

from .sensor import KtwItsSensorEntityDescription
from ..sensor import SensorDeviceClass
import pytz

from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_NAME,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfSpeed, UnitOfTime, EntityCategory,
)
from ...helpers.device_registry import DeviceInfo, DeviceEntryType

_LOGGER = logging.getLogger(__name__)


async def make_request(url: str):
    _LOGGER.warning(f"making request to {url}")
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(url) as resp:
            return await resp.json()


async def make_request_read(url: str):
    print(url)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    conn = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(url) as resp:
            return await resp.read()


class KtwItsApi:
    def __init__(self):
        self.weather_data_valid_to: datetime | None = None
        self.traffic_data_valid_to: datetime | None = None
        self.weather_data: dict = {}
        self.traffic_data: dict = {}

    async def fetch_data(self, groups: set | None = None) -> dict:
        data: dict = {}
        data.update(await self.__get_weather())
        data.update(await self.__get_traffic())

        return data

    async def get_camera_images_by_id(self, camera_id: int):
        return await make_request('https://its.katowice.eu/api/cameras/' + str(camera_id) + '/images')

    async def get_camera_image(self, camera_id: int, image_id: int) -> bytes | None:
        print('get_camera_image in api')

        images = await make_request('https://its.katowice.eu/api/cameras/' + str(camera_id) + '/images')
        filename = images['images'][image_id]['filename']

        return await make_request_read('https://its.katowice.eu/api/camera/image/' + str(camera_id) + '/' + filename)

    async def get_camera_image_data(self, camera_id: int, image_id: int) -> KtwItsCameraImageDto:
        images = await make_request('https://its.katowice.eu/api/cameras/' + str(camera_id) + '/images')
        print(images)
        filename = images['images'][image_id]['filename']
        print(filename)

        last_updated = datetime.fromisoformat(images['images'][image_id]['addTime'])
        print(last_updated)

        return KtwItsCameraImageDto(last_updated=last_updated, filename=filename)

    async def get_cameras(self):
        return await make_request('https://its.katowice.eu/api/cameras')

    async def __get_weather(self) -> Iterable[KtwItsSensorDto]:
        if self.weather_data_valid_to is not None and self.weather_data_valid_to >= datetime.now(timezone.utc):
            return self.weather_data

        weather = await make_request('https://its.katowice.eu/api/v1/weather/air')
        self.weather_data_valid_to = datetime.fromisoformat(weather['date']) + timedelta(minutes=20)

        self.weather_data.update(
            [
                (
                    SensorDeviceClass.TEMPERATURE,
                    KtwItsSensorDto(
                        state=float(weather['temperature']),
                        entity_description=KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.TEMPERATURE,
                            device_class=SensorDeviceClass.TEMPERATURE,
                            native_unit_of_measurement=UnitOfTemperature.CELSIUS
                        ),
                    )
                ),
                (
                    SensorDeviceClass.PRESSURE,
                    KtwItsSensorDto(
                        state=int(weather['pressure']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.PRESSURE,
                            device_class=SensorDeviceClass.PRESSURE,
                            native_unit_of_measurement=UnitOfPressure.HPA
                        ),
                    )
                ),
                (
                    SensorDeviceClass.HUMIDITY,
                    KtwItsSensorDto(
                        state=int(weather['humidity']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.HUMIDITY,
                            device_class=SensorDeviceClass.HUMIDITY,
                            native_unit_of_measurement=PERCENTAGE
                        ),
                    )
                ),
                (
                    SensorDeviceClass.WIND_SPEED,
                    KtwItsSensorDto(
                        state=float(weather['windSpeed']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.WIND_SPEED,
                            device_class=SensorDeviceClass.WIND_SPEED,
                            native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND
                        ),
                    )
                ),
                (
                    SensorDeviceClass.AQI,
                    KtwItsSensorDto(
                        state=int(weather['aqi']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.AQI,
                            device_class=SensorDeviceClass.AQI,
                            native_unit_of_measurement=None
                        ),
                    )
                ),
                (
                    SensorDeviceClass.CO,
                    KtwItsSensorDto(
                        state=float(weather['co']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.CO,
                            device_class=SensorDeviceClass.CO,
                            native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION
                        ),
                    )
                ),
                (
                    SensorDeviceClass.NITROGEN_MONOXIDE,
                    KtwItsSensorDto(
                        state=float(weather['no']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.NITROGEN_MONOXIDE,
                            device_class=SensorDeviceClass.NITROGEN_MONOXIDE,
                            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER

                        ),
                    )
                ),
                (
                    SensorDeviceClass.NITROGEN_DIOXIDE,
                    KtwItsSensorDto(
                        state=float(weather['no2']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.NITROGEN_DIOXIDE,
                            device_class=SensorDeviceClass.NITROGEN_DIOXIDE,
                            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
                        ),
                    )
                ),
                (
                    SensorDeviceClass.OZONE,
                    KtwItsSensorDto(
                        state=float(weather['o3']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.OZONE,
                            device_class=SensorDeviceClass.OZONE,
                            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
                        ),
                    )
                ),
                (
                    SensorDeviceClass.SULPHUR_DIOXIDE,
                    KtwItsSensorDto(
                        state=float(weather['so2']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.SULPHUR_DIOXIDE,
                            device_class=SensorDeviceClass.SULPHUR_DIOXIDE,
                            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
                        ),
                    )
                ),
                (
                    SensorDeviceClass.PM25,
                    KtwItsSensorDto(
                        state=float(weather['pm2_5']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.PM25,
                            device_class=SensorDeviceClass.PM25,
                            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
                        ),
                    )
                ),
                (
                    SensorDeviceClass.PM10,
                    KtwItsSensorDto(
                        state=float(weather['pm10']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key=SensorDeviceClass.PM10,
                            device_class=SensorDeviceClass.PM10,
                            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
                        ),
                    )
                ),
                (
                    'sunrise',
                    KtwItsSensorDto(
                        state=datetime.fromisoformat(weather['sunrise']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key='sunrise',
                            device_class=SensorDeviceClass.TIMESTAMP,
                            native_unit_of_measurement=None
                        ),
                    )
                ),
                (
                    'sunset',
                    KtwItsSensorDto(
                        state=datetime.fromisoformat(weather['sunset']),
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key='sunset',
                            device_class=SensorDeviceClass.TIMESTAMP,
                            native_unit_of_measurement=None
                        ),
                    )
                ),
            ]
        )

        return self.weather_data

    async def __get_traffic(self) -> Iterable[KtwItsSensorDto]:
        if self.traffic_data_valid_to is not None and self.traffic_data_valid_to >= datetime.now(timezone.utc):
            return self.traffic_data

        traffic = await make_request('https://its.katowice.eu/api/traffic')

        for feature in traffic['features']:
            try:
                avg_speed = int(feature['properties']['data']['avgSpeed'])
            except KeyError:
                continue

            state_attributes = {
                'update_date': datetime.fromisoformat(feature['properties']['data']['date_time']),
                'color': feature['properties']['data']['color'],
                'longitude': float(feature['geometry']['coordinates'][1][0][0]),
                'latitude': float(feature['geometry']['coordinates'][1][0][1]),
            }

            self.traffic_data_valid_to = datetime.fromisoformat(feature['properties']['data']['date_time']) + timedelta(minutes=2)

            device_info = DeviceInfo(
                entry_type=DeviceEntryType.SERVICE,
                identifiers={(DOMAIN, feature['properties']['code'])},
                manufacturer=DEFAULT_NAME,
                name='Traffic volume ' + str(feature['properties']['name']) + ' [' + str(
                    feature['properties']['code']) + ']',
                serial_number=str(feature['properties']['description']),
                configuration_url='https://its.katowice.eu',
            )

            key = DOMAIN + '_' + str(feature['properties']['code']) + '_avg_speed'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=avg_speed,
                    state_attributes=state_attributes,
                    entity_description=
                    KtwItsSensorEntityDescription(
                        group='traffic',
                        key=key,
                        name='Average speed',
                        device_class=SensorDeviceClass.SPEED,
                        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
                        device_info=device_info,
                    ),
                )
            )])

            key = DOMAIN + '_' + str(feature['properties']['code']) + '_avg_time'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=float(feature['properties']['data']['avg_time']),
                    state_attributes=state_attributes,
                    entity_description=
                    KtwItsSensorEntityDescription(
                        group='traffic',
                        key=key,
                        name='Average time',
                        device_class=SensorDeviceClass.DURATION,
                        native_unit_of_measurement=UnitOfTime.SECONDS,
                        device_info=device_info,
                        icon='mdi:car-clock',
                    ),
                )
            )])

            key = DOMAIN + '_' + str(feature['properties']['code']) + '_traffic'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=int(feature['properties']['data']['traffic']),
                    state_attributes=state_attributes,
                    entity_description=
                    KtwItsSensorEntityDescription(
                        group='traffic',
                        key=key,
                        name='Traffic',
                        device_class=None,
                        native_unit_of_measurement=None,
                        device_info=device_info,
                        icon='mdi:car-info',
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                )
            )])

            key = DOMAIN + '_' + str(feature['properties']['code']) + '_traffic_flow_per_hour'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=int((60 / int(feature['properties']['data']['trafficPeriod'])) * int(
                        feature['properties']['data']['traffic'])),
                    state_attributes=state_attributes,
                    entity_description=
                    KtwItsSensorEntityDescription(
                        group='traffic',
                        key=key,
                        name='Traffic flow per hour',
                        device_class=None,
                        native_unit_of_measurement='vehicle/h',
                        device_info=device_info,
                        icon='mdi:car-multiple'
                    ),
                )
            )])

            key = DOMAIN + '_' + str(feature['properties']['code']) + '_traffic_period'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=str(feature['properties']['data']['trafficPeriod']),
                    state_attributes=state_attributes,
                    entity_description=
                    KtwItsSensorEntityDescription(
                        group='traffic',
                        key=key,
                        name='Traffic period',
                        device_class=SensorDeviceClass.ENUM,
                        native_unit_of_measurement=None,
                        state_class=None,
                        device_info=device_info,
                        icon='mdi:traffic-cone',
                        options=['3', '10', '15'],
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                )
            )])

        return self.traffic_data
