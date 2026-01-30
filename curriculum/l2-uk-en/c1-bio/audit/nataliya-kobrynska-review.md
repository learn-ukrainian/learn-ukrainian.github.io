# Audit Report: M45 — nataliya-kobrynska.md
**Level:** C1 | **Module:** M45 | **Phase:** C1 | **Pedagogy:** Not Specified | **Target:** 4000
**Naturalness:** 1/10 (PENDING)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-30 21:15:13

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
| 1 | essay-response | Критичний аналіз: Економіка і Свобода | 1 | 1 | ✅ |
| 2 | comparative-study | Порівняння епох | 1 | 1 | ✅ |
| 3 | reading | Аналіз новели | 3 | 1 | ✅ |
| 4 | essay-response | Есе: Право бути людиною | 1 | 1 | ✅ |

**Summary:**
- Total activities: 4 (target: 3-9) ✅
- Unique types: 3 (minimum: 3) ✅
- Priority types used: 3/6 (comparative-study, essay-response, reading) ✅
- Required types used: 2/2 (essay-response, reading) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in nataliya-kobrynska.yaml: Schema validation error at key '2': {'type': 'reading', 'title': 'Аналіз новели', 'resource': {'type': 'text', 'url': 'https://www.ukrlib.com.ua/books/printit.php?tid=1027', 'title': 'Наталія Кобринська: Задля кусника хліба'}, 'tasks': ['Як авторка зображує психологічний стан героїні?', 'Які соціальні умови змушують героїню діяти проти власної волі?', 'У чому полягає трагізм ситуації?']} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Останні роки' per template 'c1-biography-module-template.md'
  - FIX: Add '## Останні роки' section as specified in docs/l2-uk-en/templates/c1-biography-module-template.md.md

## Recommendation
**📝 UPDATE** (severity 25/100)

- 2 violations (minor)
- Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar

## Gates
- **Words:** ❌ 1907/4000 (raw: 2145)
- **Activities:** ✅ 4/3
- **Density:** ✅ All > 1
- **Unique_types:** ✅ 3/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 6/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 24 (soft target)
- **Structure:** ❌ Missing '## Vocabulary' header OR vocabulary sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 1 violations
- **Content_heavy:** ✅ Content-heavy OK (4 activities)
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
| primary_sources | 4 | 4 | 100% | 19% | 19.0% |
| engagement | 6 | 6 | 100% | 14% | 14.3% |
| quotes | 9 | 3 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 7 | 4 | 100% | 10% | 9.5% |
| timeline_markers | 27 | 8 | 100% | 10% | 9.5% |
| legacy | 11 | 2 | 100% | 10% | 9.5% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 12 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **97.5%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 76 | Included in Core |
| **Вступ** | ✅ | 129 | Included in Core |
| **Життєпис** | ⚪️ | 679 | Skipped |
| **Спадщина** | ⚪️ | 56 | Skipped |
| **Внесок** | ⚪️ | 54 | Skipped |
| **Історичний контекст** | ✅ | 433 | Included in Core |
| **Порівняльний аналіз** | ✅ | 47 | Included in Core |
| **Критичне мислення** | ⚪️ | 70 | Skipped |
| **Есе** | ⚪️ | 38 | Skipped |
| **Критерії оцінювання** | ⚪️ | 0 | Skipped |
| **Зразок відповіді** | ⚪️ | 238 | Skipped |
| **Підсумок** | ✅ | 75 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 12 | Skipped |