# Рецензія: Emergencies

**Level:** A1 | **Module:** 42
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [7/8 required words used. 'травма' missing. 6 items in YAML vs ~30 in text]
- Grammar scope: [FAIL - Instrumental case found (out of scope)]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong narrative and practical scenarios. |
| 2 | Coherence | 8/10 | <7 | Text uses idiomatic "У мене вкрали" but switches to "Я не маю". |
| 3 | Relevance | 10/10 | <7 | Highly relevant survival content. |
| 4 | Educational | 9/10 | <7 | Clear, useful phrases. |
| 5 | Language | 7/10 | <8 | Scope creep (Instrumental) and unnatural possession structure. |
| 6 | Pedagogy | 7/10 | <7 | Uses grammar (Instrumental) not yet taught in A1. |
| 7 | Immersion | 9/10 | <6 | Good usage of cultural context (112, Diia/Passport). |
| 8 | Activities | 9/10 | <7 | Well-structured, though one item has scope creep. |
| 9 | Richness | 8/10 | <6 | Narrative is detailed, but `vocabulary.yaml` is empty/broken. |
| 10 | Beginner Safety | 7/10 | <7 | Unexplained case endings (-ою, -ом) cause friction. |
| 11 | LLM Fingerprint | 9/10 | <7 | Narrative feels handcrafted and emotive. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammatically correct, just stylistically rigid. |

**Weighted Overall:** (13.5 + 8 + 10 + 10.8 + 7.7 + 8.4 + 9 + 11.7 + 7.2 + 9.1 + 9 + 13.5) / 14.0 = **117.9 / 14 = 8.42/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [Line 24, 25, 57, 60: "Я не маю" instead of "У мене немає"]
- Grammar scope: [Line 53: "готівкою" (Instr), Line 66: "з гербом" (Instr)]
- Activity errors: [Activity "unjumble" item 9: "мовою" (Instr)]
- Beginner safety: 7/5

## Critical Issues Found

### Issue 1: Grammar Scope Creep (Instrumental Case)
- **Location**: Line 53 / Narrative
- **Original**: "Він платить готівкою."
- **Problem**: Instrumental case (`-ою`) is A2 grammar. Students only know Nominative/Accusative/Genitive/Locative.
- **Fix**: "Він платить за все." (He pays for everything) or "Він платить."

### Issue 2: Grammar Scope Creep (Instrumental Prepositional)
- **Location**: Line 66 / Narrative
- **Original**: "Він синій, з золотим гербом."
- **Problem**: `з` + Instrumental (`-ом`) is out of scope.
- **Fix**: "Він синій і має золотий герб." (Accusative) or "Він синій. Там золотий герб."

### Issue 3: Naturalness / Pattern Consistency
- **Location**: Line 24, 25 (Table) & Line 57, 60 (Narrative)
- **Original**: "Я не маю паспорта." / "Я не маю документів!"
- **Problem**: While grammatical, standard A1 pedagogy focuses on "У мене немає..." for possession. "Я не маю" is a structural anglicism/calque here and breaks the pattern established in Module 22.
- **Fix**: "У мене немає паспорта." / "У мене немає документів!"

### Issue 4: Activity Scope Creep
- **Location**: Activity `unjumble` / Item 9
- **Original**: `["Ви", "говорите", "англійською", "мовою", "?"]`
- **Problem**: `мовою` is Instrumental. The standard phrase "Ви говорите англійською?" uses the adverbial form and is sufficient.
- **Fix**: Remove "мовою".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 24 | Я не маю паспорта. | У мене немає паспорта. | Naturalness/Pedagogy |
| 53 | платить готівкою | платить / платить гроші | Scope (Instr) |
| 66 | з золотим гербом | і має золотий герб | Scope (Instr) |

## Fix Plan to Reach 9/10

### Language: 7/10 → 10/10
**What to fix:**
1.  Line 24: Change "Я не маю паспорта." → "У мене немає паспорта." — Enforces standard idiomatic negation.
2.  Line 25: Change "Я не маю телефону." → "У мене немає телефону." — Consistency.
3.  Line 53: Change "Він платить готівкою." → "Він платить." — Removes untaught Instrumental case.
4.  Line 57: Change "Я не маю документів!" → "У мене немає документів!" — Natural panic phrase.
5.  Line 60: Change "Я не маю документів." → "У мене немає документів." — Natural dialogue.
6.  Line 66: Change "Він синій, з золотим гербом." → "Він синій і має золотий герб." — Uses known grammar (Accusative).

### Activities: 9/10 → 10/10
**What to fix:**
1.  Activity `unjumble` (Item 9): Remove "мовою" from the word list and answer. Answer becomes: «Ви говорите англійською?» — Removes Instrumental scope creep.

### Projected Overall After Fixes
New Language Score: 10
New Pedagogy Score: 10
New Beginner Safety Score: 9
**Projected Overall:** 9.6/10

## Verdict
**FAIL**

The content is engaging and useful, but the **grammar scope violations** (Instrumental case) and **unnatural possession structures** ("Я не маю") prevent it from being a safe A1 module. These must be fixed to align with the curriculum progression.