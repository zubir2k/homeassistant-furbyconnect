"""Sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import FurbyConfigEntry, protocol as p
from .coordinator import FurbyCoordinator
from .entity import FurbyEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class FurbySensorDesc(SensorEntityDescription):
    """Describe a Furby Connect sensor entity."""

    value: Callable[[FurbyCoordinator, p.ImHere | None], Any]


def _slug(name: Any) -> str | None:
    """'HangoutMode' -> 'hangout_mode', so enum states are valid translation keys."""
    if not isinstance(name, str):
        return None
    return re.sub(
        r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z0-9])(?=[A-Z][a-z])", "_", name
    ).lower()


def _enum(
    key: str,
    names: list[str],
    value: Callable[[FurbyCoordinator, p.ImHere | None], Any],
) -> FurbySensorDesc:
    options = [s for n in names if (s := _slug(n)) is not None]
    return FurbySensorDesc(
        key=key,
        device_class=SensorDeviceClass.ENUM,
        options=options,
        value=lambda c, im: v if (v := _slug(value(c, im))) in options else None,
    )


def _pct(attr: str) -> FurbySensorDesc:
    return FurbySensorDesc(
        key=attr,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value=lambda c, im: getattr(im, attr) if im else None,
    )


SENSORS: tuple[FurbySensorDesc, ...] = (
    _enum("mood", p.MOODS, lambda c, im: im.mood if im else None),
    _enum("personality", p.PERSONALITIES, lambda c, im: im.personality if im else None),
    _enum(
        "mode",
        p.MODES,
        lambda c, im: (c.data.mode if c.present else "Sleeping") if c.data else None,
    ),
    FurbySensorDesc(
        key="states",
        value=lambda c, im: ", ".join(im.states) or "None" if im else None,
    ),
    _pct("fullness"),
    _pct("wellness"),
    _pct("excited"),
    _pct("tired"),
    _pct("displeased"),
    FurbySensorDesc(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value=lambda c, im: c.data.battery if c.data else None,
    ),
    FurbySensorDesc(
        key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda c, im: c.last_success,
    ),
    FurbySensorDesc(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value=lambda c, im: c.rssi if c.present else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FurbyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Furby Connect sensor entities."""
    coord = entry.runtime_data
    async_add_entities(
        [*(FurbySensor(coord, d) for d in SENSORS), FurbyAdvert(coord)]
    )


class FurbyAdvert(FurbyEntity, SensorEntity):
    """Raw advert, to learn what changes between awake and asleep."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(self, coord: FurbyCoordinator) -> None:
        super().__init__(coord, "advert")

    @property
    def available(self) -> bool:
        """Return True if an advertisement has been captured."""
        return super().available and bool(self.coordinator.adv)

    @property
    def native_value(self) -> str | None:
        """Return the advertised local name."""
        return self.coordinator.adv.get("name")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the remaining advertisement fields."""
        return {k: v for k, v in self.coordinator.adv.items() if k != "name"}


class FurbySensor(FurbyEntity, SensorEntity):
    """Sensor entity backed by FurbyCoordinator."""

    entity_description: FurbySensorDesc

    def __init__(self, coord: FurbyCoordinator, desc: FurbySensorDesc) -> None:
        super().__init__(coord, desc.key)
        self.entity_description = desc

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return raw power report on the battery sensor if available."""
        if self.entity_description.key == "battery" and self.coordinator.data:
            return {"power_report_raw": self.coordinator.data.power_raw}
        return None

    @property
    def available(self) -> bool:
        """Return whether the sensor has valid data."""
        if not super().available:
            return False
        if self.entity_description.key == "rssi":
            return self.coordinator.present
        if self.entity_description.key == "last_update":
            return self.coordinator.last_success is not None
        return self.coordinator.data is not None

    @property
    def native_value(self) -> str | int | float | datetime | None:
        """Return the current sensor value."""
        return self.entity_description.value(self.coordinator, self.im)

