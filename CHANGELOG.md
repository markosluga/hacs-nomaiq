# Changelog

All notable changes to this project are documented here. This project follows [Semantic Versioning](https://semver.org/): fixes are patch releases, new capabilities of existing features are minor releases, and entirely new features are major releases.

## [0.1.0] - 2026-10-21

### Added

- Dehumidifier support (Ayla model `dehum`):
  - `humidifier` entity with power on/off, target humidity (30–80%, 5% steps), current humidity reading, and operating modes (manual, auto dry, continuous).
  - `select` entity for fan speed (auto, slow, fast).
- Development tools in `tools/`:
  - `discover_devices.py`: read-only listing of devices and their properties.
  - `write_test.py`: changes the target humidity, reads it back from the cloud, and restores the original value.

### Notes

- Mode and fan speed writes through the API are not yet verified. Target humidity writes are verified.
