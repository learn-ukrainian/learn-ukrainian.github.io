# Audit Report: M46 — 46-proverbs-nature-time-caution.md
**Level:** B2 | **Module:** M46 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:09:50

## Configuration
**Type:** B2-vocab
**Word Target:** 2000 words
**Activities:** 10-14 required
**Items per Activity:** ≥14 items
**Unique Types:** ≥4 types required
**Priority Types:** mark-the-words, match-up, quiz, translate
**Required Types:** essay-response, reading, true-false
**Engagement:** ≥6 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥35 words
**Transliteration:** Not allowed

## PEDAGOGICAL VIOLATIONS
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (100% overlap): "**Регістр:** Нейтральний, часто вживається в бізнес-контексті.". Shares significant keywords with sentence at index 35.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (71% overlap): "«Краще синиця в руках, ніж журавель у небі», — порадив батько.". Shares significant keywords with sentence at index 101.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (80% overlap): "**Міжмовна паралель:** Прислів'я латинського походження, відоме в усіх європейських мовах.". Shares significant keywords with sentence at index 61.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (83% overlap): "**Батько:** **Сім разів відміряй, один раз відріж**.". Shares significant keywords with sentence at index 82.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (83% overlap): "**Надія:** **Краще синиця в руках, ніж журавель у небі**.". Shares significant keywords with sentence at index 101.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[YAML_SCHEMA_VIOLATION]** Schema error in 46-proverbs-nature-time-caution.yaml: YAML parse error: while parsing a block mapping
  in "<unicode string>", line 724, column 3:
    - type: reading
      ^
expected <block end>, but found '<scalar>'
  in "<unicode string>", line 726, column 38:
     ... le: 'Текст для аналізу: Прислів'я II: Природа, час і обережність'
                                         ^
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 55/100)

- Revision recommended (severity 55/100)
- 7 violations (significant)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 2877/2000 (raw: 3277)
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 16/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 17 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 7 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.3% (target 90-100% (vocab))
- **Richness:** ✅ 96% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 96% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 12 | 4 | 100% | 25% | 25.0% |
| variety | 0.77 | - | 77% | 17% | 12.8% |
| cultural | 12 | - | 100% | 17% | 16.7% |
| visual | 4 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 55 | - | 100% | 8% | 8.3% |
| realworld | 5 | - | 100% | 8% | 8.3% |
| questions | 11 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **96.2%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 56 | Included in Core |
| **Розминка — Природа як вчитель** | ⚪️ | 171 | Skipped |
| **Прислів'я про природу** | ⚪️ | 1539 | Skipped |
| **Прислів'я про час** | ⚪️ | 325 | Skipped |
| **Прислів'я про обережність** | ⚪️ | 150 | Skipped |
| **Практика — прислів'я у контексті** | ✅ | 385 | Included in Core |
| **Підсумок** | ✅ | 251 | Included in Core |