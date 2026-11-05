"""Buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from .entity import FurbyEntity


async def async_setup_entry(hass, entry, add):
    add([FurbyRefresh(entry.runtime_data)])


class FurbyRefresh(FurbyEntity, ButtonEntity):
    def __init__(self, c) -> None:
        super().__init__(c, "refresh")

    async def async_press(self) -> None:
        await self.coordinator.async_refresh()
