"""Coordinator: passive presence from adverts + periodic short polls."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
import time
from typing import Any

from bleak.backends.device import BLEDevice
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .client import FurbyClient, FurbySnapshot
from .const import CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES, DOMAIN, PRESENCE_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class FurbyCoordinator(DataUpdateCoordinator[FurbySnapshot | None]):
    """Coordinate passive BLE advertisements and active GATT status polls."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, address: str) -> None:
        minutes = entry.options.get(CONF_POLL_MINUTES, DEFAULT_POLL_MINUTES)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {address}",
            update_interval=timedelta(minutes=minutes),
            config_entry=entry,
        )
        self.address = address
        self.client = FurbyClient(entry.title)
        self.rssi: int | None = None
        self.last_seen: float | None = None
        self.source: str | None = None
        self.adv: dict[str, Any] = {}
        self.failures = 0
        self.last_success: datetime | None = None
        self.last_error: str | None = None
        self._skip = 0
        self._last_attempt = 0.0
        self._dr_done = False
        self._unsub_presence: CALLBACK_TYPE | None = None

    @property
    def present(self) -> bool:
        """Return True if an advertisement was seen within PRESENCE_TIMEOUT."""
        return (
            self.last_seen is not None
            and time.monotonic() - self.last_seen < PRESENCE_TIMEOUT
        )

    @callback
    def cancel_presence_timer(self) -> None:
        """Cancel the scheduled presence expiry callback if active."""
        if self._unsub_presence is not None:
            self._unsub_presence()
            self._unsub_presence = None

    @callback
    def _handle_presence_timeout(self, _now: datetime) -> None:
        """Mark listeners updated once the presence timeout expires."""
        self._unsub_presence = None
        self.async_update_listeners()

    @callback
    def handle_advert(
        self,
        info: bluetooth.BluetoothServiceInfoBleak,
        _change: bluetooth.BluetoothChange | None = None,
        *,
        seed_only: bool = False,
    ) -> None:
        """Process a Bluetooth advertisement from the Furby."""
        was_present = self.present
        self.rssi = info.rssi
        self.last_seen = time.monotonic()
        self.source = info.source
        self.cancel_presence_timer()
        self._unsub_presence = async_call_later(
            self.hass, PRESENCE_TIMEOUT + 0.5, self._handle_presence_timeout
        )
        adv: dict[str, Any] = {
            "name": info.name,
            "source": info.source,
            "rssi": info.rssi,
            "connectable": info.connectable,
            "manufacturer_data": {
                str(k): v.hex() for k, v in info.manufacturer_data.items()
            },
            "service_uuids": list(info.service_uuids),
            "tx_power": info.tx_power,
        }
        if {k: v for k, v in adv.items() if k not in ("rssi", "source")} != {
            k: v for k, v in self.adv.items() if k not in ("rssi", "source")
        }:
            _LOGGER.debug("Furby %s advert changed: %s", self.address, adv)
        self.adv = adv
        if seed_only:
            return
        self.async_update_listeners()
        if not was_present and time.monotonic() - self._last_attempt > 60:
            # Just woke up: grab a fresh status now (it's awake, so the connect should work).
            self._skip = 0
            self._last_attempt = time.monotonic()
            if self.config_entry is not None:
                self.config_entry.async_create_background_task(
                    self.hass,
                    self.async_request_refresh(),
                    "furby_wakeup_refresh",
                )
            else:
                self.hass.async_create_task(self.async_request_refresh())

    @callback
    def handle_unavailable(
        self, _info: bluetooth.BluetoothServiceInfoBleak
    ) -> None:
        """Handle Bluetooth unavailable callback."""
        self.cancel_presence_timer()
        self.last_seen = None
        self.async_update_listeners()

    async def async_shutdown(self) -> None:
        """Cancel presence timer on coordinator shutdown."""
        self.cancel_presence_timer()
        await super().async_shutdown()

    def ble_device(self) -> BLEDevice | None:
        """Return the connectable BLEDevice for this Furby, if available."""
        return bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )

    async def _async_update_data(self) -> FurbySnapshot | None:
        device = self.ble_device()
        if device is None or not self.present:
            # Asleep or out of range: keep the last known state rather than failing.
            return self.data
        if self._skip:
            # Backing off after failed connects: don't hammer a dozing Furby / busy proxy.
            self._skip -= 1
            return self.data
        self._last_attempt = time.monotonic()
        try:
            snap = await self.client.poll(device)
        except Exception as err:  # noqa: BLE001
            self.failures += 1
            self.last_error = str(err)[:250]
            self._skip = min(2 ** (self.failures - 1) - 1, 5)  # 0,1,3,5,5... polls skipped
            log = _LOGGER.warning if self.failures in (1, 5) else _LOGGER.debug
            log(
                "Furby %s unreachable via %s (rssi %s, failure %s): %s",
                self.address,
                self.source,
                self.rssi,
                self.failures,
                err,
            )
            return self.data  # keep last values; Reachable sensor shows the problem
        if self.failures:
            _LOGGER.info(
                "Furby %s reachable again after %s failures",
                self.address,
                self.failures,
            )
        self.failures = 0
        self._skip = 0
        self.last_error = None
        self.last_success = dt_util.utcnow()
        self._update_device_registry()
        return snap

    def _update_device_registry(self) -> None:
        info = self.client.device_info
        if not info or self._dr_done:
            return
        self._dr_done = True
        reg = dr.async_get(self.hass)
        dev = reg.async_get_device(identifiers={(DOMAIN, self.address)})
        if dev:
            reg.async_update_device(
                dev.id,
                sw_version=info.get("firmware") or info.get("software"),
                hw_version=info.get("hardware"),
                serial_number=info.get("serial"),
            )

    @property
    def reachable(self) -> bool:
        """Return True if the last connection attempt succeeded."""
        return self.failures == 0 and self.last_success is not None

    async def async_send(self, *packets: bytes) -> None:
        """Send one or more command packets to the Furby."""
        device = self.ble_device()
        if device is None:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="not_in_range",
            )
        try:
            await self.client.send(device, *packets)
        except Exception as err:  # noqa: BLE001
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(err)},
            ) from err

