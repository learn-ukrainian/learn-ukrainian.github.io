        # Fix ALL 14 issue(s) in `plurals-and-alternation`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 14 issues. You must produce fixes for all 14.**
        **After you finish, count your fixes. If the count is less than 14, go back and fix the ones you missed.**

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'нови́й' (m) + 'нові́' (p)
**How to fix:** Change 'нови́й' to match the gender/case of 'нові́', or vice versa.
**Where:** ~line 113

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'нова́' (f) + 'нові́' (p)
**How to fix:** Change 'нова́' to match the gender/case of 'нові́', or vice versa.
**Where:** ~line 114

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'нове́' (n) + 'нові́' (p)
**How to fix:** Change 'нове́' to match the gender/case of 'нові́', or vice versa.
**Where:** ~line 115

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'вели́кий' (m) + 'вели́кі' (p)
**How to fix:** Change 'вели́кий' to match the gender/case of 'вели́кі', or vice versa.
**Where:** ~line 116

### Fix 5: AGREEMENT_ERROR
**What:** Agreement mismatch: 'вели́ка' (f) + 'вели́кі' (p)
**How to fix:** Change 'вели́ка' to match the gender/case of 'вели́кі', or vice versa.
**Where:** ~line 117

### Fix 6: AGREEMENT_ERROR
**What:** Agreement mismatch: 'вели́ке' (n) + 'вели́кі' (p)
**How to fix:** Change 'вели́ке' to match the gender/case of 'вели́кі', or vice versa.
**Where:** ~line 118

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стари́й' (m) + 'старі́' (p)
**How to fix:** Change 'стари́й' to match the gender/case of 'старі́', or vice versa.
**Where:** ~line 119

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'стара́' (f) + 'старі́' (p)
**How to fix:** Change 'стара́' to match the gender/case of 'старі́', or vice versa.
**Where:** ~line 120

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'старе́' (n) + 'старі́' (p)
**How to fix:** Change 'старе́' to match the gender/case of 'старі́', or vice versa.
**Where:** ~line 121

### Fix 10: AGREEMENT_ERROR
**What:** Agreement mismatch: 'си́ня' (f) + 'си́ні' (f/m/p)
**How to fix:** Change 'си́ня' to match the gender/case of 'си́ні', or vice versa.
**Where:** ~line 128

### Fix 11: AGREEMENT_ERROR
**What:** Agreement mismatch: 'си́нє' (n) + 'си́ні' (f/m/p)
**How to fix:** Change 'си́нє' to match the gender/case of 'си́ні', or vice versa.
**Where:** ~line 129

### Fix 12: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: дітині, кіти, ножицю, ножиця, ножиціі, ніжі, пічі, стіли, хлопце, хлопци
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** plurals-and-alternation.yaml

### Fix 13: PEDAGOGICAL_VIOLATION
**What:** [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина
**How to fix:** Add these grammar terms to vocabulary with translations, or use English equivalents.

### Fix 14: PEDAGOGICAL_VIOLATION
**What:** [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (Noun plurals), (Adjective plurals), (Exceptions and special cases) — breaks immersion target
**How to fix:** Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section

### Other Audit Failures

```
❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (Noun plurals), (Adjective plurals), (Exceptions and special cases) — breaks immersion target
📚 PEDAGOGICAL VIOLATIONS FOUND:
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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/plurals-and-alternation.md`

        ## Rules

        1. Fix ALL 14 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

