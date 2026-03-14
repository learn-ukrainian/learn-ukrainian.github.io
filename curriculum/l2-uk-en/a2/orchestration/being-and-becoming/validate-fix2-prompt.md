        # Fix 11 issue(s) in `being-and-becoming`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'впевнений' (m) + 'що' (n)
**How to fix:** Change 'впевнений' to match the gender/case of 'що', or vice versa.
**Where:** ~line 45

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'менеджеркою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'менеджеркою', or vice versa.
**Where:** ~line 95

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'звичайною' (f)
**How to fix:** Change 'була' to match the gender/case of 'звичайною', or vice versa.
**Where:** ~line 95

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'лікарів' (m) + 'талановитих' (p)
**How to fix:** Change 'лікарів' to match the gender/case of 'талановитих', or vice versa.
**Where:** ~line 132

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'вчителькою' (f)
**How to fix:** Change 'була' to match the gender/case of 'вчителькою', or vice versa.
**Where:** ~line 166

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'простою' (f/m)
**How to fix:** Change 'була' to match the gender/case of 'простою', or vice versa.
**Where:** ~line 220

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'нашого' (m/n) + 'директоркою' (f)
**How to fix:** Change 'нашого' to match the gender/case of 'директоркою', or vice versa.
**Where:** ~line 223

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'хорошою' (f) + 'буду' (f)
**How to fix:** Change 'хорошою' to match the gender/case of 'буду', or vice versa.
**Where:** ~line 224

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'економісткою' (f)
**How to fix:** Change 'була' to match the gender/case of 'економісткою', or vice versa.
**Where:** ~line 229

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'айтівкою' (f)
**How to fix:** Change 'була' to match the gender/case of 'айтівкою', or vice versa.
**Where:** ~line 230

### Fix 11: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Іван
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** being-and-becoming.yaml





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

