# B1 Current LLM Scores

**Date:** 2026-06-26
**Branch:** `codex/B1-llm-score-ledger`
**Scope:** `curriculum/l2-uk-en/B1/` and `curriculum/l2-uk-en/plans/b1/`
**Purpose:** Create a durable score ledger for current B1 modules without
building modules, remediating content, or inventing scores.

## Summary

B1 now has a durable score ledger, but it does not yet have persisted
per-module LLM/content-review scores for the current 94-module source tree. All
current B1 modules are therefore recorded as `not yet calculated`.

The current source tree has 94 module files and 94 plan YAML files with matching
slugs. No current generated `status/`, curriculum `audit/`, curriculum
`review/`, or orchestration score artifacts were found under
`curriculum/l2-uk-en/B1/`.

`docs/status/B1-STATUS.md` is historical deterministic context, not a current
module status source. Its 94 rows use an older B1 slug set: only
`aspect-in-imperatives` overlaps the current 94 source slugs. Its PASS/PROSE/FAIL
counts are recorded below as stale context only and are not converted into
current score or readiness evidence.

## Current Counts

| Count | Measure | Notes |
| --- | --- | --- |
| 94 | Current B1 modules in source tree | `module.md` files and plan YAML files match exactly. |
| 0 | Modules with normalized LLM/content-review score | No current score source was found. |
| 94 | Current unscored modules | Every current B1 module is `not yet calculated`. |
| 0 | Current deterministic PASS-only modules | No current generated B1 status artifacts exist. |
| 0 | Current deterministic FAIL/problem modules | No current generated B1 status artifacts exist. |
| 0 | Human-review ready by LLM score | Readiness is not established without score evidence. |
| 94 | Human-review readiness not established | All current modules require future scoring or review evidence. |
| 5 | Historical deterministic PASS-only entries | From stale `docs/status/B1-STATUS.md`; not current source evidence. |
| 81 | Historical deterministic PROSE-only entries | From stale `docs/status/B1-STATUS.md`; not current source evidence. |
| 8 | Historical deterministic FAIL/problem entries | 6 FAIL plus 2 MISSING in stale `docs/status/B1-STATUS.md`. |

## Evidence Inventory

| Finding | Evidence location | Use in this ledger |
| --- | --- | --- |
| A1, A2, and B2 score ledgers exist; no B1 score ledger existed before this file. | `docs/audits/*score*` | This file creates the B1 durable ledger. |
| No B1 macro-review, content-review score table, or score ledger was found. B1 docs are plan/status/process notes, not per-module score evidence. | `docs/reports/` | Not used as score evidence. |
| Historical deterministic table has 94 rows: 5 PASS, 81 PROSE, 6 FAIL, 2 MISSING. It matches only 1 current source slug. | `docs/status/B1-STATUS.md` | Historical deterministic context only. |
| Historical project memory says 23/92 passing and mentions a non-module `8.45/10` improvement score. Current B1 is 94 modules, so this is stale context. | `docs/status/CURRENT-STATUS.md` | Not used as current per-module score evidence. |
| Current B1 has 94 module files, 94 matching plan YAML files, and no generated status/review/audit/orchestration score artifacts. | `curriculum/l2-uk-en/B1/`, `curriculum/l2-uk-en/plans/b1/` | Current module scope only. |

## Score State

| LLM/content-review score | Current modules | Human-review readiness |
| --- | --- | --- |
| `not yet calculated` | 94 | Not established. |
| Numeric score persisted | 0 | None. |

Deterministic PASS/FAIL/PROSE status is not converted to a numeric LLM score.
The stale status table is also not current enough to establish deterministic
status for the current module set.

## Current Module Scope

All modules in this table have LLM/content-review score
`not yet calculated`, deterministic status `not available in current artifacts`,
and human-review readiness `not established`.

