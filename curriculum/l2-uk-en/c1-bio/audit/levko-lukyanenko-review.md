# Audit Report: M102 — levko-lukyanenko.md
**Level:** C1 | **Module:** M102 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 19:27:38

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
| 2 | fill-in | Політична лексика | 6 | 6 | ✅ |
| 3 | error-correction | Граматика в біографічному тексті | 5 | 5 | ✅ |
| 4 | match-up | Терміни та визначення | 8 | 6 | ✅ |
| 5 | select | Аналіз діяльності Лук'яненка | 5 | 5 | ✅ |
| 6 | group-sort | Етапи життя та лексика | 18 | 1 | ✅ |
| 7 | fill-in | Прислівники та сполучники | 6 | 6 | ✅ |
| 8 | error-correction | Складні речення та пунктуація | 5 | 5 | ✅ |
| 9 | quiz | Критичне мислення | 5 | 5 | ✅ |
| 10 | true-false | Правда чи міф | 12 | 5 | ✅ |
| 11 | essay-response | Феномен незламності | 1 | 1 | ✅ |
| 12 | comparative-study | Дисиденти: Лук'яненко і Сахаров | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 9 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in levko-lukyanenko.yaml: Schema validation error at key '7': {'type': 'error-correction', 'title': 'Складні речення та пунктуація', 'items': [{'sentence': "Лук'яненко який пройшов табори став символом нації.", 'error': "Лук'яненко який", 'answer': "Лук'яненко, який", 'options': ["Лук'яненко який", "Лук'яненко, який", "Лук'яненко: який", 'none'], 'explanation': 'Виділення підрядного означального речення комами.'}, {'sentence': 'Він знав що Україна переможе.', 'error': 'знав що', 'answer': 'знав, що', 'options': ['знав що', 'знав, що', 'знав: що', 'none'], 'explanation': 'Кома перед сполучником «що» у складнопідрядному реченні.'}, {'sentence': 'Коли він вийшов на волю його зустрічали як героя.', 'error': 'волю його', 'answer': 'волю, його', 'options': ['волю його', 'волю, його', 'волю: його', 'none'], 'explanation': 'Кома між частинами складного речення.'}, {'sentence': 'Це була людина, яка не боялася смерті.', 'error': 'none', 'answer': '✓', 'options': ['людина', 'яка', 'смерті', '✓'], 'explanation': 'Речення побудоване правильно.'}, {'sentence': 'Він написав Акт, щоб Україна стала державою.', 'error': 'none', 'answer': '✓', 'options': ['Акт', 'щоб', 'державою', '✓'], 'explanation': 'Речення побудоване правильно.'}]} is not valid under any of the given schemas
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
- **Words:** ❌ 2209/4000 (raw: 2502)
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
- **Immersion:** 🇺🇦 100.0% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 11 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 12 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 12 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.1%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 74 | Included in Core |
| **Вступ** | ✅ | 178 | Included in Core |
| **Біографія** | ⚪️ | 770 | Skipped |
| **Історичний контекст** | ✅ | 295 | Included in Core |
| **Порівняльний аналіз** | ✅ | 169 | Included in Core |
| **Есе** | ⚪️ | 0 | Skipped |
| **Тема** | ⚪️ | 59 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 362 | Skipped |
| **Підсумок** | ✅ | 44 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 128 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 130 | Skipped |