# Audit Report: M86 — 86-ukrainska-arkhitektura.md

**Level:** C1 | **Module:** M86 | **Phase:** C1 | **Pedagogy:** CBI | **Target:** 3000
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:29:48

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
| 1 | quiz | Шедеври української архітектури | 12 | 5 | ✅ |
| 2 | match-up | Архітектурні стилі та пам'ятки | 10 | 6 | ✅ |
| 3 | cloze | Козацьке бароко | 9 | 12 | ❌ |
| 4 | fill-in | Архітектурна лексика | 10 | 6 | ✅ |
| 5 | essay-response | Есе: Камінь і дерево | 1 | 1 | ✅ |
| 6 | true-false | Факти про архітектуру | 10 | 5 | ✅ |
| 7 | group-sort | Архітектурні епохи | 12 | 12 | ✅ |
| 8 | mark-the-words | Опис собору | 9 | 5 | ✅ |
| 9 | translate | Архітектурні описи | 5 | 5 | ✅ |
| 10 | unjumble | Думки про архітектуру | 6 | 5 | ✅ |
| 11 | select | Стилі української архітектури | 3 | 5 | ❌ |
| 12 | reading | Відбудова України | 3 | 3 | ✅ |
| 13 | critical-analysis | Аналіз стилю модернізм | 1 | 1 | ✅ |
| 14 | comparative-study | Сакральне vs Світське | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 12-16) ✅
- Unique types: 14 (minimum: 4) ✅
- Priority types used: 2/3 (fill-in, unjumble) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS

- **[COMPLEXITY_WORD_COUNT]** quiz 'Шедеври української архітектури' Q3 prompt length 4 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Шедеври української архітектури' Q7 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Шедеври української архітектури' Q8 prompt length 3 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Шедеври української архітектури' Q10 prompt length 6 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Шедеври української архітектури' Q12 prompt length 3 (target: 8-30)
  - FIX: Adjust prompt length to 8-30 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про архітектуру' item 1 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про архітектуру' item 2 has 9 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про архітектуру' item 3 has 9 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про архітектуру' item 4 has 9 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про архітектуру' item 5 has 8 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Думки про архітектуру' item 6 has 10 words (target: 12-20)
  - FIX: Adjust sentence length to 12-20 words to match C1 complexity.
- **[COMPLEXITY]** select 'Стилі української архітектури' has 3 items (minimum: 5)
  - FIX: Add more items. C1 select requires at least 5 items.
- **[HEADING_LEVEL]** Main section 'Підсумок' uses H2 (##) but spec requires H1 (#)
  - FIX: Change '## Підсумок' to '# Підсумок' for top-level TOC compliance
- **[YAML_SCHEMA_VIOLATION]** Schema error in 86-ukrainska-arkhitektura.yaml: Schema validation error at key '10': {'type': 'select', 'title': 'Стилі української архітектури', 'items': [{'question': 'Які стилі можна побачити в Києві?', 'options': [{'text': 'Бароко', 'correct': True}, {'text': 'Модерн', 'correct': True}, {'text': 'Конструктивізм', 'correct': True}, {'text': 'Готика (неоготика)', 'correct': True}, {'text': 'Єгипетський стиль', 'correct': False}], 'min_correct': 3}, {'question': 'Що входить до комплексу Києво-Печерської лаври?', 'options': [{'text': 'Успенський собор', 'correct': True}, {'text': 'Велика лаврська дзвіниця', 'correct': True}, {'text': 'Троїцька надбрамна церква', 'correct': True}, {'text': 'Печери', 'correct': True}, {'text': 'Золоті Ворота', 'correct': False}], 'min_correct': 3}, {'question': 'Які матеріали традиційні для українського будівництва?', 'options': [{'text': 'Дерево', 'correct': True}, {'text': 'Глина (мазанка)', 'correct': True}, {'text': 'Цегла (плінфа)', 'correct': True}, {'text': 'Бамбук', 'correct': False}, {'text': 'Лід', 'correct': False}], 'min_correct': 3}]} is not valid under any of the given schemas
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

- **Words:** ❌ 1373/3000 (raw: 1468)
- **Activities:** ✅ 14/12
- **Density:** ❌ 2 < 12
- **Unique_types:** ✅ 14/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 4/7
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 14 violations
- **Content_heavy:** ✅ Content-heavy OK (14 activities)
- **Immersion:** 🇺🇦 99.0% (target 90-100% (fine-arts))
- **Richness:** ❌ 75% < 95% min (content)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 0/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 75% (minimum: 95%)
**Module Type:** content

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 12 | 15 | 80% | 25% | 20.0% |
| engagement | 4 | 5 | 80% | 19% | 15.0% |
| variety | 1.00 | - | 100% | 12% | 12.5% |
| cultural | 14 | 4 | 100% | 12% | 12.5% |
| realworld | 0 | 3 | 0% | 12% | 0.0% |
| visual | 2 | 4 | 50% | 6% | 3.1% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.2% |
| questions | 8 | 4 | 100% | 6% | 6.2% |
| **TOTAL** | | | | | **75.6%** |

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
| Козацьке бароко | cloze | 9 | 12 | Add 3 more items |
| Стилі української архітектури | select | 3 | 5 | Add 2 more items |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 68 | Included in Core |
| **Вступ: Простір і дух** | ✅ | 91 | Included in Core |
| **Київська Русь: Золотоверхий канон** | ⚪️ | 159 | Skipped |
| **Українське бароко: Мазепинський стиль** | ⚪️ | 163 | Skipped |
| **Дерев'яна архітектура: Карпатський феномен** | ⚪️ | 117 | Skipped |
| **Замки та фортеці: Кам'яна варта** | ⚪️ | 63 | Skipped |
| **Модерн і Еклектика: Місто XIX століття** | ⚪️ | 165 | Skipped |
| **Радянський період: Конструктивізм і Ампір** | ⚪️ | 128 | Skipped |
| **Модернізм другої хвилі та Бруталізм** | ⚪️ | 129 | Skipped |
| **Сучасна архітектура та відбудова** | ⚪️ | 152 | Skipped |
| **Підсумок** | ✅ | 61 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 77 | Skipped |
