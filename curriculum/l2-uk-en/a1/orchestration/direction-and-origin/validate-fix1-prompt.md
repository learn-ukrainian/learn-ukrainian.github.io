        # Fix ALL 5 issue(s) in `direction-and-origin`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 5 issues. You must produce fixes for all 5.**
        **After you finish, count your fixes. If the count is less than 5, go back and fix the ones you missed.**

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [Watch on YouTube]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 169

### Fix 2: AGREEMENT_ERROR
**What:** Agreement mismatch: 'родовий' (m) + 'до' (n/p)
**How to fix:** Change 'родовий' to match the gender/case of 'до', or vice versa.
**Where:** ~line 55

### Fix 3: AGREEMENT_ERROR
**What:** Agreement mismatch: 'друга' (f) + 'до' (n/p)
**How to fix:** Change 'друга' to match the gender/case of 'до', or vice versa.
**Where:** ~line 61

### Fix 4: AGREEMENT_ERROR
**What:** Agreement mismatch: 'друга' (f) + 'до' (n/p)
**How to fix:** Change 'друга' to match the gender/case of 'до', or vice versa.
**Where:** ~line 82

### Fix 5: LOW_ENGAGEMENT
**What:** Only 0 engagement boxes (minimum: 3 for A1)
**How to fix:** Add 3 more callout boxes (> [!tip], > [!example], > [!cultural-note], etc.)
**Where:** (whole module)

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/direction-and-origin-audit.log for details)
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


## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/direction-and-origin.md`

        ## Rules

        1. Fix ALL 5 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

