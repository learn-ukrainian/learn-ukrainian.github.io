        # Fix 7 issue(s) in `being-and-becoming`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'успішним' (m/n/p) + 'став' (m)
**How to fix:** Change 'успішним' to match the gender/case of 'став', or vice versa.
**Where:** ~line 136

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'студенткою' (f)
**How to fix:** Change 'була' to match the gender/case of 'студенткою', or vice versa.
**Where:** ~line 230

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'директоркою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'директоркою', or vice versa.
**Where:** ~line 256

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'задоволена' (f) + 'своїм' (m/n/p)
**How to fix:** Change 'задоволена' to match the gender/case of 'своїм', or vice versa.
**Where:** ~line 264

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'впевнений' (m) + 'що' (n)
**How to fix:** Change 'впевнений' to match the gender/case of 'що', or vice versa.
**Where:** ~line 282

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'лікаркою' (f)
**How to fix:** Change 'була' to match the gender/case of 'лікаркою', or vice versa.
**Where:** ~line 287

### Fix: Gate `Immersion` FAIL — 34.7% LOW (target 45-65% (A2.1))
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

