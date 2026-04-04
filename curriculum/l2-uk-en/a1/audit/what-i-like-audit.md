# Audit Report: M15 — what-i-like.md
**Level:** A1 | **Module:** M15 | **Phase:** A1.3 | **Pedagogy:** PPP | **Target:** 1200
**Overall Status:** ✅ PASS
**Generated:** 2026-04-04 19:30:19

## Configuration
**Type:** A1-grammar
**Word Target:** 1200 words
**Activities:** 0-4 required
**Items per Activity:** ≥6 items
**Unique Types:** ≥0 types required
**Priority Types:** anagram, classify, fill-in, image-to-letter, match-up, quiz, unjumble, watch-and-repeat
**Engagement:** ≥0 callouts
**Immersion:** 0-100%
**Vocab Target:** ≥1 words
**Transliteration:** Allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | fill-in |  | 8 | 6 | ✅ |
| 2 | match-up |  | 9 | 6 | ✅ |
| 3 | quiz |  | 8 | 6 | ✅ |
| 4 | fill-in |  | 6 | 6 | ✅ |
| 5 | fill-in |  | 8 | 6 | ✅ |
| 6 | group-sort |  | 12 | 6 | ✅ |
| 7 | true-false |  | 7 | 6 | ✅ |
| 8 | translate |  | 6 | 6 | ✅ |

**Summary:**
- Total activities: 8 (target: 0-4) ❌
- Unique types: 6 (minimum: 0) ✅
- Priority types used: 3/8 (fill-in, match-up, quiz) ✅
- Low density activities: 0

## PEDAGOGICAL VIOLATIONS
- **[YAML_SCHEMA_VIOLATION]** Schema error in what-i-like.yaml: Schema validation error at key '8': {'type': 'translate', 'instruction': 'Choose the correct Ukrainian translation. Watch for the **люблю / подобається** distinction.', 'items': [{'source': 'I like to watch films.', 'options': [{'text': 'Я люблю дивитися фільми.', 'correct': True}, {'text': 'Мені подобається фільми.', 'correct': False}, {'text': 'Я люблю фільми дивитися не.', 'correct': False}]}, {'source': 'I like this film.', 'options': [{'text': 'Мені подобається цей фільм.', 'correct': True}, {'text': 'Я люблю цей фільм дивитися.', 'correct': False}, {'text': 'Мені люблю цей фільм.', 'correct': False}]}, {'source': "I don't like to cook.", 'options': [{'text': 'Я не люблю готувати.', 'correct': True}, {'text': 'Я люблю не готувати.', 'correct': False}, {'text': 'Мені не подобається готувати.', 'correct': False}]}, {'source': 'I like jazz.', 'options': [{'text': 'Мені подобається джаз.', 'correct': True}, {'text': 'Я люблю джаз слухати.', 'correct': False}, {'text': 'Мені люблю джаз.', 'correct': False}]}, {'source': 'I like to sing.', 'options': [{'text': 'Я люблю співати.', 'correct': True}, {'text': 'Мені подобається пісня.', 'correct': False}, {'text': 'Я люблю пісню.', 'correct': False}]}, {'source': "I don't like this book.", 'options': [{'text': 'Мені не подобається ця книга.', 'correct': True}, {'text': 'Я не люблю читати книга.', 'correct': False}, {'text': 'Ця книга не люблю мені.', 'correct': False}]}]} is not valid under any of the given schemas
  - FIX: Fix the activity YAML to match the schema in schemas/activity-v2.schema.json

## Recommendation
**📝 UPDATE** (severity 5/100)

- 1 violations (minor)

## Gates
- **Words:** ✅ 1314/1200 (raw: 1396)
- **Activities:** ✅ 8/0
- **Density:** ✅ All > 6
- **Unique_types:** ✅ 6/0 types
- **Priority:** ✅ Priority types used
- **Engagement:** ✅ 0/0
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 42/1
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 29.0% (target 15-35% (M15))
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ⚠️ Refresh recommended: Research has 3+ learner errors but content doesn't address common mistakes

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 307 | Included in Core |
| **Я люблю... (I Like...)** | ✅ | 402 | Included in Core |
| **Мені подобається... (I Like...)** | ✅ | 372 | Included in Core |
| **Підсумок — Summary** | ✅ | 233 | Included in Core |