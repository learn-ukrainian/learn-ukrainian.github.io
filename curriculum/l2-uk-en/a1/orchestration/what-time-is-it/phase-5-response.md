# Рецензія: What Time Is It?

**Level:** A1 | **Module:** 23
**Overall Score:** 8.8/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [Most required words used in content, BUT vocabulary YAML is severely incomplete]
- Grammar scope: [clean - future tense allowed by prereq A1-22]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Clear, logical progression. |
| 2 | Coherence | 10/10 | <7 | Structure matches the plan well. |
| 3 | Relevance | 10/10 | <7 | Essential daily topic. |
| 4 | Educational | 9/10 | <7 | Good explanation of logic (ordinal numbers). |
| 5 | Language | 9/10 | <8 | Generally natural, one minor lexical precision issue ("відкривається"). |
| 6 | Pedagogy | 8/10 | <7 | Good explanations, but activities have logic gaps. |
| 7 | Immersion | 9/10 | <6 | Cultural notes on month names are excellent. |
| 8 | Activities | 6/10 | <7 | **FAIL**: Ambiguous items where multiple options are factually correct. |
| 9 | Richness | 9/10 | <6 | Good depth on month etymologies. |
| 10 | Beginner Safety | 10/10 | <7 | Welcoming tone, clear instructions. |
| 11 | LLM Fingerprint | 10/10 | <7 | No obvious robotic phrasing. |
| 12 | Linguistic Accuracy | 9/10 | <9 | High accuracy. |

**Weighted Overall:** 8.8/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** Ambiguous fill-in items (multiple correct answers).
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activity Ambiguity (Multiple Correct Answers)
- **Location**: `activities/23-what-time-is-it.yaml`, Item 1 ("Зараз ___ година.")
- **Original**: Answer: "друга", Options: ["третя", "два", "другий", "друге"]
- **Problem**: "Зараз третя година" (It is three o'clock) is just as grammatically and semantically correct as "Зараз друга година" (It is two o'clock) without any context (image or clock face) to distinguish them.
- **Fix**: Change options to remove the valid distractor. E.g., Options: ["друга", "два", "п'ять", "годин"]. OR provide a context clue.

### Issue 2: Activity Ambiguity (Multiple Correct Answers)
- **Location**: `activities/23-what-time-is-it.yaml`, Item 11 ("Зараз ___ на четверту.")
- **Original**: Answer: "пів", Options: ["пів", "чверть", "після", "за"]
- **Problem**: "Зараз чверть на четверту" (It is a quarter past three) is grammatically valid. "Зараз пів на четверту" (It is half past three) is also valid. Without context, both are correct completions.
- **Fix**: Remove "чверть" from distractors or provide specific context (e.g., "3:30").

### Issue 3: Incomplete Vocabulary YAML
- **Location**: `vocabulary/23-what-time-is-it.yaml`
- **Original**: Contains only 12 words, missing core terms like `година`, `хвилина`, `тиждень`, `понеділок`, etc.
- **Problem**: The vocabulary file does not reflect the actual vocabulary taught in the module. It seems to have missed the core words defined in the plan.
- **Fix**: Regenerate vocabulary YAML to include all bolded terms and core concepts from the module (days, months, time units).

### Issue 4: Lexical Precision (Minor)
- **Location**: Content, "Examples" and `vocabulary/23-what-time-is-it.yaml`
- **Original**: "Магазин відкривається..." / Lemma: "відкриватися"
- **Problem**: While common, "відкриватися" is often criticized as a calque or less precise than "відчинятися" when referring to physical shops/doors opening. "Відкривати" is for discoveries, seasons, meetings.
- **Fix**: Change to "Магазин відчиняється..." and update lemma to "відчинятися". (Or "працює з..." as used elsewhere).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | Магазин відкривається | Магазин відчиняється | Stylistic/Precision |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass (Etymologies make it approachable)
- Come back tomorrow? Pass

## Strengths
- Excellent cultural context on the "nature-based" names of months.
- Clear breakdown of the "ordinal number" logic for telling time.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1. `activities/23-what-time-is-it.yaml` (Item 1): Change options for "Зараз ___ година." Replace "третя" with "три" or "два" (cardinal numbers are wrong here, so they act as good distractors). Ensure only ONE ordinal number is in the options.
2. `activities/23-what-time-is-it.yaml` (Item 11): Change options for "Зараз ___ на четверту." Replace "чверть" with "сьогодні" or another irrelevant word.
3. **Regenerate Vocabulary YAML**: Add missing core words: `година`, `хвилина`, `ранок`, `вечір`, `тиждень`, `понеділок`...`неділя`, `січень`...`грудень`.

### Language: 9/10 → 10/10

**What to fix:**
1. Content & Vocabulary: Replace "відкриватися" with "відчинятися" in the context of the shop opening to model high-standard Ukrainian.

## Verdict

**FAIL**

The module is well-written and pedagogically sound in its explanation, but it fails on **Activities** due to ambiguous questions where multiple options are correct. Additionally, the **Vocabulary YAML** is severely incomplete and does not match the content. These technical issues must be resolved before approval.