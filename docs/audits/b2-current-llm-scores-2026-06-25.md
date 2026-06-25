# B2 Current LLM Scores

Date: 2026-06-25
Auditor: codex/gpt-5
Branch: `codex/b2-m03-m10-llm-scores`
Scope: active B2 preview modules on `origin/main` after PRs #3812, #3813, #3814, #3815, and #3817 merged.

This durable score note supersedes `docs/audits/b2-current-llm-scores-2026-06-24.md` and the earlier 2026-06-25 M04/M08/M09-only snapshot. It intentionally does not persist generated files under `curriculum/l2-uk-en/**/status/`, `curriculum/l2-uk-en/**/audit/`, or `curriculum/l2-uk-en/**/review/`.

## Summary

| Module | Current LLM Score | Verdict | Ready for Human Review? | Notes |
| --- | ---: | --- | --- | --- |
| B2 M01 `passive-voice-system` | 10/10 | A | Yes | Excellent B2 teaching arc, strong register control, no content blockers. Score carried forward from the 2026-06-24 durable score note. |
| B2 M02 `past-passive-participles` | 9/10 | B+ | Yes | Strong teaching arc and practice coverage. Score carried forward from the 2026-06-24 durable score note; optional activity-affordance/notation polish remains. |
| B2 M03 `b2-impersonal-passive` | 9/10 | B+ | Yes | Strong impersonal passive module after review fixes. Score held at 9 for non-blocking section-balance/formulaic-style audit notes. |
| B2 M04 `dim-zhytlo` | 9/10 | B+ | Yes | Strong housing/rental/repair communication module. Minor optional polish remains around section balance and a deterministic UA-GEC false-positive family. |
| B2 M05 `reflexive-passive` | 9/10 | B+ | Yes | Strong reflexive-passive norm module. Review blocker on essay exemplar length was fixed before merge; residual audit notes are minor. |
| B2 M06 `third-person-plural-passive` | 9/10 | B+ | Yes | Strong 3rd-person-plural passive-alternative module. Dead/fabricated resource fallback was removed before merge; score held at 9 for section-balance warnings. |
| B2 M07 `passive-in-context` | 9/10 | B+ | Yes | Strong synthesis/context module. Review notes on worked-example coherence and exemplar length were fixed before merge; minor section-balance/resource notes remain. |
| B2 M08 `pobut-shchodenne` | 10/10 | A | Yes | Excellent everyday-life module with strong activity coverage, natural Ukrainian household negotiation, and no meaningful content blockers. |
| B2 M09 `active-participles-present` | 9/10 | B+ | Yes | Strong editorial grammar module. Score held at 9 because section balance remains uneven and deterministic audit still emits false-positive naturalness warnings. |
| B2 M10 `checkpoint-passive-voice` | 9/10 | B+ | Yes | High-quality passive-voice checkpoint. Score held at 9 for non-blocking collocation/translate-position/resource-polish notes. |

## M03-M10 Report

| Module | Score | Grade | Deterministic Audit | Activity/Vocab Coverage | Independent Review | Disposition |
| --- | ---: | --- | --- | --- | --- | --- |
| M03 `b2-impersonal-passive` | 9/10 | B+ | PASS | 7 workbook / 4 inline; 35 vocab | PR #3812 Claude Opus 4.8 | Initial blockers fixed; mergeable; merged. |
| M04 `dim-zhytlo` | 9/10 | B+ | PASS | 10 workbook / 0 inline; 94 vocab | PR #3803 Claude Opus 4.8 | Mergeable; one wording nit fixed before merge. |
| M05 `reflexive-passive` | 9/10 | B+ | PASS | 11 workbook / 0 inline; 34 vocab | PR #3813 Claude Opus 4.8 | Essay model-answer blocker fixed; mergeable; merged. |
| M06 `third-person-plural-passive` | 9/10 | B+ | PASS | 11 workbook / 0 inline; 43 vocab | PR #3814 Claude Opus 4.8 | Dead/fabricated resource link fixed; mergeable; merged. |
| M07 `passive-in-context` | 9/10 | B+ | PASS | 10 workbook / 0 inline; 36 vocab | PR #3815 Claude Opus 4.8 | Non-blocking review notes fixed; mergeable; merged. |
| M08 `pobut-shchodenne` | 10/10 | A | PASS | 12 workbook / 0 inline; 55 vocab | PR #3801 Claude Opus 4.8 | Mergeable; no blockers. |
| M09 `active-participles-present` | 9/10 | B+ | PASS | 10 workbook / 0 inline; 40 vocab | PR #3805 Claude Opus 4.8 | Mergeable; one morphology-table nit fixed before merge. |
| M10 `checkpoint-passive-voice` | 9/10 | B+ | PASS | 5 workbook / 5 inline; 30 vocab | PR #3817 Claude Opus 4.8 | Mergeable; no blockers; non-blocking polish deferred. |

