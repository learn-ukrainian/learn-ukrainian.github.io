        # Fix 12 issue(s) in `being-and-becoming`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'минулий' (m) + 'ролі' (f/m/p)
**How to fix:** Change 'минулий' to match the gender/case of 'ролі', or vice versa.
**Where:** ~line 33

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'називний' (m) + 'часі' (m)
**How to fix:** Change 'називний' to match the gender/case of 'часі', or vice versa.
**Where:** ~line 47

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'минулого' (m/n) + 'форми' (f/p)
**How to fix:** Change 'минулого' to match the gender/case of 'форми', or vice versa.
**Where:** ~line 68

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'майбутнього' (m/n) + 'форми' (f/p)
**How to fix:** Change 'майбутнього' to match the gender/case of 'форми', or vice versa.
**Where:** ~line 68

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'орудний' (m) + 'часу' (m)
**How to fix:** Change 'орудний' to match the gender/case of 'часу', or vice versa.
**Where:** ~line 68

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'чоловічого' (m/n) + 'іменники' (p)
**How to fix:** Change 'чоловічого' to match the gender/case of 'іменники', or vice versa.
**Where:** ~line 88

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жіночого' (m/n) + 'іменники' (p)
**How to fix:** Change 'жіночого' to match the gender/case of 'іменники', or vice versa.
**Where:** ~line 88

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'яку' (f) + 'функція' (f)
**How to fix:** Change 'яку' to match the gender/case of 'функція', or vice versa.
**Where:** ~line 101

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'яку' (f) + 'ви' (p)
**How to fix:** Change 'яку' to match the gender/case of 'ви', or vice versa.
**Where:** ~line 101

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'минулі' (p) + 'робота' (f/m)
**How to fix:** Change 'минулі' to match the gender/case of 'робота', or vice versa.
**Where:** ~line 184

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'нової' (f) + 'громадянин' (m)
**How to fix:** Change 'нової' to match the gender/case of 'громадянин', or vice versa.
**Where:** ~line 194

### Fix: Gate `Immersion` FAIL — 19.6% LOW (target 45-65% (A2.1))
**⚠ SCOPE WARNING:** Immersion gap is 25% (19.6% → 45% min). This is too large for a fix pass. Focus on the EASIEST wins:
1. Add Ukrainian section headers with English in parentheses
2. Add 'Наприклад:' / 'Порівняйте:' before example blocks
3. Add short Ukrainian phrases with (translations) in existing paragraphs
Do NOT rewrite entire sections. Target +5-8% improvement max.

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
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/being-and-becoming.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/being-and-becoming.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

