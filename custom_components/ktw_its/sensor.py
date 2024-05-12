# coding=utf-8
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from .const import (
    DOMAIN,
    ATTRIBUTION, STATE_ATTR_UPDATE_DATE, STATE_ATTR_COLOR, STATE_ATTR_LONGITUDE, STATE_ATTR_LATITUDE
)

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    from custom_components.ktw_its import KtwItsDataUpdateCoordinator
    coordinator: KtwItsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    api_data = await coordinator.fetch_data()
    entities = [
        KtwItsSensorEntity(coordinator=coordinator, entity_description=dto.entity_description)
        for dto in api_data.values() if dto.platform == Platform.SENSOR
    ]
    async_add_entities(entities)


class KtwItsSensorEntity(CoordinatorEntity, SensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _icon: str | None = None
    _state_attributes: dict[str, str | float | datetime] | None = None
    _unrecorded_attributes = frozenset({
        STATE_ATTR_UPDATE_DATE,
        STATE_ATTR_COLOR,
        STATE_ATTR_LONGITUDE,
        STATE_ATTR_LATITUDE
    })

    def __init__(
            self,
            coordinator: DataUpdateCoordinator,
            entity_description: KtwItsSensorEntityDescription
    ) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=entity_description.group)
        self.entity_description = entity_description
        self._attr_unique_id = entity_description.key
        self._attr_name = entity_description.name
        self._attr_device_info = entity_description.device_info
        self._icon = entity_description.icon
        self.entity_id = 'sensor.{0}'.format(entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, str | float | datetime] | None:
        return self._state_attributes

    @property
    def icon(self) -> str | None:
        return self._icon

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.coordinator.data[self.entity_description.key]:
            self._attr_native_value = self.coordinator.data[self.entity_description.key].state
            self._state_attributes = self.coordinator.data[self.entity_description.key].state_attributes
            self.async_write_ha_state()


@dataclass(frozen=True, kw_only=True)
class KtwItsSensorEntityDescription(SensorEntityDescription):
    group: str
    key: str
    device_class: SensorDeviceClass | None = None
    native_unit_of_measurement: str | None = None
    state_class: SensorStateClass | str | None = SensorStateClass.MEASUREMENT
    icon: str | None = None
    device_info: DeviceInfo | None = None
    options: list[str] | None = None
    name: str | None = None
    entity_category: EntityCategory | None = None
