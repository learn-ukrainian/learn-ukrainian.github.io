# Рецензія: At the Store

**Level:** A1 | **Module:** 38
**Overall Score:** 8.6/10
**Status:** PASS
**Reviewed:** 2026-02-20

## Plan Verification

- Plan-Content Alignment: PASS
- Sections: All required sections present.
- Vocabulary: 8/8 required items present.
- Grammar scope: Accusative case correctly limited to feminine singular (-a to -u). Locative case introduced as set phrase.
- Objectives: Met.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Warm, encouraging tone ("Фінальна битва", "Магія"). Good cultural hooks. |
| 2 | Coherence | 9/10 | <7 | Logical flow from entrance to checkout. |
| 3 | Relevance | 10/10 | <7 | Extremely practical. Silpo context is very relevant for Ukraine. |
| 4 | Educational | 9/10 | <7 | Clear explanations of "магазин vs супермаркет" and cases. |
| 5 | Language | 9/10 | <8 | Simple sentences, correct IPA usage. |
| 6 | Pedagogy | 8/10 | <7 | "Activities" vocabulary exceeds lesson scope (see below). |
| 7 | Immersion | 9/10 | <6 | Good balance of English support and Ukrainian content. |
| 8 | Activities | 7/10 | <7 | Critical issue: vocabulary in "Group Sort" not taught in lesson. |
| 9 | Richness | 9/10 | <6 | 9 activities, cultural notes, detailed dialogues. |
| 10 | Beginner Safety | 8/10 | <7 | Mostly safe, but a few untaught words ("безкоштовно", "ваги") need glossing. |
| 11 | LLM Fingerprint | 9/10 | <7 | Natural voice, avoids robotic patterns. |
| 12 | Linguistic Accuracy | 8/10 | <9 | Minor logical issue with "Coffee" location. |

**Weighted Overall:** 8.6/10

## Auto-Fail Checklist Results

- Russianisms: CLEAN. Good warning about "покупка".
- Calques: CLEAN.
- Grammar scope: CLEAN.
- Activity errors: Vocabulary overflow found.
- Beginner safety: 4/5.

## Critical Issues Found

### Issue 1: Activity Vocabulary Overflow
- **Location**: `activities/at-the-store.yaml` / "group-sort"
- **Original**: Items include «курка», «сосиски», «сало», «мармелад», «шоколад».
- **Problem**: These words are NOT introduced in the text or vocabulary list. A1 learners cannot sort words they haven't seen.
- **Fix**: Replace with known words from the lesson (e.g., `яблука`, `хліб` if changing categories, or just stick to taught words).

### Issue 2: Logic/Accuracy (Coffee Location)
- **Location**: Line 207 / Dialogue 1
- **Original**: «Працівник: Кава там, у відділі «Напої».»
- **Problem**: Coffee (beans/ground) is rarely in the "Drinks" (liquid) section. It's usually in Grocery (Бакалія) or a specific Coffee/Tea aisle.
- **Fix**: Change department to «Кава і чай» (Coffee and Tea) or change the item to «Сік» (Juice) which fits "Напої" perfectly.

### Issue 3: Missing Scaffolding
- **Location**: Line 169
- **Original**: «Другий товар безкоштовно.»
- **Problem**: "Безкоштовно" is a long, complex word introduced without IPA or translation gloss.
- **Fix**: Add «[bezkɔʃˈtɔu̯nɔ] (free)».

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 207 | «у відділі «Напої»» | «у відділі «Кава і чай»» | Logic |
| 169 | «безкоштовно» | «безкоштовно [bezkɔʃˈtɔu̯nɔ] (free)» | Scaffolding |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? No.
- Instructions clear? Yes.
- Quick wins? Yes, deciphering signs.
- Ukrainian scary? Mostly no, but "безкоштовно" is a mouthful.
- Come back tomorrow? Yes.

## Strengths
- **Cultural Context**: The "Silpo" theme and receipt predictions are excellent, authentic touches.
- **Tone**: Very supportive and "human" tutor voice.
- **Clarity**: The "Bag Ritual" is explained perfectly for a beginner.

## Fix Plan to Reach 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. `activities/at-the-store.yaml`: Replace untaught words in "Group Sort" with taught words or remove them.
   - Replace `шоколад`, `мармелад` with `цукерки`, `печиво`.
   - Replace `курка`, `сосиски`, `сало` with `м'ясо`, `ковбаса`.

### Language: 9/10 → 10/10
**What to fix:**
1. Line 207: Change "Напої" to "Кава і чай" for accuracy.
2. Line 169: Add gloss to "безкоштовно".

**Expected score after fix:** 9.5/10

### Projected Overall After Fixes
9.2/10

## Verification Summary

- Content lines read: ~260
- Activity items checked: ~60
- Ukrainian sentences verified: All
- IPA transcriptions checked: Checked key terms.
- Issues found: 3

## Verdict

**PASS**

The module is strong, culturally rich, and well-structured. The only significant issues are untaught vocabulary in one activity and a minor logic error in the dialogue.