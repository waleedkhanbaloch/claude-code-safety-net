# Contributing to Claude Code Safety Net

First off, thanks for taking the time to contribute! This document provides guidelines and instructions for contributing to cc-safety-net.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Development Setup](#development-setup)
  - [Testing Your Changes Locally](#testing-your-changes-locally)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
  - [Build Commands](#build-commands)
  - [Code Style & Conventions](#code-style--conventions)
- [Making Changes](#making-changes)
  - [Adding a Git Rule](#adding-a-git-rule)
  - [Adding an rm Rule](#adding-an-rm-rule)
  - [Adding Other Command Rules](#adding-other-command-rules)
- [Pull Request Process](#pull-request-process)
- [Publishing](#publishing)
- [Getting Help](#getting-help)

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to make better tools together.

## Getting Started

### Prerequisites

- **Bun** - Required runtime and package manager ([install guide](https://bun.sh/docs/installation))
- **Claude Code** or **OpenCode** - For testing the plugin

### Development Setup

```bash
# Clone the repository
git clone https://github.com/kenryu42/claude-code-safety-net.git
cd claude-code-safety-net

# Install dependencies
bun install
```

### Testing Your Changes Locally

After making changes, you can test your local build in Claude Code:

1. **Disable the safety-net plugin** in Claude Code (if installed) and exit Claude Code completely.

2. **Run Claude Code with the local plugin**:
   ```bash
   claude --plugin-dir .
   ```

3. **Test blocked commands** to verify your changes:
   ```bash
   # This should be blocked
   git checkout -- README.md

   # This should be allowed
   git checkout -b test-branch
   ```

> [!NOTE]
> See the [official documentation](https://docs.anthropic.com/en/docs/claude-code/plugins#test-your-plugins-locally) for more details on testing plugins locally.

## Project Structure

```
claude-code-safety-net/
├── .claude-plugin/
│   ├── plugin.json         # Plugin metadata
│   └── marketplace.json    # Marketplace config
├── hooks/
│   └── hooks.json          # Hook definitions
├── src/
│   ├── index.ts            # OpenCode plugin export
│   ├── types.ts            # Shared type definitions
│   ├── bin/
│   │   └── cc-safety-net.ts  # Claude Code CLI entry point
│   └── core/
│       ├── analyze.ts      # Main analysis logic
│       ├── audit.ts        # Audit logging
│       ├── config.ts       # Config loading
│       ├── rules-git.ts    # Git subcommand analysis
│       ├── rules-rm.ts     # rm command analysis
│       ├── rules-custom.ts # Custom rule evaluation
│       ├── shell.ts        # Shell parsing utilities
│       └── verify-config.ts # Config validator
├── tests/
│   ├── helpers.ts          # Test utilities
│   ├── rules-git.test.ts   # Git rule tests
│   ├── rules-rm.test.ts    # rm rule tests
│   └── ...                 # Other test files
├── package.json            # Project config
├── tsconfig.json           # TypeScript config
└── biome.json              # Linter/formatter config
```

| Module | Purpose |
|--------|---------|
| `analyze.ts` | Main entry, command analysis orchestration |
| `rules-git.ts` | Git rules (checkout, restore, reset, clean, push, branch, stash) |
| `rules-rm.ts` | rm analysis (cwd-relative, temp paths, root/home detection) |
| `rules-custom.ts` | Custom rule matching |
| `shell.ts` | Shell parsing (`splitShellCommands`, `shlexSplit`, `stripWrappers`) |

## Development Workflow

### Build Commands

```bash
# Run all checks (lint, type check, dead code, ast-grep scan, tests)
bun run check

# Individual commands
bun run lint          # Lint + format (Biome)
bun run typecheck     # Type check
bun run knip          # Dead code detection
bun run sg:scan       # AST pattern scan
bun test              # Run tests

# Run specific test
bun test tests/rules-git.test.ts

# Run tests matching pattern
bun test --grep "checkout"

# Build for distribution
bun run build
```

### Code Style & Conventions

| Convention | Rule |
|------------|------|
| Runtime | **Bun** |
| Package Manager | **bun only** (`bun install`, `bun run`) |
| Formatter/Linter | **Biome** |
| Type Hints | Required on all functions |
| Type Syntax | `type \| null` preferred over `type \| undefined` |
| File Naming | `kebab-case` (e.g., `rules-git.ts`, not `rulesGit.ts`) |
| Function Naming | `camelCase` for functions, `PascalCase` for types/interfaces |
| Constants | `SCREAMING_SNAKE_CASE` for reason constants |
| Imports | Relative imports within package |

**Examples**:

```typescript
// Good
export function analyzeCommand(
  command: string,
  options?: { strict?: boolean }
): string | null {
  // ...
}

// Bad
export function analyzeCommand(command, options) {  // Missing type hints
  // ...
}
```

**Anti-Patterns (Do Not Do)**:
- Using npm/yarn/pnpm instead of bun
- Suppressing type errors with `@ts-ignore` or `any`
- Skipping tests for new rules
- Modifying version in `package.json` directly

## Making Changes

### Adding a Git Rule

1. **Add reason constant** in `src/core/rules-git.ts`:
   ```typescript
   const REASON_MY_RULE = "git my-command does something dangerous. Use safer alternative.";
   ```

2. **Add detection logic** in `analyzeGit()`:
   ```typescript
   if (subcommand === "my-command" && tokens.includes("--dangerous-flag")) {
     return REASON_MY_RULE;
   }
   ```

3. **Add tests** in `tests/rules-git.test.ts`:
   ```typescript
   describe("git my-command", () => {
     test("dangerous flag blocked", () => {
       assertBlocked("git my-command --dangerous-flag", "dangerous");
     });

     test("safe flag allowed", () => {
       assertAllowed("git my-command --safe-flag");
     });
   });
   ```

4. **Run checks**:
   ```bash
   bun run check
   ```

### Adding an rm Rule

1. **Add logic** in `src/core/rules-rm.ts`
2. **Add tests** in `tests/rules-rm.test.ts`
3. **Run checks**: `bun run check`

### Adding Other Command Rules

1. **Add reason constant** in `src/core/analyze.ts`:
   ```typescript
   const REASON_MY_COMMAND = "my-command is dangerous because...";
   ```

2. **Add detection** in `analyzeSegment()`

3. **Add tests** in the appropriate test file

4. **Run checks**: `bun run check`

### Edge Cases to Test

When adding rules, ensure you test these edge cases:

- Shell wrappers: `bash -c '...'`, `sh -lc '...'`
- Sudo/env prefixes: `sudo git ...`, `env VAR=1 git ...`
- Pipelines: `echo ok | git reset --hard`
- Interpreter one-liners: `python -c 'os.system("...")'`
- Xargs/parallel: `find . | xargs rm -rf`
- Busybox: `busybox rm -rf /`

## Pull Request Process

1. **Fork** the repository and create your branch from `main`
2. **Make changes** following the conventions above
3. **Run all checks** locally:
   ```bash
   bun run check  # Must pass with no errors
   ```
4. **Test in Claude Code** using the local plugin method described above
5. **Commit** with clear, descriptive messages:
   - Use present tense ("Add rule" not "Added rule")
   - Reference issues if applicable ("Fix #123")
6. **Push** to your fork and create a Pull Request
7. **Describe** your changes clearly in the PR description

### PR Checklist

- [ ] Code follows project conventions (type hints, naming, etc.)
- [ ] `bun run check` passes (lint, types, dead code, tests)
- [ ] Tests added for new rules
- [ ] Tested locally with Claude Code and Opencode
- [ ] Updated documentation if needed (README, AGENTS.md)
- [ ] No version changes in `package.json`

## Publishing

**Important**: Version bumping and releases are handled by maintainers only.

- **Never** modify the version in `package.json` directly
- Maintainers handle versioning, tagging, and releases

## Getting Help

- **Project Knowledge**: Check `CLAUDE.md` or `AGENTS.md` for detailed architecture and conventions
- **Code Patterns**: Review existing implementations in `src/core/`
- **Test Patterns**: See `tests/helpers.ts` for test utilities
- **Issues**: Open an issue for bugs or feature requests

---

Thank you for contributing to Claude Code Safety Net! Your efforts help keep AI-assisted coding safer for everyone.
