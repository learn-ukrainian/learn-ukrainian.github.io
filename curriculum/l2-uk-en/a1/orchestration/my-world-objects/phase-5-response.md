# Рецензія: My World: Objects

**Level:** A1 | **Module:** 05
**Overall Score:** 6.8/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS
- Vocabulary: FAIL (15+ words in text/activities missing from YAML; mismatch between text and summary)
- Grammar scope: FAIL (Locative case 'на тому столі' introduced prematurely)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Flow is okay, but untaught vocabulary in activities creates friction. |
| 2 | Coherence | 6/10 | <7 | Text uses "блюдо", Summary lists "тарілка". Activities test words not in text. |
| 3 | Relevance | 7/10 | <7 | Core vocab is good, but "блюдо" (platter/course) for "plate" is poor choice for A1. |
| 4 | Educational | 6/10 | <7 | Scope creep (Locative case) confuses the focus. Testing untaught words is unfair. |
| 5 | Language | 8/10 | <8 | Grammar is correct, but "блюдо" usage is questionable stylistic choice. |
| 6 | Pedagogy | 6/10 | <7 | Premature introduction of Locative case ('на тому столі'); testing untaught vocab. |
| 7 | Immersion | 10/10 | <6 | Appropriate English/Ukrainian mix for A1. (Audit metric of 75% seems incorrect vs content). |
| 8 | Activities | 6/10 | <7 | Activities include words (склянка, пляшка, підлога) never taught in the lesson. |
| 9 | Richness | 7/10 | <6 | Cultural content is good (Khruchshovkas), but vocabulary integration is messy. |
| 10 | Beginner Safety | 6/10 | <7 | Sudden case changes (Locative) and unknown words in quizzes will frustrate learners. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural tone. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Ukrainian sentences are grammatically correct, even if out of scope. |

**Weighted Overall:** (7*1.5 + 6*1.0 + 7*1.0 + 6*1.2 + 8*1.1 + 6*1.2 + 10*1.0 + 6*1.3 + 7*0.9 + 6*1.3 + 8*1.0 + 9*1.5) / 14.0 = **7.16/10**
*Correction*: The calculated weighted score is ~7.2, but the Auto-Fail triggers (Coherence, Educational, Pedagogy, Activities, Beginner Safety < 7) dictate a FAIL.

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] (Note: "блюдо" is borderline stylistic issue, not strict Russianism, but "тарілка" is preferred).
- Calques: [CLEAN]
- Grammar scope: **FAIL** (Locative case: "на тому столі", "на дивані")
- Activity errors: **FAIL** (Untaught vocabulary items)
- Beginner safety: 3/5

## Critical Issues Found

### Issue 1: Scope Creep (Locative Case)
- **Location**: Section "In the Living Room" / "Mini-Dialogue 2"
- **Original**: "Він на тому столі." (It's on that table.) / "Цей пульт на дивані."
- **Problem**: Introduces Locative case endings (-ому, -і) for nouns and pronouns. Module 05 focuses on Nominative demonstratives. This confuses the learner about the forms of "той/стіл".
- **Fix**: Change examples to Nominative. E.g., "Ось той стіл." (Here is that table.) OR "Де телефон? Там. На столі." (Where is phone? There. On table - fixed phrase), avoiding "на ТОМУ столі".

### Issue 2: Vocabulary Consistency ("Блюдо" vs "Тарілка")
- **Location**: Presentation "Kitchen Objects" vs Summary vs Vocabulary YAML
- **Original**: Text uses "Це блюдо" (this dish). Summary lists "тарілка" (plate). YAML has "блюдо" but not "тарілка".
- **Problem**: "Тарілка" is the standard A1 word for "plate". "Блюдо" is a large platter or a meal course. Inconsistent usage confuses learners.
- **Fix**: Replace all instances of "блюдо" with "тарілка" in text and YAML.

### Issue 3: Untaught Vocabulary in Activities
- **Location**: Activities `objects-and-translations` (match-up), `sort-by-gender` (group-sort)
- **Original**: Items: склянка, пляшка, плита, підлога.
- **Problem**: These words appear in the Summary list and Activities but are NEVER introduced or used in the Lesson Text.
- **Fix**: Either add them to the "Presentation" section (with images/context) or remove them from activities.

### Issue 4: Vocabulary YAML / Text Mismatch
- **Location**: `vocabulary/05-my-world-objects.yaml`
- **Original**: Missing ~15 words listed in the text Summary (тарілка, вікно, двері, стіна, підлога, etc.).
- **Problem**: Build system relies on YAML. The summary promises 40 words, YAML has ~27.
- **Fix**: Audit the text and add all actually taught words to the YAML.

### Issue 5: Ambiguous Warm-up
- **Location**: Warm-up
- **Original**: "Ця чашка?" ... "Те вікно?"
- **Problem**: Grammatically valid as elliptical questions ("This cup?"), but pedagogical weak for introducing the concept.
- **Fix**: Use full sentences or clear context: "Це чашка?" (Is this a cup?) or "Ця чашка — твоя?" (This cup is yours?).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 59 | Це блюдо | Це тарілка | Stylistic / Vocabulary |
| 79 | на тому столі | на столі (or change sentence) | Scope Creep (Locative) |
| 82 | на дивані | там (or change sentence) | Scope Creep (Locative) |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Fail** (Sudden grammar changes in examples)
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? **Fail** (Case endings appearing without explanation)
- Come back tomorrow? Maybe

## Fix Plan to Reach 9/10

### Pedagogy & Educational: 6/10 → 9/10

**What to fix:**
1.  **Remove Locative Case**: Rewrite "In the Living Room" dialogue.
    *   Change: "Він на тому столі." → "Він там. На столі." (He is there. On the table - simpler). OR "Ось той стіл. Телефон там."
    *   Change: "Цей пульт на дивані." → "Ось пульт. Він там."
2.  **Integrate Ghost Vocabulary**:
    *   Add a visual list or short text block in "Presentation" introducing: тарілка, склянка, пляшка, плита, підлога, стіна.
    *   Example: "In the Kitchen: Це плита. Це тарілка. Це склянка."

### Coherence & Activities: 6/10 → 9/10

**What to fix:**
1.  **Standardize Vocabulary**: Replace "блюдо" with "тарілка" everywhere (Text, YAML, Activities).
2.  **Sync YAML**: Run a script or manually add: тарілка, склянка, пляшка, гаманець, ліжко, шафа, плита, пилосос, двері, вікно, стіна, підлога, стеля, картина, кухня to `vocabulary/05-my-world-objects.yaml`.
3.  **Clean Activities**: Ensure every word in `group-sort` and `match-up` was explicitly shown in the text.

### Experience Quality: 7/10 → 9/10

**What to fix:**
1.  **Refine Warm-up**: Make the demonstrative usage explicit. "Imagine pointing: 'Це чашка' (This is a cup) vs 'Ця чашка' (This cup)."

### Projected Overall After Fixes

With scope creep removed, vocabulary standardized, and activities aligned:
- Pedagogy: 9/10
- Educational: 9/10
- Coherence: 10/10
- Activities: 9/10
- Beginner Safety: 9/10
**Projected Score: ~9.2/10**

## Verification Summary

- Content lines read: ~160
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: N/A (not present in text body, only YAML)
- Issues found: 5 Major
- Naturalness score recommendation: 9/10 (Language is natural, just out of scope)

## Verdict

**FAIL**

Blocking issues: Scope creep (Locative case), Vocabulary mismatch between text/summary/YAML, and testing untaught words in activities.
