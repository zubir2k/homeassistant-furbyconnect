"""Furby Connect BLE protocol (builds on Jeija/bluefluff, plus interoperability testing).

All UUIDs are DAB9XXXX-B5A1-E29C-B041-BCD562613BDE.
Bit order of the bitmasks (inputs1/inputs2/states) is UNVERIFIED: confirm on a live toy.
"""
from __future__ import annotations
from dataclasses import dataclass, field

BASE = "dab9{}-b5a1-e29c-b041-bcd562613bde"
SERVICE = BASE.format("1435")
DATA_NOTIFY = BASE.format("1382")   # GeneralPlus -> app
DATA_WRITE = BASE.format("1383")    # app -> GeneralPlus
CTRL_RSSI = BASE.format("0755")
CTRL_NOTIFY = BASE.format("0756")   # Nordic -> app
CTRL_WRITE = BASE.format("0757")    # app -> Nordic
FILE_WRITE = BASE.format("0758")
P2P_NOTIFY = BASE.format("1440")
P2P_WRITE = BASE.format("1441")

KEEPALIVE_INTERVAL_S = 3.0          # app sends AreYouThere every 3 s

# App -> Furby (DATA_WRITE)
def msg(app_to_furby: int) -> bytes:        return bytes([0x20, app_to_furby])
ARE_YOU_THERE = msg(6)                       # -> 0x22 ImHere reply (mood/status)
GET_MODE = msg(12)                           # -> 0x23 CurrentMode
ACCEL_ON, ACCEL_OFF = msg(13), msg(14)       # -> 0x21 stream
GET_LANGUAGE, GET_FURBIES_MET = msg(15), msg(16)
def antenna(r: int, g: int, b: int) -> bytes: return bytes([0x14, r, g, b])
def mood_meter(meter: int, value: int, set_: bool = True) -> bytes:
    return bytes([0x23, 1 if set_ else 0, meter, value])   # meter: 0 excited,1 displeased,2 tired,3 fullness,4 wellness
def play_specific(inp: int, idx: int, sub: int, spec: int) -> bytes: return bytes([0x13, 0, inp, idx, sub, spec])  # layout of byte1 unverified
def lcd_eyes(on: bool) -> bytes: return bytes([0xCD, 1 if on else 0])

NAMES_COLORS = ["Pink", "LightBlue", "Teal", "Purple", "Orange"]
PERSONALITIES = ["Base", "DJ", "Princess", "Ninja", "Pirate", "Cat", "Popstar"]
MOODS = ["Excited", "Displeased", "Tired", "Neutral"]
STATES = {1: "Hungry", 2: "Sick", 3: "Talking", 4: "Hiccup", 5: "Garbled", 6: "Gagging",
          7: "Chewing", 8: "Postchewing", 9: "BPM", 10: "Fart"}
MODES = ["None", "Sleeping", "Wakeup", "HangoutMode", "F2FMaster", "F2FSlave",
         "Interactive", "MakingMusic", "AppMain", "AppNaming"]
INPUTS1 = ["SensorHead", "SensorTummy", "SensorLeft", "SensorRight", "SwitchTail", "SwitchMouth",
           "AntennaFront", "AntennaBack", "AntennaLeft", "AntennaRight", "Unknown1", "Unknown2",
           "VoiceLow", "VoiceHigh", "SharpSound", "Music"]
INPUTS2 = ["TiltUpright", "TiltUpsideDown", "TiltLandscapeLeft", "TiltLandscapeRight", "TiltOnFace",
           "TiltOnBack", "TiltLeft", "TiltRight", "TiltUNUSED", "TiltShake", "TiltRightedAfterUpsideDown",
           "TiltRockingOnBack", "TiltRightedAfterRockingOnBack", "TiltJolted", "TiltPickedUp", "TiltThrown"]
FURBY_TO_APP = {1: "EnteredNamingMode", 2: "ExitedNamingMode", 3: "FurbyNamedSignal", 4: "EnteredAppMode",
    5: "ExitedAppMode", 6: "ResponsePlayed", 7: "SpeechPlaying", 8: "SlaveAck", 9: "OtherResponseReceived",
    10: "MaskAdded", 11: "MaskRemoved", 12: "SequencePlaying", 13: "SequenceCancelled", 14: "SequenceEnded",
    19: "SleepMaskAdded", 20: "SleepMaskRemoved", 21: "BodyCamOn", 22: "BodyCamOff", 23: "LCDEyesOn",
    24: "LCDEyesOff", 25: "GroupNotActive", 26: "TimedGroupSet", 27: "CustomNotificationSet", 154: "AckRequired"}


def _bits(v: int, names, base=0):
    # ASSUMPTION: enum value n == bit n, value read big-endian. Verify live.
    return [names[i] if isinstance(names, list) else names.get(i + base, f"bit{i}")
            for i in range(16) if v >> i & 1 and (isinstance(names, dict) or i < len(names))]


@dataclass
class ImHere:          # 0x22, 19 bytes on firmware seen 2026-10 (op, mac[6] LE, name, colour, pers, mood, 5 meters, wellness_en, states[2] BE)
    mac: str
    name_index: int
    color: str
    personality: str
    mood: str
    excited: float; displeased: float; tired: float; fullness: float; wellness: float
    wellness_enabled: bool
    states: list = field(default_factory=list)

def parse(pkt: bytes):
    op = pkt[0]
    if op == 0x22 and len(pkt) >= 18:
        g = lambda i, tbl: tbl[pkt[i]] if pkt[i] < len(tbl) else pkt[i]
        st = pkt[17:19] if len(pkt) >= 19 else pkt[16:18]
        return ImHere(mac=":".join(f"{b:02X}" for b in reversed(pkt[1:7])), name_index=pkt[7],
            color=g(8, NAMES_COLORS), personality=g(9, PERSONALITIES), mood=g(10, MOODS),
            excited=pkt[11], displeased=pkt[12], tired=pkt[13], fullness=pkt[14], wellness=pkt[15],
            wellness_enabled=bool(pkt[16]), states=_bits(int.from_bytes(st, "big"), STATES, 1))
    if op == 0x21 and len(pkt) >= 8:
        s8 = lambda b: b - 256 if b > 127 else b
        return {"type": "inputs",
                "inputs1": _bits(int.from_bytes(pkt[1:3], "big"), INPUTS1),
                "inputs2": _bits(int.from_bytes(pkt[3:5], "big"), INPUTS2),
                "accel_deg": tuple(round(s8(b) / 127 * 360, 1) for b in pkt[5:8])}
    if op == 0x23:
        return {"type": "mode", "mode": MODES[pkt[1]] if len(pkt) > 1 and pkt[1] < len(MODES) else pkt[1:].hex()}
    if op == 0x20 and len(pkt) > 1:
        return {"type": "message", "message": FURBY_TO_APP.get(pkt[1], pkt[1])}
    if op == 0x25 and len(pkt) > 1:
        return {"type": "language", "value": pkt[1]}
    return {"type": f"0x{op:02x}", "raw": pkt.hex()}
