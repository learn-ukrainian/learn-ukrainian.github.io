# Audit Report: M08 — aspect-in-negation.md
**Level:** B1 | **Module:** M08 | **Phase:** B1.0 | **Pedagogy:** TTT | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-10 21:25:57

## Configuration
**Type:** B1-grammar
**Word Target:** 4000 words
**Activities:** 0-4 required
**Items per Activity:** ≥6 items
**Unique Types:** ≥3 types required
**Priority Types:** critical-analysis, error-correction, essay-response, fill-in, mark-the-words, match-up, quiz
**Engagement:** ≥5 callouts
**Immersion:** 90-100%
**Vocab Target:** ≥25 words
**Transliteration:** Not allowed

## Activity Breakdown
| # | Type | Title | Items | Min | Status |
|---|------|-------|-------|-----|--------|
| 1 | quiz | quiz | 10 | 8 | ✅ |
| 2 | fill-in | fill-in | 8 | 8 | ✅ |
| 3 | group-sort | group-sort | 10 | 6 | ✅ |
| 4 | error-correction | error-correction | 6 | 6 | ✅ |
| 5 | match-up | match-up | 8 | 8 | ✅ |
| 6 | essay-response | essay-response | 1 | 6 | ❌ |
| 7 | true-false | true-false | 6 | 8 | ❌ |
| 8 | translate | translate | 6 | 6 | ✅ |

**Summary:**
- Total activities: 8 (target: 0-4) ❌
- Unique types: 8 (minimum: 3) ✅
- Priority types used: 5/7 (error-correction, essay-response, fill-in, match-up, quiz) ✅
- Low density activities: 2

## PEDAGOGICAL VIOLATIONS
- **[LEVEL_RESTRICTION]** Activity 'essay-response' not allowed at B1
  - FIX: Use level-appropriate activities. 'essay-response' is introduced at A2+.
- **[COMPLEXITY]** group-sort '' has 10 items (target: 12-999)
  - FIX: Adjust number of items to sort to 12-999.
- **[COMPLEXITY]** match-up '' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. B1 true-false requires at least 8 items.
- **[LLM_FINGERPRINT_REPETITION]** Repetitive LLM rhetorical patterns (10 total): 'не просто X, а Y' x7, 'не лише X, а й Y' x3 — robotic prose
  - FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (6 occurrences): (The topic never came up), (He is not working now), (He failed the exam) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
- **[PHASE_TRANSLATIONS_LOW]** Early B1 (B1 M01-M30) targets ~25% translated UK paragraphs — currently 0% (0/35)
  - FIX: 

## Recommendation
**📝 UPDATE** (severity 40/100)

- Revision recommended (severity 40/100)
- 7 violations (significant)
- Activity density below minimum

## Gates
- **Words:** ✅ 4629/4000 (raw: 4810)
- **Activities:** ✅ 8/0
- **Density:** ❌ 2 < 6
- **Unique_types:** ✅ 8/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 35/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 92.0% (target 85-100% (B1.1 Aspect))
- **Richness:** ❌ 59% < 95% min (grammar) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Richness Details
**Score:** 59% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 51 | 24 | 100% | 20% | 20.0% |
| engagement | 0 | 5 | 0% | 15% | 0.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.95 | - | 95% | 10% | 9.5% |
| cultural | 2 | 3 | 67% | 10% | 6.7% |
| realworld | 20 | 3 | 100% | 10% | 10.0% |
| visual | 0 | 3 | 0% | 5% | 0.0% |
| questions | 31 | 5 | 100% | 5% | 5.0% |
| tables | 1 | 2 | 50% | 4% | 2.0% |
| paragraph_var | 1.00 | - | 100% | 3% | 3.0% |
| proverbs | 10 | 1 | 100% | 3% | 3.0% |
| **TOTAL** | | | | | **59.2%** |

### Dryness Flags & Fixes
- ❌ **NO_ENGAGEMENT**
  - FIX:
    Add 2+ engagement boxes. Use this exact format:
    
    > 💡 **Чи знали ви?**
    >
    > [Interesting fact about the grammar/vocabulary topic in Ukrainian]
    
    > 🇺🇦 **Культурний момент**
    >
    > [Cultural context connecting grammar to Ukrainian life/places]
    
    > 🌍 **У реальному житті**
    >
    > [Practical scenario where this grammar is used]
- ❌ **NO_DIALOGUE**
  - FIX:
    Add 4+ mini-dialogues. The detector counts lines in blockquotes with bold speaker names.
    
    Use ONE of these formats (blockquote is required for detection):
    
    Format 1 — Bold speaker in blockquote (PREFERRED):
    > **Студент:** Чому тут знахідний відмінок?
    > **Викладач:** Бо дієслово «бачити» вимагає знахідного.
    > **Студент:** А якщо це заперечення?
    > **Викладач:** Тоді родовий: «не бачу **книжки**».
    
    Format 2 — Em-dash in blockquote:
    > — Чому тут знахідний?
    > — Бо дієслово вимагає знахідного.
    
    Format 3 — Plain А:/Б: speakers:
    А: Чому тут знахідний?
    Б: Бо дієслово вимагає знахідного.
    
    IMPORTANT: Dialogues OUTSIDE blockquotes (>) using **Speaker:** format are NOT detected.
    Place dialogues inside [!dialogue] callouts or blockquotes.

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| essay-response | essay-response | 1 | 6 | Add 5 more items |
| true-false | true-false | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 1071 | Included in Core |
| **Не + недоконаний: загальне заперечення (~1150 words total)** | ✅ | 1277 | Included in Core |
| **Ще не + доконаний: очікуване завершення (~1150 words total)** | ✅ | 1113 | Included in Core |
| **Підсумок: заперечення як прагматичний вибір** | ✅ | 1168 | Included in Core |