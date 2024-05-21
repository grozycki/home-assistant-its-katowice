# coding=utf-8

from datetime import datetime, timezone
from logging import Logger

from marshmallow import fields, post_load, Schema
from shapely import Polygon, Point

from custom_components.ktw_its.api.geo import FeatureCollection, point_in_polygon
from custom_components.ktw_its.api.http_client import HttpClientInterface
from custom_components.ktw_its.dto import KtwItsSensorDto


class Properties:
    code: str
    name: str
    color: str
    description: str
    carParkingSpots: int
    occupiedParkingSpots: int


class PropertiesSchema(Schema):
    code = fields.Str()
    name = fields.Str()
    color = fields.Str()
    description = fields.Str()
    carParkingSpots = fields.Int(data_key="carParkingSpots")
    occupiedParkingSpots = fields.Int(data_key="occupiedParkingSpots")


class ParkingZonesApi:
    def __init__(self, http_client: HttpClientInterface, logger: Logger) -> None:
        self.http_client: HttpClientInterface = http_client
        self.logger: Logger = logger
        self.parking_zones_data: dict[str, KtwItsSensorDto] = {}
        self.parking_zones_data_valid_to: datetime | None = None

    async def fetch_data(self) -> dict[str, KtwItsSensorDto]:
        self.logger.debug("Fetching parking zones data")
        # if (self.parking_zones_data_valid_to is not None
        #         and self.parking_zones_data_valid_to >= datetime.now(timezone.utc)):
        #     self.logger.debug("Parking zones data is still valid")
        #     return self.parking_zones_data

        parking_zones_json = await self.http_client.make_request('https://its.katowice.eu/api/parkingZones')

        feature_collection = FeatureCollection.from_json(json_data=parking_zones_json)

        for feature in feature_collection.features:
            resukt = point_in_polygon(
                point=Point([19.014115, 50.258911]),
                polygon=Polygon(tuple(tuple(sublist) for sublist in feature.geometry.coordinates[0]))
            )
            print(resukt)

        return self.parking_zones_data
