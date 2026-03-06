        # Fix 1 issue(s) in `colors-and-clothing`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'мають' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 113):** `Ці слова завжди мають форму множини.`

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/colors-and-clothing-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M11-14 — Adjectives & Plurals):
Student knows: alphabet, gender, greetings, Це/Я/Мене звати, basic nouns.
Learning: adjective agreement (M11), colors (M12), plurals (M13), checkpoint (M14).

GRAMMAR STATUS:
- AVAILABLE: nouns (nom. sg & pl from M13), adjective+noun agreement (from M11), Це/Я sentences, memorized phrases
- FORBIDDEN: verb conjugation (starts M15), imperatives (M47), cases beyond nominative (accusative starts M25)
- Use English for classroom instructions

METALANGUAGE: English-first, Ukrainian in parentheses



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/colors-and-clothing.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/colors-and-clothing.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

