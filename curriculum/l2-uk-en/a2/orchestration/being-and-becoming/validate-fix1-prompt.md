        # Fix 17 issue(s) in `being-and-becoming`

        ### Fix 1: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'айтішник' — prefer: айтівець
**How to fix:** Replace 'айтішник' with 'айтівець'
**Where:** ~line 94

### Fix 2: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'айтішниця' — prefer: айтівка
**How to fix:** Replace 'айтішниця' with 'айтівка'
**Where:** ~line 94

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'лікаркою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'лікаркою', or vice versa.
**Where:** ~line 33

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'минулого' (m/n) + 'лікаркою' (f)
**How to fix:** Change 'минулого' to match the gender/case of 'лікаркою', or vice versa.
**Where:** ~line 33

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'вчителькою' (f)
**How to fix:** Change 'була' to match the gender/case of 'вчителькою', or vice versa.
**Where:** ~line 42

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'директоркою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'директоркою', or vice versa.
**Where:** ~line 52

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'велике' (n) + 'Київ' (p)
**How to fix:** Change 'велике' to match the gender/case of 'Київ', or vice versa.
**Where:** ~line 111

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'великого' (m/n) + 'директоркою' (f)
**How to fix:** Change 'великого' to match the gender/case of 'директоркою', or vice versa.
**Where:** ~line 111

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'вчителькою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'вчителькою', or vice versa.
**Where:** ~line 123

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'менеджеркою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'менеджеркою', or vice versa.
**Where:** ~line 130

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'журналісткою' (f)
**How to fix:** Change 'була' to match the gender/case of 'журналісткою', or vice versa.
**Where:** ~line 147

### Fix 12: AGREEMENT_ERROR
**What:** Agreement mismatch: 'відомим' (m/n/p) + 'став' (m)
**How to fix:** Change 'відомим' to match the gender/case of 'став', or vice versa.
**Where:** ~line 181

### Fix 13: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Олег
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** being-and-becoming.yaml

### Fix: Gate `Immersion` FAIL — 31.3% LOW (target 45-65% (A2.1))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 15: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: орудний
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [CONTENT_REDUNDANCY] Redundant information detected in lesson (71% overlap): "→ He works as a journalist.)
**How to fix:** Remove redundant paragraphs. Ensure each section adds new unique value.

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'how do...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (71% overlap): "→ He works as a journalist.)
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'how do...'.
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

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

