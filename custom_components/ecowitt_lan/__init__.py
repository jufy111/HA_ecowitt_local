"""Ecowitt Gateway local integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api_client import EcowittApiClient
from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SENSORS_INFO_INTERVAL,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS_INFO_INTERVAL,
    SERVICE_VALVE_OPEN,
    SERVICE_VALVE_CLOSE,
    SERVICE_VALVE_OPEN_TIMED,
    SERVICE_VALVE_OPEN_VOLUME,
)
from .coordinator import EcowittDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Explicitly typed as Platform enum — HA uses these to find the right files
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ecowitt Gateway from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    sensors_info_interval = entry.options.get(CONF_SENSORS_INFO_INTERVAL, DEFAULT_SENSORS_INFO_INTERVAL)

    session = async_get_clientsession(hass)
    client = EcowittApiClient(host, port, session=session)

    coordinator = EcowittDataCoordinator(hass, client, scan_interval, sensors_info_interval)
    await coordinator.async_discover_iot_devices()
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
    }

    # Forward to platform files (sensor.py, switch.py, etc.)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates (polling interval)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    # Register services
    _register_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    # Remove services if no entries remain
    if not hass.data.get(DOMAIN):
        for svc in [
            SERVICE_VALVE_OPEN,
            SERVICE_VALVE_CLOSE,
            SERVICE_VALVE_OPEN_TIMED,
            SERVICE_VALVE_OPEN_VOLUME,
        ]:
            if hass.services.has_service(DOMAIN, svc):
                hass.services.async_remove(DOMAIN, svc)

    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update — adjust polling interval live."""
    coordinator: EcowittDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    new_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator.update_scan_interval(new_interval)
    new_si_interval = entry.options.get(CONF_SENSORS_INFO_INTERVAL, DEFAULT_SENSORS_INFO_INTERVAL)
    coordinator.update_sensors_info_interval(new_si_interval)
    await coordinator.async_request_refresh()


def _get_client_and_coordinator(
    hass: HomeAssistant,
) -> tuple[EcowittApiClient, EcowittDataCoordinator] | None:
    """Get first available client/coordinator."""
    for entry_data in hass.data.get(DOMAIN, {}).values():
        return entry_data["client"], entry_data["coordinator"]
    return None


def _register_services(hass: HomeAssistant) -> None:
    """Register valve control services (once globally)."""
    if hass.services.has_service(DOMAIN, SERVICE_VALVE_OPEN):
        return

    async def handle_valve_open(call: ServiceCall) -> None:
        device_id = call.data["device_id"]
        model = call.data.get("model", 1)
        result = _get_client_and_coordinator(hass)
        if result:
            client, coordinator = result
            await client.async_valve_open(device_id, model)
            await coordinator.async_request_refresh()

    async def handle_valve_close(call: ServiceCall) -> None:
        device_id = call.data["device_id"]
        model = call.data.get("model", 1)
        result = _get_client_and_coordinator(hass)
        if result:
            client, coordinator = result
            await client.async_valve_close(device_id, model)
            await coordinator.async_request_refresh()

    async def handle_valve_timed(call: ServiceCall) -> None:
        device_id = call.data["device_id"]
        minutes = call.data["minutes"]
        model = call.data.get("model", 1)
        on_time = call.data.get("on_time", 0)
        off_time = call.data.get("off_time", 0)
        result = _get_client_and_coordinator(hass)
        if result:
            client, coordinator = result
            await client.async_valve_open_for_minutes(
                device_id, minutes, model, on_time, off_time
            )
            await coordinator.async_request_refresh()

    async def handle_valve_volume(call: ServiceCall) -> None:
        device_id = call.data["device_id"]
        litres = call.data["litres"]
        model = call.data.get("model", 1)
        on_time = call.data.get("on_time", 0)
        off_time = call.data.get("off_time", 0)
        result = _get_client_and_coordinator(hass)
        if result:
            client, coordinator = result
            await client.async_valve_open_for_litres(
                device_id, litres, model, on_time, off_time
            )
            await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_VALVE_OPEN,
        handle_valve_open,
        schema=vol.Schema(
            {
                vol.Required("device_id"): cv.positive_int,
                vol.Optional("model", default=1): cv.positive_int,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_VALVE_CLOSE,
        handle_valve_close,
        schema=vol.Schema(
            {
                vol.Required("device_id"): cv.positive_int,
                vol.Optional("model", default=1): cv.positive_int,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_VALVE_OPEN_TIMED,
        handle_valve_timed,
        schema=vol.Schema(
            {
                vol.Required("device_id"): cv.positive_int,
                vol.Required("minutes"): vol.All(
                    cv.positive_int, vol.Range(min=1, max=1440)
                ),
                vol.Optional("model", default=1): cv.positive_int,
                vol.Optional("on_time", default=0): vol.All(
                    int, vol.Range(min=0, max=86400)
                ),
                vol.Optional("off_time", default=0): vol.All(
                    int, vol.Range(min=0, max=86400)
                ),
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_VALVE_OPEN_VOLUME,
        handle_valve_volume,
        schema=vol.Schema(
            {
                vol.Required("device_id"): cv.positive_int,
                vol.Required("litres"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.1, max=9999)
                ),
                vol.Optional("model", default=1): cv.positive_int,
                vol.Optional("on_time", default=0): vol.All(
                    int, vol.Range(min=0, max=86400)
                ),
                vol.Optional("off_time", default=0): vol.All(
                    int, vol.Range(min=0, max=86400)
                ),
            }
        ),
    )