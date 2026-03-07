        # Fix 16 issue(s) in `the-cyrillic-code-iii`

        ### Fix 1: LLM_FILLER
**Line 24:** `Excellent job recognizing those shapes! You're ready for the next step. In this lesson, we will learn nine new consonants: **Б**, **Д**, **П**, **З**, **Г**, **Х**, **Ж**, **Ш**, and **Ч**. Since these appear in almost every Ukrainian sentence, mastering them will help you read everyday signs and vocabulary much faster.`
**Action:** Rephrase to remove "In this lesson, we will". Start the sentence with a concrete fact instead.

### Fix 2: LLM_FILLER
**Line 24:** `Excellent job recognizing those shapes! You're ready for the next step. In this lesson, we will learn nine new consonants: **Б**, **Д**, **П**, **З**, **Г**, **Х**, **Ж**, **Ш**, and **Ч**. Since these appear in almost every Ukrainian sentence, mastering them will help you read everyday signs and vocabulary much faster.`
**Action:** Rephrase to remove "In this lesson, we will learn". Start the sentence with a concrete fact instead.

### Fix 3: DECODABILITY
**What:** [DECODABILITY_M3] 'чай' in 'Reading Practice' contains unknown letter(s): й
**How to fix:** Replace words containing unknown letters with words using only А, О, У, М, Л, Н, С, К, И, І, Р, В, Т, Е, Б, Д, П, З, Г, Х, Ж, Ш, Ч. Or move the content to a later module.
**Context (line 214):** `* **ша́пка** (hat)`

### Fix 4: DECODABILITY
**What:** [DECODABILITY_M3] 'ткий' in 'Reading Practice' contains unknown letter(s): й
**How to fix:** Replace words containing unknown letters with words using only А, О, У, М, Л, Н, С, К, И, І, Р, В, Т, Е, Б, Д, П, З, Г, Х, Ж, Ш, Ч. Or move the content to a later module.
**Context (line 216):** ``

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'відчуваєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M3. Verbs are forbidden before M15.
**How to fix:** Replace verb 'відчуваєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 232

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'вимовляєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M3. Verbs are forbidden before M15.
**How to fix:** Replace verb 'вимовляєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 234

### Fix 7: UNTRANSLATED_NON_DECODABLE
**What:** 'відчуваєте' has letters {'Є'} not yet learned (M3)
**How to fix:** Add English translation after the word: відчуваєте (English meaning)
**Where:** ~line 232

### Fix 8: UNTRANSLATED_NON_DECODABLE
**What:** 'вібрацію' has letters {'Ц', 'Ю'} not yet learned (M3)
**How to fix:** Add English translation after the word: вібрацію (English meaning)
**Where:** ~line 232

### Fix 9: UNTRANSLATED_NON_DECODABLE
**What:** 'Яка' has letters {'Я'} not yet learned (M3)
**How to fix:** Add English translation after the word: Яка (English meaning)
**Where:** ~line 233

### Fix 10: UNTRANSLATED_NON_DECODABLE
**What:** 'візуальна' has letters {'Ь'} not yet learned (M3)
**How to fix:** Add English translation after the word: візуальна (English meaning)
**Where:** ~line 233

### Fix 11: UNTRANSLATED_NON_DECODABLE
**What:** 'різниця' has letters {'Ц', 'Я'} not yet learned (M3)
**How to fix:** Add English translation after the word: різниця (English meaning)
**Where:** ~line 233

### Fix 12: UNTRANSLATED_NON_DECODABLE
**What:** 'Як' has letters {'Я'} not yet learned (M3)
**How to fix:** Add English translation after the word: Як (English meaning)
**Where:** ~line 234

### Fix 13: UNTRANSLATED_NON_DECODABLE
**What:** 'вимовляєте' has letters {'Я', 'Є'} not yet learned (M3)
**How to fix:** Add English translation after the word: вимовляєте (English meaning)
**Where:** ~line 234

### Fix: Gate `Density` FAIL — 1 < 6

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 16: PEDAGOGICAL_VIOLATION
**What:** [COMPLEXITY] match-up 'Consonant Pairs' has 6 pairs (target: 8-15)
**How to fix:** Adjust number of pairs to 8-15.

### Other Audit Failures

```
❌ Consonant Pairs
📚 PEDAGOGICAL VIOLATIONS FOUND:
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-cyrillic-code-iii-audit.log for details)
```


## Constraints (do NOT violate while fixing)

DECODABILITY (M3 — 23 known letters: previous 14 + Б Д П З Г Х Ж Ш Ч):
- Nearly all common text is readable now. Reading drills use these 23 letters.
- Still unknown: Й, Щ, Я, Ю, Є, Ь, Ї, Ц, Ф, Ґ + digraphs ДЖ, ДЗ
- Words needing unknown letters require English translation

GRAMMAR BAN (no verbs exist yet):
- NO imperative forms — BANNED. English for instructions.
- NO verb conjugation
- Allowed: bare nouns, noun phrases

METALANGUAGE: English-first, Ukrainian in parentheses



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-iii.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-iii.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-iii.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections
        4. IMMERSION RULE: When fixing issues, preserve the Ukrainian/English ratio. Do NOT replace Ukrainian text with English. If you must rewrite a section, maintain the same percentage of Ukrainian content.

