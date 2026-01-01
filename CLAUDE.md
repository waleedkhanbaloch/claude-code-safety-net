# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Claude Code plugin that blocks destructive git and filesystem commands before execution. It works as a PreToolUse hook that intercepts Bash commands and denies dangerous operations like `git reset --hard`, `rm -rf`, and `git checkout -- <files>`.

## Commands

- **Setup**: `just setup` or `uv sync && uv run pre-commit install`
- **All checks**: `just check` (runs ruff, mypy, vulture for dead code, pytest with coverage)
- **Single test**: `uv run pytest tests/test_file.py::test_name -v`
- **Lint**: `uv run ruff check` / **Format**: `uv run ruff format`
- **Type check**: `uv run mypy .`
- **Release**: `just bump` (bumps version, generates changelog, pushes tags, creates GitHub release)
- **Verify config**: `uv run scripts/verify_config.py` (validates custom rule configs)

## Architecture

The hook receives JSON input on stdin containing `tool_name` and `tool_input`. For `Bash` tools, it analyzes the command and outputs JSON with `permissionDecision: "deny"` to block dangerous operations.

**Entry point**: `scripts/safety_net.py` → delegates to `scripts/safety_net_impl/hook.py`

**Core analysis flow**:
1. `hook.py:main()` parses JSON input, extracts command
2. `_analyze_command()` splits command on shell operators (`;`, `&&`, `|`, etc.)
3. `_analyze_segment()` tokenizes each segment, strips wrappers (sudo, env), identifies the command
4. Dispatches to `rules_git.py:_analyze_git()` or `rules_rm.py:_analyze_rm()` based on command
5. Checks custom rules via `rules_custom.py:check_custom_rules()` if configured

**Key modules**:
- `shell.py`: Shell parsing (`_split_shell_commands`, `_shlex_split`, `_strip_wrappers`, `_short_opts`)
- `rules_git.py`: Git subcommand analysis (checkout, restore, reset, clean, push, branch, stash)
- `rules_rm.py`: rm analysis (allows rm -rf within cwd except when cwd is $HOME; temp paths always allowed; strict mode blocks non-temp)
- `config.py`: Config loading, validation, merging (user `~/.cc-safety-net/config.json` + project `.safety-net.json`)
- `rules_custom.py`: Custom rule matching (`check_custom_rules()`)
- `tests/safety_net_test_base.py`: `SafetyNetTestCase` with `_run_guard()`, `_assert_blocked()`, `_assert_allowed()` helpers; `TempDirTestCase` for filesystem tests. 90% coverage enforced.

**Advanced detection**:
- Recursively analyzes shell wrappers (`bash -c '...'`) up to 5 levels deep
- Detects destructive commands in interpreter one-liners (`python -c`, `node -e`, `ruby -e`, `perl -e`)
- Handles `xargs` and `parallel` with template expansion and dynamic input detection
- Detects `find -delete` and `find -exec rm` patterns
- Redacts secrets (tokens, passwords, API keys) in block messages and audit logs
- Audit logging: blocked commands logged to `~/.cc-safety-net/logs/<session_id>.jsonl`

## Code Style (Python 3.10+)

- All functions require type hints (`disallow_untyped_defs = true`)
- Use `X | None` syntax (not `Optional[X]`)
- Use `Path` not string paths where applicable
- Ruff for formatting (88 char line length)

## Environment Variables

- `SAFETY_NET_STRICT=1`: Strict mode (fail-closed on unparseable hook input/commands)
- `SAFETY_NET_PARANOID=1`: Paranoid mode (enables all paranoid checks)
- `SAFETY_NET_PARANOID_RM=1`: Paranoid rm (blocks non-temp `rm -rf` even within cwd)
- `SAFETY_NET_PARANOID_INTERPRETERS=1`: Paranoid interpreters (blocks interpreter one-liners)

## Custom Rules

Users can define additional blocking rules in two scopes (merged, project overrides user):
- **User scope**: `~/.cc-safety-net/config.json` (applies to all projects)
- **Project scope**: `.safety-net.json` (in project root)

Rules are additive only—cannot bypass built-in protections. Invalid config silently falls back to built-in rules only. Use `verify_config.py` to validate configs.
