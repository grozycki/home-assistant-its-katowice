from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from logging import Logger

from marshmallow import fields, Schema, post_load, EXCLUDE

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfSpeed, )
from ktw_its.api.http_client import HttpClientInterface
from ktw_its.dto import KtwItsSensorDto
from ktw_its.sensor import KtwItsSensorEntityDescription


@dataclass(frozen=True, kw_only=True)
class Weather:
    date: datetime
    sunrise: datetime
    sunset: datetime
    temperature: float
    humidity: int
    pressure: int
    wind_speed: float
    wind_degrees: int
    description: str
    co: float
    no: float
    no2: float
    o3: float
    so2: float
    pm2_5: float
    pm10: float
    nh3: float
    aqi: int

    @classmethod
    def from_json(cls, json_data: str) -> "Weather":
        weather: Weather = WeatherSchema().loads(json_data=json_data, unknown=EXCLUDE)
        return weather


class WeatherSchema(Schema):
    date = fields.DateTime(required=True)
    sunrise = fields.DateTime(required=True)
    sunset = fields.DateTime(required=True)
    temperature = fields.Float(required=True)
    humidity = fields.Integer(required=True)
    pressure = fields.Integer(required=True)
    wind_speed = fields.Float(required=True, data_key="windSpeed")
    wind_degrees = fields.Integer(required=True, data_key="windDegrees")
    description = fields.Str(required=True)
    co = fields.Float(required=True)
    no = fields.Float(required=True)
    no2 = fields.Float(required=True)
    o3 = fields.Float(required=True)
    so2 = fields.Float(required=True)
    pm2_5 = fields.Float(required=True)
    pm10 = fields.Float(required=True)
    nh3 = fields.Float(required=True)
    aqi = fields.Integer(required=True)

    @post_load
    def make_weather(self, data: dict, **kwargs) -> Weather:
        return Weather(**data)


class WeatherApi:
    def __init__(self, http_client: HttpClientInterface, logger: Logger) -> None:
        self.http_client: HttpClientInterface = http_client
        self.logger: Logger = logger
        self.weather_data: dict[str, KtwItsSensorDto] = {}
        self.weather_data_valid_to: datetime | None = None

    async def fetch_data(self) -> dict[str, KtwItsSensorDto]:
        if self.weather_data_valid_to is not None and self.weather_data_valid_to >= datetime.now(timezone.utc):
            self.logger.debug("Weather data is still valid")
            return self.weather_data

        weather_json = await self.http_client.make_request('https://its.katowice.eu/api/v1/weather/air')
        weather = Weather.from_json(weather_json)
        self.weather_data_valid_to = weather.date + timedelta(minutes=20)

        self.weather_data.update(
            [
                (
                    SensorDeviceClass.TEMPERATURE,
                    KtwItsSensorDto(
                        state=weather.temperature,
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
                        state=weather.pressure,
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
                        state=weather.humidity,
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
                        state=weather.wind_speed,
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
                        state=weather.aqi,
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
                        state=weather.co,
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
                        state=weather.no,
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
                        state=weather.no2,
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
                        state=weather.o3,
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
                        state=weather.so2,
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
                        state=weather.pm2_5,
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
                        state=weather.pm10,
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
                        state=weather.sunrise,
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key='sunrise',
                            device_class=SensorDeviceClass.TIMESTAMP,
                            native_unit_of_measurement=None,
                            state_class=None
                        ),
                    )
                ),
                (
                    'sunset',
                    KtwItsSensorDto(
                        state=weather.sunset,
                        entity_description=
                        KtwItsSensorEntityDescription(
                            group='weather',
                            key='sunset',
                            device_class=SensorDeviceClass.TIMESTAMP,
                            native_unit_of_measurement=None,
                            state_class=None
                        ),
                    )
                ),
            ]
        )

        return self.weather_data
