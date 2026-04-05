# Audit Report: M33 — plural-genitive.md
**Level:** A2 | **Module:** M33 | **Phase:** A2.5 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:05:04

## Configuration
**Type:** A2-grammar
**Word Target:** 2000 words
**Activities:** 0-4 required
**Items per Activity:** ≥8 items
**Unique Types:** ≥0 types required
**Priority Types:** cloze, error-correction, fill-in, group-sort, mark-the-words, match-up, observe, odd-one-out, order, quiz, reading, select, translate, true-false, unjumble
**Engagement:** ≥3 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | match-up |  | 8 | 8 | ✅ |
| 2 | fill-in |  | 8 | 8 | ✅ |
| 3 | true-false |  | 8 | 8 | ✅ |
| 4 | quiz |  | 8 | 8 | ✅ |
| 5 | error-correction |  | 6 | 6 | ✅ |
| 6 | group-sort |  | 12 | 8 | ✅ |

**Summary:**
- Total activities: 6 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q1 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q3 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[COMPLEXITY_WORD_COUNT]** quiz '' Q8 prompt length 4 (target: 5-15)
  - FIX: Adjust prompt length to 5-15 words.
- **[ROBOTIC_STRUCTURE]** Robotic structure: 3 sentences start with 'а скільки...'.
  - FIX: Vary sentence structure.
- **[RUSSICISM_DETECTED]** Found 1 Russicism(s) in content: 'давайте подивимося' → подивімося
  - FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.
- **[YAML_SCHEMA_VIOLATION]** Schema error in plural-genitive.yaml: Schema validation error at key 'correct': 2 is not of type 'boolean'
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 6 violations (moderate)

## Gates
- **Words:** ✅ 2486/2000 (raw: 2596)
- **Activities:** ✅ 6/0
- **Density:** ✅ All > 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 34/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 65.0% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 489 | Included in Core |
| **I відміна: нульове закінчення** | ✅ | 580 | Included in Core |
| **II відміна: -ів, нульове, -ей** | ✅ | 742 | Included in Core |
| **Скільки чого? Кількість у житті** | ✅ | 497 | Included in Core |
| **Підсумок** | ✅ | 178 | Included in Core |