# checkpoint-register-domain (L2-UK-EN B2/M42) — LOCKED review

- **File reviewed:** `wiki/grammar/b2/checkpoint-register-domain.md`
- **Review date:** 2026-06-15
- **Reviewer:** codex/b2-wiki-readiness-batch-18
- **Rubric:** B2 wiki readiness pass: no unresolved VERIFY markers, source-backed factual claims, lifecycle metadata on wiki and paired plan, and a companion LOCKED review note.
- **Prior state:** unlocked B2 wiki page with seven VERIFY markers around medical-document terminology, greeting/surname anchors, and generated register examples.
- **Fixes applied:** Added lifecycle metadata, cleared all markers, replaced the ambiguous `лікарняний лист` example, and labeled generated examples as author-created drills based on the registered sources.

## Evidence

| Claim area | Evidence used | Resolution |
|---|---|---|
| `лікарняний` paronym row | Existing [S3] supports the paronym family; VESUM attests `лікарняний`, `листок`, and `непрацездатності`. | Removed the ambiguous `лікарняний лист` example and kept hospital-context examples. |
| Greetings and surname terminology | `data/canonical_anchors.yaml` entries `greeting_hello_formal`, `farewell_goodbye`, and `surname_name_term`; VESUM attests `прізвище`. | Removed comments and softened the wording to register-specific training guidance. |
| Register examples | [S4] supports repetition as expressive word formation; [S6] lists the conversational/evaluative lexemes used in the author-created sentences. | Labeled the examples as generated drills rather than source quotations. |

## Dimension Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | Factual accuracy | **9/10** | Ambiguous terminology was removed, and generated examples are identified as author-created. |
| 2 | Ukrainian language quality | **9/10** | The page keeps natural register contrasts and corrects high-frequency L2 traps. |
| 3 | Decolonization | **8/10** | Anti-russism guidance remains, now bounded to the module's training register. |
| 4 | Completeness | **9/10** | Style matrix, paronyms, errors, examples, and exercise guidance remain intact. |
| 5 | Actionable guidance | **9/10** | Writers get clear register-differentiation tasks without unresolved markers. |

**Overall: 9/10 — LOCKED.**

## What "LOCKED" Means For This Artifact

- The wiki meta block carries `lifecycle: locked`, `last_reviewed`, and `reviewed_by`.
- The paired plan carries `lifecycle: locked`, `reviewed_at`, `reviewed_by`, and `review_notes`.
- No unresolved VERIFY markers remain on the page.
- Batch 18 changes are limited to source-checked examples and bounded corrections.

## Unlock Triggers

1. A future terminology review requires restoring a document-specific `лікарняний` example with a stronger source.
2. The canonical anchor registry changes for greetings, farewell, or `прізвище`.
3. A future wiki rebuild reintroduces VERIFY markers or drops lifecycle metadata.
