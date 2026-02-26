# Module Validation Checklist — l2-uk-direct

> Last updated: 2026-02-26
> Applies to: all A1 modules in `curriculum/l2-uk-direct/a1/`
> Schema: `schemas/activities-direct.schema.json`, `schemas/vocabulary-direct.schema.json`

---

## How to Use

Every module must pass **all applicable criteria** before moving from `draft` to `ready` status.
- **S** (Structural) — automatable, checked by `scripts/validate_direct.py`
- **P** (Pedagogical) — manual review checklist
- **Q** (Quality) — manual review checklist

Mark each criterion ✅ PASS or ❌ FAIL. A single ❌ blocks `ready` status.

---

## S — Structural Criteria (automatable)

| ID | Criterion | Threshold | How to check |
|---|---|---|---|
| S1 | Single thematic focus | Title maps to ONE communicative goal or grammar topic | Module description has one focus; no "and" between unrelated topics |
| S2 | Vocabulary count | Vocab modules: 15–35 words. Grammar modules: 5–15 new. Checkpoints: 0 new. | Count `vocabulary` entries in YAML |
| S3 | Activity count | Min 5 per module. Checkpoints: min 20 items. | Count activity entries in YAML |
| S4 | Activity variety | Min 3 distinct activity types per module | Count unique `type` values |
| S5 | Schema compliance | YAML validates against `activities-direct.schema.json` | `scripts/validate_direct.py {path}` |
| S6 | Pre-literacy gate | Modules 1–2: ONLY `watch_and_repeat`, `classify`, `image_to_letter` | Check activity types in modules 1–2 |

---

## P — Pedagogical Criteria (review checklist)

| ID | Criterion | Threshold | Notes |
|---|---|---|---|
| P1 | Engagement element | Min 1 of: `riddle`, `proverb_drill`, `tongue_twister` per module | Except checkpoints (17, 34, 44) |
| P2 | Reading passage | Min 1 `reading` activity per module | Except modules 1–2 (pre-literacy) |
| P3 | Grammar builds on previous | No forward references to untaught grammar | Activities only use grammar from this + prior modules |
| P4 | Vocabulary recycling | Min 3 items from prior modules reused in examples | Check examples for words taught in earlier modules |
| P5 | Ukrainian-only | Zero L1 content in learner-facing text | No English/other languages in activities, prompts, passages |
| P6 | Question-word grammar | Zero case names in learner-facing text | No називний, знахідний, давальний, etc. Only ХТО?/ЩО?/ДЕ? etc. |
| P7 | State Standard coverage | Module covers all items in its `standard_ref` field | Cross-check against `CURRICULUM-PLAN.md` spec |

---

## Q — Quality Criteria (review)

| ID | Criterion | Threshold | Notes |
|---|---|---|---|
| Q1 | No mixed themes | Module describable in one sentence without "and" between unrelated topics | E.g., "past tense formation" ✅ / "past tense and food vocabulary" ❌ |
| Q2 | Activity progression | Recognition → production within the module | First activities = classify/true_false, later = build_sentence/pattern_drill |
| Q3 | Textbook source cited | Each riddle/proverb/tongue_twister has `source: {book, page}` | Grade 1–3 textbooks as documented in `textbook-map.yaml` |
| Q4 | Known vocabulary | 90%+ of words in examples from this or prior modules | Unfamiliar words should be glossed or limited to 10% |
| Q5 | Cultural authenticity | Content reflects Ukrainian reality | Ukrainian names, cities, customs, culturally appropriate scenarios |

---

## Checkpoint-Specific Criteria

Checkpoints (modules 17, 34, 44) have modified thresholds:

| ID | Criterion | Checkpoint threshold |
|---|---|---|
| S2 | Vocabulary count | 0 new words (review only) |
| S3 | Activity count | Min 20 items |
| P1 | Engagement element | Optional (may include riddles for variety) |
| P4 | Vocabulary recycling | All items from prior modules in scope |

---

## Validation Workflow

```
1. Author writes module YAML
2. Run: scripts/validate_direct.py {path}         → S5 (schema)
3. Count: vocabulary entries                        → S2
4. Count: activity entries + unique types            → S3, S4
5. Check: pre-literacy gate (if modules 1–2)        → S6
6. Review: single focus, no mixed themes             → S1, Q1
7. Review: engagement element present                → P1
8. Review: reading activity present                  → P2
9. Review: no forward grammar references             → P3
10. Review: vocabulary recycling (3+ prior items)    → P4
11. Review: zero L1 content                          → P5
12. Review: zero case names in learner text           → P6
13. Review: State Standard items covered              → P7
14. Review: recognition → production order            → Q2
15. Review: textbook sources cited                    → Q3
16. Review: 90%+ known vocabulary                    → Q4
17. Review: cultural authenticity                     → Q5
18. If ALL pass → status: ready
    If ANY fail → fix and re-validate
```
