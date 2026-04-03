# Audit Report: M23 — days-and-months.md
**Level:** A1 | **Module:** M23 | **Phase:** A1.4 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-04-03 14:02:04

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
| 1 | fill-in |  | 7 | 6 | ✅ |
| 2 | match-up |  | 8 | 6 | ✅ |
| 3 | fill-in |  | 6 | 6 | ✅ |
| 4 | group-sort |  | 14 | 6 | ✅ |
| 5 | true-false |  | 8 | 6 | ✅ |
| 6 | quiz |  | 6 | 6 | ✅ |
| 7 | fill-in |  | 6 | 6 | ✅ |
| 8 | translate |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 8 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 3/8 (fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in days-and-months.yaml: Schema validation error at key '7': {'type': 'translate', 'instruction': 'Оберіть правильний переклад (Choose the correct translation)', 'items': [{'source': 'On Monday', 'options': [{'text': 'понеділок', 'correct': False}, {'text': 'у понеділок', 'correct': True}, {'text': 'у понеділка', 'correct': False}]}, {'source': 'In April', 'options': [{'text': 'квітень', 'correct': False}, {'text': 'у квітня', 'correct': False}, {'text': 'у квітні', 'correct': True}]}, {'source': 'In autumn', 'options': [{'text': 'восени', 'correct': True}, {'text': 'осінь', 'correct': False}, {'text': 'у осінь', 'correct': False}]}, {'source': 'On Saturday', 'options': [{'text': 'субота', 'correct': False}, {'text': 'в суботу', 'correct': True}, {'text': 'у субота', 'correct': False}]}, {'source': 'In spring', 'options': [{'text': 'весна', 'correct': False}, {'text': 'у весну', 'correct': False}, {'text': 'навесні', 'correct': True}]}, {'source': 'In December', 'options': [{'text': 'грудень', 'correct': False}, {'text': 'в грудні', 'correct': True}, {'text': 'в грудня', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 1318/1200 (raw: 1455)
- **Activities:** ✅ 8/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 0/0
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 69/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 29.1% (target 15-35% (M23))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 385 | Included in Core |
| **Дні тижня (Days of the Week)** | ✅ | 332 | Included in Core |
| **Мі́сяці і по́ри ро́ку (Months and Seasons)** | ✅ | 390 | Included in Core |
| **Підсумок — Summary** | ✅ | 211 | Included in Core |