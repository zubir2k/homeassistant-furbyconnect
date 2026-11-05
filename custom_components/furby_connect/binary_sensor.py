"""Binary sensors. States bit order is unverified (see protocol.py)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from homeassistant.const import EntityCategory

from .entity import FurbyEntity


async def async_setup_entry(hass, entry, add):
    c = entry.runtime_data
    add([FurbyAwake(c), FurbyReachable(c), FurbyState(c, "hungry", "Hungry"), FurbyState(c, "sick", "Sick", BinarySensorDeviceClass.PROBLEM)])


class FurbyAwake(FurbyEntity, BinarySensorEntity):
    """Furby only advertises while awake, so a recent advert = awake. Passive, no connection."""

    def __init__(self, c) -> None:
        super().__init__(c, "awake")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.present

    @property
    def extra_state_attributes(self):
        c = self.coordinator
        return {"proxy": c.source, "rssi": c.rssi}


class FurbyState(FurbyEntity, BinarySensorEntity):
    def __init__(self, c, key, state, dc=None) -> None:
        super().__init__(c, key)
        self._state, self._attr_device_class = state, dc

    @property
    def available(self) -> bool:
        return self.im is not None

    @property
    def is_on(self) -> bool | None:
        return self._state in self.im.states if self.im else None


class FurbyReachable(FurbyEntity, BinarySensorEntity):
    """Last connection attempt succeeded."""
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "reachable")

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.reachable

    @property
    def extra_state_attributes(self):
        c = self.coordinator
        return {"failures": c.failures, "last_error": c.last_error, "proxy": c.source, "rssi": c.rssi}
