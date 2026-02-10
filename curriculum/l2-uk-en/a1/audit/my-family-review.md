# Рецензія: My Family

**Level:** A1 | **Module:** 32
**Overall Score:** 8.9/10
**Status:** PASS
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required used, 6/6 recommended used]
- Grammar scope: [Minor scope creep in Dialogues]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong flow, warm tone. |
| 2 | Coherence | 10/10 | <7 | Logical progression from vocabulary to grammar to practice. |
| 3 | Relevance | 10/10 | <7 | Core A1 topic. |
| 4 | Educational | 9/10 | <7 | Objectives met effectively. |
| 5 | Language | 8/10 | <8 | Generally correct, but one confusing explanation and one scope risk. |
| 6 | Pedagogy | 9/10 | <7 | Good PPP structure, useful patterns. |
| 7 | Immersion | 10/10 | <6 | Cultural notes on "родина" vs "сім'я" are excellent. |
| 8 | Activities | 8/10 | <7 | Good variety, but formatting typos in YAML. |
| 9 | Richness | 10/10 | <6 | 1597 words vs 916 target (174%). |
| 10 | Beginner Safety | 8/10 | <7 | Dative case in dialogue might confuse without explanation. |
| 11 | LLM Fingerprint | 9/10 | <7 | Natural voice, minimal robotic phrasing. |
| 12 | Linguistic Accuracy | 9/10 | <9 | High accuracy in Ukrainian text. |

**Weighted Overall:** 8.93/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [Dative case 'Дочці' used but not taught]
- Activity errors: [Double quotes typos in strings]
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Confusing Vocative Instruction
- **Location**: Line 132 (approx) / Section "Vocative Case"
- **Original**: "Don't use with titles: Пане Іване! (Mr. Ivan!) — not «Пан Іване!»"
- **Problem**: The header "Don't use with titles" implies one should *avoid* using the Vocative with titles, but the example shows using it (`Пане Іване`) is correct. The text contradicts itself.
- **Fix**: "Use with titles too: Пане Іване! (Mr. Ivan!) — not «Пан Іване!»"

### Issue 2: Grammar Scope Creep (Dative Case)
- **Location**: Line 167 (approx) / Section "Діалоги"
- **Original**: "— Скільки років твоїй дочці? / — Дочці п'ять років."
- **Problem**: The Dative case for nouns (`дочці`) has not been taught yet (Plan says Dative is Out of Scope). While `Мені 5 років` is a common chunk, declension of nouns is advanced for A1 M32.
- **Fix**: Use pronouns if possible (assuming `Їй` is known) or add a specific tip explaining this form.
  *Preferred Fix*: Add a tip immediately after the dialogue:
  `> [!note] Grammar Tip`
  `> When talking about age, we change the form: **Дочка** (Daughter) → **Дочці** (To the daughter). Literally: "To the daughter is 5 years."`

### Issue 3: YAML Formatting Typos
- **Location**: `activities/32-my-family.yaml`, Item 14 (True-False)
- **Original**: `statement: ««Тато» is informal for «father.».»`
- **Problem**: Double angular quotes (`««...»`) and punctuation inside quotes look like an LLM artifact.
- **Fix**: `statement: «Тато» is informal for «father».` (Remove outer angular quotes if they are part of the string value, or fix the nesting).

## Fix Plan to Reach 9/10

### Language: 8/10 → 9/10

**What to fix:**
1.  **Section "Vocative Case"**: Change "**Don't use with titles:** Пане Іване!..." → "**Use with titles:** Пане Іване!..." — Clarifies the rule.
2.  **Section "Dialogues"**: Add a `[!note]` explaining `Дочці` (Dative) as a "receiver of age". — Resolves scope confusion without removing authentic dialogue.

### Activities: 8/10 → 9/10

**What to fix:**
1.  **File `activities/32-my-family.yaml`**: Search for `««` and replace with `«`.
2.  **File `activities/32-my-family.yaml`**: Fix `explanation: ««Incorrect! it means «grandmother»»»` → `explanation: "Incorrect! It means «grandmother»."` (Clean up nesting).

### Beginner Safety: 8/10 → 9/10

**What to fix:**
1.  **Section "Dialogues"**: The added note about `Дочці` (from Language fix) will restore safety by explaining the "scary" new grammar form.

### Projected Overall After Fixes

```
(9*1.5 + 10*1.0 + 10*1.0 + 9*1.2 + 9*1.1 + 9*1.2 + 10*1.0 + 9*1.3 + 10*0.9 + 9*1.3 + 9*1.0 + 9*1.5) / 14.0 = 9.25/10
```

## Verification Summary

- Content lines read: ~200
- Activity items checked: 12 activities
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: 15
- Issues found: 3
- Naturalness score recommendation: 10/10

## Verdict

**PASS** (Conditional)

The module is excellent but requires 3 specific small fixes (Vocative explanation, Dative note, Activity quotes) to be perfect.