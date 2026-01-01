#!/usr/bin/env python3
"""Verify user and project scope config files for safety-net."""

import sys
from pathlib import Path

try:
    from scripts.safety_net_impl.config import validate_config_file
except ImportError:  # When executed as a script from the scripts/ directory.
    from safety_net_impl.config import validate_config_file  # type: ignore[no-redef]

_USER_CONFIG = Path.home() / ".cc-safety-net" / "config.json"
_PROJECT_CONFIG = Path(".safety-net.json")


def _print_errors(scope: str, path: Path, errors: list[str]) -> None:
    """Print detailed error messages for a config file."""
    print(f"\n{scope} config: {path}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    for error in errors:
        for part in error.split("; "):
            print(f"  ✗ {part}", file=sys.stderr)


def main() -> int:
    """Verify config files and print results."""
    has_errors = False
    configs_found = 0

    if _USER_CONFIG.exists():
        configs_found += 1
        errors = validate_config_file(str(_USER_CONFIG))
        if errors:
            has_errors = True
            _print_errors("User", _USER_CONFIG, errors)

    if _PROJECT_CONFIG.exists():
        configs_found += 1
        errors = validate_config_file(str(_PROJECT_CONFIG))
        if errors:
            has_errors = True
            _print_errors("Project", _PROJECT_CONFIG.resolve(), errors)

    if has_errors:
        print("\nConfig validation failed.", file=sys.stderr)
        return 1

    if configs_found == 0:
        print("No config files found. Using built-in rules only.")
    else:
        scopes = []
        if _USER_CONFIG.exists():
            scopes.append("user")
        if _PROJECT_CONFIG.exists():
            scopes.append("project")
        print(f"Config OK ({', '.join(scopes)})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
