        # Fix 4 issue(s) in `the-cyrillic-code-iii`

        ### Fix 1: UNTRANSLATED_NON_DECODABLE
**What:** 'Ф' has letters {'Ф'} not yet learned (M3)
**How to fix:** Add English translation after the word: Ф (English meaning)
**Where:** ~line 138

### Fix: Gate `Pedagogy` FAIL — 1 violations

### Fix: Gate `Immersion` FAIL — 9.3% LOW (target 10-25% (M03))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Fix 4: PEDAGOGICAL_VIOLATION
**What:** [HINT_IN_ACTIVITY] anagram activity 'Unscramble the Words' has item-level hint in item 1
**How to fix:** Remove all 'hint' fields from activity items (they break activities and provide no real pedagogical value)

### Other Audit Failures

```
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

