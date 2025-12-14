# Audit Report: test-markdown-format.md
**Phase:** A1.1 | **Level:** A1 | **Pedagogy:** PPP | **Target:** 750
**Overall Status:** ❌ FAIL

## PEDAGOGICAL VIOLATIONS
- **[LEVEL_RESTRICTION]** Activity 'error-correction' not allowed at A1
  - FIX: Use level-appropriate activities. 'error-correction' is introduced at A2+.
- **[QUIZ_FORMAT]** Quiz 'Test Quiz with Bullets' uses bullets (-) for questions instead of numbered list
  - FIX: Use numbered items (1. 2. 3.) for quiz questions, not bullets. Format: '1. Question text?\n   - [x] Correct\n   - [ ] Wrong'
- **[TRUE_FALSE_FORMAT]** True-false 'Test True False with Embedded Answers' has embedded answer text '—TRUE/FALSE' in statement
  - FIX: Remove '— TRUE/FALSE' from statements. Use checkbox format: '- [x]' for true, '- [ ]' for false.
- **[UNJUMBLE_FORMAT]** Unjumble 'Test Unjumble with Nested Bullets' uses nested bullets for answers instead of callout blocks
  - FIX: Use '> [!answer]' callout for unjumble answers, not nested bullets. Format: '1. jumbled words\n   > [!answer] Correct sentence\n   > (translation) [word count]'
- **[MATCHUP_FORMAT]** Match-up 'Test Matchup without Table' uses bullets but not table or :: separator format
  - FIX: Use table format '| Left | Right |' or separator format '- item :: item' for match-up activities.
- **[ERROR_CORRECTION_FORMAT]** Error-correction 'Test Error Correction Missing Explanations' missing '> [!explanation]' callouts
  - FIX: Each error-correction item REQUIRES '> [!explanation]' explaining why it's wrong and the rule.

## Recommendation
**🔄 REWRITE** (severity 75/100)

- 6 pedagogical violations (moderate)
- Immersion 9% off target (minor)
- Activity count below minimum
- Activity density below minimum
- Vocabulary count below minimum

## Gates
- **Words:** ❌ 4/750
- **Activities:** ❌ 6/8
- **Density:** ❌ 6 < 12
- **Unique_types:** ✅ 6/4 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/3
- **Audio:** ℹ️ No audio
- **Vocab:** ❌ 1 < 20
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 6 violations
- **Immersion:** ❌ 26.3% LOW (target 35-55% (M999))

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| quiz: Test Quiz with Bullets | quiz | 4 | 8 | Add 4 more items |
| true-false: Test True False with Embedded Answers | true-false | 2 | 8 | Add 6 more items |
| unjumble: Test Unjumble with Nested Bullets | unjumble | 2 | 6 | Add 4 more items |
| match-up: Test Matchup without Table | match-up | 4 | 8 | Add 4 more items |
| fill-in: Test Fill-in Missing Options | fill-in | 2 | 8 | Add 6 more items |
| error-correction: Test Error Correction Missing Explanations | error-correction | 1 | 6 | Add 5 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Test Module** | ⚪️ | 0 | Skipped |
| **Presentation** | ✅ | 4 | Included in Core |
| **Activities** | ➖ | 0 | Excluded Type |
| **quiz: Test Quiz with Bullets** | 🎮 | 4 | Activity (4 items, min 8) |
| **true-false: Test True False with Embedded Answers** | 🎮 | 2 | Activity (2 items, min 8) |
| **unjumble: Test Unjumble with Nested Bullets** | 🎮 | 2 | Activity (2 items, min 6) |
| **match-up: Test Matchup without Table** | 🎮 | 4 | Activity (4 items, min 8) |
| **fill-in: Test Fill-in Missing Options** | 🎮 | 2 | Activity (2 items, min 8) |
| **error-correction: Test Error Correction Missing Explanations** | 🎮 | 1 | Activity (1 items, min 6) |
| **Summary** | ✅ | 5 | Included in Core |
| **Vocabulary** | ➖ | 0 | Excluded Type |