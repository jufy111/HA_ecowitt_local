"""Sensor platform for Ecowitt Gateway."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, COMMON_LIST_MAP, RAIN_MAP, IOT_MODEL_MAP, BATTERY_LEVEL_MAP
from .coordinator import EcowittDataCoordinator
from .device import (
    gateway_device_info,
    outdoor_device_info,
    rain_device_info,
    channel_device_info,
    soil_device_info,
    iot_device_info,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcowittDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list[SensorEntity] = []

    # ═══════════════════════════════════════════════════════
    # GATEWAY DEVICE — diagnostics only
    # ═══════════════════════════════════════════════════════
    gw_info = gateway_device_info(entry)

    if "gw_runtime" in coordinator.data:
        entities.append(EcowittSimpleSensor(
            coordinator, entry, "gw_runtime", "Gateway Uptime",
            gw_info, icon="mdi:timer", unit="s",
            state_class=SensorStateClass.TOTAL_INCREASING,
        ))
    if "gw_heap" in coordinator.data:
        entities.append(EcowittSimpleSensor(
            coordinator, entry, "gw_heap", "Gateway Free Memory",
            gw_info, icon="mdi:memory", unit="bytes",
            state_class=SensorStateClass.MEASUREMENT,
        ))
    if "gw_interval" in coordinator.data:
        entities.append(EcowittSimpleSensor(
            coordinator, entry, "gw_interval", "Gateway Report Interval",
            gw_info, icon="mdi:update", unit="s",
        ))

    # ═══════════════════════════════════════════════════════
    # OUTDOOR DEVICE (WS90) — weather sensors + piezo rain
    # ═══════════════════════════════════════════════════════
    has_outdoor = coordinator.data.get("has_outdoor")
    has_piezo = coordinator.data.get("has_piezo")

    if has_outdoor or has_piezo:
        ws90_ver = coordinator.data.get("ws90_version", "")
        outdoor_info = outdoor_device_info(entry, ws90_ver)

        # common_list weather sensors
        if has_outdoor:
            for sensor_id, meta in COMMON_LIST_MAP.items():
                key = f"common_{sensor_id}"
                if key in coordinator.data:
                    entities.append(
                        EcowittMappedSensor(coordinator, entry, key, meta, outdoor_info)
                    )

            if "ws90_cap_voltage" in coordinator.data:
                entities.append(EcowittSimpleSensor(
                    coordinator, entry, "ws90_cap_voltage", "Capacitor Voltage",
                    outdoor_info,
                    device_class=SensorDeviceClass.VOLTAGE, unit="V",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=1,
                ))

        # piezo rain sensors
        if has_piezo:
            for sensor_id, meta in RAIN_MAP.items():
                key = f"piezo_{sensor_id}"
                if key in coordinator.data:
                    entities.append(EcowittMappedSensor(
                        coordinator, entry, key,
                        {**meta, "name": f"Piezo Rain {meta['name']}"},
                        outdoor_info,
                    ))

            if "piezo_battery" in coordinator.data:
                entities.append(EcowittSimpleSensor(
                    coordinator, entry, "piezo_battery", "Battery Level",
                    outdoor_info,
                    device_class=SensorDeviceClass.BATTERY,
                    unit=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                    value_map=BATTERY_LEVEL_MAP,
                ))
            if "piezo_voltage" in coordinator.data:
                entities.append(EcowittSimpleSensor(
                    coordinator, entry, "piezo_voltage", "Battery Voltage",
                    outdoor_info,
                    device_class=SensorDeviceClass.VOLTAGE, unit="V",
                    state_class=SensorStateClass.MEASUREMENT,
                    suggested_display_precision=1,
                ))

    # ═══════════════════════════════════════════════════════
    # RAIN GAUGE DEVICE
    # ═══════════════════════════════════════════════════════
    if coordinator.data.get("has_rain"):
        rain_info = rain_device_info(entry)

        for sensor_id, meta in RAIN_MAP.items():
            key = f"rain_{sensor_id}"
            if key in coordinator.data:
                entities.append(EcowittMappedSensor(
                    coordinator, entry, key,
                    {**meta, "name": f"Rain {meta['name']}"},
                    rain_info,
                ))

        if "rain_battery" in coordinator.data:
            entities.append(EcowittSimpleSensor(
                coordinator, entry, "rain_battery", "Battery Level",
                rain_info,
                device_class=SensorDeviceClass.BATTERY,
                unit=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                value_map=BATTERY_LEVEL_MAP,
            ))
        if "rain_voltage" in coordinator.data:
            entities.append(EcowittSimpleSensor(
                coordinator, entry, "rain_voltage", "Battery Voltage",
                rain_info,
                device_class=SensorDeviceClass.VOLTAGE, unit="V",
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
            ))

    # ═══════════════════════════════════════════════════════
    # INDOOR SENSORS (on gateway device)
    # ═══════════════════════════════════════════════════════
    if coordinator.data.get("has_indoor"):
        indoor_temp_unit = coordinator.data.get("indoor_temp_unit", "°C")
        pressure_unit = coordinator.data.get("pressure_unit", "hPa")
        entities.extend([
            EcowittSimpleSensor(
                coordinator, entry, "indoor_temp", "Temperature",
                gw_info,
                device_class=SensorDeviceClass.TEMPERATURE,
                unit=indoor_temp_unit,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
            ),
            EcowittSimpleSensor(
                coordinator, entry, "indoor_humidity", "Humidity",
                gw_info,
                device_class=SensorDeviceClass.HUMIDITY,
                unit=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=0,
            ),
            EcowittSimpleSensor(
                coordinator, entry, "rel_pressure", "Relative Pressure",
                gw_info,
                device_class=SensorDeviceClass.PRESSURE,
                unit=pressure_unit,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
            ),
            EcowittSimpleSensor(
                coordinator, entry, "abs_pressure", "Absolute Pressure",
                gw_info,
                device_class=SensorDeviceClass.PRESSURE,
                unit=pressure_unit,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
            ),
        ])

    # ═══════════════════════════════════════════════════════
    # CHANNEL DEVICES (1 device per channel)
    # ═══════════════════════════════════════════════════════
    for ch in coordinator.data.get("channels_present", []):
        ch_name = coordinator.data.get(f"ch{ch}_name", "")
        ch_info = channel_device_info(entry, ch, ch_name)
        ch_temp_unit = coordinator.data.get(f"ch{ch}_temp_unit", "°C")

        entities.extend([
            EcowittSimpleSensor(
                coordinator, entry, f"ch{ch}_temp", "Temperature",
                ch_info,
                device_class=SensorDeviceClass.TEMPERATURE,
                unit=ch_temp_unit,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
            ),
            EcowittSimpleSensor(
                coordinator, entry, f"ch{ch}_humidity", "Humidity",
                ch_info,
                device_class=SensorDeviceClass.HUMIDITY,
                unit=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=0,
            ),
            EcowittSimpleSensor(
                coordinator, entry, f"ch{ch}_battery", "Battery",
                ch_info,
                device_class=SensorDeviceClass.BATTERY,
                state_class=SensorStateClass.MEASUREMENT,
                unit=PERCENTAGE,
                value_map=BATTERY_LEVEL_MAP,
            ),
        ])

    # ═══════════════════════════════════════════════════════
    # SOIL DEVICES (1 device per channel)
    # ═══════════════════════════════════════════════════════
    for ch in coordinator.data.get("soil_channels_present", []):
        soil_name = coordinator.data.get(f"soil{ch}_name", "")
        soil_info = soil_device_info(entry, ch, soil_name)

        entities.extend([
            EcowittSimpleSensor(
                coordinator, entry, f"soil{ch}_humidity", "Moisture",
                soil_info,
                device_class=SensorDeviceClass.MOISTURE,
                unit=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=0,
            ),
            EcowittSimpleSensor(
                coordinator, entry, f"soil{ch}_voltage", "Battery Voltage",
                soil_info,
                device_class=SensorDeviceClass.VOLTAGE,
                unit="V",
                state_class=SensorStateClass.MEASUREMENT,
                suggested_display_precision=1,
            ),
            EcowittSimpleSensor(
                coordinator, entry, f"soil{ch}_battery", "Battery",
                soil_info,
                device_class=SensorDeviceClass.BATTERY,
                state_class=SensorStateClass.MEASUREMENT,
                unit=PERCENTAGE,
                value_map=BATTERY_LEVEL_MAP,
            ),
        ])



    # ═══════════════════════════════════════════════════════
    # IOT DEVICES (auto-discovered, 1 device per IoT)
    # ═══════════════════════════════════════════════════════
    for dev in coordinator.iot_devices:
        dev_id = dev["id"]
        model = dev.get("model", 1)
        iot_data = coordinator.data.get(f"iot_{dev_id}", {})
        if not iot_data:
            continue

        dev_info = iot_device_info(entry, dev_id, model, iot_data)
        nickname = iot_data.get("nickname", f"{IOT_MODEL_MAP.get(model, 'IoT')} {dev_id}")

        if model == 1:  # WFC01
            entities.extend(_create_wfc01_sensors(
                coordinator, entry, dev_id, dev_info
            ))

    async_add_entities(entities)


def _create_wfc01_sensors(
    coordinator: EcowittDataCoordinator,
    entry: ConfigEntry,
    dev_id: int,
    device_info: DeviceInfo,
) -> list[SensorEntity]:
    """Create sensors for a WFC01 water valve controller."""
    return [
        EcowittIoTSensor(
            coordinator, entry, dev_id, "water_temp", "Water Temperature",
            device_info,
            device_class=SensorDeviceClass.TEMPERATURE,
            unit=coordinator.data.get("indoor_temp_unit", "°C"),
            state_class=SensorStateClass.MEASUREMENT,
        ),
        EcowittIoTSensor(
            coordinator, entry, dev_id, "water_total", "Total Water Used",
            device_info,
            icon="mdi:water", unit="m³",
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        EcowittIoTSensor(
            coordinator, entry, dev_id, "happen_water", "Session Start Water Value",
            device_info,
            icon="mdi:water-outline", unit="m³",
            state_class=SensorStateClass.TOTAL,
        ),
        EcowittSessionWaterUsageSensor(
            coordinator, entry, dev_id, device_info,
        ),
        EcowittIoTSensor(
            coordinator, entry, dev_id, "flow_velocity", "Flow Rate",
            device_info,
            icon="mdi:speedometer", unit="L/min",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        EcowittIoTSensor(
            coordinator, entry, dev_id, "run_time", "Run Time (Polled)",
            device_info,
            icon="mdi:timer-check-outline", unit="s",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        EcowittValveRunTimeSensor(
            coordinator, entry, dev_id, device_info,
        ),
        EcowittIoTSensor(
            coordinator, entry, dev_id, "wfc01batt", "Battery",
            device_info,
            device_class=SensorDeviceClass.BATTERY,
            state_class=SensorStateClass.MEASUREMENT,
            unit=PERCENTAGE,
            value_map=BATTERY_LEVEL_MAP,
        ),
        EcowittIoTSensor(
            coordinator, entry, dev_id, "rssi", "RF Signal",
            device_info,
            icon="mdi:signal",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        EcowittIoTSensor(
            coordinator, entry, dev_id, "gw_rssi", "Gateway RSSI",
            device_info,
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
            unit="dBm",
            state_class=SensorStateClass.MEASUREMENT,
        ),
    ]


# ─── Entity Classes ─────────────────────────────────────

class EcowittMappedSensor(CoordinatorEntity[EcowittDataCoordinator], SensorEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor using const maps (COMMON_LIST_MAP, RAIN_MAP)."""

    def __init__(self, coordinator, entry, data_key, meta, device_info):
        super().__init__(coordinator)
        self._data_key = data_key
        self._meta = meta
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        self._attr_name = meta["name"]
        self._attr_device_info = device_info
        self._attr_has_entity_name = True

        dc = meta.get("device_class")
        if dc:
            self._attr_device_class = SensorDeviceClass(dc) if isinstance(dc, str) else dc
        sc = meta.get("state_class")
        if sc:
            self._attr_state_class = SensorStateClass(sc) if isinstance(sc, str) else sc
        if "icon" in meta:
            self._attr_icon = meta["icon"]

        self._attr_native_unit_of_measurement = (
            coordinator.data.get(f"{data_key}_unit") or meta.get("unit")
        )
        self._attr_native_value = coordinator.data.get(data_key)

    @callback
    def _handle_coordinator_update(self) -> None:
        detected = self.coordinator.data.get(f"{self._data_key}_unit")
        self._attr_native_unit_of_measurement = detected or self._meta.get("unit")
        self._attr_native_value = self.coordinator.data.get(self._data_key)
        self.async_write_ha_state()


