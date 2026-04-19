"""Device info helpers for Ecowitt Gateway."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, IOT_MODEL_MAP, SENSOR_TYPE_MODEL_MAP


def gateway_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Gateway hub device (includes WH25 indoor sensor)."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_gateway")},
        name="Ecowitt Gateway",
        manufacturer="Ecowitt",
        model="WH25",
        configuration_url=f"http://{entry.data.get('host', '')}",
    )


def outdoor_device_info(
    entry: ConfigEntry, sensor_id: str = "", sensor_type: str = "",
    ws90_version: str = "",
) -> DeviceInfo:
    """Outdoor / WS90 sensor array (includes piezo rain)."""
    model = SENSOR_TYPE_MODEL_MAP.get(sensor_type, "WS90")
    identifier = sensor_id if sensor_id else f"{entry.entry_id}_outdoor"
    info = DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name=f"Outdoor Sensor ({model})",
        manufacturer="Ecowitt",
        model=model,
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )
    if ws90_version:
        info["sw_version"] = ws90_version
    return info


def rain_device_info(
    entry: ConfigEntry, sensor_id: str = "", sensor_type: str = "",
) -> DeviceInfo:
    """Traditional rain gauge."""
    model = SENSOR_TYPE_MODEL_MAP.get(sensor_type, "Rain Gauge")
    identifier = sensor_id if sensor_id else f"{entry.entry_id}_rain"
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name="Rain Gauge",
        manufacturer="Ecowitt",
        model=model,
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )


def channel_device_info(
    entry: ConfigEntry, channel: int | str, name: str = "",
    sensor_id: str = "", sensor_type: str = "",
) -> DeviceInfo:
    """Per-channel wireless T/H sensor."""
    model = SENSOR_TYPE_MODEL_MAP.get(sensor_type, "WH31")
    label = name.strip() if name and name.strip() else f"Channel {channel}"
    identifier = sensor_id if sensor_id else f"{entry.entry_id}_ch{channel}"
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name=label,
        manufacturer="Ecowitt",
        model=model,
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )


def soil_device_info(
    entry: ConfigEntry, channel: int | str, name: str = "",
    sensor_id: str = "", sensor_type: str = "",
) -> DeviceInfo:
    """Per-channel soil moisture sensor."""
    model = SENSOR_TYPE_MODEL_MAP.get(sensor_type, "WH51")
    label = name.strip() if name and name.strip() else f"Soil {channel}"
    identifier = sensor_id if sensor_id else f"{entry.entry_id}_soil{channel}"
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name=label,
        manufacturer="Ecowitt",
        model=model,
        via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
    )


def temp_device_info(
    entry: ConfigEntry, channel: int | str, name: str = "",
    sensor_id: str = "", sensor_type: str = "",
) -> DeviceInfo:
    """Per-channel temperature-only sensor (WH34)."""
    model = SENSOR_TYPE_MODEL_MAP.get(sensor_type, "WH34")
    label = name.strip() if name and name.strip() else f"Temp {channel}"
    identifier = sensor_id if sensor_id else f"{entry.entry_id}_temp{channel}"
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name=label,
        manufacturer="Ecowitt",
        model=model,
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