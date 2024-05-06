from collections.abc import Iterable
from datetime import datetime, timezone, timedelta
from logging import Logger

from ktw_its.api.http_client import HttpClientInterface
from ktw_its.dto import KtwItsSensorDto
from ktw_its.sensor import KtwItsSensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfSpeed, UnitOfTime, EntityCategory
from ktw_its.const import DEFAULT_NAME, DOMAIN, STATE_ATTR_UPDATE_DATE, STATE_ATTR_COLOR, STATE_ATTR_LONGITUDE, \
    STATE_ATTR_LATITUDE
from marshmallow import Schema, fields, post_load, EXCLUDE
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PropertiesData:
    avg_speed: int | None = None
    avg_time: float | None = None
    traffic: int | None = None
    traffic_period: int | None = None
    date_time: datetime | None = None
    color: str | None = None


@dataclass
class Properties:
    name: str
    description: str
    code: int
    data: PropertiesData


@dataclass
class Geometry:
    type: str
    coordinates: List[List[List[float]]]


@dataclass
class Feature:
    type: str
    properties: Properties
    geometry: Geometry


@dataclass
class FeatureCollection:
    type: str
    features: List[Feature]

    @classmethod
    def from_json(cls, json_data: str) -> "FeatureCollection":
        future_collection: FeatureCollection = FeatureCollectionSchema().loads(json_data=json_data)
        return future_collection

    def get_newest_datetime(self) -> Optional[datetime]:
        if not self.features:
            return None

        return max((feature.properties.data.date_time for feature in self.features if
                    feature.properties.data.date_time is not None), default=None)


class PropertiesDataSchema(Schema):
    avg_speed = fields.Int(data_key="avgSpeed", required=False)
    avg_time = fields.Float(data_key="avg_time", required=False)
    traffic = fields.Int(data_key="traffic", required=False)
    traffic_period = fields.Int(data_key="trafficPeriod", required=False)
    date_time = fields.DateTime(data_key="date_time", required=False)
    color = fields.Str(data_key="color", required=False)

    @post_load
    def make_properties_data(self, data, **kwargs):
        return PropertiesData(**data)


class PropertiesSchema(Schema):
    name = fields.Str()
    description = fields.Str()
    code = fields.Int()
    data = fields.Nested(PropertiesDataSchema, required=False)

    @post_load
    def make_properties(self, data, **kwargs):
        return Properties(**data)


class GeometrySchema(Schema):
    type = fields.Str()
    coordinates = fields.List(fields.List(fields.List(fields.Float())))

    @post_load
    def make_geometry(self, data, **kwargs):
        return Geometry(**data)


class FeatureSchema(Schema):
    type = fields.Str()
    properties = fields.Nested(PropertiesSchema)
    geometry = fields.Nested(GeometrySchema)

    @post_load
    def make_feature(self, data, **kwargs):
        return Feature(**data)


class FeatureCollectionSchema(Schema):
    type = fields.Str()
    features = fields.List(fields.Nested(FeatureSchema))

    @post_load
    def make_feature_collection(self, data, **kwargs):
        return FeatureCollection(**data)


class TrafficApi:
    def __init__(self, http_client: HttpClientInterface, logger: Logger) -> None:
        self.http_client: HttpClientInterface = http_client
        self.logger: Logger = logger
        self.traffic_data: dict[str, KtwItsSensorDto] = {}
        self.traffic_data_valid_to: datetime | None = None

    async def fetch_data(self) -> dict[str, KtwItsSensorDto]:
        if self.traffic_data_valid_to is not None and self.traffic_data_valid_to >= datetime.now(timezone.utc):
            self.logger.debug('Traffic data is still valid')
            return self.traffic_data

        traffic_json = await self.http_client.make_request('https://its.katowice.eu/api/traffic')
        feature_collection = FeatureCollection.from_json(traffic_json)

        self.traffic_data_valid_to = (feature_collection.get_newest_datetime() + timedelta(minutes=5))

        for feature in feature_collection.features:
            if feature.properties.data.date_time is None:
                continue

            state_attributes = {
                STATE_ATTR_UPDATE_DATE: feature.properties.data.date_time,
                STATE_ATTR_COLOR: feature.properties.data.color,
                STATE_ATTR_LONGITUDE: feature.geometry.coordinates[1][0][0],
                STATE_ATTR_LATITUDE: feature.geometry.coordinates[1][0][1],
            }

            device_info = DeviceInfo(
                entry_type=DeviceEntryType.SERVICE,
                identifiers={(DOMAIN, str(feature.properties.code))},
                manufacturer=DEFAULT_NAME,
                name='Traffic volume ' + feature.properties.name + ' [' + str(
                    feature.properties.code) + ']',
                serial_number=feature.properties.description,
                configuration_url='https://its.katowice.eu',
            )

            key = DOMAIN + '_' + str(feature.properties.code) + '_avg_speed'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=feature.properties.data.avg_speed,
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

            key = DOMAIN + '_' + str(feature.properties.code) + '_avg_time'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=feature.properties.data.avg_time,
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

            key = DOMAIN + '_' + str(feature.properties.code) + '_traffic'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=feature.properties.data.traffic,
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

            key = DOMAIN + '_' + str(feature.properties.code) + '_traffic_flow_per_hour'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=int((60 / feature.properties.data.traffic_period * feature.properties.data.traffic)),
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

            key = DOMAIN + '_' + str(feature.properties.code) + '_traffic_period'

            self.traffic_data.update([(
                key,
                KtwItsSensorDto(
                    state=str(feature.properties.data.traffic_period),
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
