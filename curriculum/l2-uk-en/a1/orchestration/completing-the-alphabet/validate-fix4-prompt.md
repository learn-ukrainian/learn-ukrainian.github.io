        # Fix 12 issue(s) in `completing-the-alphabet`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Verb 'Звучить' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'Звучить' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 137

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Verb 'має' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'має' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 147

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'вимовляєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'вимовляєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 153

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Verb 'створюєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'створюєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 153

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'Вітаємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'Вітаємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 182

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'завершили' (VESUM: verb:perf:past:p) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'завершили' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 187

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Verb 'пом'якшує' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'пом'якшує' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 189

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Verb 'розділяє' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'розділяє' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 190

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Verb 'звучить' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'звучить' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 192

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Verb 'робить' (VESUM: verb:imperf:inf:short) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'робить' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 197

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Verb 'стоїть' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'стоїть' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 198

### Fix 12: MORPHOLOGICAL_VIOLATION
**What:** Verb 'утворюють' (VESUM: verb:imperf:pres:p:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'утворюють' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 199

### Other Audit Failures

```
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

TARGET: 10-25% Ukrainian.

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

