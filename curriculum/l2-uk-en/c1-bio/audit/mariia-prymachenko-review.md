# Audit Report: M96 — mariia-prymachenko.md
**Level:** C1 | **Module:** M96 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:45

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
| 2 | fill-in | Мистецтвознавча та фольклорна лексика | 6 | 6 | ✅ |
| 3 | error-correction | Граматика в описі художнього стилю | 5 | 5 | ✅ |
| 4 | match-up | Художні засоби та образи | 8 | 6 | ✅ |
| 5 | select | Аналіз візуальної мови Примаченко | 5 | 5 | ✅ |
| 6 | group-sort | Кольори та настрої наївного мистецтва | 16 | 1 | ✅ |
| 7 | fill-in | Прислівники та епітети | 6 | 6 | ✅ |
| 8 | error-correction | Складні прикметники та узгодження | 5 | 5 | ✅ |
| 9 | quiz | Глибинний аналіз творчості | 5 | 5 | ✅ |
| 10 | true-false | Правда чи міф про Марію Примаченко | 12 | 5 | ✅ |
| 11 | essay-response | Феномен Марії Примаченко | 1 | 1 | ✅ |
| 12 | comparative-study | Дві грані українського наїву: Примаченко та Білокур | 1 | 1 | ✅ |

**Summary:**
- Total activities: 12 (target: 3-9) ❌
- Unique types: 9 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, quiz) ✅
- Required types used: 5/6 (essay-response, fill-in, group-sort, match-up, quiz) ❌
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in mariia-prymachenko.yaml: Schema validation error at key '7': {'type': 'error-correction', 'title': 'Складні прикметники та узгодження', 'items': [{'sentence': 'Вона створила глибоко філософську серію робіт про атомну загрозу.', 'error': 'глибоко філософську', 'answer': 'глибокофілософську', 'options': ['глибоко філософську', 'глибокофілософську', 'глибоко-філософську', 'none'], 'explanation': 'Складні прикметники, де одна частина залежить від іншої, пишуться разом.'}, {'sentence': 'Її диво-звірі мають ярко-сині та яскраво-жовті кольори.', 'error': 'ярко-сині', 'answer': 'яскраво-сині', 'options': ['ярко-сині', 'яскраво-сині', 'яркосині', 'none'], 'explanation': 'Назви відтінків кольорів пишуться через дефіс, правильно «яскраво».'}, {'sentence': 'Поліська природа дарувала їй багато ідей для творчості.', 'error': 'none', 'answer': '✓', 'options': ['дарувала', 'ідей', 'природа', '✓'], 'explanation': 'Речення побудоване правильно.'}, {'sentence': 'Картина була врятована з палаючого будівлі музею.', 'error': 'з палаючого', 'answer': 'з палаючої', 'options': ['з палаючого', 'з палаючої', 'з палаючою', 'none'], 'explanation': 'Прикметник (дієприкметник) має узгоджуватися з іменником «будівля» (жін. рід).'}, {'sentence': 'Примаченко є найвідоміша художниця українського наїву.', 'error': 'найвідоміша', 'answer': 'найвідомішою', 'options': ['найвідоміша', 'найвідомішою', 'найвідомішу', 'none'], 'explanation': 'Орудний відмінок у ролі іменної частини присудка.'}]} is not valid under any of the given schemas
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
- **Words:** ❌ 2576/4000 (raw: 2901)
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
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 6 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 7 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 10 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 20 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 87 | Included in Core |
| **Вступ** | ✅ | 231 | Included in Core |
| **Біографія** | ⚪️ | 846 | Skipped |
| **Історичний контекст** | ✅ | 355 | Included in Core |
| **Порівняльний аналіз** | ✅ | 203 | Included in Core |
| **Есе** | ⚪️ | 0 | Skipped |
| **Тема** | ⚪️ | 70 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 356 | Skipped |
| **Підсумок** | ✅ | 69 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 179 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 180 | Skipped |