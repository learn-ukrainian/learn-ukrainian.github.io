# B1 M01-M05 Activity Fix List

**Generated:** 2025-12-25
**Target:** A2 complexity for B1 bridge modules (M01-M05)

---

## Match-up Issues (All Modules)

All modules have match-ups with 13 pairs. A2 limit is 10-12 pairs.

**Fix:** Remove 1-3 pairs from each match-up to bring to 10-12 range.

| Module | Match-up Title | Current | Target |
|--------|----------------|---------|--------|
| M01 | Частини мови | 13 | 10-12 |
| M01 | Відмінки та категорії | 13 | 10-12 |
| M02 | Терміни виду | 13 | 10-12 |
| M02 | Терміни часу та способу | 13 | 10-12 |
| M03 | Пояснювальні конструкції | 13 | 10-12 |
| M03 | Словотвір і порівняння | 13 | 10-12 |
| M04 | Члени речення | 13 | 10-12 |
| M04 | Синтаксис і пунктуація | 13 | 10-12 |
| M05 | Комплексний огляд — Частини мови | 13 | 10-12 |
| M05 | Комплексний огляд — Відмінки і речення | 13 | 10-12 |

---

## Unjumble Issues

## Instructions for AI Agent

For each unjumble item listed below:

1. **WORD COUNT issues (13-15 words → 8-10 words):**
   - Simplify the sentence while keeping the core meaning
   - Split into two shorter sentences if needed
   - Remove redundant words
   - Use simpler syntax

2. **WORD MISMATCH issues (unsolvable):**
   - Ensure jumbled words EXACTLY match answer words
   - Check for duplicates (word appears twice in answer but once in jumbled)
   - Check for form mismatches (дія vs дії)

3. **CONSISTENCY:**
   - Similar content types should use similar sentence structures
   - E.g., all case descriptions should follow the same pattern

---

## M01: 01-how-to-talk-about-grammar.md

### Activity: `## unjumble: Граматичні терміни`

**WORD COUNT issues (rewrite to 8-10 words):**
- Item 3: 13 words → simplify
- Item 5: 13 words → simplify
- Item 10: 14 words → simplify
- Item 11: 14 words → simplify
- Item 12: 13 words → simplify
- Item 14: 13 words → simplify

**WORD MISMATCH issues (fix jumbled/answer alignment):**
- Item 1: answer has "поняття" twice, jumbled has it once → remove duplicate from answer OR add to jumbled
- Item 5: jumbled has extra "слова" not in answer → remove from jumbled OR add to answer
- Item 7: jumbled has "дії", answer has "дія" → use same form in both

**STRUCTURE CONSISTENCY issue:**
- Items 2 and 10 describe grammatical cases but use different sentence structures
- Standardize: `[Case] — [ordinal] відмінок, відповідає на питання [X, Y], позначає/показує [function]`

---

## M02: 02-language-about-verbs.md

### Activity: `## unjumble: Граматичні пояснення`

**WORD COUNT issues (rewrite to 8-10 words):**
- Item 3: 14 words → simplify
- Item 5: 13 words → simplify

**WORD MISMATCH issues:**
- Item 9: jumbled has extra "би" not in answer → remove from jumbled OR add to answer

---

## M03: 03-reading-grammar-rules.md

### Activity: `## unjumble: Граматичні пояснення`

**WORD COUNT issues (rewrite to 8-10 words):**
- Item 2: 13 words → simplify
- Item 6: 15 words → simplify (worst offender!)
- Item 11: 13 words → simplify
- Item 14: 14 words → simplify

---

## M04: 04-sentence-structure-terms.md

### Activity: `## unjumble: Синтаксичні пояснення`

**WORD COUNT issues (rewrite to 8-10 words):**
- Item 1: 14 words → simplify
- Item 2: 13 words → simplify
- Item 5: 14 words → simplify
- Item 6: 13 words → simplify
- Item 12: 13 words → simplify

---

## M05: 05-full-immersion-checkpoint.md

No unjumble issues found.

---

## Example Rewrites

**Before (13 words):**
```
прислівник / опису / для / швидко / дії / означає / як / відбувається / добре / тут / там / наприклад
> [!answer] Прислівник означає, як відбувається дія, для опису: швидко, добре, тут, там, наприклад.
```

**After (9 words):**
```
прислівник / означає / як / відбувається / дія / наприклад / швидко
> [!answer] Прислівник означає, як відбувається дія, наприклад швидко.
```

**Pattern for case descriptions (consistent structure):**
```
[Case] — [ordinal] відмінок, відповідає на питання [X, Y].
```
Example:
```
давальний / третій / відмінок / відповідає / на / питання / кому / чому
> [!answer] Давальний — третій відмінок, відповідає на питання кому, чому.
```

---

## Verification

After fixing, run:
```bash
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/01-*.md
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/02-*.md
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/03-*.md
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/04-*.md
```

All `UNJUMBLE_WORD_MISMATCH` and `COMPLEXITY_WORD_COUNT` for unjumble should be gone.
