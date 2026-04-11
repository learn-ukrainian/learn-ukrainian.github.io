# Audit Report: M28 — reflexive-verbs-nuances.md
**Level:** B1 | **Module:** M28 | **Phase:** B1.2 | **Pedagogy:** PPP | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-10 21:26:10

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
| 1 | quiz | quiz | 8 | 8 | ✅ |
| 2 | group-sort | group-sort | 15 | 6 | ✅ |
| 3 | fill-in | fill-in | 8 | 8 | ✅ |
| 4 | error-correction | error-correction | 6 | 6 | ✅ |
| 5 | match-up | match-up | 10 | 8 | ✅ |
| 6 | fill-in | fill-in | 6 | 8 | ❌ |
| 7 | true-false | true-false | 6 | 8 | ❌ |
| 8 | match-up | match-up | 6 | 8 | ❌ |
| 9 | translate | translate | 6 | 6 | ✅ |

**Summary:**
- Total activities: 9 (target: 0-4) ❌
- Unique types: 7 (minimum: 3) ✅
- Priority types used: 4/7 (error-correction, fill-in, match-up, quiz) ✅
- Low density activities: 3

## PEDAGOGICAL VIOLATIONS
- **[COMPLEXITY]** match-up '' has 10 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[COMPLEXITY]** fill-in '' has 6 items (minimum: 8)
  - FIX: Add more items. B1 fill-in requires at least 8 items.
- **[COMPLEXITY]** true-false '' has 6 items (minimum: 8)
  - FIX: Add more items. B1 true-false requires at least 8 items.
- **[COMPLEXITY]** match-up '' has 6 pairs (target: 12-16)
  - FIX: Adjust number of pairs to 12-16.
- **[RUSSICISM_DETECTED]** Found 1 Russicism(s) in content: 'давайте подивимося' → подивімося
  - FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.
- **[SALAD_EXCESSIVE_INLINE_GLOSSES]** paragraph has 13 inline **term** (gloss) markers across 11 sentence(s) — too dense; move to vocabulary section or convert to UK paragraph + translation block
  - FIX: Convert inline-gloss paragraphs to monolingual Ukrainian paragraphs followed by a blockquote + italic English translation block. See docs/best-practices/language-salad.md.

## Recommendation
**📝 UPDATE** (severity 25/100)

- 6 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ✅ 4702/4000 (raw: 4755)
- **Activities:** ✅ 9/0
- **Density:** ❌ 3 < 6
- **Unique_types:** ✅ 7/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 55/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 92.9% (target 85-100% (B1.3-4 Complex))
- **Richness:** ❌ 50% < 95% min (grammar) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Richness Details
**Score:** 50% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 43 | 24 | 100% | 20% | 20.0% |
| engagement | 0 | 5 | 0% | 15% | 0.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.98 | - | 98% | 10% | 9.8% |
| cultural | 0 | 3 | 0% | 10% | 0.0% |
| realworld | 20 | 3 | 100% | 10% | 10.0% |
| visual | 0 | 3 | 0% | 5% | 0.0% |
| questions | 21 | 5 | 100% | 5% | 5.0% |
| tables | 0 | 2 | 0% | 4% | 0.0% |
| paragraph_var | 1.00 | - | 100% | 3% | 3.0% |
| proverbs | 10 | 1 | 100% | 3% | 3.0% |
| **TOTAL** | | | | | **50.8%** |

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
| fill-in | fill-in | 6 | 8 | Add 2 more items |
| true-false | true-false | 6 | 8 | Add 2 more items |
| match-up | match-up | 6 | 8 | Add 2 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 729 | Included in Core |
| **Семантичні групи зворотних дієслів** | ✅ | 1047 | Included in Core |
| **Милозвучність: -ся чи -сь?** | ✅ | 632 | Included in Core |
| **Зворотні дієслова у повсякденному мовленні** | ✅ | 1012 | Included in Core |
| **Типові помилки та контрастні пари** | ✅ | 751 | Included in Core |
| **Підсумок та перехід до M23** | ✅ | 531 | Included in Core |