# Audit Report: M88 — 88-ukrainske-kino.md

**Level:** C1 | **Module:** M88 | **Phase:** C1 | **Pedagogy:** CBI | **Target:** 3000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:29:49

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
| 1 | quiz | Історія українського кіно | 12 | 5 | ✅ |
| 2 | match-up | Режисери та їхні фільми | 10 | 6 | ✅ |
| 3 | cloze | Поетичне кіно | 9 | 12 | ❌ |
| 4 | fill-in | Кінематографічна лексика | 10 | 6 | ✅ |
| 5 | essay-response | Есе: Українське кіно сьогодні | 1 | 1 | ✅ |
| 6 | true-false | Факти про кіно | 10 | 5 | ✅ |
| 7 | group-sort | Жанри кіно | 12 | 12 | ✅ |
| 8 | mark-the-words | Враження від фільму | 6 | 5 | ✅ |
| 9 | translate | Кінотерміни | 5 | 5 | ✅ |
| 10 | unjumble | Цитати про кіно | 6 | 5 | ✅ |
| 11 | select | Сучасні українські фільми | 3 | 5 | ❌ |
| 12 | reading | Довженко-Центр | 3 | 3 | ✅ |
| 13 | critical-analysis | Аналіз фільму «Земля» | 1 | 1 | ✅ |
| 14 | comparative-study | Поетичне vs Реалістичне | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 12-16) ✅
- Unique types: 14 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS

- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського кіно' Q2 prompt length 7 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського кіно' Q4 prompt length 4 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського кіно' Q9 prompt length 5 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського кіно' Q10 prompt length 4 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Історія українського кіно' Q12 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про кіно' item 1 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про кіно' item 2 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про кіно' item 3 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про кіно' item 4 has 6 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про кіно' item 5 has 6 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Цитати про кіно' item 6 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY]** select 'Сучасні українські фільми' has 3 items (minimum: 5)
  - FIX: Add more items. C1 select requires at least 5 items.
- **[HEADING_LEVEL]** Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Підсумок' to '# Підсумок' for top-level TOC compliance
- **[YAML_SCHEMA_VIOLATION]** Schema error in 88-ukrainske-kino.yaml: Schema validation error at key '10': {'type': 'select', 'title': 'Сучасні українські фільми', 'items': [{'question': 'Який фільм зняв Антоніо Лукіч?', 'options': [{'text': '«Люксембург, Люксембург»', 'correct': True}, {'text': '«Додому»', 'correct': False}, {'text': "«Плем'я»", 'correct': False}, {'text': '«Кіборги»', 'correct': False}, {'text': '«Мої думки тихі»', 'correct': True}], 'min_correct': 2}, {'question': 'Які фільми про війну варто подивитися?', 'options': [{'text': '«Кіборги»', 'correct': True}, {'text': '«Атлантида»', 'correct': True}, {'text': '«Погані дороги»', 'correct': True}, {'text': '«Скажене весілля»', 'correct': False}, {'text': '«Dzidzio Контрабас»', 'correct': False}], 'min_correct': 3}, {'question': 'Які актори відомі в Україні?', 'options': [{'text': 'Станіслав Боклан', 'correct': True}, {'text': 'Ірма Вітовська', 'correct': True}, {'text': 'Ахтем Сеітаблаєв', 'correct': True}, {'text': 'Бред Пітт', 'correct': False}, {'text': 'Леонардо Ді Капріо', 'correct': False}], 'min_correct': 3}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Аналіз' per template 'c1-module-template.md'
  - FIX: Add '## Аналіз' section as specified in docs/l2-uk-en/templates/c1-module-template.md.md

## Recommendation

**🔄 REWRITE** (severity 80/100)

- 15 violations (severe - consider revision)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar
- Activity density below minimum

## Gates

- **Words:** ❌ 1148/3000 (raw: 1233)
- **Activities:** ✅ 14/12
- **Density:** ❌ 2 < 12
- **Unique_types:** ✅ 14/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 3/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.4% (target 90-100% (fine-arts))
- **Richness:** ❌ 75% < 95% min (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 75% (minimum: 95%)
**Module Type:** content

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 30 | 15 | 100% | 25% | 25.0% |
| engagement | 3 | 5 | 60% | 19% | 11.2% |
| variety | 1.00 | - | 100% | 12% | 12.5% |
| cultural | 7 | 4 | 100% | 12% | 12.5% |
| realworld | 0 | 3 | 0% | 12% | 0.0% |
| visual | 2 | 4 | 50% | 6% | 3.1% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 3 | 4 | 75% | 6% | 4.7% |
| **TOTAL** | | | | | **75.3%** |

### Dryness Flags & Fixes

- ❌ **ABSTRACT_ONLY**
  - FIX:
    Add 3+ real-world boxes. Use this exact format:

    > 🌍 **У реальному житті**
    >
    > [Specific scenario: "На співбесіді...", "У магазині...", "На вокзалі..."]
    > [Example sentence showing grammar in that context]

## Low Density Activities

| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Поетичне кіно | cloze | 9 | 12 | Add 3 more items |
| Сучасні українські фільми | select | 3 | 5 | Add 2 more items |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 67 | Included in Core |
| **Вступ: Від німого до цифрового** | ✅ | 80 | Included in Core |
| **Олександр Довженко: Поет камери** | ⚪️ | 149 | Skipped |
| **Українське поетичне кіно** | ⚪️ | 208 | Skipped |
| **Одеський феномен: Кіра Муратова** | ⚪️ | 43 | Skipped |
| **Анімація: Від козаків до Мавки** | ⚪️ | 47 | Skipped |
| **Застій і відродження: 90-ті та 2000-ні** | ⚪️ | 71 | Skipped |
| **Нова хвиля: Після 2014 року** | ⚪️ | 231 | Skipped |
| **Документальне кіно: Свідок історії** | ⚪️ | 76 | Skipped |
| **Актори та Фестивалі** | ⚪️ | 58 | Skipped |
| **Підсумок** | ✅ | 47 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 71 | Skipped |
