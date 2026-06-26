# A1 Current LLM Scores

**Generated:** 2026-06-26
**Scope:** A1 only, current 55-module source tree under `curriculum/l2-uk-en/A1/`
and current plans under `curriculum/l2-uk-en/plans/A1/`
**Purpose:** Normalize already-persisted A1 LLM/content-review scores into a
durable `docs/audits/` ledger. This report does not build modules, rewrite
module content, or create generated status/audit/review artifacts.

## Bottom Line

A1 now has a durable LLM score ledger for the current 55-module source tree.
The score source is `docs/reports/A1-MACRO-REVIEW-REPORT.md`, generated on
2026-04-04, which reports current-slug scores for all M01-M55 modules.

No fresh LLM scoring was run for this ledger. No deterministic audit was
re-run. Existing deterministic status evidence is historical and does not cover
the current 55-module layout.

## Counts

| Measure | Count | Notes |
| --- | ---: | --- |
| Current A1 modules in source tree | 55 | Source directories and plan YAML files match exactly. |
| Modules with normalized LLM/content-review score | 55 | All from `docs/reports/A1-MACRO-REVIEW-REPORT.md` Appendix B. |
| Unscored current modules | 0 | No current A1 module lacks a macro-review score. |
| Current modules with deterministic PASS only and no LLM score | 0 | The current source tree is fully scored by the macro review. |
| Current modules with current persisted deterministic PASS/FAIL status | 0 | No `curriculum/l2-uk-en/A1/status/*.json` directory exists in this checkout. |
| Historical deterministic PASS entries | 44 | `docs/status/A1-STATUS.md`, generated 2026-02-25, is an older 44-module status doc. |
| LLM problem modules | 2 | `days-and-months` and `euphony` scored 7/10. |
| LLM fail modules | 0 | The macro report has no score below 7/10. |
| Human-review ready by score threshold | 53 | Scores 8/10 or above. |
| Needs targeted content review before human-ready | 2 | The two 7/10 modules. |

## Score Distribution

| Score | Count | Modules |
| ---: | ---: | --- |
| 10/10 | 23 | `reading-ukrainian`, `who-am-i`, `my-family`, `what-is-it-like`, `colors`, `many-things`, `checkpoint-actions`, `what-time`, `free-time`, `checkpoint-time-nature`, `where-is-it`, `around-the-city`, `checkpoint-places`, `at-the-cafe`, `shopping`, `people-around-me`, `please-do-this`, `checkpoint-communication`, `yesterday`, `what-will-happen`, `my-plans`, `health`, `emergencies` |
| 9/10 | 20 | `sounds-letters-and-hello`, `stress-and-melody`, `checkpoint-first-contact`, `things-have-gender`, `how-many`, `this-and-that`, `checkpoint-my-world`, `what-i-like`, `my-morning`, `my-day`, `my-city`, `where-to`, `where-from`, `food-and-drink`, `i-eat-i-drink`, `checkpoint-food-shopping`, `linking-ideas`, `when-and-where`, `holidays`, `what-happened` |
| 8/10 | 10 | `special-signs`, `verbs-group-one`, `verbs-group-two`, `i-want-i-can`, `questions`, `weather`, `transport`, `hey-friend`, `my-story`, `a1-finale` |
| 7/10 | 2 | `days-and-months`, `euphony` |
| Below 7/10 | 0 | None reported. |

## Evidence Inventory

| Evidence | Coverage | Use in this ledger |
| --- | --- | --- |
| `docs/audits/*score*` | No pre-existing A1 durable score ledger found. B2 uses this pattern. | This file creates the A1 durable ledger. |
| `docs/reports/A1-MACRO-REVIEW-REPORT.md` | Current 55-module A1 score table; generated 2026-04-04. | Canonical score source for all current A1 modules. |
| `docs/reports/a1_reviews/` | 39 individual older review files, all with 10/10 scores, mostly older 44-module naming. | Supporting legacy evidence only; not a complete current 55-module ledger. |
| `docs/status/A1-STATUS.md` | Older deterministic 44-module status; 44 passing, 0 failing, 0 stubs; generated 2026-02-25. | Historical deterministic evidence only; not mapped to the current 55-module source tree. |
| `curriculum/l2-uk-en/A1/status/*.json` | No status directory exists in this checkout. | No generated status files were created or committed. |
| `curriculum/l2-uk-en/A1/audit/*-plan-review.md` | Seven local plan-review artifacts for early A1 modules. | Not used as LLM/content-review score evidence and not changed. |

## Normalization Rules

`LLM score` is the calculated content-review score from
`docs/reports/A1-MACRO-REVIEW-REPORT.md` Appendix B.

