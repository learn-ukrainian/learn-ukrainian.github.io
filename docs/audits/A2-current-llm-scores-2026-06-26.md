# A2 Current LLM Scores

**Date:** 2026-06-26
**Branch:** `codex/A2-llm-score-ledger`
**Scope:** A2 only
**Purpose:** Create a durable score ledger for current A2 modules without
inventing LLM/content-review scores.

## Verdict

A2 now has a durable score ledger, but it does not yet have persisted
LLM/content-review scores. All 69 current A2 modules are marked
`not yet calculated`.

The only prior A2 status evidence found is deterministic and stale:
`docs/status/A2-STATUS.md` was generated on 2026-02-25 for an older 71-module
A2 layout. It is useful historical evidence, but it is not a current LLM score
source and cannot be promoted to human-review readiness.

## Current Counts

Current module scope comes from `curriculum/l2-uk-en/curriculum.yaml`.
The 69 manifest slugs exactly match both:

- `curriculum/l2-uk-en/A2/*/module.md`
- `curriculum/l2-uk-en/plans/A2/*.yaml`

| Measure | Count | Notes |
| --- | ---: | --- |
| Current A2 modules in source tree | 69 | Manifest, plan YAML, and module files match. |
| Modules with persisted LLM/content-review score | 0 | No A2 score source was found. |
| Current unscored modules | 69 | Every current A2 module is `not yet calculated`. |
| Current deterministic PASS-only modules | 0 | No current `curriculum/l2-uk-en/A2/status/*.json` files exist. |
| Current deterministic FAIL/problem modules | 0 | No current generated deterministic status files exist. |
| Human-review ready by LLM score | 0 | Readiness is not established without score evidence. |
| Historical deterministic PASS-only entries | 37 | From stale `docs/status/A2-STATUS.md`, generated 2026-02-25. |
| Historical deterministic PROSE-only entries | 33 | From stale `docs/status/A2-STATUS.md`, generated 2026-02-25. |
| Historical deterministic FAIL/problem entries | 1 | `checkpoint-cases`, structure issue in stale status doc. |

## Evidence Inventory

| Evidence location | Finding | Use in this ledger |
| --- | --- | --- |
| `docs/audits/*score*` | A1 and B2 score ledgers exist; no A2 score ledger existed before this file. | This file creates the A2 durable ledger. |
| `docs/reports/` | No A2 macro-review, content-review, or score ledger found. A2 mentions are incidental reports, vocabulary audits, or older GitHub comments. | Not used as score evidence. |
| `docs/status/A2-STATUS.md` | Historical deterministic status doc: 71 modules, 37 passing, 33 prose-only, 1 failing, generated 2026-02-25. | Historical deterministic evidence only. |
| `curriculum/l2-uk-en/A2/` | Current source has 69 module files. No local `status/`, `audit/`, `review/`, or `orchestration/` score artifacts were found. | Current module scope only. |
| `curriculum/l2-uk-en/plans/A2/` | 69 plan YAML files, matching the manifest and module files. | Current module scope only. |

No repo-approved A2 content-review score sweep was run in this PR. The task is
score persistence and normalization; running a first-time 69-module LLM scoring
sweep would create new subjective review data rather than normalize existing
evidence.

## Historical Status Overlap

Only five current A2 slugs also appear in the stale 2026-02-25 deterministic
status doc. These entries are not current LLM scores.

| Current module | Historical deterministic status | Historical words | Historical issues | Normalized LLM score |
| --- | --- | ---: | --- | --- |
| `dative-verbs` | PASS | 3452/3000 | - | not yet calculated |
| `all-cases-practice` | PASS | 3132/3000 | - | not yet calculated |
| `checkpoint-cases` | FAIL | 2573/2500 | structure | not yet calculated |
| `preferences-and-choices` | PASS | 4071/3000 | - | not yet calculated |
| `because-and-although` | PROSE-only | 4528/3000 | - | not yet calculated |

## Current Unscored Modules

All current modules below have LLM/content-review score `not yet calculated`.
Human-review readiness is not established by this ledger.

| Phase | Range | Modules |
| --- | --- | --- |
| A2.1 | M01-M08 | `a2-bridge`, `aspect-concept`, `aspect-in-vocabulary`, `liudyna-i-stosunky`, `genitive-intro`, `genitive-dates-numbers`, `foundations-practice`, `checkpoint-foundations` |
| A2.2 | M09-M16 | `genitive-prepositions-source`, `genitive-prepositions-purpose`, `genitive-prepositions-direction`, `euphony-advanced`, `genitive-adjectives-pronouns`, `genitive-plural`, `shopping-and-health`, `checkpoint-genitive` |
| A2.3 | M17-M23 | `dative-pronouns`, `dative-nouns`, `dative-adjectives-pronouns`, `locative-expanded`, `dative-verbs`, `services-and-communication`, `checkpoint-dative` |
| A2.4 | M24-M31 | `instrumental-accompaniment`, `instrumental-means`, `instrumental-profession`, `vocative-expanded`, `instrumental-prepositions`, `instrumental-adjectives-pronouns`, `work-and-food`, `checkpoint-instrumental` |
| A2.5 | M32-M39 | `plural-nominative-accusative`, `plural-genitive`, `plural-other-cases`, `dozvillia-i-khobi`, `which-case-when`, `all-cases-practice`, `home-and-daily-life`, `checkpoint-cases` |
| A2.6 | M40-M46 | `aspect-in-past`, `synthetic-future`, `aspect-mastery`, `motion-verbs`, `imperative-complete`, `telling-stories-and-travel`, `checkpoint-verbs` |
| A2.7 | M47-M53 | `because-and-although`, `purpose-clauses`, `relative-clauses`, `word-order-emphasis`, `real-conditionals`, `education-and-work`, `checkpoint-syntax` |
| A2.8 | M54-M60 | `comparison`, `numerals-and-cases`, `sviy-and-sebe`, `indefinite-negative-pronouns`, `synonyms-antonyms-style`, `preferences-and-choices`, `nature-and-traditions` |
| A2.9 | M61-M66 | `metalanguage-words-and-cases`, `metalanguage-verbs-and-time`, `metalanguage-sentences-and-classroom`, `metalanguage-phonetics`, `metalanguage-morphology`, `metalanguage-syntax-cases` |
| A2.10 | M67-M69 | `a2-comprehensive-review`, `a2-practice-exam`, `a2-finale` |

## Normalization Rules Used

- A numeric LLM/content-review score is recorded only when a persisted score
  source exists.
- Deterministic PASS/FAIL/PROSE status is not converted to a numeric LLM score.
- A stale deterministic status doc is cited as historical evidence, not current
  readiness evidence.
- Human-review readiness requires current score evidence or an explicit current
  review finding; neither exists for A2 in this checkout.
