# Audit Report: M08 — 08-konotop-witch.md
**Level:** LIT | **Module:** M08 | **Phase:** LIT.2 | **Pedagogy:** literature | **Target:** 4500
**Naturalness:** 10/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-07 23:05:29

## Configuration
**Type:** LIT-literature
**Word Target:** 4500 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, reading
**Engagement:** ≥4 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥0 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | reading | Ключові епізоди повісті | 0 | 1 | ❌ |
| 2 | quiz | Перевірка розуміння змісту | 0 | 1 | ❌ |
| 3 | match-up | Персонажі та їхні характеристики | 5 | 1 | ✅ |
| 4 | true-false | Правда чи вигадка? | 0 | 1 | ❌ |
| 5 | fill-in | Мова Пістряка (Канцеляризми) | 0 | 1 | ❌ |
| 6 | critical-analysis | Аналіз сатиричних засобів | 1 | 1 | ✅ |
| 7 | essay-response | Гумор як зброя критики | 1 | 1 | ✅ |
| 8 | mark-the-words | Знайдіть канцеляризми | 0 | 1 | ❌ |

**Summary:**
- Total activities: 8 (target: 3-9) ✅
- Unique types: 8 (minimum: 2) ✅
- Priority types used: 3/4 (critical-analysis, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 5

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** reading 'Ключові епізоди повісті' has 0 items (minimum: 1)
  - FIX: Add more items. LIT reading requires at least 1 items.
- **[INVALID_META_YAML]** Meta YAML Schema Violation at 'content_outline -> 5': 'points' is a required property
  - FIX: Correct the YAML structure to match schemas/meta-module.schema.json
- **[MISSING_FIELD]** mark-the-words 'Знайдіть канцеляризми' is missing 'passage' field
  - FIX: Add 'passage' field with the content
- **[MISSING_FIELD]** mark-the-words 'Знайдіть канцеляризми' is missing 'correct_words' array
  - FIX: Add 'correct_words' array with correct words
- **[YAML_SCHEMA_VIOLATION]** Schema error in 08-konotop-witch.yaml: Schema validation error at key '7': {'type': 'mark-the-words', 'title': 'Знайдіть канцеляризми', 'instructions': 'Позначте слова, які є канцеляризмами або русизмами в мові Пістряка.', 'sentence': 'Я {покорнейше} прошу вас {уведомить} мене про {состояніє} справ у {ввіреній} вам сотні {касательно} походу.', 'target_words': ['покорнейше', 'уведомить', 'состояніє', 'ввіреній', 'касательно']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**📝 UPDATE** (severity 25/100)

- 5 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ❌ 1338/4500 (raw: 1407)
- **Activities:** ✅ 8/3
- **Density:** ❌ 5 < 1
- **Unique_types:** ✅ 8/2 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 5/4
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/0
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 5 violations
- **Content_heavy:** ✅ Content-heavy OK (8 activities)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (literature))
- **Richness:** ⚠️ 91% (literature) - 1 flags
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 10/10 (High)

## Richness Details
**Score:** 91% (minimum: 90%)
**Module Type:** literature

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| analysis_sections | 10 | 5 | 100% | 17% | 17.4% |
| literary_citations | 5 | 5 | 100% | 17% | 17.4% |
| engagement | 5 | 4 | 100% | 13% | 13.0% |
| historical_context | 11 | 3 | 100% | 13% | 13.0% |
| essays | 3 | 2 | 100% | 13% | 13.0% |
| resources | 0 | 3 | 0% | 9% | 0.0% |
| variety | 1.00 | - | 100% | 4% | 4.3% |
| cultural | 4 | - | 100% | 4% | 4.3% |
| visual | 6 | 1 | 100% | 4% | 4.3% |
| paragraph_var | 1.00 | - | 100% | 4% | 4.3% |
| **TOTAL** | | | | | **91.3%** |

### Dryness Flags & Fixes
- ❌ **NO_RESOURCES**
  - FIX:
    Add 2+ resource blocks. Use this format:
    
    > [!resources] Додаткові ресурси
    >
    > - [Resource 1 with link or description]
    > - [Resource 2 with link or description]

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Ключові епізоди повісті | reading | 0 | 1 | Add 1 more items |
| Перевірка розуміння змісту | quiz | 0 | 1 | Add 1 more items |
| Правда чи вигадка? | true-false | 0 | 1 | Add 1 more items |
| Мова Пістряка (Канцеляризми) | fill-in | 0 | 1 | Add 1 more items |
| Знайдіть канцеляризми | mark-the-words | 0 | 1 | Add 1 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 57 | Included in Core |
| **Вступ — Найтемніша і найсмішніша повість** | ✅ | 217 | Included in Core |
| **Сюжет — полювання на відьму** | ⚪️ | 271 | Skipped |
| **Антигерої — галерея типів** | ⚪️ | 260 | Skipped |
| **Готика та народна демонологія** | ⚪️ | 208 | Skipped |
| **Мовна стилізація** | ⚪️ | 182 | Skipped |
| **Підсумок — Енциклопедія шахрайства** | ✅ | 143 | Included in Core |