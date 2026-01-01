"""Custom rule matching logic."""

import posixpath

from .config import CustomRule
from .shell import _short_opts


def _normalize_command(token: str) -> str:
    """Normalize command token to basename (case-sensitive per spec)."""
    return posixpath.basename(token)


def _extract_subcommand(tokens: list[str]) -> str | None:
    """Extract the first non-option argument after the command.

    This is the subcommand for commands like git, docker, npm.

    Limitation: We do NOT assume short options consume the next token, because
    we can't know without command-specific knowledge. For commands like
    `git -C /path push`, this returns `/path` (the option value) instead of
    `push` (the real subcommand), causing false negatives for subcommand-based
    rules. This is a known trade-off to avoid command-specific parsing.
    """
    i = 1
    while i < len(tokens):
        tok = tokens[i]

        # End of options marker
        if tok == "--":
            i += 1
            # Return next token if exists
            if i < len(tokens):
                return tokens[i]
            return None

        # Long option with attached value: --option=value
        if tok.startswith("--"):
            # Skip this token (value is attached or option is boolean)
            i += 1
            continue

        # Short option: -X or -Xvalue or -abc (bundled)
        if tok.startswith("-") and len(tok) >= 2:
            # Skip this token only (don't assume it consumes next token)
            # This is conservative: we might treat an option's value as subcommand,
            # but we won't skip the real subcommand
            i += 1
            continue

        # Non-option: this is the subcommand
        return tok

    return None


def check_custom_rules(
    tokens: list[str],
    rules: list[CustomRule],
) -> str | None:
    """Check if any custom rule matches the tokenized command.

    Returns formatted block message "[rule-name] reason" if blocked, None otherwise.
    """
    if not tokens or not rules:
        return None

    # Normalize command to basename for matching
    command = _normalize_command(tokens[0])

    # Extract subcommand (first non-option arg)
    subcommand = _extract_subcommand(tokens)

    # Build a set of all tokens for fast lookup
    token_set = set(tokens)

    # Extract expanded short options (e.g., -Ap -> {'A', 'p'})
    short_opts = _short_opts(tokens)

    for rule in rules:
        # Check command match (case-sensitive per spec)
        if rule.command != command:
            continue

        # Check subcommand match if rule specifies one
        if rule.subcommand is not None:
            if subcommand != rule.subcommand:
                continue

        # Check if any blocked arg is present
        for blocked_arg in rule.block_args:
            # Exact match
            if blocked_arg in token_set:
                return f"[{rule.name}] {rule.reason}"

            # Short option expansion: -A matches -Ap, -Au, etc.
            if (
                len(blocked_arg) == 2
                and blocked_arg[0] == "-"
                and blocked_arg[1] != "-"
                and blocked_arg[1] in short_opts
            ):
                return f"[{rule.name}] {rule.reason}"

    return None
