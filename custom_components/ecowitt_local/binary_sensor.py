"""Binary sensor platform for Ecowitt Gateway."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, IOT_MODEL_MAP
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
        iot_data = coordinator.data.get(f"iot_{dev_id}", {})
        if not iot_data:
            continue

        dev_info = iot_device_info(entry, dev_id, model, iot_data)

        entities.extend([
            EcowittIoTBinarySensor(
                coordinator, entry, dev_id,
                "warning", "Warning",
                dev_info, BinarySensorDeviceClass.PROBLEM,
            ),
            EcowittIoTBinarySensor(
                coordinator, entry, dev_id,
                "water_running", "Water Running",
                dev_info, BinarySensorDeviceClass.RUNNING,
                icon="mdi:water",
            ),
            EcowittIoTRfState(
                coordinator, entry, dev_id, dev_info,
            ),
        ])

    async_add_entities(entities)


class EcowittIoTBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor from IoT device field."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entry, dev_id, field, name, device_info,
        device_class=None, icon=None,
    ):
        super().__init__(coordinator)
        self._device_id = dev_id
        self._field = field
        self._attr_unique_id = f"{entry.entry_id}_iot_{dev_id}_{field}"
        self._attr_name = name
        self._attr_device_info = device_info
        if device_class:
            self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data.get(f"iot_{self._device_id}", {})
        val = data.get(self._field)
        if val is None:
            return None
        try:
            return bool(int(val))
        except (ValueError, TypeError):
            return None


class EcowittIoTRfState(CoordinatorEntity, BinarySensorEntity):
    """RF connectivity from device list."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, dev_id, device_info):
        super().__init__(coordinator)
        self._device_id = dev_id
        self._attr_unique_id = f"{entry.entry_id}_iot_{dev_id}_rfstate"
        self._attr_name = "RF Connected"
        self._attr_device_info = device_info

    @property
    def is_on(self) -> bool | None:
        for dev in self.coordinator.iot_devices:
            if dev.get("id") == self._device_id:
                rf = dev.get("rfnet_state")
                return bool(int(rf)) if rf is not None else None
        return None