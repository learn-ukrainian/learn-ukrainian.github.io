        # Fix 2 issue(s) in `imperative-and-requests`

        ### Fix 1: RUSSIANISM
**Found:** `Found 1 Russicism(s) in content: 'давайте подивимося' → подивімося`
**Replace with:** `Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.` (preserve grammatical form)

### Fix 2: PLAN_SECTION_MISSING
**What:** Missing 5 plan section(s): Наказовий спосіб (Imperative mood), Вісім обов'язкових дієслів (Eight required verbs), Ввічливе прохання (Polite requests), Заборони (Prohibitions), Практика (Practice)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/imperative-and-requests-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/imperative-and-requests.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/imperative-and-requests.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/imperative-and-requests.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

