"""Platform for dehumidifier integration."""

from __future__ import annotations

from typing import Any

import ayla_iot_unofficial
import ayla_iot_unofficial.device

from homeassistant.components.humidifier import (
    HumidifierDeviceClass,
    HumidifierEntity,
    HumidifierEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NomaIQConfigEntry
from .const import DOMAIN
from .coordinator import NomaIQDataUpdateCoordinator

DEHUMIDIFIER_OEM_MODEL = "dehum"

# App label -> raw value stored in the device's "mode" property
MODE_TO_RAW: dict[str, str] = {
    "manual": "Normal",
    "auto dry": "Auto",
    "continuous": "Persistent",
}
RAW_TO_MODE: dict[str, str] = {raw: label for label, raw in MODE_TO_RAW.items()}

MIN_HUMIDITY = 30
MAX_HUMIDITY = 80


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NomaIQConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Noma IQ dehumidifier platform."""
    coordinator: NomaIQDataUpdateCoordinator = entry.runtime_data

    for device in coordinator.data:
        if device.oem_model_number == DEHUMIDIFIER_OEM_MODEL:
            async_add_entities(
                [NomaIQDehumidifierEntity(coordinator, device)],
                update_before_add=False,
            )


class NomaIQDehumidifierEntity(HumidifierEntity):
    """Representation of a NomaIQ dehumidifier."""

    _attr_device_class = HumidifierDeviceClass.DEHUMIDIFIER
    _attr_supported_features = HumidifierEntityFeature.MODES
    _attr_available_modes = list(MODE_TO_RAW)
    _attr_min_humidity = MIN_HUMIDITY
    _attr_max_humidity = MAX_HUMIDITY
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: NomaIQDataUpdateCoordinator,
        device: ayla_iot_unofficial.device.Device,
    ) -> None:
        """Initialize a NomaIQ dehumidifier."""
        self.coordinator = coordinator
        self._device = device
        self._attr_unique_id = f"nomaiq_dehumidifier_{device.serial_number}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.serial_number)},
            name=device.name,
            model=device.device_model_number,
        )

    def _get_current_device(self) -> ayla_iot_unofficial.device.Device | None:
        """Get the current device from coordinator data."""
        data: list[ayla_iot_unofficial.device.Device] = self.coordinator.data
        return next(
            (d for d in data if d.serial_number == self._device.serial_number),
            None,
        )

    def _get_value(self, property_name: str) -> Any:
        """Read a property from the latest coordinator data."""
        device = self._get_current_device()
        return device.get_property_value(property_name) if device else None

    @property
    def is_on(self) -> bool | None:
        """Return true if the dehumidifier is on."""
        power = self._get_value("power")
        return None if power is None else bool(power)

    @property
    def current_humidity(self) -> int | None:
        """Return the measured indoor humidity."""
        return self._get_value("indoor_humidity")

    @property
    def target_humidity(self) -> int | None:
        """Return the target humidity."""
        return self._get_value("humidity")

    @property
    def mode(self) -> str | None:
        """Return the current mode as an app label."""
        raw = self._get_value("mode")
        return RAW_TO_MODE.get(raw)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the dehumidifier on."""
        await self._device.async_set_property_value("power", 1)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the dehumidifier off."""
        await self._device.async_set_property_value("power", 0)
        await self.coordinator.async_request_refresh()

    async def async_set_humidity(self, humidity: int) -> None:
        """Set the target humidity, rounded to the device's 5% step."""
        step_value = round(humidity / 5) * 5
        step_value = min(max(step_value, MIN_HUMIDITY), MAX_HUMIDITY)
        await self._device.async_set_property_value("humidity", step_value)
        await self.coordinator.async_request_refresh()

    async def async_set_mode(self, mode: str) -> None:
        """Set the operating mode."""
        raw = MODE_TO_RAW.get(mode)
        if raw is None:
            raise ValueError(f"Unsupported mode: {mode}")
        await self._device.async_set_property_value("mode", raw)
        await self.coordinator.async_request_refresh()

    async def async_update(self) -> None:
        """Update the dehumidifier state."""
        await self.coordinator.async_request_refresh()
