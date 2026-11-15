"""Buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import FurbyConfigEntry
from .coordinator import FurbyCoordinator
from .entity import FurbyEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurbyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Furby Connect button entities."""
    async_add_entities([FurbyRefresh(entry.runtime_data)])


class FurbyRefresh(FurbyEntity, ButtonEntity):
    """Button to trigger an immediate GATT status poll."""

    def __init__(self, coord: FurbyCoordinator) -> None:
        super().__init__(coord, "refresh")

    async def async_press(self) -> None:
        """Poll the Furby now."""
        await self.coordinator.async_refresh()

