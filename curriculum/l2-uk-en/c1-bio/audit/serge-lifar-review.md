# Audit Report: M91 — serge-lifar.md

**Level:** C1 | **Module:** M91 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:44

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
| 1 | quiz | Розуміння біографії | 5 | 5 | ✅ |
| 2 | fill-in | Балетна термінологія та лексика | 6 | 6 | ✅ |
| 3 | error-correction | Граматика в мистецтвознавчому тексті | 5 | 5 | ✅ |
| 4 | match-up | Поняття та визначення | 8 | 6 | ✅ |
| 5 | select | Аналіз реформ Лифаря | 5 | 5 | ✅ |
| 6 | group-sort | Елементи театрального світу | 15 | 1 | ✅ |
| 7 | fill-in | Якості та характеристики митця | 6 | 6 | ✅ |
| 8 | error-correction | Синтаксис та пунктуація | 5 | 5 | ✅ |
| 9 | quiz | Глибинний аналіз біографії | 5 | 5 | ✅ |
| 10 | true-false | Правда чи міф про Сержа Лифаря | 12 | 5 | ✅ |
| 11 | essay-response | Ідентичність у вигнанні | 1 | 1 | ✅ |
| 12 | comparative-study | Порівняння балетних шкіл: Лифар та класична традиція | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 9 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in serge-lifar.yaml: Schema validation error at key '7': {'type': 'error-correction', 'title': 'Синтаксис та пунктуація', 'items': [{'sentence': 'Серж Лифар будучи киянином за походженням підкорив весь світ.', 'error': 'будучи киянином за походженням', 'answer': ', будучи киянином за походженням,', 'options': ['будучи киянином за походженням', ', будучи киянином за походженням,', 'будучи киянином за походженням!', 'none'], 'explanation': 'Дієприслівниковий зворот має виділятися комами з обох боків.'}, {'sentence': 'На його могилі написано що він з Києва.', 'error': 'написано що', 'answer': 'написано, що', 'options': ['написано що', 'написано, що', 'написано: що', 'none'], 'explanation': 'Перед сполучником «що» у складнопідрядному реченні ставиться кома.'}, {'sentence': 'Лифар створив балети які стали класикою.', 'error': 'балети які', 'answer': 'балети, які', 'options': ['балети які', 'балети, які', 'балети: які', 'none'], 'explanation': 'Перед відносним займенником «які» у підрядному реченні ставиться кома.'}, {'sentence': 'Працюючи в Опері він реформував систему навчання.', 'error': 'в Опері він', 'answer': 'в Опері, він', 'options': ['в Опері він', 'в Опері, він', 'в Опері: він', 'none'], 'explanation': 'Кома після дієприслівникового звороту на початку речення.'}, {'sentence': 'Він ніколи не забував про своє коріння, незважаючи на славу.', 'error': 'none', 'answer': '✓', 'options': ['про', 'незважаючи', 'на', '✓'], 'explanation': 'Речення побудоване правильно.'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 25/100)

- 3 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2530/4000 (raw: 2868)
- **Activities:** ✅ 12/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 9/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 12 (target 3-9)
- **Immersion:** 🇺🇦 99.7% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 85 | Included in Core |
| **Вступ** | ✅ | 217 | Included in Core |
| **Біографія** | ⚪️ | 768 | Skipped |
| **Історичний контекст** | ✅ | 409 | Included in Core |
| **Порівняльний аналіз** | ✅ | 217 | Included in Core |
| **Есе** | ⚪️ | 0 | Skipped |
| **Тема** | ⚪️ | 66 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 367 | Skipped |
| **Підсумок** | ✅ | 65 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 161 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 175 | Skipped |
