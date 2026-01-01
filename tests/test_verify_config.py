"""Tests for verify_config.py script."""

import json
from io import StringIO
from pathlib import Path
from unittest import mock

import scripts.verify_config as verify_config_module
from scripts.verify_config import main

from . import TempDirTestCase


class TestMainNoConfigs(TempDirTestCase):
    """Tests for main() when no config files exist."""

    def setUp(self) -> None:
        super().setUp()
        self._original_cwd = Path.cwd()
        import os

        os.chdir(self.tmpdir)
        self._user_config_path = self.tmpdir / ".cc-safety-net" / "config.json"
        self._patcher = mock.patch.object(
            verify_config_module, "_USER_CONFIG", self._user_config_path
        )
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        import os

        os.chdir(self._original_cwd)
        super().tearDown()

    def test_no_configs_returns_zero(self) -> None:
        result = main()
        self.assertEqual(result, 0)

    def test_no_configs_prints_header(self) -> None:
        stdout = StringIO()
        with mock.patch(
            "builtins.print",
            side_effect=lambda *a, **_: stdout.write(str(a[0]) + "\n") if a else None,
        ):
            main()
        output = stdout.getvalue()
        self.assertIn("Safety Net Config", output)
        self.assertIn("═", output)

    def test_no_configs_prints_message(self) -> None:
        stdout = StringIO()
        with mock.patch(
            "builtins.print",
            side_effect=lambda *a, **_: stdout.write(str(a[0]) + "\n") if a else None,
        ):
            main()
        output = stdout.getvalue()
        self.assertIn("No config files found", output)
        self.assertIn("Using built-in rules only", output)


class TestMainValidConfigs(TempDirTestCase):
    """Tests for main() with valid config files."""

    def _write_user_config(self, data: dict) -> None:
        self._user_config_path.parent.mkdir(parents=True, exist_ok=True)
        self._user_config_path.write_text(json.dumps(data), encoding="utf-8")

    def _write_project_config(self, data: dict) -> None:
        path = Path(".safety-net.json")
        path.write_text(json.dumps(data), encoding="utf-8")

    def _capture_output(self) -> str:
        stdout = StringIO()
        with mock.patch(
            "builtins.print",
            side_effect=lambda *a, **_: stdout.write(str(a[0]) + "\n") if a else None,
        ):
            main()
        return stdout.getvalue()

    def setUp(self) -> None:
        super().setUp()
        self._original_cwd = Path.cwd()
        import os

        os.chdir(self.tmpdir)
        self._user_config_path = self.tmpdir / ".cc-safety-net" / "config.json"
        self._patcher = mock.patch.object(
            verify_config_module, "_USER_CONFIG", self._user_config_path
        )
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        import os

        os.chdir(self._original_cwd)
        super().tearDown()

    def test_user_config_only_returns_zero(self) -> None:
        self._write_user_config({"version": 1})
        result = main()
        self.assertEqual(result, 0)

    def test_user_config_prints_checkmark(self) -> None:
        self._write_user_config({"version": 1})
        output = self._capture_output()
        self.assertIn("✓ User config:", output)

    def test_user_config_shows_rules_none(self) -> None:
        self._write_user_config({"version": 1})
        output = self._capture_output()
        self.assertIn("Rules: (none)", output)

    def test_user_config_with_rules_shows_numbered_list(self) -> None:
        self._write_user_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-foo",
                        "command": "foo",
                        "block_args": ["-x"],
                        "reason": "Blocked",
                    },
                    {
                        "name": "block-bar",
                        "command": "bar",
                        "block_args": ["-y"],
                        "reason": "Blocked",
                    },
                ],
            }
        )
        output = self._capture_output()
        self.assertIn("Rules:", output)
        self.assertIn("1. block-foo", output)
        self.assertIn("2. block-bar", output)

    def test_project_config_only_returns_zero(self) -> None:
        self._write_project_config({"version": 1})
        result = main()
        self.assertEqual(result, 0)

    def test_project_config_prints_checkmark(self) -> None:
        self._write_project_config({"version": 1})
        output = self._capture_output()
        self.assertIn("✓ Project config:", output)

    def test_both_configs_returns_zero(self) -> None:
        self._write_user_config({"version": 1})
        self._write_project_config({"version": 1})
        result = main()
        self.assertEqual(result, 0)

    def test_both_configs_prints_both_checkmarks(self) -> None:
        self._write_user_config({"version": 1})
        self._write_project_config({"version": 1})
        output = self._capture_output()
        self.assertIn("✓ User config:", output)
        self.assertIn("✓ Project config:", output)

    def test_valid_config_prints_success_message(self) -> None:
        self._write_project_config({"version": 1})
        output = self._capture_output()
        self.assertIn("All configs valid.", output)


