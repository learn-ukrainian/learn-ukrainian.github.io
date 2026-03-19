        # Fix ALL 13 issue(s) in `checkpoint-daily-life`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 13 issues. You must produce fixes for all 13.**
        **After you finish, count your fixes. If the count is less than 13, go back and fix the ones you missed.**

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Пам'ятай' (VESUM: verb:imperf:impr:s:2) — imperatives not taught until M47.
**How to fix:** Replace 'Пам'ятай' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 40

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Да́йте' (VESUM: verb:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Да́йте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 76

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'гаря́чий' (m) + 'пив' (p)
**How to fix:** Change 'гаря́чий' to match the gender/case of 'пив', or vice versa.
**Where:** ~line 119

### Fix 4: STRESS_MISMATCH
**What:** Wrong stress: 'піде́ш' → should be 'пі́деш'
**How to fix:** Replace 'піде́ш' with 'пі́деш'.
**Where:** ~line 50

### Fix 5: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: робо́ти (роботи)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 53

### Fix 6: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: обі́д (обід)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 70

### Fix 7: STRESS_MISMATCH
**What:** Wrong stress: 'ко́штує' → should be 'ко́шту́є'
**How to fix:** Replace 'ко́штує' with 'ко́шту́є'.
**Where:** ~line 72

### Fix 8: STRESS_MISMATCH
**What:** Wrong stress: 'ко́штувати' → should be 'ко́штува́ти'
**How to fix:** Replace 'ко́штувати' with 'ко́штува́ти'.
**Where:** ~line 72

### Fix 9: STRESS_MISMATCH
**What:** Wrong stress: 'хочу́' → should be 'хо́чу'
**How to fix:** Replace 'хочу́' with 'хо́чу'.
**Where:** ~line 74

### Fix 10: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: дя́кую (дякую)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 78

### Fix 11: STRESS_MISMATCH
**What:** Wrong stress: 'говори́ш' → should be 'гово́риш'
**How to fix:** Replace 'говори́ш' with 'гово́риш'.
**Where:** ~line 91

### Fix 12: STRESS_MISMATCH
**What:** Wrong stress: 'те́пло' → should be 'тепло́'
**How to fix:** Replace 'те́пло' with 'тепло́'.
**Where:** ~line 96

### Fix 13: STRESS_UNKNOWN
**What:** Stressed word not in dictionary: па́рку (парку)
**How to fix:** Verify stress manually — word not found in ukrainian-word-stress dictionary.
**Where:** ~line 132

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/checkpoint-daily-life-audit.log for details)
```


## Constraints (do NOT violate while fixing)

GRAMMAR CONSTRAINTS (A1.4 — Tenses & Daily Life):
Past tense and future tense introduced. All present tense available.
Imperatives available.

BANNED: participles, passive voice, complex subordination




## Immersion Rules

TARGET: 20-35% Ukrainian.

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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-daily-life.md`

        ## Rules

        1. Fix ALL 13 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

