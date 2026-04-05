# Audit Report: M38 — home-and-daily-life.md
**Level:** A2 | **Module:** M38 | **Phase:** A2.5 | **Pedagogy:** TBL | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:04:58

## Configuration
**Type:** A2
**Word Target:** 2000 words
**Activities:** 0-4 required
**Items per Activity:** ≥8 items
**Unique Types:** ≥0 types required
**Priority Types:** cloze, error-correction, fill-in, group-sort, mark-the-words, match-up, observe, odd-one-out, order, quiz, reading, select, translate, true-false, unjumble
**Engagement:** ≥3 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | fill-in |  | 8 | 8 | ✅ |
| 2 | quiz |  | 8 | 8 | ✅ |
| 3 | match-up |  | 8 | 8 | ✅ |
| 4 | error-correction |  | 6 | 6 | ✅ |
| 5 | fill-in |  | 8 | 8 | ✅ |
| 6 | group-sort |  | 12 | 8 | ✅ |
| 7 | true-false |  | 6 | 8 | ❌ |

**Summary:**
- Total activities: 7 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 true-false requires at least 8 items.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'can you...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in home-and-daily-life.yaml: Schema validation error at key '7': {'id': 'unjumble-sentences', 'type': 'unjumble', 'instruction': 'Складіть правильне речення зі слів', 'items': [{'words': ['ходить', 'у', 'дні', 'він', 'кіно.', 'вільні', 'часто', 'У'], 'correct_order': ['У', 'вільні', 'дні', 'він', 'часто', 'ходить', 'у', 'кіно.']}, {'words': ['встаю', 'О', 'сьомій', 'і', 'вмиваюся.', 'завжди', 'я', 'годині'], 'correct_order': ['О', 'сьомій', 'годині', 'я', 'завжди', 'встаю', 'і', 'вмиваюся.']}, {'words': ['пити', 'ввечері?', 'Що', 'сьогодні', 'будете', 'ви'], 'correct_order': ['Що', 'ви', 'будете', 'пити', 'сьогодні', 'ввечері?']}, {'words': ['немає', 'кімнаті', 'У', 'телевізора.', 'цій', 'світлій'], 'correct_order': ['У', 'цій', 'світлій', 'кімнаті', 'немає', 'телевізора.']}, {'words': ['кухні.', 'Я', 'задоволенням', 'господарям', 'із', 'допомагаю', 'на'], 'correct_order': ['Я', 'із', 'задоволенням', 'допомагаю', 'господарям', 'на', 'кухні.']}, {'words': ['офісі', 'зі', 'своїми', 'Він', 'колегами.', 'працює', 'великому', 'у'], 'correct_order': ['Він', 'працює', 'у', 'великому', 'офісі', 'зі', 'своїми', 'колегами.']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 3 violations (minor)
- Activity density below minimum

## Gates
- **Words:** ✅ 2565/2000 (raw: 2678)
- **Activities:** ✅ 7/0
- **Density:** ❌ 1 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 61/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 54.4% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | true-false | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 856 | Included in Core |
| **Сценарій 2: Мій звичайний день (Scenario 2: My Typical Day)** | ✅ | 575 | Included in Core |
| **Сценарій 3: В гостях (Scenario 3: Visiting Someone)** | ✅ | 640 | Included in Core |
| **Мовленнєве завдання: Опишіть свій дім (Speaking Task: Describe Your Home)** | ✅ | 314 | Included in Core |
| **Підсумок** | ✅ | 180 | Included in Core |