# Audit Report: M18 — questions-and-negation.md
**Level:** A1 | **Module:** M18 | **Phase:** A1.2 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ❌ FAIL
**Generated:** 2026-03-18 05:21:40

## Configuration
**Type:** A1-grammar
**Word Target:** 1200 words
**Activities:** 0-4 required
**Items per Activity:** ≥6 items
**Unique Types:** ≥0 types required
**Priority Types:** anagram, classify, fill-in, image-to-letter, match-up, quiz, unjumble, watch-and-repeat
**Engagement:** ≥3 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | fill-in | Form Yes/No Questions with Чи | 20 | 6 | ✅ |
| 2 | fill-in | Complete with Question Words | 20 | 6 | ✅ |
| 3 | fill-in | Make Sentences Negative | 20 | 6 | ✅ |
| 4 | fill-in | Question-Answer Pairs | 20 | 6 | ✅ |
| 5 | quiz | Questions and Negation Rules | 15 | 6 | ✅ |
| 6 | match-up | Match Question Words to Meanings | 9 | 6 | ✅ |
| 7 | true-false | True or False? Questions and Negation | 20 | 6 | ✅ |
| 8 | unjumble | Put the Words in Order | 20 | 6 | ✅ |
| 9 | group-sort | Sort the Words by Category | 12 | 6 | ✅ |

**Summary:**
- Total activities: 9 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 4/8 (fill-in, match-up, quiz, unjumble) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[GRAMMAR]** Subordinate clause marker at A1: 'у що я'
  - FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
- **[GRAMMAR]** Subordinate clause marker at A1: 'тому що я'
  - FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
- **[GRAMMAR]** Subordinate clause marker at A1: 'бо х'
  - FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Questions and Negation Rules' Q7 prompt length 4 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Questions and Negation Rules' Q8 prompt length 4 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Questions and Negation Rules' Q9 prompt length 4 (target: 5-10)
  - FIX: Adjust prompt length to 5-10 words.
- **[COMPLEXITY_WORD_COUNT]** unjumble 'Put the Words in Order' item 10 has 2 words (target: 4-6)
  - FIX: Adjust sentence length to 4-6 words to match A1 complexity.
- **[VOCAB_NOT_IN_CONTENT]** Only 10/20 (50%) vocabulary words appear in content+activities. Missing: а, але, бо, де, коли, куди, ні, хто (+2 more)
  - FIX: Integrate missing vocabulary words into the prose or activities. Each vocab word should appear at least once in context.
- **[YAML_SCHEMA_VIOLATION]** Schema error in questions-and-negation.yaml: Schema validation error at key 'words': ['сніданок', 'Коли'] is too short
  - FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json

## TEMPLATE COMPLIANCE
- ❌ **[DUPLICATE_SYNONYMOUS_HEADERS]** Multiple headers contain 'Introduction': Вступ: Основи заперечення та інтонації (Introduction: Basics of Negation and Intonation), Культурний контекст та ALF (Cultural Context and ALF)
  - FIX: RENAME one header to NOT contain 'Introduction'. Example: 'Агіографічна спадщина' → 'Житійна творчість' (removes the duplicate word).

## Recommendation
**📝 UPDATE** (severity 50/100)

- Revision recommended (severity 50/100)
- 10 violations (significant)
- 3 grammar-level violations (fundamental)

## Gates
- **Words:** ✅ 2042/1200 (raw: 2180)
- **Activities:** ✅ 9/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 3/3
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 20/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ❌ 8 violations
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 22.2% (target 15-25% (M18))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Вступ: Основи заперечення та інтонації (Introduction: Basics of Negation and Intonation)** | ✅ | 319 | Included in Core |
| **Презентація: Питальні конструкції (Presentation: Interrogative Structures)** | ✅ | 392 | Included in Core |
| **Практика: Тренування заперечень та запитань (Practice: Drilling Negation and Questions)** | ✅ | 261 | Included in Core |
| **Продукція: Комунікативні сценарії (Production: Communicative Scenarios)** | ➖ | 304 | Excluded Type |
| **З'єднуємо речення (Joining Sentences)** | ✅ | 418 | Included in Core |
| **Культурний контекст та ALF (Cultural Context and ALF)** | ✅ | 179 | Included in Core |
| **Підсумок** | ✅ | 169 | Included in Core |