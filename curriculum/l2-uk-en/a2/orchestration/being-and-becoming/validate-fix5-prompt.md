        # Fix 2 issue(s) in `being-and-becoming`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'українська' (f) + 'роботу' (f/m)
**How to fix:** Change 'українська' to match the gender/case of 'роботу', or vice versa.
**Where:** ~line 36

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'програмісткою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'програмісткою', or vice versa.
**Where:** ~line 313





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

