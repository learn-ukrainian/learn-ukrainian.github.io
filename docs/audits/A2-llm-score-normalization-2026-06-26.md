# A2 LLM Score Normalization

**Date:** 2026-06-26
**Branch:** `codex/A2-llm-score-ledger`
**Primary ledger:** `docs/audits/A2-current-llm-scores-2026-06-26.md`

## Decision

Create a durable A2 score ledger with every current module marked
`not yet calculated`.

No LLM/content-review scores were found for current A2 modules, and no new
score sweep was run. The existing deterministic A2 status document is stale and
must not be normalized into LLM scores.

## Why The Old Status Doc Is Not A Score Source

`docs/status/A2-STATUS.md` is generated deterministic status evidence, not an
LLM/content-review report. It was generated on 2026-02-25 for a 71-module A2
layout:

- 37 PASS entries
- 33 PROSE-only entries
- 1 FAIL/problem entry

The current A2 source tree has 69 modules. The manifest, plans, and module
files agree on those 69 slugs. Only five current slugs appear in the old status
doc by exact name: `dative-verbs`, `all-cases-practice`, `checkpoint-cases`,
`preferences-and-choices`, and `because-and-although`.

Because the status doc is both deterministic and stale, it can only be cited as
historical audit context. It cannot establish a numeric score or current
human-review readiness.

## Normalized State

| Category | Count | Normalized state |
| --- | ---: | --- |
| Current A2 modules | 69 | In scope for future score calculation. |
| Current persisted LLM scores | 0 | No score evidence found. |
| Current unscored modules | 69 | `not yet calculated`. |
| Current PASS-only modules | 0 | No current deterministic status files exist. |
| Current FAIL/problem modules | 0 | No current deterministic status files exist. |
| Historical PASS-only entries | 37 | Stale deterministic context only. |
| Historical PROSE-only entries | 33 | Stale deterministic context only. |
| Historical FAIL/problem entries | 1 | Stale deterministic context only. |

## Future Update Path

When an approved A2 content-review scoring run exists, update the primary ledger
by recording each module's persisted numeric score, verdict, score source, and
human-review readiness. Do not replace `not yet calculated` with a score unless
the score is backed by a durable review artifact or a new approved scoring run.
