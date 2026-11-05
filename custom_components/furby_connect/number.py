"""Set mood meters (feed, heal...)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE

from . import protocol as p
from .entity import FurbyEntity

METERS = {"set_fullness": (3, "fullness"), "set_wellness": (4, "wellness")}


async def async_setup_entry(hass, entry, add):
    add(FurbyMeter(entry.runtime_data, k, *v) for k, v in METERS.items())


class FurbyMeter(FurbyEntity, NumberEntity):
    _attr_native_min_value, _attr_native_max_value, _attr_native_step = 0, 100, 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, c, key, meter, attr) -> None:
        super().__init__(c, key)
        self._meter, self._attr = meter, attr

    @property
    def available(self) -> bool:
        return self.coordinator.ble_device() is not None

    @property
    def native_value(self):
        return getattr(self.im, self._attr) if self.im else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_send(p.mood_meter(self._meter, int(value), set_=True))
        await self.coordinator.async_request_refresh()
