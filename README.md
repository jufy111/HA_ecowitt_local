# Ecowitt Gateway (Local) for Home Assistant

A Home Assistant custom component that integrates Ecowitt weather gateways over your local network. All communication stays on your LAN -- no cloud dependency.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![version](https://img.shields.io/badge/version-0.3.8-blue)
![ha](https://img.shields.io/badge/HA-2024.1.0+-green)

## Features

- **100% local** -- communicates directly with your Ecowitt gateway via HTTP
- **Weather sensors** -- temperature, humidity, wind, solar radiation, UV index, dew point, barometric pressure, and more
- **Rain monitoring** -- traditional and piezo rain gauges with event, rate, hourly, daily, weekly, monthly, and yearly totals
- **Multi-channel support** -- wireless temperature/humidity sensors (WH31) and soil moisture sensors (WH51)
- **IoT device control** -- WFC01 smart water valve with timed runs, volume-based runs, and on/off cycling for irrigation
- **Auto-discovery** -- IoT devices are discovered automatically at startup
- **Configurable polling** -- adjust the scan interval from 1 to 600 seconds without restarting

## Supported Devices

| Device | Type | Sensors |
|--------|------|---------|
| **WS90** | Outdoor array | Temperature, humidity, wind speed/gust/direction, solar radiation, UV index, dew point, feels-like, capacitor voltage |
| **WH25** | Indoor sensor | Temperature, humidity, absolute & relative pressure |
| **WH31 / WN31** | Wireless channel | Temperature, humidity (up to 8 channels) |
| **WH51** | Soil moisture | Moisture level, battery voltage (up to 8 channels) |
| **Rain gauge** | Traditional | Event, rate, hourly, daily, weekly, monthly, yearly |
| **Piezo rain** | WS90 variant | Same as rain gauge, from piezoelectric sensor |
| **WFC01** | Water valve | Water temp, flow rate, total/session usage, battery, valve control |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** > **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Search for "Ecowitt Gateway (Local)" and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/ecowitt_local` folder into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for **Ecowitt Gateway (Local)**
3. Enter your gateway's local IP address and port (default: 80)
4. Set the polling interval in seconds (default: 10)

The polling interval can be adjusted later from the integration's options without restarting.

## Platforms & Entities

| Platform | Description |
|----------|-------------|
| **Sensor** | Weather data, diagnostics, water valve metrics |
| **Binary Sensor** | Device warnings, water running state, RF connectivity |
| **Switch** | Water valve on/off control |
| **Number** | Valve run parameters (minutes, litres, cycle on/off times) |
| **Button** | Trigger timed or volume-based valve runs |
| **Select** | Current valve operating mode (read-only) |

All entities use `has_entity_name`, so Home Assistant automatically combines the device name with the entity name.

## Services

Four services are available for automating the WFC01 water valve:

### `ecowitt_gw.valve_open`

Opens the valve indefinitely.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `device_id` | Yes | Numeric ID of the valve |

### `ecowitt_gw.valve_close`

Closes the valve immediately.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `device_id` | Yes | Numeric ID of the valve |

### `ecowitt_gw.valve_open_timed`

Opens the valve for a set duration with optional on/off cycling.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `device_id` | Yes | Numeric ID of the valve |
| `minutes` | Yes | Duration in minutes (1-1440) |
| `on_time` | No | Cycle on-time in seconds (0 = continuous) |
| `off_time` | No | Cycle off-time in seconds (0 = continuous) |

### `ecowitt_gw.valve_open_volume`

Opens the valve until a target volume has been dispensed.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `device_id` | Yes | Numeric ID of the valve |
| `litres` | Yes | Target volume in litres (0.1-9999) |
| `on_time` | No | Cycle on-time in seconds (0 = continuous) |
| `off_time` | No | Cycle off-time in seconds (0 = continuous) |

## Example Automations

### Water the garden for 30 minutes every morning

```yaml
automation:
  - alias: "Morning garden watering"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: ecowitt_gw.valve_open_timed
        data:
          device_id: 12345
          minutes: 30
```

### Stop watering if it starts raining

```yaml
automation:
  - alias: "Stop valve on rain"
    trigger:
      - platform: numeric_state
        entity_id: sensor.rain_gauge_rain_rate
        above: 0
    action:
      - service: ecowitt_gw.valve_close
        data:
          device_id: 12345
```

### Dispense exactly 50 litres with 10-min on / 5-min off cycling

```yaml
automation:
  - alias: "Cycled volume watering"
    action:
      - service: ecowitt_gw.valve_open_volume
        data:
          device_id: 12345
          litres: 50
          on_time: 600
          off_time: 300
```

## How It Works

The integration polls your Ecowitt gateway over HTTP using three local API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `/get_livedata_info` | Fetch all sensor readings |
| `/get_iot_device_list` | Discover paired IoT devices |
| `/parse_quick_cmd_iot` | Read state and send commands to IoT devices |

Data is parsed into a flat key-value dictionary by the coordinator, which drives all entity state updates using Home Assistant's `DataUpdateCoordinator` pattern.

## Requirements

- Home Assistant 2024.1.0 or newer
- Ecowitt gateway accessible on the local network
- Gateway firmware that supports the local HTTP API

## License

This project is provided as-is for personal use. See [LICENSE](LICENSE) for details.
