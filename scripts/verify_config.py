#!/usr/bin/env python3
"""Verify user and project scope config files for safety-net."""

import sys
from pathlib import Path

try:
    from scripts.safety_net_impl.config import ValidationResult, validate_config_file
except ImportError:  # When executed as a script from the scripts/ directory.
    from safety_net_impl.config import (  # type: ignore[no-redef]
        ValidationResult,
        validate_config_file,
    )

_USER_CONFIG = Path.home() / ".cc-safety-net" / "config.json"
_PROJECT_CONFIG = Path(".safety-net.json")

_HEADER = "Safety Net Config"
_SEPARATOR = "═" * len(_HEADER)


def _print_header() -> None:
    print(_HEADER)
    print(_SEPARATOR)


def _print_valid_config(scope: str, path: Path, result: ValidationResult) -> None:
    print(f"\n✓ {scope} config: {path}")
    if result.rule_names:
        print("  Rules:")
        for i, name in enumerate(result.rule_names, 1):
            print(f"    {i}. {name}")
    else:
        print("  Rules: (none)")


def _print_invalid_config(scope: str, path: Path, errors: list[str]) -> None:
    print(f"\n✗ {scope} config: {path}", file=sys.stderr)
    print("  Errors:", file=sys.stderr)
    error_num = 1
    for error in errors:
        for part in error.split("; "):
            print(f"    {error_num}. {part}", file=sys.stderr)
            error_num += 1


def main() -> int:
    """Verify config files and print results."""
    has_errors = False
    configs_checked: list[tuple[str, Path, ValidationResult]] = []

    _print_header()

    if _USER_CONFIG.exists():
        result = validate_config_file(str(_USER_CONFIG))
        configs_checked.append(("User", _USER_CONFIG, result))
        if result.errors:
            has_errors = True

    if _PROJECT_CONFIG.exists():
        result = validate_config_file(str(_PROJECT_CONFIG))
        configs_checked.append(("Project", _PROJECT_CONFIG.resolve(), result))
        if result.errors:
            has_errors = True

    if not configs_checked:
        print("\nNo config files found. Using built-in rules only.")
        return 0

    for scope, path, result in configs_checked:
        if result.errors:
            _print_invalid_config(scope, path, result.errors)
        else:
            _print_valid_config(scope, path, result)

    if has_errors:
        print("\nConfig validation failed.", file=sys.stderr)
        return 1

    print("\nAll configs valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
