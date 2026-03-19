        # Fix ALL 12 issue(s) in `questions-and-negation`

        **CRITICAL: You MUST fix every issue below. Partial fixes are REJECTED.**
        **There are 12 issues. You must produce fixes for all 12.**
        **After you finish, count your fixes. If the count is less than 12, go back and fix the ones you missed.**

        ### Fix 1: IPA_BANNED
**What:** Banned IPA transcription: [sentence 1]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 119

### Fix 2: IPA_BANNED
**What:** Banned IPA transcription: [conjunction]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 119

### Fix 3: IPA_BANNED
**What:** Banned IPA transcription: [sentence 2]
**How to fix:** Remove phonetic brackets. Use only stress marks (´) for pronunciation.
**Where:** ~line 119

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M18. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 29

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M18. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 105

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M18. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 121

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M18. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 122

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Accusative 'каву' (VESUM: noun:inanim:f:v_zna) in M18. Accusative not taught until M25.
**How to fix:** Replace 'каву' (accusative) with nominative form or use English equivalent.
**Where:** ~line 123

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Non-present verb 'прийшов' (past tense, VESUM: verb:perf:past:m) in M18. Only present tense available before M36.
**How to fix:** Replace 'прийшов' with present tense form or English.
**Where:** ~line 128

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'котів' (genitive, VESUM: noun:anim:p:v_rod) in M18. Only nominative case allowed before M25.
**How to fix:** Replace 'котів' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 138

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Non-nominative 'їх' (genitive, VESUM: noun:unanim:p:v_rod:pron:pers:3) in M18. Only nominative case allowed before M25.
**How to fix:** Replace 'їх' (genitive) with its nominative form or use English equivalent.
**Where:** ~line 138

### Fix 12: LOW_ENGAGEMENT
**What:** Only 0 engagement boxes (minimum: 1 for A1)
**How to fix:** Add 1 more callout boxes (> [!tip], > [!example], > [!cultural-note], etc.)
**Where:** (whole module)

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/questions-and-negation-audit.log for details)
```


## Constraints (do NOT violate while fixing)

GRAMMAR CONSTRAINTS (A1.2 — Verbs & Sentences):
Present tense verbs are fully available. Simple sentences.

ALLOWED:
- Present tense (я читаю, він іде, вони мають)
- Basic imperatives (читай/читайте, слухай/слухайте, дивись/дивіться)
- Infinitives in simple contexts (можна читати, треба слухати)
- Simple questions and answers

BANNED (too complex for A1.2):
- Past tense, future tense, conditionals
- Participles, passive voice
- Complex subordinate clauses




## Immersion Rules

TARGET: 15-25% Ukrainian.

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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`

        ## Rules

        1. Fix ALL 12 issues listed above — every single one, not a subset
        2. Do not rewrite working content — only touch what's broken
        3. Preserve section structure and word counts
        4. Do NOT add or remove sections
        5. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

