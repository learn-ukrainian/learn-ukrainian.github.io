        # Fix 16 issue(s) in `being-and-becoming`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'називного' (m/n) + 'Пастка' (f)
**How to fix:** Change 'називного' to match the gender/case of 'Пастка', or vice versa.
**Where:** ~line 48

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'коротких' (p) + 'кілька' (f)
**How to fix:** Change 'коротких' to match the gender/case of 'кілька', or vice versa.
**Where:** ~line 56

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'студенткою' (f)
**How to fix:** Change 'була' to match the gender/case of 'студенткою', or vice versa.
**Where:** ~line 78

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'доконане' (n) + 'дієслова' (n/p)
**How to fix:** Change 'доконане' to match the gender/case of 'дієслова', or vice versa.
**Where:** ~line 87

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'хорошим' (m/n/p) + 'стану' (m)
**How to fix:** Change 'хорошим' to match the gender/case of 'стану', or vice versa.
**Where:** ~line 97

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'українським' (m/n/p) + 'слово' (n)
**How to fix:** Change 'українським' to match the gender/case of 'слово', or vice versa.
**Where:** ~line 105

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Нова' (f) + 'Читання' (n/p)
**How to fix:** Change 'Нова' to match the gender/case of 'Читання', or vice versa.
**Where:** ~line 129

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'хорошим' (m/n/p) + 'став' (m)
**How to fix:** Change 'хорошим' to match the gender/case of 'став', or vice versa.
**Where:** ~line 134

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'український' (m) + 'році' (m)
**How to fix:** Change 'український' to match the gender/case of 'році', or vice versa.
**Where:** ~line 158

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'освіченої' (f) + 'ознака' (f)
**How to fix:** Change 'освіченої' to match the gender/case of 'ознака', or vice versa.
**Where:** ~line 172

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'головною' (f)
**How to fix:** Change 'стала' to match the gender/case of 'головною', or vice versa.
**Where:** ~line 209

### Fix 12: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночий' (m) + 'мати' (f/p)
**How to fix:** Change 'жіночий' to match the gender/case of 'мати', or vice versa.
**Where:** ~line 215

### Fix 13: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'хорошою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'хорошою', or vice versa.
**Where:** ~line 289

### Fix 14: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Велика' (f) + 'Читання' (n/p)
**How to fix:** Change 'Велика' to match the gender/case of 'Читання', or vice versa.
**Where:** ~line 293

### Fix 15: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'вчителькою' (f)
**How to fix:** Change 'була' to match the gender/case of 'вчителькою', or vice versa.
**Where:** ~line 295

### Fix: Gate `Immersion` FAIL — 44.2% LOW (target 45-65% (A2.1))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Other Audit Failures

```
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a2/audit/being-and-becoming-audit.log for details)
```





## Immersion Rules

TARGET: 45-65% Ukrainian.

**Structural containment**: English prose in paragraphs. Ukrainian in CONTAINERS ONLY (tables, blockquotes, numbered lists, dialogues). Do NOT mix Ukrainian words into English sentences.


## Level Constraints

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles


## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

