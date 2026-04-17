"""Constants for ecowitt_gw integration."""
from __future__ import annotations

DOMAIN = "ecowitt_gw"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 1
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 600

CONF_SCAN_INTERVAL = "scan_interval"

# ── Endpoints ────────────────────────────────────────
ENDPOINT_LIVEDATA = "/get_livedata_info"
ENDPOINT_IOT_CMD = "/parse_quick_cmd_iot"
ENDPOINT_IOT_DEVICE_LIST = "/get_iot_device_list"

# ── Services ─────────────────────────────────────────
SERVICE_VALVE_OPEN = "valve_open"
SERVICE_VALVE_CLOSE = "valve_close"
SERVICE_VALVE_OPEN_TIMED = "valve_open_timed"
SERVICE_VALVE_OPEN_VOLUME = "valve_open_volume"

# ── Valve control constants ──────────────────────────
VAL_TYPE_TIME = 1      # val = minutes
VAL_TYPE_VOLUME = 3    # val = decilitres (13L = 130)

# ── Device type identifiers (for device_info) ───────
DEVICE_TYPE_GATEWAY = "gateway"
DEVICE_TYPE_INDOOR = "wh25"
DEVICE_TYPE_OUTDOOR = "outdoor"
DEVICE_TYPE_RAIN = "rain_gauge"
DEVICE_TYPE_CHANNEL = "channel"
DEVICE_TYPE_SOIL = "soil"
DEVICE_TYPE_IOT = "iot"

# ── Sensor ID mapping (common_list) ─────────────────
COMMON_LIST_MAP: dict[str, dict] = {
    "0x02": {
        "name": "Temperature",
        "device_class": "temperature",
        "unit_key": "unit",
        "state_class": "measurement",
    },
    "0x07": {
        "name": "Humidity",
        "device_class": "humidity",
        "unit": "%",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "3": {
        "name": "Feels Like",
        "device_class": "temperature",
        "unit_key": "unit",
        "state_class": "measurement",
    },
    "5": {
        "name": "Vapor Pressure",
        "device_class": "pressure",
        "unit": "kPa",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x03": {
        "name": "Dew Point",
        "device_class": "temperature",
        "unit_key": "unit",
        "state_class": "measurement",
    },
    "0x0B": {
        "name": "Wind Speed",
        "device_class": "wind_speed",
        "unit": "m/s",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x0C": {
        "name": "Wind Gust",
        "device_class": "wind_speed",
        "unit": "m/s",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x19": {
        "name": "Max Daily Gust",
        "device_class": "wind_speed",
        "unit": "m/s",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x15": {
        "name": "Solar Radiation",
        "device_class": "irradiance",
        "unit": "W/m²",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x17": {
        "name": "UV Index",
        "icon": "mdi:sun-wireless",
        "unit": "UV",
        "state_class": "measurement",
    },
    "0x0A": {
        "name": "Wind Direction",
        "icon": "mdi:compass",
        "unit": "°",
        "state_class": "measurement",
    },
    "0x6D": {
        "name": "Wind Direction (10m avg)",
        "icon": "mdi:compass",
        "unit": "°",
        "state_class": "measurement",
    },
}

RAIN_MAP: dict[str, dict] = {
    "0x0D": {"name": "Event", "unit": "mm", "strip_unit": True, "state_class": "total_increasing"},
    "0x0E": {"name": "Rate", "unit": "mm/h", "strip_unit": True, "state_class": "measurement"},
    "0x7C": {"name": "Hourly", "unit": "mm", "strip_unit": True, "state_class": "total_increasing"},
    "0x10": {"name": "Daily", "unit": "mm", "strip_unit": True, "state_class": "total_increasing"},
    "0x11": {"name": "Weekly", "unit": "mm", "strip_unit": True, "state_class": "total_increasing"},
    "0x12": {"name": "Monthly", "unit": "mm", "strip_unit": True, "state_class": "total_increasing"},
    "0x13": {"name": "Yearly", "unit": "mm", "strip_unit": True, "state_class": "total_increasing"},
}

UNIT_MAP = {
    "C": "°C",
    "F": "°F",
    "hPa": "hPa",
    "inHg": "inHg",
}

IOT_MODEL_MAP = {
    1: "WFC01",
}

BATTERY_LEVEL_MAP: dict[int, int] = {
    5: 100,
    4: 80,
    3: 60,
    2: 40,
    1: 20,
    0: 0,
}