`Deterministic status` is kept separate from the LLM score. The current 55-module
source tree has no persisted deterministic PASS/FAIL status directory in this
checkout. The older `docs/status/A1-STATUS.md` status doc is recorded only as
historical evidence for the previous 44-module layout.

`Human-review readiness` is marked `ready` for scores 8/10 or above and
`targeted review first` for the two 7/10 modules. This is a score-ledger
classification, not a fresh pedagogical review.

## Current A1 Score Ledger

| Module | LLM score | Review round | Deterministic status | Human-review readiness | Evidence |
| --- | ---: | --- | --- | --- | --- |
| M01 `sounds-letters-and-hello` | 9/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M02 `reading-ukrainian` | 10/10 | r9 | not currently persisted | ready | A1 macro report Appendix B |
| M03 `special-signs` | 8/10 | r5 | not currently persisted | ready | A1 macro report Appendix B |
| M04 `stress-and-melody` | 9/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M05 `who-am-i` | 10/10 | r7 | not currently persisted | ready | A1 macro report Appendix B |
| M06 `my-family` | 10/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M07 `checkpoint-first-contact` | 9/10 | r7 | not currently persisted | ready | A1 macro report Appendix B |
| M08 `things-have-gender` | 9/10 | r5 | not currently persisted | ready | A1 macro report Appendix B |
| M09 `what-is-it-like` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M10 `colors` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M11 `how-many` | 9/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M12 `this-and-that` | 9/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M13 `many-things` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M14 `checkpoint-my-world` | 9/10 | r1 | not currently persisted | ready | A1 macro report Appendix B |
| M15 `what-i-like` | 9/10 | r5 | not currently persisted | ready | A1 macro report Appendix B |
| M16 `verbs-group-one` | 8/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M17 `verbs-group-two` | 8/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M18 `i-want-i-can` | 8/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M19 `questions` | 8/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M20 `my-morning` | 9/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M21 `checkpoint-actions` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M22 `what-time` | 10/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M23 `days-and-months` | 7/10 | r2 | not currently persisted | targeted review first | A1 macro report Appendix B |
| M24 `weather` | 8/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M25 `my-day` | 9/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M26 `free-time` | 10/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M27 `checkpoint-time-nature` | 10/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M28 `euphony` | 7/10 | r4 | not currently persisted | targeted review first | A1 macro report Appendix B |
| M29 `where-is-it` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M30 `my-city` | 9/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M31 `where-to` | 9/10 | r1 | not currently persisted | ready | A1 macro report Appendix B |
| M32 `transport` | 8/10 | r1 | not currently persisted | ready | A1 macro report Appendix B |
| M33 `around-the-city` | 10/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M34 `where-from` | 9/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M35 `checkpoint-places` | 10/10 | r5 | not currently persisted | ready | A1 macro report Appendix B |
| M36 `food-and-drink` | 9/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M37 `i-eat-i-drink` | 9/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M38 `at-the-cafe` | 10/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M39 `shopping` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M40 `people-around-me` | 10/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M41 `checkpoint-food-shopping` | 9/10 | r4 | not currently persisted | ready | A1 macro report Appendix B |
| M42 `hey-friend` | 8/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M43 `please-do-this` | 10/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M44 `linking-ideas` | 9/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M45 `when-and-where` | 9/10 | r1 | not currently persisted | ready | A1 macro report Appendix B |
| M46 `holidays` | 9/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M47 `checkpoint-communication` | 10/10 | r5 | not currently persisted | ready | A1 macro report Appendix B |
| M48 `what-happened` | 9/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M49 `yesterday` | 10/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M50 `what-will-happen` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M51 `my-plans` | 10/10 | r3 | not currently persisted | ready | A1 macro report Appendix B |
| M52 `my-story` | 8/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M53 `health` | 10/10 | r1 | not currently persisted | ready | A1 macro report Appendix B |
| M54 `emergencies` | 10/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |
| M55 `a1-finale` | 8/10 | r2 | not currently persisted | ready | A1 macro report Appendix B |

## Historical Deterministic Status

`docs/status/A1-STATUS.md` says it was generated on 2026-02-25 and reports
44 passing modules, 0 failing modules, and 0 stubs. Its slug set is the older
44-module A1 layout, so this ledger does not treat it as current deterministic
status for the 55-module source tree.

## Missing Or Unscored Modules

No current A1 module is missing from the normalized LLM score ledger. No current
A1 module is LLM-unscored. The missing artifact is a current deterministic
PASS/FAIL status ledger for the 55-module layout; this report intentionally does
not generate one.

## Follow-Up

1. Run the repo-approved deterministic A1 status/audit workflow separately if a
   current 55-module PASS/FAIL status ledger is needed.
2. Prioritize targeted content review before human-ready signoff for
   `days-and-months` and `euphony`.