## Current Raw Stats

| Module | Raw Word Count | Activities | Vocabulary |
| --- | ---: | --- | ---: |
| M03 `b2-impersonal-passive` | 4608 | 7 workbook / 4 inline | 35 |
| M04 `dim-zhytlo` | 5224 | 10 workbook / 0 inline | 94 |
| M05 `reflexive-passive` | 4422 | 11 workbook / 0 inline | 34 |
| M06 `third-person-plural-passive` | 4779 | 11 workbook / 0 inline | 43 |
| M07 `passive-in-context` | 4751 | 10 workbook / 0 inline | 36 |
| M08 `pobut-shchodenne` | 5047 | 12 workbook / 0 inline | 55 |
| M09 `active-participles-present` | 5428 | 10 workbook / 0 inline | 40 |
| M10 `checkpoint-passive-voice` | 4671 | 5 workbook / 5 inline | 30 |

## Scoring Method

B2 uses the Tier 2 Core rubric. The LLM score here is the content-review `Lesson Quality Score`, grounded in the Tier 2 "Did I Learn?" test:

| Pass Count | Score |
| ---: | ---: |
| 5/5 with no meaningful content polish | 10/10 |
| 5/5 with non-blocking polish or unevenness | 9/10 |
| 4/5 | 8/10 |
| 3/5 | 7/10 |
| 0-2/5 | 6/10 or lower |

All M03-M10 modules pass the five Tier 2 teaching checks. Scores below 10 reflect non-blocking polish, section-balance warnings, or review notes, not deployment blockers.

## Review Evidence

| Module | Independent Review | Result |
| --- | --- | --- |
| M03 `b2-impersonal-passive` | Claude Opus 4.8 PR #3812 blocker review + re-review | Initial blockers fixed; final disposition mergeable. |
| M04 `dim-zhytlo` | Claude Opus 4.8 PR #3803 blocker review | Mergeable, 0 blockers; one wording nit addressed before merge. |
| M05 `reflexive-passive` | Claude Opus 4.8 PR #3813 blocker review + final verdict | Initial essay-length blocker fixed; final disposition mergeable. |
| M06 `third-person-plural-passive` | Claude Opus 4.8 PR #3814 blocker review + re-review | Dead resource link blocker fixed; final disposition mergeable. |
| M07 `passive-in-context` | Claude Opus 4.8 PR #3815 blocker review + re-review | Mergeable; non-blocking exemplar/coherence notes fixed before merge. |
| M08 `pobut-shchodenne` | Claude Opus 4.8 PR #3801 blocker review | Mergeable, 0 blockers. |
| M09 `active-participles-present` | Claude Opus 4.8 PR #3805 blocker review | Mergeable, 0 blockers; one morphology-table nit addressed before merge. |
| M10 `checkpoint-passive-voice` | Claude Opus 4.8 PR #3817 blocker review | Mergeable, 0 blockers; non-blocking polish deferred. |

## Artifact Hygiene

- No generated `curriculum/l2-uk-en/**/status/*.json` files persisted.
- No generated `curriculum/l2-uk-en/**/audit/*-review.md` or `review/*-review.md` files persisted.
- No telemetry database files persisted.
- `.python-version`, `.yamllint`, and `.markdownlint.json` unchanged.
