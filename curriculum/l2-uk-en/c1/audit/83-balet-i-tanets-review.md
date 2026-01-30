# Audit Report: M83 — 83-balet-i-tanets.md
**Level:** C1 | **Module:** M83 | **Phase:** C1.5 | **Pedagogy:** CBI | **Target:** 3000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-30 21:14:45

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
| 1 | quiz | Історія танцю | 12 | 5 | ✅ |
| 2 | match-up | Особистості та терміни | 10 | 6 | ✅ |
| 3 | cloze | Історія Сержа Лифаря | 8 | 12 | ❌ |
| 4 | fill-in | Балетна термінологія | 10 | 6 | ✅ |
| 5 | essay-response | Есе: Український слід у світовому балеті | 1 | 1 | ✅ |
| 6 | true-false | Міфи про танець | 10 | 5 | ✅ |
| 7 | group-sort | Види танцю | 15 | 12 | ✅ |
| 8 | mark-the-words | Опис балетної вистави | 8 | 5 | ✅ |
| 9 | translate | Переклад танцювальних понять | 5 | 5 | ✅ |
| 10 | unjumble | Факти про танець | 6 | 5 | ✅ |
| 11 | select | Балетні професії | 3 | 5 | ❌ |
| 12 | critical-analysis | Аналіз стилю Лифаря | 1 | 1 | ✅ |
| 13 | comparative-study | Народний vs Класичний | 1 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 12-16) ✅
- Unique types: 13 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія танцю' Q1 prompt length 4 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія танцю' Q2 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія танцю' Q4 prompt length 7 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія танцю' Q5 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія танцю' Q6 prompt length 3 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія танцю' Q9 prompt length 5 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія танцю' Q11 prompt length 5 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Факти про танець' item 1 has 6 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Факти про танець' item 2 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Факти про танець' item 3 has 7 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Факти про танець' item 4 has 9 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Факти про танець' item 5 has 9 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Факти про танець' item 6 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY]** select 'Балетні професії' has 3 items (minimum: 5)
  - FIX: Add more items. C1 select requires at least 5 items.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'модерн —...'.
  - FIX: Vary sentence structure.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 83-balet-i-tanets.yaml: Schema validation error at key '10': {'type': 'select', 'title': 'Балетні професії', 'items': [{'question': 'Хто створює танець?', 'options': [{'text': 'Хореограф', 'correct': True}, {'text': 'Балетмейстер', 'correct': True}, {'text': 'Постановник', 'correct': True}, {'text': 'Диригент', 'correct': False}, {'text': 'Костюмер', 'correct': False}], 'min_correct': 3}, {'question': 'Що входить до екіпірування балерини?', 'options': [{'text': 'Пуанти', 'correct': True}, {'text': 'Пачка', 'correct': True}, {'text': 'Тріко', 'correct': True}, {'text': 'Чоботи', 'correct': False}, {'text': 'Шолом', 'correct': False}], 'min_correct': 3}, {'question': 'Які якості необхідні танцівнику?', 'options': [{'text': 'Витривалість', 'correct': True}, {'text': 'Музикальність', 'correct': True}, {'text': 'Гнучкість', 'correct': True}, {'text': 'Артистизм', 'correct': True}, {'text': 'Вміння співати', 'correct': False}], 'min_correct': 3}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**🔄 REWRITE** (severity 80/100)

- 16 violations (severe - consider revision)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar
- Activity density below minimum

## Gates
- **Words:** ❌ 1926/3000 (raw: 2029)
- **Activities:** ✅ 13/12
- **Density:** ❌ 2 < 12
- **Unique_types:** ✅ 13/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 5/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 16 violations
- **Content_heavy:** ✅ Content-heavy OK (13 activities)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (fine-arts))
- **Richness:** ❌ 86% < 95% min (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 86% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 20 | 15 | 100% | 25% | 25.0% |
| engagement | 5 | 5 | 100% | 19% | 18.7% |
| variety | 1.00 | - | 100% | 12% | 12.5% |
| cultural | 6 | 4 | 100% | 12% | 12.5% |
| realworld | 1 | 3 | 33% | 12% | 4.1% |
| visual | 2 | 4 | 50% | 6% | 3.1% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 3 | 4 | 75% | 6% | 4.7% |
| **TOTAL** | | | | | **86.9%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Історія Сержа Лифаря | cloze | 8 | 12 | Add 4 more items |
| Балетні професії | select | 3 | 5 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 79 | Included in Core |
| **Вступ: Мова тіла як код ідентичності** | ✅ | 105 | Included in Core |
| **Серж Лифар: Ікар з Києва** | ⚪️ | 351 | Skipped |
| **Павло Вірський: Академія народного танцю** | ⚪️ | 355 | Skipped |
| **Класичний балет в Україні: Школа та традиції** | ⚪️ | 435 | Skipped |
| **Сучасний балет: Раду Поклітару та Київ Модерн-Балет** | ⚪️ | 165 | Skipped |
| **Аналіз** | ✅ | 231 | Included in Core |
| **Підсумок** | ✅ | 77 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 128 | Skipped |