        # Fix 3 issue(s) in `syllables-and-transfer`

        ### Fix 1: UNTRANSLATED_NON_DECODABLE
**What:** 'ґу-дзик' has letters {'Ґ'} not yet learned (M5)
**How to fix:** Add English translation after the word: ґу-дзик (English meaning)
**Where:** ~line 108

### Fix 2: UNTRANSLATED_NON_DECODABLE
**What:** 'ґуд-зик' has letters {'Ґ'} not yet learned (M5)
**How to fix:** Add English translation after the word: ґуд-зик (English meaning)
**Where:** ~line 108

### Fix 3: ACTIVITY_VESUM_FAIL
**What:** Activity answers contain VESUM-failed words: У-кра-ї-на, ав-то-бус, де-ре-во, о-стрів, паль-ці, се-стра, сі-м'я, ґу-дзик
**How to fix:** Fix spelling or replace these words — students will practice non-existent forms.
**Where:** syllables-and-transfer.yaml

### Other Audit Failures

```
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/syllables-and-transfer-audit.log for details)
```


## Constraints (do NOT violate while fixing)

SEQUENCE CONSTRAINTS (M5-10 — Phonology & First Grammar):
Full alphabet known. Modules teach: syllables (M5), stress (M6), gender (M7), greetings (M8), Це/Я/Мене звати (M9), Що це? (M10).

GRAMMAR STATUS:
- AVAILABLE: bare nouns, gender classification, Це + noun, Я + noun, memorized politeness phrases (Дякую, Будь ласка, Вибачте from M8)
- FORBIDDEN: verb conjugation, imperatives, adjective agreement, plurals, all cases except nominative
- Use English for all classroom instructions

METALANGUAGE: English-first, Ukrainian term in parentheses on first use



        ## Files

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/syllables-and-transfer.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/syllables-and-transfer.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/syllables-and-transfer.yaml`

        ## Rules

        1. Fix ONLY the issues listed above — do not rewrite working content
        2. Preserve section structure and word counts
        3. Do NOT add or remove sections

