        # Fix 9 issue(s) in `imperative-and-requests`

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [it]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 111

### Fix 2: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: стояй
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** imperative-and-requests.yaml

### Fix: Gate `Words` FAIL — 1011/1200 (raw: 1495)
**Action:** Expand content in the shortest sections. Add examples, explanations, or practice scenarios.

### Fix: Gate `Activities` FAIL — 5/8
**Action:** Add more activities or diversify activity types in the activities YAML file.

### Fix: Gate `Pedagogy` FAIL — 3 violations

### Fix: Gate `Immersion` FAIL — 23.1% LOW (target 35-55% (M47))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 8: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Fix 9: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Dative case used at A1: 'мені'
**How to fix:** Dative case not allowed until A2 (M31+). Restructure sentence.

### Other Audit Failures

```
❌ [SECTION_LENGTH_MISMATCH] Section 'Наказовий спосіб (Imperative Mood)' is under target word count.
❌ [SECTION_LENGTH_MISMATCH] Section 'Вісім обов'язкових дієслів (Eight Required Verbs)' is under target word count.
❌ [SECTION_LENGTH_MISMATCH] Section 'Практика і підсумок (Summary and Practice)' is under target word count.
Наказовий спосіб (Imperative Mood)                  223 /  300  ❌ (-77)
Вісім обов'язкових дієслів (Eight Required Verbs)   250 /  350  ❌ (-100)
Практика і підсумок (Summary and Practice)           97 /  150  ❌ (-53)
TOTAL                                              1061 / 1200  ❌ (-139)
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/imperative-and-requests-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M47 — Imperative Mood):
This module TEACHES the imperative mood. Imperative forms are ALLOWED and REQUIRED.
Use imperative forms freely: читай/читайте, пиши/пишіть, скажи/скажіть, дай/дайте, іди/ідіть, дивись/дивіться, стій/стійте, слухай/слухайте.

Both imperfective AND perfective verbs are allowed for imperatives.
Past tense and future tense are available (taught at M36/M37).

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental) apply, EXCEPT: perfective aspect is ALLOWED for imperative forms.



## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/imperative-and-requests.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

