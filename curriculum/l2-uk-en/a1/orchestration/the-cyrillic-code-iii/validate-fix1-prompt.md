        # Fix 2 issue(s) in `the-cyrillic-code-iii`

        ### Fix 1: LOW_ENGAGEMENT
**What:** Only 0 engagement boxes (minimum: 2 for A1)
**How to fix:** Add 2 more callout boxes (> [!tip], > [!example], > [!cultural-note], etc.)
**Where:** (whole module)

### Fix 2: PLAN_SECTION_MISSING
**What:** Missing 1 plan section(s): Підсумок — Summary
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-iii-audit.log for details)
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

