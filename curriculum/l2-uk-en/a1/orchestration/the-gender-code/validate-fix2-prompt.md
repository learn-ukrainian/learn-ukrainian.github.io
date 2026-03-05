        # Fix 2 issue(s) in `the-gender-code`

        ### Fix 1: LOW_ENGAGEMENT
**What:** Only 0 engagement boxes (minimum: 3 for A1)
**How to fix:** Add 3 more callout boxes (> [!tip], > [!example], > [!cultural-note], etc.)
**Where:** (whole module)

### Fix 2: PLAN_SECTION_MISSING
**What:** Missing 4 plan section(s): Презентація правил (Presentation of Rules), Практичні вправи (Practice Exercises), Самостійна робота (Independent Work/Production), Культурний код та підсумок (Cultural Code and Summary)
**How to fix:** Add content for the missing plan sections or update section headings to match plan.
**Where:** (plan vs content)

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-gender-code-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M5-10 — Phonology & First Grammar):
Full alphabet known. Modules teach: syllables (M5), stress (M6), gender (M7), greetings (M8), Це/Я/Мене звати (M9), Що це? (M10).

GRAMMAR STATUS:
- AVAILABLE: bare nouns, gender classification, Це + noun, Я + noun, memorized politeness phrases (Дякую, Будь ласка, Вибачте from M8)
- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals, all cases except nominative
  Exception (M6 stress): Conjugated verb forms allowed ONLY as stress pattern examples (e.g., писа́ти → пишу́ → пи́шеш to show stress mobility). Do not teach conjugation rules.
  Exception (M7 gender): Adjective agreement examples allowed to demonstrate what gender does (e.g., великий стіл, нова книга, чисте вікно). Do not teach agreement rules.
- BANNED Ukrainian phrases: Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо — always use English equivalents (Let us look at, Let's talk about, Let's review)
- Use English for all classroom instructions

METALANGUAGE: English-first, Ukrainian term in parentheses on first use



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-gender-code.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-gender-code.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-gender-code.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

