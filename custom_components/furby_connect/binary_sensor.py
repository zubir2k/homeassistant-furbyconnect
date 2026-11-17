"""Binary sensors. States bit order is unverified (see protocol.py)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FurbyConfigEntry
from .coordinator import FurbyCoordinator
from .entity import FurbyEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurbyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Furby Connect binary sensor entities."""
    coord = entry.runtime_data
    async_add_entities(
        [
            FurbyAwake(coord),
            FurbyReachable(coord),
            FurbyState(coord, "hungry", "Hungry"),
            FurbyState(coord, "sick", "Sick", BinarySensorDeviceClass.PROBLEM),
        ]
    )


class FurbyAwake(FurbyEntity, BinarySensorEntity):
    """Furby only advertises while awake, so a recent advert = awake. Passive, no connection."""

    def __init__(self, coord: FurbyCoordinator) -> None:
        super().__init__(coord, "awake")

    @property
    def available(self) -> bool:
        """Return True if the coordinator is available."""
        return super().available

    @property
    def is_on(self) -> bool:
        """Return True if the Furby has advertised recently."""
        return self.coordinator.present

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return advertisement proxy and RSSI."""
        coord = self.coordinator
        return {"proxy": coord.source, "rssi": coord.rssi}


class FurbyState(FurbyEntity, BinarySensorEntity):
    """Binary sensor for a flag in the ImHere states bitmask."""

    def __init__(
        self,
        coord: FurbyCoordinator,
        key: str,
        state: str,
        dc: BinarySensorDeviceClass | None = None,
    ) -> None:
        super().__init__(coord, key)
        self._state = state
        self._attr_device_class = dc

    @property
    def available(self) -> bool:
        """Return True once an ImHere packet has been received."""
        return super().available and self.im is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if the state flag is active."""
        return self._state in self.im.states if self.im else None


class FurbyReachable(FurbyEntity, BinarySensorEntity):
    """Last connection attempt succeeded."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coord: FurbyCoordinator) -> None:
        super().__init__(coord, "reachable")

    @property
    def available(self) -> bool:
        """Return True if the coordinator is available."""
        return super().available

    @property
    def is_on(self) -> bool:
        """Return True if the last GATT poll succeeded."""
        return self.coordinator.reachable

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return connection failure count and last error details."""
        coord = self.coordinator
        return {
            "failures": coord.failures,
            "last_error": coord.last_error,
            "proxy": coord.source,
            "rssi": coord.rssi,
        }

