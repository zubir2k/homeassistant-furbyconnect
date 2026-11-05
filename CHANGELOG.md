# Changelog

## v0.1.6

First public release. Requires Home Assistant 2026.3 or newer.

### Added
- Diagnostics (serial number redacted).
- Malay translation (`ms.json`) and `strings.json`.
- Tests for the protocol decoder (pytest-homeassistant-custom-component).
- hassfest and HACS validation workflows.

### Changed
- New original icon and logo; no Hasbro artwork.
- Repository renamed to `homeassistant-furbyconnect`.

## v0.1.5

### Added
- Probes Furby's control channel for a power report (`Battery` diagnostic, `power_report_raw` attribute).
- Model, firmware, hardware and serial from Device Information go into the device registry.

### Fixed
- Data writes use write-without-response, as Furby expects.
- Mode shows `Sleeping` when Furby isn't advertising, instead of a stale `AppMain`.

## v0.1.4

### Added
- Diagnostic Battery sensor (standard `0x2A19`; later confirmed absent on Furby).
- GATT service dump at debug level.

## v0.1.3

### Changed
- Awake is passive, from advertisement recency (Awake / Asleep).
- Polls as soon as Furby wakes (60 s cooldown) and never while it sleeps.

### Added
- Reachable diagnostic binary sensor and `icons.json`.

## v0.1.2

### Fixed
- Status packet layout (states offset, MAC byte order).

### Added
- Advertisement diagnostic sensor. Controls stay available while Furby sleeps.

## v0.1.1

### Changed
- Fewer connection attempts, exponential backoff, keeps the last values when a poll fails.

### Added
- Diagnostics sensors: failures, last error and success, proxy, RSSI, Last status.

## v0.1.0
- Initial version.
