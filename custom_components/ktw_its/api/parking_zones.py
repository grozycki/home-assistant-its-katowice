# coding=utf-8
from dataclasses import dataclass
from datetime import datetime
from logging import Logger

from homeassistant.core import Event, EventStateChangedData, State

from custom_components.ktw_its.api.geo import FeatureCollection, point_in_polygon, Point, Polygon, Coordinate
from custom_components.ktw_its.api.http_client import HttpClientInterface
from custom_components.ktw_its.dto import KtwItsSensorDto


@dataclass(frozen=True, kw_only=True)
class ParkingZone:
    code: str
    polygon: Polygon

    def __str__(self) -> str:
        return f"ParkingZone[code={self.code}]"


class ParkingZoneRepository:
    def __init__(self, logger: Logger) -> None:
        self.__parking_zones: dict[str, ParkingZone] = {}
        self.__logger: Logger = logger

    def add_parking_zone(self, parking_zone: ParkingZone) -> None:
        self.__logger.debug(f"Adding parking zone: {parking_zone}")
        self.__parking_zones[parking_zone.code] = parking_zone

    def get_parking_zone(self, name: str) -> ParkingZone | None:
        return self.__parking_zones.get(name)

    def get_all(self) -> dict[str, ParkingZone]:
        return self.__parking_zones

    def find_by_point(self, point: Point) -> ParkingZone | None:
        self.__logger.debug(f"Finding parking zone for point: {point}")
        for parking_zone in self.__parking_zones.values():
            self.__logger.debug(f"Checking parking zone: {parking_zone}")
            if point_in_polygon(point=point, polygon=parking_zone.polygon):
                return parking_zone
        return None


class ParkingZonesApi:
    def __init__(
            self,
            http_client: HttpClientInterface,
            repository: ParkingZoneRepository,
            logger: Logger
    ) -> None:
        self.__http_client: HttpClientInterface = http_client
        self.__repository: ParkingZoneRepository = repository
        self.__logger: Logger = logger
        self.__parking_zones_data: dict[str, KtwItsSensorDto] = {}
        self.__parking_zones_data_valid_to: datetime | None = None

    async def fetch_data(self) -> dict[str, KtwItsSensorDto]:
        self.__logger.debug("Fetching parking zones data")
        # if (self.parking_zones_data_valid_to is not None
        #         and self.parking_zones_data_valid_to >= datetime.now(timezone.utc)):
        #     self.logger.debug("Parking zones data is still valid")
        #     return self.parking_zones_data

        parking_zones_json = await self.__http_client.make_request('https://its.katowice.eu/api/parkingZones')

        feature_collection = FeatureCollection.from_json(json_data=parking_zones_json)

        for feature in feature_collection.features:
            self.__repository.add_parking_zone(
                ParkingZone(
                    code=feature.properties.code,
                    polygon=Polygon.from_geometry(geometry=feature.geometry)
                )
            )

            # result = point_in_polygon(
            #     point=Point(Coordinate(latitude=19.014115, longitude=50.258911)),
            #     polygon=Polygon.from_geometry(geometry=feature.geometry)
            # )
            # print(result)

        return self.__parking_zones_data

    def on_entity_state_change(self, event: Event[EventStateChangedData]):
        old_state: State | None = event.data["old_state"]
        new_state: State | None = event.data["new_state"]
        old_zone = self.__repository.find_by_point(point=Point(Coordinate(
            latitude=old_state.attributes.get('latitude'),
            longitude=old_state.attributes.get('longitude')
        )))
        new_zone = self.__repository.find_by_point(point=Point(Coordinate(
            latitude=new_state.attributes.get('latitude'),
            longitude=new_state.attributes.get('longitude')
        )))

        self.__logger.warning(event.data["entity_id"])
        self.__logger.warning(old_state)
        self.__logger.warning(new_state)
        self.__logger.warning(old_zone)
        self.__logger.warning(new_zone)
