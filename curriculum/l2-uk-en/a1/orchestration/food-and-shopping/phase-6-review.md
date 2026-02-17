# Рецензія: Food, Drinks & Shopping

**Level:** A1 | **Module:** 18
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-16

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (Matches concept and Meta outline)
- Vocabulary: PASS (Required and Recommended words present)
- Grammar scope: PASS (Accusative and Genitive covered appropriately)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Tone is good, but jarred by factual/grammar errors. |
| 2 | Coherence | 9/10 | <7 | Logical flow and progression. |
| 3 | Relevance | 10/10 | <7 | Highly practical vocabulary for daily life. |
| 4 | Educational | 7/10 | <7 | IPA polluted with Cyrillic characters; grammar mismatch. |
| 5 | Language | 8/10 | <8 | Some calques ("makes shopping easy"). |
| 6 | Pedagogy | 9/10 | <7 | Good scaffolding and clear tables. |
| 7 | Immersion | 10/10 | <6 | 39% (Target 25-40%). Excellent balance. |
| 8 | Activities | 6/10 | <7 | Logic error in "Vegetable or Fruit" (Chicken is neither). |
| 9 | Richness | 8/10 | <6 | Good cultural notes, but one contains a hallucination. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. |
| 11 | LLM Fingerprint | 8/10 | <7 | Minor structural repetition, generally okay. |
| 12 | Linguistic Accuracy | 6/10 | <9 | Subject-verb mismatch, mixed Cyrillic in IPA. |

**Weighted Overall:** 112.7 / 14.0 = **8.05/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [LIST] "Це робить покупки легкими", "Ми маємо"
- Grammar scope: [CLEAN]
- Activity errors: [LIST] Chicken in Veggie/Fruit quiz; Broken MD display for Group Sort.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Linguistic Accuracy (IPA)
- **Location**: Throughout the module (e.g., Lines 110, 126, 142)
- **Original**: «[prɔ.ˈduk.тɪ]», «[ˈkur.кa]», «[ba.ˈтɔn]»
- **Problem**: The IPA transcriptions use Cyrillic characters `т` and `к` instead of Latin `t` and `k`. This renders the IPA invalid and confusing for tools/learners.
- **Fix**: Replace all Cyrillic homoglyphs in IPA with Latin characters.

### Issue 2: Grammar (Subject-Verb Mismatch)
- **Location**: Line 124 / Section "М'ясо та молочні продукти"
- **Original**: «Тепер ми йдете у магазин.»
- **Problem**: Mismatch between subject «ми» (we) and verb «йдете» (you go - plural).
- **Fix**: Change to «Тепер ми йдемо у магазин.» (Now we go...) or «Тепер ви йдете...» (Now you go...). Given context "Now *we* go...", use «йдемо».

### Issue 3: Cultural/Factual Error
- **Location**: Line 223 / Section "Українські традиції"
- **Original**: «Булочки не мають часник.»
- **Problem**: This statement regarding pampushky is factually confusing or incorrect. Pampushky are famous specifically *for* their garlic sauce. Saying they "do not have garlic" (even if technically meaning "inside the dough") contradicts the primary cultural association. Also, «не мають часник» uses Accusative instead of Genitive of negation («не мають часнику»).
- **Fix**: «Ці булочки подають з часником.» (These buns are served with garlic.)

### Issue 4: Activity Logic
- **Location**: Activity "quiz: Vegetable or Fruit?" / Item 5
- **Original**: «5. курка [ˈкʊrkɐ] - (овоч / м'ясо)»
- **Problem**: The instruction asks to decide if the item is a "Vegetable or Fruit". Item 5 is "Chicken". The inline options show `(овоч / м'ясо)`, but this violates the binary constraint of the instruction "Vegetable or Fruit".
- **Fix**: Remove "Chicken" from this specific quiz or change the quiz to "Food Categories".

### Issue 5: Linguistic Accuracy (IPA Error)
- **Location**: Line 116
- **Original**: «[tsɛ ˈdu.ʒɛ ˈsmantʃ.nɔ]»
- **Problem**: The IPA for «смачно» includes an intrusive `n` (`smantʃ`). There is no nasal `n` before `ch` in this word.
- **Fix**: «[ˈsmatʃ.nɔ]»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 124 | «ми йдете» | «ми йдемо» | Grammar |
| 152 | «Це робить покупки легкими» | «Це спрощує покупки» | Calque |
| 223 | «не мають часник» | «не мають часнику» | Grammar/Scope |
| 116 | «[ˈsmantʃ.nɔ]» | «[ˈsmatʃ.nɔ]» | IPA Error |
| All | «[...т...к...]» | «[...t...k...]» | IPA/Encoding |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass
- Come back tomorrow? Pass

## Strengths
- **Practical Utility**: The vocabulary is immediately useful for a learner engaging in real life.
- **Scaffolding**: The verb tables and clear explanations of Accusative case are very helpful.
- **Immersion**: Great balance of English explanation and Ukrainian examples.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 6/10 → 9/10
**What to fix:**
1. **Global IPA Clean-up**: Run a script or Find/Replace to ensure all `т` are `t` and all `к` are `k` within brackets `[...]`.
2. **Line 116**: Fix «[ˈsmantʃ.nɔ]» to «[ˈsmatʃ.nɔ]».
3. **Line 124**: Change «ми йдете» to «ми йдемо».

### Activities: 6/10 → 9/10
**What to fix:**
1. **Activity "Vegetable or Fruit"**: Replace item 5 "курка" with a fruit like "слива" or vegetable like "цибуля" to fit the binary choice.
2. **Group Sort**: Ensure the markdown rendering matches the logical structure (currently looks like a list of questions in MD view).

### Richness/Culture: 8/10 → 9/10
**What to fix:**
1. **Line 223**: Rewrite the Pampushky note. Instead of "The buns do not have garlic", write "Українці люблять пампушки з часником" (Ukrainians love pampushky with garlic).

**Expected score after fix:** 9.2/10

### Projected Overall After Fixes
```
(8*1.5 + 9 + 10 + 9*1.2 + 9*1.1 + 9*1.2 + 10 + 9*1.3 + 9*0.9 + 9*1.3 + 8 + 9*1.5) / 14 = 9.1/10
```

## Verification Summary

- Content lines read: 260
- Activity items checked: 60
- Ukrainian sentences verified: ~45
- IPA transcriptions checked: ~30
- Issues found: 5 Major

## Verdict

**FAIL**

The module is structurally sound and pedagogically strong, but it fails due to **widespread IPA encoding errors** (Cyrillic homoglyphs), a glaring **grammar mismatch** ("ми йдете"), a **cultural hallucination** regarding pampushky, and a **logical error** in the activity design. These must be fixed before publication.
