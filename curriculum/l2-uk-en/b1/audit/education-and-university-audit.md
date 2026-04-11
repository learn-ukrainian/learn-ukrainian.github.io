# Audit Report: M55 — education-and-university.md
**Level:** B1 | **Module:** M55 | **Phase:** B1.5 | **Pedagogy:** PPP | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-10 21:26:28

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
| 1 | true-false | Розуміння системи освіти | 12 | 8 | ✅ |
| 2 | quiz | Університетські терміни | 8 | 8 | ✅ |
| 3 | match-up | Навчальні дисципліни та спеціальності | 12 | 8 | ✅ |
| 4 | essay-response | Моя майбутня спеціальність | 1 | 6 | ❌ |
| 5 | fill-in | Академічне середовище | 12 | 8 | ✅ |
| 6 | error-correction | Виправлення помилок академічного стилю | 8 | 6 | ✅ |
| 7 | group-sort | Категорії закладів та ступенів | 16 | 6 | ✅ |
| 8 | unjumble | Академічні речення | 8 | 6 | ✅ |

**Summary:**
- Total activities: 8 (target: 0-4) ❌
- Unique types: 8 (minimum: 3) ✅
- Priority types used: 5/7 (error-correction, essay-response, fill-in, match-up, quiz) ✅
- Low density activities: 1

## PEDAGOGICAL VIOLATIONS
- **[LEVEL_RESTRICTION]** Activity 'essay-response' not allowed at B1
  - FIX: Use level-appropriate activities. 'essay-response' is introduced at A2+.
- **[COMPLEXITY_WORD_COUNT]** quiz 'Університетські терміни' Q5 prompt length 4 (target: 5-20)
  - FIX: Adjust prompt length to 5-20 words.
- **[RUSSICISM_DETECTED]** Found 1 Russicism(s) in content: 'давайте подивимося' → подивімося
  - FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.
- **[LLM_FINGERPRINT_REPETITION]** Repetitive LLM rhetorical patterns (4 total): 'не лише X, а й Y' x4 — robotic prose
  - FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
- **[INLINE_ENGLISH_IN_PROSE]** Inline English translations in B1+ prose (13 occurrences): (Having read your term paper), (Having analyzed your results), (Having corrected all these minor errors) — breaks immersion target
  - FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section
- **[SALAD_EXCESSIVE_INLINE_GLOSSES]** paragraph has 14 inline **term** (gloss) markers across 14 sentence(s) — too dense; move to vocabulary section or convert to UK paragraph + translation block
  - FIX: Convert inline-gloss paragraphs to monolingual Ukrainian paragraphs followed by a blockquote + italic English translation block. See docs/best-practices/language-salad.md.

## Recommendation
**📝 UPDATE** (severity 25/100)

- 6 violations (moderate)
- Activity density below minimum

## Gates
- **Words:** ✅ 4934/4000 (raw: 4989)
- **Activities:** ✅ 8/0
- **Density:** ❌ 1 < 6
- **Unique_types:** ✅ 8/3 types
- **Priority:** ✅ Priority types used
- **Engagement:** ❌ 0/5
- **Audio:** ℹ️ No audio
- **Vocab:** ✅ 74/25
- **Structure:** ✅ Valid Structure
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 92.4% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ❌ 74% < 80% min (skills)
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Richness Details
**Score:** 74% (minimum: 80%)
**Module Type:** skills

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 54 | 15 | 100% | 26% | 25.5% |
| engagement | 0 | 5 | 0% | 19% | 0.0% |
| variety | 0.97 | - | 97% | 12% | 11.9% |
| cultural | 1 | - | 100% | 12% | 12.2% |
| realworld | 20 | 3 | 100% | 12% | 12.2% |
| visual | 0 | 2 | 0% | 6% | 0.0% |
| paragraph_var | 1.00 | - | 100% | 6% | 6.1% |
| questions | 23 | 4 | 100% | 6% | 6.1% |
| **TOTAL** | | | | | **74.1%** |

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

## Low Density Activities
| Activity | Type | Items | Required | Fix |
|----------|------|-------|----------|-----|
| Моя майбутня спеціальність | essay-response | 1 | 6 | Add 5 more items |


## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 950 | Included in Core |
| **Навчальні дисципліни та спеціальності** | ✅ | 887 | Included in Core |
| **Академічне середовище** | ✅ | 927 | Included in Core |
| **Навчальний процес: дієприкметники і дієприслівники** | ✅ | 966 | Included in Core |
| **Порівняння систем освіти** | ✅ | 673 | Included in Core |
| **Підсумок фази 7 та перехід до M65** | ✅ | 531 | Included in Core |