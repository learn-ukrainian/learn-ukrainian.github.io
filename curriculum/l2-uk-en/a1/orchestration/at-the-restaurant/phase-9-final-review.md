Now let me do the detailed adversarial analysis. I've read all files. Let me compile findings.

---

## Adversarial QA Review: at-the-restaurant (a1-36)

**Word count:** 3044 words (target: 2000) — well exceeds minimum. ✅

---

### Issues Found

**Issue 1 (Pedagogical Contradiction): Match-up "Кафе" = "Місце для кави та розмов"**
- **File:** `activities/at-the-restaurant.yaml`, line 496–497
- **Problem:** The content at line 48–50 explicitly teaches: "A кафе is a casual place where you can eat a full meal. This establishment is not just for coffee!" But the match-up activity reinforces the exact misconception the prose combats — matching Кафе to "Місце для кави та розмов" (Place for coffee and conversations). This is a direct pedagogical contradiction.
- **Fix:** Change to "Місце для обіду та кави" (Place for lunch and coffee) — acknowledges the eatery function first.

**Issue 2 (Plan Compliance): Missing бронювати**
- **File:** `at-the-restaurant.md`, section "Крок 1: Резервація"
- **Problem:** The plan source of truth (line 27–29) explicitly requires: "Distinguish between the collocations «бронювати» (specifically for booking tables/reservations) and «замовити»." The content only uses "замовити столик". The verb бронювати — which is the more specific reservation verb — is never mentioned.
- **Fix:** Add a brief note in Крок 1 mentioning бронювати as an alternative.

**Issue 3 (Activity — Untaught Vocabulary): "порція" in match-up**
- **File:** `activities/at-the-restaurant.yaml`, line 27–28
- **Problem:** The word "порція" (portion) appears in the first match-up activity but is never introduced, used, or explained anywhere in the lesson prose. A learner encounters it cold.
- **Fix:** Remove the pair from the match-up (11 pairs is still rich) since adding it to prose would be padding.

**Issue 4 (IPA Mismatch): сметаною with nominative IPA**
- **File:** `at-the-restaurant.md`, line 157
- **Current:** `зі сметаною [smɛˈtɑnɐ]`
- **Problem:** The IPA transcribes the nominative form (сметана), but it's placed directly after the instrumental form (сметаною). At A1, this creates confusion — the learner thinks `[smɛˈtɑnɐ]` is how you pronounce "сметаною".
- **Fix:** Introduce the word in nominative with IPA, then use the inflected form.

**Issue 5 (Formatting): Proverb missing dash**
- **File:** `at-the-restaurant.md`, line 397
- **Current:** `«Хліб усьому голова»`
- **Problem:** The standard form of this proverb uses an em-dash: «Хліб — усьому голова». Missing it is a formatting error in a cultural citation.

**Issue 6 (Verified Green Team False Alarm): "Дайте, будь ласка, меню"**
- The Green team flagged this as "blunt". **I disagree.** "Дайте, будь ласка, меню" is perfectly natural polite Ukrainian with the imperative softened by "будь ласка". This is standard and does NOT need removal. No fix.

**Issue 7 (Verified Green Team Fix Already Applied): "Офіціанте" → "Перепрошую"**
- Dialogue 3 (line 298) already uses "Перепрошую" — the Green team's fix was either already applied or was never needed in this version. No action needed.

### Items Verified Clean
- **IPA accuracy:** All transcriptions use ʋ (not w) for В, ɦ (not g) for Г, tie bars on all affricates (t͡s, t͡ʃ, ʃt͡ʃ). ✅
- **No Russianisms in content.** «Счёт» appears only in the myth-buster warning box — intentional pedagogical use. ✅
- **No Russian characters** (ы, э, ъ) in content. The ё in «счёт» is in a clearly-marked Russian example. ✅
- **Gender/case agreement:** All checked — борщ (masc.), каву (fem. Acc.), картоплю (fem. Acc.), свіжа риба, ніжна риба, гостра страва — all correct. ✅
- **Fill-in activities:** All 16 items produce grammatical sentences with correct case forms. ✅
- **Unjumble activities:** All 12 items — words arrays contain exactly the words in the answers. ✅
- **Factual accuracy:** Three-course structure, tipping norms, proverbs, Будьмо semantics, cloakroom etiquette — all accurate. ✅
- **No LLM artifacts:** No purple prose, no "Це не просто X, а Y" overuse, no invented statistics. ✅
- **All plan objectives** covered with matching self-check questions. ✅
- **All required vocabulary** from plan used in prose. ✅

---

### Fixes

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/at-the-restaurant.yaml
---OLD---
    - left: 'Кафе'
      right: 'Місце для кави та розмов'
---NEW---
    - left: 'Кафе'
      right: 'Неформальне місце для обіду'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/at-the-restaurant.yaml
---OLD---
    - left: 'порція'
      right: 'portion'
---NEW---
---
===FIX_END===

Wait — the empty replacement would break YAML. Let me remove the full pair properly.

===FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/at-the-restaurant.yaml
---OLD---
    - left: 'гарнір'
      right: 'side dish'
    - left: 'порція'
      right: 'portion'
---NEW---
    - left: 'гарнір'
      right: 'side dish'
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-restaurant.md
---OLD---
*   **Замовити** [zɐˈmɔʋɪtɪ] — to order / to book.

*   *Example:* «Добрий день. Я хотів би замовити столик на сьому годину.» (Good day. I would like to book a table for 7:00.)
---NEW---
*   **Замовити** [zɐˈmɔʋɪtɪ] — to order / to book.
*   **Забронювати** [zɐbrɔnʲuˈʋɑtɪ] — to reserve (specifically for tables and rooms).

> [!tip]
> **Замовити чи забронювати?**
> Both work for booking a table. «Забронювати столик» is more specific (reserve), «замовити столик» is more universal (order/book). In everyday speech, both are equally common.

*   *Example:* «Добрий день. Я хотів би замовити столик на сьому годину.» (Good day. I would like to book a table for 7:00.)
---
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-restaurant.md
---OLD---
*   **Деруни** [dɛˈrunɪ] — це млинці з картоплі. Дуже смачно зі сметаною [smɛˈtɑnɐ].
---NEW---
*   **Деруни** [dɛˈrunɪ] — це млинці з картоплі. Дуже смачно зі **сметаною** (< **сметана** [smɛˈtɑnɐ] — sour cream).
===FIX_END===

===FIX_START===
FILE: curriculum/l2-uk-en/a1/at-the-restaurant.md
---OLD---
*   **«Хліб усьому голова»** — Bread is the head of everything.
---NEW---
*   **«Хліб — усьому голова»** — Bread is the head of everything.
===FIX_END===

---

===VERDICT===
APPROVE
===END_VERDICT===

**Summary:** The module is strong — culturally rich, pedagogically sound, exceeds word target by 50%, and has clean Ukrainian throughout. Five issues found: one pedagogical contradiction in activities (Кафе misconception reinforced), one plan compliance gap (missing бронювати/забронювати), one untaught word in activities (порція), one IPA-form mismatch, and one proverb formatting issue. All fixed above. No Russianisms, no broken activities, no factual errors. After these fixes, the module is ready for production.