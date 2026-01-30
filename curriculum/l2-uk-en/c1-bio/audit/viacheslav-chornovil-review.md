# Audit Report: M107 — viacheslav-chornovil.md
**Level:** C1 | **Module:** M107 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-30 21:15:42

## Configuration
**Type:** C1-biography
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥3 types required
**Priority Types:** authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 95-100%
**Vocab Target:** ≥24 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | reading | Первинні джерела: Промова В'ячеслава Чорновола | 3 | 1 | ✅ |
| 2 | reading | Науковий нарис про дисидентський рух | 3 | 1 | ✅ |
| 3 | true-false | Факти про Чорновола та Рух | 5 | 5 | ✅ |
| 4 | essay-response | Творча робота: Уроки Чорновола | 1 | 1 | ✅ |
| 5 | comparative-study | Чорновіл та дисиденти: Порівняння | 1 | 1 | ✅ |

**Summary:**
- Total activities: 5 (target: 3-9) ✅
- Unique types: 4 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in viacheslav-chornovil.yaml: Schema validation error at key '1': {'type': 'reading', 'title': 'Науковий нарис про дисидентський рух', 'resource': {'type': 'article', 'url': 'https://history.vn.ua/pidruchniki/ukraine-history-11-class-vlasov-2019-standard-level/16.php', 'title': "Дисидентський рух: В'ячеслав Чорновіл та «Український вісник»"}, 'tasks': ['Яку роль відіграв часопис «Український вісник» у прориві інформаційної блокади?', 'Проаналізуйте лексику, що описує судові процеси над дисидентами.', 'Як історики оцінюють внесок Чорновола у перехід від правозахисної до політичної боротьби?']} is not valid under any of the given schemas
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
- **Words:** ❌ 1984/4000 (raw: 2252)
- **Activities:** ✅ 5/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 4/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (5 activities)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 95% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 95% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 8 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 2 | 4 | 50% | 10% | 4.8% |
| visual | 13 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 29 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **95.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 71 | Included in Core |
| **Вступ** | ✅ | 190 | Included in Core |
| **Біографія** | ⚪️ | 544 | Skipped |
| **Історичний контекст** | ✅ | 242 | Included in Core |
| **Порівняльний аналіз** | ✅ | 201 | Included in Core |
| **Есе** | ⚪️ | 388 | Skipped |
| **Підсумок** | ✅ | 54 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 175 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 119 | Skipped |