"""Sensors."""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
    SensorEntityDescription, SensorStateClass)
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory

from . import protocol as p
from .entity import FurbyEntity


@dataclass(frozen=True, kw_only=True)
class FurbySensorDesc(SensorEntityDescription):
    value: Callable


def _slug(name) -> str | None:
    """'HangoutMode' -> 'hangout_mode', so enum states are valid translation keys."""
    if not isinstance(name, str):
        return None
    return re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z0-9])(?=[A-Z][a-z])", "_", name).lower()


def _enum(key, names, value):
    options = [_slug(n) for n in names]
    return FurbySensorDesc(key=key, device_class=SensorDeviceClass.ENUM, options=options,
        value=lambda c, im: v if (v := _slug(value(c, im))) in options else None)


def _pct(attr):
    return FurbySensorDesc(key=attr, native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, value=lambda c, im: getattr(im, attr) if im else None)


SENSORS = [
    _enum("mood", p.MOODS, lambda c, im: im.mood if im else None),
    _enum("personality", p.PERSONALITIES, lambda c, im: im.personality if im else None),
    _enum("mode", p.MODES, lambda c, im: (c.data.mode if c.present else "Sleeping") if c.data else None),
    FurbySensorDesc(key="states", value=lambda c, im: ", ".join(im.states) or "None" if im else None),
    _pct("fullness"), _pct("wellness"), _pct("excited"), _pct("tired"), _pct("displeased"),
    FurbySensorDesc(key="battery", device_class=SensorDeviceClass.BATTERY, native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC,
        value=lambda c, im: c.data.battery if c.data else None),
    FurbySensorDesc(key="last_update", device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC, value=lambda c, im: c.last_success),
    FurbySensorDesc(key="rssi", device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT, entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False, value=lambda c, im: c.rssi if c.present else None),
]


async def async_setup_entry(hass, entry, add):
    add([*(FurbySensor(entry.runtime_data, d) for d in SENSORS), FurbyAdvert(entry.runtime_data)])


class FurbyAdvert(FurbyEntity, SensorEntity):
    """Raw advert, to learn what changes between awake and asleep."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "advert")

    @property
    def available(self) -> bool:
        return bool(self.coordinator.adv)

    @property
    def native_value(self):
        return self.coordinator.adv.get("name")

    @property
    def extra_state_attributes(self):
        return {k: v for k, v in self.coordinator.adv.items() if k != "name"}


class FurbySensor(FurbyEntity, SensorEntity):
    @property
    def extra_state_attributes(self):
        if self.entity_description.key == "battery" and self.coordinator.data:
            return {"power_report_raw": self.coordinator.data.power_raw}
        return None

    entity_description: FurbySensorDesc

    def __init__(self, coord, desc: FurbySensorDesc) -> None:
        super().__init__(coord, desc.key)
        self.entity_description = desc

    @property
    def available(self) -> bool:
        return self.entity_description.key in ("rssi", "last_update") or self.coordinator.data is not None

    @property
    def native_value(self):
        return self.entity_description.value(self.coordinator, self.im)
