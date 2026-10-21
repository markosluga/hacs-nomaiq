"""The nomaiq integration."""

from __future__ import annotations

from datetime import timedelta
import logging

import ayla_iot_unofficial

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    ServiceValidationError,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import CLIENT_ID, CLIENT_SECRET, DOMAIN, NORMAL_UPDATE_INTERVAL
from .coordinator import NomaIQDataUpdateCoordinator, properties_snapshot

_PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.COVER,
    Platform.HUMIDIFIER,
    Platform.SELECT,
]
_LOGGER = logging.getLogger(__name__)

type NomaIQConfigEntry = ConfigEntry[NomaIQDataUpdateCoordinator]

CAPTURE_STATE_SERVICE = "capture_state"
CAPTURE_STATE_SCHEMA = vol.Schema(
    {
        vol.Required("device"): cv.string,
        vol.Required("description"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register integration-level services."""

    async def _async_capture_state(call: ServiceCall) -> None:
        """Fetch fresh cloud values for a device and store them as a labeled capture."""
        device_entry = dr.async_get(hass).async_get(call.data["device"])
        serial = next(
            (ident for domain, ident in device_entry.identifiers if domain == DOMAIN),
            None,
        ) if device_entry else None
        if serial is None:
            raise ServiceValidationError("Select a Noma IQ device")

        for entry in hass.config_entries.async_entries(DOMAIN):
            coordinator = entry.runtime_data
            device = next(
                (d for d in coordinator.data if d.serial_number == serial), None
            )
            if device is None:
                continue
            await device.async_update()
            coordinator.snapshots.append(
                {
                    "captured_at": dt_util.utcnow().isoformat(),
                    "description": call.data["description"],
                    "device_name": device.name,
                    "properties": properties_snapshot(device),
                }
            )
            return

        raise ServiceValidationError("Device is not loaded")

    hass.services.async_register(
        DOMAIN, CAPTURE_STATE_SERVICE, _async_capture_state, schema=CAPTURE_STATE_SCHEMA
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: NomaIQConfigEntry) -> bool:
    """Set up nomaiq from a config entry."""

    config = entry.data
    options = entry.options

    username = options.get(CONF_USERNAME, config.get(CONF_USERNAME, ""))
    password = options.get(CONF_PASSWORD, config.get(CONF_PASSWORD, ""))

    session = async_get_clientsession(hass)
    api = ayla_iot_unofficial.new_ayla_api(
        username, password, CLIENT_ID, CLIENT_SECRET, session
    )

    try:
        await api.async_sign_in()
    except ayla_iot_unofficial.AylaAuthError as err:
        raise ConfigEntryAuthFailed(f"Authentication failed: {err}") from err
    except ayla_iot_unofficial.AylaApiError as err:
        raise ConfigEntryNotReady(f"API error: {err}") from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during setup", extra={"error": err})
        raise ConfigEntryNotReady(f"Unexpected error: {err}") from err

    coordinator = NomaIQDataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        update_interval=timedelta(seconds=NORMAL_UPDATE_INTERVAL),
        api=api,
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: NomaIQConfigEntry) -> bool:
    """Unload a config entry."""

    await entry.runtime_data.api.async_sign_out()
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
