from dataclasses import dataclass
from datetime import datetime

from homeassistant.const import Platform
from custom_components.ktw_its.image import KtwItsImageEntityDescription
from custom_components.ktw_its.sensor import KtwItsSensorEntityDescription


@dataclass(frozen=False)
class KtwItsCameraImageDto:
    image_last_updated: datetime | None = None
    entity_description: KtwItsImageEntityDescription | None = None
    state_attributes: dict[str, str | float | datetime] | None = None
    platform: Platform = Platform.IMAGE


@dataclass(frozen=True)
class KtwItsSensorDto:
    state: str | int | float | datetime
    entity_description: KtwItsSensorEntityDescription
    state_attributes: dict[str, str | float | datetime] | None = None
    platform: Platform = Platform.SENSOR
