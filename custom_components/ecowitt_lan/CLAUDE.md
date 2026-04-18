# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom component (`ecowitt_lan`) that integrates Ecowitt weather gateways over the local LAN using HTTP polling. Supports weather sensors (WS90, WH25, WH31, WH51), rain gauges, and IoT devices (WFC01 water valve controller). Installed via HACS; requires HA 2024.1.0+.

## Deployment

No build system, tests, or CI. Deploy by copying to the HA instance:
```bash
scp -r ecowitt_lan/ root@<HA_HOST>:/root/config/custom_components/ecowitt_lan
```

## Architecture

### Data Flow

```
Ecowitt Gateway (LAN)
  -> EcowittApiClient (aiohttp, 3 endpoints)
    -> EcowittDataCoordinator (polling + parsing into flat key-value dict)
      -> Platform entities (CoordinatorEntity subclasses)
```

### Key Design Decisions

- **Flat coordinator data dict**: The coordinator transforms nested API responses (`common_list`, `rain`, `piezoRain`, `wh25`, `ch_aisle`, `ch_soil`, `debug`) into flat keys like `common_0x02`, `rain_0x0D`, `ch1_temp`, `soil2_humidity`, `iot_12345`. This is the single source of truth for all entity state.

- **Presence flags**: `has_rain`, `has_piezo`, `has_indoor`, `has_outdoor`, `channels_present`, `soil_channels_present` in coordinator data control which entities are created at setup time.

- **Three entity class patterns** in sensor.py:
  - `EcowittMappedSensor` — metadata driven by `COMMON_LIST_MAP` / `RAIN_MAP` dicts in const.py (sensor ID hex codes to name/unit/device_class)
  - `EcowittSimpleSensor` — reads a single flat key from coordinator.data
  - `EcowittIoTSensor` — reads nested `iot_{device_id}` dicts, supports `value_map` for enum-to-value translation

- **Device grouping**: `device.py` has factory functions that create `DeviceInfo` objects. Every physical sensor type gets its own device, linked to the gateway via `via_device`. IoT devices use their numeric ID as identifier (not entry-scoped).

- **IoT device discovery**: Done once at startup via `async_discover_iot_devices()`, then the device list is refreshed on every coordinator update. Per-device state is fetched individually via `read_device` POST command.

- **Valve control**: Exposed as both HA services (registered in `__init__.py`) and platform entities (switch for on/off, number for timed/volume runs, select for mode display). The API uses decilitres internally for volume (`litres * 10`).

### API Endpoints (all local HTTP)

| Endpoint | Method | Purpose |
|---|---|---|
| `/get_livedata_info` | GET | All sensor readings |
| `/get_iot_device_list` | GET | Discover paired IoT devices |
| `/parse_quick_cmd_iot` | POST | Read device state / send commands |

### Domain and Unique IDs

- Integration domain: `ecowitt_lan` (used in `DOMAIN`, `manifest.json`, `hass.data` keys)
- Entity unique IDs: `{entry_id}_{data_key}` for sensors, `{entry_id}_iot_{device_id}_{field}` for IoT entities

## Conventions

- All entities inherit from `CoordinatorEntity` — state updates are driven by the coordinator, not individual polling.
- `has_entity_name = True` on all entities — HA combines device name + entity name automatically.
- Unit stripping happens in `coordinator.parse_value()` (removes `%`, `mm`, `m/s`, etc. from raw API strings).
- Sensor metadata maps in `const.py` use hex string IDs (e.g., `"0x02"`) matching the gateway API's `id` field, plus some plain integer strings (e.g., `"3"`, `"5"`) for computed values.
- Options flow only exposes `scan_interval` (10-600s); changes apply live via `coordinator.update_scan_interval()`.
