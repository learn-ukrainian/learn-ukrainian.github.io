# Audit Report: M31 — 31-numeral-declension-time-dates.md
**Level:** B2 | **Module:** M31 | **Phase:** B2.1c | **Pedagogy:** TTT | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:59:58

## Configuration
**Type:** B2-grammar
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, unjumble
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 31-numeral-declension-time-dates.yaml: Schema validation error at key '9': {'type': 'translate', 'title': 'Перекладіть вирази часу та дат', 'items': [{'source': "At 5 o'clock", 'options': [{'text': "О п'ятій годині", 'correct': True}, {'text': "В п'ять годин", 'correct': False}, {'text': "На п'яту годину", 'correct': False}]}, {'source': 'Half past two', 'options': [{'text': 'Пів на третю', 'correct': True}, {'text': 'Пів третього', 'correct': False}, {'text': 'Половина третього', 'correct': False}]}, {'source': 'On the first of May', 'options': [{'text': 'Першого травня', 'correct': True}, {'text': 'Перше травня', 'correct': False}, {'text': 'В перше травня', 'correct': False}]}, {'source': 'In 2020', 'options': [{'text': 'У дві тисячі двадцятому році', 'correct': True}, {'text': 'В дві тисячі двадцять році', 'correct': False}, {'text': 'У двадцять двадцять', 'correct': False}]}, {'source': 'Quarter to six', 'options': [{'text': 'За чверть шоста', 'correct': True}, {'text': 'Без чверті шість', 'correct': False}, {'text': 'Чверть до шостої', 'correct': False}]}, {'source': 'Twenty minutes past four', 'options': [{'text': "Двадцять хвилин на п'яту", 'correct': True}, {'text': "Двадцять хвилин п'ятого", 'correct': False}, {'text': 'Чотири двадцять', 'correct': False}]}, {'source': 'Додаткове речення 7.', 'options': ['переклад'], 'explanation': 'Пояснення.'}, {'source': 'Додаткове речення 8.', 'options': ['переклад'], 'explanation': 'Пояснення.'}], 'instruction': 'Оберіть правильний переклад.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: grammar) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 30/100)

- 2 violations (minor)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 1859/2000 (raw: 2061)
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 2 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.6% (target 90-100% (grammar))
- **Richness:** ✅ 95% (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 19 | 24 | 79% | 20% | 15.8% |
| engagement | 6 | 5 | 100% | 15% | 15.0% |
| dialogues | 5 | 4 | 100% | 15% | 15.0% |
| variety | 0.99 | - | 99% | 10% | 9.9% |
| cultural | 6 | 3 | 100% | 10% | 10.0% |
| realworld | 4 | 3 | 100% | 10% | 10.0% |
| visual | 8 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.91 | - | 91% | 5% | 4.6% |
| questions | 28 | 5 | 100% | 5% | 5.0% |
| proverbs | 1 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 90 | Included in Core |
| **Розминка — Числівники в повсякденному житті** | ⚪️ | 146 | Skipped |
| **Час — години та хвилини** | ⚪️ | 691 | Skipped |
| **Дати — дні та місяці** | ⚪️ | 89 | Skipped |
| **Числівники в офіційних документах** | ⚪️ | 371 | Skipped |
| **Практика** | ⚪️ | 460 | Skipped |
| **Підсумок** | ✅ | 12 | Included in Core |