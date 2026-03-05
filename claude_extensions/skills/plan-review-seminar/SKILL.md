---
name: plan-review-seminar
description: Review SEMINAR track plans (HIST, BIO, ISTORIO, LIT, OES, RUTH) using ESU + Wikipedia + Literary RAG + VESUM. Finds factual errors, ghost sources, decolonization issues.
argument-hint: <track> [modules: all | 1 | 5-10 | slug-name]
---

# Plan Review (Seminar): $ARGUMENTS

**Scope: HIST, BIO, ISTORIO, LIT (all subtracks), OES, RUTH only.** For core levels (A1-C2, PRO), use `/plan-review`.

## Parse Arguments

The user provides one of these argument patterns:

1. **Track + modules**: `hist all`, `hist 1`, `hist 5-10`, `hist 1,3,5`
2. **Track + slug**: `hist volodymyr-khreshchennia`
3. **Full path**: `curriculum/l2-uk-en/plans/hist/volodymyr-khreshchennia.yaml`
4. **Track only**: `hist` (defaults to `all`)

Parse the arguments:

- If `$ARGUMENTS` contains a `/` and ends in `.yaml`, treat it as a **full path** to a single plan file. Extract the track from the path (the directory name under `plans/`).
- Otherwise, `$0` = track, `$1` = module selector (default: `all`).

**Plans directory**: `curriculum/l2-uk-en/plans/{track}/*.yaml`

**Valid tracks**: hist, bio, istorio, lit, lit-drama, lit-essay, lit-doc, lit-crimea, lit-fantastika, lit-hist-fic, lit-humor, lit-war, lit-youth, oes, ruth

## Module Selection

- `all` -- process every `.yaml` file in the plans directory
- Single number (e.g., `1`) -- find the plan with `sequence: 1` in its YAML
- Range (e.g., `5-10`) -- find plans with sequence 5 through 10
- List (e.g., `1,3,5`) -- find plans with those specific sequences
- Slug (e.g., `volodymyr-khreshchennia`) -- find the plan file `{slug}.yaml`

To match sequence numbers, read each YAML and check the `sequence:` field.

## Execute

Read and follow the full seminar plan review prompt at [plan-review-seminar-prompt.md](plan-review-seminar-prompt.md). It contains all checks, RAG tool usage, and the output format.

For review-tier reference, see the Tier 3 rubric at `claude_extensions/skills/plan-review/review-tiers/tier-3-seminar.md`.

**Output path**: Save each review to `curriculum/l2-uk-en/{track}/audit/{slug}-plan-review.md`

After all plans, produce a summary: PASS/FAIL counts, CRITICAL and HIGH issues grouped by pattern, suggested template fixes. Do NOT fix plans -- report only. Reference issue #729.
