        # Fix 18 issue(s) in `being-and-becoming`

        ### Fix 1: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'айтішник' — prefer: айтівець
**How to fix:** Replace 'айтішник' with 'айтівець'
**Where:** ~line 120

### Fix 2: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'айтішниця' — prefer: айтівка
**How to fix:** Replace 'айтішниця' with 'айтівка'
**Where:** ~line 120

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'студенткою' (f)
**How to fix:** Change 'була' to match the gender/case of 'студенткою', or vice versa.
**Where:** ~line 56

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'відомою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'відомою', or vice versa.
**Where:** ~line 66

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'хорошим' (m/n/p) + 'стану' (m)
**How to fix:** Change 'хорошим' to match the gender/case of 'стану', or vice versa.
**Where:** ~line 70

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'минулого' (m/n) + 'юристом' (m)
**How to fix:** Change 'минулого' to match the gender/case of 'юристом', or vice versa.
**Where:** ~line 100

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'хорошим' (m/n/p) + 'став' (m)
**How to fix:** Change 'хорошим' to match the gender/case of 'став', or vice versa.
**Where:** ~line 128

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'інженеркою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'інженеркою', or vice versa.
**Where:** ~line 146

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'хорошою' (f)
**How to fix:** Change 'була' to match the gender/case of 'хорошою', or vice versa.
**Where:** ~line 158

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'відомою' (f)
**How to fix:** Change 'була' to match the gender/case of 'відомою', or vice versa.
**Where:** ~line 172

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'новий' (m) + 'Ви' (p)
**How to fix:** Change 'новий' to match the gender/case of 'Ви', or vice versa.
**Where:** ~line 184

### Fix 12: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'простою' (f/m)
**How to fix:** Change 'була' to match the gender/case of 'простою', or vice versa.
**Where:** ~line 218

### Fix 13: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стала' (f) + 'програмісткою' (f)
**How to fix:** Change 'стала' to match the gender/case of 'програмісткою', or vice versa.
**Where:** ~line 218

### Fix 14: AGREEMENT_ERROR
**What:** Agreement mismatch: 'наступного' (m/n) + 'України' (f)
**How to fix:** Change 'наступного' to match the gender/case of 'України', or vice versa.
**Where:** ~line 218

### Fix 15: AGREEMENT_ERROR
**What:** Agreement mismatch: 'була' (f) + 'лікаркою' (f)
**How to fix:** Change 'була' to match the gender/case of 'лікаркою', or vice versa.
**Where:** ~line 242

### Fix: Gate `Immersion` FAIL — 29.4% LOW (target 45-65% (A2.1))
**⚠ SCOPE WARNING:** Immersion gap is 16% (29.4% → 45% min). This is too large for a fix pass. Focus on the EASIEST wins:
1. Add Ukrainian section headers with English in parentheses
2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
3. Add short Ukrainian phrases with (translations) in existing paragraphs
Do NOT rewrite entire sections. Target +5-8% improvement max.

### Fix 17: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: називний, орудний
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Fix 18: PEDAGOGICAL_VIOLATION
**What:** [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "- **Мій син хоче стати програмістом.** — My son wants to become a programmer.". Shares significant keywords with sentence at index 13.
**How to fix:** Remove redundant paragraphs. Ensure each section adds new unique value.

### Other Audit Failures

```
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "- **Мій син хоче стати програмістом.** — My son wants to become a programmer.". Shares significant keywords with sentence at index 13.
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

