"""Tests for custom rule matching logic."""

import unittest

from scripts.safety_net_impl.config import CustomRule
from scripts.safety_net_impl.rules_custom import check_custom_rules


class TestCustomRuleMatching(unittest.TestCase):
    """Tests for check_custom_rules function."""

    def test_basic_command_match(self) -> None:
        """Basic command + block_arg match."""
        rules = [
            CustomRule(
                name="block-git-add-all",
                command="git",
                subcommand="add",
                block_args=["-A", "--all"],
                reason="Use specific files.",
            )
        ]
        result = check_custom_rules(["git", "add", "-A"], rules)
        self.assertEqual(result, "[block-git-add-all] Use specific files.")

    def test_match_with_long_option(self) -> None:
        """Match with long option form."""
        rules = [
            CustomRule(
                name="block-git-add-all",
                command="git",
                subcommand="add",
                block_args=["-A", "--all"],
                reason="Use specific files.",
            )
        ]
        result = check_custom_rules(["git", "add", "--all"], rules)
        self.assertEqual(result, "[block-git-add-all] Use specific files.")

    def test_no_match_when_command_differs(self) -> None:
        """No match when command differs."""
        rules = [
            CustomRule(
                name="block-git-add-all",
                command="git",
                subcommand="add",
                block_args=["-A"],
                reason="test",
            )
        ]
        result = check_custom_rules(["npm", "add", "-A"], rules)
        self.assertIsNone(result)

    def test_no_match_when_subcommand_differs(self) -> None:
        """No match when subcommand differs."""
        rules = [
            CustomRule(
                name="block-git-add-all",
                command="git",
                subcommand="add",
                block_args=["-A"],
                reason="test",
            )
        ]
        result = check_custom_rules(["git", "commit", "-A"], rules)
        self.assertIsNone(result)

    def test_no_match_when_no_blocked_args_present(self) -> None:
        """No match when no blocked args present."""
        rules = [
            CustomRule(
                name="block-git-add-all",
                command="git",
                subcommand="add",
                block_args=["-A", "--all"],
                reason="test",
            )
        ]
        result = check_custom_rules(["git", "add", "file.txt"], rules)
        self.assertIsNone(result)

    def test_rule_without_subcommand_matches_any(self) -> None:
        """Rule without subcommand matches any invocation."""
        rules = [
            CustomRule(
                name="block-npm-global",
                command="npm",
                subcommand=None,
                block_args=["-g", "--global"],
                reason="No global installs.",
            )
        ]
        # Match with install subcommand
        result = check_custom_rules(["npm", "install", "-g", "pkg"], rules)
        self.assertEqual(result, "[block-npm-global] No global installs.")

        # Match with uninstall subcommand too
        result = check_custom_rules(["npm", "uninstall", "-g", "pkg"], rules)
        self.assertEqual(result, "[block-npm-global] No global installs.")

    def test_multiple_rules_first_match_wins(self) -> None:
        """Multiple matching rules - first match wins."""
        rules = [
            CustomRule(
                name="rule1",
                command="git",
                subcommand="add",
                block_args=["-A"],
                reason="Rule 1 reason",
            ),
            CustomRule(
                name="rule2",
                command="git",
                subcommand="add",
                block_args=["-A"],
                reason="Rule 2 reason",
            ),
        ]
        result = check_custom_rules(["git", "add", "-A"], rules)
        self.assertEqual(result, "[rule1] Rule 1 reason")

    def test_case_sensitive_command_matching(self) -> None:
        """Command matching is case-sensitive per spec."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand=None,
                block_args=["-A"],
                reason="test",
            )
        ]
        # Lowercase git matches
        result = check_custom_rules(["git", "-A"], rules)
        self.assertEqual(result, "[test] test")

        # Uppercase GIT does NOT match (case-sensitive)
        result = check_custom_rules(["GIT", "-A"], rules)
        self.assertIsNone(result)

    def test_case_sensitive_arg_matching(self) -> None:
        """Argument matching is case-sensitive (exact match)."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand=None,
                block_args=["-A"],
                reason="test",
            )
        ]
        # -A matches
        result = check_custom_rules(["git", "-A"], rules)
        self.assertIsNotNone(result)

        # -a does NOT match
        result = check_custom_rules(["git", "-a"], rules)
        self.assertIsNone(result)

    def test_args_with_values(self) -> None:
        """Arguments with values can be matched."""
        rules = [
            CustomRule(
                name="test",
                command="docker",
                subcommand="run",
                block_args=["--privileged"],
                reason="No privileged mode.",
            )
        ]
        result = check_custom_rules(["docker", "run", "--privileged", "image"], rules)
        self.assertEqual(result, "[test] No privileged mode.")

    def test_subcommand_with_options_before(self) -> None:
        """Subcommand extraction with options that consume arguments.

        Limitation: We cannot distinguish between option values and subcommands
        without command-specific knowledge. For `git -C /path push`, we treat
        `/path` as the subcommand because we don't know `-C` consumes an argument.

        This is a deliberate trade-off: most short options are boolean flags,
        so not assuming they consume arguments is safer. Options that take
        values can use the attached form (e.g., `-C/path`) to avoid ambiguity.
        """
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="push",
                block_args=["--force"],
                reason="No force push.",
            )
        ]
        # git -C /path push --force: we incorrectly treat /path as subcommand
        # since we can't know -C consumes an argument. This is a known limitation.
        result = check_custom_rules(["git", "-C", "/path", "push", "--force"], rules)
        # Rule expects subcommand="push" but we see "/path", so no match
        self.assertIsNone(result)

        # Workaround: use attached form -C/path, then push is correctly identified
        result = check_custom_rules(["git", "-C/path", "push", "--force"], rules)
        self.assertEqual(result, "[test] No force push.")

    def test_docker_compose_pattern(self) -> None:
        """docker compose up pattern from spec."""
        rules = [
            CustomRule(
                name="block-docker-compose-up",
                command="docker",
                subcommand="compose",
                block_args=["up"],
                reason="No docker compose up.",
            )
        ]
        result = check_custom_rules(["docker", "compose", "up", "-d"], rules)
        self.assertEqual(result, "[block-docker-compose-up] No docker compose up.")

    def test_empty_tokens_returns_none(self) -> None:
        """Empty tokens list returns None."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand=None,
                block_args=["-A"],
                reason="test",
            )
        ]
        result = check_custom_rules([], rules)
        self.assertIsNone(result)

    def test_empty_rules_returns_none(self) -> None:
        """Empty rules list returns None."""
        result = check_custom_rules(["git", "add", "-A"], [])
        self.assertIsNone(result)

    def test_command_with_path_normalized(self) -> None:
        """Command with path is normalized to basename."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand=None,
                block_args=["-A"],
                reason="test",
            )
        ]
        result = check_custom_rules(["/usr/bin/git", "-A"], rules)
        self.assertEqual(result, "[test] test")

    def test_block_args_with_equals_value(self) -> None:
        """Block args with = values."""
        rules = [
            CustomRule(
                name="test",
                command="npm",
                subcommand="config",
                block_args=["--location=global"],
                reason="No global config.",
            )
        ]
        tokens = ["npm", "config", "set", "--location=global"]
        result = check_custom_rules(tokens, rules)
        self.assertEqual(result, "[test] No global config.")

    def test_block_dot_for_git_add(self) -> None:
        """Block git add . pattern."""
        rules = [
            CustomRule(
                name="block-git-add-dot",
                command="git",
                subcommand="add",
                block_args=["."],
                reason="Use specific files.",
            )
        ]
        result = check_custom_rules(["git", "add", "."], rules)
        self.assertEqual(result, "[block-git-add-dot] Use specific files.")

        # git add file.txt should pass
        result = check_custom_rules(["git", "add", "file.txt"], rules)
        self.assertIsNone(result)

    def test_multiple_blocked_args_any_matches(self) -> None:
        """Any blocked arg matching triggers block."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="add",
                block_args=["-A", "--all", ".", "-u"],
                reason="No blanket add.",
            )
        ]
        # Each blocked arg should trigger
        for arg in ["-A", "--all", ".", "-u"]:
            result = check_custom_rules(["git", "add", arg], rules)
            self.assertIsNotNone(result, f"Expected {arg} to trigger block")

    def test_combined_short_options_expanded(self) -> None:
        """Combined short options like -Ap ARE expanded to match -A."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="add",
                block_args=["-A"],
                reason="test",
            )
        ]
        # -Ap contains -A, so it should be blocked
        result = check_custom_rules(["git", "add", "-Ap"], rules)
        self.assertEqual(result, "[test] test")

    def test_combined_short_options_case_sensitive(self) -> None:
        """Short option expansion is case-sensitive."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="add",
                block_args=["-A"],
                reason="test",
            )
        ]
        # -ap does NOT contain -A (lowercase a != uppercase A)
        result = check_custom_rules(["git", "add", "-ap"], rules)
        self.assertIsNone(result)

    def test_combined_short_options_multiple_flags(self) -> None:
        """Multiple bundled flags are all expanded."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="add",
                block_args=["-u"],
                reason="test",
            )
        ]
        # -Aup contains -u
        result = check_custom_rules(["git", "add", "-Aup"], rules)
        self.assertEqual(result, "[test] test")

    def test_long_options_not_expanded(self) -> None:
        """Long options are NOT expanded (exact match only)."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="add",
                block_args=["--all"],
                reason="test",
            )
        ]
        # --all-files is not --all
        result = check_custom_rules(["git", "add", "--all-files"], rules)
        self.assertIsNone(result)

    def test_subcommand_after_double_dash(self) -> None:
        """Subcommand after -- is found correctly."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="checkout",
                block_args=["--force"],
                reason="test",
            )
        ]
        # git -- checkout --force: subcommand is checkout after --
        result = check_custom_rules(["git", "--", "checkout", "--force"], rules)
        self.assertEqual(result, "[test] test")

    def test_no_subcommand_after_double_dash_at_end(self) -> None:
        """-- at end means no subcommand."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="push",
                block_args=["--force"],
                reason="test",
            )
        ]
        result = check_custom_rules(["git", "--"], rules)
        self.assertIsNone(result)

    def test_long_option_with_equals(self) -> None:
        """Long option with = value doesn't affect subcommand."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="push",
                block_args=["--force"],
                reason="test",
            )
        ]
        result = check_custom_rules(["git", "--config=foo", "push", "--force"], rules)
        self.assertEqual(result, "[test] test")

    def test_long_option_without_equals(self) -> None:
        """Long option without = skips just that token."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="push",
                block_args=["--force"],
                reason="test",
            )
        ]
        # --verbose is a flag, push is subcommand
        result = check_custom_rules(["git", "--verbose", "push", "--force"], rules)
        self.assertEqual(result, "[test] test")

    def test_attached_short_option_value(self) -> None:
        """Attached short option value like -Cpath."""
        rules = [
            CustomRule(
                name="test",
                command="git",
                subcommand="push",
                block_args=["--force"],
                reason="test",
            )
        ]
        # -C/path is attached, so push is next
        result = check_custom_rules(["git", "-C/path", "push", "--force"], rules)
        self.assertEqual(result, "[test] test")
