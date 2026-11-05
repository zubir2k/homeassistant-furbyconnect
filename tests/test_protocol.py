"""Packet decoding and building."""
from __future__ import annotations

from custom_components.furby_connect import protocol as p

from .conftest import IM_HERE


def test_im_here_decodes() -> None:
    """The 19-byte status reply decodes with the little-endian MAC and BE states."""
    im = p.parse(IM_HERE)
    assert isinstance(im, p.ImHere)
    assert im.mac == "6B:07:12:C1:6C:6C"
    assert im.color == "LightBlue"
    assert im.personality == "Base"
    assert im.mood == "Excited"
    assert (im.excited, im.displeased, im.tired, im.fullness, im.wellness) == (69, 0, 9, 83, 100)
    assert im.wellness_enabled is True
    assert im.states == ["Chewing"]


def test_mode_and_messages() -> None:
    """0x23 is the mode reply, 0x20 a Furby message, anything else is kept raw."""
    assert p.parse(bytes([0x23, 0x08])) == {"type": "mode", "mode": "AppMain"}
    assert p.parse(bytes([0x23, 0x01]))["mode"] == "Sleeping"
    assert p.parse(bytes([0x20, 0x0E]))["message"] == "SequenceEnded"
    assert p.parse(bytes([0x99, 0x01])) == {"type": "0x99", "raw": "9901"}


def test_commands() -> None:
    """Outgoing packets match the protocol."""
    assert p.ARE_YOU_THERE == bytes.fromhex("2006")
    assert p.GET_MODE == bytes.fromhex("200c")
    assert p.antenna(255, 0, 128) == bytes.fromhex("14ff0080")
    assert p.mood_meter(3, 100) == bytes.fromhex("23010364")
