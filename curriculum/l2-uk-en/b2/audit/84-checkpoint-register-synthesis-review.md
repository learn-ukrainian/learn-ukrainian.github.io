# Audit Report: M84 — 84-checkpoint-register-synthesis.md
**Level:** B2 | **Module:** M84 | **Phase:** B2.4 | **Pedagogy:** Test | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 23:00:53

## Configuration
**Type:** B2-checkpoint
**Word Target:** 2000 words
**Activities:** 15-19 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, quiz
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥4 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥10 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 84-checkpoint-register-synthesis.yaml: Schema validation error at key '17': {'type': 'translate', 'title': 'Фрази для дискусій та дебатів', 'items': [{'source': 'I totally agree with your point of view.', 'options': [{'text': 'Я повністю згоден з вашою точкою зору.', 'correct': True}, {'text': 'Я думаю так само як і ви зараз.', 'correct': False}, {'text': 'Ваша думка мені дуже подобається.', 'correct': False}, {'text': 'Ви кажете правду, я вірю вам.', 'correct': False}]}, {'source': 'On the other hand, we should consider risks.', 'options': [{'text': 'З іншого боку, нам варто зважити на ризики.', 'correct': True}, {'text': 'З іншої руки, ми маємо думати про проблеми.', 'correct': False}, {'text': 'Але також є дуже великі небезпеки.', 'correct': False}, {'text': 'Навпаки, ми забули про всі ризики.', 'correct': False}]}, {'source': 'Summarizing the above, I would like to emphasize...', 'options': [{'text': 'Підсумовуючи вищесказане, я хотів би підкреслити...', 'correct': True}, {'text': 'Коротко кажучи про все, я скажу...', 'correct': False}, {'text': 'Наприкінці своєї промови я наголошу на...', 'correct': False}, {'text': 'Отже, я думаю, що це важливо знати...', 'correct': False}]}, {'source': 'Could you please clarify this point?', 'options': [{'text': 'Чи не могли б ви уточнити цей момент?', 'correct': True}, {'text': 'Що ви мали на увазі під цим словом?', 'correct': False}, {'text': 'Поясніть мені ще раз, я не зрозумів.', 'correct': False}, {'text': 'Кажіть простіше, будь ласка, я чекаю.', 'correct': False}]}, {'source': 'I am afraid I cannot support this idea.', 'options': [{'text': 'Боюсь, що я не можу підтримати цю ідею.', 'correct': True}, {'text': 'Я не хочу допомагати вам у цій справі.', 'correct': False}, {'text': 'Ця ідея мені зовсім не подобається.', 'correct': False}, {'text': 'Я маю великий страх перед вашою ідеєю.', 'correct': False}]}, {'source': 'According to the latest research data...', 'options': [{'text': 'Згідно з останніми даними досліджень...', 'correct': True}, {'text': 'Як кажуть нові наукові книжки...', 'correct': False}, {'text': 'Через останні результати нашої роботи...', 'correct': False}, {'text': 'По даним, які ми отримали вчора...', 'correct': False}]}, {'source': 'Додаткове речення 7.', 'options': ['переклад'], 'explanation': 'Пояснення.'}, {'source': 'Додаткове речення 8.', 'options': ['переклад'], 'explanation': 'Пояснення.'}], 'instruction': 'Оберіть найбільш влучний академічний переклад фрази для ведення професійної дискусії.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 30/100)

- 1 violations (minor)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 1807/2000 (raw: 1984)
- **Activities:** ❌ 0/15
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 6/4
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 5 < 10 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 15-19)
- **Immersion:** 🇺🇦 99.8% (checkpoint - no gate)
- **Richness:** ❌ 73% < 85% min (checkpoint)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 73% (minimum: 85%)
**Module Type:** checkpoint

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| activity_types | 0 | 8 | 0% | 25% | 0.0% |
| review_sections | 25 | 3 | 100% | 20% | 20.0% |
| variety | 0.91 | - | 91% | 15% | 13.7% |
| engagement | 6 | 3 | 100% | 10% | 10.0% |
| cultural | 2 | - | 100% | 10% | 10.0% |
| visual | 10 | 3 | 100% | 10% | 10.0% |
| paragraph_var | 1.00 | - | 100% | 10% | 10.0% |
| **TOTAL** | | | | | **73.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 52 | Included in Core |
| **Огляд — Контрольна точка** | ⚪️ | 84 | Skipped |
| **Навичка 1: Офіційно-діловий регістр** | ⚪️ | 54 | Skipped |
| **Навичка 2: Публіцистичний регістр** | ⚪️ | 285 | Skipped |
| **Навичка 3: Науковий регістр** | ⚪️ | 269 | Skipped |
| **Навичка 4: Перемикання регістрів** | ⚪️ | 320 | Skipped |
| **Навичка 5: Інтеграція регістрів у письмі** | ⚪️ | 253 | Skipped |
| **Підсумок та результати** | ✅ | 490 | Included in Core |