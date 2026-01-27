# Audit Report: M108 — vasyl-stus.md

**Level:** C1 | **Module:** M108 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:51

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
| 1 | reading | Первинні джерела: Поезія Василя Стуса | 3 | 1 | ✅ |
| 2 | reading | Науковий нарис про «Палімпсести» | 3 | 1 | ✅ |
| 3 | quiz | Розуміння біографії | 5 | 5 | ✅ |
| 4 | fill-in | Лексика стоїцизму | 6 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз поетичного тексту | 5 | 5 | ✅ |
| 6 | error-correction | Граматика в літературному контексті | 5 | 5 | ✅ |
| 7 | match-up | Поняття та дефініції | 8 | 6 | ✅ |
| 8 | true-false | Трагічний шлях Стуса | 5 | 5 | ✅ |
| 9 | unjumble | Цитати про вертикальне стояння | 5 | 5 | ✅ |
| 10 | group-sort | Філософські та табірні реалії | 12 | 1 | ✅ |
| 11 | cloze | Доля Поета | 12 | 1 | ✅ |
| 12 | group-sort | Лексичні пласти духу | 12 | 1 | ✅ |
| 13 | group-sort | Світ Стуса | 12 | 1 | ✅ |
| 14 | essay-response | Творча робота: Феномен Стуса | 1 | 1 | ✅ |
| 15 | comparative-study | Стус та європейський модернізм: Порівняння | 1 | 1 | ✅ |

**Summary:**
- Total activities: 15 (target: 3-9) ❌
- Unique types: 12 (minimum: 3) ✅
- Priority types used: 4/6 (comparative-study, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS

- **[YAML_SCHEMA_VIOLATION]** Schema error in vasyl-stus.yaml: Schema validation error at key 'options': ['Вінниччині', 'Донеччині', 'Одещині'] is too short
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

- **Words:** ❌ 2250/4000 (raw: 2550)
- **Activities:** ✅ 15/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 12/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 15 (target 3-9)
- **Immersion:** 🇺🇦 99.9% (target 95-100% (biography))
- **Richness:** ✅ 97% (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details

**Score:** 97% (minimum: 95%)
**Module Type:** biography

### Score Breakdown

| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 11 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 15 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 13 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 16 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.6%** |

## Section Audit

| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 72 | Included in Core |
| **Вступ** | ✅ | 217 | Included in Core |
| **Біографія** | ⚪️ | 746 | Skipped |
| **Історичний контекст** | ✅ | 223 | Included in Core |
| **Порівняльний аналіз** | ✅ | 207 | Included in Core |
| **Есе** | ⚪️ | 383 | Skipped |
| **Підсумок** | ✅ | 58 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 215 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 129 | Skipped |
