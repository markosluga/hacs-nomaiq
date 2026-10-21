# Technical documentation

This page explains how the Noma IQ integration works, which devices it supports, and how the tools in the repository fit in. For setup and for helping add a device, see the [README](../README.md) and [capturing device states](capturing-device-states.md).

## How it connects

Noma IQ devices are cloud devices on the Ayla IoT platform. The integration signs in to Ayla with the username and password from the Noma IQ app, then polls the cloud for device properties and writes changes back to it.

- **Library:** `ayla_iot_unofficial` 1.5.0, pinned in `manifest.json`.
- **Client ID and secret:** the app's credentials, in `custom_components/nomaiq/const.py`. These aren't user secrets, but they are hardcoded.
- **Config flow:** asks for username and password, checks them by signing in, and stores them in the config entry. Reauthentication uses the same form.
- **Polling:** the coordinator (`coordinator.py`) refreshes every 30 seconds. While a cover is opening or closing, it speeds up to every 2 seconds until the door reaches a stable state.

## Files

| File | Purpose |
|---|---|
| `__init__.py` | Sets up the config entry, registers the platforms, and registers the `capture_state` service |
| `config_flow.py` | Credentials form and reauthentication |
| `coordinator.py` | Polls devices, tracks devices in transition, and holds captured states |
| `cover.py` | Garage door (`oem_model` `gdo`) |
| `light.py` | Light on a device that has `light_control` and `light_name` |
| `humidifier.py` | Dehumidifier (`oem_model` `dehum`): power, target humidity, current humidity, mode |
| `select.py` | Dehumidifier fan speed |
| `diagnostics.py` | Diagnostics download |
| `services.yaml` | Describes the `capture_state` service in the Home Assistant UI |

## How devices are matched

On setup, each device returned by the cloud is checked against the platforms:

- `gdo` becomes a garage door cover.
- A device with `light_control` and `light_name` properties becomes a light.
- `dehum` becomes a humidifier and a fan speed select.

Devices that match none of these are ignored. Their properties still appear in the diagnostics download.

## Dehumidifier

The dehumidifier stores its settings as raw strings, which don't match the labels in the app. The mapping lives in `humidifier.py` and `select.py`.

| Entity | Property | Read | Write | Values |
|---|---|---|---|---|
| Humidifier (on/off) | `power` | yes | yes | 1 = on, 0 = off |
| Humidifier (target) | `humidity` | yes | yes | 30–80, step 5 |
| Humidifier (current) | `indoor_humidity` | yes | no | Measured value |
| Humidifier (mode) | `mode` | yes | yes | manual ↔ `Normal`, auto dry ↔ `Auto`, continuous ↔ `Persistent` |
| Select (fan speed) | `fan_speed` | yes | yes | auto ↔ `Smart`, slow ↔ `Low`, fast ↔ `High` |

Target humidity values are rounded to the nearest 5 and clamped to 30–80 before they're sent.

**Verified:** writing `humidity` through the cloud, confirmed by reading it back.

**Not verified:** writing `mode` and `fan_speed` through the cloud. The mappings above come from changes made in the app, not from the integration.

**Unknown:** whether `humidity` takes effect in every mode.

## Diagnostics and captured states

The `capture_state` service fetches fresh values for one device and stores them with a timestamp and a description. It's available under **Developer Tools > Actions** as **Noma IQ: Capture device state**.

Captured states are kept in memory on the coordinator. A restart clears them.

Downloading diagnostics (**Settings > Devices & services > Noma IQ > Download diagnostics**) returns:

- `devices`: each device's name, `oem_model`, model number, and property values.
- `captured_states`: every capture so far.

The download excludes the username, password, and serial numbers. Device names are included, so they should be checked before sharing.

## Tools

Scripts in `tools/` run outside Home Assistant and need `NOMAIQ_USER` and `NOMAIQ_PASS` set in the environment. They read the client ID and secret from `const.py`.

- `discover_devices.py`: signs in, lists devices, and prints each device's properties. It only reads data.
- `write_test.py`: changes the target humidity on the dehumidifier, reads it back, and restores the original value. It asks for confirmation first, and it changes the real device.

## Adding support for a device

1. Capture states as described in [capturing device states](capturing-device-states.md).
2. Find the device's `oem_model` and property names in the diagnostics file.
3. Add a platform for it, or extend an existing one, and register it in `_PLATFORMS` in `__init__.py`.
4. Add the value mapping for any labels that differ from the stored values.
5. Test the writes on the device before relying on them.

## Limitations

- The Ayla library is unofficial and may change without notice.
- Writes are confirmed only for `humidity`.
- Mode and fan speed mappings come from the app and haven't been checked against the cloud.
- Captured states are lost on restart.
- The integration hasn't been tested with more than one dehumidifier.
