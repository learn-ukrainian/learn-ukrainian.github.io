        # Fix ALL 10 issue(s) in `syllables-and-word-division`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 10 issues. You must produce fixes for all 10.**
        **After you finish, count your fixes. If the count is less than 10, go back and fix the ones you missed.**

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Verb 'стрів' (VESUM: verb:perf:past:m) in pre-verb module M5. Verbs are forbidden before M15.
**How to fix:** Replace verb 'стрів' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 58

### Fix 2: RUSSICISM_OR_NONSTANDARD
**What:** Non-standard form 'перено́с' — prefer: перенесення
**How to fix:** Replace 'перено́с' with 'перенесення'
**Where:** ~line 60

### Fix 3: STRESS_MISMATCH
**What:** Wrong stress: 'приголо́сний' → should be 'при́голосний'
**How to fix:** Replace 'приголо́сний' with 'при́голосний'.
**Where:** ~line 20

### Fix 4: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: ї́на (їна)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 80

### Fix 5: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: Украї́ (украї)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 81

### Fix 6: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: ніверсите́т (ніверситет)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 97

### Fix 7: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: бліоте́ка (бліотека)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 105

### Fix 8: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: оте́ка (отека)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 106

### Fix 9: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: бібліоте́ (бібліоте)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 108

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'therefore, it...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'therefore, it...'.
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

TARGET: 5-15% Ukrainian.

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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/syllables-and-word-division.md`

        ## Rules

        1. Fix ALL 10 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

