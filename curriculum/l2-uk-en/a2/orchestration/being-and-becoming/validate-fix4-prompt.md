        # Fix 10 issue(s) in `being-and-becoming`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'українська' (f) + 'роботи' (f/p)
**How to fix:** Change 'українська' to match the gender/case of 'роботи', or vice versa.
**Where:** ~line 36

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'професійну' (f) + 'процес' (m)
**How to fix:** Change 'професійну' to match the gender/case of 'процес', or vice versa.
**Where:** ~line 36

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'студенткою' (f)
**How to fix:** Change 'була' to match the gender/case of 'студенткою', or vice versa.
**Where:** ~line 82

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'доконане' (n) + 'дієслова' (n/p)
**How to fix:** Change 'доконане' to match the gender/case of 'дієслова', or vice versa.
**Where:** ~line 91

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночу' (f) + 'форми' (f/p)
**How to fix:** Change 'жіночу' to match the gender/case of 'форми', or vice versa.
**Where:** ~line 126

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'сучасної' (f) + 'аспект' (m)
**How to fix:** Change 'сучасної' to match the gender/case of 'аспект', or vice versa.
**Where:** ~line 194

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночий' (m) + 'айтівка' (f)
**How to fix:** Change 'жіночий' to match the gender/case of 'айтівка', or vice versa.
**Where:** ~line 194

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'хорошою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'хорошою', or vice versa.
**Where:** ~line 313

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'українською' (f) + 'плани' (p)
**How to fix:** Change 'українською' to match the gender/case of 'плани', or vice versa.
**Where:** ~line 341

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'теперішній' (f/m) + 'що' (n)
**How to fix:** Change 'теперішній' to match the gender/case of 'що', or vice versa.
**Where:** ~line 341





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

