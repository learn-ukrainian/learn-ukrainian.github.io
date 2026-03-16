        # Fix 6 issue(s) in `vowel-sounds`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Verb 'ка́же' (VESUM: verb:imperf:pres:s:3) in pre-verb module M2. Verbs are forbidden before M15.
**How to fix:** Replace verb 'ка́же' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 224

### Fix 2: LOW_ENGAGEMENT
**What:** Only 0 engagement boxes (minimum: 3 for A1)
**How to fix:** Add 3 more callout boxes (> [!tip], > [!example], > [!cultural-note], etc.)
**Where:** (whole module)

### Fix: Gate `Engagement` FAIL — 0/3
**Action:** Add engagement boxes: `[!tip]`, `[!note]`, `[!cultural]`, `[!myth-buster]`.

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "### Літера Є
**How to fix:** Remove redundant paragraphs. Ensure each section adds new unique value.

### Fix 6: PEDAGOGICAL_VIOLATION
**What:** [SEMANTIC_FALSE_FRIEND] Found 1 semantic false friend(s): 'лук' translated as 'onion' (Ukrainian meaning: bow (weapon), use цибуля instead)
**How to fix:** The word exists in Ukrainian but the English translation uses the Russian meaning. Replace the word or fix the translation to match Ukrainian semantics.

### Other Audit Failures

```
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "### Літера Є
❌ [SEMANTIC_FALSE_FRIEND] Found 1 semantic false friend(s): 'лук' translated as 'onion' (Ukrainian meaning: bow (weapon), use цибуля instead)
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/vowel-sounds-audit.log for details)
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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vowel-sounds.md`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

