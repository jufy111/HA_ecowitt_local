"""DataUpdateCoordinator for Ecowitt Gateway."""
from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api_client import EcowittApiClient, EcowittApiError
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_SENSORS_INFO_INTERVAL, UNIT_MAP, UNIT_NORMALIZE, SENSOR_TYPE_DEVICE_MAP

_LOGGER = logging.getLogger(__name__)


import re

_NUMERIC_RE = re.compile(r"^([+-]?\d+\.?\d*)\s*(.*)")


def parse_value(val: str | None) -> float | str | None:
    """Parse ecowitt value strings like '10.8', '75%', '7.92 km/h'.

    Extracts the leading numeric portion, ignoring any trailing unit text.
    """
    if val is None:
        return None
    match = _NUMERIC_RE.match(val.strip())
    if match:
        return float(match.group(1))
    return None


def _safe_int(val, default: int = 0) -> int:
    """Convert to int, returning default if the value is non-numeric (e.g. '--')."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def extract_unit(val: str | None) -> str | None:
    """Extract trailing unit from a value string like '7.92 km/h' -> 'km/h'.

    Normalizes known variants (e.g. 'W/m2' -> 'W/m²').
    """
    if val is None:
        return None
    match = _NUMERIC_RE.match(val.strip())
    if match:
        unit = match.group(2).strip()
        if not unit:
            return None
        return UNIT_NORMALIZE.get(unit, unit)
    return None


class EcowittDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls livedata, discovers IoT devices, reads their state."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: EcowittApiClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        sensors_info_interval: int = DEFAULT_SENSORS_INFO_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.iot_devices: list[dict[str, Any]] = []
        self.valve_params: dict[str, float] = {}
        self.reset_run_time: set[int] = set()
        self._sensors_info_interval = sensors_info_interval
        self._sensors_info_last: float = 0.0
        self._sensors_info_cache: dict[str, Any] = {}

    def update_scan_interval(self, seconds: int) -> None:
        """Update polling interval (called from options flow)."""
        self.update_interval = timedelta(seconds=seconds)
        _LOGGER.info("Scan interval updated to %ds", seconds)

    def update_sensors_info_interval(self, seconds: int) -> None:
        """Update sensor info polling interval (called from options flow)."""
        self._sensors_info_interval = seconds
        _LOGGER.info("Sensors info interval updated to %ds", seconds)

    async def async_discover_iot_devices(self) -> list[dict[str, Any]]:
        """GET /get_iot_device_list to find all paired IoT devices."""
        try:
            devices = await self.client.async_get_iot_device_list()
            self.iot_devices = devices
            _LOGGER.info(
                "Discovered %d IoT device(s): %s",
                len(devices),
                [d.get("id") for d in devices],
            )
            return devices
        except EcowittApiError:
            _LOGGER.warning("Failed to discover IoT devices")
            return []

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            raw = await self.client.async_get_livedata()
            data: dict[str, Any] = {"raw": raw}

            # ── common_list ──────────────────────────────
            for item in raw.get("common_list", []):
                sid = item["id"]
                raw_val = item.get("val")
                data[f"common_{sid}"] = parse_value(raw_val)
                detected = extract_unit(raw_val)
                if detected:
                    data[f"common_{sid}_unit"] = detected
                elif "unit" in item:
                    mapped = UNIT_MAP.get(item["unit"])
                    if mapped:
                        data[f"common_{sid}_unit"] = mapped

            # ── rain ─────────────────────────────────────
            for item in raw.get("rain", []):
                sid = item["id"]
                raw_val = item.get("val")
                data[f"rain_{sid}"] = parse_value(raw_val)
                detected = extract_unit(raw_val)
                if detected:
                    data[f"rain_{sid}_unit"] = detected
                if "battery" in item:
                    data["rain_battery"] = int(item["battery"])
                    data["rain_voltage"] = float(item.get("voltage", 0))

            # ── piezoRain ────────────────────────────────
            for item in raw.get("piezoRain", []):
                sid = item["id"]
                raw_val = item.get("val")
                data[f"piezo_{sid}"] = parse_value(raw_val)
                detected = extract_unit(raw_val)
                if detected:
                    data[f"piezo_{sid}_unit"] = detected
                if "battery" in item:
                    data["piezo_battery"] = int(item["battery"])
                    data["piezo_voltage"] = float(item.get("voltage", 0))
                if "ws90_ver" in item:
                    data["ws90_version"] = item["ws90_ver"]
                if "ws90cap_volt" in item:
                    data["ws90_cap_voltage"] = float(item["ws90cap_volt"])

            # ── wh25 (indoor) ────────────────────────────
            for item in raw.get("wh25", []):
                data["indoor_temp"] = float(item.get("intemp", 0))
                data["indoor_humidity"] = parse_value(item.get("inhumi", "0"))
                temp_unit = UNIT_MAP.get(item.get("unit", "C"), "°C")
                data["indoor_temp_unit"] = temp_unit
                abs_raw = item.get("abs", "0")
                rel_raw = item.get("rel", "0")
                data["abs_pressure"] = parse_value(abs_raw)
                data["rel_pressure"] = parse_value(rel_raw)
                pressure_unit = extract_unit(abs_raw)
                if pressure_unit:
                    data["pressure_unit"] = pressure_unit

            # ── ch_aisle ─────────────────────────────────
            data["channels_present"] = []
            for item in raw.get("ch_aisle", []):
                ch = item["channel"]
                data["channels_present"].append(ch)
                data[f"ch{ch}_temp"] = float(item.get("temp", 0))
                data[f"ch{ch}_humidity"] = parse_value(item.get("humidity", "0"))
                data[f"ch{ch}_battery"] = int(item.get("battery", 0))
                data[f"ch{ch}_name"] = item.get("name", "")
                ch_temp_unit = UNIT_MAP.get(item.get("unit", "C"), "°C")
                data[f"ch{ch}_temp_unit"] = ch_temp_unit

            # ── ch_soil ──────────────────────────────────
            data["soil_channels_present"] = []
            for item in raw.get("ch_soil", []):
                ch = item["channel"]
                data["soil_channels_present"].append(ch)
                data[f"soil{ch}_humidity"] = parse_value(item.get("humidity", "0"))
                data[f"soil{ch}_battery"] = int(item.get("battery", 0))
                data[f"soil{ch}_voltage"] = float(item.get("voltage", 0))
                data[f"soil{ch}_name"] = item.get("name", "")

            # ── debug ────────────────────────────────────
            for item in raw.get("debug", []):
                data["gw_heap"] = _safe_int(item.get("heap"), 0)
                data["gw_runtime"] = _safe_int(item.get("runtime"), 0)
                data["gw_interval"] = _safe_int(item.get("usr_interval"), 60)

            # ── presence flags ───────────────────────────
            data["has_rain"] = bool(raw.get("rain"))
            data["has_piezo"] = bool(raw.get("piezoRain"))
            data["has_indoor"] = bool(raw.get("wh25"))
            data["has_outdoor"] = any(
                k in data for k in ["common_0x02", "common_0x07"]
            )

            # ── sensor info (rssi, signal) — throttled ───
            now = time.monotonic()
            if now - self._sensors_info_last >= self._sensors_info_interval:
                try:
                    sensors_info = await self.client.async_get_sensors_info()
                    si_data: dict[str, Any] = {}
                    for sensor in sensors_info:
                        if sensor.get("id") == "FFFFFFFF":
                            continue
                        stype = str(sensor.get("type", ""))
                        device_key = SENSOR_TYPE_DEVICE_MAP.get(stype)
                        if not device_key:
                            continue
                        rssi = sensor.get("rssi")
                        signal = sensor.get("signal")
                        if rssi and rssi != "--":
                            si_data[f"{device_key}_rssi"] = _safe_int(rssi)
                        if signal and signal != "--":
                            si_data[f"{device_key}_signal"] = _safe_int(signal)
                        sid = sensor.get("id")
                        if sid and sid != "FFFFFFFF":
                            si_data[f"{device_key}_sensor_id"] = sid
                    self._sensors_info_cache = si_data
                    self._sensors_info_last = now
                except EcowittApiError:
                    _LOGGER.debug("Sensor info fetch failed, using cached")
            data.update(self._sensors_info_cache)

            # ── Refresh IoT device list ──────────────────
            try:
                iot_list = await self.client.async_get_iot_device_list()
                self.iot_devices = iot_list
            except EcowittApiError:
                _LOGGER.debug("IoT device list fetch failed, using cached")

            data["iot_device_list"] = self.iot_devices

            # ── Fetch full status for each IoT device ────
            for dev in self.iot_devices:
                dev_id = dev["id"]
                model = dev.get("model", 1)
                try:
                    iot_data = await self.client.async_read_iot_device(dev_id, model)
                    data[f"iot_{dev_id}"] = iot_data
                except EcowittApiError:
                    _LOGGER.warning("Failed to read IoT device %s", dev_id)
                    data[f"iot_{dev_id}"] = {}

            return data

        except EcowittApiError as err:
            raise UpdateFailed(f"Error fetching Ecowitt data: {err}") from err