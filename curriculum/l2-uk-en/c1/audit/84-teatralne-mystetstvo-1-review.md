# Audit Report: M84 — 84-teatralne-mystetstvo-1.md
**Level:** C1 | **Module:** M84 | **Phase:** C1.5 | **Pedagogy:** CBI | **Target:** 3000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:24:56

## Configuration
**Type:** C1-fine-arts
**Word Target:** 3000 words
**Activities:** 12-16 required
**Items per Activity:** ≥12 items
**Unique Types:** ≥4 types required
**Priority Types:** error-correction, fill-in, unjumble
**Engagement:** ≥7 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Історія українського театру | 12 | 5 | ✅ |
| 2 | match-up | Театральні діячі та їхній внесок | 10 | 6 | ✅ |
| 3 | cloze | Реформа Леся Курбаса | 9 | 12 | ❌ |
| 4 | fill-in | Театральна лексика | 10 | 6 | ✅ |
| 5 | essay-response | Есе: Курбас і сьогодення | 1 | 1 | ✅ |
| 6 | true-false | Театральні факти | 10 | 5 | ✅ |
| 7 | group-sort | Театральні епохи | 15 | 12 | ✅ |
| 8 | mark-the-words | Опис сцени | 8 | 5 | ✅ |
| 9 | translate | Театральні терміни | 5 | 5 | ✅ |
| 10 | unjumble | Цитати про театр | 6 | 5 | ✅ |
| 11 | select | Театральні жанри | 3 | 5 | ❌ |
| 12 | critical-analysis | Аналіз вистави «Мина Мазайло» | 1 | 1 | ✅ |
| 13 | comparative-study | Побутовий vs Модерний театр | 1 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 12-16) ✅
- Unique types: 13 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського театру' Q1 prompt length 4 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського театру' Q2 prompt length 5 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського театру' Q4 prompt length 7 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського театру' Q7 prompt length 5 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського театру' Q9 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського театру' Q10 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про театр' item 1 has 10 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про театр' item 2 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про театр' item 3 has 7 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про театр' item 4 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про театр' item 5 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про театр' item 6 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY]** select 'Театральні жанри' has 3 items (minimum: 5)
  - FIX: Add more items. C1 select requires at least 5 items.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 84-teatralne-mystetstvo-1.yaml: Schema validation error at key '10': {'type': 'select', 'title': 'Театральні жанри', 'items': [{'question': 'Який жанр є веселим і легким?', 'options': [{'text': 'Комедія', 'correct': True}, {'text': 'Трагедія', 'correct': False}, {'text': 'Драма', 'correct': False}, {'text': 'Водевіль', 'correct': True}, {'text': 'Фарс', 'correct': True}], 'min_correct': 3}, {'question': 'Що характерно для драми?', 'options': [{'text': 'Серйозний сюжет', 'correct': True}, {'text': 'Конфлікт героїв', 'correct': True}, {'text': 'Психологізм', 'correct': True}, {'text': 'Тільки сміх', 'correct': False}, {'text': "Обов'язкова смерть героя", 'correct': False}], 'min_correct': 3}, {'question': "Які п'єси писав Карпенко-Карий?", 'options': [{'text': 'Сатиричні комедії', 'correct': True}, {'text': 'Історичні драми', 'correct': True}, {'text': 'Соціально-побутові драми', 'correct': True}, {'text': 'Опери', 'correct': False}, {'text': 'Балети', 'correct': False}], 'min_correct': 3}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**🔄 REWRITE** (severity 80/100)

- 14 violations (severe - consider revision)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar
- Activity density below minimum

## Gates
- **Words:** ❌ 1945/3000 (raw: 2040)
- **Activities:** ✅ 13/12
- **Density:** ❌ 2 < 12
- **Unique_types:** ✅ 13/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 7/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ✅ Content-heavy OK (13 activities)
- **Immersion:** 🇺🇦 99.7% (target 90-100% (fine-arts))
- **Richness:** ✅ 96% (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 23 | 15 | 100% | 25% | 25.0% |
| engagement | 7 | 5 | 100% | 19% | 18.7% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 6 | 4 | 100% | 12% | 12.5% |
| realworld | 3 | 3 | 100% | 12% | 12.5% |
| visual | 2 | 4 | 50% | 6% | 3.1% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 10 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **96.8%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Реформа Леся Курбаса | cloze | 9 | 12 | Add 3 more items |
| Театральні жанри | select | 3 | 5 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 98 | Included in Core |
| **Вступ: Театр як дзеркало суспільства** | ✅ | 110 | Included in Core |
| **Давній театр: Вертеп і Шкільна драма** | ⚪️ | 348 | Skipped |
| **Театр Корифеїв: Професіонали на сцені** | ⚪️ | 347 | Skipped |
| **Лесь Курбас і «Березіль»: Театральна революція** | ⚪️ | 627 | Skipped |
| **Аналіз: Еволюція театральної думки** | ✅ | 196 | Included in Core |
| **Підсумок** | ✅ | 81 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 138 | Skipped |