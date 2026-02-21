Good — the Green Team's two previous issues ("візьму" and "повинні купити хліб" in the wrong section) are already resolved in the current version. Now I proceed with my own adversarial review.

---

## Adversarial QA Review: can-must-want-modals (a1-24)

### Issues Found

**Issue 1: SPELLING — Missing apostrophe in "прислів'я"**
- **File:** `can-must-want-modals.md`, line 391
- **Current:** `Це український аналог прислівя "Where there's a will, there's a way".`
- **Problem:** "прислівя" is misspelled. The correct Ukrainian spelling is **прислів'я** (with an apostrophe before я). The apostrophe is mandatory after labial consonants (б, п, в, м, ф) before я/ю/є/ї per Ukrainian orthography.
- **Severity:** Medium — spelling error in Ukrainian target-language text

**Issue 2: RUSSICISM — "поміряти" should be "приміряти"**
- **File:** `can-must-want-modals.md`, line 351
- **Current:** `— Добрий день. **Можна** поміряти цю сорочку? (Good day. May I try on this shirt?)`
- **Problem:** "Поміряти" in the meaning "to try on clothing" is a Russian calque (from Rus. померить/померять). Standard Ukrainian uses **приміряти** for trying on clothes. "Поміряти" in Ukrainian properly means "to measure." A curriculum module teaching correct Ukrainian must use the standard form.
- **Severity:** High — Russicism in target-language dialogue

**Issue 3: MINOR PEDAGOGICAL — мусити tested in activities but explicitly scoped out**
- **File:** `can-must-want-modals.yaml`, lines 141-147 (fill-in item 8)
- **Current:** The fill-in activity tests `"Я _____ (мусити) йти"` → answer: `"мушу"`
- **Problem:** The module text (line 171) explicitly says: *"At the A1 stage, use 'треба' and 'повинен'."* Testing мусити conjugation in a scored activity contradicts this guidance. The meta's content_outline says "Brief mention" — mention ≠ test.
- **Severity:** Low — pedagogical inconsistency, not a blocker. The learner encounters mixed signals (told it's optional, then quizzed on it). Leaving as-is because it provides useful exposure and the fill-in is recognition-level, not production-level.

### Verified Clean

- **IPA transcriptions:** All 15 IPA entries checked. Correct use of ʋ (not w) for В, proper stress placement, correct vowel qualities. No affricates needed in this module's vocabulary.
- **Russian characters (ы, э, ё, ъ):** None found.
- **Russianisms scan:** Clean except Issue 2 above. No кушати, получати, приймати участь, слідуючий.
- **Gender/case agreement:** All потрібен/потрібна/потрібне/потрібні examples correct. Повинен/повинна/повинно/повинні table correct.
- **Verb conjugation tables:** могти (г→ж alternation) correct. вміти correct. All forms verified.
- **Plan compliance:** All 4 plan sections present. All 8 required vocabulary items used in prose. All 4 objectives addressed. Grammar scope respected (no future imperfective, no conditional).
- **Meta compliance:** All 10 meta content_outline sections present with matching headers.
- **Unjumble activities:** All 6 items verified — words arrays contain exactly the tokens in the answer strings, including punctuation.
- **Fill-in activities:** All 16 items verified — inserting each answer produces a grammatical Ukrainian sentence.
- **Quiz activities:** All 22 items verified — correct answers are correct, distractors are plausible but wrong.
- **Match-up:** All 8 pairs correct.
- **True-false:** All 8 statements have correct boolean values.
- **Group-sort:** All 12 items correctly categorized.
- **LLM artifacts:** No purple prose. No "Це не просто X, а Y" pattern. No folk etymology. No invented statistics. Opening is slightly metaphorical but appropriate for A1 tone.
- **Green Team prior issues:** Both previously identified issues (візьму scope creep, повинні grouping error) already resolved in current version.
- **Factual claims:** Proverb «Хто хоче — той може» is authentic Ukrainian. Cultural note about "Можна?" as universal politeness key is accurate.
- **Word target:** Content is well over 2000 words. No shortfall.

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/can-must-want-modals.md
---OLD---
Це український аналог прислівя "Where there's a will, there's a way".
---NEW---
Це український аналог прислів'я "Where there's a will, there's a way".
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/can-must-want-modals.md
---OLD---
— Добрий день. **Можна** поміряти цю сорочку? (Good day. May I try on this shirt?)
---NEW---
— Добрий день. **Можна** приміряти цю сорочку? (Good day. May I try on this shirt?)
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Summary:** Two real issues found and fixed — a missing apostrophe in "прислів'я" (spelling) and a Russicism "поміряти" → "приміряти" (trying on clothes). Both are clean surgical fixes. One minor pedagogical note (мусити tested despite being scoped out) left as-is because it's recognition-level exposure, not a blocker. The module is otherwise strong: well-structured, plan-compliant, activities are diverse and error-free, IPA is correct, no scope creep, good cultural integration.