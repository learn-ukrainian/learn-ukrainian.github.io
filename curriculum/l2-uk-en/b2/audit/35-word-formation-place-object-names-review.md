# Audit Report: M35 — 35-word-formation-place-object-names.md
**Level:** B2 | **Module:** M35 | **Phase:** B2.1c | **Pedagogy:** TTT | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:03:51

## Configuration
**Type:** B2-grammar
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** cloze, error-correction, fill-in, unjumble
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[SECTION_ORDER]** Content section '## Практика — утворення назв місць' appears after end section '# Підсумок'
  - FIX: Reorder sections to: Summary → Activities → Self-Assessment → External → Vocabulary
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "Археологи знайшли тут сховище для зерна та залишки укріплень.". Shares significant keywords with sentence at index 14.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 35-word-formation-place-object-names.yaml: YAML parse error: while parsing a block mapping
  in "<unicode string>", line 1233, column 3:
    - type: reading
      ^
expected <block end>, but found '<scalar>'
  in "<unicode string>", line 1235, column 63:
     ... ловотворення: назви місць та об'єктів'
                                         ^
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: grammar) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 4 violations (moderate)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 2332/2000 (raw: 2743)
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 19 < 25 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 4 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 98.8% (target 90-100% (grammar))
- **Richness:** ✅ 98% (grammar)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 98% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 61 | 24 | 100% | 20% | 20.0% |
| engagement | 9 | 5 | 100% | 15% | 15.0% |
| dialogues | 20 | 4 | 100% | 15% | 15.0% |
| variety | 0.95 | - | 95% | 10% | 9.5% |
| cultural | 4 | 3 | 100% | 10% | 10.0% |
| realworld | 5 | 3 | 100% | 10% | 10.0% |
| visual | 7 | 3 | 100% | 5% | 5.0% |
| paragraph_var | 0.87 | - | 87% | 5% | 4.4% |
| questions | 42 | 5 | 100% | 5% | 5.0% |
| proverbs | 6 | 1 | 100% | 5% | 5.0% |
| **TOTAL** | | | | | **98.8%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 67 | Included in Core |
| **Розминка — Як утворюються назви місць** | ⚪️ | 244 | Skipped |
| **Suffix -ня** | ⚪️ | 1227 | Skipped |
| **Suffix -ище (place/area)** | ⚪️ | 229 | Skipped |
| **Suffix -арня (workshop/establishment)** | ⚪️ | 308 | Skipped |
| **Підсумок** | ✅ | 73 | Included in Core |
| **Практика — утворення назв місць** | ⚪️ | 184 | Skipped |