        # Fix ALL 15 issue(s) in `colors-and-clothing`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 15 issues. You must produce fixes for all 15.**
        **After you finish, count your fixes. If the count is less than 15, go back and fix the ones you missed.**

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Verb 'означає' (VESUM: verb:imperf:pres:s:3) in pre-verb module M12. Verbs are forbidden before M15.
**How to fix:** Replace verb 'означає' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 5

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Verb 'символізує' (VESUM: verb:imperf:pres:s:3) in pre-verb module M12. Verbs are forbidden before M15.
**How to fix:** Replace verb 'символізує' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 5

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'утворюють' (VESUM: verb:imperf:pres:p:3) in pre-verb module M12. Verbs are forbidden before M15.
**How to fix:** Replace verb 'утворюють' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 5

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Verb 'знаєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M12. Verbs are forbidden before M15.
**How to fix:** Replace verb 'знаєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 218

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'змінюють' (VESUM: verb:imperf:pres:p:3) in pre-verb module M12. Verbs are forbidden before M15.
**How to fix:** Replace verb 'змінюють' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 218

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'люблю' (VESUM: verb:imperf:pres:s:1) in pre-verb module M12. Verbs are forbidden before M15.
**How to fix:** Replace verb 'люблю' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 238

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Червоне' (n) + 'кольори' (p)
**How to fix:** Change 'Червоне' to match the gender/case of 'кольори', or vice versa.
**Where:** ~line 17

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'якої' (f) + 'м' (m/p)
**How to fix:** Change 'якої' to match the gender/case of 'м', or vice versa.
**Where:** ~line 58

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жовтий' (m) + 'жовта' (f)
**How to fix:** Change 'жовтий' to match the gender/case of 'жовта', or vice versa.
**Where:** ~line 60

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жовта' (f) + 'жовте' (n)
**How to fix:** Change 'жовта' to match the gender/case of 'жовте', or vice versa.
**Where:** ~line 60

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'жовте' (n) + 'жовті' (p)
**How to fix:** Change 'жовте' to match the gender/case of 'жовті', or vice versa.
**Where:** ~line 60

### Fix 12: AGREEMENT_ERROR
**What:** Agreement mismatch: 'синій' (f/m) + 'синя' (f)
**How to fix:** Change 'синій' to match the gender/case of 'синя', or vice versa.
**Where:** ~line 61

### Fix 13: AGREEMENT_ERROR
**What:** Agreement mismatch: 'синя' (f) + 'синє' (n)
**How to fix:** Change 'синя' to match the gender/case of 'синє', or vice versa.
**Where:** ~line 61

### Fix 14: AGREEMENT_ERROR
**What:** Agreement mismatch: 'синє' (n) + 'сині' (f/m/p)
**How to fix:** Change 'синє' to match the gender/case of 'сині', or vice versa.
**Where:** ~line 61

### Fix 15: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Синя' (f) + 'синій' (f/m)
**How to fix:** Change 'Синя' to match the gender/case of 'синій', or vice versa.
**Where:** ~line 73

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/colors-and-clothing-audit.log for details)
```


## Constraints (do NOT violate while fixing)

GRAMMAR CONSTRAINTS (A1.1 — First Contact):
Keep grammar simple — this is the learner's first exposure to Ukrainian.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Simple present tense (я читаю, я бачу)
- Basic imperatives (читай, слухай, дивись)
- Question words: «Хто це?», «Що це?», «Де?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга»

BANNED (too complex for first contact):
- Past tense, future tense, conditionals
- Participles, passive voice, gerunds
- Compound/complex sentences — max 1 clause per sentence (no і/а/але joining clauses)
- Do not explicitly teach cases — use nouns in natural contexts

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'
- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')
- Explanatory prose in English, Ukrainian for examples and dialogues




## Immersion Rules

TARGET: 10-20% Ukrainian.

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


## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`

        ## Rules

        1. Fix ALL 15 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

