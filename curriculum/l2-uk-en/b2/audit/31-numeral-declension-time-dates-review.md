# Audit Report: M31 — 31-numeral-declension-time-dates.md
**Level:** B2 | **Module:** M31 | **Phase:** B2.1c | **Pedagogy:** TTT | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-06 00:42:29

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
- **[YAML_SCHEMA_VIOLATION]** Schema error in 31-numeral-declension-time-dates.yaml: Schema validation error at key '3': {'type': 'error-correction', 'title': 'Виправте помилки у виразах часу та дат', 'items': [{'sentence': "Зустрінемося в п'ять годин.", 'error': "в п'ять годин", 'options': ["о п'ятій годині", "на п'ять годин", "у п'ять годин", "біля п'яти годин"], 'explanation': 'Час події позначається прийменником "о" + місцевий відмінок.', 'correct': "о п'ятій годині"}, {'sentence': "Зараз без п'ятнадцяти сім.", 'error': "без п'ятнадцяти сім", 'options': ['за чверть сьома', "за п'ятнадцять сім", "п'ятнадцять до сьомої", 'без чверті сім'], 'explanation': 'Конструкція "без..." є калькою. Правильно "за...".', 'correct': 'за чверть сьома'}, {'sentence': "Мій день народження п'ятого березня.", 'error': "п'ятого березня", 'options': ["п'яте березня", "п'ятого березня", "п'ять березня", "п'ятому березня"], 'explanation': 'Якщо це констатація факту (називний), то "п\'яте". Якщо дата події (коли?), то "п\'ятого". У цьому контексті краще "п\'яте" (яке число?).', 'correct': "п'яте березня"}, {'sentence': 'Поїзд прибуває в дванадцять тридцять.', 'error': 'в дванадцять тридцять', 'options': ['о дванадцятій тридцять', 'на дванадцять тридцять', 'у дванадцять тридцять', 'біля дванадцяти тридцяти'], 'explanation': 'Офіційний час теж вимагає "о" + порядковий числівник.', 'correct': 'о дванадцятій тридцять'}, {'sentence': 'Я чекаю тебе з двох годин.', 'error': 'з двох годин', 'options': ['з другої години', 'з двох', 'від двох годин', 'з другої'], 'explanation': '"З котрої?" - з другої.', 'correct': 'з другої години'}, {'sentence': 'Скільки годин?', 'error': 'Скільки годин', 'options': ['Котра година', 'Який час', 'Скільки часу', 'Яка година'], 'explanation': 'Стандартне питання про час.', 'correct': 'Котра година'}], 'instruction': 'Знайдіть помилку і оберіть правильний варіант.'} is not valid under any of the given schemas
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