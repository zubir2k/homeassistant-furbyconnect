"""Short-lived BLE sessions with a Furby Connect.

Every call connects, does its job and disconnects, so the toy can fall asleep
again and the ESPHome proxy slot is freed.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from . import protocol as p
from .const import REPLY_TIMEOUT

_LOGGER = logging.getLogger(__name__)
DIS = {"model": "00002a24-0000-1000-8000-00805f9b34fb", "serial": "00002a25-0000-1000-8000-00805f9b34fb",
       "firmware": "00002a26-0000-1000-8000-00805f9b34fb", "hardware": "00002a27-0000-1000-8000-00805f9b34fb",
       "software": "00002a28-0000-1000-8000-00805f9b34fb", "manufacturer": "00002a29-0000-1000-8000-00805f9b34fb"}
BATTERY_LEVEL = "00002a19-0000-1000-8000-00805f9b34fb"  # standard Battery Service, if the Furby exposes it


@dataclass
class FurbySnapshot:
    im_here: p.ImHere | None
    mode: str | None
    battery: int | None = None
    power_raw: str | None = None


class FurbyClient:
    def __init__(self, name: str) -> None:
        self._name = name
        self._lock = asyncio.Lock()
        self._logged_services = False
        self.battery: int | None = None
        self.power_raw: str | None = None
        self.device_info: dict[str, str] = {}

    async def _session(self, device: BLEDevice, writes: list[bytes], want: set[int],
                       probe_power: bool = False) -> dict[int, bytes]:
        """Connect, subscribe, send writes, collect first reply per opcode in `want`."""
        got: dict[int, bytes] = {}
        done = asyncio.Event()

        def _on_notify(_char, data: bytearray) -> None:
            pkt = bytes(data)
            _LOGGER.debug("%s <- %s", self._name, pkt.hex())
            if pkt and pkt[0] in want and pkt[0] not in got:
                got[pkt[0]] = pkt
                if want <= got.keys():
                    done.set()

        async with self._lock:
            client = await establish_connection(
                BleakClientWithServiceCache, device, self._name, max_attempts=2
            )
            try:
                if not self._logged_services:
                    self._logged_services = True
                    for svc in client.services:
                        _LOGGER.debug("%s service %s: %s", self._name, svc.uuid,
                                      [f"{c.uuid}({','.join(c.properties)})" for c in svc.characteristics])
                if not self.device_info:
                    for key, uuid in DIS.items():
                        ch = client.services.get_characteristic(uuid)
                        if ch is not None:
                            try:
                                self.device_info[key] = bytes(await client.read_gatt_char(ch)).decode(errors="replace").strip("\x00 ")
                            except Exception as err:  # noqa: BLE001
                                _LOGGER.debug("%s read %s failed: %s", self._name, key, err)
                    _LOGGER.debug("%s device info: %s", self._name, self.device_info)
                if probe_power:
                    def _on_ctrl(_c, data: bytearray) -> None:
                        pkt = bytes(data)
                        _LOGGER.debug("%s ctrl <- %s", self._name, pkt.hex())
                        if pkt[:1] == b"\x03":
                            self.power_raw = pkt.hex()
                    try:
                        await client.start_notify(p.CTRL_NOTIFY, _on_ctrl)
                        _LOGGER.debug("%s ctrl -> 03", self._name)
                        await client.write_gatt_char(p.CTRL_WRITE, b"\x03", response=False)
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.debug("%s power probe failed: %s", self._name, err)
                batt = client.services.get_characteristic(BATTERY_LEVEL)
                if batt is not None:
                    try:
                        self.battery = (await client.read_gatt_char(batt))[0]
                        _LOGGER.debug("%s battery %s%%", self._name, self.battery)
                    except Exception as err:  # noqa: BLE001
                        _LOGGER.debug("%s battery read failed: %s", self._name, err)
                await client.start_notify(p.DATA_NOTIFY, _on_notify)
                for w in writes:
                    _LOGGER.debug("%s -> %s", self._name, w.hex())
                    await client.write_gatt_char(p.DATA_WRITE, w, response=False)  # char is write-without-response
                    await asyncio.sleep(0.15)
                if want:
                    try:
                        await asyncio.wait_for(done.wait(), REPLY_TIMEOUT)
                    except asyncio.TimeoutError:
                        _LOGGER.debug("%s: timed out, got %s", self._name, list(got))
            finally:
                await client.disconnect()
        return got

    async def poll(self, device: BLEDevice) -> FurbySnapshot:
        got = await self._session(device, [p.ARE_YOU_THERE, p.GET_MODE], {0x22, 0x23}, probe_power=True)
        im = p.parse(got[0x22]) if 0x22 in got else None
        mode = p.parse(got[0x23])["mode"] if 0x23 in got else None
        if im is None and mode is None:
            raise TimeoutError("Furby connected but sent no status")
        return FurbySnapshot(im_here=im, mode=mode, battery=self.battery, power_raw=self.power_raw)

    async def send(self, device: BLEDevice, *packets: bytes) -> None:
        await self._session(device, list(packets), set())
