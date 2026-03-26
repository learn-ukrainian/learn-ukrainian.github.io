---
name: plan-review
description: Review CORE level plans (A1-C2, PRO) using State Standard 2024 + textbook RAG + VESUM. Finds bad vocab, wrong grammar scope, Russianisms, factual errors.
argument-hint: <track> [modules: all | 1 | 5-10 | slug-name]
effort: high
---

# Plan Review (Core): $ARGUMENTS

**Scope: A1, A2, B1, B2, C1, C2, B2-PRO, C1-PRO only.** For seminar tracks (HIST, BIO, ISTORIO, LIT, OES, RUTH), use `/plan-review-seminar`.

## Parse Arguments

The user provides one of these argument patterns:

1. **Track + modules**: `a1 all`, `a1 1`, `a1 5-10`, `a1 1,3,5`
2. **Track + slug**: `a1 the-cyrillic-code-i`
3. **Full path**: `curriculum/l2-uk-en/plans/a1/the-cyrillic-code-i.yaml`
4. **Track only**: `a1` (defaults to `all`)

Parse the arguments:

- If `$ARGUMENTS` contains a `/` and ends in `.yaml`, treat it as a **full path** to a single plan file. Extract the track from the path (the directory name under `plans/`).
- Otherwise, `$0` = track, `$1` = module selector (default: `all`).

**Plans directory**: `curriculum/l2-uk-en/plans/{track}/*.yaml`

## Module Selection

- `all` -- process every `.yaml` file in the plans directory
- Single number (e.g., `1`) -- find the plan with `sequence: 1` in its YAML
- Range (e.g., `5-10`) -- find plans with sequence 5 through 10
- List (e.g., `1,3,5`) -- find plans with those specific sequences
- Slug (e.g., `the-cyrillic-code-i`) -- find the plan file `{slug}.yaml`

To match sequence numbers, read each YAML and check the `sequence:` field.

## Execute

Read and follow the full plan review prompt at [plan-review-prompt.md](plan-review-prompt.md). It contains all checks, RAG tool usage, and the output format.

For review-tier reference docs, see [review-tiers/](review-tiers/).

**MANDATORY first step**: Read `docs/l2-uk-en/state-standard-2024-mapping.yaml` ONCE before reviewing any plans. This is the curriculum authority for core levels.

**Output path**: Save each review to `curriculum/l2-uk-en/{track}/audit/{slug}-plan-review.md`

After all plans, produce a summary: PASS/FAIL counts, CRITICAL and HIGH issues grouped by pattern, suggested template fixes. Do NOT fix plans -- report only. Reference issue #729.
