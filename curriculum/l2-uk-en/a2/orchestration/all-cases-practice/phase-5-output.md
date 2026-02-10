===REVIEW_START===
# Рецензія: All Cases Practice

**Level:** A2 | **Module:** 09
**Overall Score:** 6.9/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Most required terms present; 'хто/що' implicit in tables]
- Grammar scope: [Mostly A2, but 'три предметів' violates 2,3,4 rule]
- Objectives: [Covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 6/10 | <7 | Broken activity item (dangling preposition) causes frustration. |
| 2 | Coherence | 8/10 | <7 | Logical flow is good. |
| 3 | Relevance | 9/10 | <7 | Highly relevant topic. |
| 4 | Educational | 7/10 | <7 | Good explanations, but undermined by grammar errors. |
| 5 | Language | 7/10 | <8 | Critical grammar error "три предметів"; unnatural "кошти". |
| 6 | Pedagogy | 7/10 | <7 | Good PPP structure, but review exercises must be flawless. |
| 7 | Immersion | 8/10 | <6 | Appropriate English/Ukrainian balance for complex grammar. |
| 8 | Activities | 5/10 | <7 | Unjumble item is broken/nonsensical; vague instructions. |
| 9 | Richness | 8/10 | <6 | Good use of tables and dialogue. |
| 10 | Beginner Safety | 6/10 | <7 | Teaching incorrect grammar (2,3,4 rule) is unsafe. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural voice. |
| 12 | Linguistic Accuracy | 6/10 | <9 | Fails on basic numeracy grammar. |

**Weighted Overall:** (6*1.5 + 8 + 9 + 7*1.2 + 7*1.1 + 7*1.2 + 8 + 5*1.3 + 8*0.9 + 6*1.3 + 8 + 6*1.5) / 14.0 = **6.9/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [Error in "Need More Practice"]
- Activity errors: [Unjumble item 2 is broken; Mark-words instruction missing]
- Beginner safety: 6/5 (Fail due to grammar error)

## Critical Issues Found

### Issue 1: Critical Grammar Error (Numerals)
- **Location**: Section "Need More Practice?" / Last paragraph
- **Original**: "Оберіть три предметів в кімнаті"
- **Problem**: The numerals 2, 3, 4 govern the Nominative Plural (sometimes Genitive Singular form historically, but functionally Nom Pl/Gen Sg form), NOT the Genitive Plural. "Три предметів" is grammatically incorrect. It should be "три предмети". Genitive Plural is for 5+.
- **Fix**: "Оберіть три предмети в кімнаті"

### Issue 2: Broken Activity Item (Unjumble)
- **Location**: Activity `unjumble` / Item 2
- **Original**: Answer: "Книга лежить на столі вже давно тут у"
- **Problem**: The sentence ends with a preposition "у" with no object. It is nonsensical.
- **Fix**: Remove "у" from the word list and answer, or complete the phrase (e.g., "у кімнаті"). Given the other words, just removing "у" is best.

### Issue 3: Unnatural Vocabulary (Register)
- **Location**: Dialogues / "Зустріч друзів"
- **Original**: "У мене є кошти на обід."
- **Problem**: "Кошти" (funds) is too formal/administrative for a casual chat between friends. It sounds like a corporate budget allocation.
- **Fix**: "У мене є гроші на обід." or simply "Маю гроші на обід."

### Issue 4: Vague Activity Instructions
- **Location**: Activity `mark-the-words`
- **Original**: "instruction: Клацніть на слова, що відповідають критерію."
- **Problem**: The "criterion" is never defined for the user. They don't know if they should click nouns, verbs, or specific cases. Based on the answers, it seems to be "oblique cases" (non-Nominative).
- **Fix**: Change instruction to: "Знайдіть і виділіть усі іменники, що стоять НЕ в називному відмінку (find nouns in oblique cases)."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Text | три предметів | три предмети | Grammar Error |
| Dial | кошти на обід | гроші на обід | Unnatural Register |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? No
- Instructions clear? No (Mark-the-words is guessing game)
- Quick wins? Yes
- Ukrainian scary? No
- Come back tomorrow? Maybe, but "три предметів" might confuse me if I learned the rule elsewhere.

## Fix Plan to Reach 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Section "Need More Practice?": Change "три предметів" → "три предмети" — fixes basic grammar error.
2. Section "Dialogues": Change "кошти на обід" → "гроші на обід" — improves naturalness.

### Activities: 5/10 → 9/10
**What to fix:**
1. YAML `unjumble` item 2: Remove "у" from `words` list and `answer`. New answer: "Книга лежить на столі вже давно тут".
2. YAML `mark-the-words`: Change `instruction` from "Клацніть на слова, що відповідають критерію." to "Знайдіть слова, що стоять у непрямих відмінках (не в називному)." (Find words in oblique cases).

### Linguistic Accuracy: 6/10 → 10/10
**What to fix:**
1. The fix for "три предметів" resolves the primary accuracy failure.

### Projected Overall After Fixes

(7*1.5 + 8 + 9 + 8*1.2 + 9*1.1 + 8*1.2 + 8 + 9*1.3 + 8*0.9 + 8*1.3 + 8 + 10*1.5) / 14.0 = **9.1/10**

## Verdict

**FAIL**

The module contains a critical grammar error ("три предметів") which teaches incorrect rules to learners. Additionally, one activity item is broken (nonsensical sentence) and another lacks clear instructions. These issues must be fixed before release.

===REVIEW_END===
