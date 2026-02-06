# Audit Report: M20 — 20-register-medical-ukrainian.md
**Level:** B2 | **Module:** M20 | **Phase:** B2.1b | **Pedagogy:** Not Specified | **Target:** 3800
**Naturalness:** 8/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-06 00:31:24

## Configuration
**Type:** B2-grammar
**Word Target:** 3800 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, unjumble
**Required Types:** error-correction, essay-response, fill-in, match-up, quiz, reading
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Медична лексика та комунікація | 16 | 8 | ✅ |
| 2 | match-up | Симптоми та їх описи | 16 | 8 | ✅ |
| 3 | cloze | Діалог лікар-пацієнт | 16 | 14 | ✅ |
| 4 | true-false | Медичний регістр | 16 | 8 | ✅ |
| 5 | group-sort | Типи болю за характером | 17 | 14 | ✅ |
| 6 | unjumble | Складіть медичні інструкції | 16 | 6 | ✅ |
| 7 | error-correction | Виправте помилки у медичному мовленні | 16 | 6 | ✅ |
| 8 | cloze | Заповніть діалог на прийомі у лікаря | 18 | 14 | ✅ |
| 9 | mark-the-words | Знайдіть медичні терміни | 19 | 6 | ✅ |
| 10 | select | Оберіть усі правильні варіанти | 8 | 6 | ✅ |
| 11 | translate | Оберіть правильний переклад | 16 | 6 | ✅ |
| 12 | fill-in | Частини тіла та симптоми | 16 | 8 | ✅ |
| 13 | quiz | Комплексна перевірка медичної лексики | 16 | 8 | ✅ |
| 14 | essay-response | Візит до лікаря | 1 | 1 | ✅ |
| 15 | reading | Медичний протокол: аналіз | 0 | 3 | ❌ |

**Summary:**
- Total activities: 15 (target: 10-14) ❌
- Unique types: 13 (minimum: 4) ✅
- Priority types used: 4/4 (cloze, error-correction, fill-in, unjumble) ✅
- Required types used: 6/6 (error-correction, essay-response, fill-in, match-up, quiz, reading) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** reading 'Медичний протокол: аналіз' has 0 items (minimum: 3)
  - FIX: Add more items. B2 reading requires at least 3 items.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (71% overlap): "Якщо температура підніметься вище 38,5° — давайте жарознижувальне.". Shares significant keywords with sentence at index 12.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'у мене...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 20-register-medical-ukrainian.yaml: Schema validation error at key '14': {'id': 'reading-20-register-medical-ukrainian', 'type': 'reading', 'title': 'Медичний протокол: аналіз', 'instruction': 'Прочитайте текст та дайте відповіді на запитання.', 'passage': 'Пацієнт звернувся до сімейного лікаря зі скаргами на головний біль, запаморочення та підвищений артеріальний тиск. Після первинного огляду лікар призначив загальний аналіз крові, біохімічний аналіз та електрокардіограму. Результати обстеження показали підвищений рівень холестерину та ознаки гіпертонії першого ступеня. Лікар рекомендував дієту з обмеженням солі, помірні фізичні навантаження та призначив медикаментозне лікування. Контрольний огляд — через два тижні.', 'items': [{'question': 'З якими скаргами звернувся пацієнт?', 'answer': 'Головний біль, запаморочення, підвищений тиск'}, {'question': 'Які обстеження призначив лікар?', 'answer': 'Загальний аналіз крові, біохімічний аналіз, ЕКГ'}, {'question': 'Що показали результати?', 'answer': 'Підвищений холестерин, гіпертонія першого ступеня'}, {'question': 'Які рекомендації дав лікар?', 'answer': 'Дієта, фізичні навантаження, медикаменти'}, {'question': 'Коли призначено контрольний огляд?', 'answer': 'Через два тижні'}, {'question': 'Який тип тексту це представляє?', 'answer': 'Медичний протокол / виписка'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 4 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ❌ 2807/3800 (raw: 3512)
- **Activities:** ✅ 15/10
- **Density:** ❌ 1 < 14
- **Unique_types:** ✅ 13/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/6
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (grammar))
- **Richness:** ✅ 99% (style)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 8/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** style

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| exemplar_texts | 6 | 2 | 100% | 25% | 25.0% |
| model_answers | 100 | 3 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| register_analysis | 15 | 5 | 100% | 15% | 15.0% |
| visual | 12 | 4 | 100% | 10% | 10.0% |
| variety | 0.91 | - | 91% | 5% | 4.6% |
| cultural | 6 | - | 100% | 5% | 5.0% |
| paragraph_var | 1.00 | - | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **99.5%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Медичний протокол: аналіз | reading | 0 | 3 | Add 3 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 67 | Included in Core |
| **Вступ — Медичний регістр** | ✅ | 18 | Included in Core |
| **Опис симптомів** | ⚪️ | 226 | Skipped |
| **Діалог лікар-пацієнт** | ✅ | 829 | Included in Core |
| **Медичні інструкції** | ⚪️ | 793 | Skipped |
| **Медична документація** | ⚪️ | 599 | Skipped |
| **Типові помилки та русизми** | ✅ | 77 | Included in Core |
| **Практика і підсумок** | ✅ | 186 | Included in Core |
| **Підсумок** | ✅ | 12 | Included in Core |