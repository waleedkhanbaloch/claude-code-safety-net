"""Tests for safety-net audit logging."""

import io
import json
from pathlib import Path
from unittest import mock

from scripts import safety_net

from . import TempDirTestCase


class AuditLogTestCase(TempDirTestCase):
    """Base test case with helpers for testing audit logging."""

    def _run_guard_with_session(
        self,
        command: str,
        *,
        session_id: str | None = None,
        cwd: str | None = None,
    ) -> dict | None:
        """Run the guard with session_id and return parsed output or None."""
        input_data: dict = {"tool_name": "Bash", "tool_input": {"command": command}}
        if session_id is not None:
            input_data["session_id"] = session_id
        if cwd is not None:
            input_data["cwd"] = cwd

        with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
            with mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                with mock.patch("pathlib.Path.home", return_value=self.tmpdir):
                    result = safety_net.main()
                    output = mock_stdout.getvalue()

        self.assertEqual(result, 0)
        if output.strip():
            parsed: dict = json.loads(output)
            return parsed
        return None

    def _get_log_file(self, session_id: str) -> Path:
        return self.tmpdir / ".cc-safety-net" / "logs" / f"{session_id}.jsonl"

    def _read_log_entries(self, session_id: str) -> list[dict]:
        log_file = self._get_log_file(session_id)
        if not log_file.exists():
            return []
        entries = []
        with log_file.open() as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries


class AuditLogTests(AuditLogTestCase):
    def test_denied_command_creates_log_entry(self) -> None:
        session_id = "test-session-123"
        self._run_guard_with_session("git reset --hard", session_id=session_id)

        entries = self._read_log_entries(session_id)
        self.assertEqual(len(entries), 1)
        self.assertIn("git reset --hard", entries[0]["command"])

    def test_allowed_command_no_log(self) -> None:
        session_id = "test-session-456"
        self._run_guard_with_session("ls -la", session_id=session_id)

        entries = self._read_log_entries(session_id)
        self.assertEqual(len(entries), 0)

    def test_log_format_fields(self) -> None:
        session_id = "test-session-789"
        self._run_guard_with_session(
            "git reset --hard",
            session_id=session_id,
            cwd="/home/user/project",
        )

        entries = self._read_log_entries(session_id)
        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertIn("ts", entry)
        self.assertIn("command", entry)
        self.assertIn("segment", entry)
        self.assertIn("reason", entry)
        self.assertIn("cwd", entry)

        self.assertEqual(entry["cwd"], "/home/user/project")
        self.assertIn("git reset --hard", entry["reason"])

    def test_log_redacts_secrets(self) -> None:
        session_id = "test-session-redact"
        self._run_guard_with_session(
            "TOKEN=secret123 git reset --hard",
            session_id=session_id,
        )

        entries = self._read_log_entries(session_id)
        self.assertEqual(len(entries), 1)
        entry = entries[0]

        self.assertNotIn("secret123", entry["command"])
        self.assertIn("<redacted>", entry["command"])

    def test_missing_session_id_no_log(self) -> None:
        self._run_guard_with_session("git reset --hard", session_id=None)

        logs_dir = self.tmpdir / ".cc-safety-net" / "logs"
        if logs_dir.exists():
            log_files = list(logs_dir.iterdir())
            self.assertEqual(len(log_files), 0)

    def test_multiple_denials_append(self) -> None:
        session_id = "test-session-multi"
        self._run_guard_with_session("git reset --hard", session_id=session_id)
        self._run_guard_with_session("git clean -f", session_id=session_id)
        self._run_guard_with_session("rm -rf /", session_id=session_id)

        entries = self._read_log_entries(session_id)
        self.assertEqual(len(entries), 3)

        self.assertIn("git reset --hard", entries[0]["command"])
        self.assertIn("git clean -f", entries[1]["command"])
        self.assertIn("rm -rf /", entries[2]["command"])

    def test_session_id_path_traversal_does_not_escape_logs_dir(self) -> None:
        session_id = "../../outside"
        self._run_guard_with_session("git reset --hard", session_id=session_id)

        self.assertFalse((self.tmpdir / "outside.jsonl").exists())

        logs_dir = self.tmpdir / ".cc-safety-net" / "logs"
        log_files = list(logs_dir.glob("*.jsonl"))
        self.assertEqual(len(log_files), 1)
        self.assertEqual(log_files[0].parent, logs_dir)

    def test_session_id_absolute_path_does_not_escape_logs_dir(self) -> None:
        escaped = self.tmpdir / "escaped"
        session_id = str(escaped)
        self._run_guard_with_session("git reset --hard", session_id=session_id)

        self.assertFalse((self.tmpdir / "escaped.jsonl").exists())

        logs_dir = self.tmpdir / ".cc-safety-net" / "logs"
        log_files = list(logs_dir.glob("*.jsonl"))
        self.assertEqual(len(log_files), 1)
        self.assertEqual(log_files[0].parent, logs_dir)

    def test_cwd_null_when_missing(self) -> None:
        session_id = "test-session-no-cwd"
        self._run_guard_with_session(
            "git reset --hard", session_id=session_id, cwd=None
        )

        entries = self._read_log_entries(session_id)
        self.assertEqual(len(entries), 1)
        self.assertIsNone(entries[0]["cwd"])

    def test_invalid_config_uses_builtin_only_no_log(self) -> None:
        session_id = "test-session-config-error"
        config_dir = self.tmpdir / "project"
        config_dir.mkdir()
        config_file = config_dir / ".safety-net.json"
        config_file.write_text('{"version": 999}', encoding="utf-8")

        self._run_guard_with_session(
            "echo hello",
            session_id=session_id,
            cwd=str(config_dir),
        )

        entries = self._read_log_entries(session_id)
        self.assertEqual(len(entries), 0)
