        # Fix 20 issue(s) in `the-cyrillic-code-iv`

        ### Fix 1: LLM_FILLER
**Line 27:** `Ду́же до́бре! (Very good!) If you can read those words easily, you are perfectly ready for this final step. In this lesson, we will explain the grammar and mechanics in English, but you will see plenty of real Ukrainian examples to practice with. Почина́ємо! (We are starting!) Let us jump into the final set of letters and complete your alphabet once and for all!`
**Action:** Rephrase to remove "In this lesson, we will". Start the sentence with a concrete fact instead.

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Verb 'ма́ємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'ма́ємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 11

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'мо́жете' (VESUM: verb:imperf:pres:p:2) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'мо́жете' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 11

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Verb 'чита́ти' (VESUM: verb:imperf:inf) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'чита́ти' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 11

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Чита́йте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Чита́йте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 17

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'Почина́ємо' (VESUM: verb:imperf:pres:p:1) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'Почина́ємо' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 27

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Verb 'запам'ята́ти' (VESUM: verb:perf:inf) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'запам'ята́ти' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 35

### Fix 8: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Диві́ться' (VESUM: verb:rev:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Диві́ться' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 37

### Fix 9: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Слу́хайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Слу́хайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 50

### Fix 10: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Диві́ться' (VESUM: verb:rev:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Диві́ться' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 66

### Fix 11: MORPHOLOGICAL_VIOLATION
**What:** Verb 'познача́ють' (VESUM: verb:imperf:pres:p:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'познача́ють' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 75

### Fix 12: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Слу́хайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Слу́хайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 93

### Fix 13: MORPHOLOGICAL_VIOLATION
**What:** Verb 'ма́ють' (VESUM: verb:imperf:pres:p:3) in pre-verb module M4. Verbs are forbidden before M15.
**How to fix:** Replace verb 'ма́ють' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 106

### Fix 14: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Диві́ться' (VESUM: verb:rev:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Диві́ться' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 112

### Fix 15: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Слу́хайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Слу́хайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 125

### Fix 16: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Диві́ться' (VESUM: verb:rev:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Диві́ться' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 138

### Fix 17: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: ДЖ, ДЗ
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** the-cyrillic-code-iv.yaml

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 19: PEDAGOGICAL_VIOLATION
**What:** [ANAGRAM_TOO_SHORT] Anagram 'Unscramble the Words' item 2 has only 2 letter(s): 'е щ'
**How to fix:** Anagram items must have at least 3 letters.

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [VOCAB_NOT_IN_CONTENT] Only 12/20 (60%) vocabulary words appear in content+activities. Missing: кафе, це, центр, щастя, ще, яблуко, їжа, ґанок
**How to fix:** Integrate missing vocabulary words into the prose or activities. Each vocab word should appear at least once in context.

### Other Audit Failures

```
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-cyrillic-code-iv-audit.log for details)
```


## Constraints (do NOT violate while fixing)

DECODABILITY (M4 — full 33-letter alphabet now complete):
- No letter restrictions — all Ukrainian words are decodable after this module.

GRAMMAR BAN (no verbs exist yet):
- NO imperative forms — BANNED. English for instructions.
- NO verb conjugation
- Allowed: bare nouns, noun phrases, Це + noun (preview)

METALANGUAGE: English-first, Ukrainian in parentheses



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-iv.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-iv.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

