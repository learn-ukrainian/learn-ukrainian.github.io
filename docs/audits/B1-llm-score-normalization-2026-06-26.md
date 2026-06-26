# B1 LLM Score Normalization

**Date:** 2026-06-26
**Scope:** Normalize B1 score evidence for the current source tree.

## Normalized State

| Category | Count | Normalized state |
| --- | --- | --- |
| Current B1 modules | 94 | In scope for future score calculation. |
| Current persisted LLM/content-review scores | 0 | No current score evidence found. |
| Current unscored modules | 94 | `not yet calculated`. |
| Current deterministic PASS-only modules | 0 | No current generated deterministic status artifacts exist. |
| Current deterministic FAIL/problem modules | 0 | No current generated deterministic status artifacts exist. |
| Historical deterministic status rows | 94 | Stale context only. |
| Historical PASS-only entries | 5 | Stale deterministic context only. |
| Historical PROSE-only entries | 81 | Stale deterministic context only. |
| Historical FAIL/problem entries | 8 | Stale deterministic context only. |

## Evidence Rules

1. Use numeric LLM/content-review scores only when a durable score table, a
   content-review artifact, or an explicit score ledger exists.
2. Record unscored current modules as `not yet calculated`; do not infer scores.
3. Keep deterministic audit status separate from LLM/content-review scores.
4. Do not convert deterministic PASS/FAIL/PROSE labels into numeric scores.
5. Treat `docs/status/B1-STATUS.md` as historical unless its slug set matches
   the current source tree.

## Why The Existing Status Page Is Historical

The current B1 source tree has 94 plan YAML files and 94 `module.md` files with
matching slugs. The deterministic status page also has 94 rows, but it describes
an older module set:

| Check | Result |
| --- | --- |
| Current module slugs not present in `docs/status/B1-STATUS.md` | 93 |
| Status-page slugs not present in current source tree | 93 |
| Overlapping slug | `aspect-in-imperatives` only |
| Current first module | `b1-baseline-past-present` |
| Historical status first module | `how-to-talk-about-grammar` |
| Current final module | `practice-exam` |
| Historical status final module | `b1-final-exam` |

Because of this mismatch, `docs/status/B1-STATUS.md` can support only a
historical deterministic-status note. It cannot establish current B1 pass/fail
counts, score readiness, or human-review readiness.

## Inventory Result

| Evidence source | Result |
| --- | --- |
| `docs/audits/*score*` | A1, A2, and B2 ledgers exist; no B1 ledger existed before this work. |
| `docs/reports/` | B1 plan and process reports found; no per-module LLM/content-review score table found. |
| `docs/status/B1-STATUS.md` | Stale deterministic table only. |
| `docs/status/CURRENT-STATUS.md` | Stale project-memory status only; not a per-module score source. |
| `curriculum/l2-uk-en/B1/` | Current source scope has no generated score/status/review artifacts. |
| `curriculum/l2-uk-en/plans/b1/` | Current source scope has 94 matching plan files. |

## Durable Ledger Created

The durable current ledger is
`docs/audits/B1-current-llm-scores-2026-06-26.md`.
