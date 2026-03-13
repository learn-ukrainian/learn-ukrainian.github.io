        # Fix 14 issue(s) in `being-and-becoming`

        ### Fix 1: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'айтішник' — prefer: айтівець
**How to fix:** Replace 'айтішник' with 'айтівець'
**Where:** ~line 124

### Fix 2: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'айтішниця' — prefer: айтівка
**How to fix:** Replace 'айтішниця' with 'айтівка'
**Where:** ~line 124

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'директоркою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'директоркою', or vice versa.
**Where:** ~line 100

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'успішним' (m/n/p) + 'став' (m)
**How to fix:** Change 'успішним' to match the gender/case of 'став', or vice versa.
**Where:** ~line 128

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'журналісткою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'журналісткою', or vice versa.
**Where:** ~line 140

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'студенткою' (f)
**How to fix:** Change 'була' to match the gender/case of 'студенткою', or vice versa.
**Where:** ~line 148

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'вчителькою' (f)
**How to fix:** Change 'була' to match the gender/case of 'вчителькою', or vice versa.
**Where:** ~line 150

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'чудовим' (m/n/p) + 'став' (m)
**How to fix:** Change 'чудовим' to match the gender/case of 'став', or vice versa.
**Where:** ~line 193

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'українською' (f) + 'фразу' (f)
**How to fix:** Change 'українською' to match the gender/case of 'фразу', or vice versa.
**Where:** ~line 232

### Fix 10: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Марія, Олег, програмітки
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** being-and-becoming.yaml

### Fix: Gate `Engagement` FAIL — 3/4
**Action:** Add engagement boxes: `[!tip]`, `[!note]`, `[!cultural]`, `[!myth-buster]`.

### Fix: Gate `Immersion` FAIL — 20.6% LOW (target 45-65% (A2.1))
**⚠ SCOPE WARNING:** Immersion gap is 24% (20.6% → 45% min). This is too large for a fix pass. Focus on the EASIEST wins:
1. Add Ukrainian section headers with English in parentheses
2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
3. Add short Ukrainian phrases with (translations) in existing paragraphs
Do NOT rewrite entire sections. Target +5-8% improvement max.

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "- **Вона мріє стати програмісткою.** — She dreams of becoming a programmer.". Shares significant keywords with sentence at index 44.
**How to fix:** Remove redundant paragraphs. Ensure each section adds new unique value.

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (4 occurrences): (Past role), (Current identity), (Current function) — breaks immersion target
**How to fix:** Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section

### Other Audit Failures

```
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "- **Вона мріє стати програмісткою.** — She dreams of becoming a programmer.". Shares significant keywords with sentence at index 44.
❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (4 occurrences): (Past role), (Current identity), (Current function) — breaks immersion target
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

