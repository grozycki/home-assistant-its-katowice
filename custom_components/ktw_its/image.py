from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, datetime

from homeassistant.components.image import (
    ImageEntityDescription,
    ImageEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import (
    DOMAIN,
    ATTRIBUTION, STATE_ATTR_UPDATE_DATE, STATE_ATTR_COLOR, STATE_ATTR_LONGITUDE, STATE_ATTR_LATITUDE
)

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    from ktw_its import KtwItsDataUpdateCoordinator
    coordinator: KtwItsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    api_data = await coordinator.fetch_data()
    entities = [KtwItsImageEntity(
        coordinator=coordinator,
        entity_description=dto.entity_description,
        hass=hass
    ) for dto in api_data.values() if dto.platform == Platform.IMAGE]
    async_add_entities(entities)


class KtwItsImageEntity(CoordinatorEntity, ImageEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _icon: str | None = None
    __state_attributes: dict[str, str | float | datetime] | None = None
    _unrecorded_attributes = frozenset({
        STATE_ATTR_UPDATE_DATE,
        STATE_ATTR_COLOR,
        STATE_ATTR_LONGITUDE,
        STATE_ATTR_LATITUDE
    })

    def __init__(
            self,
            hass: HomeAssistant,
            coordinator: KtwItsDataUpdateCoordinator,
            entity_description: KtwItsImageEntityDescription
    ) -> None:
        super().__init__(coordinator, context=entity_description.group)
        ImageEntity.__init__(self, hass=hass)
        self.entity_description = entity_description
        self._attr_unique_id = entity_description.key
        self._attr_name = entity_description.name
        self._attr_device_info = entity_description.device_info
        self._icon = entity_description.icon
        self.entity_id = 'image.{0}'.format(entity_description.key)

        self._attr_entity_picture = 'https://its.katowice.eu/mapa/static/img/marker_camera_ptz--light.2d8c239a.svg'

        self.__coordinator = coordinator
        self.__camera_id: int = entity_description.camera_id
        self.__image_id: int = entity_description.image_id

    @property
    def extra_state_attributes(self) -> dict[str, str | float | datetime] | None:
        return self.__state_attributes

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.data[self.entity_description.key]:
            self._attr_image_last_updated = self.coordinator.data[self.entity_description.key].image_last_updated
            self.__state_attributes = self.coordinator.data[self.entity_description.key].state_attributes
            self.async_write_ha_state()

    async def async_image(self) -> bytes | None:
        image = await self.__coordinator.get_camera_image(self.__camera_id, self.__image_id)
        await self.coordinator.async_request_refresh()
        return image


@dataclass(frozen=True, kw_only=True)
class KtwItsImageEntityDescription(ImageEntityDescription):
    """A class that describes image entities."""
    camera_id: int
    camera_name: str
    camera_description: str
    image_id: int
    group: str
    key: str
    icon: str | None = None
    device_info: DeviceInfo | None = None
    options: list[str] | None = None
    name: str | None = None
