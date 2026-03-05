        # Fix 4 issue(s) in `the-cyrillic-code-iv`

        ### Fix 1: UNTRANSLATED_NON_DECODABLE
**What:** 'Ц' has letters {'Ц'} not yet learned (M4)
**How to fix:** Add English translation after the word: Ц (English meaning)
**Where:** ~line 33

### Fix 2: UNTRANSLATED_NON_DECODABLE
**What:** 'Ґ' has letters {'Ґ'} not yet learned (M4)
**How to fix:** Add English translation after the word: Ґ (English meaning)
**Where:** ~line 71

### Fix 3: UNTRANSLATED_NON_DECODABLE
**What:** 'Ь' has letters {'Ь'} not yet learned (M4)
**How to fix:** Add English translation after the word: Ь (English meaning)
**Where:** ~line 138

### Fix 4: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: Європа, Львів
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** the-cyrillic-code-iv.yaml

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-iv-audit.log for details)
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

