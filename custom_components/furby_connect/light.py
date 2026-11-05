"""Antenna LED (write-only; state is assumed)."""
from __future__ import annotations

from homeassistant.components.light import ATTR_RGB_COLOR, ColorMode, LightEntity
from homeassistant.helpers.restore_state import RestoreEntity

from . import protocol as p
from .entity import FurbyEntity


async def async_setup_entry(hass, entry, add):
    add([FurbyAntenna(entry.runtime_data)])


class FurbyAntenna(FurbyEntity, LightEntity, RestoreEntity):
    _attr_assumed_state = True
    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}

    def __init__(self, c) -> None:
        super().__init__(c, "antenna")
        self._attr_is_on, self._attr_rgb_color = False, (255, 255, 255)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            self._attr_is_on = last.state == "on"
            if rgb := last.attributes.get(ATTR_RGB_COLOR):
                self._attr_rgb_color = tuple(rgb)

    @property
    def available(self) -> bool:
        return self.coordinator.ble_device() is not None

    async def async_turn_on(self, **kw) -> None:
        rgb = kw.get(ATTR_RGB_COLOR, self._attr_rgb_color)
        await self.coordinator.async_send(p.antenna(*rgb))
        self._attr_is_on, self._attr_rgb_color = True, tuple(rgb)
        self.async_write_ha_state()

    async def async_turn_off(self, **kw) -> None:
        await self.coordinator.async_send(p.antenna(0, 0, 0))
        self._attr_is_on = False
        self.async_write_ha_state()
