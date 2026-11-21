#!/usr/bin/env python3
"""Patch Lagrange Reader AppCoordinator.kt to preconfigure the default BookOrbit server."""

import os
import re
import sys
from pathlib import Path

URL_RE = re.compile(r"\Ahttps?://[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?(:[0-9]{1,5})?(/[A-Za-z0-9._~!*'()%/+,;=:@-]*)?\Z")
NAME_RE = re.compile(r"\A[^\x00-\x1f\x7f\"]{1,64}\Z")


def validate_url(url: str) -> str:
    """Accept only https?://host[:port][/path] with no quotes, whitespace or control chars."""
    if not URL_RE.match(url):
        raise ValueError(f"Invalid SERVER_URL: {url!r}")
    return url


def validate_name(name: str) -> str:
    """Accept a 1-64 char display name without control characters (newlines) or double quotes."""
    if not NAME_RE.match(name):
        raise ValueError(f"Invalid SERVER_NAME: {name!r}")
    return name


def kotlin_escape(value: str) -> str:
    """Escape a value for use inside a Kotlin double-quoted string literal."""
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("$", "\\$")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


try:
    DEFAULT_URL = validate_url(os.environ.get("SERVER_URL", "https://book.karbono.es").strip())
    DEFAULT_NAME = validate_name(os.environ.get("SERVER_NAME", "BookOrbit").strip())
except ValueError as exc:
    sys.stderr.write(f"ERROR: {exc}\n")
    sys.exit(1)


def patch_app_coordinator(path: Path) -> None:
    raw = path.read_text(encoding="utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")

    pattern = re.compile(
        r"(            val serverUrl = \(serverSelectionModule\(\)\?\.getServerUrl\(\) \?: repository\.getServerUrl\(\)\)\n)"
        r"            if \(serverUrl\.isNullOrBlank\(\)\) \{\n"
        r"                _screen\.value = AppScreen\.ServerSetup\(\)\n"
        r"                return@launch\n"
        r"            \}\n"
    )

    replacement = (
        r"\1"
        f"            if (serverUrl.isNullOrBlank()) {{\n"
        f'                val defaultUrl = "{kotlin_escape(DEFAULT_URL)}"\n'
        f"                repository.setServerUrl(defaultUrl)\n"
        f"                serverProfileStore?.upsert(\n"
        f"                    ServerProfile(\n"
        f"                        id = serverProfileId(defaultUrl),\n"
        f"                        serverUrl = defaultUrl,\n"
        f"                        providerId = PROVIDER_BOOKORBIT,\n"
        f'                        displayName = "{kotlin_escape(DEFAULT_NAME)}",\n'
        f"                        lastUsedAtMillis = System.currentTimeMillis()\n"
        f"                    )\n"
        f"                )\n"
        f"                showLogin(\n"
        f'                    message = "",\n'
        f"                    destination = PostLoginDestination.Browser\n"
        f"                )\n"
        f"                return@launch\n"
        f"            }}\n"
    )

    patched, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        sys.stderr.write(
            f"ERROR: Could not find expected bootstrap() serverUrl block in {path} (matches={count}).\n"
            "Upstream AppCoordinator.kt likely changed; update scripts/patch_server.py.\n"
        )
        sys.exit(1)

    if kotlin_escape(DEFAULT_URL) not in patched:
        sys.stderr.write("ERROR: Patched file does not contain expected server URL.\n")
        sys.exit(1)

    path.write_text(patched.replace("\n", eol), encoding="utf-8")
    print(f"OK: Patched {path} with default server {DEFAULT_URL} ({DEFAULT_NAME})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: patch_server.py <path/to/AppCoordinator.kt>\n")
        sys.exit(2)
    patch_app_coordinator(Path(sys.argv[1]))
