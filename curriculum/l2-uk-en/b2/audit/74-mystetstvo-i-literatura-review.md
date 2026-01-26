# Audit Report: M74 — 74-mystetstvo-i-literatura.md
**Level:** B2 | **Module:** M74 | **Phase:** B2 | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:28:35

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
| 1 | match-up | Знайдіть відповідність: мистецькі терміни | 12 | 8 | ✅ |
| 2 | fill-in | Заповніть пропуски: розмова про літературу | 12 | 8 | ✅ |
| 3 | quiz | Тест: українська культура | 12 | 8 | ✅ |
| 4 | true-false | Правда чи ні: факти про культуру | 12 | 8 | ✅ |
| 5 | group-sort | Розподіліть за категоріями | 18 | 1 | ✅ |
| 6 | unjumble | Складіть речення правильно | 12 | 6 | ✅ |
| 7 | cloze | Заповніть текст про українську культуру | 16 | 1 | ✅ |
| 8 | cloze | Розмова в музеї | 18 | 1 | ✅ |
| 9 | true-false | Українські культурні явища | 16 | 8 | ✅ |
| 10 | fill-in | Заповніть мистецьку критику | 8 | 8 | ✅ |
| 11 | essay-response | Улюблений український твір | 1 | 1 | ✅ |

**Summary:**
- Total activities: 11 (target: 3-9) ❌
- Unique types: 8 (minimum: 2) ✅
- Priority types used: 1/4 (essay-response) ✅
- Required types used: 1/2 (essay-response) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in 74-mystetstvo-i-literatura.yaml: Schema validation error at key '9': {'type': 'fill-in', 'title': 'Заповніть мистецьку критику', 'instruction': 'Оберіть правильні слова для опису твору.', 'items': [{'answer': 'вражає', 'options': ['вражає', 'дивує', 'шокує', 'вражає'], 'sentence': 'Цей твір ___ своєю глибиною.'}, {'answer': 'майстерно', 'options': ['майстерно', 'погано', 'рідко', 'ніколи'], 'sentence': 'Автор ___ використовує метафори.'}, {'answer': 'тривоги', 'options': ['тривоги', 'веселощів', 'байдужості', 'нудьги'], 'sentence': 'Картина створює атмосферу ___.'}, {'answer': 'збалансована', 'options': ['збалансована', 'порушена', 'забута', 'змінена'], 'sentence': 'Композиція вдало ___.'}, {'answer': 'Стиль', 'options': ['Стиль', 'Жанр', 'Сюжет', 'Автор'], 'sentence': '___ нагадує імпресіонізм.'}, {'answer': 'відображає', 'options': ['відображає', 'приховує', 'ігнорує', 'змінює'], 'sentence': 'Твір ___ дух епохи.'}, {'answer': 'тему', 'options': ['тему', 'мету', 'ціль', 'помилку'], 'sentence': 'Визначте головну ___ твору.'}, {'answer': 'символіку', 'options': ['символіку', 'кількість', 'вартість', 'назву'], 'sentence': 'Проаналізуйте ___ образів.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ❌ 2002/4000 (raw: 2270)
- **Activities:** ✅ 11/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 8/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 16 < 20 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ⚠️ Too many activities: 11 (target 3-9)
- **Immersion:** 🇺🇦 98.7% (target 90-100% (history))
- **Richness:** ❌ 91% < 95% min (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 91% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 56 | 24 | 100% | 20% | 20.0% |
| engagement | 12 | 5 | 100% | 15% | 15.0% |
| dialogues | 2 | 4 | 50% | 15% | 7.5% |
| variety | 0.97 | - | 97% | 10% | 9.7% |
| cultural | 18 | 3 | 100% | 10% | 10.0% |
| realworld | 3 | 3 | 100% | 10% | 10.0% |
| visual | 4 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.76 | - | 76% | 5% | 3.8% |
| questions | 8 | 5 | 100% | 5% | 5.0% |
| proverbs | 10 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **91.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 50 | Included in Core |
| **Вступ: Українська культура та її значення** | ✅ | 364 | Included in Core |
| **Теорія: Українська література та її класики** | ⚪️ | 397 | Skipped |
| **Українське образотворче мистецтво** | ⚪️ | 363 | Skipped |
| **Українська музика** | ⚪️ | 185 | Skipped |
| **Театр та кіно** | ⚪️ | 192 | Skipped |
| **Культурна критика** | ✅ | 75 | Included in Core |
| **Українська культура у світі** | ✅ | 176 | Included in Core |
| **Підсумок** | ✅ | 90 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 110 | Skipped |