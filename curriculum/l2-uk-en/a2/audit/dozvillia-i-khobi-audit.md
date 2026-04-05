# Audit Report: M35 — dozvillia-i-khobi.md
**Level:** A2 | **Module:** M35 | **Phase:** A2.5 | **Pedagogy:** PPP | **Target:** 2000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-05 10:04:50

## Configuration
**Type:** A2
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
| 2 | quiz |  | 8 | 8 | ✅ |
| 3 | error-correction |  | 6 | 6 | ✅ |
| 4 | group-sort |  | 16 | 8 | ✅ |
| 5 | fill-in |  | 8 | 8 | ✅ |
| 6 | true-false |  | 6 | 8 | ❌ |

**Summary:**
- Total activities: 6 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 6/15 (error-correction, fill-in, group-sort, match-up, quiz, true-false) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. A2 true-false requires at least 8 items.
- **[YAML_SCHEMA_VIOLATION]** Schema error in dozvillia-i-khobi.yaml: Schema validation error at key '0': {'statement': 'Дієслово «захоплюватися» вимагає використання Знахідного відмінка (Accusative).', 'correct': False, 'explanation': 'Дієслово «захоплюватися» вимагає Орудного відмінка (Instrumental).'} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 15/100)

- 2 violations (minor)
- Activity density below minimum

## Gates
- **Words:** ✅ 2679/2000 (raw: 2825)
- **Activities:** ✅ 6/0
- **Density:** ❌ 1 < 8
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 45/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 65.2% (target 50-80% (A2.2))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | true-false | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 694 | Included in Core |
| **Куди́ йдемо́? Де ми? (Where Are We Going? Where Are We?)** | ✅ | 645 | Included in Core |
| **Плани на вихідні (Weekend Plans)** | ✅ | 645 | Included in Core |
| **Що мені подобається найбі́льше (What I Like Most)** | ✅ | 512 | Included in Core |
| **Підсумок** | ✅ | 183 | Included in Core |