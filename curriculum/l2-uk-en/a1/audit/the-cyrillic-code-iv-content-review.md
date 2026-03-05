# Content Review: the-cyrillic-code-iv

**Track:** a1 | **Sequence:** 4
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: ~1400+, target: 1200)
**Verdict:** C

## Plan Adherence

| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Recognize and pronounce all 33 Ukrainian letters | YES | Full Alphabet section | All letters presented |
| Explain iotated vowels and dual nature | YES | Iotated Vowels section | Dual nature explained clearly |
| Explain soft sign and apostrophe functions | YES | Soft Sign & Apostrophe | Both explained with examples |
| Identify digraphs as single sounds | YES | Affricates section | ДЖ and ДЗ covered |
| Read the complete Ukrainian alphabet fluently | PARTIAL | Summary section | Alphabet listing is **garbled** (see CRITICAL issue 1) |

### Section Structure

Plan has 6 sections; content has 5 sections. The plan's separate section "Дигріфи та Ґ -- Digraphs ДЖ, ДЗ + Letter Ґ" was merged into "Злиті звуки та рідкісні букви". This is a minor structural deviation -- the content covers the same material.

### Plan Key Words Not Used

The plan specifies key words for each letter. Most were replaced with alternatives:

| Letter | Plan Key Word | Content Key Word | Issue? |
|--------|--------------|-----------------|--------|
| Ц | цибуля | центр | OK -- both valid |
| Щ | щітка | ще | OK -- ще is higher frequency |
| Ф | фламінго | факт | OK -- both valid |
| Є | єнот | Європа | OK -- Європа is culturally better |
| Ї | їжак | їжа | OK -- їжа is higher frequency |
| Й | йогурт | чай | OK -- demonstrates word-final Й |
| Ь | сіль | день | OK -- both valid |

None of the plan key words appear. This is not blocking but shows the content writer diverged from the plan's vocabulary guidance.

### Vocabulary Coverage

| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| чай (tea) | YES | YES | YES |
| яблуко (apple) | YES | YES | YES |
| ще (more/still) | YES (table only) | YES | NO |
| їжа (food) | YES | YES | YES |
| день (day) | YES | YES | YES |
| сім'я (family) | YES | YES | YES |
| Львів (Lviv) | YES | YES | NO |

All required vocabulary present in prose and vocab YAML.

## Linguistic Accuracy

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| Garbled alphabet listing | **CRITICAL** | Line 236 | See Critical Issues below |
| Й classified as vowel | **HIGH** | Line 239 | "10 голосні (vowels): А, Е, И, **Й**, О, У + 4 йотовані" -- Й is a consonant, not a vowel. The module itself correctly states on line 175 that Й is "a very short consonant." This directly contradicts its own teaching. |
| юшка translated as "fish soup" | **MEDIUM** | Line 141 | юшка means "broth" or "soup" in general, not specifically "fish soup". VESUM confirms it as a valid word. The narrowing is misleading. |
| "Із з" in alphabet | **CRITICAL** | Line 236 | Part of the garbled alphabet listing -- "І і" became "Із з" |

## Pedagogical Quality

**Lesson Quality Score:** 8/10
**Tier Rubric Results:**

"Would I Continue?" Test: 4/5
- Overwhelmed? PASS -- concepts introduced progressively, one at a time
- Instructions clear? PASS -- English scaffolding throughout
- Quick wins? PASS -- diagnostic check at start, reading practice at end
- Ukrainian scary? PASS -- gentle introduction with translations
- Come back tomorrow? FAIL -- the garbled alphabet listing would confuse a learner at the milestone moment

**Strengths:**
- Each letter gets its own subsection with video, word table, and example sentences
- The dual nature concept is explained clearly for iotated vowels
- The soft sign vs apostrophe contrast is well-handled
- The Shevchenko poetry reading exercise is an excellent pedagogical touch
- Cultural hooks (Ґ as repressed letter, Ї as resistance symbol) are engaging

**Weaknesses:**
- The summary section, which should be a celebration moment, contains the most serious error in the module
- Some example sentences are repetitive ("Це X" pattern dominates)

## Activities Quality

