---
name: context-budget-audit
description: Audit prompt sizes across build orchestration dirs. Surfaces sections that dominate the prompt (>40%), tracks per-phase budget vs the model's context window, and checks whether directives in the prompt were actually covered in the response.
argument-hint: <track>/<slug> | <track> <slug> | <track> <range>
---

# Context Budget Audit: $ARGUMENTS

## Why

When a build produces low scores, we usually discover only after the fact that the wiki packet was 62.5% of the write prompt and drowned out everything else. This skill catches that pattern BEFORE it wastes a build — or explains it AFTER when you're debugging.

The v6 write prompt has historically grown without anyone noticing. The first real data point: #1070 surfaced a 33K-char write prompt that was causing Gemini to ignore MCP tool instructions. The Gemini session analyzer (#1174, `scripts/build/session_analysis.py`) now emits a `session-analysis.yaml` next to every dispatch meta file. This skill is the human-readable interpretation layer on top of those raw files.

## Parse Arguments

The user provides one of these patterns:

1. **Full path**: `curriculum/l2-uk-en/a2/orchestration/a2-bridge/`
2. **Track + slug**: `a2 a2-bridge`
3. **Track + range**: `a2 1-10` (audit a range of modules in sequence)
4. **Level only**: `a2` (audit every module with a non-empty orchestration dir)

Resolve the path(s) and process each in turn.

## Execute

For each orchestration dir, walk `dispatch/` and load every `*-session-analysis.yaml` file. Each file has this shape:

```yaml
session_path: /Users/.../session-2026-04-10T21-23-efd64bd5.json
phase: write-chunk-02
prompt_chars: 41214
response_chars: 8695
prompt_words: 5683
response_words: 1442
sections:
  - name: header
    length: 489
    fraction: 0.0119
  - name: skeleton
    length: 1535
    fraction: 0.0372
  - name: plan
    length: 9991
    fraction: 0.2424
  - name: wiki
    length: 25780
    fraction: 0.6254
  - name: output_spec
    length: 128
    fraction: 0.0031
large_sections:
  - wiki
directives_total: 10
directives_covered: 6
directives_missed:
  - kind: must
    text: Each section MUST contain at least one callout.
    covered: false
    coverage_note: "1/4 keywords (25%)"
```

Aggregate this data across phases and produce a report with four sections:

### 1. Budget overview per phase

A table: phase → prompt_chars → response_chars → compression ratio → flagged (yes if any large section).

### 2. Oversized sections (> 40% threshold)

Any section whose `fraction > 0.40`. These are drowning-out candidates. Group by phase and section name:

- `write-chunk-02: wiki at 62.5% (25.7K of 41.2K)` — recommendation: **chunk the wiki packet** or reduce `_SECTION_MARKERS` trim window in `scripts/build/session_analysis.py`.
- `write: plan at 48% (19K of 40K)` — recommendation: **trim plan content_outline** in the writer prompt template (the plan belongs in `check` phase, not `write`).

### 3. Directive coverage

Cross-phase average of `directives_covered / directives_total`. List the top 5 most-frequently-missed directives (normalize by text prefix) so the user can decide if the directive is worth keeping or rephrasing.

### 4. Context window headroom

For each phase, compute `prompt_chars / model_context_chars`. Model context windows (as of 2026-04):

| Model | Context (chars, 4 chars/token approx) |
|---|---|
| `gemini-3.1-pro-preview` | 4,000,000 (1M tokens) |
| `gemini-3-flash` | 4,000,000 |
| `claude-opus-4-6` | 800,000 (200K tokens) |
| `gpt-5.4` (Codex) | 1,000,000 |

Flag any phase where prompt_chars exceeds 50% of the model's window — that's a hard rule for this skill. (For all current pipelines, this is ~500K+ chars, which should NEVER happen for a single v6 phase. If it does, something is badly wrong.)

### 5. Trend analysis (optional)

If there are multiple orchestration dirs for the same slug (from repeated builds / retries), compare prompt sizes across attempts. If the prompt is GROWING across retries (e.g. due to correction directives being appended), flag it.

## Output

Save the report to `curriculum/l2-uk-en/{track}/audit/{slug}-context-budget.md`.

Format:

```markdown
# Context Budget Audit: {slug}

**Track**: {track}
**Audited at**: {ISO timestamp}
**Orchestration dir**: {absolute path}

## Phase overview

| Phase | Prompt (chars) | Response (chars) | Compression | Flagged |
|---|---:|---:|---:|:-:|
| check | 1234 | 456 | 2.7x | |
| research | ... |
| skeleton | ... |
| write-chunk-01 | 41214 | 8695 | 4.7x | ⚠️ wiki 62.5% |
| write-chunk-02 | ... |
| review | ... |

## Oversized sections (> 40% of prompt)

- **write-chunk-01**: `wiki` at 62.5% (25,780 / 41,214 chars)
  - Recommendation: cap wiki packet at 20K chars in `_build_chunk_prompt`, or move wiki to a separate enrich phase after write.

## Directive coverage

Average: 6 / 10 (60%) — this is low. Target is ≥85%.

Top 5 missed directives (across all phases):
1. `Each section MUST contain at least one callout.` — missed in 3 of 4 chunks
2. `<!-- INJECT_ACTIVITY: quiz, Case Drill, 8 items -->` — missed in write-chunk-01
...

## Context window headroom

| Phase | Prompt | Model | Window | Used |
|---|---:|---|---:|---:|
| write-chunk-01 | 41K | gemini-3.1-pro-preview | 4M | 1.0% |

No phase exceeds the 50% threshold. Good.

## Recommendations

1. Cap wiki packet at 20K chars in `_build_chunk_prompt` (drops prompt by 30%).
2. Investigate why the callout directive is being ignored — it's explicit in the prompt but gets 25% keyword coverage.
```

## Batch mode

When given a range or a whole level, also produce `curriculum/l2-uk-en/{track}/audit/context-budget-summary.md`:

- Per-phase averages (mean prompt_chars, mean directive coverage)
- Top 10 modules with the largest prompts
- Top 10 modules with the lowest directive coverage
- Cross-module patterns: directives missed in >50% of modules (these need prompt engineering, not per-module fixes)

## Source of truth

All data comes from `*-session-analysis.yaml` files emitted by `_save_dispatch_log` in `scripts/build/dispatch.py`. The analysis logic lives in `scripts/build/session_analysis.py` and the parser in `scripts/build/gemini_session.py`. If a phase has no `*-session-analysis.yaml` file, skip it silently — that phase either pre-dates #1174 or used a non-Gemini agent (Codex/Claude session parsers are follow-up work).

Reference issues: #1076 (this skill), #1174 (the underlying analyzer), #1070 (the original 33K-prompt incident that motivated both).