class EcowittSimpleSensor(CoordinatorEntity[EcowittDataCoordinator], SensorEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor reading a direct key from coordinator.data."""

    def __init__(
        self, coordinator, entry, data_key, name, device_info,
        device_class=None, unit=None, state_class=None, icon=None,
        value_map=None, suggested_display_precision=None,
    ):
        super().__init__(coordinator)
        self._data_key = data_key
        self._value_map = value_map
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        self._attr_name = name
        self._attr_device_info = device_info
        self._attr_has_entity_name = True

        if device_class:
            self._attr_device_class = device_class
        if unit:
            self._attr_native_unit_of_measurement = unit
        if state_class:
            self._attr_state_class = state_class
        if icon:
            self._attr_icon = icon
        if suggested_display_precision is not None:
            self._attr_suggested_display_precision = suggested_display_precision

        self._update_native_value()

    def _update_native_value(self) -> None:
        raw = self.coordinator.data.get(self._data_key)
        if raw is None:
            self._attr_native_value = None
        elif self._value_map:
            try:
                self._attr_native_value = self._value_map.get(int(raw), raw)
            except (ValueError, TypeError):
                self._attr_native_value = raw
        else:
            self._attr_native_value = raw

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_native_value()
        self.async_write_ha_state()


class EcowittIoTSensor(CoordinatorEntity[EcowittDataCoordinator], SensorEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """Sensor from nested iot_{id} dict."""

    def __init__(
        self, coordinator, entry, device_id, field, name, device_info,
        device_class=None, unit=None, state_class=None, icon=None,
        value_map=None,
    ):
        super().__init__(coordinator)
        self._device_id = device_id
        self._field = field
        self._value_map = value_map
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_{field}"
        self._attr_name = name
        self._attr_device_info = device_info
        self._attr_has_entity_name = True

        if device_class:
            self._attr_device_class = device_class
        if unit:
            self._attr_native_unit_of_measurement = unit
        if state_class:
            self._attr_state_class = state_class
        if icon:
            self._attr_icon = icon

        self._update_native_value()

    def _update_native_value(self) -> None:
        iot_data = self.coordinator.data.get(f"iot_{self._device_id}", {})
        raw = iot_data.get(self._field)
        if raw is None:
            self._attr_native_value = None
        elif self._value_map:
            try:
                self._attr_native_value = self._value_map.get(int(raw), raw)
            except (ValueError, TypeError):
                self._attr_native_value = raw
        else:
            try:
                self._attr_native_value = float(raw)
            except (ValueError, TypeError):
                self._attr_native_value = raw

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_native_value()
        self.async_write_ha_state()


class EcowittValveRunTimeSensor(CoordinatorEntity[EcowittDataCoordinator], SensorEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """Local run time counter.

    - Resets to 0 when valve is turned on (via switch or button).
    - Ticks up every second while water_running is true.
    - On each poll: if the polled run_time changed from last poll,
      adopt it as the new value. Otherwise keep ticking locally.
    """

    _attr_icon = "mdi:timer-outline"
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device_id, device_info):
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_run_time_live"
        self._attr_name = "Run Time Live"
        self._attr_device_info = device_info
        self._counter: int = 0
        self._last_polled: int | None = None
        self._cancel_timer = None
        self._attr_native_value = 0

    @callback
    def _handle_coordinator_update(self) -> None:
        # Reset requested by switch/button
        if self._device_id in self.coordinator.reset_run_time:
            self.coordinator.reset_run_time.discard(self._device_id)
            self._counter = 0
            self._attr_native_value = 0
            self._last_polled = None

        # Check polled value — adopt only if it changed since last poll
        iot_data = self.coordinator.data.get(f"iot_{self._device_id}", {})
        polled = iot_data.get("run_time")
        if polled is not None:
            try:
                polled_int = int(polled)
                if self._last_polled is None or polled_int != self._last_polled:
                    self._counter = polled_int
                    self._attr_native_value = polled_int
                self._last_polled = polled_int
            except (ValueError, TypeError):
                pass

        # Start/stop the 1-second timer based on water_running
        running = self._is_water_running()
        if running and self._cancel_timer is None:
            self._start_timer()
        elif not running and self._cancel_timer is not None:
            self._stop_timer()

        self.async_write_ha_state()

    def _is_water_running(self) -> bool:
        iot_data = self.coordinator.data.get(f"iot_{self._device_id}", {})
        try:
            return bool(int(iot_data.get("water_running", 0)))
        except (ValueError, TypeError):
            return False

    def _start_timer(self) -> None:
        from datetime import timedelta
        self._cancel_timer = async_track_time_interval(
            self.hass, self._tick, timedelta(seconds=1)
        )

    def _stop_timer(self) -> None:
        if self._cancel_timer:
            self._cancel_timer()
            self._cancel_timer = None

    @callback
    def _tick(self, _now) -> None:
        self._counter += 1
        self._attr_native_value = self._counter
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        self._stop_timer()


class EcowittSessionWaterUsageSensor(CoordinatorEntity[EcowittDataCoordinator], SensorEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """Computed sensor: water_total - happen_water."""

    _attr_icon = "mdi:water-check"
    _attr_native_unit_of_measurement = "m³"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device_id, device_info):
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_session_water_usage"
        self._attr_name = "Session Water Usage"
        self._attr_device_info = device_info

        self._update_native_value()

    def _update_native_value(self) -> None:
        iot_data = self.coordinator.data.get(f"iot_{self._device_id}", {})
        total = iot_data.get("water_total")
        start = iot_data.get("happen_water")
        if total is None or start is None:
            self._attr_native_value = None
            return
        try:
            self._attr_native_value = round(float(total) - float(start), 3)
        except (ValueError, TypeError):
            self._attr_native_value = None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_native_value()
        self.async_write_ha_state()