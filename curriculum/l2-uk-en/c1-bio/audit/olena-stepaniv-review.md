# Audit Report: M83 — olena-stepaniv.md
**Level:** C1 | **Module:** M83 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-26 22:56:39

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
| 1 | quiz | Розуміння тексту: Життя Олени Степанів | 5 | 5 | ✅ |
| 2 | fill-in | Лексика: Війна, Наука та Героїзм | 6 | 6 | ✅ |
| 3 | error-correction | Граматика: Опис біографії | 5 | 5 | ✅ |
| 4 | match-up | Військова та історична термінологія | 8 | 6 | ✅ |
| 5 | select | Лінгвістичний аналіз спогадів | 5 | 5 | ✅ |
| 6 | group-sort | Етапи життя Олени Степанів | 12 | 1 | ✅ |
| 7 | true-false | Факти про Олену Степанів | 5 | 5 | ✅ |
| 8 | authorial-intent | Намір автора: Жінка на війні | 1 | 1 | ✅ |
| 9 | essay-response | Аналіз феномену: Жінка-воїн | 1 | 1 | ✅ |
| 10 | comparative-study | Порівняння: Степанів та Жанна д’Арк | 1 | 1 | ✅ |
| 11 | critical-analysis | Аналіз радянських репресій | 1 | 1 | ✅ |
| 12 | translate | Переклад термінів: Військо та Наука | 5 | 5 | ✅ |
| 13 | reading | Спогади Олени Степанів | 3 | 1 | ✅ |

**Summary:**
- Total activities: 13 (target: 3-9) ❌
- Unique types: 13 (minimum: 3) ✅
- Priority types used: 6/6 (authorial-intent, comparative-study, critical-analysis, essay-response, quiz, reading) ✅
- Required types used: 6/6 (essay-response, fill-in, group-sort, match-up, quiz, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in olena-stepaniv.yaml: Schema validation error at key '12': {'type': 'reading', 'title': 'Спогади Олени Степанів', 'resource': {'type': 'primary_source', 'url': 'https://elib.nlu.org.ua/', 'title': 'Олена Степанів: Напередодні великих подій'}, 'tasks': ['Знайдіть у тексті опис мотивації вступу до УСС.', 'Які емоції описує авторка перед першим боєм?', 'Випишіть 5 військових термінів, вжитих у тексті.']} is not valid under any of the given schemas
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
- **Words:** ❌ 2533/4000 (raw: 2815)
- **Activities:** ✅ 13/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 13/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 9/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ⚠️ Too many activities: 13 (target 3-9)
- **Immersion:** 🇺🇦 99.8% (target 95-100% (biography))
- **Richness:** ❌ 92% < 95% min (biography)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ❌ 1/10 (PENDING) - Naturalness check required

## Richness Details
**Score:** 92% (minimum: 95%)
**Module Type:** biography

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 5 | 4 | 100% | 19% | 19.0% |
| engagement | 9 | 6 | 100% | 14% | 14.3% |
| quotes | 14 | 3 | 100% | 14% | 14.3% |
| cultural | 1 | 4 | 25% | 10% | 2.4% |
| visual | 12 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 30 | 8 | 100% | 10% | 9.5% |
| legacy | 15 | 2 | 100% | 10% | 9.5% |
| variety | 0.99 | - | 99% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 21 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 113 | Included in Core |
| **Вступ** | ✅ | 239 | Included in Core |
| **Біографія** | ⚪️ | 742 | Skipped |
| **Сучасний контекст** | ✅ | 241 | Included in Core |
| **Історичний контекст** | ✅ | 458 | Included in Core |
| **Порівняльний аналіз** | ✅ | 224 | Included in Core |
| **Підсумок** | ✅ | 169 | Included in Core |
| **Практикум рефлексії** | ⚪️ | 210 | Skipped |
| **Потрібно більше практики?** | ⚪️ | 137 | Skipped |