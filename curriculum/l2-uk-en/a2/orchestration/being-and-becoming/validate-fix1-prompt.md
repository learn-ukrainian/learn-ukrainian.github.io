        # Fix 4 issue(s) in `being-and-becoming`

        ### Fix 1: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'Айтішник' — prefer: айтівець
**How to fix:** Replace 'Айтішник' with 'айтівець'
**Where:** ~line 105

### Fix 2: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'айтішниця' — prefer: айтівка
**How to fix:** Replace 'айтішниця' with 'айтівка'
**Where:** ~line 106

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'юристкою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'юристкою', or vice versa.
**Where:** ~line 120

### Fix 4: REPETITIVE_TRANSITIONS
**What:** 3 sections start with '<!-- adapted from: вашуленко...'
**How to fix:** Vary section openings — repetitive transitions are an LLM pattern.
**Where:** ~lines 13, 110, 143

### Other Audit Failures

```
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
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

