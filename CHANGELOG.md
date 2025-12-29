# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.2.0 (2025-12-29)

### Feat

- add audit logging for denied commands
- add paranoid mode environment variable checks
- detect dangerous commands via xargs and parallel
- block git worktree remove --force
- block git checkout <ref> <pathspec> without --
- block find -delete destructive command

### Fix

- Add cross-platform script execution compatibility
- recognize rm -R (uppercase) as recursive and respect -- delimiter
- preserve case sensitivity for git branch -D detection

### Refactor

- rename strict to paranoid for rm rule parameter

## v0.1.0 (2025-12-26)

### Feat

- initial implementation
