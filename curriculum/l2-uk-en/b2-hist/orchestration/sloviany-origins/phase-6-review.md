# Рецензія: Слов'яни на українських землях: Витоки державності

**Level:** B2_HIST | **Module:** 4
**Overall Score:** 8.7/10
**Status:** FAIL
**Reviewed:** 2026-02-18

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS
- Vocabulary: FAIL [10/26 from plan] - Missing: праслов'яни, прабатьківщина, розселення, плем'я, язичництво, міграція, народоправство, громада, волхв, Перун, Велес, старійшина, дружина, вождь, данина, автохтон.
- Grammar scope: PASS
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Narrative is strong, but disrupted by excessive inline English translation (scaffolding). |
| 2 | Coherence | 9/10 | <7 | Logical flow is excellent, clear transition between sections. |
| 3 | Relevance | 10/10 | <7 | "De-colonization" and "So What" angles are exceptionally strong. |
| 4 | Educational | 10/10 | <7 | Historical facts are accurate and well-explained. |
| 5 | Language | 9/10 | <8 | High-quality literary Ukrainian, minor stylistic repetitions. |
| 6 | Pedagogy | 9/10 | <7 | Good use of inquiry-based learning. |
| 7 | Immersion | 7/10 | <6 | Frequent inline English (e.g., `**соха** (wooden plow)`) violates the "Seminar" feel of 100% immersion. |
| 8 | Activities | 10/10 | <7 | Activities are varied, relevant, and well-structured. |
| 9 | Richness | 9/10 | <6 | Good specific details (fibulae, reeds), but missing direct Jordanes quote. |
| 10 | Beginner Safety | 10/10 | <7 | Content is accessible yet challenging. |
| 11 | LLM Fingerprint | 8/10 | <7 | Repetitive "Уявіть собі" hook; standard "AI lecture" structure in places. |
| 12 | Linguistic Accuracy | 9/10 | <9 | No major errors found. |

**Weighted Overall:** (8×1.5 + 9×1 + 10×1 + 10×1.2 + 9×1.1 + 9×1.2 + 7×1 + 10×1.3 + 9×0.9 + 10×1.3 + 8×1 + 9×1.5) / 14.0 = **121.9 / 14 = 8.71/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Content Contradiction (Weapons)
- **Location**: Line 28 vs Line 150
- **Original**: «Зброя схожа — списи, щити, мечі.» (Intro) vs «Мечі були рідкістю і належали лише вождям...» (Military)
- **Problem**: The introduction creates a visual of common soldiers with swords, which the specific military section explicitly refutes. This confuses the learner about historical reality.
- **Fix**: In the intro, replace «мечі» with «сокири» (axes) or remove it to align with the later fact.

### Issue 2: Broken Immersion (Inline Scaffolding)
- **Location**: Throughout text (e.g., Lines 117, 120, 148, 161)
- **Original**: «**соха** (wooden plow)», «**землянка** (dugout)», «**тризни** (funeral feast)»
- **Problem**: This is a B2 "Seminar" track module where the goal is 100% immersion. Constant inline English translations for basic historical terms turn a lecture into a bilingual glossary, breaking the narrative flow and "Student in a Ukrainian University" persona.
- **Fix**: Remove parenthetical English translations in the main text. Rely on the context and the separate vocabulary list/glossary.

### Issue 3: Missing Primary Source Voice
- **Location**: Section "«Гетика» Йордана: Погляд ворога"
- **Original**: (Summary of Jordanes without a direct quote block)
- **Problem**: While Procopius and Maurikios have `> [!quote]` blocks that let the student "hear" the source, Jordanes—who provides the crucial account of Bozh's crucifixion—is only summarized. This creates an imbalance in the "Primary Sources" section.
- **Fix**: Add a `> [!quote]` block with an excerpt from "Getica" regarding the crucifixion of Bozh and the 70 elders to maintain consistency and impact.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 38 | «лягала в канву» | «відповідала духу» / «вписувалася в контекст» | Cliché/Calque |
| 26/127 | «Уявіть собі» (repeated) | (Vary the phrasing, e.g., «Згадаймо...», «Погляньмо на...») | Repetition |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

## Strengths
- **Decolonization Narrative**: The framing of the "Antean roots" vs "Soviet Cradle" is powerful and politically astute.
- **Visual Details**: The description of the underwater reed breathing tactic is memorable and engaging ("History Bite" quality).
- **Activity Design**: The "Essay Response" linking Procopius to modern Ukrainian democracy is excellent pedagogy.

## Fix Plan to Reach 9/10

### Immersion: 7/10 → 9/10
**What to fix:**
1. Global Find/Replace: Remove ` (English translation)` pattern from bolded terms in the body text.
2. Ensure bolded terms exist in the `vocabulary.yaml` (which needs expansion).

### Vocabulary: FAIL → PASS
**What to fix:**
1. Update `vocabulary.yaml` to include ALL required terms from the Plan (currently missing ~16 items).

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 28: Fix the sword contradiction.
2. Section "Jordanes": Add the missing direct quote.
3. Line 127: Change "Уявіть собі запах..." to "Запах диму... наповнював..." to avoid repetitive hook.

**Expected score after fix:** 9.2/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1 + 10×1 + 10×1.2 + 9.5×1.1 + 9×1.2 + 9×1 + 10×1.3 + 9.5×0.9 + 10×1.3 + 9×1 + 9.5×1.5) / 14 = 9.3/10
```

## Verification Summary

- Content lines read: 245
- Activity items checked: 5 activities
- Ukrainian sentences verified: ~110
- IPA transcriptions checked: 10
- Issues found: 3 Critical, 1 Plan Violation

## Verdict

**FAIL**

The module is narratively strong but fails on two blocking issues:
1.  **Plan Deviation**: The vocabulary file is missing >50% of the required terms listed in the plan.
2.  **Immersion Violation**: Excessive inline English translations disrupt the B2 Seminar experience.
3.  **Factual Contradiction**: The introduction claims swords were common, while the body text correctly states they were rare.

These must be fixed before the module can pass.
