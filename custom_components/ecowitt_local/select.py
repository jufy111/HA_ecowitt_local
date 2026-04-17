"""Select platform for Ecowitt IoT valve run mode."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IOT_MODEL_MAP
from .coordinator import EcowittDataCoordinator
from .device import iot_device_info

VALVE_MODES = ["off", "always_on", "timed", "volume"]


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
        if model in (1,):
            iot_data = coordinator.data.get(f"iot_{dev_id}", {})
            if iot_data:
                entities.append(
                    EcowittValveModeSelect(coordinator, entry, dev_id, model, iot_data)
                )

    async_add_entities(entities)


class EcowittValveModeSelect(CoordinatorEntity, SelectEntity):
    """
    Shows the current operating mode of the valve.
    Read-only indicator derived from device state.
    """

    _attr_icon = "mdi:cog"
    _attr_options = VALVE_MODES
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device_id, model, iot_data):
        super().__init__(coordinator)
        self._device_id = device_id
        self._model = model
        self._attr_unique_id = f"{entry.entry_id}_iot_{device_id}_mode"
        self._attr_name = "Run Mode"
        self._attr_device_info = iot_device_info(entry, device_id, model, iot_data)

    @property
    def current_option(self) -> str:
        data = self.coordinator.data.get(f"iot_{self._device_id}", {})
        if not data:
            return "off"

        status = data.get("water_status", 0)
        try:
            status = int(status)
        except (ValueError, TypeError):
            status = 0

        if not status:
            return "off"

        always_on = data.get("always_on", 0)
        try:
            always_on = int(always_on)
        except (ValueError, TypeError):
            always_on = 0

        if always_on:
            return "always_on"

        val_type = data.get("val_type", 1)
        try:
            val_type = int(val_type)
        except (ValueError, TypeError):
            val_type = 1

        return "volume" if val_type == 3 else "timed"

    async def async_select_option(self, option: str) -> None:
        """
        This select is primarily a status indicator.
        Actual control is via the switch + number entities or services.
        """
        pass  # Read-only indicator