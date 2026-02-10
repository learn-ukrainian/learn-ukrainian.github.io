===REVIEW_START===
# Рецензія: She Said That...

**Level:** A2 | **Module:** 28
**Overall Score:** 8.6/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [20+/20 from plan used]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong cultural hooks ("BBC", "Lavka"); clear, friendly tone. |
| 2 | Coherence | 9/10 | <7 | Logical flow from concepts to practice. |
| 3 | Relevance | 10/10 | <7 | Essential social skill ("She said that..."). |
| 4 | Educational | 9/10 | <7 | Clear explanation of the "No Backshift" rule. |
| 5 | Language | 8/10 | <8 | Minor stylistic oddities ("звітувати", "запитати щоб"). |
| 6 | Pedagogy | 9/10 | <7 | Good scaffolding (Statement -> Question -> Command). |
| 7 | Immersion | 9/10 | <6 | Strong Ukrainian examples and cultural context. |
| 8 | Activities | 6/10 | <7 | **CRITICAL:** Duplicate keys in match-up; ambiguous distractor. |
| 9 | Richness | 9/10 | <6 | "Lavka" context adds depth. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Very welcoming. |
| 11 | LLM Fingerprint | 9/10 | <7 | Feels handcrafted and authentic. |
| 12 | Linguistic Accuracy | 8/10 | <9 | A few awkward phrasings in text. |

**Weighted Overall:** 8.6/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** (Duplicate item, ambiguous answer)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activities - Duplicate Match-Up Keys
- **Location**: Activities YAML / type: match-up (Reporting Verbs)
- **Original**:
  ```yaml
  - left: Повідомити
    right: To inform
  ...
  - left: повідомити
    right: to report
  ```
- **Problem**: The word "Повідомити" appears twice (once capitalized, once lowercase) mapping to different English definitions. This creates confusion and potential UI errors in matching games.
- **Fix**: Remove the second pair (`left: повідомити`, `right: to report`).

### Issue 2: Activities - Ambiguous Distractor
- **Location**: Activities YAML / type: fill-in / Item "Не забудь паспорт"
- **Original**: `options: [нагадала, забула, сказала, повідомила]`
- **Problem**: The distractor "сказала" is also grammatically correct ("Мама сказала, щоб я взяв паспорт"). A distractor cannot be a valid answer.
- **Fix**: Change `сказала` to `мовчала` or `спала`.

### Issue 3: Language - Syntactic Logic
- **Location**: Content / Dialogues / "Office Rumors" / Last line
- **Original**: "Треба запитати, щоб директор сам все пояснив."
- **Problem**: "Запитати, щоб..." (Ask so that...) is syntactically awkward here. The context implies a request for action ("Ask him to explain").
- **Fix**: "Треба **попросити**, щоб директор сам все пояснив."

### Issue 4: Language - Stylistic Register
- **Location**: Content / Intro / Paragraph 1
- **Original**: "Вміння звітувати про сказане..."
- **Problem**: "Звітувати" implies an official report (military/corporate). For casual speech ("gossip"), "переказувати" is the correct term.
- **Fix**: "Вміння **переказувати** сказане..."

## Strengths
- **Cultural Integration**: The "BBC: Баба Бабі Сказала" tip is excellent for engagement and memory.
- **Clear Contrast**: The "Golden Rule: No Backshift" is explained very clearly for English speakers.
- **Vocabulary Selection**: The list of reporting verbs is comprehensive and useful (including emotional ones like *скаржитися*).

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10
**What to fix:**
1. **Reporting Verbs (match-up)**: Remove the duplicate pair:
   ```yaml
   - left: повідомити
     right: to report
   ```
   (Keep the capitalized "Повідомити" -> "To inform").
2. **Report the Sentence (fill-in)**: In item "Не забудь паспорт...", change option `сказала` to `мовчала`.

### Language: 8/10 → 9/10
**What to fix:**
1. **Intro**: Change "Вміння звітувати про сказане" → "Вміння переказувати сказане".
2. **Dialogues**: Change "Треба запитати, щоб директор сам все пояснив" → "Треба попросити, щоб директор сам все пояснив".

### Projected Overall After Fixes
With Activities fixed to 9/10 and Language to 9/10, the weighted average will exceed 9.0.

## Verification Summary
- Content lines read: 84
- Activity items checked: 10 activities (approx 60 items)
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 39
- Issues found: 4 (2 Critical)
- Naturalness score recommendation: 9/10

## Verdict
**FAIL**

The module is excellent in content and tone, but the **duplicate keys in the activities file** and the **ambiguous distractor** are blocking technical issues that must be resolved before release.

===REVIEW_END===
