        # Fix 19 issue(s) in `completing-the-alphabet`

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [First Contact]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 11

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Verb 'Завершуємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'Завершуємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 8

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'пройшли' (VESUM: verb:perf:past:p) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'пройшли' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 23

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Verb 'вивчите' (VESUM: verb:perf:futr:p:2) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'вивчите' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 25

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'зможете' (VESUM: verb:perf:futr:p:2) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'зможете' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 27

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'прочитати' (VESUM: verb:perf:inf) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'прочитати' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 27

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Уявіть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Уявіть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 33

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Verb 'бачите' (VESUM: verb:imperf:pres:p:2:insert) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'бачите' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 33

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Зверніть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Зверніть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 44

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Verb 'знаєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'знаєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 47

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Спробуйте' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Спробуйте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 47

### Fix 12: MORPHOLOGICAL_VIOLATION
**What:** Verb 'вимовити' (VESUM: verb:perf:inf) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'вимовити' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 47

### Fix 13: MORPHOLOGICAL_VIOLATION
**What:** Verb 'пишеться' (VESUM: verb:rev:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'пишеться' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 73

### Fix 14: MORPHOLOGICAL_VIOLATION
**What:** Verb 'стоїть' (VESUM: verb:imperf:pres:s:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'стоїть' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 73

### Fix 15: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Зверніть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Зверніть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 85

### Fix 16: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Почніть' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Почніть' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 93

### Fix 17: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: ДЖ, ДЗ, нок, поб, спр, чення
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** completing-the-alphabet.yaml

### Fix: Gate `Immersion` FAIL — 25.8% HIGH (target 10-25% (M04))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [CONTENT_REDUNDANCY] Redundant information detected in lesson (71% overlap): "<iframe style="aspect-ratio: 16/9; width: 100%;" src="https://www.youtube.com/embed/QmBLieIuf6Q" tit...". Shares significant keywords with sentence at index 33.
**How to fix:** Remove redundant paragraphs. Ensure each section adds new unique value.

### Other Audit Failures

```
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (71% overlap): "<iframe style="aspect-ratio: 16/9; width: 100%;" src="https://www.youtube.com/embed/QmBLieIuf6Q" tit...". Shares significant keywords with sentence at index 33.
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

