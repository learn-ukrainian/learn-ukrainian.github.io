# Plan Review: special-signs

**Track:** a1 | **Sequence:** 3 | **Version:** 1.4.1 | **Lifecycle:** locked
**Verdict:** PASS
**Authority:** `docs/l2-uk-en/state-standard-2024-mapping.yaml` — A1 §4.1.2 (apostrophe), §4.1.3 (soft sign).

## Rule Compliance
| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS | Plan: 1200 = Config A1: 1200 |
| section_budgets | PASS | Sum = 250+250+250+250+200 = 1200 (exact match) |
| required_fields | PASS | All present, `letter_module: true` set |
| version_string | PASS | `version: '1.4.1'` (explicit string-quoted) |
| no Latin in Cyrillic | PASS | Scan clean |

## State Standard Alignment
| Grammar Topic | In Standard? | Standard Level | Plan Level | Status |
|--------------|-------------|----------------|------------|--------|
| Apostrophe usage | YES (§4.1.2) | A1 | A1 | PASS |
| Soft sign (ь) | YES (§4.1.3) | A1 | A1 | PASS |
| Iotated vowels (precondition framing) | YES (§4.1.4) | A1 | A1 | PASS — light review, no overreach |
| `буряк` / `бур'ян` / `свято` 3-way contrast | NUS pedagogy (Захарійчук 1 кл. с.97) | A1 | A1 | PASS — classic A1 orthography contrast |
| Word transfer rules (`Мар'-яна`, `дере-в'яний`) | NUS pedagogy (Большакова 2 кл. с.58–59) | A1 | A1 | PASS — basic перенесення rule |

## Grammar Verification (Textbook RAG)
| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Apostrophe after б, п, в, м, ф, р + я/ю/є/ї | Захарійчук 1 кл. с.97 (cited) | YES | Standard A1 rule |
| Soft sign as silent softener | Авраменко 5 кл. с.75 (cited) | YES | Correct pedagogy — distinguishes [н] vs [н'] |
| Apostroph keeps preceding consonant HARD (м'я = hard м + [йа]) | Standard | YES | Critical distinction correctly stated — common L2 misperception is exactly this |
| Зона без апострофа: свято, цвях, морквяний | Standard (post-consonant cluster rule) | YES | Correct exception; presented as memorized examples not derived rule (appropriate for A1) |
| Transfer: `Мар'-яна`, `дере-в'яний` | Большакова 2 кл. с.58-59 (cited) | YES | Verified — apostroph stays attached to preceding letter |

## Vocabulary Verification (VESUM)
| Word | VESUM | Notes |
|------|-------|-------|
| день / кінь / сіль / вчитель | All FOUND | OK — high-frequency ь-words |
| сім'я / м'ясо / п'ять / комп'ютер | All FOUND | OK — canonical apostrophe set |
| буряк / бур'ян | Both FOUND | OK — the central contrast |
| свято / цвях | Both FOUND | OK — post-cluster exception |
| дев'ять / ім'я / здоров'я | All FOUND | OK |
| маленький / сьогодні / ложка | All FOUND | OK; `ложка` correctly framed as counterexample to *льожка |
| дерев'яний / Мар'яна | Both FOUND | OK — transfer-model words |

## Issues Found

### CRITICAL (must fix before build)
None.

### HIGH (should fix before build)
None.

### MEDIUM (fix if possible)
None.

### LOW (informational)
1. The `author_note` in vocabulary_hints provides excellent guardrails for the writer (forbids inflectional paradigm intro, forbids productive prefix rule, anchors to 3 contrasts). This is exemplary author-note design — should be propagated as a template pattern.
2. The plan deliberately defers the префіксний апостроф (`під'їзд`, `з'їзд`) as "mentioned, not productive" — appropriate scope management for A1.

## Suggested Fixes
None required.

## Verdict
PASS. The plan is tight, narrowly scoped to ь + apostrophe, well-grounded in NUS textbooks (Захарійчук 1 кл., Авраменко 5 кл., Большакова 2 кл.), and includes a thoughtful 3-way contrast (`буряк`/`бур'ян`/`свято`) that addresses the most common L2 errors. Re-scoping pass in v1.4.0 (removed voiced/voiceless, Г/Ґ, Р, И drift) was the correct call. Recommend **LOCK_NOW**.
