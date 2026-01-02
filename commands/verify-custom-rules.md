---
description: Verify custom rules for the project
allowed-tools: Bash, AskUserQuestion
---

**Reference**: @CUSTOM_RULES_REFERENCE.md for schema details, field constraints, and examples.

You are helping the user verify the custom rules config file.
ALWAYS use AskUserQuestion tool when you need to ask the user questions.

### Verification Script

```bash
python3 --version >/dev/null 2>&1 && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/verify_config.py" || python "${CLAUDE_PLUGIN_ROOT}/scripts/verify_config.py"
```

If the config has validation errors, inform the user:
- Show the specific validation errors
- Offer to fix them with your best suggestion
- Ask for confirmation before proceeding

After fixing the config, verify it again.