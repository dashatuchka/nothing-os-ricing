#!/usr/bin/env python3
"""Render a merged settings candidate without modifying the live shell."""
import argparse
import copy
import json
from pathlib import Path


def merge(current, overrides):
    result = copy.deepcopy(current)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("settings", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    preset = Path(__file__).resolve().parent.parent / "presets/serpantinum/nothing-monochrome.json"
    current = json.loads(args.settings.read_text())
    overrides = json.loads(preset.read_text())
    if not isinstance(current, dict):
        parser.error("settings must contain a JSON object")
    if args.output.resolve() == args.settings.resolve():
        parser.error("output must differ from the input settings")
    # Exclusive creation also protects an existing destination or symlink.
    with args.output.open("x") as handle:
        json.dump(merge(current, overrides), handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Candidate saved: {args.output}; live settings unchanged")


if __name__ == "__main__":
    main()
