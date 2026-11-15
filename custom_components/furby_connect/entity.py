"""Base entity."""
from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import protocol as p
from .const import DOMAIN
from .coordinator import FurbyCoordinator


class FurbyEntity(CoordinatorEntity[FurbyCoordinator]):
    """Base entity for Furby Connect."""

    _attr_has_entity_name = True

    def __init__(self, coord: FurbyCoordinator, key: str) -> None:
        super().__init__(coord)
        self._attr_unique_id = f"{coord.address}_{key}"
        self._attr_translation_key = key
        name = (
            coord.config_entry.title
            if coord.config_entry is not None
            else f"Furby {coord.address[-5:]}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coord.address)},
            connections={(CONNECTION_BLUETOOTH, coord.address)},
            name=name,
            manufacturer="Hasbro",
            model="Furby Connect",
        )

    @property
    def im(self) -> p.ImHere | None:
        """Return the latest decoded ImHere status, if available."""
        d = self.coordinator.data
        return d.im_here if d else None

