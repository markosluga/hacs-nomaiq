# Changelog

All notable changes to this project are documented here. This project follows [Semantic Versioning](https://semver.org/): fixes are patch releases, new capabilities of existing features are minor releases, and entirely new features are major releases.

## [0.1.1] - 2026-10-21

### Added

- Dehumidifier support (Ayla model `dehum`):
  - `humidifier` entity with power on/off, target humidity (30–80%, 5% steps), current humidity reading, and operating modes (manual, auto dry, continuous).
  - `select` entity for fan speed (auto, slow, fast).
- Capture service `nomaiq.capture_state`: select a device, describe a change you made in the app, and record the cloud state for it. Captures are kept until Home Assistant restarts.
- Diagnostics download for the integration, listing every device's properties and all captured states. Credentials and serial numbers are excluded.
- GitHub issue template "Add device support" and a guide at `docs/capturing-device-states.md`.
- Development tools in `tools/`:
  - `discover_devices.py`: read-only listing of devices and their properties.
  - `write_test.py`: changes the target humidity, reads it back from the cloud, and restores the original value.
- Technical documentation at `docs/technical.md`.

### Notes

- Target humidity writes are verified against the cloud. Mode and fan speed writes through the API are not yet verified.
- Entities were confirmed to load in Home Assistant under NomaIQ (`humidifier.trailer_dehumidifier`, `select.trailer_dehumidifier`).
