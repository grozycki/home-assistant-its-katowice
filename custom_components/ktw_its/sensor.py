from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.core import callback
from .const import (
    DOMAIN,
    DEFAULT_NAME, ATTRIBUTION
)
from datetime import timedelta

from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_NAME,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfSpeed,
)

SCAN_INTERVAL = timedelta(seconds=60)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    api_data = await coordinator.api.fetch_data()
    entities = [KtwItsSensorEntity(coordinator, dto.entity_description) for dto in api_data.values()]
    async_add_entities(entities, False)


class KtwItsSensorEntity(CoordinatorEntity, SensorEntity):
    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _icon: str | None = None
    _state_attributes: dict[str, str | float | datetime] | None = None

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
