"""Button platform for Ecowitt IoT valve run triggers.

Reads parameters from coordinator.valve_params (set by number entities)
and sends the corresponding command to the gateway.
"""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api_client import EcowittApiClient
from .const import DOMAIN
from .coordinator import EcowittDataCoordinator
from .device import iot_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcowittDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    client: EcowittApiClient = hass.data[DOMAIN][entry.entry_id]["client"]
    entities = []

    for dev in coordinator.iot_devices:
        dev_id = dev["id"]
        model = dev.get("model", 1)
        if model in (1,):  # WFC01
            iot_data = coordinator.data.get(f"iot_{dev_id}", {})
            if iot_data:
                dev_info = iot_device_info(entry, dev_id, model, iot_data)
                entities.extend([
                    EcowittValveTimedRunButton(
                        coordinator, client, entry, dev_id, model, dev_info
                    ),
                    EcowittValveVolumeRunButton(
                        coordinator, client, entry, dev_id, model, dev_info
                    ),
                ])

    async_add_entities(entities)


class EcowittValveTimedRunButton(CoordinatorEntity, ButtonEntity):
    """Press to open the valve for the configured minutes with cycle settings."""

    _attr_icon = "mdi:timer-play"
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, entry, device_id, model, device_info):
        super().__init__(coordinator)
        self._client = client
        self._device_id = device_id
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_start_timed"
        self._attr_name = "Start Timed Run"
        self._attr_device_info = device_info

    async def async_press(self) -> None:
        params = self.coordinator.valve_params
        minutes = int(params.get(f"{self._device_id}_minutes", 10))
        on_time = int(params.get(f"{self._device_id}_cycle_on", 0))
        off_time = int(params.get(f"{self._device_id}_cycle_off", 0))

        _LOGGER.info(
            "Timed run: valve %s for %d min (cycle: %ds on / %ds off)",
            self._device_id, minutes, on_time, off_time,
        )
        self.coordinator.reset_run_time.add(self._device_id)
        await self._client.async_valve_open_for_minutes(
            self._device_id, minutes, self._model, on_time, off_time
        )
        await self.coordinator.async_request_refresh()


class EcowittValveVolumeRunButton(CoordinatorEntity, ButtonEntity):
    """Press to open the valve for the configured litres with cycle settings."""

    _attr_icon = "mdi:water-plus"
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, entry, device_id, model, device_info):
        super().__init__(coordinator)
        self._client = client
        self._device_id = device_id
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_start_volume"
        self._attr_name = "Start Volume Run"
        self._attr_device_info = device_info

    async def async_press(self) -> None:
        params = self.coordinator.valve_params
        litres = float(params.get(f"{self._device_id}_litres", 10))
        on_time = int(params.get(f"{self._device_id}_cycle_on", 0))
        off_time = int(params.get(f"{self._device_id}_cycle_off", 0))

        _LOGGER.info(
            "Volume run: valve %s for %.1f L (cycle: %ds on / %ds off)",
            self._device_id, litres, on_time, off_time,
        )
        self.coordinator.reset_run_time.add(self._device_id)
        await self._client.async_valve_open_for_litres(
            self._device_id, litres, self._model, on_time, off_time
        )
        await self.coordinator.async_request_refresh()
