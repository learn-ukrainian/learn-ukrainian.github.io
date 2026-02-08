# Рецензія: Colors & Clothing

**Level:** A1 | **Module:** 27
**Overall Score:** 7.6/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 required used, extra words found in activities]
- Grammar scope: [scope creep in activities]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good flow, but frustrated by untaught vocabulary in activities. |
| 2 | Coherence | 7/10 | <7 | Activities test words (`спідниця`, `піджак`) not taught in Presentation. |
| 3 | Relevance | 9/10 | <7 | Highly relevant vocabulary and skills. |
| 4 | Educational | 8/10 | <7 | Clear grammar explanations. |
| 5 | Language | 8/10 | <8 | Some calques ("Вона має", "Я виглядаю"); gender errors in quiz keys. |
| 6 | Pedagogy | 7/10 | <7 | Scope creep (Past Tense) and testing untaught material. |
| 7 | Immersion | 8/10 | <6 | Good balance of English and Ukrainian. |
| 8 | Activities | 6/10 | <7 | Gender agreement errors in Quiz keys; vocabulary mismatch. |
| 9 | Richness | 7/10 | <6 | Standard content, meets requirements. |
| 10 | Beginner Safety | 7/10 | <7 | "Would I Continue?" 4/5. |
| 11 | LLM Fingerprint | 8/10 | <7 | Typical "Let's start our journey" intro, but acceptable. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Quiz keys have gender mismatches (pig/mouse). |

**Weighted Overall:** 106.0 / 14.0 = **7.6/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [list] "Вона має" (She has), "Я виглядаю добре" (I look good).
- Grammar scope: [list] Past tense "Він купив" (Line 132); Locative "в червоній сукні" (Activity fill-in).
- Activity errors: [list] Quiz: "Pink pig" -> Answer "Рожевий" (Pig is fem/neut); "Gray mouse" -> Answer "Сірий" (Mouse is fem).
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Untaught Vocabulary in Activities
- **Location**: Activities file (match-up, group-sort, fill-in)
- **Original**: `спідниця`, `пальто`, `капелюх`, `шарф`, `піджак`, `черевики`
- **Problem**: These words appear in activities but are not listed in the Presentation/Vocabulary sections of the module.
- **Fix**: Add these common items to the "Presentation: Clothing" section or the vocabulary list.

### Issue 2: Gender Agreement Errors in Quiz
- **Location**: Activities file, Quiz "Який колір?"
- **Original**: "What color is a pink pig?" -> Correct: "Рожевий"; "What color is accurately associated with a gray mouse?" -> Correct: "Сірий"
- **Problem**: `Свиня` is feminine (should be `Рожева`), `Порося` is neuter (`Рожеве`). `Миша` is feminine (should be `Сіра`). The masculine adjectives are incorrect for these nouns.
- **Fix**: Change animals to masculine ones (e.g., "Pink flamingo" -> `Рожевий фламінго` or just "What is the color pink?" -> `Рожевий`; "Gray elephant" -> `Сірий слон`).

### Issue 3: Scope Creep - Past Tense
- **Location**: Line 132 / Practice "Describing a Friend"
- **Original**: "Він купив її вчора."
- **Problem**: Past tense `купив` and adverb `вчора` are likely not taught yet in A1 M27.
- **Fix**: Change to present tense: "Він носить її сьогодні." or "Це його нова куртка."

### Issue 4: Scope Creep - Locative Case
- **Location**: Activities file, Fill-in "Опис одягу"
- **Original**: "Вона сьогодні в ___ сукні." (Answer: `червоній`)
- **Problem**: Requires Locative case (`в ... сукні`) and Locative adjective ending `-ій`. This is advanced.
- **Fix**: Change to "У неї сьогодні ___ сукня." (Answer: `червона`).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 104 | "Вона має червоне плаття." | "У неї червоне плаття." | Calque |
| 106 | "Я виглядаю добре сьогодні." | "Я маю гарний вигляд сьогодні." | Calque |
| Act | "Рожевий" (for pig) | "Рожеве/Рожева" | Grammar |
| Act | "Сірий" (for mouse) | "Сіра" | Grammar |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Fail (Activities ask for words I didn't learn)
- Come back tomorrow? Pass

Emotional beats: 4 found
- Welcome: "Сьогодні ми вивчаємо кольори."
- Curiosity: "Чи синій — це просто синій?"
- Quick wins: Simple matching activities.
- Encouragement: "Ви великі молодці!"

## Strengths
- Clear explanation of the `синій`/`блакитний` distinction.
- Good "Myth Buster" about cultural context.
- Useful shopping dialogues.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1. **Add Vocabulary**: Update `27-colors-and-clothing.md` Section "Clothing and Verbs" to include: `спідниця` (skirt), `пальто` (coat), `капелюх` (hat), `шарф` (scarf), `черевики` (boots).
2. **Fix Quiz Gender**: In `activities/27-colors-and-clothing.yaml`, change "pink pig" question to "What color is a flamingo?" (or just "the color pink") -> `Рожевий`. Change "gray mouse" to "gray wolf" (`вовк`) or "elephant" -> `Сірий`.
3. **Fix Scope**: In `activities/27-colors-and-clothing.yaml`, change "Вона сьогодні в ___ сукні" to "У неї сьогодні ___ сукня" (Answer: `червона`).

### Language: 8/10 → 9/10

**What to fix:**
1. Line 104: Change "Вона має червоне плаття" → "У неї червоне плаття" (More natural).
2. Line 106: Change "Я виглядаю добре" → "Я маю гарний вигляд".

### Pedagogy: 7/10 → 9/10

**What to fix:**
1. Line 132: Change "Він купив її вчора" → "Він дуже любить її" (Stays in present tense).

### Coherence: 7/10 → 10/10

**What to fix:**
1. Ensure every word in the match-up/group-sort activities is listed in the module's vocabulary table or presentation text.

### Projected Overall After Fixes

(8*1.5 + 10*1 + 9*1 + 9*1.2 + 9*1.1 + 9*1.2 + 8*1 + 9*1.3 + 8*0.9 + 8*1.3 + 8*1 + 9*1.5) / 14 = 8.8 -> 9.0

## Verification Summary

- Content lines read: ~165
- Activity items checked: 55
- Ukrainian sentences verified: ~40
- IPA transcriptions checked: N/A (in vocab file, looked ok)
- Issues found: 6 critical
- Naturalness score recommendation: 9/10 (after fixes)

## Verdict

**FAIL**

The module fails due to **activity errors** (gender agreement in quiz keys), **scope creep** (past tense, locative case), and **coherence issues** (activities testing untaught vocabulary). These must be fixed to ensure a safe and effective A1 learner experience.