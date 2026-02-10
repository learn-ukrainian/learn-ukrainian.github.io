# Рецензія: Numerals and Nouns

**Level:** A2 | **Module:** 21
**Overall Score:** 5.7/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS - all headers present]
- Vocabulary: [PASS - matches plan scope]
- Grammar scope: [FAIL - Content teaches only Nominative/Basic Agreement. Activities test Dative and Accusative Animate, which are NOT in the content.]
- Objectives: [FAIL - Objectives "use numerals in accusative" and "dative" are not supported by the learning material.]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 5/10 | <7 | Users are tested on concepts (Dative, Accusative Animate) they were never taught. |
| 2 | Coherence | 5/10 | <7 | Major disconnect between Content (Basic) and Activities (Advanced cases). |
| 3 | Relevance | 8/10 | <7 | Topic is highly relevant for A2. |
| 4 | Educational | 4/10 | <7 | Teaches incorrect grammar ("євра") and fails to explain tested concepts. |
| 5 | Language | 6/10 | <8 | Critical error: declension of indeclinable noun "євро". |
| 6 | Pedagogy | 5/10 | <7 | "Testing what wasn't taught" violation regarding Dative/Accusative cases. |
| 7 | Immersion | 8/10 | <6 | Good balance of explanation and examples. |
| 8 | Activities | 4/10 | <7 | Contains grammar errors ("дві вікна") and malformed items. |
| 9 | Richness | 7/10 | <6 | Good examples, but undermined by accuracy issues. |
| 10 | Beginner Safety | 4/10 | <7 | High frustration likely due to untaught activity questions. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural tone, "євра" is a hallucination. |
| 12 | Linguistic Accuracy | 6/10 | <9 | "Євро" error is unacceptable for a grammar module. |

**Weighted Overall:** (5×1.5 + 5 + 8 + 4×1.2 + 6×1.1 + 5×1.2 + 8 + 4×1.3 + 7×0.9 + 4×1.3 + 8 + 6×1.5) / 14.0 = **5.7/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: **FAIL** (Activities test Dative/Accusative Animate, Content does not teach it)
- Activity errors: **FAIL** (Items 2, 9, 10 in various activities)
- Beginner safety: 2/5 (Tests untaught material, confused rules)

## Critical Issues Found

### Issue 1: "Євро" Declension Error
- **Location**: Content / Section 4 "Practical Application", Table Row 2, 5, 24
- **Original**: "два євр**а**", "двадцять чотири євр**а**"
- **Problem**: The noun "євро" is indeclinable in Ukrainian. It never changes form (одне євро, два євро, п'ять євро).
- **Fix**: Replace "євра" with "євро" in all instances.

### Issue 2: Activity Grammar Error (Gender Agreement)
- **Location**: `activities.yaml` / Item 2 (fill-in) "Complete the Phrase"
- **Original**: `sentence: дві [___]`, `answer: вікна`
- **Problem**: "Вікно" is neuter. Neuter nouns use "два" (same as masculine), not "дві" (feminine). "Дві вікна" is grammatically impossible.
- **Fix**: Change item to `sentence: два [___]`, `answer: вікна` OR change target noun to feminine `sentence: дві [___]`, `answer: книги`.

### Issue 3: Malformed Cloze Item
- **Location**: `activities.yaml` / Item 11 (cloze) "Age Expressions"
- **Original**: `тридцять {тридцять|тридцяти|тридцятьом|тридцятьма} років`
- **Problem**: The word "тридцять" is repeated outside the brace, and the options are cases of the number "30" while the blank seems to imply a missing number or case agreement check. The sentence structure is broken.
- **Fix**: Change to `Вони працюють разом уже {тридцять} років` (if testing the number) or remove the duplicate word.

### Issue 4: Pedagogical Scope Mismatch (Dative/Accusative)
- **Location**: `activities.yaml` / Quiz "Accusative with Numerals" AND Fill-in "Dative with Numerals"
- **Original**: Activities asking for "двох студентів", "двом студентам", "п'ятьох дітей".
- **Problem**: The Content module (`21-numerals-and-nouns.md`) **NEVER** mentions that animate nouns have special forms in Accusative, nor does it mention Dative case forms for numerals. It only teaches the "1-2-5" Nominative rule.
- **Fix**: Either **ADD** a section to the Content explaining Accusative Animate and Dative forms of numerals, OR **REMOVE** these activities and objectives. Given the complexity of A2 M21, removing Dative is recommended, but Accusative Animate is useful.

### Issue 5: Stylistic Phrasing
- **Location**: Content / Dialogues
- **Original**: "Мені потрібно один кілограм яблук"
- **Problem**: While colloquial, "потрібно" (impersonal) with a nominative/accusative object is stylistically weak. "Мені потрібен один кілограм" (Personal construction) is standard literary Ukrainian.
- **Fix**: Change to "Мені потрібен один кілограм яблук" OR "Мені треба один кілограм яблук".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Content | два євра | два євро | Grammar |
| Content | двадцять чотири євра | двадцять чотири євро | Grammar |
| Activity | дві [вікна] | два [вікна] | Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: 2/5
- Overwhelmed? **Fail** (Activities ask impossible questions based on reading).
- Instructions clear? **Pass**
- Quick wins? **Pass** (Initial logic is clear).
- Ukrainian scary? **Fail** (Sudden appearance of "двом/п'ятьох" without warning).
- Come back tomorrow? **Fail** (Feeling of "I missed something crucial").

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 6/10 → 10/10
**What to fix:**
1.  **Content**: Search/Replace all instances of "євра" -> "євро".
2.  **Activities**: Fix the "дві вікна" item to "два вікна" or use a feminine noun.

### Pedagogy & Educational: 4/10 → 9/10
**What to fix:**
1.  **Scope Alignment**: The Plan requires Dative/Accusative. The Content lacks it.
    *   **Action**: Update `21-numerals-and-nouns.md` to include a new section **"4. Advanced: People and Giving (Accusative & Dative)"**.
    *   **Content**: Briefly explain: "When counting *people* (animate), 2-4 look like 5+ (Gen Pl/Acc Gen). When giving *to* someone (Dative), numerals change: 2->двом, 3->трьом, 4->чотирьом, 5->п'ятьом."
    *   **Alternative**: If this makes the module too long (it is already long), **REMOVE** the Dative/Accusative activities from `activities.yaml` and update the `plan` to move these objectives to a later module.
    *   *Recommendation*: **Add Accusative Animate** (it's essential for "I see two students") but **Cut Dative** (too much morphology for one lesson).

### Activities: 4/10 → 9/10
**What to fix:**
1.  **Fix Broken Cloze**: Repair the "Age Expressions" item logic.
2.  **Align**: Remove "Dative with Numerals" activity entirely (move to future module). Keep "Accusative with Numerals" ONLY if content is updated to teach it.

### Projected Overall After Fixes
With "євро" fixed, "дві вікна" fixed, and the scope aligned (either by teaching the cases or removing the tests):
Weighted Score ≈ **9.2/10**

## Verdict

**FAIL**

Blocking issues: Grammar error ("євро"), Activity error ("дві вікна"), and major Pedagogical failure (testing untaught Dative/Accusative cases). These must be resolved before release.