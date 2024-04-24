from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.components.image import (
    ImageEntityDescription,
    ImageEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)
from . import KtwItsDataUpdateCoordinator
from .const import (
    DOMAIN,
    DEFAULT_NAME
)

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = await _get_image_entities(hass, coordinator)
    async_add_entities(entities, False)


async def _get_image_entities(hass: HomeAssistant, coordinator: KtwItsDataUpdateCoordinator) \
        -> Iterable[KtwItsImageEntity]:
    descriptions = []
    cameras = await coordinator.get_cameras()
    for feature in cameras['features']:
        if feature['properties']['state'] == 1:
            if feature['properties']['type'] == 'ptz':
                count = 4
            else:
                count = 1
            i = 0
            while i < count:
                descriptions.append(KtwItsImageEntity(
                    hass,
                    coordinator,
                    KtwItsImageEntityDescription(
                        key=str(feature['properties']['id']) + '-' + str(i),
                        camera_id=feature['properties']['id'],
                        camera_name=feature['properties']['name'],
                        camera_description=feature['properties']['description'],
                        image_id=i,
                        longitude=feature['geometry']['coordinates'][0],
                        latitude=feature['geometry']['coordinates'][1],
                    )
                ))
                i += 1

    return descriptions


class KtwItsImageEntity(ImageEntity):
    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: KtwItsDataUpdateCoordinator,
            description: KtwItsImageEntityDescription
    ) -> None:
        ImageEntity.__init__(self, hass)
        self.entity_description = description
        self._attr_entity_picture = 'https://its.katowice.eu/mapa/static/img/marker_camera_ptz--light.2d8c239a.svg'
        _device_id = "ktw-its"
        self._attr_has_entity_name = True
        self._attr_name = description.camera_name + " " + description.camera_description
        self._attr_unique_id = f"{_device_id}-{description.key.lower()}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(description.camera_id))},
            manufacturer=DEFAULT_NAME,
            name=DEFAULT_NAME,
        )
        self.coordinator = coordinator
        self.camera_id: int = description.camera_id
        self.image_id: int = description.image_id
        self._latitude: float = description.latitude
        self._longitude: float = description.longitude

    @property
    def extra_state_attributes(self) -> dict[str, str | float]:
        return {
            "latitude": self._latitude,
            "longitude": self._longitude,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated coordinator."""
        ##self._attr_image_url = 'https://its.katowice.eu/api/camera/image/372/image24-04-10_18-49-57-01_00013.jpg'
        ##self._attr_image_last_updated = datetime.now()
        ##super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        print('async_image')
        # if self._cached_image:
        #     return self._cached_image.content

        camera_image_dto = await self.coordinator.get_camera_image_data(self.camera_id, self.image_id)
        print(camera_image_dto)
        self._attr_image_last_updated = camera_image_dto.last_updated
        print(self._attr_image_last_updated)


        return await self.coordinator.get_camera_image(self.camera_id, self.image_id)


@dataclass(frozen=True, kw_only=True)
class KtwItsImageEntityDescription(ImageEntityDescription):
    """A class that describes image entities."""
    camera_id: int
    camera_name: str
    camera_description: str
    image_id: int
    latitude: float
    longitude: float
