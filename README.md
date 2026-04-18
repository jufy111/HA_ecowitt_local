# Ecowitt Gateway (Local) for Home Assistant

A Home Assistant custom component that integrates Ecowitt weather gateways over your local network. All communication stays on your LAN -- no cloud dependency.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![version](https://img.shields.io/badge/version-1.0.4-blue)
![ha](https://img.shields.io/badge/HA-2024.1.0+-green)

## Features

- **100% local** -- communicates directly with your Ecowitt gateway via HTTP
- **Weather sensors** -- temperature, humidity, wind, solar radiation, UV index, dew point, barometric pressure, and more
- **Rain monitoring** -- traditional and piezo rain gauges with event, rate, hourly, daily, weekly, monthly, and yearly totals
- **Multi-channel support** -- wireless temperature/humidity sensors (WH31) and soil moisture sensors (WH51)
- **IoT device control** -- WFC01 smart water valve with timed runs, volume-based runs, and on/off cycling for irrigation
- **Auto-discovery** -- IoT devices are discovered automatically at startup
- **Configurable polling** -- adjust the scan interval from 1 to 600 seconds without restarting
- Unlike the Ecowitt integrations sensors are seperated into physical devices. There is also more sensors that are now included in the official integration

<img width="836" height="1320" alt="image" src="https://github.com/user-attachments/assets/1a598394-854b-4832-8905-9aa357c7e538" />


## Supported Devices
I've only added the devices for hardware I own. This is a GW2000 gateway and the below sensors
| Device | Type | Sensors |
|--------|------|---------|
| **WS90** | Outdoor array | Temperature, humidity, wind speed/gust/direction, solar radiation, UV index, dew point, feels-like, capacitor voltage, Event, rate, hourly, daily, weekly, monthly, yearly |
| **WH25** | Indoor sensor | Temperature, humidity, absolute & relative pressure |
| **WH31 / WN31** | Wireless channel | Temperature, humidity (up to 8 channels) |
| **WH51** | Soil moisture | Moisture level, battery voltage (up to 8 channels) |
| **WH40** | Rain gauge- Traditional | Event, rate, hourly, daily, weekly, monthly, yearly |
| **WFC01** | Water valve | Water temp, flow rate, total/session usage, battery, valve control |

<img width="606" height="1224" alt="image" src="https://github.com/user-attachments/assets/694a012c-d874-4f1a-b945-d57fad804aca" />

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations** > **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Search for "Ecowitt Gateway (Local)" and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/ecowitt_lan` folder into your Home Assistant `config/custom_components/` directory and restart.

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

### `ecowitt_lan.valve_open`

Opens the valve indefinitely.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `device_id` | Yes | Numeric ID of the valve |

### `ecowitt_lan.valve_close`

Closes the valve immediately.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `device_id` | Yes | Numeric ID of the valve |

### `ecowitt_lan.valve_open_timed`

Opens the valve for a set duration with optional on/off cycling. The valve will shut off itself when the time is reached, there is no need for home assistant to send another command to the valve when the time is reached.

| Parameter | Required | Description |
|-----------|----------|-------------|
| `device_id` | Yes | Numeric ID of the valve |
| `minutes` | Yes | Duration in minutes (1-1440) |
| `on_time` | No | Cycle on-time in seconds (0 = continuous) |
| `off_time` | No | Cycle off-time in seconds (0 = continuous) |

### `ecowitt_lan.valve_open_volume`

Opens the valve until a target volume has been dispensed. The valve will shut off itself when the target volume is reached, there is no need for home assistant to send another command to the valve when the target volume is reached.

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
      - service: ecowitt_lan.valve_open_timed
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
      - service: ecowitt_lan.valve_close
        data:
          device_id: 12345
```

### Dispense exactly 50 litres with 10-min on / 5-min off cycling

```yaml
automation:
  - alias: "Cycled volume watering"
    action:
      - service: ecowitt_lan.valve_open_volume
        data:
          device_id: 12345
          litres: 50
          on_time: 600
          off_time: 300
```

## Blueprints

### Valve Daily Schedule

A ready-made automation blueprint that opens the WFC01 valve at a scheduled time each day for a configurable duration.

**Prerequisites** -- create three helpers in **Settings > Devices & Services > Helpers**:

| Helper | Type | Purpose |
|--------|------|---------|
| `input_boolean.valve_schedule_enabled` | Toggle | Enable / disable the schedule |
| `input_datetime.valve_schedule_time` | Time only | Daily start time |
| `input_number.valve_schedule_duration` | Number (1-1440) | Run duration in minutes |

**Install the blueprint:**

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fjufy111%2FHA_ecowitt_lan%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fvalve_daily_schedule.yaml)

Or manually: copy `blueprints/automation/valve_daily_schedule.yaml` into your Home Assistant `config/blueprints/automation/ecowitt_lan/` directory and restart.

Once imported, create an automation from the blueprint and select your valve's entities from the dropdowns.

## Example Dashboard Card

Below is a Lovelace card for the WFC01 water valve. It requires the [Mushroom](https://github.com/piitaya/lovelace-mushroom) custom cards (available via HACS) and one helper toggle for the collapsible cycle-settings section:
<img width="553" height="923" alt="image" src="https://github.com/user-attachments/assets/3289497b-6fd4-4e11-a0ae-04b113635daf" />

| Helper | Type | Purpose |
|--------|------|---------|
| `input_boolean.show_valve_cycle` | Toggle | Show/hide cycle settings in the card |

Replace `DEVICE_ID` with your valve's ID (e.g. `00004185`).

<details>
<summary>Click to expand valve card YAML</summary>

```yaml
type: vertical-stack
title: Water Valve
cards:
  - type: custom:mushroom-entity-card
    entity: switch.wfc01_DEVICE_ID_valve
    icon: mdi:toggle-switch
    tap_action:
      action: toggle
    fill_container: true
    layout: vertical
    icon_color: green
    name: Manual On/Off
    primary_info: name
    secondary_info: last-changed
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-template-card
        primary: |-
          {% set s = states('sensor.wfc01_DEVICE_ID_run_time_live') | int %}
          {{ '%02d:%02d' % (s // 60, s % 60) }}
        secondary: Run Time
        icon: mdi:timer-outline
        tap_action:
          action: none
        color: blue
        vertical: true
      - type: custom:mushroom-template-card
        primary: >-
          {% set vtype = state_attr('switch.wfc01_DEVICE_ID_valve', 'val_type') %}
          {% set val = state_attr('switch.wfc01_DEVICE_ID_valve', 'val') %}
          {% set always = state_attr('switch.wfc01_DEVICE_ID_valve', 'always_on') %}
          {% if always == 1 %}-- {% elif vtype == 1 and val is not none %}{{ val }} min
          {% elif vtype == 3 and val is not none %}{{ (val | float / 10) | round(1) }} L
          {% else %}--{% endif %}
        secondary: Target
        icon: mdi:target
        icon_color: orange
        layout: vertical
        tap_action:
          action: none
      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.wfc01_DEVICE_ID_flow_rate') }} L/min"
        secondary: Flow Rate
        icon: mdi:speedometer
        icon_color: cyan
        layout: vertical
        tap_action:
          action: none
      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.wfc01_DEVICE_ID_session_water_usage') }} L"
        secondary: Water Used
        tap_action:
          action: none
        color: cyan
        vertical: true
        icon: mdi:water
  - type: horizontal-stack
    cards:
      - type: entities
        entities:
          - entity: number.wfc01_DEVICE_ID_run_minutes
            name: Time (min)
      - type: entities
        entities:
          - entity: number.wfc01_DEVICE_ID_run_litres
            name: Volume (L)
  - type: horizontal-stack
    cards:
      - type: button
        entity: button.wfc01_DEVICE_ID_start_timed_run
        name: Start Timed
        icon: mdi:timer-play
        show_state: false
        tap_action:
          action: toggle
      - type: button
        entity: button.wfc01_DEVICE_ID_start_volume_run
        name: Start Volume
        icon: mdi:water-plus
        show_state: false
        tap_action:
          action: toggle
  - type: custom:mushroom-template-card
    primary: Cycle Settings
    secondary: >-
      {% set on_t = states('number.wfc01_DEVICE_ID_cycle_on_time') | int(0) %}
      {% set off_t = states('number.wfc01_DEVICE_ID_cycle_off_time') | int(0) %}
      {% if on_t > 0 and off_t > 0 %}
        {{ on_t }}s on / {{ off_t }}s off
      {% else %}
        Continuous (no cycling)
      {% endif %}
    icon: |-
      {% if is_state('input_boolean.show_valve_cycle', 'on') %}
        mdi:chevron-up
      {% else %}
        mdi:chevron-down
      {% endif %}
    icon_color: purple
    tap_action:
      action: call-service
      service: input_boolean.toggle
      target:
        entity_id: input_boolean.show_valve_cycle
  - type: conditional
    conditions:
      - condition: state
        entity: input_boolean.show_valve_cycle
        state: "on"
    card:
      type: entities
      entities:
        - entity: number.wfc01_DEVICE_ID_cycle_on_time
          name: Cycle On Time (seconds)
        - entity: number.wfc01_DEVICE_ID_cycle_off_time
          name: Cycle Off Time (seconds)
  - type: custom:mushroom-template-card
    primary: Schedule
    secondary: |-
      {% if is_state('input_boolean.valve_schedule_enabled', 'on') %}
        Daily at {{ states('input_datetime.valve_schedule_time') }} for {{ states('input_number.valve_schedule_duration') | int }} min
      {% else %}
        Disabled
      {% endif %}
    icon: mdi:calendar-clock
    icon_color: |-
      {% if is_state('input_boolean.valve_schedule_enabled', 'on') %}
        green
      {% else %}
        grey
      {% endif %}
    tap_action:
      action: none
  - type: entities
    entities:
      - entity: input_boolean.valve_schedule_enabled
        name: Enable Schedule
      - entity: input_datetime.valve_schedule_time
        name: Start Time
      - entity: input_number.valve_schedule_duration
        name: Duration (min)
```

</details>

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

