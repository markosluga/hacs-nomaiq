"""List Noma IQ devices and their properties for development.

Read-only: signs in, fetches device list and property values, prints them,
and signs out. Credentials come from environment variables so they never
touch the repo:

    $env:NOMAIQ_USER = "you@example.com"
    $env:NOMAIQ_PASS = "..."
    python tools/discover_devices.py > devices.txt

Serial numbers are masked in the output. Review devices.txt before sharing it.
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


def _read_const(name: str) -> str:
    """Read a string constant from const.py without importing the HA package."""
    match = re.search(rf'^{name}\s*=\s*"([^"]+)"', CONST_FILE.read_text(), re.M)
    if not match:
        sys.exit(f"{name} not found in {CONST_FILE}")
    return match.group(1)


def _mask(value: str) -> str:
    """Hide all but the last 4 characters of an identifier."""
    return f"***{value[-4:]}" if len(value) > 4 else "***"


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
            print(f"Found {len(devices)} device(s)\n")
            for device in devices:
                await device.async_update()
                print("=" * 70)
                print(f"name:          {device.name}")
                print(f"oem_model:     {device.oem_model_number}")
                print(f"model_number:  {device.device_model_number}")
                print(f"serial:        {_mask(device.serial_number)}")
                print("properties:")
                for prop_name, prop in device.properties_full.items():
                    print(
                        f"  - {prop_name}"
                        f" | display={prop.get('display_name')!r}"
                        f" | type={prop.get('base_type')}"
                        f" | read_only={prop.get('read_only')}"
                        f" | value={prop.get('value')!r}"
                    )
                print()
        finally:
            await api.async_sign_out()


if __name__ == "__main__":
    asyncio.run(main())
