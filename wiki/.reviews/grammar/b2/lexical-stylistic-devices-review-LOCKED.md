# lexical-stylistic-devices (L2-UK-EN B2/M33) — LOCKED review

- **File reviewed:** `wiki/grammar/b2/lexical-stylistic-devices.md`
- **Review date:** 2026-06-15
- **Reviewer:** codex/b2-wiki-readiness-batch-18
- **Rubric:** B2 wiki readiness pass: no unresolved VERIFY markers, source-backed factual claims, lifecycle metadata on wiki and paired plan, and a companion LOCKED review note.
- **Prior state:** unlocked B2 wiki page with seven VERIFY markers around generated trope examples, suffix constraints, active-participle formation, and L2/decolonization anchors.
- **Fixes applied:** Added lifecycle metadata, cleared all markers, labeled generated trope examples, and bounded morphology constraints to source-supported training guidance.

## Evidence

| Claim area | Evidence used | Resolution |
|---|---|---|
| Metonymy and synecdoche examples | Existing [S1], [S3], [S4] support the trope categories; VESUM attests `Шевченка` and `копійку`. | Labeled both examples as author-created training examples rather than source quotations. |
| Expressive suffixes | [S7] supports stylistic word formation examples such as `рученька`, `ручище`, and `ручисько`; VESUM attests the same forms. | Reframed the abstract/concrete limitation as a module training choice. |
| Active participle `посивілий` | Existing B2 `active-participles-past` and `checkpoint-passive-voice` pages cite textbook sources for `посивіти -> посивілий`; VESUM tags `посивілий` as an active perfect participial adjective. | Removed comments and kept bounded participle guidance. |
| L2/decolonization anchors | `data/canonical_anchors.yaml` entries `greeting_hello_formal`, `copula_present_tense`, `name_introduction`, `age_model`, `flag_ukraine`, `capital`, and `trident`. | Removed comments and kept the anchor forms. |

## Dimension Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Generated examples are no longer presented as direct source examples. |
| 2 | Ukrainian language quality | **9/10** | The page preserves natural stylistic examples and corrects transfer errors. |
| 3 | Decolonization | **9/10** | Canonical anchors remain with unresolved comments removed. |
| 4 | Completeness | **9/10** | Tropes, rhetorical figures, word formation, examples, and exercises remain intact. |
| 5 | Actionable guidance | **9/10** | Writers can distinguish source-backed categories from author-created drills. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" Means For This Artifact

- The wiki meta block carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by`.
- The paired plan carries `lifecycle: locked`, `reviewed_at`, `reviewed_by`, and `review_notes`.
- No unresolved VERIFY markers remain on the page.
- Batch 18 changes are limited to source-checked examples and bounded corrections.

## Unlock Triggers

1. A stylistics review disputes the author-created metonymy or synecdoche examples.
2. The active-participle source pages change in a way that removes support for `посивілий`.
3. A future wiki rebuild reintroduces VERIFY markers or drops lifecycle metadata.
