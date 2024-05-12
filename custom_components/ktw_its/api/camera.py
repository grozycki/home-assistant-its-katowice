from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, TypedDict
from marshmallow import Schema, fields, post_load, INCLUDE
from typing import Iterable

from homeassistant.helpers.device_registry import DeviceInfo, DeviceEntryType
from custom_components.ktw_its.api.http_client import HttpClientInterface
from logging import Logger

from custom_components.ktw_its.image import KtwItsImageEntityDescription
from custom_components.ktw_its.const import DEFAULT_NAME, DOMAIN

from custom_components.ktw_its.dto import KtwItsCameraImageDto


@dataclass(frozen=True, kw_only=True)
class Properties:
    id: int
    name: str
    description: str
    state: int
    type: str
    image: str


class PropertiesSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str()
    state = fields.Int()
    type = fields.Str()
    image = fields.Str()

    @post_load
    def make_properties(self, data, **kwargs):
        return Properties(**data)


@dataclass(frozen=True, kw_only=True)
class Geometry:
    type: str
    coordinates: list[float]


class GeometrySchema(Schema):
    type = fields.Str()
    coordinates = fields.List(fields.Float())

    @post_load
    def make_geometry(self, data, **kwargs):
        return Geometry(**data)


@dataclass(frozen=True, kw_only=True)
class Feature:
    type: str
    properties: Properties
    geometry: Geometry


class FeatureSchema(Schema):
    type = fields.Str()
    properties = fields.Nested(PropertiesSchema)
    geometry = fields.Nested(GeometrySchema)

    @post_load
    def make_feature(self, data, **kwargs):
        return Feature(**data)


@dataclass(frozen=True, kw_only=True)
class FeatureCollection:
    type: str
    features: list[Feature]

    @classmethod
    def from_json(cls, json_data: str) -> "FeatureCollection":
        future_collection: FeatureCollection = FeatureCollectionSchema().loads(json_data=json_data)
        return future_collection


class FeatureCollectionSchema(Schema):
    type = fields.Str()
    features = fields.List(fields.Nested(FeatureSchema))

    @post_load
    def make_feature_collection(self, data, **kwargs):
        return FeatureCollection(**data)


@dataclass
class Image:
    filename: str
    addTime: datetime
    size: int
    mimeType: str
    code: str
    digest: str


class ImageSchema(Schema):
    filename = fields.Str()
    addTime = fields.DateTime()
    size = fields.Int()
    mimeType = fields.Str()
    code = fields.Str()
    digest = fields.Str()

    @post_load
    def make_image(self, data, **kwargs):
        return Image(**data)


@dataclass
class Images:
    images: list[Image]

    @classmethod
    def from_json(cls, json_data: str) -> "Images":
        images: Images = ImagesSchema().loads(json_data=json_data)
        return images

    def is_empty(self) -> bool:
        return len(self.images) == 0


class ImagesSchema(Schema):
    images = fields.List(fields.Nested(ImageSchema))

    @post_load
    def make_images(self, data, **kwargs):
        return Images(**data)


class CameraApi:
    def __init__(self, http_client: HttpClientInterface, logger: Logger) -> None:
        self.__http_client: HttpClientInterface = http_client
        self.__logger: Logger = logger
        self.__cameras_data: dict[str, KtwItsCameraImageDto] = {}
        self.__cameras_data_valid_to: datetime | None = None
        self.__camera_images_data: dict[int, list[Image]] = {}
        self.__camera_images_data_valid_to: dict[int, datetime] = {}

    async def fetch_data(self) -> dict[str, KtwItsCameraImageDto]:
        if self.__cameras_data_valid_to is not None and self.__cameras_data_valid_to >= datetime.now(timezone.utc):
            self.__logger.debug("Cameras data is still valid")

            for cameras_data in self.__cameras_data.values():
                if (cameras_data is not None
                        and cameras_data.image_last_updated is not None
                        and cameras_data.image_last_updated < datetime.now(timezone.utc) - timedelta(minutes=5)):
                    cameras_data.image_last_updated = None

            return self.__cameras_data

        camera_json = await self.__http_client.make_request('https://its.katowice.eu/api/cameras')
        feature_collection = FeatureCollection.from_json(camera_json)

        self.__cameras_data_valid_to = datetime.now(timezone.utc) + timedelta(minutes=60)

        for feature in feature_collection.features:

            state_attributes = {
                'longitude': feature.geometry.coordinates[0],
                'latitude': feature.geometry.coordinates[1],
                'camera_id': feature.properties.id,
                'camera_type': feature.properties.type,
            }

            device_info = DeviceInfo(
                entry_type=DeviceEntryType.SERVICE,
                identifiers={(DOMAIN, str(feature.properties.id))},
                manufacturer=DEFAULT_NAME,
                name='Camera ' + feature.properties.name + ' [' + str(
                    feature.properties.description) + ']',
                configuration_url='https://its.katowice.eu',
            )

            if feature.properties.state == 1:
                if feature.properties.type == 'ptz':
                    count = 4
                else:
                    count = 1
                i = 0
                while i < count:
                    key = DOMAIN + '_' + feature.properties.name + '_' + str(i) + '_' + '_image'

                    self.__cameras_data.update([(
                        key,
                        KtwItsCameraImageDto(
                            state_attributes=state_attributes,
                            entity_description=KtwItsImageEntityDescription(
                                key=key,
                                group='camera',
                                camera_id=feature.properties.id,
                                camera_name=feature.properties.name,
                                camera_description=feature.properties.description,
                                image_id=i,
                                device_info=device_info
                            )
                        )
                    )])
                    i += 1

        return self.__cameras_data

    async def get_camera_image(self, camera_id: int, image_id: int) -> bytes | None:
        images = await self.__get_camera_images(camera_id)
        if images.__len__() == 0:
            self.__logger.error("Camera " + str(camera_id) + " has no image with id " + str(image_id))
            return None

        filename = images[image_id].filename

        return await self.__http_client.make_request_bytes(
            'https://its.katowice.eu/api/camera/image/{0}/{1}'.format(str(camera_id), filename)
        )

    async def __get_camera_images(self, camera_id: int) -> list[Image]:
        if bool(self.__camera_images_data_valid_to.get(camera_id)) and self.__camera_images_data_valid_to[camera_id] >= datetime.now(timezone.utc):
            self.__logger.debug("Camera " + str(camera_id) + " data is still valid")
            return self.__camera_images_data[camera_id]

        images_json = await self.__http_client.make_request(
            'https://its.katowice.eu/api/cameras/{0}/images'.format(str(camera_id))
        )
        images = Images.from_json(images_json)
        if images.is_empty():
            self.__logger.error("Camera " + str(camera_id) + " has no images")
            return []

        image_last_updated = images.images[0].addTime

        self.__camera_images_data_valid_to[camera_id] = image_last_updated + timedelta(minutes=5)
        self.__camera_images_data[camera_id] = images.images

        for cameras_data in self.__cameras_data.values():
            if cameras_data is not None and cameras_data.entity_description.camera_id == camera_id:
                cameras_data.image_last_updated = image_last_updated

        return self.__camera_images_data[camera_id]
