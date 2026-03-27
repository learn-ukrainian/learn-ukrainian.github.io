---
name: code-review
description: Review changed code for reuse, quality, and efficiency, then fix any issues found.
argument-hint: "[files|diff|all]"
---

# Code Review: $ARGUMENTS

## Parse Arguments

The user provides one of:

1. **No args or "diff"**: Review only files changed since last commit (`git diff --name-only` + `git diff --cached --name-only`)
2. **"all"**: Review all staged + unstaged changes
3. **Specific files**: `scripts/build/v6_build.py scripts/build/dispatch.py`

## Execute

Read and follow the full code review checklist at [code-review-checklist.md](code-review-checklist.md).

## Output

Print a structured report to the conversation. Do NOT write a file unless specifically asked.
