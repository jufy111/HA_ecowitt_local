"""Device info helpers for Ecowitt Gateway."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, IOT_MODEL_MAP


def gateway_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Gateway hub device (includes WH25 indoor sensor)."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_gateway")},
        name="Ecowitt Gateway",
        manufacturer="Ecowitt",
        model="WH25",
        configuration_url=f"http://{entry.data.get('host', '')}",
    )


def outdoor_device_info(entry: ConfigEntry, ws90_version: str = "") -> DeviceInfo:
    """Outdoor / WS90 sensor array (includes piezo rain)."""
    info = DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_outdoor")},
        name="Outdoor Sensor (WS90)",
        manufacturer="Ecowitt",
        model="WS90",
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )
    if ws90_version:
        info["sw_version"] = ws90_version
    return info


def rain_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Traditional rain gauge."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_rain")},
        name="Rain Gauge",
        manufacturer="Ecowitt",
        model="Rain Gauge",
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )



def channel_device_info(
    entry: ConfigEntry, channel: int | str, name: str = ""
) -> DeviceInfo:
    """Per-channel wireless T/H sensor."""
    label = name.strip() if name and name.strip() else f"Channel {channel}"
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_ch{channel}")},
        name=f"{label} Sensor",
        manufacturer="Ecowitt",
        model="WH31 / WN31",
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )


def soil_device_info(
    entry: ConfigEntry, channel: int | str, name: str = ""
) -> DeviceInfo:
    """Per-channel soil moisture sensor."""
    label = name.strip() if name and name.strip() else f"Soil {channel}"
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_soil{channel}")},
        name=f"{label} Sensor",
        manufacturer="Ecowitt",
        model="WH51",
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )


def iot_device_info(
    entry: ConfigEntry, dev_id: int, model: int, iot_data: dict
) -> DeviceInfo:
    """IoT device (WFC01 etc)."""
    model_name = IOT_MODEL_MAP.get(model, f"Model {model}")
    nickname = iot_data.get("nickname", f"{model_name} {dev_id}")
    info = DeviceInfo(
        identifiers={(DOMAIN, f"iot_{dev_id}")},
        name=nickname,
        manufacturer="Ecowitt",
        model=model_name,
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )
    version = iot_data.get("version") or iot_data.get("ver")
    if version:
        info["sw_version"] = str(version)
    return info