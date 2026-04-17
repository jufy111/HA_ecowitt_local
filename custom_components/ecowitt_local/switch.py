"""Switch platform for Ecowitt IoT water valves."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api_client import EcowittApiClient
from .const import DOMAIN, IOT_MODEL_MAP
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
                entities.append(
                    EcowittWaterValveSwitch(coordinator, client, entry, dev_id, model, iot_data)
                )

    async_add_entities(entities)


class EcowittWaterValveSwitch(CoordinatorEntity, SwitchEntity):
    """
    Switch for WFC01 water valve.
    ON = always_on (indefinite). For timed/volume runs, use services or number entities.
    OFF = quick_stop.
    """

    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_icon = "mdi:water-pump"
    _attr_has_entity_name = True

    def __init__(self, coordinator, client, entry, device_id, model, iot_data):
        super().__init__(coordinator)
        self._client = client
        self._device_id = device_id
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_valve"
        self._attr_name = "Valve"
        self._attr_device_info = iot_device_info(entry, device_id, model, iot_data)

    @property
    def _iot_data(self) -> dict[str, Any]:
        return self.coordinator.data.get(f"iot_{self._device_id}", {})

    @property
    def is_on(self) -> bool | None:
        data = self._iot_data
        if not data:
            return None
        status = data.get("water_status", 0)
        try:
            return bool(int(status))
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._iot_data
        if not data:
            return {"device_id": self._device_id}
        attrs = {
            "device_id": self._device_id,
            "model": self._model,
            "water_status": data.get("water_status"),
            "water_action": data.get("water_action"),
            "always_on": data.get("always_on"),
            "val_type": data.get("val_type"),
            "val_type_label": {1: "minutes", 3: "litres"}.get(data.get("val_type"), "unknown"),
            "val": data.get("val"),
            "run_time_seconds": data.get("run_time"),
            "warning": data.get("warning"),
            "plan_status": data.get("plan_status"),
            "water_total_m3": data.get("water_total"),
            "happen_water_m3": data.get("happen_water"),
            "flow_velocity_lpm": data.get("flow_velocity"),
            "water_temp_c": data.get("water_temp"),
        }
        return {k: v for k, v in attrs.items() if v is not None}

    async def async_turn_on(self, **kwargs) -> None:
        """Open valve (always on)."""
        _LOGGER.info("Opening valve %s (always on)", self._device_id)
        self.coordinator.reset_run_time.add(self._device_id)
        await self._client.async_valve_open(self._device_id, self._model)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Close valve (quick_stop)."""
        _LOGGER.info("Closing valve %s", self._device_id)
        await self._client.async_valve_close(self._device_id, self._model)
        await self.coordinator.async_request_refresh()