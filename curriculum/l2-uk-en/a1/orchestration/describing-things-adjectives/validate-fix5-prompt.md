        # Fix 2 issue(s) in `describing-things-adjectives`

        ### Fix 1: PEDAGOGICAL
**What:** [NO_VERB_CONJUGATION_PRE_M15] 'дає' — Conjugated Ukrainian verb forms should not appear before M15. Students are still learning the alphabet and basic words.
**How to fix:** Replace conjugated verbs with English equivalents or noun phrases. E.g. 'Ми вивчаємо літери' → 'We are learning letters' / 'Вивчення літер'
**Context (line 49):** `Часта помилка — не змінювати закінчення. Словник дає форму чоловічого роду. — A frequent mistake is not changing the ending. The dictionary gives the masculine form.`

### Fix: Gate `Immersion` FAIL — 24.6% LOW (target 25-40% (M11))
**Action:** Add more Ukrainian-language content blocks. Convert some English explanations to Ukrainian with English glosses.

### Other Audit Failures

```
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/describing-things-adjectives-audit.log for details)
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

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/describing-things-adjectives.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/describing-things-adjectives.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

