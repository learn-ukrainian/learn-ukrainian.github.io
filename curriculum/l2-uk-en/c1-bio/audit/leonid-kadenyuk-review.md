# Audit Report: M112 — leonid-kadenyuk.md
**Level:** C1 | **Module:** M112 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:53

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
| 1 | reading | Первинні джерела: Спогади Леоніда Каденюка | 3 | 1 | ✅ |
| 2 | reading | Науковий нарис про космічну галузь України | 3 | 1 | ✅ |
| 3 | quiz | Розуміння біографії | 5 | 5 | ✅ |
| 4 | fill-in | Космічна лексика | 6 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз наукового тексту | 5 | 5 | ✅ |
| 6 | error-correction | Граматика в науковому контексті | 5 | 5 | ✅ |
| 7 | match-up | Космічні терміни та поняття | 8 | 6 | ✅ |
| 8 | true-false | Факти про політ Каденюка | 5 | 5 | ✅ |
| 9 | unjumble | Аналіз наукового значення | 5 | 5 | ✅ |
| 10 | group-sort | Атрибути космонавтики | 12 | 1 | ✅ |
| 11 | cloze | Зірковий шлях | 12 | 1 | ✅ |
| 12 | group-sort | Лексика успіху та досягнень | 12 | 1 | ✅ |
| 13 | essay-response | Творча робота: Україна космічна | 1 | 1 | ✅ |
| 14 | comparative-study | Каденюк та Попович: Порівняння | 1 | 1 | ✅ |

**Summary:**
- Total activities: 14 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in leonid-kadenyuk.yaml: Schema validation error at key 'options': ['Буковині', 'Донбасі', 'Поліссі'] is too short
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
- **Words:** ❌ 1971/4000 (raw: 2228)
- **Activities:** ✅ 14/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 14 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 99% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 6 | 3 | 100% | 14% | 14.3% |
| cultural | 4 | 4 | 100% | 10% | 9.5% |
| visual | 13 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 28 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 15 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **100.0%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 73 | Included in Core |
| **Вступ** | ✅ | 227 | Included in Core |
| **Біографія** | ⚪️ | 554 | Skipped |
| **Історичний контекст** | ✅ | 224 | Included in Core |
| **Порівняльний аналіз** | ✅ | 171 | Included in Core |
| **Есе** | ⚪️ | 373 | Skipped |
| **Підсумок** | ✅ | 49 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 187 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 113 | Skipped |