"""Diagnostics support for tetraHAconnect integration."""

from __future__ import annotations

from typing import Any
from pathlib import Path

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

TO_REDACT: set[str] = {
    "latitude",
    "longitude",
    "lat",
    "lng",
    "issi_sen",
    "issi_rec",
}


def _read_log(log_path: str) -> list[str]:
    try:
        with Path(log_path).open("r", encoding="utf-8") as log_file:
            return [line.rstrip() for line in log_file if "tetrahaconnect" in line]
    except OSError as ex:
        return [f"Log read error: {ex}"]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data: dict[str, Any] = dict(entry.data)
    options: dict[str, Any] = dict(entry.options)

    # Read and filter logs for tetraHAconnect
    log_path = "config/home-assistant.log"
    tetrahaconnect_logs = await hass.async_add_executor_job(_read_log, log_path)

    return {
        "entry_data": async_redact_data(data, TO_REDACT),
        "options": async_redact_data(options, TO_REDACT),
        "runtime_data": getattr(entry, "runtime_data", None),
        "logs": tetrahaconnect_logs,
    }


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
    device: dr.DeviceEntry,
) -> dict[str, Any]:
    """Return diagnostics for a device."""
    # entity_registry = er.async_get(hass)
    # config_entry_id = entry.entry_id

    return {
        "device_details": {
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "revision": device.sw_version,
        },
    }
