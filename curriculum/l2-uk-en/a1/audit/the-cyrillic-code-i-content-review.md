# Content Review: The Cyrillic Code I (a1-001)

**Reviewer:** Claude (Opus 4.6)
**Date:** 2026-03-05
**Build:** v4 pipeline (fresh rebuild)
**Plan version:** 4.1
**Issue:** #730

---

## Summary

| Metric | Value |
|--------|-------|
| **Grade** | **B** |
| **Word count** | 1566 (target: 1200) |
| **Activities** | 8 types, 249 lines |
| **Vocabulary** | 20 items (15 plan + 5 extra) |
| **CRITICAL** | 0 |
| **HIGH** | 0 |
| **MEDIUM** | 6 |
| **LOW** | 4 |

**Verdict:** PASS with fixes needed. Content is well-structured and linguistically accurate but misses several specific plan requirements. No factual or linguistic errors found.

---

## Check 1: Plan Adherence

### Objectives Coverage

| Objective | Covered? | Notes |
|-----------|----------|-------|
| Recognize and pronounce 7 letters (A, O, У, М, Л, Н, С) | YES | Each letter has its own subsection with video |
| Classify letters as голосні vs приголосні | YES | Clear definitions with correct grouping |
| Combine letters into open and closed syllables | YES | Full tables for both open and closed syllables |
| Read simple words using the 7 known letters | YES | 14-word reading drill |

### Section Coverage

| Plan Section | Words Target | Present | Notes |
|---|---|---|---|
| Introduction | 200 | Yes | ~250 words |
| Vowels A O U | 250 | Yes | ~300 words |
| Consonants M L N S | 250 | Yes | ~280 words |
| Syllables and Words | 400 | Yes | ~500 words, strong drill section |
| Summary | 100 | Yes | ~120 words |

### Plan Points — Missing Items

| # | Severity | Plan Requirement | Status |
|---|---|---|---|
| M1 | MEDIUM | Cultural hook: Cyrillic script descends from alphabet created by students of Saints Cyril and Methodius in the First Bulgarian Empire | **MISSING** — Introduction mentions Cyrillic origin but not the First Bulgarian Empire or students of Cyril/Methodius specifically |
| M2 | MEDIUM | Critical contrast: Ukrainian O never reduces to /a/ in unstressed position (unlike Russian) | **MISSING** — O section describes the sound but omits the Russian contrast |
| M3 | MEDIUM | Textbook phrases from Bolshakova p.22: "У нас — ананас." "У нас — сом." "А у вас?" | **MISSING** — Syllables section has word drills but not these specific phrases |
| M4 | MEDIUM | Summary should preview next module listing 7 letters: "The Cyrillic Code II adds К, И, І, Р, В, Т, Е" | **MISSING** — Summary mentions next module but doesn't list the 7 letters |
| M5 | MEDIUM | Embed overview video link (Anna Ohoiko) in Introduction | **MISSING** — Individual letter videos present but overview video not embedded |
| L1 | LOW | "Ukrainian has 10 vowels (голосні)" — total count not stated | **MISSING** — Vowel section doesn't state the total of 10 |
| L2 | LOW | Word "мало" (little/few) missing from reading drill | **MISSING** — In vocab YAML but not in content drill list |

### Vocabulary Coverage

**Plan required (8):** мама, сом, сон, масло, ананас, нам, нас, сам — all present in content and vocab YAML.

**Plan recommended (7):** оса, сосна, насос, лама, смола, слон, мало — all present except мало missing from content drill.

**Extra words in vocab YAML (5):** сало, соус, сума, мул, луна — all verified in VESUM. All decodable from the 7-letter charset (АОУМЛНС). Acceptable additions but not in plan.

---

## Check 2: Linguistic Accuracy

### VESUM Verification

All 20 vocabulary words verified. No ghost words found.

| Word | VESUM | Decodable (АОУМЛНС) |
|---|---|---|
| мама | noun, f | Yes |
| сом | noun, m | Yes |
| сон | noun, m | Yes |
| масло | noun, n | Yes |
| ананас | noun, m | Yes |
| нам | pronoun | Yes |
| нас | pronoun | Yes |
| сам | adj/pronoun | Yes |
| оса | noun, f | Yes |
| сосна | noun, f | Yes |
| насос | noun, m | Yes |
| лама | noun, f | Yes |
| смола | noun, f | Yes |
| слон | noun, m | Yes |
| мало | adverb | Yes |
| сало | noun, n | Yes |
| соус | noun, m | Yes |
| сума | noun, f | Yes |
| мул | noun, m | Yes |
| луна | noun, f | Yes |

### Russianisms Check

No Russianisms detected. All Ukrainian forms correct.

### Grammar & Phonetics Accuracy

- Letter-sound correspondences are accurate
- False friend warnings for Н/N and С/S are correct and well-emphasized
- "Highly phonetic" claim is an appropriate A1 simplification
- Cyrillic origin description is accurate

---

