# Audit Report: M24 — pylyp-orlyk.md

**Level:** C1 | **Module:** M24 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** None/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:07

## Configuration

**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** critical-analysis, essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown

| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Державницька візія Пилипа Орлика | 8 | 5 | ✅ |
| 2 | match-up | Термінологія українського конституціоналізму | 12 | 6 | ✅ |
| 3 | fill-in | Політичний шлях Пилипа Орлика: Аналітична реконструкція | 12 | 6 | ✅ |
| 4 | essay-response | Есе: Конституція Пилипа Орлика як цивілізаційний вибір | 1 | 1 | ✅ |
| 5 | comparative-study | Компаративістика: Орлик vs Монтеск'є | 1 | 1 | ✅ |
| 6 | select | Структура та принципи Конституції 1710 року | 8 | 5 | ✅ |
| 7 | true-false | Деконструкція міфів про гетьмана-вигнанця | 9 | 5 | ✅ |
| 8 | mark-the-words | Лексика Державного Права | 7 | 5 | ✅ |
| 9 | unjumble | Відновлення конституційних тез | 8 | 5 | ✅ |
| 10 | cloze | Аналіз 'Діаріуша' та еміграційної долі | 12 | 1 | ✅ |
| 11 | group-sort | Класифікація статей Конституції 1710 року | 15 | 1 | ✅ |
| 12 | translate | Переклад конституційних декларацій | 8 | 5 | ✅ |
| 13 | error-correction | Корекція правового дискурсу XVIII ст. | 10 | 5 | ✅ |
| 14 | true-false | Деталі Конституційного Устрою | 8 | 5 | ✅ |
| 15 | authorial-intent | Аналіз стратегічних намірів гетьмана-інтелектуала | 1 | 1 | ✅ |
| 16 | critical-analysis | Критичний аналіз: Конституція як правовий щит | 1 | 1 | ✅ |

**Summary:**
- Total activities: 16 (target: 3-9) ❌
- Unique types: 15 (minimum: 3) ✅
- Priority types used: 5/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz) ✅
- Required types used: 6/7 (critical-analysis, essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in pylyp-orlyk.yaml: Schema validation error at key '13': {'type': 'true-false', 'title': 'Деталі Конституційного Устрою', 'instruction': 'Перевірка знань про конкретні статті документа 1710 року.', 'items': [{'statement': 'Конституція Орлика передбачала право гетьмана призначати наступника без виборів.', 'correct': False, 'explanation': 'Навпаки, виборність була ключовим принципом легітимності влади.'}, {'statement': "Документ встановлював обов'язковість звітування гетьмана перед Радою за державні витрати.", 'correct': True, 'explanation': 'Це було засобом запобігання корупції та зловживанням.'}, {'statement': 'Конституція гарантувала безкоштовну освіту для всіх дітей козацького стану.', 'correct': True, 'explanation': 'Підтримка освіти була частиною стратегії формування національної еліти.'}, {'statement': 'Згідно з документом, Україна мала стати повноправною частиною Російської імперії.', 'correct': False, 'explanation': 'Конституція проголошувала повну незалежність від московського патріархату та царату.'}, {'statement': "Орлик ввів поняття 'суспільної каси', яка мала допомагати сім'ям загиблих воїнів.", 'correct': True, 'explanation': "Соціальний захист був невід'ємною частиною його бачення справедливої держави."}, {'statement': 'Конституція гарантувала збереження прав міст на самоврядування.', 'correct': True, 'explanation': 'Магдебурзьке право підтверджувалося як основа міських свобод.'}, {'statement': 'Гетьман мав право одноосібно оголошувати війну та укладати мир.', 'correct': False, 'explanation': 'Ці рішення потребували згоди Генеральної ради.'}, {'statement': 'Пилип Орлик був обраний гетьманом довічно.', 'correct': True, 'explanation': 'Його повноваження були довічними, але обмеженими законом і радою.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2177/4000 (raw: 2374)
- **Activities:** ✅ 16/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 15/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 16 (target 3-9)
- **Immersion:** 🇺🇦 99.7% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ None/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 14 | 4 | 100% | 19% | 19.0% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 9 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 99 | Included in Core |
| **Вступ** | ✅ | 220 | Included in Core |
| **Життєпис** | ⚪️ | 795 | Skipped |
| **Історичний контекст: Перша Політична Еміграція як Виклик Імперії** | ✅ | 258 | Included in Core |
| **Внесок** | ⚪️ | 274 | Skipped |
| **Порівняльний аналіз: Орлик vs Тоталітарні Моделі Часу** | ✅ | 184 | Included in Core |
| **Критичне мислення: Питання для глибокого аналізу та дискусії** | ✅ | 114 | Included in Core |
| **Спадщина** | ⚪️ | 137 | Skipped |
| **Підсумок** | ✅ | 46 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 50 | Skipped |
