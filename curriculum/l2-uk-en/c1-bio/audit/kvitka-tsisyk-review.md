# Audit Report: M114 — kvitka-tsisyk.md
**Level:** C1 | **Module:** M114 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:46

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, fill-in, group-sort, match-up, quiz, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | Життєвий шлях Квітки Цісик | 5 | 5 | ✅ |
| 2 | match-up | Музична та культурологічна термінологія | 8 | 6 | ✅ |
| 3 | group-sort | Характеристика творчості Квітки Цісик | 12 | 1 | ✅ |
| 4 | fill-in | Контекст створення українських альбомів | 6 | 6 | ✅ |
| 5 | quiz | Мистецький аналіз вокалу | 5 | 5 | ✅ |
| 6 | match-up | Синоніми та художні означення | 8 | 6 | ✅ |
| 7 | group-sort | Діяльність Квітки Цісик у США | 12 | 1 | ✅ |
| 8 | fill-in | Спадщина Квітки Цісик | 6 | 6 | ✅ |
| 9 | quiz | Роль діаспори у збереженні ідентичності | 5 | 5 | ✅ |
| 10 | group-sort | Лексика модуля: Квітка Цісик | 12 | 1 | ✅ |
| 11 | essay-response | Творча робота: Голос нації | 1 | 1 | ✅ |
| 12 | comparative-study | Квітка Цісик та сучасні виконавці фольклору | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 6 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in kvitka-tsisyk.yaml: Schema validation error at key '7': {'type': 'fill-in', 'title': 'Спадщина Квітки Цісик', 'items': [{'sentence': "Сьогодні Квітка Цісик є символом культурної [м'якої] сили України у світі.", 'answer': "м'якої", 'options': ["м'якої", 'жорсткої', 'фінансової', 'військової']}, {'sentence': 'Її приклад надихає сучасних музикантів експериментувати з [фольклором] та народною музикою.', 'answer': 'фольклором', 'options': ['фольклором', 'джазом', 'роком', 'шансоном']}, {'sentence': 'Голос Квітки став частиною сучасного українського культурного [коду].', 'answer': 'коду', 'options': ['коду', 'статуту', 'права', 'архіву']}, {'sentence': 'Вона довела, що щирість та професіоналізм здатні долати будь-які [кордони] та відстані.', 'answer': 'кордони', 'options': ['кордони', 'перешкоди', 'іспити', 'рівні']}, {'sentence': "Пам'ять про співачку в Україні вшановують назвами вулиць та мистецькими [фестивалями].", 'answer': 'фестивалями', 'options': ['фестивалями', 'мітингами', 'реформами', 'законами']}, {'sentence': 'Квітка назавжди залишиться для нас [білою] пташкою з українським серцем.', 'answer': 'білою', 'options': ['білою', 'чорною', 'синьою', 'золотою']}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Спадщина' per template 'c1-biography-module-template.md'
  - FIX: Add '## Спадщина' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 35/100)

- 5 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 2182/4000 (raw: 2461)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 6/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 10/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.4% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 4 | 100% | 19% | 19.0% |
| engagement | 10 | 6 | 100% | 14% | 14.3% |
| quotes | 12 | 3 | 100% | 14% | 14.3% |
| cultural | 6 | 4 | 100% | 10% | 9.5% |
| visual | 14 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 24 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.96 | - | 96% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **99.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ✅ | 199 | Included in Core |
| **Біографія** | ⚪️ | 788 | Skipped |
| **Історичний контекст** | ✅ | 237 | Included in Core |
| **Порівняльний аналіз** | ✅ | 159 | Included in Core |
| **Есе** | ⚪️ | 360 | Skipped |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 189 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 123 | Skipped |