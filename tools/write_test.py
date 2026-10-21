"""Write-test a single dehumidifier property through the Ayla cloud API.

Changes the target humidity to a different value, reads it back from the
cloud, then restores the original value. This DOES change the device.

Credentials come from environment variables:

    $env:NOMAIQ_USER = "you@example.com"
    $env:NOMAIQ_PASS = "..."
    python tools/write_test.py
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

import aiohttp
import ayla_iot_unofficial

CONST_FILE = Path(__file__).resolve().parent.parent / "custom_components" / "nomaiq" / "const.py"
PROPERTY = "humidity"
VALID_MIN, VALID_MAX, VALID_STEP = 30, 80, 5


def _read_const(name: str) -> str:
    """Read a string constant from const.py without importing the HA package."""
    match = re.search(rf'^{name}\s*=\s*"([^"]+)"', CONST_FILE.read_text(), re.M)
    if not match:
        sys.exit(f"{name} not found in {CONST_FILE}")
    return match.group(1)


def _pick_test_value(current: int) -> int:
    """Pick a valid value 5 steps away from the current one, staying in range."""
    candidate = current + 5 * VALID_STEP
    if candidate > VALID_MAX:
        candidate = current - 5 * VALID_STEP
    if not VALID_MIN <= candidate <= VALID_MAX:
        sys.exit(f"No valid test value available from current {current}")
    return candidate


async def _read_humidity(device) -> int:
    """Fetch fresh values from the cloud and return the target humidity."""
    await device.async_update()
    return device.get_property_value(PROPERTY)


async def main() -> None:
    username = os.environ.get("NOMAIQ_USER")
    password = os.environ.get("NOMAIQ_PASS")
    if not username or not password:
        sys.exit("Set NOMAIQ_USER and NOMAIQ_PASS environment variables first.")

    async with aiohttp.ClientSession() as session:
        api = ayla_iot_unofficial.new_ayla_api(
            username,
            password,
            _read_const("CLIENT_ID"),
            _read_const("CLIENT_SECRET"),
            session,
        )
        await api.async_sign_in()
        try:
            devices = await api.async_get_devices()
            dehums = [d for d in devices if d.oem_model_number == "dehum"]
            if len(dehums) != 1:
                sys.exit(f"Expected exactly one dehum device, found {len(dehums)}")
            device = dehums[0]

            original = await _read_humidity(device)
            test_value = _pick_test_value(original)
            print(f"Current cloud humidity target: {original}")
            print(f"Will set to {test_value}, read back, then restore {original}.")
            if input("Type 'yes' to change the device: ").strip().lower() != "yes":
                sys.exit("Aborted, no changes made.")

            try:
                await device.async_set_property_value(PROPERTY, test_value)
                readback = await _read_humidity(device)
                print(f"Read back after write: {readback}")
                print("Write OK" if readback == test_value else "MISMATCH: cloud did not confirm the new value")
            finally:
                await device.async_set_property_value(PROPERTY, original)
                restored = await _read_humidity(device)
                print(f"Restored to: {restored}" + ("" if restored == original else " (MISMATCH, check the app)"))
        finally:
            await api.async_sign_out()


if __name__ == "__main__":
    asyncio.run(main())
