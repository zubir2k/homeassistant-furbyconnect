"""Diagnostics for Furby Connect."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import FurbyConfigEntry

TO_REDACT = {"serial"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: FurbyConfigEntry
) -> dict[str, Any]:
    """Return diagnostics: advert, last poll, device info and the raw power report."""
    coord = entry.runtime_data
    snap = coord.data
    return {
        "entry": {"title": entry.title, "options": dict(entry.options)},
        "presence": {
            "awake": coord.present,
            "rssi": coord.rssi,
            "source": coord.source,
            "advertisement": coord.adv,
        },
        "polling": {
            "reachable": coord.reachable,
            "failures": coord.failures,
            "last_error": coord.last_error,
            "last_success": coord.last_success.isoformat() if coord.last_success else None,
        },
        "device_info": async_redact_data(dict(coord.client.device_info), TO_REDACT),
        "status": {
            "im_here": asdict(snap.im_here) if snap and snap.im_here else None,
            "mode": snap.mode if snap else None,
            "power_raw": snap.power_raw if snap else None,
        },
    }
