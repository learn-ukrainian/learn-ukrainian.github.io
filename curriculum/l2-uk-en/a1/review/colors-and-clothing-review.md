# Рецензія: Colors & Clothing

**Level:** A1 | **Module:** 27
**Overall Score:** 8.1/10
**Status:** PASS
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: Matches content coverage (Colors, Gender, Clothes, Nosyty, Shopping).
- Vocabulary: 23/25 from plan. Missing: "коричневий", "взуття".
- Grammar scope: PASS. Covers adjectives, nosyty, accusative, pluralia tantum.
- Objectives: PASS. All met.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Generally warm, but some metaphors are too abstract for A1 ("canvas for the soul"). |
| 2 | Coherence | 8/10 | <7 | Inconsistent terminology (плаття vs сукня). |
| 3 | Relevance | 10/10 | <7 | Very practical shopping skills. |
| 4 | Educational | 8/10 | <7 | Explanations are clear, but some activity items are untaught. |
| 5 | Language | 9/10 | <8 | "Плаття" is acceptable but "Сукня" is preferred standard. |
| 6 | Pedagogy | 7/10 | <7 | Testing untaught verb forms (plural "wear", "I buy"). |
| 7 | Immersion | 10/10 | <6 | 40% is appropriate for A1.3 transition. |
| 8 | Activities | 7/10 | <7 | "Phrase Building" includes untaught conjugation. |
| 9 | Richness | 9/10 | <6 | Good cultural notes (Vyshyvanka, symbolism). |
| 10 | Beginner Safety | 8/10 | <7 | Good pacing, but "Znahidnyi vidminok" terminology is borderline (though explained well). |
| 11 | LLM Fingerprint | 7/10 | <7 | "Painting a picture", "Music of words", "Canvas for the soul" - high metaphor density. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammatical errors found. |

**Weighted Overall:** 8.1/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [List] - Testing "Ми/Ви/Вони" forms of "носити" without teaching.
- Activity errors: [List] - "Phrase Building" requires untaught knowledge.
- Beginner Safety: 4/5

## Critical Issues Found

### Issue 1: Pedagogy / Scope Violation
- **Location**: Activities / "Phrase Building" & Content Section "The Art of Wearing"
- **Original**: Activity pairs: `left: "Ми носимо" right: "We wear"`, `left: "Ви носите" right: "You (pl) wear"`, `left: "Вони носять" right: "They wear"`.
- **Problem**: The content only teaches the singular forms ("Я ношу", "Ти носиш", "Він/Вона носить"). The plural forms are NOT introduced in the grammar table or text (except one example of "Ми носимо"). The learner cannot answer this activity based on the lesson.
- **Fix**: Add the plural forms to the grammar section or remove them from the activity.

### Issue 2: Vocabulary Inconsistency
- **Location**: Content / Various lines
- **Original**: «Чи є у вас зелене **плаття**?», «Вона носить біле **плаття**», «Я люблю чорне **плаття**».
- **Problem**: The Vocabulary YAML and the definitions list use **«сукня»**. The text mixes both. "Сукня" is the preferred standard term in this curriculum.
- **Fix**: Replace all instances of «плаття» with «сукня».

### Issue 3: LLM Fingerprint / Purple Prose
- **Location**: Section "The Language of Symbols" / Quote
- **Original**: «A clean white shirt is the canvas for the soul.»
- **Problem**: This is a high-abstraction metaphor typical of LLM "purple prose". It confuses beginners who might try to translate "canvas" or "soul".
- **Fix**: Simplify to: "White represents purity and new beginnings."

### Issue 4: Untaught Verb in Activity
- **Location**: Activities / "Complete the Dialogue"
- **Original**: Item: `- Я ___ їх. (купую)`
- **Problem**: The verb form **«купую»** (I buy) is not taught. The text uses "купувати" (infinitive) and "купуємо" (title), but the 1st person singular conjugation is not explicitly taught.
- **Fix**: Change the sentence to use a known verb, e.g., «Я **беру** їх» (if taught) or «Я **хочу** їх» (if taught), or simply teach "купую" in the "Shopping" section.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | «плаття» | «сукня» | Stylistic Choice |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

## Strengths
- **Cultural Context**: Excellent integration of Vyshyvanka and color symbolism.
- **Scaffolding**: The explanation of gender agreement using "painting" is helpful (despite the metaphor density).
- **Practicality**: The shopping dialogue is immediately useful.

## Fix Plan to Reach 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Section "The Art of Wearing": Add the full conjugation table for **носити** (include Ми, Ви, Вони).
2. Activities: Ensure all verbs in "Complete the Dialogue" (like *купую*) are introduced in the text.

### Coherence: 8/10 → 10/10
**What to fix:**
1. Content: Global find/replace «плаття» → «сукня» to match vocabulary list.

### LLM Fingerprint: 7/10 → 9/10
**What to fix:**
1. Section "The Language of Symbols": Remove "A clean white shirt is the canvas for the soul."
2. Section "The Art of Wearing": Remove "It can be a story." (Cliché).

**Expected score after fix:** 9.2/10

### Projected Overall After Fixes
9.2/10

## Verification Summary

- Content lines read: ~160
- Activity items checked: ~50
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: ~20
- Issues found: 4

## Verdict

**PASS**

The module is solid but needs cleanup on inconsistencies (плаття/сукня) and pedagogical scope (untaught verb forms).
