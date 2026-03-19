        # Fix ALL 18 issue(s) in `mine-and-yours`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 18 issues. You must produce fixes for all 18.**
        **After you finish, count your fixes. If the count is less than 18, go back and fix the ones you missed.**

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'зна́хідок' (genitive, VESUM: noun:inanim:p:v_rod) in M20. Only nominative case allowed before M25.
**How to fix:** Replace 'зна́хідок' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 3

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'їх' (genitive, VESUM: noun:unanim:p:v_rod:pron:pers:3) in M20. Only nominative case allowed before M25.
**How to fix:** Replace 'їх' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 57

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'ма́му' (VESUM: noun:anim:f:v_zna) in M20. Accusative not taught until M25.
**How to fix:** Replace 'ма́му' (accusative) with nominative form or use English equivalent.
**Where:** ~line 63

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'свою́' (VESUM: adj:f:v_zna:pron:pos) in M20. Accusative not taught until M25.
**How to fix:** Replace 'свою́' (accusative) with nominative form or use English equivalent.
**Where:** ~line 64

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'ма́му' (VESUM: noun:anim:f:v_zna) in M20. Accusative not taught until M25.
**How to fix:** Replace 'ма́му' (accusative) with nominative form or use English equivalent.
**Where:** ~line 64

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'зна́хідок' (genitive, VESUM: noun:inanim:p:v_rod) in M20. Only nominative case allowed before M25.
**How to fix:** Replace 'зна́хідок' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 102

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'їх' (genitive, VESUM: noun:unanim:p:v_rod:pron:pers:3) in M20. Only nominative case allowed before M25.
**How to fix:** Replace 'їх' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 124

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'чий' (m) + 'чия́' (f)
**How to fix:** Change 'чий' to match the gender/case of 'чия́', or vice versa.
**Where:** ~line 17

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'ї́хній' (f/m) + 'ї́хня' (f)
**How to fix:** Change 'ї́хній' to match the gender/case of 'ї́хня', or vice versa.
**Where:** ~line 50

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'ї́хня' (f) + 'ї́хнє' (n)
**How to fix:** Change 'ї́хня' to match the gender/case of 'ї́хнє', or vice versa.
**Where:** ~line 50

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'ї́хнє' (n) + 'ї́хні' (p)
**How to fix:** Change 'ї́хнє' to match the gender/case of 'ї́хні', or vice versa.
**Where:** ~line 50

### Fix 12: AGREEMENT_ERROR
**What:** Agreement mismatch: 'чий' (m) + 'зна́хідок' (p)
**How to fix:** Change 'чий' to match the gender/case of 'зна́хідок', or vice versa.
**Where:** ~line 102

### Fix 13: AGREEMENT_ERROR
**What:** Agreement mismatch: 'чия́' (f) + 'чиє́' (n)
**How to fix:** Change 'чия́' to match the gender/case of 'чиє́', or vice versa.
**Where:** ~line 102

### Fix 14: AGREEMENT_ERROR
**What:** Agreement mismatch: 'чиє́' (n) + 'чиї́' (p)
**How to fix:** Change 'чиє́' to match the gender/case of 'чиї́', or vice versa.
**Where:** ~line 102

### Fix 15: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: чиї́ (чиї)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 31

### Fix 16: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: гро́ші (гроші)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 34

### Fix 17: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: її́ (її)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 44

### Fix 18: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: дя́кую (дякую)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 106

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/mine-and-yours-audit.log for details)
```


## Constraints (do NOT violate while fixing)

GRAMMAR CONSTRAINTS (A1.2 — Verbs & Sentences):
Present tense verbs are fully available. Simple sentences.

ALLOWED:
- Present tense (я читаю, він іде, вони мають)
- Basic imperatives (читай/читайте, слухай/слухайте, дивись/дивіться)
- Infinitives in simple contexts (можна читати, треба слухати)
- Simple questions and answers

BANNED (too complex for A1.2):
- Past tense, future tense, conditionals
- Participles, passive voice
- Complex subordinate clauses




## Immersion Rules

TARGET: 15-25% Ukrainian.

**Structural containment**: English prose in paragraphs. Ukrainian in CONTAINERS ONLY (tables, blockquotes, numbered lists, dialogues). Do NOT mix Ukrainian words into English sentences.


## Level Constraints

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M19 likes-and-preferences): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M13), Genitive (basics), Vocative


## Friction Constraints (DO NOT reintroduce)

FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.


## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md`

        ## Rules

        1. Fix ALL 18 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

