# Audit Report: M87 — 87-suchasna-muzyka.md
**Level:** C1 | **Module:** M87 | **Phase:** C1.5 | **Pedagogy:** CBI | **Target:** 3000
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-06 20:13:35

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
| 1 | quiz | Історія українського шоу-бізнесу | 12 | 5 | ✅ |
| 2 | match-up | Виконавці та їхні хіти | 10 | 6 | ✅ |
| 3 | cloze | Феномен Євробачення | 9 | 12 | ❌ |
| 4 | fill-in | Музична термінологія | 10 | 6 | ✅ |
| 5 | essay-response | Есе: Музика свободи | 1 | 1 | ✅ |
| 6 | true-false | Факти про музикантів | 10 | 5 | ✅ |
| 7 | group-sort | Музичні жанри | 15 | 12 | ✅ |
| 8 | mark-the-words | Опис концерту | 7 | 5 | ✅ |
| 9 | translate | Музичні фрази | 5 | 5 | ✅ |
| 10 | unjumble | Думки про музику | 6 | 5 | ✅ |
| 11 | select | Жанри сучасної музики | 3 | 5 | ❌ |
| 12 | reading | Феномен «Стефанії» | 3 | 3 | ✅ |
| 13 | critical-analysis | Аналіз тексту «Ой у лузі червона калина» | 1 | 1 | ✅ |
| 14 | comparative-study | Естрада vs Інді | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 12-16) ✅
- Unique types: 14 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського шоу-бізнесу' Q5 prompt length 5 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського шоу-бізнесу' Q7 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського шоу-бізнесу' Q9 prompt length 4 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського шоу-бізнесу' Q11 prompt length 7 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про музику' item 1 has 9 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про музику' item 2 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про музику' item 3 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про музику' item 4 has 9 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про музику' item 5 has 7 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про музику' item 6 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY]** select 'Жанри сучасної музики' has 3 items (minimum: 5)
  - FIX: Add more items. C1 select requires at least 5 items.
- **[HEADING_LEVEL]** Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Підсумок' to '# Підсумок' for top-level TOC compliance
- **[YAML_SCHEMA_VIOLATION]** Schema error in 87-suchasna-muzyka.yaml: Schema validation error at key '10': {'type': 'select', 'title': 'Жанри сучасної музики', 'items': [{'question': 'Що співає alyona alyona?', 'options': [{'text': 'Реп', 'correct': True}, {'text': 'Хіп-хоп', 'correct': True}, {'text': 'Оперу', 'correct': False}, {'text': 'Джаз', 'correct': False}, {'text': 'Рок', 'correct': False}], 'min_correct': 2}, {'question': 'Яку музику грає ONUKA?', 'options': [{'text': 'Електро-фолк', 'correct': True}, {'text': 'Експериментальну', 'correct': True}, {'text': 'Інструментальну', 'correct': True}, {'text': 'Шансон', 'correct': False}, {'text': 'Панк-рок', 'correct': False}], 'min_correct': 3}, {'question': 'Хто співає рок?', 'options': [{'text': 'The Hardkiss', 'correct': True}, {'text': 'Океан Ельзи', 'correct': True}, {'text': 'Без Обмежень', 'correct': True}, {'text': 'Тіна Кароль', 'correct': False}, {'text': 'Ірина Федишин', 'correct': False}], 'min_correct': 3}], 'instruction': 'Оберіть усі правильні відповіді.'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## Recommendation
**🔄 REWRITE** (severity 80/100)

- 13 violations (severe - consider revision)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar
- Activity density below minimum

## Gates
- **Words:** ❌ 1138/3000 (raw: 1212)
- **Activities:** ✅ 14/12
- **Density:** ❌ 2 < 12
- **Unique_types:** ✅ 14/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 4/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 13 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 95.8% (target 90-100% (fine-arts))
- **Richness:** ❌ 78% < 95% min (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review

## Richness Details
**Score:** 78% (minimum: 95%)
**Module Type:** content

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 24 | 15 | 100% | 25% | 25.0% |
| engagement | 4 | 5 | 80% | 19% | 15.0% |
| variety | 0.99 | - | 99% | 12% | 12.4% |
| cultural | 3 | 4 | 75% | 12% | 9.4% |
| realworld | 1 | 3 | 33% | 12% | 4.1% |
| visual | 2 | 4 | 50% | 6% | 3.1% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 2 | 4 | 50% | 6% | 3.1% |
| **TOTAL** | | | | | **78.4%** |

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Феномен Євробачення | cloze | 9 | 12 | Add 3 more items |
| Жанри сучасної музики | select | 3 | 5 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 60 | Included in Core |
| **Вступ: Від «вусатого фанку» до електроніки** | ✅ | 93 | Included in Core |
| **Рок-легенди: ВВ та Океан Ельзи** | ⚪️ | 208 | Skipped |
| **Телевізійна ера: «Територія А»** | ⚪️ | 40 | Skipped |
| **Феномен Євробачення** | ⚪️ | 197 | Skipped |
| **Поп-діви і Рок-діви: Тіна Кароль і The Hardkiss** | ⚪️ | 62 | Skipped |
| **Електро-фолк та Інді: ONUKA, Go_A, Один в каное** | ⚪️ | 72 | Skipped |
| **Індустрія кліпмейкінгу** | ⚪️ | 44 | Skipped |
| **Реп та Хіп-хоп** | ⚪️ | 96 | Skipped |
| **Музика війни: Саундтрек спротиву** | ⚪️ | 151 | Skipped |
| **Підсумок** | ✅ | 52 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 63 | Skipped |