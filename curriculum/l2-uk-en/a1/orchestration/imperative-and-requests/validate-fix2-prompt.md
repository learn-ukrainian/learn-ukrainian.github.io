        # Fix 5 issue(s) in `imperative-and-requests`

        ### Fix 1: AGREEMENT_ERROR
**What:** Agreement mismatch: 'ввічливим' (m/n/p) + 'прохання' (n/p)
**How to fix:** Change 'ввічливим' to match the gender/case of 'прохання', or vice versa.
**Where:** ~line 272

### Fix 2: PLAN_SECTION_MISSING
**What:** Missing 5 plan section(s): Наказовий спосіб (Imperative mood), Вісім обов'язкових дієслів (Eight required verbs), Ввічливе прохання (Polite requests), Заборони (Prohibitions), Практика (Practice)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix: Gate `Immersion` FAIL — 30.0% LOW (target 30-55% (M47))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 5: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY_WORD_COUNT] quiz 'Choose correct imperative form in context' Q9 prompt length 4 (target: 5-10)
**How to fix:** Adjust prompt length to 5-10 words.

### Other Audit Failures

```
❌ [MISSING_OUTLINE_SECTION] Section 'Наказовий спосіб (Imperative mood)' defined in outline but not found in markdown.
❌ [MISSING_OUTLINE_SECTION] Section 'Вісім обов'язкових дієслів (Eight required verbs)' defined in outline but not found in markdown.
❌ [MISSING_OUTLINE_SECTION] Section 'Ввічливе прохання (Polite requests)' defined in outline but not found in markdown.
Наказовий спосіб (Imperative mood)                    0 /  300  ❌ (-300)
Вісім обов'язкових дієслів (Eight required verbs)     0 /  300  ❌ (-300)
Ввічливе прохання (Polite requests)                   0 /  250  ❌ (-250)
Заборони (Prohibitions)                               0 /  175  ❌ (-175)
Практика (Practice)                                   0 /  175  ❌ (-175)
TOTAL                                                 0 / 1200  ❌ (-1200)
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/imperative-and-requests-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M47 — Imperative Mood):
This module TEACHES the imperative mood. Imperative forms are ALLOWED and REQUIRED.
Use imperative forms freely: читай/читайте, пиши/пишіть, скажи/скажіть, дай/дайте, іди/ідіть, дивись/дивіться, стій/стійте, слухай/слухайте.

Both imperfective AND perfective verbs are allowed for imperatives.
Past tense and future tense are available (taught at M36/M37).

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental) apply, EXCEPT: perfective aspect is ALLOWED for imperative forms.



## Lexical Sandbox (allowed Ukrainian vocabulary)

This module's verified vocabulary: **я, ти, він, вона, воно, ми, ви, вони, хто, людина, слово, мова, день, час, той, цей, який, читати, писати, сказати, дати, іти, слухати, дивитися, стояти, показати, допомогти, взяти, чекати, це, та, так, ні, не, дуже, тут, там, ось, також, ще, вже, теж, тільки, і, а, але, або, що, як, бо, в, у, на, з, до, для, по, де, коли, чому, DATIVE CASE FORBIDDEN, INSTRUMENTAL CASE FORBIDDEN, Max 10 words per Ukrainian sentence, No subordinate clauses, MANDATORY**

**CRITICAL**: When adding or modifying Ukrainian text, use ONLY words from this list plus basic function words (pronouns, prepositions, conjunctions, numbers). Do NOT introduce new content words not in this sandbox.


## Immersion Rules

TARGET: 30-55% Ukrainian.

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


## Verification Tools (USE THEM)

You have MCP tools for Ukrainian language verification. **Use them before fixing.**

- `verify_words(["word1", "word2"])` — check words exist in VESUM (standard Ukrainian dictionary)
- `verify_lemma("word")` — get all inflected forms of a word

**Before replacing any Ukrainian word:**
1. Call `verify_words` with your replacement to confirm it exists
2. If NOT FOUND, call `verify_lemma` on the base form to find correct inflections
3. Never use a word that returns NOT FOUND — rephrase in English instead


        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/imperative-and-requests.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

