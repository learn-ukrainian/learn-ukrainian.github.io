# Audit Report: M37 — i-eat-i-drink.md
**Level:** A1 | **Module:** M37 | **Phase:** A1.6 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-04-04 19:30:02

## Configuration
**Type:** A1-grammar
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
| 1 | fill-in |  | 8 | 6 | ✅ |
| 2 | fill-in |  | 8 | 6 | ✅ |
| 3 | quiz |  | 6 | 6 | ✅ |
| 4 | group-sort |  | 12 | 6 | ✅ |
| 5 | match-up |  | 6 | 6 | ✅ |
| 6 | match-up |  | 6 | 6 | ✅ |
| 7 | error-correction |  | 6 | 6 | ✅ |
| 8 | true-false |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 8 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 3/8 (fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'feminine nouns...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in i-eat-i-drink.yaml: Schema validation error at key '8': {'type': 'unjumble', 'instruction': 'Складіть правильне речення зі слів (Put the words in the correct order)', 'items': [{'words': ['їм', 'Я', 'рибу'], 'correct_order': ['Я', 'їм', 'рибу']}, {'words': ["п'є", 'каву', 'Вона'], 'correct_order': ['Вона', "п'є", 'каву']}, {'words': ['їдять', 'кашу', 'Вони'], 'correct_order': ['Вони', 'їдять', 'кашу']}, {'words': ['воду', 'Ми', "п'ємо"], 'correct_order': ['Ми', "п'ємо", 'воду']}, {'words': ['хліб', 'Він', 'їсть'], 'correct_order': ['Він', 'їсть', 'хліб']}, {'words': ["п'єш", 'Ти', 'сік'], 'correct_order': ['Ти', "п'єш", 'сік']}, {'words': ['картоплю', 'їсте', 'Ви'], 'correct_order': ['Ви', 'їсте', 'картоплю']}, {'words': ['молоко', 'Вони', "п'ють"], 'correct_order': ['Вони', "п'ють", 'молоко']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ⚠️ 1156/1200 (raw: 1352) (44 short)
- **Activities:** ✅ 8/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 1/0
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 37/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 24.2% (target 20-40% (M37))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 334 | Included in Core |
| **Їсти і пити (To Eat and To Drink)** | ✅ | 271 | Included in Core |
| **Знахі́дний відмі́нок — неживе́ (Accusative Inanimate)** | ✅ | 384 | Included in Core |
| **Підсумок — Summary** | ✅ | 167 | Included in Core |