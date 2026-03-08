        # Fix 23 issue(s) in `the-cyrillic-code-iii`

        ### Fix 1: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Подивіться' (VESUM: verb:rev:perf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Подивіться' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 77

### Fix 2: MORPHOLOGICAL_VIOLATION
**What:** Imperative 'Слухайте' (VESUM: verb:imperf:impr:p:2) — imperatives not taught until M47.
**How to fix:** Replace 'Слухайте' with English instruction. E.g., use 'Remember that...' instead of Ukrainian imperatives.
**Where:** ~line 89

### Fix 3: MORPHOLOGICAL_VIOLATION
**What:** Verb 'звучить' (VESUM: verb:imperf:pres:s:3) in pre-verb module M3. Verbs are forbidden before M15.
**How to fix:** Replace verb 'звучить' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 125

### Fix 4: MORPHOLOGICAL_VIOLATION
**What:** Verb 'трима́ти' (VESUM: verb:imperf:inf) in pre-verb module M3. Verbs are forbidden before M15.
**How to fix:** Replace verb 'трима́ти' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 194

### Fix 5: MORPHOLOGICAL_VIOLATION
**What:** Verb 'можете' (VESUM: verb:imperf:pres:p:2) in pre-verb module M3. Verbs are forbidden before M15.
**How to fix:** Replace verb 'можете' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 202

### Fix 6: MORPHOLOGICAL_VIOLATION
**What:** Verb 'відчути' (VESUM: verb:perf:inf) in pre-verb module M3. Verbs are forbidden before M15.
**How to fix:** Replace verb 'відчути' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 202

### Fix 7: MORPHOLOGICAL_VIOLATION
**What:** Verb 'вимовляєте' (VESUM: verb:imperf:pres:p:2) in pre-verb module M3. Verbs are forbidden before M15.
**How to fix:** Replace verb 'вимовляєте' with an English equivalent or a noun phrase. Students haven't learned verbs yet.
**Where:** ~line 204

### Fix 8: AGREEMENT_ERROR
**What:** Agreement mismatch: 'бі́лий' (m) + 'сіль' (f)
**How to fix:** Change 'бі́лий' to match the gender/case of 'сіль', or vice versa.
**Where:** ~line 111

### Fix 9: AGREEMENT_ERROR
**What:** Agreement mismatch: 'те́плий' (m) + 'ша́пка' (f)
**How to fix:** Change 'те́плий' to match the gender/case of 'ша́пка', or vice versa.
**Where:** ~line 146

### Fix 10: UNTRANSLATED_NON_DECODABLE
**What:** 'для' has letters {'Я'} not yet learned (M3)
**How to fix:** Add English translation after the word: для (English meaning)
**Where:** ~line 34

### Fix 11: UNTRANSLATED_NON_DECODABLE
**What:** 'Подивіться' has letters {'Я', 'Ь'} not yet learned (M3)
**How to fix:** Add English translation after the word: Подивіться (English meaning)
**Where:** ~line 77

### Fix 12: UNTRANSLATED_NON_DECODABLE
**What:** 'Слухайте' has letters {'Й'} not yet learned (M3)
**How to fix:** Add English translation after the word: Слухайте (English meaning)
**Where:** ~line 89

### Fix 13: UNTRANSLATED_NON_DECODABLE
**What:** 'Ось' has letters {'Ь'} not yet learned (M3)
**How to fix:** Add English translation after the word: Ось (English meaning)
**Where:** ~line 102

### Fix 14: UNTRANSLATED_NON_DECODABLE
**What:** 'як' has letters {'Я'} not yet learned (M3)
**How to fix:** Add English translation after the word: як (English meaning)
**Where:** ~line 125

### Fix 15: UNTRANSLATED_NON_DECODABLE
**What:** 'звучить' has letters {'Ь'} not yet learned (M3)
**How to fix:** Add English translation after the word: звучить (English meaning)
**Where:** ~line 125

### Fix 16: UNTRANSLATED_NON_DECODABLE
**What:** 'теплий' has letters {'Й'} not yet learned (M3)
**How to fix:** Add English translation after the word: теплий (English meaning)
**Where:** ~line 146

### Fix 17: UNTRANSLATED_NON_DECODABLE
**What:** 'Остання' has letters {'Я'} not yet learned (M3)
**How to fix:** Add English translation after the word: Остання (English meaning)
**Where:** ~line 150

### Fix 18: UNTRANSLATED_NON_DECODABLE
**What:** 'Ф' has letters {'Ф'} not yet learned (M3)
**How to fix:** Add English translation after the word: Ф (English meaning)
**Where:** ~line 165

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix 20: PEDAGOGICAL_VIOLATION
**What:** [CONTENT_REDUNDANCY] Redundant information detected in lesson (74% overlap): "Відео для літери Ш (Video for letter Ш):
**How to fix:** Remove redundant paragraphs. Ensure each section adds new unique value.

### Fix 21: PEDAGOGICAL_VIOLATION
**What:** [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'the letter...'.
**How to fix:** Vary sentence structure.

### Fix 22: PEDAGOGICAL_VIOLATION
**What:** [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (32 occurrences): (This is milk), (There is a cat), (This is a city) — breaks immersion target
**How to fix:** Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section

### Fix 23: PEDAGOGICAL_VIOLATION
**What:** [HINT_IN_ACTIVITY] anagram activity 'Unscramble the Words' has item-level hint in item 1
**How to fix:** Remove all 'hint' fields from activity items (they break activities and provide no real pedagogical value)

### Other Audit Failures

```
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (74% overlap): "Відео для літери Ш (Video for letter Ш):
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'the letter...'.
❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (32 occurrences): (This is milk), (There is a cat), (This is a city) — breaks immersion target
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

