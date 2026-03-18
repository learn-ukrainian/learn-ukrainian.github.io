        # Fix ALL 15 issue(s) in `greetings-and-politeness`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 15 issues. You must produce fixes for all 15.**
        **After you finish, count your fixes. If the count is less than 15, go back and fix the ones you missed.**

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Бувай' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'Бувай' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 23

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Бувайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Бувайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 24

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Давай' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'Давай' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 52

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Verb 'просимо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'просимо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 100

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'звати' (VESUM: verb:imperf:inf) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'звати' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 133

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'звати' (VESUM: verb:imperf:inf) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'звати' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 134

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Verb 'познайомитись' (VESUM: verb:rev:perf:inf) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'познайомитись' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 146

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Verb 'звати' (VESUM: verb:imperf:inf) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'звати' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 150

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Verb 'звати' (VESUM: verb:imperf:inf) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'звати' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 157

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Verb 'познайомитись' (VESUM: verb:rev:perf:inf) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'познайомитись' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 175

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Verb 'просимо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M8. Verbs are forbidden before M15.
**How to fix:** Replace verb 'просимо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 175

### Fix 12: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Бувай' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'Бувай' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 188

### Fix 13: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Бувай' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'Бувай' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 189

### Fix 14: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Бувай' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'Бувай' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 191

### Fix 15: AGREEMENT_ERROR
**What:** Agreement mismatch: 'Добрий' (m) + 'Ви' (p)
**How to fix:** Change 'Добрий' to match the gender/case of 'Ви', or vice versa.
**Where:** ~line 179

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/greetings-and-politeness-audit.log for details)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Perfective aspect (plan teaches perfective verbs). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.


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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/greetings-and-politeness.md`

        ## Rules

        1. Fix ALL 15 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

