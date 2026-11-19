#!/usr/bin/env python3
"""Verify that built APKs contain the preconfigured server URL in their DEX bytecode."""

import os
import sys
import zipfile
from pathlib import Path

EXPECTED_URL = os.environ.get("SERVER_URL", "https://book.lulospi.party").strip().encode("utf-8")


def verify_apk(apk_path: Path) -> None:
    if not apk_path.is_file():
        sys.stderr.write(f"ERROR: APK not found: {apk_path}\n")
        sys.exit(1)

    found = False
    with zipfile.ZipFile(apk_path, "r") as zf:
        dex_names = [n for n in zf.namelist() if n.startswith("classes") and n.endswith(".dex")]
        if not dex_names:
            sys.stderr.write(f"ERROR: No DEX files found in {apk_path}\n")
            sys.exit(1)
        for name in dex_names:
            if EXPECTED_URL in zf.read(name):
                found = True
                break

    if not found:
        sys.stderr.write(
            f"ERROR: {EXPECTED_URL.decode()} not found in DEX files of {apk_path}\n"
        )
        sys.exit(1)

    print(f"OK: Verified {EXPECTED_URL.decode()} in {apk_path.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: verify_apk.py <apk1> [apk2 ...]\n")
        sys.exit(2)
    for arg in sys.argv[1:]:
        verify_apk(Path(arg))
