Now I have all the data. Let me do the deep adversarial review.

---

## Phase 9 Final QA Review: the-cyrillic-code-ii

### Files Verified
- Content: `the-cyrillic-code-ii.md` (289 lines) — read in full
- Activities: `activities/the-cyrillic-code-ii.yaml` (426 lines) — read in full
- Vocabulary: `vocabulary/the-cyrillic-code-ii.yaml` (81 lines, 20 entries) — read in full
- Meta: `meta/the-cyrillic-code-ii.yaml` — read in full
- Plan: `plans/a1/the-cyrillic-code-ii.yaml` — read in full
- Module 1 SCOPE — cross-checked

**Note**: The Green Team review was based on an older version. Several issues they flagged (unscrambled anagrams, "you will sound Russian" phrasing, jargon "voiced glottal fricative") are already fixed in the current content. The vocabulary file exists with 20 entries (Green Team reported "file not found").

---

### Issues Found

**Issue 1: FACTUAL ERROR — "four letters that exist in no other Cyrillic alphabet" (MEDIUM)**
- **Location**: `the-cyrillic-code-ii.md`, line 262
- **Text**: `Ukrainian has four letters that exist in no other Cyrillic alphabet: **Ґ**, **Є**, **Ї**, **І**.`
- **Problem**: **І** (with dot) is also used in the Belarusian alphabet, Kazakh Cyrillic, and several other Cyrillic scripts. The claim that all four individually exist in "no other Cyrillic alphabet" is factually wrong and could undermine credibility if a student cross-references. The *combination* of all four is what's unique to Ukrainian. **Ї** specifically is the one that exists in no other modern standard alphabet.
- **Fix**: Reword to claim the combination is unique and single out Ї.

**Issue 2: INCONSISTENT SECTION HEADER — English among Ukrainian headers (MINOR)**
- **Location**: `the-cyrillic-code-ii.md`, line 184
- **Text**: `### Distinguishing Sounds: И vs І`
- **Problem**: All parallel subsection headers in "Практика" are in Ukrainian (Читаємо нові звуки, Тренування шиплячих, Розрізняємо звуки: Г проти Ґ, Виклик м'якого знака, Сила апострофа) except this one. Inconsistent.
- **Fix**: Change to Ukrainian: `### Розрізняємо звуки: И проти І`

**Issue 3: MISLEADING ROMANIZATION — "dyen'" for день (MINOR)**
- **Location**: `the-cyrillic-code-ii.md`, line 115
- **Text**: `With soft sign: *dyen'* (soft n, sounds lighter and higher).`
- **Problem**: "dyen'" incorrectly implies the **д** is palatalized (the "dy" suggests a change in the d). In день [dɛnʲ], only the **н** is palatalized. The д stays hard. The romanization should reflect that only the ending changes.
- **Fix**: Change to `*den'*` to match the "without" version and show only the n changes.

**Issue 4: CONFUSING PRONUNCIATION GUIDE — "KYY-yee-w" for Київ (MINOR)**
- **Location**: `the-cyrillic-code-ii.md`, line 236
- **Text**: `Result: KYY-yee-w. It is not "Key-ev."`
- **Problem**: "KYY-yee-w" suggests three syllables when Київ is two syllables [ˈkɪ.jiu̯]. The double Y in "KYY" is confusing. A clearer approximation for A1 learners: "KY-yiv".
- **Fix**: Simplify to a two-syllable approximation.

---

### Checks Passed (No Issues)

**IPA Accuracy**: All IPA transcriptions verified. Affricates have tie bars (t͡s, t͡ʃ). В correctly rendered as [ʋ]. Г correctly as [ɦ]. Palatalization marks [ʲ] present where needed. Європа [jɛu̯ˈrɔpɑ] — defensible (В → [u̯] before consonant).

**Russianisms**: CLEAN. No кушати, получати, приймати участь, слідуючий found.

**Russian characters**: CLEAN. The Ъ in the quiz (line 139) is an intentional incorrect-answer distractor — pedagogically valid.

**Grammar/Case agreement**: All Ukrainian text correct. Summary section uses proper forms.

**Plan compliance**: All 5 meta outline sections present. All 8 required vocabulary words used in prose. All 6 recommended vocabulary words appear. All 4 objectives map to self-check questions.

**Activities**: 8 activities total. All quiz answers correct. All fill-in answers produce grammatical Ukrainian sentences. Anagram letters are properly scrambled (verified letter-by-letter). Match-up pairs are accurate. Group-sort categories correct (Й omitted from the sort — acceptable).

**Vocabulary YAML**: 20 entries with IPA, lemma, POS, translation. All IPA matches the content file transcriptions. Tie bars on affricates present.

**Factual accuracy**: 1933 ban of Ґ — correct. 1990 reinstatement — correct. Mariupol Ї graffiti — documented. Kyiv vs Kiev transliteration explanation — accurate.

**LLM artifacts**: No purple prose. No "Це не просто X, а Y" overuse. No folk etymology. No invented statistics. "100 times more common" for Г vs Ґ (line 182) is conservative if anything.

**Word count**: Audit tool reports PASS on all 7 gates. Content is dense and well-structured.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
> Looking at the alphabet alone disproves this. Ukrainian has four letters that exist in no other Cyrillic alphabet: **Ґ**, **Є**, **Ї**, **І**. These are not cosmetic variations — they represent sounds and phonetic principles unique to Ukrainian.
---NEW---
> Looking at the alphabet alone disproves this. Ukrainian is the only language whose alphabet contains all four of these letters: **Ґ**, **Є**, **Ї**, **І**. The letter **Ї** exists in no other alphabet on earth. These are not cosmetic variations — they represent sounds and phonetic principles unique to Ukrainian.
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
### Distinguishing Sounds: И vs І
---NEW---
### Розрізняємо звуки: И проти І
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
    *   With soft sign: *dyen'* (soft n, sounds lighter and higher).
---NEW---
    *   With soft sign: *den'* (soft n, sounds lighter and higher).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
---OLD---
    *   Result: KYY-yee-w. It is not "Key-ev."
---NEW---
    *   Result: KY-yiv. It is not "Key-ev."
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Rationale**: The module is pedagogically strong, linguistically accurate, and well-structured. The four issues found are all minor and fully addressed by the fix blocks above. No Russianisms, no broken activities, no scope violations, no LLM artifacts. The factual error about the four unique letters is the most substantive issue but is cleanly fixable without structural changes. Content passes all audit gates. After applying fixes, this is a solid A1 module.