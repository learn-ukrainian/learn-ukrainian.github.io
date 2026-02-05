# Audit Report: M74 — 74-mystetstvo-i-literatura.md
**Level:** B2 | **Module:** M74 | **Phase:** B2.4 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:32:01

## Configuration
**Type:** B2-vocab
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥35 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up | Знайдіть відповідність: мистецькі терміни | 12 | 8 | ✅ |
| 2 | fill-in | Заповніть пропуски: розмова про літературу | 12 | 8 | ✅ |
| 3 | quiz | Тест: українська культура | 12 | 8 | ✅ |
| 4 | true-false | Правда чи ні: факти про культуру | 12 | 8 | ✅ |
| 5 | group-sort | Розподіліть за категоріями | 18 | 14 | ✅ |
| 6 | unjumble | Складіть речення правильно | 12 | 6 | ✅ |
| 7 | cloze | Заповніть текст про українську культуру | 16 | 14 | ✅ |
| 8 | cloze | Розмова в музеї | 18 | 14 | ✅ |
| 9 | true-false | Українські культурні явища | 16 | 8 | ✅ |
| 10 | fill-in | Заповніть мистецьку критику | 8 | 8 | ✅ |
| 11 | essay-response | Улюблений український твір | 1 | 1 | ✅ |
| 12 | reading | Текст для аналізу: Мистецтво і література | 3 | 3 | ✅ |

**Summary:**
- Total activities: 12 (target: 10-14) ✅
- Unique types: 9 (minimum: 4) ✅
- Priority types used: 2/4 (match-up, quiz) ✅
- Required types used: 3/3 (essay-response, reading, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[SECTION_ORDER]** '## Лексика мистецької критики' should come after 'summary' section
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[YAML_SCHEMA_VIOLATION]** Schema error in 74-mystetstvo-i-literatura.yaml: Schema validation error at key '9': {'type': 'fill-in', 'title': 'Заповніть мистецьку критику', 'instruction': 'Оберіть правильні слова для опису твору.', 'items': [{'answer': 'вражає', 'options': ['вражає', 'дивує', 'шокує', 'вражає'], 'sentence': 'Цей твір ___ своєю глибиною.'}, {'answer': 'майстерно', 'options': ['майстерно', 'погано', 'рідко', 'ніколи'], 'sentence': 'Автор ___ використовує метафори.'}, {'answer': 'тривоги', 'options': ['тривоги', 'веселощів', 'байдужості', 'нудьги'], 'sentence': 'Картина створює атмосферу ___.'}, {'answer': 'збалансована', 'options': ['збалансована', 'порушена', 'забута', 'змінена'], 'sentence': 'Композиція вдало ___.'}, {'answer': 'Стиль', 'options': ['Стиль', 'Жанр', 'Сюжет', 'Автор'], 'sentence': '___ нагадує імпресіонізм.'}, {'answer': 'відображає', 'options': ['відображає', 'приховує', 'ігнорує', 'змінює'], 'sentence': 'Твір ___ дух епохи.'}, {'answer': 'тему', 'options': ['тему', 'мету', 'ціль', 'помилку'], 'sentence': 'Визначте головну ___ твору.'}, {'answer': 'символіку', 'options': ['символіку', 'кількість', 'вартість', 'назву'], 'sentence': 'Проаналізуйте ___ образів.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 2 violations (minor)

## Gates
- **Words:** ✅ 2002/2000 (raw: 2257)
- **Activities:** ✅ 12/10
- **Density:** ✅ All > 14
- **Unique_types:** ✅ 9/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 14/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 16 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ✅ Content-heavy OK (12 activities)
- **Immersion:** 🇺🇦 98.7% (target 90-100% (vocab))
- **Richness:** ❌ 73% < 95% min (vocabulary)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 73% (minimum: 95%)
**Module Type:** vocabulary

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| collocations | 0 | 20 | 0% | 25% | 0.0% |
| usage_examples | 56 | 15 | 100% | 20% | 20.0% |
| engagement | 12 | 4 | 100% | 15% | 15.0% |
| cultural | 18 | 3 | 100% | 10% | 10.0% |
| visual | 4 | 3 | 100% | 10% | 10.0% |
| register_notes | 8 | 5 | 100% | 10% | 10.0% |
| variety | 0.97 | - | 97% | 5% | 4.9% |
| paragraph_var | 0.76 | - | 76% | 5% | 3.8% |
| **TOTAL** | | | | | **73.6%** |

### Dryness Flags & Fixes
- ❌ **NO_COLLOCATIONS**
  - FIX:
    Add 5+ collocations in format: **слово** + noun/verb (e.g., **важка** робота, **приймати** рішення)

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 50 | Included in Core |
| **Розминка — Культурний ландшафт України** | ✅ | 364 | Included in Core |
| **Літературні жанри та епохи** | ⚪️ | 397 | Skipped |
| **Образотворче мистецтво** | ⚪️ | 548 | Skipped |
| **Музика та театр** | ⚪️ | 192 | Skipped |
| **Лексика мистецької критики** | ⚪️ | 75 | Skipped |
| **Підсумок та практика** | ✅ | 376 | Included in Core |