| Activity | Type | Issues |
|----------|------|--------|
| Pronunciation Practice | watch-and-repeat | 10 items -- good coverage of all new letters |
| Iotated vs Basic Vowels | classify | Clean, well-designed |
| Complete Alphabet Categories | classify | Correct -- Й properly placed in consonants here |
| First Letter from Picture | image-to-letter | 8 items -- good; door emoji for ґанок is creative |
| Sort Letters and Symbols | group-sort | Clean |
| Knowledge Check | quiz | 8 items, all correct answers verified |
| True or False? | true-false | 8 items -- well-written with good explanations |
| Vocabulary Match | match-up | 8 pairs -- clean |
| Unscramble Words | anagram | 8 items -- letter counts verified correct |
| Complete the Phrase | fill-in | 8 items -- plausible distractors |

**Activity variety:** 7 distinct types out of 10 activities -- excellent variety.

**Note:** The classify activity on line 53 correctly places Й in consonants, contradicting the prose on line 239 which calls Й a vowel.

## Engagement

| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 4 | 3 | PASS |
| Tables | 14+ | -- | PASS |
| Videos embedded | 10 | 10 | PASS |

Callout types used: `[!history-bite]`, `[!culture]` (x2), `[!warning]`, `[!example]` -- good variety.

## Issues Found

### CRITICAL (blocks deployment)

1. **Garbled alphabet listing (line 236)**: The complete alphabet sequence is corrupted. The text reads:
   ```
   А а, Б б, У в, Г г, Ґ ґ, Д д, Е е, Є є, Ж ж, Із з, И и, Й і, Ї ї, Й і, К к, Л л, М м, Н н, О о, П п, Р р, С с, Т т, В у, Ф ф, Х х, Ц ц, Ч ч, Ш ш, Щ щ, Ь ь, Ю ю, Я я
   ```

   Multiple errors:
   - "У в" should be "В в" (uppercase/lowercase swapped)
   - "Із з" should be "З з" (extra І prepended)
   - "Й і" appears where "І і" should be
   - "Й і" appears again where "Й й" should be
   - "В у" should be "У у" (uppercase/lowercase swapped)

   The correct sequence should be:
   ```
   А а, Б б, В в, Г г, Ґ ґ, Д д, Е е, Є є, Ж ж, З з, И и, І і, Ї ї, Й й, К к, Л л, М м, Н н, О о, П п, Р р, С с, Т т, У у, Ф ф, Х х, Ц ц, Ч ч, Ш ш, Щ щ, Ь ь, Ю ю, Я я
   ```

   This is the culmination of the entire 4-module Cyrillic arc. A garbled alphabet at the finish line is a critical pedagogical failure.

### HIGH (should fix before deployment)

1. **Й misclassified as vowel (line 239)**: The text says "10 голосні (vowels): А, Е, И, Й, О, У + 4 йотовані (Є, Ї, Ю, Я)". Й is a consonant (the module itself says so on line 175). Ukrainian has 10 vowels: А, Е, И, І, О, У, Є, Ї, Ю, Я. The correct breakdown is: 10 vowels (including the 4 iotated ones), 22 consonants (including Й), 1 special (Ь). Replace the listing with:
   ```
   * **10 голосні (vowels):** А, Е, И, І, О, У + Є, Ї, Ю, Я (iotated)
   * **22 приголосні (consonants):** including Й
   ```

### MEDIUM (fix if possible)

1. **юшка as "fish soup" (line 141)**: юшка is a general term for broth/soup, not specifically fish soup. Correct to "soup/broth."
2. **Sentence pattern repetitiveness**: The example sentences heavily rely on "Це X" and "Там X" patterns. While acceptable for M4, adding variety (e.g., "Мій чай тут" for Й) would improve pedagogical value.

### LOW (informational)

1. **"Let us" used throughout instead of "Let's"**: The prose uses formal "Let us" consistently. While not wrong, "Let's" is more natural for the warm tutor persona. The tier-1 rubric says "Contractions allowed."
2. **Missing plan key words**: None of the plan's specified key words (цибуля, щітка, фламінго, єнот, їжак, йогурт, сіль) appear. The replacements are reasonable but this shows divergence from plan intent.

## Grade Justification

Grade **C**: The module has one CRITICAL issue (garbled alphabet listing at the culmination of the 4-module Cyrillic arc) and one HIGH issue (Й misclassified as vowel, contradicting the module's own teaching). The pedagogy, activities, and engagement are solid, and the linguistic content is otherwise accurate. However, the garbled alphabet listing in the summary section is a blocking deployment issue -- it would teach learners the wrong letter sequence at the exact moment they should be celebrating mastery.
