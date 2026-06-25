# B2 Current LLM Scores

Date: 2026-06-25
Auditor: codex/gpt-5.5
Branch: `codex/b2-m16-m21-scores`
Scope: active B2 preview modules on `origin/main` after PR #3841 merged.

This durable score note supersedes `docs/audits/b2-current-llm-scores-2026-06-24.md` and earlier 2026-06-25 snapshots. It intentionally does not persist generated files under `curriculum/l2-uk-en/**/status/`, `curriculum/l2-uk-en/**/audit/`, or `curriculum/l2-uk-en/**/review/`.

## Summary

| Module | Current LLM Score | Verdict | Ready for Human Review? | Notes |
| --- | ---: | --- | --- | --- |
| B2 M01 `passive-voice-system` | 10/10 | A | Yes | Excellent B2 teaching arc, strong register control, no content blockers. Score carried forward from the 2026-06-24 durable score note. |
| B2 M02 `past-passive-participles` | 9/10 | B+ | Yes | Strong teaching arc and practice coverage. Score carried forward from the 2026-06-24 durable score note; optional activity-affordance/notation polish remains. |
| B2 M03 `b2-impersonal-passive` | 9/10 | B+ | Yes | Strong impersonal passive module after review fixes. Score held at 9 for non-blocking section-balance/formulaic-style audit notes. |
| B2 M04 `dim-zhytlo` | 9/10 | B+ | Yes | Strong housing/rental/repair communication module. Minor optional polish remains around section balance and deterministic UA-GEC false positives. |
| B2 M05 `reflexive-passive` | 9/10 | B+ | Yes | Strong reflexive-passive norm module. Review blocker on essay exemplar length was fixed before merge; residual audit notes are minor. |
| B2 M06 `third-person-plural-passive` | 9/10 | B+ | Yes | Strong 3rd-person-plural passive-alternative module. Dead/fabricated resource fallback was removed before merge; score held at 9 for section-balance warnings. |
| B2 M07 `passive-in-context` | 9/10 | B+ | Yes | Strong synthesis/context module. Review notes on worked-example coherence and exemplar length were fixed before merge; minor section-balance/resource notes remain. |
| B2 M08 `pobut-shchodenne` | 10/10 | A | Yes | Excellent everyday-life module with strong activity coverage, natural Ukrainian household negotiation, and no meaningful content blockers. |
| B2 M09 `active-participles-present` | 9/10 | B+ | Yes | Strong editorial grammar module. Score held at 9 because section balance remains uneven and deterministic audit still emits false-positive naturalness warnings. |
| B2 M10 `checkpoint-passive-voice` | 9/10 | B+ | Yes | High-quality passive-voice checkpoint. Score held at 9 for non-blocking collocation/translate-position/resource-polish notes. |
| B2 M11 `active-participles-past` | 9/10 | B+ | Yes | Strong advanced participle module after review fixes. Score held at 9 for normal post-build polish risk. |
| B2 M12 `participles-vs-relative-clauses` | 9/10 | B+ | Yes | Strong contrast module for participles and relative clauses. Review blocker on a padded quiz was fixed; score held at 9 for minor polish risk. |
| B2 M13 `zdorovya-i-medytsyna` | 9/10 | B+ | Yes | Strong health/medicine communication module after factual wording fixes. Score held at 9 for residual deterministic advisory warnings. |
| B2 M14 `phrases-word-combinations` | 8/10 | B | Yes | Useful collocation and word-combination module after MDX and collocation blockers were fixed. Score held at 8 because cleanup required multiple passes and residual polish risk is higher. |
| B2 M15 `predicate-types` | 9/10 | B+ | Yes | Strong predicate-types module after render and activity consistency fixes. Score held at 9 for residual section-balance and deterministic advisory warnings. |
| B2 M16 `secondary-sentence-members` | 9/10 | B+ | Yes | Strong grammar-production module. Independent review blocker was stale-base MDX drift only; follow-up review found no blockers. |
| B2 M17 `sport-i-dozvillia` | 9/10 | B+ | Yes | Strong sport and leisure communication module with validated activity and vocabulary coverage. Independent review passed with no blockers. |
| B2 M18 `b2-one-member-sentences` | 9/10 | B+ | Yes | Strong one-member sentence module with 100% immersion and 96% richness. Independent review found no merge-blocking issues. |
| B2 M19 `homogeneous-members` | 9/10 | B+ | Yes | Strong homogeneous-members syntax module with 100% immersion and 96% richness. Independent review passed with no blockers. |
| B2 M20 `detached-members` | 9/10 | B+ | Yes | Strong detached-members module; audit passed at 4107/4000 words with 96% richness and 100% immersion. Independent review found no blockers. |
| B2 M21 `checkpoint-syntax-i` | 9/10 | B+ | Yes | Strong B2.1 syntax checkpoint; audit passed with 100% immersion and 99% richness. Score held at 9 for compact checkpoint scope and non-blocking section-balance warnings. |

