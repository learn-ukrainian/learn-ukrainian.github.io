# Audit Report: M30 — my-city.md
**Level:** A1 | **Module:** M30 | **Phase:** A1.5 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-04-04 19:30:05

## Configuration
**Type:** A1-vocab
**Word Target:** 1200 words
**Activities:** 0-4 required
**Items per Activity:** ≥6 items
**Unique Types:** ≥0 types required
**Priority Types:** anagram, classify, fill-in, image-to-letter, match-up, quiz, unjumble, watch-and-repeat
**Engagement:** ≥0 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz |  | 8 | 6 | ✅ |
| 2 | match-up |  | 8 | 6 | ✅ |
| 3 | quiz |  | 6 | 6 | ✅ |
| 4 | fill-in |  | 6 | 6 | ✅ |
| 5 | quiz |  | 7 | 6 | ✅ |
| 6 | group-sort |  | 16 | 6 | ✅ |
| 7 | true-false |  | 7 | 6 | ✅ |
| 8 | error-correction |  | 6 | 6 | ✅ |
| 9 | fill-in |  | 6 | 6 | ✅ |
| 10 | translate |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 10 (target: 0-4) ❌
- Unique types: 7 (minimum: 0) ✅
- Priority types used: 3/8 (fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in my-city.yaml: Schema validation error at key '9': {'type': 'translate', 'instruction': 'Оберіть правильний переклад (Choose the correct Ukrainian translation)', 'items': [{'source': 'at the pharmacy', 'options': [{'text': 'в аптеці', 'correct': True}, {'text': 'на аптеці', 'correct': False}, {'text': 'біля аптеки', 'correct': False}]}, {'source': 'at the post office', 'options': [{'text': 'в пошті', 'correct': False}, {'text': 'на пошті', 'correct': True}, {'text': 'біля пошти', 'correct': False}]}, {'source': 'near the park', 'options': [{'text': 'в парку', 'correct': False}, {'text': 'на парку', 'correct': False}, {'text': 'біля парку', 'correct': True}]}, {'source': 'at the train station', 'options': [{'text': 'у вокзалі', 'correct': False}, {'text': 'на вокзалі', 'correct': True}, {'text': 'біля вокзалу', 'correct': False}]}, {'source': 'in the city center', 'options': [{'text': 'у центрі міста', 'correct': True}, {'text': 'на центрі міста', 'correct': False}, {'text': 'від центру міста', 'correct': False}]}, {'source': 'the library is nearby', 'options': [{'text': 'Бібліотека далеко.', 'correct': False}, {'text': 'Бібліотека там.', 'correct': False}, {'text': 'Бібліотека близько.', 'correct': True}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 1424/1200 (raw: 1459)
- **Activities:** ✅ 10/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 7/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 1/0
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 48/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 33.5% (target 15-40% (M30))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 465 | Included in Core |
| **Місця́ в мі́сті (City Places)** | ✅ | 401 | Included in Core |
| **Де це? (Where Is It?)** | ✅ | 414 | Included in Core |
| **Підсумок — Summary** | ✅ | 144 | Included in Core |