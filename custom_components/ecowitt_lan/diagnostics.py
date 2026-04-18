"""Diagnostics for Ecowitt Gateway."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    return {
        "config": {
            "host": entry.data.get("host"),
            "port": entry.data.get("port"),
        },
        "options": dict(entry.options),
        "iot_devices_discovered": coordinator.iot_devices,
        "raw_livedata": coordinator.data.get("raw", {}),
        "parsed_data": {
            k: v for k, v in coordinator.data.items()
            if k not in ("raw",) and not k.startswith("_")
        },
    }