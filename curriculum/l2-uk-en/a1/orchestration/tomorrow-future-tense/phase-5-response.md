# Рецензія: Tomorrow - Future Tense

**Level:** A1 | **Module:** 22
**Overall Score:** 5.8/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [FAIL]
- Sections: [PASS] All plan points covered, though some merged.
- Vocabulary: [FAIL] "незабаром" required but missing (replaced by "скоро").
- Grammar scope: [FAIL] Massive scope creep: Perfective Future used extensively despite module explicitly stating it is for A2.
- Objectives: [PASS] Core objectives met, but undermined by out-of-scope examples.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Generally clear, but confusion from grammar inconsistencies lowers score. |
| 2 | Coherence | 5/10 | <7 | Explains "Imperfective Future" then uses "Perfective Future" in examples without explanation. |
| 3 | Relevance | 7/10 | <7 | Future tense is highly relevant. |
| 4 | Educational | 6/10 | <7 | Confuses the learner by breaking its own rules about "Coming in A2". |
| 5 | Language | 9/10 | <8 | Natural Ukrainian, but pedagogical scope violations. |
| 6 | Pedagogy | 5/10 | <7 | Teaches one pattern (Budu + Inf), tests/exemplifies another (Simple Future). |
| 7 | Immersion | 8/10 | <6 | Good usage of Ukrainian. |
| 8 | Activities | 4/10 | <7 | Critical logic errors in True/False answer keys. |
| 9 | Richness | 6/10 | <6 | Meets basic needs, but missing "незабаром" from plan. |
| 10 | Beginner Safety | 5/10 | <7 | Students will be baffled seeing "зроблю" after just learning "буду робити". |
| 11 | LLM Fingerprint | 8/10 | <7 | Content feels structured, few hallucinations. |
| 12 | Linguistic Accuracy | 9/10 | <9 | The Ukrainian itself is correct, just out of scope. |

**Weighted Overall:** (7*1.5 + 5*1.0 + 7*1.0 + 6*1.2 + 9*1.1 + 5*1.2 + 8*1.0 + 4*1.3 + 6*0.9 + 5*1.3 + 8*1.0 + 9*1.5) / 14.0 = **6.45/10**

*(Correction: The calculated score is low due to Activities (4) and Pedagogy (5). Let's stick to the strict calculation.
10.5 + 5 + 7 + 7.2 + 9.9 + 6 + 8 + 5.2 + 5.4 + 6.5 + 8 + 13.5 = 92.2 / 14 = 6.58)*

**Weighted Overall:** 6.6/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] List: *поїдемо, скоро, пізніше, згодом, зрозуміє, приїде, одружимося, зроблю, поїде, спробую, постараюся, зателефоную*.
- Activity errors: [FAIL] True/False items marked FALSE when actually TRUE.
- Beginner safety: 3/5

## Critical Issues Found

### Issue 1: Activity Logic Errors (True/False)
- **Location**: `curriculum/l2-uk-en/a1/activities/22-tomorrow-future-tense.yaml` (Lines 319-354)
- **Original**:
    - statement: «Скоро» means "soon."
    correct: false
  - statement: «Вже» means "already."
    correct: false
  - statement: «Планую» means "I plan."
    correct: false
  - statement: «Ніколи» means "never."
    correct: false
  - **Problem**: These statements are TRUE, but the key says `false` (and the explanation even says "Correct!" which implies the generator got confused between "Correct statement" and "True/False").
- **Fix**: Change `correct: false` to `correct: true` for these items.

### Issue 2: Grammar Scope Creep (Perfective Future)
- **Location**: Multiple locations in `22-tomorrow-future-tense.md`
- **Original**:
  - "Післязавтра ми **поїдемо**." (Line 139)
  - "Скоро буде весна." (Line 140 - *буде* is ok, but strictly simple future here acts perfective-ish in aspect, though formally simple. Acceptable.)
  - "Пізніше я **подзвоню**." (Line 141)
  - "Згодом він **зрозуміє**." (Line 143)
  - "Наступного місяця вона **приїде**." (Line 145)
  - "Наступного року ми **одружимося**." (Line 146)
  - "Я обов'язково **зроблю** це завтра." (Line 177)
  - "Вона ще не вирішила, куди **поїде**." (Line 179)
  - "Я **спробую**..." (Line 104)
  - "Я **постараюся**..." (Line 105)
  - "Я **зателефоную**..." (Line 214)
