# Audit Report: M45 — 45-proverbs-work-wisdom-character.md
**Level:** B2 | **Module:** M45 | **Phase:** B2.2 | **Pedagogy:** CBI | **Target:** 2000
**Naturalness:** 9/10 (PASS)
**Overall Status:** ❌ FAIL
**Generated:** 2026-02-05 22:04:02

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
- **[YAML_SCHEMA_VIOLATION]** Schema error in 45-proverbs-work-wisdom-character.yaml: YAML parse error: while parsing a block mapping
  in "<unicode string>", line 950, column 3:
    - type: reading
      ^
expected <block end>, but found '<scalar>'
  in "<unicode string>", line 952, column 38:
     ... le: 'Текст для аналізу: Прислів'я I: Праця, мудрість і характер'
                                         ^
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json
- **[MISSING_ADVANCED_ACTIVITY]** B2+ module (focus: vocab) missing advanced activity type: essay-response
  - FIX: Add a essay-response activity to meet advanced richness standards.

## Recommendation
**📝 UPDATE** (severity 30/100)

- 2 violations (minor)
- Activity count below minimum
- Activity density below minimum

## Gates
- **Words:** ✅ 2087/2000 (raw: 2309)
- **Activities:** ❌ 0/10
- **Density:** ❌ 0 < 14
- **Unique_types:** ❌ 0/4 types
- **Priority:** ❌ No priority types
- **Engagement:** ✅ 8/6
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 22 < 35 (soft target)
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 2 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 99.5% (target 90-100% (vocab))
- **Richness:** ✅ 99% (phraseology)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ✅ 9/10 (High)

## Richness Details
**Score:** 99% (minimum: 95%)
**Module Type:** phraseology

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| engagement | 8 | 4 | 100% | 25% | 25.0% |
| variety | 0.98 | - | 98% | 17% | 16.3% |
| cultural | 2 | - | 100% | 17% | 16.7% |
| visual | 3 | 3 | 100% | 8% | 8.3% |
| paragraph_var | 1.00 | - | 100% | 8% | 8.3% |
| examples | 43 | - | 100% | 8% | 8.3% |
| realworld | 6 | - | 100% | 8% | 8.3% |
| questions | 5 | - | 100% | 8% | 8.3% |
| **TOTAL** | | | | | **99.7%** |

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 58 | Included in Core |
| **Розминка — Народна мудрість про працю** | ⚪️ | 348 | Skipped |
| **Прислів'я про працю** | ⚪️ | 630 | Skipped |
| **Прислів'я про мудрість** | ⚪️ | 17 | Skipped |
| **Прислів'я про характер** | ⚪️ | 528 | Skipped |
| **Практика — вживання прислів'їв** | ⚪️ | 175 | Skipped |
| **Підсумок** | ✅ | 331 | Included in Core |