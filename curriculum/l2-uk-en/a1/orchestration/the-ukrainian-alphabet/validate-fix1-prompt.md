        # Fix 16 issue(s) in `the-ukrainian-alphabet`

        ### Fix 1: DECODABILITY
**What:** [DECODABILITY_M1] 'Це' in 'First Words' contains unknown letter(s): Ц, е
**How to fix:** Replace words containing unknown letters with words using only А, О, У, І, М, Н, Т, К, С, Л. Or move the content to a later module.
**Context (line 130):** ``

### Fix 2: UNTRANSLATED_NON_DECODABLE
**What:** 'Е' has letters {'Е'} not yet learned (M1)
**How to fix:** Add English translation after the word: Е (English meaning)
**Where:** ~line 59

### Fix 3: UNTRANSLATED_NON_DECODABLE
**What:** 'И' has letters {'И'} not yet learned (M1)
**How to fix:** Add English translation after the word: И (English meaning)
**Where:** ~line 59

### Fix 4: UNTRANSLATED_NON_DECODABLE
**What:** 'Я' has letters {'Я'} not yet learned (M1)
**How to fix:** Add English translation after the word: Я (English meaning)
**Where:** ~line 59

### Fix 5: UNTRANSLATED_NON_DECODABLE
**What:** 'Ю' has letters {'Ю'} not yet learned (M1)
**How to fix:** Add English translation after the word: Ю (English meaning)
**Where:** ~line 59

### Fix 6: UNTRANSLATED_NON_DECODABLE
**What:** 'Є' has letters {'Є'} not yet learned (M1)
**How to fix:** Add English translation after the word: Є (English meaning)
**Where:** ~line 59

### Fix 7: UNTRANSLATED_NON_DECODABLE
**What:** 'Ї' has letters {'Ї'} not yet learned (M1)
**How to fix:** Add English translation after the word: Ї (English meaning)
**Where:** ~line 59

### Fix 8: UNTRANSLATED_NON_DECODABLE
**What:** 'Б' has letters {'Б'} not yet learned (M1)
**How to fix:** Add English translation after the word: Б (English meaning)
**Where:** ~line 60

### Fix 9: UNTRANSLATED_NON_DECODABLE
**What:** 'В' has letters {'В'} not yet learned (M1)
**How to fix:** Add English translation after the word: В (English meaning)
**Where:** ~line 60

### Fix 10: UNTRANSLATED_NON_DECODABLE
**What:** 'Г' has letters {'Г'} not yet learned (M1)
**How to fix:** Add English translation after the word: Г (English meaning)
**Where:** ~line 60

### Fix 11: UNTRANSLATED_NON_DECODABLE
**What:** 'Ґ' has letters {'Ґ'} not yet learned (M1)
**How to fix:** Add English translation after the word: Ґ (English meaning)
**Where:** ~line 60

### Fix 12: UNTRANSLATED_NON_DECODABLE
**What:** 'Д' has letters {'Д'} not yet learned (M1)
**How to fix:** Add English translation after the word: Д (English meaning)
**Where:** ~line 60

### Fix 13: UNTRANSLATED_NON_DECODABLE
**What:** 'Ж' has letters {'Ж'} not yet learned (M1)
**How to fix:** Add English translation after the word: Ж (English meaning)
**Where:** ~line 60

### Fix 14: UNTRANSLATED_NON_DECODABLE
**What:** 'З' has letters {'З'} not yet learned (M1)
**How to fix:** Add English translation after the word: З (English meaning)
**Where:** ~line 60

### Fix 15: UNTRANSLATED_NON_DECODABLE
**What:** 'Й' has letters {'Й'} not yet learned (M1)
**How to fix:** Add English translation after the word: Й (English meaning)
**Where:** ~line 60

### Fix 16: UNTRANSLATED_NON_DECODABLE
**What:** 'П' has letters {'П'} not yet learned (M1)
**How to fix:** Add English translation after the word: П (English meaning)
**Where:** ~line 60

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-ukrainian-alphabet-audit.log for details)
```


## Constraints (do NOT violate while fixing)

GRAMMAR BAN (pre-verbal phase — no verbs exist yet):
- NO imperative forms: Слухайте, Читайте, Повторюйте, Пишіть, Дивіться — ALL BANNED
- NO verb conjugation of any kind (present, past, future)
- Classroom instructions MUST be in English: 'Listen carefully', 'Read aloud', 'Repeat'
- Allowed Ukrainian structures: bare nouns, noun phrases, Це + noun

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'
- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')
- NEVER write Ukrainian-only explanatory prose

VERB-FREE UKRAINIAN PATTERN BANK:
- Це + noun: «Це кіт», «Це стіл»
- Question particles: «Хто це?», «Що це?»
- Adj + noun: «великий дім», «нова книга»
- Contextual labels: «Наприклад — For example», «А тепер — And now»
DO NOT use conjugated verbs, imperatives, or infinitives.


DECODABLE VOCABULARY (only letters: І, А, К, Л, М, Н, О, С, Т, У):
Use ONLY these words in reading drills and prose examples.
Any word with a letter outside this set will FAIL the decodability audit gate.
Sight words from the plan are exempt — they are recognized as whole shapes,
not decoded letter-by-letter. Label them clearly.
Video pronunciation examples are also exempt (heard, not read).

Available decodable words: мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні, сон, сом, ніс, мак, сік, стіл, тут, там, лук, кіно

If you need a word not on this list, check that ALL its letters are in the
allowed set above. Words with unknown letters need English translation.



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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-ukrainian-alphabet.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-ukrainian-alphabet.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

