#!/usr/bin/env python3
"""Start the independent Nothing shell with its own weather/font configuration."""
import json
import os
from pathlib import Path
import shutil
import sys


def main():
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    settings_path = config / "nothing-niri/settings.json"
    try:
        settings = json.loads(settings_path.read_text())
        if not isinstance(settings, dict):
            raise ValueError('expected a JSON object')
    except (OSError, ValueError) as error:
        sys.exit(f"Cannot load Nothing settings: {settings_path}: {error}. Check that --apply completed successfully.")
    environment = os.environ.copy()
    location = settings.get("location", {})
    if not isinstance(location, dict):
        sys.exit(f"Invalid location in {settings_path}: expected a JSON object.")
    if location.get("latitude") is not None and location.get("longitude") is not None:
        environment["NOTHING_LATLON"] = f'{location["latitude"]},{location["longitude"]}'
    environment["NOTHING_CITY"] = location.get("city", "")
    if settings.get("dotFontPath"):
        environment["NOTHING_DOT_FONT_PATH"] = settings["dotFontPath"]
        environment["NOTHING_NDOT_FAMILY"] = settings.get("dotFontFamily", "Ndot 57")
    executable = shutil.which("qs") or shutil.which("quickshell")
    if not executable:
        sys.exit("Quickshell is missing. Install the quickshell package first.")
    environment["QT_QUICK_CONTROLS_STYLE"] = "Basic"
    os.execve(executable, [executable, "-p", str(Path(__file__).resolve().parent)], environment)


if __name__ == "__main__":
    main()
