![Furby Connect](custom_components/furby_connect/brand/logo@2x.png)
## Furby Connect for Home Assistant
![GitHub Repo stars](https://img.shields.io/github/stars/zubir2k/homeassistant-furbyconnect?style=social)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
![GitHub all releases](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=Download%20Count&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.furby_connect.total)
[![Buy](https://img.shields.io/badge/Belanja-Coffee-yellow.svg)](https://zubirco.de/buymecoffee)
[![Github Releases](https://img.shields.io/github/v/release/zubir2k/homeassistant-furbyconnect)](https://github.com/zubir2k/homeassistant-furbyconnect/releases)

Bring your old **Furby Connect** (Hasbro, 2016) into Home Assistant. See its mood and needs, feed or heal it, and change its antenna colour. It's fully local over Bluetooth, through your HA adapter or **ESPHome Bluetooth proxies**.

> [!Note]
> Requires Home Assistant 2026.3 or newer. This is a **beta**: it works on real hardware, but parts of the protocol are still being verified.

## Features
- **Awake / Asleep**, passively, from Bluetooth adverts. Nothing connects while Furby sleeps.
- **Mood, Personality, Mode** and the five mood meters: **Fullness, Wellness, Excitement, Tiredness, Displeasure**.
- **Hungry** and **Sick** binary sensors, ready for automations ("Furby is hungry!").
- **Antenna** RGB light, **Feed** and **Heal** sliders, **Refresh status** button.
- Device info (model, firmware, hardware) in the device page, plus diagnostics.
- English and Bahasa Melayu.

## Installation
#### With HACS
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=zubir2k&repository=homeassistant-furbyconnect&category=integration)

> [!Tip]
> If the button doesn't work: HACS → ⋮ → **Custom repositories**, then add `https://github.com/zubir2k/homeassistant-furbyconnect` as **Integration**. Download **Furby Connect** and restart Home Assistant.

#### Manual
1. Copy the `furby_connect` directory from `custom_components` in this repository into your Home Assistant's `custom_components` directory.
2. Restart Home Assistant.
3. Follow the steps in the `Setup` section.

> [!WARNING]
> If you install manually, subscribe to this repository's releases to hear about new versions.

## Setup
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=furby_connect)

> [!Tip]
> 1. Wake your Furby (tickle it or pull its tail) so it advertises.
> 2. Home Assistant usually discovers it on its own. If it doesn't, go to **Settings → Devices & services → Add integration** and search for `Furby Connect`.
> 3. Optional: **Configure** sets how often to check status while Furby is awake (default 10 minutes).

You need a Bluetooth adapter Home Assistant can use, or an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html) with `active: true`.

## Entities

| Entity | Type | Notes |
|---|---|---|
| Awake | binary sensor | `Awake` while Furby advertises, `Asleep` about 2 minutes after it stops |
| Mood, Personality, Mode | sensor | Mode shows `Sleeping` when Furby isn't advertising |
| Fullness, Wellness, Excitement, Tiredness, Displeasure | sensor (%) | |
| Hungry, Sick | binary sensor | |
| Active states | sensor | e.g. `Chewing` |
| Antenna | light (RGB) | Shows the last colour set from HA; Furby can't report it |
| Feed (fullness), Heal (wellness) | number | |
| Refresh status | button | Polls now |
| Signal strength, Advertisement, Last status, Reachable, Battery | diagnostic | |

## How it works
When Furby wakes, and every few minutes while it stays awake, the integration connects briefly, asks for status (`20 06`) and mode (`20 0c`), then disconnects. It never holds a connection open: that would keep Furby awake, drain its batteries and tie up a proxy slot.

> [!Note]
> **Battery:** Furby Connect has no standard Bluetooth battery service. The Battery diagnostic shows a raw power report when Furby sends one. There's no reliable percentage yet, so low-battery alerts aren't possible for now.

## Troubleshooting
Turn on debug logging, reproduce the problem, and attach the `furby_connect` lines (and the integration's **Download diagnostics**) to an [issue](https://github.com/zubir2k/homeassistant-furbyconnect/issues).

```yaml
logger:
  default: warning
  logs:
    custom_components.furby_connect: debug
```

- **Awake but polls fail:** Furby is dozing, or your proxy is out of free connection slots. The integration backs off and retries on its own.
- **Not discovered:** wake Furby and check that your proxy is connectable (`active: true`).

## Credits
- [Jeija/bluefluff](https://github.com/Jeija/bluefluff) for the original Furby Connect Bluetooth research.

## Disclaimer
Furby and Furby Connect are trademarks of Hasbro, Inc. This project is not affiliated with, endorsed by, or sponsored by Hasbro. The icon and logo are original artwork.
