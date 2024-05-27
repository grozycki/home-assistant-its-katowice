# coding=utf-8

from abc import ABC
from dataclasses import dataclass, make_dataclass

from marshmallow import Schema, fields, post_load, INCLUDE
from shapely.geometry import Point as SPoint, Polygon as SPolygon


@dataclass(frozen=True, kw_only=True)
class Geometry:
    type: str
    coordinates: list[list[list[float]]]


class GeometrySchema(Schema):
    type = fields.Str()
    coordinates = fields.List(fields.List(fields.List(fields.Float())))

    @post_load
    def make_geometry(self, data, **kwargs):
        return Geometry(**data)


@dataclass(frozen=True, kw_only=False)
class Properties:
    pass


class PropertiesSchema(Schema):
    class Meta:
        unknown = INCLUDE

    @post_load
    def make_properties(self, data, **kwargs):
        return make_dataclass('Properties', data.keys())(**data)


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
    def from_json(cls, json_data: str, context: dict | None = None) -> "FeatureCollection":
        future_collection: FeatureCollection = FeatureCollectionSchema(context=context).loads(json_data=json_data)
        return future_collection


class FeatureCollectionSchema(Schema):
    type = fields.Str()
    features = fields.List(fields.Nested(FeatureSchema))

    @post_load
    def make_feature_collection(self, data, **kwargs):
        return FeatureCollection(**data)


@dataclass(frozen=True, kw_only=True)
class Coordinate:
    latitude: float
    longitude: float


class Shape(ABC):
    @classmethod
    def from_geometry(cls, geometry: Geometry):
        raise NotImplementedError


class Point(Shape):
    def __init__(self, coordinate: Coordinate):
        self.coordinate = coordinate

    def __str__(self):
        return f"Point({self.coordinate.latitude}, {self.coordinate.longitude})"

    @classmethod
    def from_geometry(cls, geometry: Geometry):
        pass


class Polygon(Shape):
    def __init__(self, coordinates: list[Coordinate]):
        self.coordinates = coordinates

    def __str__(self):
        return f"Polygon({', '.join([str(coordinate) for coordinate in self.coordinates])})"

    @classmethod
    def from_geometry(cls, geometry: Geometry):
        coordinates = [
            Coordinate(latitude=latitude, longitude=longitude) for longitude, latitude, in geometry.coordinates[0]
        ]
        return Polygon(coordinates=coordinates)


def point_in_polygon(point: Point, polygon: Polygon) -> bool:
    return SPoint(point.coordinate.latitude, point.coordinate.longitude).within(
        SPolygon([(coordinate.latitude, coordinate.longitude) for coordinate in polygon.coordinates]))
