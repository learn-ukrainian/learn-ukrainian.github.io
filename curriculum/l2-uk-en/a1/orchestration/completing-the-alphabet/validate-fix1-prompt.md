        # Fix 12 issue(s) in `completing-the-alphabet`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Verb 'показує' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'показує' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 89

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Verb 'позначають' (VESUM: verb:imperf:pres:p:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'позначають' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 89

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'бачу' (VESUM: verb:imperf:pres:s:1:insert) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'бачу' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 198

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Verb 'Дякую' (VESUM: verb:imperf:pres:s:1) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'Дякую' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 208

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Будь' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'Будь' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 209

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'Дякую' (VESUM: verb:imperf:pres:s:1) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'Дякую' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 212

### Fix 7: AGREEMENT_ERROR
**What:** Agreement mismatch: 'приголосний' (m) + 'що' (n)
**How to fix:** Change 'приголосний' to match the gender/case of 'що', or vice versa.
**Where:** ~line 89

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'твердий' (m) + 'апострофом' (m)
**How to fix:** Change 'твердий' to match the gender/case of 'апострофом', or vice versa.
**Where:** ~line 89

### Fix: Gate `Pedagogy` FAIL — 2 violations

### Fix 10: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Instrumental case used at A1: 'перед апострофом'
**How to fix:** Instrumental case not allowed until A2 (M36+). Restructure sentence.

### Fix 11: PEDAGOGICAL_VIOLATION
**What:** [GRAMMAR] Subordinate clause marker at A1: 'є, що п'
**How to fix:** Complex sentences not allowed at A1. Use simple SVO sentences.

### Fix 12: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'in module...'.
**How to fix:** Vary sentence structure.

### Other Audit Failures

```
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'in module...'.
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/completing-the-alphabet-audit.log for details)
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


## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

