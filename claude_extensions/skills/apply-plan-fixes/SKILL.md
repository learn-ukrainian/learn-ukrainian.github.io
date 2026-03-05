---
name: apply-plan-fixes
description: Apply fixes from plan review reports. Reads audit reports, shows proposed changes for approval, then applies them. Respects plan versioning rules.
argument-hint: <track> [modules: all | 1 | 5-10 | slug-name] [--severity CRITICAL,HIGH | --all-fixes]
---

# Apply Plan Fixes: $ARGUMENTS

**Prerequisite:** Plan review reports must exist at `curriculum/l2-uk-en/{track}/audit/{slug}-plan-review.md`. Run `/plan-review` or `/plan-review-seminar` first.

## Parse Arguments

The user provides one of these argument patterns:

1. **Track + modules**: `a1 all`, `hist 5-10`, `bio 1,3,5`
2. **Track + slug**: `a1 the-cyrillic-code-i`
3. **Full path**: `curriculum/l2-uk-en/plans/a1/the-cyrillic-code-i.yaml`
4. **Track only**: `a1` (defaults to `all`)

Optional flags (appended after module selector):
- `--severity CRITICAL` — only apply CRITICAL fixes
- `--severity CRITICAL,HIGH` — apply CRITICAL and HIGH (no MEDIUM)
- `--all-fixes` — apply all fixes including LOW
- Default (no flag): CRITICAL, HIGH, and MEDIUM

**Plans directory**: `curriculum/l2-uk-en/plans/{track}/*.yaml`

## Execute

Read and follow the full prompt at [apply-plan-fixes-prompt.md](apply-plan-fixes-prompt.md).

**Output**: Modified plan files + summary of changes applied.
