# coding=utf-8

from abc import ABC, abstractmethod, ABCMeta
from dataclasses import dataclass, make_dataclass
from typing import List

from marshmallow import Schema, fields, post_load, INCLUDE, pre_load
from shapely.geometry import Point, Polygon


@dataclass(frozen=True, kw_only=True)
class Geometry:
    type: str
    coordinates: List[List[List[float]]]


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
    features: List[Feature]

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


def point_in_polygon(point: Point, polygon: Polygon) -> bool:
    return point.within(polygon)