Current average across M01-M21: 9.0/10.

## Score Distribution

| Score | Count | Modules |
| ---: | ---: | --- |
| 10/10 | 2 | M01, M08 |
| 9/10 | 18 | M02-M07, M09-M13, M15-M21 |
| 8/10 | 1 | M14 |

## Batch Reports

| Scope | Durable Report |
| --- | --- |
| M03-M10 | `docs/audits/b2-m03-m10-llm-score-report-2026-06-25.md` |
| M11-M15 | `docs/audits/b2-m11-m15-llm-score-report-2026-06-25.md` |
| M16-M21 | `docs/audits/b2-m16-m21-llm-score-report-2026-06-25.md` |

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
| M11 `active-participles-past` | 4736 | 11 workbook / 0 inline | 30 |
| M12 `participles-vs-relative-clauses` | 4383 | 10 workbook / 0 inline | 45 |
| M13 `zdorovya-i-medytsyna` | 4123 | 10 workbook / 0 inline | 40 |
| M14 `phrases-word-combinations` | 5696 | 11 workbook / 5 inline | 42 |
| M15 `predicate-types` | 5645 | 10 workbook / 5 inline | 32 |
| M16 `secondary-sentence-members` | 5396 | 12 workbook / 0 inline | 32 |
| M17 `sport-i-dozvillia` | 4153 | 10 workbook / 0 inline | 32 |
| M18 `b2-one-member-sentences` | 4430 | 10 workbook / 0 inline | 32 |
| M19 `homogeneous-members` | 4569 | 10 workbook / 0 inline | 32 |
| M20 `detached-members` | 4267 | 11 workbook / 0 inline | 32 |
| M21 `checkpoint-syntax-i` | 4334 | 10 workbook / 0 inline | 20 |

## Scoring Method

B2 uses the Tier 2 Core rubric. The LLM score here is the content-review `Lesson Quality Score`, grounded in the Tier 2 "Did I Learn?" test:

| Pass Count | Score |
| ---: | ---: |
| 5/5 with no meaningful content polish | 10/10 |
| 5/5 with non-blocking polish or unevenness | 9/10 |
| 4/5 | 8/10 |
| 3/5 | 7/10 |
| 0-2/5 | 6/10 or lower |

All M01-M21 modules are active, audit-passing, independently reviewed where applicable, and ready for human review in B2 preview. Scores below 10 reflect non-blocking polish, section-balance warnings, review notes, or conservative checkpoint scoring, not deployment blockers.

## Review Evidence

| Scope | Independent Review Evidence |
| --- | --- |
| M03-M10 | See `docs/audits/b2-m03-m10-llm-score-report-2026-06-25.md`. |
| M11-M15 | See `docs/audits/b2-m11-m15-llm-score-report-2026-06-25.md`. |
| M16-M21 | See `docs/audits/b2-m16-m21-llm-score-report-2026-06-25.md`. |

## Artifact Hygiene

- No generated `curriculum/l2-uk-en/**/status/*.json` files persisted.
- No generated `curriculum/l2-uk-en/**/audit/*-review.md` or `review/*-review.md` files persisted.
- No telemetry database files persisted.
- `.python-version`, `.yamllint`, and `.markdownlint.json` unchanged.
