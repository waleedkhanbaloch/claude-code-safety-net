---
description: Set custom rules for Safety Net
allowed-tools: Bash, Read, Write, AskUserQuestion
---

You are helping the user configure custom blocking rules for claude-code-safety-net.

## Context

### Schema Documentation

!`npx -y cc-safety-net --custom-rules-doc`

## Your Task

Follow this flow exactly:

### Step 1: Ask for Scope

Use AskUserQuestion to let user select scope:

```json
{
  "questions": [
    {
      "question": "Which scope would you like to configure?",
      "header": "Configure",
      "multiSelect": false,
      "options": [
        {
          "label": "User",
          "description": "(`~/.cc-safety-net/config.json`) - applies to all your projects"
        },
        {
          "label": "Project",
          "description": "(`.safety-net.json`) - applies only to this project"
        }
      ]
    }
  ]
}
```

### Step 2: Show Examples and Ask for Rules

Show examples in natural language:
- "Block `git add -A` and `git add .` to prevent blanket staging"
- "Block `npm install -g` to prevent global package installs"
- "Block `docker system prune` to prevent accidental cleanup"

Ask the user to describe rules in natural language. They can list multiple.

### Step 3: Generate and Show JSON Config

Parse user input and generate valid schema JSON using the schema documentation above.

Then show the generated config JSON to the user.

### Step 4: Ask for Confirmation

Use AskUserQuestion to let user choose:

```json
{
  "questions": [
    {
      "question": "Does this look correct?",
      "header": "Confirmation",
      "multiSelect": false,
      "options": [
        {
          "label": "Yes",
        },
        {
          "label": "No",
        }
      ]
    }
  ]
}
```

### Step 5: Check and Handle Existing Config

1. Check existing User Config with `cat ~/.cc-safety-net/config.json 2>/dev/null || echo "No user config found"`
2. Check existing Project Config with `cat .safety-net.json 2>/dev/null || echo "No project config found"`

If the chosen scope already has a config:

Show the existing config to the user.
Use AskUserQuestion tool to let user choose:
```json
{
"questions": [
    {
    "question": "The chosen scope already has a config. What would you like to do?",
    "header": "Configure",
    "multiSelect": false,
    "options": [
        {
        "label": "Merge",
        },
        {
        "label": "Replace",
        }
    ]
    }
]
}
```

### Step 6: Write and Validate

Write the config to the chosen scope, then validate with `npx -y cc-safety-net --verify-config`.

If validation errors:
- Show specific errors
- Offer to fix with your best suggestion
- Confirm before proceeding

### Step 7: Confirm Success

Tell the user:
1. Config saved to [path]
2. **Changes take effect immediately** - no restart needed
3. Summary of rules added

## Important Notes

- Custom rules can only ADD restrictions, not bypass built-in protections
- Rule names must be unique (case-insensitive)
- Invalid config → entire config ignored, only built-in rules apply