| Range | Group | Modules |
| --- | --- | --- |
| M01-M10 | B1.0 | `b1-baseline-past-present`, `b1-baseline-future-aspect`, `people-and-relationships`, `aspect-past-tense`, `aspect-future-tense`, `aspect-in-narration`, `daily-life-and-routines`, `aspect-in-negation`, `work-and-career`, `checkpoint-aspect` |
| M11-M21 | B1.1 | `alternation-vowels`, `alternation-consonants-nouns`, `alternation-consonants-verbs`, `health-at-the-doctor`, `simplification-consonants`, `noun-subclasses-masculine`, `noun-subclasses-hissing`, `restaurant-and-food`, `noun-subclasses-feminine`, `pluralia-tantum`, `checkpoint-morphophonemics` |
| M22-M33 | B1.2 | `conditionals-real`, `conditionals-unreal`, `aspect-in-conditionals`, `shopping-and-services`, `imperative-nuances`, `aspect-in-imperatives`, `reflexive-verbs-nuances`, `housing-and-renting`, `passive-voice-intro`, `verbal-nouns`, `verb-formation-suffixes`, `checkpoint-verbs` |
| M34-M43 | B1.3 | `prepositions-spatial-review`, `motion-base-review`, `motion-prefixes-arrival`, `traveling-ukraine`, `motion-prefixes-departure`, `motion-prefixes-in-out`, `motion-prefixes-transit`, `motion-flight-swim`, `figurative-motion`, `checkpoint-motion` |
| M44-M54 | B1.4 | `adjectives-comparative`, `adjectives-superlative`, `adverbs-comparison-formation`, `nature-and-environment`, `word-formation-adjectives`, `possessive-adjectives`, `word-formation-nouns`, `checkpoint-comparison`, `homogeneous-members`, `genitive-nuances`, `dative-nuances` |
| M55-M64 | B1.5 | `education-and-university`, `instrumental-nuances`, `vocative-formal`, `prepositions-temporal`, `places-and-locations`, `prepositions-cause-purpose`, `cases-with-ordinal-numerals`, `cases-with-quantity-expressions`, `advanced-pronouns`, `checkpoint-cases` |
| M65-M74 | B1.6 | `participles-active`, `participles-passive`, `participle-phrases`, `leisure-culture-festivals`, `short-form-adjectives`, `gerunds-imperfective`, `gerunds-perfective`, `gerund-phrases`, `society-and-media`, `checkpoint-participles` |
| M75-M84 | B1.7 | `complex-compound`, `complex-subordinate-object`, `complex-subordinate-relative`, `complex-subordinate-time`, `complex-subordinate-reason`, `complex-subordinate-condition`, `complex-subordinate-purpose`, `complex-subordinate-concess`, `reported-speech`, `checkpoint-syntax` |
| M85-M90 | B1.8 | `text-register-formal`, `text-register-informal`, `text-compression`, `reading-literature`, `introductory-words`, `checkpoint-text-register` |
| M91-M94 | B1.9 | `narrative-mastery`, `debate-and-opinion`, `comprehensive-b1-review`, `practice-exam` |

## Historical Deterministic Context

The following problem rows are from stale `docs/status/B1-STATUS.md` and are not
current B1 source-tree evidence.

| Historical row | Slug | Historical status | Issues |
| --- | --- | --- | --- |
| 020 | `motion-approaching-departing` | FAIL | 5 Outline Compliance Errors |
| 080 | `active-lifestyle` | FAIL | `word_count`, `activities`, `structure` |
| 081 | `running-in-ukraine` | FAIL | `word_count`, `activities`, `structure` |
| 084 | `winter-sports` | FAIL | `activities`, `structure` |
| 085 | `ukrainian-cuisine` | MISSING | `no_file` |
| 086 | `ukrainski-sviata-ta-festyvali` | MISSING | `no_file` |
| 093 | `phonetics-assimilation` | FAIL | `word_count`, `activities`, `structure` |
| 094 | `b1-final-exam` | FAIL | `activities`, `structure` |

## Interpretation Rules

- `not yet calculated` means no durable numeric LLM/content-review score was
  found for the current module.
- Deterministic audit status means only status emitted by a current deterministic
  audit artifact. B1 has no current generated status artifact in this checkout.
- Human-review readiness requires current score evidence or an explicit current
  review signoff. B1 has neither in the inspected evidence.
- The historical status page remains useful for archaeology, but its stale slug
  set prevents using it as current B1 pass/fail evidence.

## Next Needed Evidence

To turn this ledger into scored records, run the repo-approved content-review or
LLM-QG scoring workflow on current B1 modules and persist the resulting per-module
scores in a durable `docs/audits/` report. Do not infer scores from deterministic
PASS/FAIL/PROSE labels.
