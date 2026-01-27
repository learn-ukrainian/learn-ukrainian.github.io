# Audit Report: M100 — kateryna-yushchenko.md

**Level:** C1 | **Module:** M100 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:46

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
| 2 | fill-in | Технічна та наукова термінологія | 6 | 6 | ✅ |
| 3 | error-correction | Граматика в науковому контексті | 5 | 5 | ✅ |
| 4 | match-up | Світ кібернетики | 8 | 6 | ✅ |
| 5 | select | Аналіз наукового спадку | 5 | 5 | ✅ |
| 6 | group-sort | Класифікація понять IT-сфери | 18 | 1 | ✅ |
| 7 | fill-in | Прислівники та сполучники в науковому тексті | 6 | 6 | ✅ |
| 8 | error-correction | Складні синтаксичні зв'язки | 5 | 5 | ✅ |
| 9 | quiz | Критичне мислення та аналіз контексту | 5 | 5 | ✅ |
| 10 | true-false | Правда чи міф про Катерину Ющенко | 12 | 5 | ✅ |
| 11 | essay-response | Український слід у цифровій історії | 1 | 1 | ✅ |
| 12 | comparative-study | Жінки в історії IT: Лавлейс та Ющенко | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 9 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in kateryna-yushchenko.yaml: Schema validation error at key '7': {'type': 'error-correction', 'title': "Складні синтаксичні зв'язки", 'items': [{'sentence': 'Вона була жінкою яка бачила майбутнє.', 'error': 'жінкою яка', 'answer': 'жінкою, яка', 'options': ['жінкою яка', 'жінкою, яка', 'жінкою: яка', 'none'], 'explanation': 'Кома перед підрядним реченням.'}, {'sentence': 'Вона знала, що машина може більше ніж просто рахувати.', 'error': 'більше ніж', 'answer': 'більше, ніж', 'options': ['більше ніж', 'більше, ніж', 'більше: ніж', 'none'], 'explanation': 'Кома перед порівняльним сполучником «ніж».'}, {'sentence': 'Працюючи в лабораторії вона зробила відкриття.', 'error': 'в лабораторії вона', 'answer': 'в лабораторії, вона', 'options': ['в лабораторії вона', 'в лабораторії, вона', 'в лабораторії: вона', 'none'], 'explanation': 'Кома після дієприслівникового звороту.'}, {'sentence': 'Це був успіх української математичної школи.', 'error': 'none', 'answer': '✓', 'options': ['успіх', 'школи', 'математичної', '✓'], 'explanation': 'Речення побудоване правильно.'}, {'sentence': "Її ім'я вписане золотими буквами в історії науки.", 'error': 'в історії', 'answer': 'в історію', 'options': ['в історії', 'в історію', 'в історією', 'none'], 'explanation': 'Знахідний відмінок після дієслова «вписане у що?».'}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE

- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Життєпис' per template 'c1-biography-module-template.md'
  - FIX: Add '## Життєпис' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Внесок' per template 'c1-biography-module-template.md'
  - FIX: Add '## Внесок' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation

**📝 UPDATE** (severity 35/100)

- 4 violations (moderate)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates

- **Words:** ❌ 2030/4000 (raw: 2304)
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
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 8 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.97 | - | 97% | 5% | 4.6% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 70 | Included in Core |
| **Вступ** | ✅ | 205 | Included in Core |
| **Біографія** | ⚪️ | 541 | Skipped |
| **Історичний контекст** | ✅ | 338 | Included in Core |
| **Порівняльний аналіз** | ✅ | 170 | Included in Core |
| **Есе** | ⚪️ | 0 | Skipped |
| **Тема** | ⚪️ | 62 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 356 | Skipped |
| **Підсумок** | ✅ | 53 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 118 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 117 | Skipped |