class TestMainInvalidConfigs(TempDirTestCase):
    """Tests for main() with invalid config files."""

    def _write_user_config(self, content: str) -> None:
        self._user_config_path.parent.mkdir(parents=True, exist_ok=True)
        self._user_config_path.write_text(content, encoding="utf-8")

    def _write_project_config(self, content: str) -> None:
        path = Path(".safety-net.json")
        path.write_text(content, encoding="utf-8")

    def _capture_stderr(self) -> str:
        stderr = StringIO()
        with mock.patch("sys.stderr", stderr):
            main()
        return stderr.getvalue()

    def setUp(self) -> None:
        super().setUp()
        self._original_cwd = Path.cwd()
        import os

        os.chdir(self.tmpdir)
        self._user_config_path = self.tmpdir / ".cc-safety-net" / "config.json"
        self._patcher = mock.patch.object(
            verify_config_module, "_USER_CONFIG", self._user_config_path
        )
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        import os

        os.chdir(self._original_cwd)
        super().tearDown()

    def test_invalid_user_config_returns_one(self) -> None:
        self._write_user_config('{"version": 2}')
        result = main()
        self.assertEqual(result, 1)

    def test_invalid_user_config_prints_x_mark(self) -> None:
        self._write_user_config('{"version": 2}')
        output = self._capture_stderr()
        self.assertIn("✗ User config:", output)

    def test_invalid_config_shows_numbered_errors(self) -> None:
        self._write_user_config('{"version": 2}')
        output = self._capture_stderr()
        self.assertIn("Errors:", output)
        self.assertIn("1.", output)
        self.assertIn("unsupported version", output)

    def test_invalid_project_config_returns_one(self) -> None:
        self._write_project_config('{"rules": []}')
        result = main()
        self.assertEqual(result, 1)

    def test_invalid_project_config_prints_x_mark(self) -> None:
        self._write_project_config('{"rules": []}')
        output = self._capture_stderr()
        self.assertIn("✗ Project config:", output)

    def test_both_invalid_returns_one(self) -> None:
        self._write_user_config('{"version": 2}')
        self._write_project_config('{"rules": []}')
        result = main()
        self.assertEqual(result, 1)

    def test_both_invalid_prints_both_errors(self) -> None:
        self._write_user_config('{"version": 2}')
        self._write_project_config('{"rules": []}')
        output = self._capture_stderr()
        self.assertIn("✗ User config:", output)
        self.assertIn("✗ Project config:", output)

    def test_invalid_json_prints_error(self) -> None:
        self._write_project_config("{ not valid json }")
        output = self._capture_stderr()
        self.assertIn("✗ Project config:", output)

    def test_validation_failed_message(self) -> None:
        self._write_project_config('{"version": 2}')
        output = self._capture_stderr()
        self.assertIn("Config validation failed.", output)


class TestMainMixedValidity(TempDirTestCase):
    """Tests for main() with one valid and one invalid config."""

    def _write_user_config(self, content: str) -> None:
        self._user_config_path.parent.mkdir(parents=True, exist_ok=True)
        self._user_config_path.write_text(content, encoding="utf-8")

    def _write_project_config(self, content: str) -> None:
        path = Path(".safety-net.json")
        path.write_text(content, encoding="utf-8")

    def _capture_output(self) -> tuple[str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr):
            main()
        return stdout.getvalue(), stderr.getvalue()

    def setUp(self) -> None:
        super().setUp()
        self._original_cwd = Path.cwd()
        import os

        os.chdir(self.tmpdir)
        self._user_config_path = self.tmpdir / ".cc-safety-net" / "config.json"
        self._patcher = mock.patch.object(
            verify_config_module, "_USER_CONFIG", self._user_config_path
        )
        self._patcher.start()

    def tearDown(self) -> None:
        self._patcher.stop()
        import os

        os.chdir(self._original_cwd)
        super().tearDown()

    def test_valid_user_invalid_project_returns_one(self) -> None:
        self._write_user_config('{"version": 1}')
        self._write_project_config('{"version": 2}')
        result = main()
        self.assertEqual(result, 1)

    def test_valid_user_invalid_project_shows_both(self) -> None:
        self._write_user_config('{"version": 1}')
        self._write_project_config('{"version": 2}')
        stdout, stderr = self._capture_output()
        self.assertIn("✓ User config:", stdout)
        self.assertIn("✗ Project config:", stderr)

    def test_invalid_user_valid_project_returns_one(self) -> None:
        self._write_user_config('{"version": 2}')
        self._write_project_config('{"version": 1}')
        result = main()
        self.assertEqual(result, 1)

    def test_invalid_user_valid_project_shows_both(self) -> None:
        self._write_user_config('{"version": 2}')
        self._write_project_config('{"version": 1}')
        stdout, stderr = self._capture_output()
        self.assertIn("✗ User config:", stderr)
        self.assertIn("✓ Project config:", stdout)
