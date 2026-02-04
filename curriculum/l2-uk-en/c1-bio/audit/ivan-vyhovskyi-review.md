# Audit Report: M24 — ivan-vyhovskyi.md
**Level:** C1-BIO | **Module:** M24 | **Phase:** C1 | **Pedagogy:** seminar | **Target:** 3500
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-04 12:12:35

## Configuration
**Type:** C1-biography
**Word Target:** 3500 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** comparative-study, essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | reading | Уривок з Гадяцького трактату (1658) | 1 | 1 | ✅ |
| 2 | select | Аналіз умов Гадяча | 8 | 5 | ✅ |
| 3 | comparative-study | Переяслав (1654) vs Гадяч (1658) | 1 | 1 | ✅ |
| 4 | translate | Дипломатична лексика | 10 | 5 | ✅ |
| 5 | error-correction | Спростування міфів | 10 | 5 | ✅ |
| 6 | essay-response | Есе: Ціна елітарності | 1 | 1 | ✅ |
| 7 | critical-analysis | Аналіз джерела: Маніфест | 1 | 1 | ✅ |

**Summary:**
- Total activities: 7 (target: 3-9) ✅
- Unique types: 7 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, critical-analysis, essay-response, reading) ✅
- Required types used: 3/3 (comparative-study, essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in ivan-vyhovskyi.yaml: Schema validation error at key '1': {'type': 'select', 'title': 'Аналіз умов Гадяча', 'instruction': 'Проаналізуйте положення договору та оберіть правильні твердження.', 'items': [{'question': 'Який статус отримувала Україна за договором?', 'options': [{'text': 'Статус третього рівноправного члена федерації (Великого Князівства)', 'correct': True}, {'text': 'Статус автономної провінції у складі Польщі', 'correct': False}, {'text': 'Статус незалежної держави поза межами Речі Посполитої', 'correct': False}, {'text': 'Статус тимчасової військової адміністрації', 'correct': False}]}, {'question': 'Як вирішувалося релігійне питання?', 'options': [{'text': 'Православним гарантувалася рівність і місця в Сенаті', 'correct': True}, {'text': 'Православ’я ставало єдиною державною релігією', 'correct': False}, {'text': 'Всі козаки мусили прийняти католицизм', 'correct': False}, {'text': 'Питання релігії не згадувалося', 'correct': False}]}, {'question': 'Якою була доля збройних сил (козаків)?', 'options': [{'text': 'Встановлювався реєстр у 30 тисяч (плюс найманці)', 'correct': True}, {'text': 'Козацьке військо розпускалося', 'correct': False}, {'text': 'Всі козаки ставали регулярною армією Польщі', 'correct': False}, {'text': 'Чисельність війська не обмежувалася', 'correct': False}]}, {'question': 'Як договір впливав на соціальну структуру?', 'options': [{'text': 'Передбачалася масова нобілітація (надання шляхетства) козацької старшини', 'correct': True}, {'text': 'Всі селяни ставали вільними', 'correct': False}, {'text': 'Скасовувалося кріпосне право', 'correct': False}, {'text': 'Шляхта втрачала свої привілеї', 'correct': False}]}, {'question': 'Чому договір викликав спротив "черні" (простих козаків і селян)?', 'options': [{'text': 'Вони боялися повернення польських панів і відновлення панщини', 'correct': True}, {'text': 'Вони хотіли союзу з Туреччиною', 'correct': False}, {'text': 'Вони не хотіли вчитися в академіях', 'correct': False}, {'text': 'Вони були проти православ’я', 'correct': False}]}, {'question': 'Хто був головним ідеологом цього союзу з українського боку?', 'options': [{'text': 'Іван Виговський та Юрій Немирич', 'correct': True}, {'text': 'Богдан Хмельницький', 'correct': False}, {'text': 'Іван Сірко', 'correct': False}, {'text': 'Петро Дорошенко', 'correct': False}]}, {'question': 'Якою була реакція Московії на цей договір?', 'options': [{'text': 'Оголошення війни та військова інтервенція', 'correct': True}, {'text': 'Дипломатичне визнання угоди', 'correct': False}, {'text': 'Спроба приєднатися до союзу', 'correct': False}, {'text': 'Байдужість', 'correct': False}]}, {'question': 'Що означав пункт про "дві академії"?', 'options': [{'text': 'Культурну автономію та розвиток власної еліти', 'correct': True}, {'text': 'Підготовку кадрів для польської армії', 'correct': False}, {'text': 'Створення релігійних сект', 'correct': False}, {'text': 'Будівництво фортець', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 15/100)

- 4 violations (moderate)

## Gates
- **Words:** ❌ 1550/3500 (raw: 1605)
- **Activities:** ✅ 7/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 7/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 3/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/24
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (7 activities)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ❌ 71% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 71% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 3 | 4 | 75% | 19% | 14.3% |
| engagement | 3 | 6 | 50% | 14% | 7.1% |
| quotes | 0 | 3 | 0% | 14% | 0.0% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 3 | 4 | 75% | 10% | 7.1% |
| timeline_markers | 20 | 8 | 100% | 10% | 9.5% |
| legacy | 3 | 2 | 100% | 10% | 9.5% |
| variety | 1.00 | - | 100% | 5% | 4.8% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **71.4%** |

### Dryness Flags & Fixes
- ❌ **NO_QUOTES**
  - FIX:
    Add 2+ direct quotes from the subject. Use this format:
    
    > «[Exact quote from the person]»
    > — *[Person name], [context/year]*

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 65 | Included in Core |
| **Вступ** | ✅ | 183 | Included in Core |
| **Шлях до булави** | ⚪️ | 321 | Skipped |
| **Гадяцький договір** | ⚪️ | 283 | Skipped |
| **Конотопська битва** | ⚪️ | 289 | Skipped |
| **Падіння та загибель** | ⚪️ | 228 | Skipped |
| **Спадщина** | ⚪️ | 124 | Skipped |
| **Підсумок** | ✅ | 57 | Included in Core |