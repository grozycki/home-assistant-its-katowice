import voluptuous as vol
from homeassistant.const import (
    CONF_TYPE,
)
from homeassistant.helpers.config_validation import TRIGGER_BASE_SCHEMA

TRIGGER_TYPES = {"parking_zone_enter", "parking_zone_leave"}

TRIGGER_SCHEMA = TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
    }
)
