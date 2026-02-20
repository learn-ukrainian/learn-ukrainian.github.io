Good — the status JSON confirms word count is **2545/2000** (passes comfortably). The Green Team's ~1450 estimate was wrong. Now let me do the deep adversarial review.

---

## Phase 9: Final QA Review — the-cyrillic-code-ii

### Issues Found

**Issue 1 (CRITICAL): Anagram activity letters NOT scrambled**
- **File**: `activities/the-cyrillic-code-ii.yaml`, lines 283-298
- **Evidence**: `scrambled: ш к о л а` for answer `школа`, `scrambled: ц е н т р` for answer `центр`, etc. All 8 items have the letters in the correct order with spaces. The activity is trivial and broken.
- **Fix**: Actually scramble the letters.

**Issue 2 (IMPORTANT): Pedagogical jargon — "voiced glottal fricative"**
- **File**: `the-cyrillic-code-ii.md`, line 44
- **Text**: `This is a **voiced** glottal fricative.`
- **Problem**: "Glottal fricative" is linguistics jargon that intimidates A1 beginners. The simpler description follows it, but the technical term is a wall.
- **Fix**: Remove the technical term; keep the accessible description.

**Issue 3 (IMPORTANT): Alienating tone — "you will sound Russian"**
- **File**: `the-cyrillic-code-ii.md`, line 59
- **Text**: `If you pronounce **Г** as a hard "g", you will sound Russian.`
- **Problem**: Accusatory framing discourages beginners who are still learning. The pedagogical goal (correct [ɦ] pronunciation) is right, but the motivation should be positive ("sound authentic") not negative ("sound Russian").
- **Fix**: Rephrase to focus on sounding authentically Ukrainian.

**Issue 4 (IMPORTANT): Match-up activity missing Я and Й**
- **File**: `activities/the-cyrillic-code-ii.yaml`, lines 1-24
- **Evidence**: 10 pairs covering Г, Ґ, Ж, Ш, Ч, Ц, Щ, Є, Ї, Ю. Missing **Я** (ya, like 'yard') and **Й** (y, like 'boy'), both taught in the lesson.
- **Fix**: Add both to the match-up.

**Issue 5 (MODERATE): IPA tie bar missing for Ц — two locations**
- **File**: `the-cyrillic-code-ii.md`, line 81: `**Sound**: [ts]` — should be `[t͡s]`
- **File**: `the-cyrillic-code-ii.md`, line 165: `**Ц** [ts]` — should be `[t͡s]`
- **Problem**: All other affricates (Ч [t͡ʃ], Щ [ʃt͡ʃ]) correctly use tie bars. Ц is inconsistent. The formal example on line 82 (`[t͡sɛntr]`) has the tie bar, but the Sound field and the inline reference don't.

**Issue 6 (MODERATE): Є "Function" line misleading**
- **File**: `the-cyrillic-code-ii.md`, lines 88-90
- **Text**: `*   **Function**: Softens the previous consonant.` followed by example **Європа** (word-initial — no preceding consonant to soften).
- **Problem**: The intro paragraph already explains the softening function for all iotated vowels. Repeating it under Є alone (not under Ю, Я, Ї) is both redundant and contradicted by the word-initial example. A beginner will think "what consonant does Є soften in Європа?"
- **Fix**: Remove the misleading "Function" line; integrate position awareness into the example.

**Issue 7 (MINOR): Missing шість from Soft Sign section**
- **File**: `the-cyrillic-code-ii.md`, lines 110-117
- **Evidence**: Meta point says "Examples: Львів, шість, день." Content has день and Львів but NOT шість.
- **Fix**: Add шість as a third example.

**Issue 8 (MINOR — no fix needed): Ъ as quiz distractor**
- **File**: `activities/the-cyrillic-code-ii.yaml`, line 135
- **Evidence**: Option `Ъ` (Russian hard sign) used as wrong answer in "Which symbol is the Soft Sign?" quiz.
- **Assessment**: Pedagogically justified in context — the module is literally about distinguishing Ukrainian from non-Ukrainian letters. Acceptable distractor.