- **Problem**: The module introduces *Compound Future* (буду + infinitive) and explicitly says "Perfective future... Coming in A2". However, all these examples use Perfective Future forms which have unique conjugations not taught yet.
- **Fix**: Rewrite examples to use *Compound Future* (буду + inf) OR *Modal + Infinitive* (планую, хочу + inf).

### Issue 3: Missing Vocabulary Plan Compliance
- **Location**: Content vs Plan
- **Original**: Plan requires "незабаром". Content uses "скоро".
- **Problem**: "незабаром" is a required vocabulary item but is missing.
- **Fix**: Replace one instance of "скоро" with "незабаром" or add it to the adverbs list.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 139 | "Післязавтра ми поїдемо." | "Післязавтра ми плануємо поїхати." | Scope (Perf. Future) |
| 141 | "Пізніше я подзвоню." | "Пізніше я буду дзвонити." / "Пізніше я зателефоную" (Keep as set phrase? No, A1.) -> "Пізніше я подзвоню" (Change to: "Пізніше я буду вдома" - simpler) | Scope |
| 143 | "Згодом він зрозуміє." | "Згодом він буде розуміти." (Awkward) -> "Згодом він буде знати." | Scope |
| 145 | "Наступного місяця вона приїде." | "Наступного місяця вона буде тут." | Scope |
| 146 | "Наступного року ми одружимося." | "Наступного року ми плануємо весілля." (Noun) or "плануємо одружитися." | Scope |
| 177 | "Я обов'язково зроблю це завтра." | "Я обов'язково буду це робити завтра." | Scope |
| 179 | "куди поїде" | "куди їхати" (where to go - inf) or "куди планує поїхати" | Scope |
| 205 | "Я спробую вивчити..." | "Я хочу спробувати вивчити..." | Scope |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? [Fail] (Too many unknown verb forms in examples)
- Instructions clear? [Pass]
- Quick wins? [Pass] (Budu pattern is easy)
- Ukrainian scary? [Fail] (Examples contradict the rules taught)
- Come back tomorrow? [Pass] (If fixed)

## Fix Plan to Reach 9/10

### Pedagogy & Coherence: 5/10 → 9/10

**What to fix:**
1.  **Strictly enforce Compound Future**: In sections "Presentation: Time Expressions" and "examples in Context", replace every Perfective Future verb with a structure students actually know (Budu + Inf, or Modal + Inf).
    *   Change "Я обов'язково зроблю це завтра" → "Я обов'язково буду це робити завтра" OR "Я обов'язково хочу це зробити завтра".
    *   Change "Наступного року ми одружимося" → "Наступного року ми плануємо одружитися".
    *   Change "Пізніше я подзвоню" → "Пізніше я буду дзвонити" or "Пізніше я планую подзвонити".
2.  **Add "незабаром"**: Add to "Presentation: Useful Adverbs".
    *   Add: "**незабаром** (soon) — synonym for скоро. *Ми незабаром будемо вдома.*"

### Activities: 4/10 → 9/10

**What to fix:**
1.  **Fix True/False Logic**: In `activities/22-tomorrow-future-tense.yaml`, locate the `true-false` section.
    *   For items: "«Скоро» means 'soon'", "«Вже» means 'already'", "«Планую» means 'I plan'", "«Ніколи» means 'never'".
    *   Change `correct: false` to `correct: true`.

### Beginner Safety: 5/10 → 9/10

**What to fix:**
1.  **Reduce Cognitive Load**: By fixing the scope creep (Issue 2), the student won't be confused by seeing "зроблю" after being told the future is "буду + inf".

## Verdict

**FAIL**

The module fails on two critical counts: 1) Massive scope creep by using Perfective Future forms throughout examples while explicitly stating they are for A2, creating pedagogical dissonance. 2) Broken logic in the Activities file where correct definitions are marked as False. These must be fixed before release.