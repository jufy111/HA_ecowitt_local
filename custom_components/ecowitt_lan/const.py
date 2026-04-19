"""Constants for ecowitt_lan integration."""
from __future__ import annotations

DOMAIN = "ecowitt_lan"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 10
DEFAULT_SENSORS_INFO_INTERVAL = 60
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 600

CONF_SCAN_INTERVAL = "scan_interval"
CONF_SENSORS_INFO_INTERVAL = "sensors_info_interval"

# ── Endpoints ────────────────────────────────────────
ENDPOINT_LIVEDATA = "/get_livedata_info"
ENDPOINT_SENSORS_INFO = "/get_sensors_info"
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
DEVICE_TYPE_TEMP = "temp"
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
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x0C": {
        "name": "Wind Gust",
        "device_class": "wind_speed",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x19": {
        "name": "Max Daily Gust",
        "device_class": "wind_speed",
        "state_class": "measurement",
        "strip_unit": True,
    },
    "0x15": {
        "name": "Solar Radiation",
        "device_class": "irradiance",
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
    "0x0D": {"name": "Event", "strip_unit": True, "state_class": "total_increasing"},
    "0x0E": {"name": "Rate", "strip_unit": True, "state_class": "measurement"},
    "0x7C": {"name": "Hourly", "strip_unit": True, "state_class": "total_increasing"},
    "0x10": {"name": "Daily", "strip_unit": True, "state_class": "total_increasing"},
    "0x11": {"name": "Weekly", "strip_unit": True, "state_class": "total_increasing"},
    "0x12": {"name": "Monthly", "strip_unit": True, "state_class": "total_increasing"},
    "0x13": {"name": "Yearly", "strip_unit": True, "state_class": "total_increasing"},
}

UNIT_MAP = {
    "C": "°C",
    "F": "°F",
    "hPa": "hPa",
    "inHg": "inHg",
    "mmHg": "mmHg",
}

# Normalize unit strings extracted from value text (e.g. "1.57 mph" -> "mph")
UNIT_NORMALIZE: dict[str, str] = {
    "W/m2": "W/m²",
    "in/Hr": "in/h",
    "mm/Hr": "mm/h",
    "Klux": "klx",
    "Kfc": "kfc",
    "BFT": "Bft",
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

# Map sensor_info "type" -> device category used in coordinator.data keys.
# Sensors with id "FFFFFFFF" are not present and should be skipped.
SENSOR_TYPE_DEVICE_MAP: dict[str, str] = {
    # WS90 (outdoor + piezo rain)
    "48": "outdoor",
    # WH69 / WH80 (outdoor)
    "0": "outdoor",
    "2": "outdoor",
    # WH68 (solar & wind, outdoor)
    "1": "outdoor",
    # WH85 (wind & rain, outdoor)
    "49": "outdoor",
    # WH40 (rain gauge)
    "3": "rain",
    # WN20 (rain mini)
    "70": "rain",
    # WH25 (indoor temp/humi/pressure)
    "4": "gateway",
    # WH26 (temp & humidity)
    "5": "gateway",
    # WH31/WN31 Temp & Humidity CH1-CH8
    "6": "ch1", "7": "ch2", "8": "ch3", "9": "ch4",
    "10": "ch5", "11": "ch6", "12": "ch7", "13": "ch8",
    # WH51 Soil Moisture CH1-CH8
    "14": "soil1", "15": "soil2", "16": "soil3", "17": "soil4",
    "18": "soil5", "19": "soil6", "20": "soil7", "21": "soil8",
    # WH51 Soil Moisture CH9-CH16 (extended)
    "58": "soil9", "59": "soil10", "60": "soil11", "61": "soil12",
    "62": "soil13", "63": "soil14", "64": "soil15", "65": "soil16",
    # WH34 Temperature CH1-CH8
    "31": "temp1", "32": "temp2", "33": "temp3", "34": "temp4",
    "35": "temp5", "36": "temp6", "37": "temp7", "38": "temp8",
}