---
name: prompt-template-review
description: Validate pipeline prompt templates. Finds unreplaced placeholders, contradictions between templates, stale instructions.
argument-hint: "[all | specific-template.md]"
---

# Prompt Template Review: $ARGUMENTS

## Parse Arguments

The user provides one of:

1. **No args or "all"**: Review all templates in `scripts/build/phases/`
2. **Specific file**: `v6-write.md` or full path

## Execute

Read and follow the full review checklist at [template-review-checklist.md](template-review-checklist.md).

## Output

Print a structured report to the conversation. Save findings to `docs/architecture/prompt-template-findings.md` if issues found.
