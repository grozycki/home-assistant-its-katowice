# coding=utf-8
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from logging import Logger

from homeassistant.core import Event, EventStateChangedData, State, EventBus

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
            event_bus: EventBus,
            logger: Logger
    ) -> None:
        self.__http_client: HttpClientInterface = http_client
        self.__repository: ParkingZoneRepository = repository
        self.__event_bus: EventBus = event_bus
        self.__logger: Logger = logger
        self.__parking_zones_data: dict[str, KtwItsSensorDto] = {}
        self.__parking_zones_data_valid_to: datetime | None = None

    async def fetch_data(self) -> None:
        self.__logger.debug("Fetching parking zones data")
        if (self.__parking_zones_data_valid_to is not None
                and self.__parking_zones_data_valid_to >= datetime.now(timezone.utc)):
            self.__logger.debug("Parking zones data is still valid")
            return

        parking_zones_json = await self.__http_client.make_request('https://its.katowice.eu/api/parkingZones')
        feature_collection = FeatureCollection.from_json(json_data=parking_zones_json)
        for feature in feature_collection.features:
            self.__repository.add_parking_zone(
                ParkingZone(
                    code=feature.properties.code,
                    polygon=Polygon.from_geometry(geometry=feature.geometry)
                )
            )
        self.__parking_zones_data_valid_to = datetime.now(timezone.utc) + timedelta(minutes=60)

    def on_entity_state_change(self, event: Event[EventStateChangedData]) -> None:
        old_zone: ParkingZone | None = None
        new_zone: ParkingZone | None = None
        entity_id: str = event.data["entity_id"]
        old_state: State | None = event.data["old_state"]
        new_state: State | None = event.data["new_state"]

        if old_state is not None:
            old_zone = self.__repository.find_by_point(point=Point(Coordinate(
                latitude=old_state.attributes.get('latitude'),  # type: ignore
                longitude=old_state.attributes.get('longitude')  # type: ignore
            )))

        if new_state is not None:
            new_zone = self.__repository.find_by_point(point=Point(Coordinate(
                latitude=new_state.attributes.get('latitude'),  # type: ignore
                longitude=new_state.attributes.get('longitude')  # type: ignore
            )))

        if old_zone != new_zone:
            self.__logger.debug(f"Entity {entity_id} changed zone from {old_zone} to {new_zone}")

            if old_zone is not None:
                event_data = {
                    "device_id": entity_id,
                    "entity_id": entity_id,
                    "type": "parking_zone_leave",
                }
                self.__event_bus.async_fire("ktw_its_event", event_data)

            if new_zone is not None:
                event_data = {
                    "device_id": entity_id,
                    "entity_id": entity_id,
                    "type": "parking_zone_enter",
                }
                self.__event_bus.async_fire("ktw_its_event", event_data)
