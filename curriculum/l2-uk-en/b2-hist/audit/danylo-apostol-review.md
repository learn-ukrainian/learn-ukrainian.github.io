# Audit Report: M70 — danylo-apostol.md
**Level:** B2 | **Module:** M70 | **Phase:** B2.3b | **Pedagogy:** CBI | **Target:** 4000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-01-25 09:04:10

## Configuration
**Type:** B2-history
**Word Target:** 4000 words
**Activities:** 3-9 required
**Items per Activity:** ≥1 items
**Unique Types:** ≥2 types required
**Priority Types:** comparative-study, critical-analysis, essay-response, reading
**Required Types:** essay-response, reading
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥20 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in danylo-apostol.yaml: YAML parse error: while parsing a block mapping
  in "<unicode string>", line 274, column 5:
      - sentence: "Рішительні пункти" до ... 
        ^
expected <block end>, but found '<scalar>'
  in "<unicode string>", line 274, column 35:
      - sentence: "Рішительні пункти" дозволяли росіянам купувати землю.
                                      ^
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: history) missing advanced activity type: comparative-study
  - FIX: Add a comparative-study activity to meet advanced richness standards.

## TEMPLATE COMPLIANCE
- ❌ **[MISSING_REQUIRED_SECTION]** Missing required section 'Читання' per template 'b2-history-module-template.md'
  - FIX: Add '## Читання' section as specified in docs/l2-uk-en/templates/b2-history-module-template.md.md
- ⚠️ **[MISSING_REQUIRED_CALLOUT]** Missing required callout '[!history-bite]' per template 'b2-history-module-template.md'
  - FIX: Add a `> [!history-bite]` box as specified in the template. This enhances module quality.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 5 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ❌ 2681/4000 (raw: 2777)
- **Activities:** ❌ 0/3
- **Density:** ❌ 0 < 1
- **Unique_types:** ❌ 0/2 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 5/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 25/20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 3 violations
- **Content_heavy:** ⚠️ Too few activities: 0 (target 3-9)
- **Immersion:** 🇺🇦 99.6% (target 90-100% (history))
- **Richness:** ❌ 92% < 95% min (history)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 92% (minimum: 95%)
**Module Type:** history

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| primary_sources | 7 | 3 | 100% | 24% | 23.8% |
| engagement | 5 | 6 | 83% | 14% | 11.9% |
| timeline_markers | 30 | 10 | 100% | 14% | 14.3% |
| decolonization | 15 | 2 | 100% | 14% | 14.3% |
| cultural | 3 | 4 | 75% | 10% | 7.1% |
| visual | 3 | 4 | 75% | 10% | 7.1% |
| variety | 0.98 | - | 98% | 5% | 4.7% |
| paragraph_var | 1.00 | - | 100% | 5% | 4.8% |
| questions | 6 | 3 | 100% | 5% | 4.8% |
| **TOTAL** | | | | | **92.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 84 | Included in Core |
| **Вступ: Між молотом і ковадлом** | ✅ | 327 | Included in Core |
| **Епоха Данила Апостола: Відновлення порядку** | ⚪️ | 582 | Skipped |
| **Економіка та суспільство: Стабільність і криза** | ⚪️ | 341 | Skipped |
| **Епоха Розумовського: Європейська мрія** | ⚪️ | 449 | Skipped |
| **Первинні джерела: Голоси епохи** | ✅ | 398 | Included in Core |
| **Деколонізаційний погляд: Дві стратегії виживання** | ✅ | 319 | Included in Core |
| **Підсумок: Захід сонця** | ✅ | 120 | Included in Core |
| **Потрібно більше практики?** | ⚪️ | 61 | Skipped |