**Issue 9 (INFO — no fix needed): SCOPE parenthetical lists 12 letters but says 14**
- Line 2 lists 12 letters; the module also covers Й and the И/І distinction. Non-student-facing comment, not worth fixing.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
*   **Sound**: [ɦ]. This is a **voiced** glottal fricative. It sounds like the "h" in "ahead" or "behave," but with your voice box vibrating. It is NOT the hard "g" in "go."
---NEW---
*   **Sound**: [ɦ]. It sounds like the "h" in "ahead" or "behave," but deeper and with your voice box vibrating. It is NOT the hard "g" in "go."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
> If you pronounce **Г** as a hard "g", you will sound Russian. Using the correct soft [ɦ] for **Г** is the #1 way to improve your accent immediately.
---NEW---
> If you pronounce **Г** as a hard "g", you will lose the authentic Ukrainian sound. Using the correct soft [ɦ] for **Г** is the #1 way to improve your accent immediately.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
*   **Sound**: [ts]. Identical to the "ts" in "cats" or "boots." It looks like a square U with a tail.
---NEW---
*   **Sound**: [t͡s]. Identical to the "ts" in "cats" or "boots." It looks like a square U with a tail.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
#### Є (Ye)
*   **Sound**: [jɛ]. Pronounced as "ye" in "yes."
*   **Function**: Softens the previous consonant.
*   **Example**: **Європа** [jɛu̯ˈrɔpɑ] (Europe).
---NEW---
#### Є (Ye)
*   **Sound**: [jɛ]. Pronounced as "ye" in "yes."
*   **Example**: **Європа** [jɛu̯ˈrɔpɑ] (Europe). At the start of a word, you hear the full "ye" sound. After a consonant, the [j] merges and softens that consonant.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
*   **Example**: **день** [dɛnʲ] (day).
    *   Without soft sign: *den* (hard n).
    *   With soft sign: *dyen'* (soft n, sounds lighter and higher).
*   **Example**: **Львів** [lʲʋiu̯] (Lviv). The "L" is soft, almost like the "l" in "leaf," not the hard "l" in "ball."
---NEW---
*   **Example**: **день** [dɛnʲ] (day).
    *   Without soft sign: *den* (hard n).
    *   With soft sign: *dyen'* (soft n, sounds lighter and higher).
*   **Example**: **шість** [ʃistʲ] (six). The final **Т** is softened — it ends with a light, gentle release.
*   **Example**: **Львів** [lʲʋiu̯] (Lviv). The "L" is soft, almost like the "l" in "leaf," not the hard "l" in "ball."
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
1.  **центр** [t͡sɛntr] — center. Note the **Ц** [ts] at the start. It is sharp, like a snare drum.
---NEW---
1.  **центр** [t͡sɛntr] — center. Note the **Ц** [t͡s] at the start. It is sharp, like a snare drum.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml
---OLD---
  - left: Ю
    right: yu (like 'universe')
  title: Letter to Sound Match
---NEW---
  - left: Ю
    right: yu (like 'universe')
  - left: Я
    right: ya (like 'yard')
  - left: Й
    right: y (like 'boy')
  title: Letter to Sound Match
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml
---OLD---
  - answer: школа
    scrambled: ш к о л а
  - answer: центр
    scrambled: ц е н т р
  - answer: яблуко
    scrambled: я б л у к о
  - answer: Європа
    scrambled: Є в р о п а
  - answer: гарний
    scrambled: г а р н и й
  - answer: чай
    scrambled: ч а й
  - answer: день
    scrambled: д е н ь
  - answer: жити
    scrambled: ж и т и
---NEW---
  - answer: школа
    scrambled: а л ш к о
  - answer: центр
    scrambled: р ц е т н
  - answer: яблуко
    scrambled: к о б я л у
  - answer: Європа
    scrambled: р п а Є в о
  - answer: гарний
    scrambled: й р а н г и
  - answer: чай
    scrambled: й ч а
  - answer: день
    scrambled: н ь е д
  - answer: жити
    scrambled: т и ж и
===FIX_END===

---

### Verification Summary

| Check | Result |
|-------|--------|
| Word count | 2545/2000 — PASS (Green Team's ~1450 estimate was wrong) |
| All meta sections present | PASS (5/5 sections) |
| Required vocabulary in prose | PASS (центр, чай, школа, гарний, жити, день, Європа, яблуко — all present) |
| Objectives → self-check mapping | PASS (4/4 objectives covered) |
| IPA accuracy (tie bars, ʋ for В) | PASS after Ц fix (two locations) |
| Russianisms | CLEAN |
| Russian characters in content | CLEAN (Ъ as quiz distractor is pedagogically justified) |
| Gender/case agreement | N/A (module is about alphabet, no inflected forms tested) |
| Activity grammar (fill-in) | PASS (all 16 fill-in sentences produce grammatical Ukrainian) |
| Factual claims | PASS (1933 Ґ ban, 1990 reinstatement — historically accurate) |
| LLM artifacts | CLEAN (no purple prose, no "Це не просто X, а Y" pattern, no invented statistics) |
| Anagram scrambling | FAIL → FIXED |

===VERDICT===
APPROVE
===END_VERDICT===