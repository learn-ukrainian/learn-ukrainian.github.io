# Audit Report: M131 — viyna-donbas.md
**Level:** B2 | **Module:** M131 | **Phase:** B2.3e | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 22:23:46

## Configuration
**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Дайте відповідь на запитання на основі прочитаного тексту про війну на Донбасі. | 8 | 8 | ✅ |
| 2 | fill-in | Заповніть пропуски відповідними словами з лексичного мінімуму. | 8 | 8 | ✅ |
| 3 | match-up | Поєднайте дати та події. | 12 | 8 | ✅ |
| 4 | error-correction | Виправте помилки в узгодженні слів. | 6 | 6 | ✅ |
| 5 | select | Аналіз подій та явищ війни | 6 | 6 | ✅ |
| 6 | mark-the-words | Дієслова в історичному контексті | 7 | 6 | ✅ |
| 7 | group-sort | Розподіліть поняття за відповідними категоріями. | 20 | 1 | ✅ |
| 8 | cloze | Заповніть пропуски в тексті про війну на Донбасі. | 16 | 1 | ✅ |
| 9 | unjumble | Складіть речення про війну. | 6 | 6 | ✅ |
| 10 | translate | Перекладіть терміни українською мовою. | 8 | 6 | ✅ |
| 11 | select | Символи та терміни війни на Донбасі | 6 | 6 | ✅ |
| 12 | quiz | Перевірте свої знання фактів про війну. | 8 | 8 | ✅ |
| 13 | true-false | Визначте правдивість тверджень. | 8 | 8 | ✅ |
| 14 | select | Міста та реалії воєнного часу | 6 | 6 | ✅ |
| 15 | essay-response | Есе: Феномен українського добровольчого руху | 1 | 1 | ✅ |
| 16 | comparative-study | Порівняльний аналіз: АТО та ООС | 1 | 1 | ✅ |

**Summary:**
- Total activities: 16 (target: 3-9) ❌
- Unique types: 13 (minimum: 2) ✅
- Priority types used: 2/4 (comparative-study, essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in viyna-donbas.yaml: Schema validation error at key '13': {'type': 'select', 'items': [{'question': 'Які міста були звільнені українською армією влітку 2014 року?', 'options': [{'text': "Слов'янськ", 'correct': True}, {'text': 'Краматорськ', 'correct': True}, {'text': 'Донецьк', 'correct': False}, {'text': 'Маріуполь', 'correct': True}, {'text': 'Луганськ', 'correct': False}, {'text': 'Сєвєродонецьк', 'correct': True}]}, {'question': 'Оберіть назви міст, що знаходилися на лінії розмежування.', 'options': [{'text': 'Авдіївка', 'correct': True}, {'text': "Мар'їнка", 'correct': True}, {'text': 'Львів', 'correct': False}, {'text': 'Піски', 'correct': True}]}, {'question': 'Виберіть терміни, що описують військовий побут.', 'options': [{'text': 'Бліндаж', 'correct': True}, {'text': 'Буржуйка', 'correct': True}, {'text': 'Басейн', 'correct': False}, {'text': 'Берці', 'correct': True}]}, {'question': 'Що було складовою Мінських домовленостей?', 'options': [{'text': 'Відведення важкого озброєння', 'correct': True}, {'text': "Обмін полоненими 'всіх на всіх'", 'correct': True}, {'text': 'Приєднання Донбасу до Росії', 'correct': False}, {'text': 'Припинення вогню', 'correct': True}]}, {'question': 'Які організації надавали гуманітарну допомогу?', 'options': [{'text': 'Червоний Хрест', 'correct': True}, {'text': 'ООН', 'correct': True}, {'text': 'НАТО', 'correct': False}, {'text': 'Місцеві волонтерські фонди', 'correct': True}]}, {'question': "Виберіть символи пам'яті про війну.", 'options': [{'text': "Дзвони пам'яті у Міноборони", 'correct': True}, {'text': "Маки пам'яті (символ перемоги над нацизмом)", 'correct': True}, {'text': 'Зірка героя (радянського зразка)', 'correct': False}, {'text': 'Мурали із зображенням воїнів', 'correct': True}]}], 'title': 'Міста та реалії воєнного часу', 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 1 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2061/4000 (raw: 2231)
- **Activities:** ✅ 16/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 11/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 20 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 16 (target 3-9)
- **Immersion:** 🇺🇦 96.1% (target 90-100% (history))
- **Richness:** ✅ 95% (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 3 | 100% | 24% | 23.8% |
| engagement | 11 | 6 | 100% | 14% | 14.3% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 5 | 2 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 0 | Included in Core |
| **Війна на Донбасі 2014-2022: Гібридна агресія** | ⚪️ | 86 | Skipped |
| **Вступ** | ✅ | 169 | Included in Core |
| **Читання: Хроніка оборони** | ✅ | 1194 | Included in Core |
| **Первинні джерела** | ✅ | 220 | Included in Core |
| **Деколонізаційний погляд** | ✅ | 214 | Included in Core |
| **Підсумок** | ✅ | 68 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |