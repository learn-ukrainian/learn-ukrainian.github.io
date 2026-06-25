# B2 M11-M15 LLM Score Report

Date: 2026-06-25

Scope: B2 production batch M11-M15 after merge to `main`.

Preflight basis: `docs/audits/b2-preflight-readiness-remediation-2026-06-22.md`.

## Score Summary

| Score | Module | Activity/Vocab Coverage | Deterministic Audit | Ready for Human Review? | Verdict |
| --- | --- | --- | --- | --- | --- |
| 9/10 | M11 `active-participles-past` | 11 workbook / 0 inline; 30 vocab | PASS | Yes | B+ |
| 9/10 | M12 `participles-vs-relative-clauses` | 10 workbook / 0 inline; 45 vocab | PASS | Yes | B+ |
| 9/10 | M13 `zdorovya-i-medytsyna` | 10 workbook / 0 inline; 40 vocab | PASS | Yes | B+ |
| 8/10 | M14 `phrases-word-combinations` | 11 workbook / 5 inline; 42 vocab | PASS | Yes | B |
| 9/10 | M15 `predicate-types` | 10 workbook / 5 inline; 32 vocab | PASS | Yes | B+ |

Average score: 8.8/10.

## Notes

| Module | Notes |
| --- | --- |
| M11 `active-participles-past` | Strong advanced participle module after review fix. Corrected the impossible `пожовтіти -> пожовклий` pairing to `пожовкнути -> пожовклий` and repaired `листя само` to `листя саме`. Score held at 9 for normal post-build polish risk. |
| M12 `participles-vs-relative-clauses` | Strong contrast module for participles and relative clauses. Review blocker on a padded quiz was fixed by varying the items. Score held at 9 for minor polish risk rather than content blockers. |
| M13 `zdorovya-i-medytsyna` | Strong health/medicine communication module after factual wording fixes. Removed the false `оскільки` calque label and corrected the `доктор`/`лікар` degree/profession contrast. Score held at 9 for residual deterministic advisory warnings. |
| M14 `phrases-word-combinations` | Broad, useful collocation and word-combination module. Initial review blockers around MDX callout rendering and `багате прикладами` were fixed, and Astro build passed after remediation. Score held at 8 because residual deterministic naturalness advisories remain significant and the rendered-callout blocker required multiple cleanup passes. |
| M15 `predicate-types` | Strong predicate-types module after render and activity consistency fixes. Corrected MDX callout rendering, changed `Рішення є ____` to require `чинним`, and clarified the majority-agreement correction. Score held at 9 for residual section-balance and deterministic advisory warnings. |

## Raw Counts

| Module | Raw Word Count | Vocabulary | Activities |
| --- | ---: | ---: | --- |
| M11 `active-participles-past` | 4736 | 30 | 11 workbook / 0 inline |
| M12 `participles-vs-relative-clauses` | 4383 | 45 | 10 workbook / 0 inline |
| M13 `zdorovya-i-medytsyna` | 4123 | 40 | 10 workbook / 0 inline |
| M14 `phrases-word-combinations` | 5696 | 42 | 11 workbook / 5 inline |
| M15 `predicate-types` | 5645 | 32 | 10 workbook / 5 inline |

## Independent Review

| Reviewer | Module | Result |
| --- | --- | --- |
| Claude Opus 4.8 blocker review + re-review | M11 `active-participles-past` | Initial blocker fixed; final disposition mergeable. |
| Claude Opus 4.8 blocker review + re-review | M12 `participles-vs-relative-clauses` | Initial quiz-padding blocker fixed; final disposition mergeable. |
| Claude Opus 4.8 blocker review + final re-review | M13 `zdorovya-i-medytsyna` | `оскільки` and `доктор`/`лікар` blockers fixed; final disposition mergeable. |
| Claude Opus 4.8 blocker review + final re-review | M14 `phrases-word-combinations` | MDX callout rendering and collocation blockers fixed; final disposition mergeable. |
| Claude Opus 4.8 blocker review + final re-review | M15 `predicate-types` | MDX callout rendering and activity contradiction blockers fixed; final disposition mergeable. |

## Merge And Telemetry

| Module | PR | Merge Commit | Telemetry Run |
| --- | --- | --- | --- |
| M11 `active-participles-past` | #3820 | `15450925bcb325c72dbad38131994db251a8731f` | `b2-m11-active-participles-past-pr3820` |
| M12 `participles-vs-relative-clauses` | #3821 | `4fe3ce501d27b78165601f0fc3461e6e2cc1df1a` | `b2-m12-participles-vs-relative-clauses-pr3821` |
| M13 `zdorovya-i-medytsyna` | #3823 | `6afaae0a9e6f94a8b1406a0d0c50e790153eb632` | `b2-m13-zdorovya-i-medytsyna-pr3823` |
| M14 `phrases-word-combinations` | #3825 | `36f51a268735570bcce3bde6185f077b91edcee5` | `b2-m14-phrases-word-combinations-pr3825` |
| M15 `predicate-types` | #3826 | `0efa556e55919abba9ea886904122a8a681da4e4` | `b2-m15-predicate-types-pr3826` |

All five telemetry records were persisted with `status: merged`, `swarm_used: true`, `swarm_label: thin`, and `token_source: unavailable`.

Forbidden generated artifacts included in the module PRs: no.
