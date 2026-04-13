# Audit Report: M06 — aspect-in-narration.md
**Level:** B1 | **Module:** M06 | **Phase:** B1.0 | **Pedagogy:** TTT | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-11 13:26:45

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
| 1 | quiz |  | 10 | 8 | ✅ |
| 2 | group-sort |  | 10 | 6 | ✅ |
| 3 | fill-in |  | 8 | 8 | ✅ |
| 4 | match-up |  | 8 | 8 | ✅ |
| 5 | group-sort |  | 16 | 6 | ✅ |
| 6 | fill-in |  | 6 | 8 | ❌ |
| 7 | essay-response |  | 1 | 6 | ❌ |

**Summary:**
- Total activities: 7 (target: 0-4) ❌
- Unique types: 5 (minimum: 3) ✅
- Priority types used: 4/7 (essay-response, fill-in, match-up, quiz) ✅
- Low density activities: 2

## LINT ERRORS
- ❌ Line 171: AI Contamination detected ('\bRewrite this\b'). Remove thinking/self-correction artifacts.

## PEDAGOGICAL VIOLATIONS
- **[LEVEL_RESTRICTION]** Activity 'essay-response' not allowed at B1
  - FIX: Use level-appropriate activities. 'essay-response' is introduced at A2+.
- **[COMPLEXITY]** group-sort '' has 10 items (target: 12-999)
  - FIX: Adjust number of items to sort to 12-999.
- **[COMPLEXITY]** match-up '' has 8 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** fill-in '' has 6 items (minimum: 8)
  - FIX: Add more items. B1 fill-in requires at least 8 items.
- **[CONTENT_REDUNDANCY]** Redundant information detected in lesson (83% overlap): "Because the imperfective always focuses on the process itself rather than the final result, it allow...". Shares significant keywords with sentence at index 76.
  - FIX: Remove redundant paragraphs. Ensure each section adds new unique value.
- **[STATE_STANDARD_LOW_IMMERSION]** Module 6 has 28.1% immersion (target: 90.0%+)
  - FIX: Add more Ukrainian content to reach 90%+ immersion for full immersion modules

## Recommendation
**📝 UPDATE** (severity 67/100)

- Revision recommended (severity 67/100)
- 6 violations (moderate)
- Immersion 57% off target (major rebalancing needed)
- Activity density below minimum

## Gates
- **Words:** ✅ 6415/4000 (raw: 6503)
- **Activities:** ✅ 7/0
- **Density:** ❌ 2 < 6
- **Unique_types:** ✅ 5/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 2/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 45/25
- **Structure:** ✅ Valid Structure
- **Lint:** ❌ 1 Format Errors
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** ❌ 28.1% LOW (target 85-100% (B1.1 Aspect))
- **Richness:** ❌ 39% < 95% min (grammar) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Richness Details
**Score:** 39% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 11 | 24 | 46% | 20% | 9.2% |
| engagement | 0 | 5 | 0% | 15% | 0.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.95 | - | 95% | 10% | 9.5% |
| cultural | 0 | 3 | 0% | 10% | 0.0% |
| realworld | 20 | 3 | 100% | 10% | 10.0% |
| visual | 0 | 3 | 0% | 5% | 0.0% |
| questions | 13 | 5 | 100% | 5% | 5.0% |
| tables | 0 | 2 | 0% | 4% | 0.0% |
| paragraph_var | 1.00 | - | 100% | 3% | 3.0% |
| proverbs | 10 | 1 | 100% | 3% | 3.0% |
| **TOTAL** | | | | | **39.7%** |

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
- ❌ **NO_EXAMPLES**
  - FIX:
    Add 24+ example sentences. Each grammar point needs 3-4 examples showing the pattern in context.
- ❌ **NO_TABLES**
  - FIX:
    Address this issue to improve richness score
- ❌ **NO_CULTURAL_ANCHOR**
  - FIX:
    Add 3+ cultural references. Use this exact format:
    
    > 🇺🇦 **Культурний момент**
    >
    > [Reference to Ukrainian place (Київ, Львів, Одеса, Карпати), tradition, or custom]
    > [How it connects to the grammar/vocabulary being taught]
    > [Example sentence using the grammar with cultural context]

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
|  | fill-in | 6 | 8 | Add 2 more items |
|  | essay-response | 1 | 6 | Add 5 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 1102 | Included in Core |
| **Тло: недоконаний вид у наративі (~1150 words total)** | ✅ | 1784 | Included in Core |
| **Передній план: доконаний вид у наративі (~1200 words total)** | ✅ | 1546 | Included in Core |
| **Підсумок: аспект як наративний інструмент (~1150 words total)** | ✅ | 1983 | Included in Core |