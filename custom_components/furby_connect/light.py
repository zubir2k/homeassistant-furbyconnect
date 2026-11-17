"""Antenna LED (write-only; state is assumed)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_RGB_COLOR, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import FurbyConfigEntry, protocol as p
from .coordinator import FurbyCoordinator
from .entity import FurbyEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurbyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Furby Connect antenna light entity."""
    async_add_entities([FurbyAntenna(entry.runtime_data)])


class FurbyAntenna(FurbyEntity, LightEntity, RestoreEntity):
    """RGB light entity controlling the Furby Connect antenna LED."""

    _attr_assumed_state = True
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, coord: FurbyCoordinator) -> None:
        super().__init__(coord, "antenna")
        self._attr_is_on = False
        self._attr_rgb_color = (255, 255, 255)

    async def async_added_to_hass(self) -> None:
        """Restore the last known light state."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state == "on"
            if rgb := last.attributes.get(ATTR_RGB_COLOR):
                self._attr_rgb_color = (int(rgb[0]), int(rgb[1]), int(rgb[2]))

    @property
    def available(self) -> bool:
        """Return True if the Furby is in Bluetooth range."""
        return super().available and self.coordinator.ble_device() is not None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the antenna LED with the given or stored RGB colour."""
        rgb = kwargs.get(ATTR_RGB_COLOR, self._attr_rgb_color) or (255, 255, 255)
        await self.coordinator.async_send(p.antenna(int(rgb[0]), int(rgb[1]), int(rgb[2])))
        self._attr_is_on = True
        self._attr_rgb_color = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the antenna LED."""
        await self.coordinator.async_send(p.antenna(0, 0, 0))
        self._attr_is_on = False
        self.async_write_ha_state()

