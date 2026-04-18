"""Number platform for Ecowitt IoT valve run parameters.

These are input-only parameters. They do not send commands to the device.
The button platform reads these values when triggering timed/volume runs.
Values are stored in coordinator.valve_params keyed as "{device_id}_{param}".
"""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EcowittDataCoordinator
from .device import iot_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EcowittDataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []

    for dev in coordinator.iot_devices:
        dev_id = dev["id"]
        model = dev.get("model", 1)
        if model in (1,):  # WFC01
            iot_data = coordinator.data.get(f"iot_{dev_id}", {})
            if iot_data:
                dev_info = iot_device_info(entry, dev_id, model, iot_data)
                entities.extend([
                    EcowittValveMinutes(coordinator, entry, dev_id, dev_info),
                    EcowittValveLitres(coordinator, entry, dev_id, dev_info),
                    EcowittValveCycleOnTime(coordinator, entry, dev_id, dev_info),
                    EcowittValveCycleOffTime(coordinator, entry, dev_id, dev_info),
                ])

    async_add_entities(entities)


class _ValveParamNumber(CoordinatorEntity[EcowittDataCoordinator], NumberEntity):  # pyright: ignore[reportIncompatibleVariableOverride]
    """Base for valve parameter number entities (input only, no command).

    Stores its value in coordinator.valve_params so button entities can read it.
    """

    _attr_mode = NumberMode.BOX
    _attr_has_entity_name = True
    _param_key: str = ""  # Override in subclasses

    def __init__(self, coordinator, entry, device_id, device_info, default: float = 0):
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_device_info = device_info
        key = f"{device_id}_{self._param_key}"
        if key not in coordinator.valve_params:
            coordinator.valve_params[key] = default

        self._update_native_value()

    def _update_native_value(self) -> None:
        self._attr_native_value = self.coordinator.valve_params.get(
            f"{self._device_id}_{self._param_key}", 0
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_native_value()
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.valve_params[f"{self._device_id}_{self._param_key}"] = value
        self._attr_native_value = value
        self.async_write_ha_state()


class EcowittValveMinutes(_ValveParamNumber):
    """Minutes parameter for timed valve run."""

    _attr_icon = "mdi:timer"
    _attr_native_min_value = 1
    _attr_native_max_value = 1440
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _param_key = "minutes"

    def __init__(self, coordinator, entry, device_id, device_info):
        super().__init__(coordinator, entry, device_id, device_info, default=10)
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_run_minutes"
        self._attr_name = "Run Minutes"


class EcowittValveLitres(_ValveParamNumber):
    """Litres parameter for volume valve run."""

    _attr_icon = "mdi:water"
    _attr_native_min_value = 0.1
    _attr_native_max_value = 9999
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "L"
    _param_key = "litres"

    def __init__(self, coordinator, entry, device_id, device_info):
        super().__init__(coordinator, entry, device_id, device_info, default=10)
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_run_litres"
        self._attr_name = "Run Litres"


class EcowittValveCycleOnTime(_ValveParamNumber):
    """Cycle ON time in seconds (0 = continuous)."""

    _attr_icon = "mdi:timer-play"
    _attr_native_min_value = 0
    _attr_native_max_value = 86400
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _param_key = "cycle_on"

    def __init__(self, coordinator, entry, device_id, device_info):
        super().__init__(coordinator, entry, device_id, device_info, default=0)
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_cycle_on"
        self._attr_name = "Cycle On Time"


class EcowittValveCycleOffTime(_ValveParamNumber):
    """Cycle OFF time in seconds (0 = continuous)."""

    _attr_icon = "mdi:timer-pause"
    _attr_native_min_value = 0
    _attr_native_max_value = 86400
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "s"
    _param_key = "cycle_off"

    def __init__(self, coordinator, entry, device_id, device_info):
        super().__init__(coordinator, entry, device_id, device_info, default=0)
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_cycle_off"
        self._attr_name = "Cycle Off Time"
