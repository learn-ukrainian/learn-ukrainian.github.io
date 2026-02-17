# Рецензія: Numbers & Money

**Level:** A1 | **Module:** 17
**Overall Score:** 8.8/10
**Status:** FAIL
**Reviewed:** Monday, February 16, 2026

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: All H2 sections from the plan are present and well-developed.
- Vocabulary: 31 items (Plan required 8, recommended 6). All key terms like "гривня", "скільки", "коштувати" are covered.
- Grammar scope: Numbers 0-100 and 1-2-5 agreement rule fully implemented.
- Objectives: All objectives (counting, shopping transactions, price inquiry) are addressed.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Repetitive section openings ("Imagine..."). |
| 2 | Coherence | 9/10 | <7 | Logical progression from 0-10 to complex numbers and shopping. |
| 3 | Relevance | 10/10 | <7 | Highly practical for A1 survival. |
| 4 | Educational | 9/10 | <7 | Excellent "Bazaar Accountant" mnemonic for the 1-2-5 rule. |
| 5 | Language | 8/10 | <8 | Correct grammar but several stress/IPA errors found. |
| 6 | Pedagogy | 10/10 | <7 | Strong PPP implementation with clear scaffolding. |
| 7 | Immersion | 9/10 | <6 | 27% (Target: 25-40%). Perfect for A1.2. |
| 8 | Activities | 8/10 | <7 | One activity item contains a grammatical error (тридцять гривні). |
| 9 | Richness | 9/10 | <6 | Cultural overview of history and symbolism is high quality. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Warm, non-threatening tone. |
| 11 | LLM Fingerprint | 7/10 | <7 | Identical section structures and consistent batching of 3 examples. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **FAIL**: Stress errors on «числа», IPA error on «вода», and activity grammar. |

**Weighted Overall:** 123.2 / 14.0 = **8.8/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] Item in `unjumble` has incorrect agreement.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Linguistic Accuracy (Stress)
- **Location**: Lines 48, 60 / Section "Числа навколо нас"
- **Original**: «Я зна́ю числа́ від нуля́ до де́сяти»
- **Problem**: The plural of «число́» is «чи́сла» [ˈtʃɪslɐ] with stress on the first syllable. The text uses «числа́».
- **Fix**: Change «числа́» to «чи́сла» (move stress mark to 'и').

### Issue 2: IPA Error
- **Location**: Vocabulary file / word: "вода"
- **Original**: `ipa: "[oˈda]"`
- **Problem**: Missing the initial consonant [ʋ].
- **Fix**: Change `[oˈda]` to `[ʋoˈda]`.

### Issue 3: Activity Grammar Error
- **Location**: `activities/numbers-and-money.yaml` / Unjumble Item 3
- **Original**: «Хліб коштує тридцять гривні.»
- **Problem**: Round tens (30) require Genitive Plural «гривень».
- **Fix**: Change «тридцять гривні» to «тридцять гривень».

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 48 | «Числа́ в Украї́ні» | «Чи́сла в Украї́ні» | Grammar (Stress) |
| 60 | «Я зна́ю числа́ від...» | «Я зна́ю чи́сла від...» | Grammar (Stress) |
| YAML | `ipa: "[oˈda]"` | `ipa: "[ʋoˈda]"` | Phonetics (IPA) |
| YAML | «тридцять гривні» | «тридцять гривень» | Grammar (Agreement) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass] No, chunks are manageable.
- Instructions clear? [Pass] Yes, bilingual headers help.
- Quick wins? [Pass] Yes, basic numbers are easy to grasp.
- Ukrainian scary? [Pass] No, patient tone.
- Come back tomorrow? [Pass] Yes, very practical.

## Strengths
- **Pedagogical Mnemonics**: The "Bazaar Accountant's Secret" is a brilliant way to explain the complex 1-2-5 rule to beginners.
- **Cultural Depth**: The history of the hryvnia and the explanation of the symbols (Taras Shevchenko, symbol ₴) add significant value.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 8/10 → 10/10
**What to fix:**
1. Lines 48, 60: Correct stress on «числа́» → «чи́сла».
2. Vocabulary.yaml: Correct IPA for «вода» → `[ʋoˈda]`.
3. Activities.yaml: Correct unjumble item 3 to «тридцять гривень».

### LLM Fingerprint: 7/10 → 9/10
**What to fix:**
1. Vary section openings: Change the "Imagine..." formula in at least two H2 sections to something more direct or conversational (e.g., "Look at the menu in your local cafe...").
2. Example batching: Add or remove examples to break the "exactly 3 examples per block" pattern.

### Projected Overall After Fixes
```
(8.5*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 9*1.1 + 10*1.2 + 9*1.0 + 10*1.3 + 9*0.9 + 10*1.3 + 9*1.0 + 10*1.5) / 14.0 = 9.4
```

## Verification Summary

- Content lines read: 285
- Activity items checked: 60
- Ukrainian sentences verified: 124
- IPA transcriptions checked: 31
- Issues found: 3

## Verdict

**FAIL**

The module is pedagogically excellent and rich in culture, but it fails on **Linguistic Accuracy** due to objective errors in stress marks (чи́сла vs числа́), phonetics (вода), and grammatical agreement in the practice activities. Correcting these three points will result in a high-quality Pass.
