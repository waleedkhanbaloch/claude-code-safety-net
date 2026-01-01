"""Integration tests for custom rules feature."""

import json

from scripts.safety_net_impl.hook import _reset_config_cache

from .safety_net_test_base import SafetyNetTestCase


class CustomRulesIntegrationTests(SafetyNetTestCase):
    """End-to-end tests for custom rules."""

    def _write_config(self, data: dict) -> str:
        """Write config to temp directory and return path."""
        path = self.tmpdir / ".safety-net.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def test_custom_rule_blocks_command(self) -> None:
        """Custom rule blocks matching command."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-git-add-all",
                        "command": "git",
                        "subcommand": "add",
                        "block_args": ["-A", "--all", "."],
                        "reason": "Use specific files.",
                    }
                ],
            }
        )
        self._assert_blocked(
            "git add -A",
            "[block-git-add-all] Use specific files.",
            cwd=str(self.tmpdir),
        )

    def test_custom_rule_blocks_with_dot(self) -> None:
        """Custom rule blocks git add ."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-git-add-all",
                        "command": "git",
                        "subcommand": "add",
                        "block_args": ["-A", "--all", "."],
                        "reason": "Use specific files.",
                    }
                ],
            }
        )
        self._assert_blocked(
            "git add .",
            "[block-git-add-all]",
            cwd=str(self.tmpdir),
        )

    def test_custom_rule_allows_non_matching_command(self) -> None:
        """Custom rule does not block non-matching commands."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-git-add-all",
                        "command": "git",
                        "subcommand": "add",
                        "block_args": ["-A"],
                        "reason": "Use specific files.",
                    }
                ],
            }
        )
        self._assert_allowed("git add file.txt", cwd=str(self.tmpdir))

    def test_builtin_rule_takes_precedence(self) -> None:
        """Built-in rules block before custom rules are checked."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "custom-reset-rule",
                        "command": "git",
                        "subcommand": "reset",
                        "block_args": ["--soft"],
                        "reason": "Custom reason.",
                    }
                ],
            }
        )
        # Built-in rule blocks git reset --hard, not custom rule
        self._assert_blocked(
            "git reset --hard",
            "git reset --hard destroys",
            cwd=str(self.tmpdir),
        )

    def test_multiple_custom_rules(self) -> None:
        """Multiple custom rules - any match triggers block."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-git-add-all",
                        "command": "git",
                        "subcommand": "add",
                        "block_args": ["-A"],
                        "reason": "No blanket add.",
                    },
                    {
                        "name": "block-npm-global",
                        "command": "npm",
                        "subcommand": "install",
                        "block_args": ["-g"],
                        "reason": "No global installs.",
                    },
                ],
            }
        )
        self._assert_blocked("git add -A", "[block-git-add-all]", cwd=str(self.tmpdir))
        _reset_config_cache()
        self._assert_blocked(
            "npm install -g pkg",
            "[block-npm-global]",
            cwd=str(self.tmpdir),
        )

    def test_rule_without_subcommand_matches_any(self) -> None:
        """Rule without subcommand matches any invocation."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-npm-global",
                        "command": "npm",
                        "block_args": ["-g", "--global"],
                        "reason": "No global.",
                    }
                ],
            }
        )
        self._assert_blocked(
            "npm install -g pkg", "[block-npm-global]", cwd=str(self.tmpdir)
        )
        _reset_config_cache()
        self._assert_blocked(
            "npm uninstall -g pkg", "[block-npm-global]", cwd=str(self.tmpdir)
        )

    def test_no_config_uses_builtin_only(self) -> None:
        """When no config exists, only built-in rules apply."""
        # tmpdir has no config file
        self._assert_blocked(
            "git reset --hard",
            "git reset --hard destroys",
            cwd=str(self.tmpdir),
        )
        self._assert_allowed("git add -A", cwd=str(self.tmpdir))

    def test_empty_rules_list_uses_builtin_only(self) -> None:
        """Config with empty rules list uses only built-in rules."""
        self._write_config({"version": 1, "rules": []})
        self._assert_blocked(
            "git reset --hard",
            "git reset --hard destroys",
            cwd=str(self.tmpdir),
        )
        self._assert_allowed("git add -A", cwd=str(self.tmpdir))

    def test_invalid_config_uses_builtin_only(self) -> None:
        """Invalid config file uses built-in rules only (silent fallback)."""
        path = self.tmpdir / ".safety-net.json"
        path.write_text('{"version": 2}', encoding="utf-8")

        self._assert_blocked(
            "git reset --hard",
            "git reset --hard destroys",
            cwd=str(self.tmpdir),
        )
        _reset_config_cache()
        self._assert_allowed("echo hello", cwd=str(self.tmpdir))

    def test_custom_rules_not_applied_to_embedded_commands(self) -> None:
        """Custom rules don't apply to commands in bash -c wrappers."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-git-add-all",
                        "command": "git",
                        "subcommand": "add",
                        "block_args": ["-A"],
                        "reason": "No blanket add.",
                    }
                ],
            }
        )
        # Direct command is blocked
        self._assert_blocked("git add -A", "[block-git-add-all]", cwd=str(self.tmpdir))
        _reset_config_cache()
        # Embedded in bash -c is NOT blocked by custom rule (per spec)
        self._assert_allowed("bash -c 'git add -A'", cwd=str(self.tmpdir))

    def test_custom_rules_apply_to_xargs(self) -> None:
        """Custom rules are checked for xargs commands."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-xargs-grep",
                        "command": "xargs",
                        "block_args": ["grep"],
                        "reason": "Use ripgrep instead.",
                    }
                ],
            }
        )
        self._assert_blocked(
            "find . | xargs grep pattern",
            "[block-xargs-grep]",
            cwd=str(self.tmpdir),
        )

    def test_custom_rules_apply_to_parallel(self) -> None:
        """Custom rules are checked for parallel commands."""
        self._write_config(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "block-parallel-curl",
                        "command": "parallel",
                        "block_args": ["curl"],
                        "reason": "No parallel curl.",
                    }
                ],
            }
        )
        self._assert_blocked(
            "parallel curl ::: url1 url2",
            "[block-parallel-curl]",
            cwd=str(self.tmpdir),
        )
