"""Diagnostics support for nomaiq.

The download contains device properties and any states captured with the
capture_state service. Credentials and serial numbers are never included.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import NomaIQConfigEntry
from .coordinator import properties_snapshot


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: NomaIQConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a nomaiq config entry."""
    coordinator = entry.runtime_data
    return {
        "devices": [
            {
                "name": device.name,
                "oem_model": device.oem_model_number,
                "model_number": device.device_model_number,
                "properties": properties_snapshot(device),
            }
            for device in coordinator.data
        ],
        "captured_states": coordinator.snapshots,
    }
