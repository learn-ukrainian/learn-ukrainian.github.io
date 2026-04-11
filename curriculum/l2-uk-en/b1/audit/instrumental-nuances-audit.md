# Audit Report: M56 — instrumental-nuances.md
**Level:** B1 | **Module:** M56 | **Phase:** B1.5 | **Pedagogy:** PPP | **Target:** 4000
**Overall Status:** ❌ FAIL
**Generated:** 2026-04-10 21:26:29

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

## PEDAGOGICAL VIOLATIONS
- **[RUSSICISM_DETECTED]** Found 1 Russicism(s) in content: 'давайте подивимося' → подивімося
  - FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.
- **[LLM_FINGERPRINT_REPETITION]** Repetitive LLM rhetorical patterns (4 total): 'не просто X, а Y' x4 — robotic prose
  - FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
- **[STATE_STANDARD_LOW_IMMERSION]** Module 56 has 88.8% immersion (target: 90.0%+)
  - FIX: Add more Ukrainian content to reach 90%+ immersion for full immersion modules
- **[SALAD_EXCESSIVE_INLINE_GLOSSES]** paragraph has 4 inline **term** (gloss) markers across 3 sentence(s) — too dense; move to vocabulary section or convert to UK paragraph + translation block
  - FIX: Convert inline-gloss paragraphs to monolingual Ukrainian paragraphs followed by a blockquote + italic English translation block. See docs/best-practices/language-salad.md.
- **[SALAD_EXCESSIVE_INLINE_GLOSSES]** paragraph has 14 inline **term** (gloss) markers across 11 sentence(s) — too dense; move to vocabulary section or convert to UK paragraph + translation block
  - FIX: Convert inline-gloss paragraphs to monolingual Ukrainian paragraphs followed by a blockquote + italic English translation block. See docs/best-practices/language-salad.md.
- **[SALAD_EXCESSIVE_INLINE_GLOSSES]** paragraph has 10 inline **term** (gloss) markers across 9 sentence(s) — too dense; move to vocabulary section or convert to UK paragraph + translation block
  - FIX: Convert inline-gloss paragraphs to monolingual Ukrainian paragraphs followed by a blockquote + italic English translation block. See docs/best-practices/language-salad.md.

## Recommendation
**📝 UPDATE** (severity 35/100)

- 6 violations (moderate)
- Structure issue: Missing '## Activities' header OR activities sidecar

## Gates
- **Words:** ✅ 5146/4000 (raw: 5201)
- **Activities:** ✅ 0/0
- **Density:** ✅ All > 6
- **Unique_types:** ❌ 0/3 types
- **Priority:** ⚠️ No priority types
- **Engagement:** ❌ 0/5
- **Audio:** ℹ️ No audio
- **Vocab:** ⚠️ 0 < 25 (soft target)
- **Structure:** ❌ Missing '## Activities' header OR activities sidecar
- **Lint:** ✅ Clean Format
- **Pedagogy:** ✅ Level-appropriate
- **Content_heavy:** ℹ️ N/A (standard module)
- **Immersion:** 🇺🇦 88.8% (target 85-100% (B1.5-6 Vocab))
- **Richness:** ❌ 60% < 95% min (grammar) - REWRITE needed
- **Grammar:** ℹ️ N/A (covered by naturalness)
- **Naturalness:** ℹ️ PENDING — awaiting review
- **Research:** ✅ Content aligned with research

## Richness Details
**Score:** 60% (minimum: 95%)
**Module Type:** grammar

### Score Breakdown
| Metric | Count | Target | Score | Weight | Contribution |
|--------|-------|--------|-------|--------|--------------|
| examples | 52 | 24 | 100% | 20% | 20.0% |
| engagement | 0 | 5 | 0% | 15% | 0.0% |
| dialogues | 0 | 4 | 0% | 15% | 0.0% |
| variety | 0.93 | - | 93% | 10% | 9.3% |
| cultural | 3 | 3 | 100% | 10% | 10.0% |
| realworld | 20 | 3 | 100% | 10% | 10.0% |
| visual | 0 | 3 | 0% | 5% | 0.0% |
| questions | 13 | 5 | 100% | 5% | 5.0% |
| tables | 0 | 2 | 0% | 4% | 0.0% |
| paragraph_var | 1.00 | - | 100% | 3% | 3.0% |
| proverbs | 10 | 1 | 100% | 3% | 3.0% |
| **TOTAL** | | | | | **60.3%** |

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

## Section Audit
| Section | Status | Count | Notes |
|---|---|---|---|
| **Intro/Narrative** | ✅ | 1105 | Included in Core |
| **Орудний засобу та знаряддя** | ✅ | 865 | Included in Core |
| **Орудний шляху та простору** | ✅ | 720 | Included in Core |
| **Орудний сумісності та керування дієслів** | ✅ | 742 | Included in Core |
| **Орудний у пасивних конструкціях** | ✅ | 609 | Included in Core |
| **Прийменники з Ор.в. (§4.2.2.5)** | ✅ | 588 | Included in Core |
| **Підсумок** | ✅ | 517 | Included in Core |