"""Base entity."""
from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FurbyCoordinator


class FurbyEntity(CoordinatorEntity[FurbyCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coord: FurbyCoordinator, key: str) -> None:
        super().__init__(coord)
        self._attr_unique_id = f"{coord.address}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coord.address)},
            connections={(CONNECTION_BLUETOOTH, coord.address)},
            name=coord.config_entry.title, manufacturer="Hasbro", model="Furby Connect")

    @property
    def im(self):
        d = self.coordinator.data
        return d.im_here if d else None
