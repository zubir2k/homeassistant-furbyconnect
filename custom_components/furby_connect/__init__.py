"""Furby Connect integration."""
from __future__ import annotations

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant

from .coordinator import FurbyCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.LIGHT, Platform.NUMBER, Platform.BUTTON]
type FurbyConfigEntry = ConfigEntry[FurbyCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FurbyConfigEntry) -> bool:
    address = entry.data[CONF_ADDRESS]
    coord = FurbyCoordinator(hass, entry, address)
    entry.runtime_data = coord
    entry.async_on_unload(bluetooth.async_register_callback(
        hass, coord.handle_advert,
        bluetooth.BluetoothCallbackMatcher(address=address, connectable=True),
        bluetooth.BluetoothScanningMode.PASSIVE))
    entry.async_on_unload(bluetooth.async_track_unavailable(
        hass, coord.handle_unavailable, address, connectable=True))
    if info := bluetooth.async_last_service_info(hass, address, connectable=True):
        coord.handle_advert(info, None)
    await coord.async_refresh()  # never blocks setup if the toy is asleep
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: FurbyConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: FurbyConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
