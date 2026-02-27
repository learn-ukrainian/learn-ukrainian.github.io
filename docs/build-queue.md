# Shared Priority Build Queue

**Status**: ACTIVE
**Updated**: 2026-02-21
**Purpose**: Single source of truth for the immediate build order. Both Blue (Claude) and Yellow (Gemini) teams pull their next tasks from the top of this list. Do not work on modules not listed here without prior coordination.

## Rationale

Priority order: finish A1 (1 remaining) > fix failing A2 modules > expand A2 > parallel seminar tracks (HIST, BIO). Core levels are sequential (learners need them in order). Seminar tracks can run in parallel since they're independent.

## Current Priorities (Next 20 Targets)

| # | Track | Module (slug) | Phase | Assignee | Status | Notes |
|:--|:------|:-------------|:------|:---------|:-------|:------|
| 1 | `a1` | `a1-final-exam` | A-D | Yellow | Pending | Last A1 module — completes the level |
| 2 | `a2` | `the-dative-i-pronouns` | Fix | Yellow | Failing audit | Content exists, needs fixes to pass |
| 3 | `a2` | `the-dative-ii-nouns` | Fix | Yellow | Failing audit | Content exists, needs fixes to pass |
| 4 | `a2` | `dative-verbs` | Fix | Yellow | Failing audit | Content exists, needs fixes to pass |
| 5 | `a2` | `the-instrumental-i-accompaniment` | Fix | Yellow | Failing audit | Content exists, needs fixes to pass |
| 6 | `a2` | `the-instrumental-ii-means-and-tools` | A-D | Yellow | No status | Content may exist, needs audit |
| 7 | `a2` | `being-and-becoming` | Fix | Yellow | Failing audit | Content exists, needs fixes to pass |
| 8 | `a2` | `spatial-prepositions` | A-D | Yellow | Pending | Next A2 module in sequence |
| 9 | `a2` | `logical-prepositions` | A-D | Yellow | Pending | |
| 10 | `a2` | `all-cases-practice` | A-D | Yellow | Pending | |
| 11 | `a2` | `at-the-post-office-and-bank` | A-D | Yellow | Pending | |
| 12 | `a2` | `checkpoint-cases` | A-D | Yellow | Pending | Checkpoint — tests all case modules |
| 13 | `hist` | `zasnuvannia-kyieva` | A-D | Yellow | Pending | Seminar — parallel with A2 |
| 14 | `hist` | `khozary-i-sloviany` | A-D | Yellow | Pending | |
| 15 | `hist` | `syntez-vytoky-1` | A-D | Yellow | Pending | Synthesis module |
| 16 | `hist` | `oleh-ihor` | A-D | Yellow | Pending | |
| 17 | `bio` | `knyazhna-anna-yaroslavna` | A-D | Yellow | Pending | Seminar — parallel with HIST |
| 18 | `bio` | `volodymyr-monomakh` | A-D | Yellow | Pending | |
| 19 | `bio` | `nestor-litopysets` | A-D | Yellow | Pending | |
| 20 | `bio` | `roman-mstyslavych` | A-D | Yellow | Pending | |

## Handoff Contract Template

Before starting Phase A on any module, Yellow posts this on the assigned GitHub issue:

```
Track: {track}
Module: #{num} ({slug})
Plan: curriculum/l2-uk-en/plans/{level}/{slug}.yaml
Meta: curriculum/l2-uk-en/{level}/meta/{slug}.yaml
Research: curriculum/l2-uk-en/{level}/research/{slug}-research.md
Known constraints: [deviations from template, if any]
Priority dimensions: [which review dimensions matter most]
Key Facts Ledger: [included in research notes — Y/N]
```

Blue echoes back confirmation or flags mismatches before work begins.

## Workflow Rules

1. **Pull from top**: Work on the highest-priority available module in your phase.
2. **Fix before build**: Modules marked "Failing audit" should be fixed before building new ones in the same track.
3. **Batch limit**: Seminar tracks (HIST, BIO): max 2 modules per batch to prevent context exhaustion.
4. **Factual verification**: Seminar tracks require Key Facts Ledger in Phase A research. Phase D reviewer verifies against it.
5. **Completion**: When a module passes Phase D, mark it DONE here and add the next module from the backlog.
6. **No freelancing**: Do not work on modules outside this queue without explicit coordination on #619.
