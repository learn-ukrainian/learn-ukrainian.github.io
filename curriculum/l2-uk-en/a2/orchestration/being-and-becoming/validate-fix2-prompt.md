        # Fix 7 issue(s) in `being-and-becoming`

        ### Fix: Gate `Pedagogy` FAIL — 4 violations

### Fix: Gate `Immersion` FAIL — 11.3% LOW (target 45-65% (A2.1))
**⚠ SCOPE WARNING:** Immersion gap is 34% (11.3% → 45% min). This is too large for a fix pass. Focus on the EASIEST wins:
1. Add Ukrainian section headers with English in parentheses
2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
3. Add short Ukrainian phrases with (translations) in existing paragraphs
Do NOT rewrite entire sections. Target +5-8% improvement max.

### Fix 3: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] unjumble 'Put the Words in Order' item 2 has 3 words (target: 5-10)
**How to fix:** Adjust sentence length to 5-10 words to match A2 complexity.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] unjumble 'Put the Words in Order' item 3 has 3 words (target: 5-10)
**How to fix:** Adjust sentence length to 5-10 words to match A2 complexity.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] unjumble 'Put the Words in Order' item 4 has 3 words (target: 5-10)
**How to fix:** Adjust sentence length to 5-10 words to match A2 complexity.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] unjumble 'Put the Words in Order' item 5 has 3 words (target: 5-10)
**How to fix:** Adjust sentence length to 5-10 words to match A2 complexity.

### Fix 7: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: називний, орудний
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Other Audit Failures

```
❌ AUDIT FAILED: Transliteration detected: 'Вступ (Introduction)'. Remove Latin in parentheses.
📚 PEDAGOGICAL VIOLATIONS FOUND:
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
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

