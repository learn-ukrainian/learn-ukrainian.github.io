I've read all source files. Now performing a deep adversarial review.

---

## Adversarial QA Review: a1-11 — The Accusative I: Things

### Systematic Check Results

**IPA Accuracy:** All 35+ IPA transcriptions verified. Correct use of `[ʋ]` for В (not `[w]`), `[t͡ʃ]` for Ч, `[t͡s]` for Ц with tie bars throughout. Stress placement verified on all polysyllabic items. No errors found.

**Russianisms:** CLEAN. "Брати участь" (not "приймати участь"). No кушати, получати, слідуючий.

**Russian characters (ы, э, ё, ъ):** CLEAN. None detected.

**Gender/case agreement:** All Ukrainian sentences verified correct. Dialogue case endings correct (Газовану воду, Чорну шоколадку, Яку ідею — all accusative agreement correct).

**Unjumble activities:** All 16 items verified — `words` arrays contain exactly the words in `answer`, no missing words or punctuation.

**Fill-in activities:** All 24 items produce grammatical sentences when `answer` is inserted. All options are real Ukrainian forms (correct distractors from other cases).

**Quiz activities:** All 20 items have exactly one correct answer. Correct answers verified linguistically.

**Activity YAML structure:** Bare list at root (no `activities:` wrapper). Correct.

**Plan compliance:** All 5 plan sections present in prose. All 11 required vocabulary items used in prose and present in vocab file. All 4 objectives map to self-check questions in the summary.

**LLM artifacts:** No purple prose. No "Це не просто X, а Y" pattern. No folk etymology. No invented statistics. The tone is appropriately warm for A1 without being grandiose.

**Factual accuracy:** Гречка as panic-buy staple — accurate (well-documented during 2014, 2020, 2022 crises). "Пакет потрібен?" — authentic checkout phrase. Булава as Cossack hetman symbol — correct. Bazaar culture description — accurate.

### Issues Found

**Issue 1: Pedagogical trap — "можливість" without clarification (MEDIUM)**

**File:** `curriculum/l2-uk-en/a1/the-accusative-i-things.md`, line 245

The "Using Мати" practice section shows three examples:
- `Я маю ідею` — annotated: *ідея → ідею*
- `Я маю план` — annotated: *план → план (Masculine, no change)*
- `Я маю можливість` — **no annotation**

"Можливість" is feminine but ends in a consonant (-ість), not -а/-я. By the module's own rule, only feminines ending in -а/-я change. But a student seeing this unannotated third-declension feminine sitting alongside an annotated masculine "no change" example will reasonably wonder: "Is можливість masculine? Or did the author forget to change it?" The conspicuous absence of an annotation — when the other two items have them — is a genuine confusion risk at A1.

**Fix:** Add a brief annotation explaining this is feminine but consonant-ending (not -а/-я), so it stays unchanged.

**Issue 2: Green Team phantom issue (NOTE)**

The Green Team review claims IPA is missing for диню, грушу, капусту, сметану in the Cultural section. This is **incorrect** — all four items have IPA at lines 373-376. The Green Team review has a phantom Issue 1. No fix needed; noting for record.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/the-accusative-i-things.md
---OLD---
*   **Я маю можливість**. (I have an opportunity.)
---NEW---
*   **Я маю можливість**. (I have an opportunity.) — *можливість → можливість* (Feminine, but ends in a consonant, not -а/-я — no change!)
---
===FIX_END===

---

### Summary

| Check | Result |
|:------|:-------|
| IPA accuracy | PASS (35+ items, all correct) |
| Russianisms | PASS (clean) |
| Russian chars | PASS (clean) |
| Grammar/case correctness | PASS |
| Activity correctness | PASS (92 items, all verified) |
| Unjumble word arrays | PASS (16/16 match) |
| Plan compliance | PASS (all sections, vocab, objectives) |
| Factual accuracy | PASS |
| LLM artifacts | PASS (none detected) |
| Pedagogical safety | 1 fix applied (можливість clarification) |

Total issues: 1 real (fixed above), 0 blocking. This is a strong module with clear pedagogy, accurate Ukrainian, well-designed activities, and authentic cultural content. The "Safe Harbor" metaphor and "Wizard" mnemonic are pedagogically effective. The single fix prevents a subtle but real confusion point for A1 learners encountering a third-declension feminine for the first time.

===VERDICT===
APPROVE
===END_VERDICT===