## Check 3: Pedagogical Quality

**Lesson Quality Score:** 8/10

### Strengths
- Clear progression: individual letters -> syllables -> words
- False friend warnings prominent and well-explained (Н looks like H, С looks like C)
- Open vs closed syllable distinction taught explicitly
- Decodability maintained — every word uses only the 7 target letters
- Warm, encouraging tone appropriate for absolute beginners
- Video links for each letter provide pronunciation support

### Weaknesses
- Missing O/Russian contrast (M2) is a pedagogical gap — learners with Russian exposure will expect vowel reduction
- Missing Bolshakova phrases (M3) removes a textbook connection point that gives authenticity
- Missing cultural hook specifics (M1) reduces the "why Cyrillic matters" motivation

### Tier 1 "Would I Continue?" Test

| Question | Result |
|----------|--------|
| Did I feel overwhelmed? | PASS — 7 letters, gentle pacing |
| Were instructions clear? | PASS — English scaffolding throughout |
| Did I get quick wins? | PASS — Reading "мама" early |
| Was Ukrainian scary? | PASS — Heavy English support |
| Would I come back tomorrow? | PASS — Encouraging ending with preview |

---

## Check 4: Activities Review

| Activity | Type | Items | Quality |
|----------|------|-------|---------|
| Watch and Repeat | watch-and-repeat | 7 | Good — one video per letter, correct URLs |
| Vowels and Consonants | classify | 7 | Good — correct categorization |
| What Letter Does it Start With? | image-to-letter | 8 | **Issue M6** — see below |
| Match the Word to its Meaning | match-up | 8 | Good — correct translations |
| Sort Syllables | group-sort | 12 | Good — correct open/closed classification |
| Unscramble the Words | anagram | 8 | Good — all decodable |
| Letter and Sound Check | quiz | 8 | Good — false friend focus, good explanations |
| True or False | true-false | 8 | Good — reinforces key concepts |

**Total items:** 66 — strong coverage.
**Type variety:** 8/8 unique types — excellent.
**Decodability:** All activity items use only АОУМЛНС — PASS.

### Activity Issue

| # | Severity | Issue |
|---|---|---|
| M6 | MEDIUM | image-to-letter: bee emoji (line 64) used for word "оса" (wasp). A bee is бджола, not оса. Should use a different emoji or word pair. |

---

## Check 5: Engagement

| Metric | Status | Notes |
|--------|--------|-------|
| Videos embedded | 7 letter videos present | Overview video missing (M5) |
| Activity variety | 8 types | Excellent |
| Callout boxes / formatting | Present | Tables, bold, structured layout |
| Walls of text | None | Short paragraphs throughout |

---

## Issues Summary

### CRITICAL (0)
None.

### HIGH (0)
None.

### MEDIUM (6)

| ID | Description | Location | Fix |
|----|-------------|----------|-----|
| M1 | Missing cultural hook (First Bulgarian Empire, students of Cyril & Methodius) | Content: Introduction | Add 1-2 sentences about Cyrillic origin |
| M2 | Missing O/Russian vowel reduction contrast | Content: Vowels section | Add note: "Unlike Russian, Ukrainian О never reduces" |
| M3 | Missing Bolshakova textbook phrases ("У нас — ананас." etc.) | Content: Syllables section | Add phrase box with attribution |
| M4 | Summary doesn't list the 7 letters of next module | Content: Summary | Add: "К, И, І, Р, В, Т, Е" |
| M5 | Overview video not embedded in Introduction | Content: Introduction | Embed overview video link |
| M6 | Bee emoji used for оса (wasp) — бджола vs оса mismatch | Activities: image-to-letter line 64 | Replace emoji or word |

### LOW (4)

| ID | Description | Location |
|----|-------------|----------|
| L1 | Total vowel count (10) not stated in vowels section | Content: Vowels |
| L2 | мало missing from word reading drill (in vocab YAML but not prose) | Content: Syllables |
| L3 | Minor "Let us" sentence opening repetition | Content: multiple sections |
| L4 | 5 extra words in vocab YAML beyond plan (acceptable, just noting) | Vocabulary YAML |

---

## Grade Justification

**Grade: B.** Content is linguistically flawless (zero ghost words, zero Russianisms, all decodable), pedagogically sound with good pacing and encouragement, and has excellent activity variety (8 types, 66 items). However, 5 specific plan content points are missing (cultural hook details, O/Russian contrast, Bolshakova phrases, next-module letter list, overview video). These are all explicitly listed in the plan's `content_outline.points` and represent plan adherence gaps. The bee/wasp emoji mismatch in activities is an additional accuracy issue. No CRITICAL or HIGH issues — all fixable in one patch pass.

**Compared to previous review (Grade A):** The previous review was from an earlier build that included the cultural hook, O/Russian contrast, Bolshakova phrases, and overview video. The fresh v4 rebuild dropped these plan points, resulting in more plan adherence gaps.

---

*Review generated by Claude Opus 4.6 for issue #730.*
