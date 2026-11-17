"""Set mood meters (feed, heal...)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FurbyConfigEntry, protocol as p
from .coordinator import FurbyCoordinator
from .entity import FurbyEntity

PARALLEL_UPDATES = 1

METERS: dict[str, tuple[int, str]] = {
    "set_fullness": (3, "fullness"),
    "set_wellness": (4, "wellness"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurbyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Furby Connect number entities."""
    coord = entry.runtime_data
    async_add_entities(
        FurbyMeter(coord, key, meter, attr)
        for key, (meter, attr) in METERS.items()
    )


class FurbyMeter(FurbyEntity, NumberEntity):
    """Number entity to set a Furby mood meter."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self, coord: FurbyCoordinator, key: str, meter: int, attr: str
    ) -> None:
        super().__init__(coord, key)
        self._meter = meter
        self._attr = attr

    @property
    def available(self) -> bool:
        """Return True if the Furby is in Bluetooth range."""
        return super().available and self.coordinator.ble_device() is not None

    @property
    def native_value(self) -> float | None:
        """Return the current meter percentage."""
        return getattr(self.im, self._attr) if self.im else None

    async def async_set_native_value(self, value: float) -> None:
        """Write the new meter percentage to the Furby."""
        await self.coordinator.async_send(
            p.mood_meter(self._meter, int(value), set_=True)
        )
        await self.coordinator.async_request_refresh()

