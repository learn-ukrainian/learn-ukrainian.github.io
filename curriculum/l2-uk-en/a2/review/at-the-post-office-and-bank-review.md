<!-- content-hash: af067fd64467 -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Key Evidence |
|---|-----------|-------|-------------|
| 1 | Lesson Quality | 8/10 | Functional but cold — zero "Great!/Well done" quick-wins, zero "Don't worry" moments, only 1 "You are now" marker at line 272. 3/5 on "Would I Continue?" test. |
| 2 | Language | 7/10 | Grammatical error «щоден життя» (line 22, must be «щоденне життя»); IPA error in vocab file: `[ʍklɑˈdɑtɪ]` for вкладати (line 110 of vocab YAML, should be `[ʋklɑˈdɑtɪ]`); unnatural example «Це мій старий білий лист.» (line 58) |
| 3 | Immersion | 9/10 | 50.2% well within the 50-60% target. Good English/Ukrainian balance for A2 Band 1. |
| 4 | Activity Quality | 7/10 | Quiz "Ввічливі прохання" (activities YAML lines 30-143): all 10 items test the same binary хотів/хотіла gender distinction — extreme monotony. Other 11 activities are well-designed. |
| 5 | Richness | 7/10 | Plan explicitly requires Monobank, Privat24, and QR codes (plan lines 42, 15-16); all three are completely absent from content. Named Ukrainian cultural references are thin. |
| 6 | LLM Fingerprint | 7/10 | «дуже» appears 15 times across prose — filler padding. Many Ukrainian paragraphs stack short declarative sentences in identical rhythm. "In this module, we will learn" (line 16) is a generic AI opener. |
| 7 | Factual Accuracy | 9/10 | Grammar rules accurate; stamp cultural hook correct; numbers 100-1000 correct. No fabricated claims. |

**Weighted Average: 7.7/10**

---

## Critical Issues Found

### Issue 1: CRITICAL — Grammatical Error in Ukrainian Prose (line 22)

**Location:** Section «Вступ: Світ послуг в Україні», line 22

**Evidence:** «Це робить щоден життя набагато простішим і комфортнішим.»

"Щоден" is not a valid Ukrainian word form. The adjective must agree with "життя" (neuter gender) → **«щоденне»**. This is a morphological truncation error.

**Fix:** Replace «щоден життя» → «щоденне життя» on line 22.

---

### Issue 2: CRITICAL — IPA Error in Vocabulary File (vocab YAML line 110)

**Location:** Vocabulary file, entry for "вкладати"

**Evidence:** `ipa: '[ʍklɑˈdɑtɪ]'`

The symbol `ʍ` is the voiceless labial-velar approximant (English "wh-"). This phoneme does not exist in Ukrainian. The correct initial consonant is `ʋ` (voiced labiodental approximant). Should be `[ʋklɑˈdɑtɪ]`.

**Fix:** Replace `ʍ` → `ʋ` in the IPA for вкладати.

---

### Issue 3: MAJOR — Plan Compliance Gap: Missing Monobank/Privat24/QR References

**Location:** Sections «Вступ: Світ послуг в Україні» and «Банківські операції та цифрова екосистема»

**Evidence:** The plan (plan YAML lines 15-16 and 42) explicitly requires:
- "Cultural motivator: Overview of Ukraine's leading digital banking ecosystem (Monobank/Privat24)"
- "The role of QR codes and instant transfers in daily Ukrainian life (Monobank context)"

Grep confirms zero occurrences of "Monobank", "Privat24", or "QR" in the content. The prose discusses digital banking generically (line 118: «Банківська система нашої країни є однією з найсучасніших») but never names the specific apps or technologies.

**Fix:** Add named references to Monobank and Privat24 in section «Банківські операції та цифрова екосистема» (around lines 118-124). Add QR code reference in section «Цифрова екосистема України» (around line 149-158).

---

### Issue 4: MAJOR — Quiz Activity Extreme Monotony (activities YAML lines 30-143)

**Location:** Activity "Ввічливі прохання: оберіть правильний варіант"

**Evidence:** All 10 quiz items test the identical binary: "Is the speaker male (хотів) or female (хотіла)?" Items 1-8 use the identical frame: "[Жінка/Чоловік] говорить: ... [blank] [infinitive]." The learner is never tested on service vocabulary, preposition choice, or case selection — just gender agreement.

**Fix:** Retain 4-5 gender items. Replace the remaining 5-6 with items testing: (a) correct preposition choice (в банк vs на пошту), (b) Accusative vs Locative case (пошту vs пошті), (c) correct service vocabulary matching. This aligns with the plan's activity hint: "quiz focus: 'I want to...' service phrases" — not just gender agreement.

---

### Issue 5: MAJOR — Unnatural Example Sentence (line 58)

**Location:** Section «Укрпошта: Листи та патріотичні марки», line 58

**Evidence:** «Це мій старий білий лист.»

No Ukrainian speaker would naturally say "This is my old white letter." Stacking two adjectives ("old" + "white") serves no pedagogical purpose at this point in the module — the section is introducing postal vocabulary, not adjective order. The sentence doesn't reinforce Accusative case practice (it's Nominative) and doesn't match the service context.

**Fix:** Replace with a contextually relevant sentence, e.g., «Це мій лист для бабусі.» or «Ось мій важливий лист.»

---

### Issue 6: MINOR — Excessive "дуже" Repetition (15 occurrences)

**Location:** Throughout all Ukrainian prose sections

**Evidence:** "дуже" appears on lines 11, 22 (×3 in one paragraph), 38, 51, 53, 55, 105, 118, 120, 122, 124, 130, 245, 250. In the paragraph on line 22 alone: «дуже швидко... дуже швидко... дуже цінують» — three instances in 5 sentences.

This creates a monotonous, padded reading experience. Many occurrences are filler that adds no meaning (e.g., line 120: «Ви знаєте, скільки грошей ви витратили на їжу вчора» doesn't need "дуже" anywhere near it).

**Fix:** Remove or replace at least 8-10 instances of "дуже" with varied intensifiers (надзвичайно, напрочуд, справді, значно) or simply delete them where they add nothing.

---

### Issue 7: MINOR — Missing Warmth Markers for Beginner Module

**Location:** Entire module

**Evidence:** Grep for "Great!", "Well done", "You've", "Don't worry", "Чудово" returned zero matches except one "You are now fully ready" at line 272. Required minimums per rubric:
- Encouragement phrases ≥3 → Found: 0
- "Don't worry" moments ≥2 → Found: 0
- "You can now..." validation ≥2 → Found: 1

The module reads like a reference manual, not a patient tutor.

**Fix:** Add 3+ encouragement phrases at natural pedagogical breakpoints (after the Accusative examples on line 79, after the comparison table on line 183, before the dialogues on line 219). Add 2 "Don't worry" moments near challenging grammar explanations (lines 66, 165).

---

## Factual Verification

| Claim | Location | Status |
|-------|----------|--------|
| Accusative feminine: -а → -у rule | Line 66-67, section «Укрпошта: Листи та патріотичні марки» | **CORRECT** — Standard A2 grammar rule |
| Masculine inanimate Accusative = Nominative | Line 68, section «Укрпошта: Листи та патріотичні марки» | **CORRECT** |
| Locative for Де? / Accusative for Куди? | Lines 169-173, section «Граматичний практикум: Куди чи де?» | **CORRECT** — Matches State Standard §4.2.2.4, §4.2.2.6 |
| Пошта takes "на", банк takes "в/у" | Line 186, section «Граматичний практикум: Куди чи де?» | **CORRECT** — Standard preposition usage |
| Numbers 100-1000 (двісті, триста, etc.) | Lines 88-97, section «Укрпошта: Листи та патріотичні марки» | **CORRECT** — All forms accurate |
| "Рахунок" vs "счет" distinction | Line 133, section «Банківські операції та цифрова екосистема» | **CORRECT** — "Счет" is Russian/surzhyk |
| Ukrposhta patriotic stamp phenomenon 2022 | Lines 104-105, section «Укрпошта: Листи та патріотичні марки» | **CORRECT** — Factually accurate cultural reference |
| "Листа" as Accusative of "лист" (letter) | Line 79, section «Укрпошта: Листи та патріотичні марки» | **CORRECT** — Traditional usage, Accusative -а ending for "лист" in the meaning "letter" is conventionally preferred |

**Callout Box Verification:**

| Box | Type | Location | Status |
|-----|------|----------|--------|
| Чому це важливо? | [!note] | Lines 10-11, section «Вступ: Світ послуг в Україні» | OK — No factual claims |
| Культура ввічливості | [!tip] | Lines 37-38, section «Вступ: Світ послуг в Україні» | OK — Accurate cultural advice |
| Часта помилка | [!warning] | Lines 81-82, section «Укрпошта: Листи та патріотичні марки» | OK — Correct grammar warning |
| Патріотичні марки | [!culture] | Lines 104-105, section «Укрпошта: Листи та патріотичні марки» | OK — Factually accurate |
| Слово "Рахунок" | [!myth-buster] | Lines 132-133, section «Банківські операції та цифрова екосистема» | OK — Correct debunking |
| «Скинути на банку» | [!context] | Lines 159-160, section «Банківські операції та цифрова екосистема» | OK — Accurate contemporary slang explanation |
| Вибір між В/У та На | [!fact] | Lines 185-186, section «Граматичний практикум: Куди чи де?» | OK — Correct preposition explanation |
| Мислення відмінками | [!reflection] | Lines 214-215, section «Граматичний практикум: Куди чи де?» | OK — Good self-reflection prompt |

**Colonial framing check:** No instances of "Unlike Russian", "Different from Russian", or Russian-as-baseline framing found. The [!myth-buster] about "счет" frames it as a surzhyk error — legitimate usage.

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from plan present? | **YES** — All 5 plan sections present as H2 headers |
| Vocabulary scope matches plan? | **YES** — All 15 required + 6 recommended items present in vocab YAML |
| Grammar scope — no scope creep? | **YES** — Content stays within Accusative/Locative/numbers scope |
| Learning objectives addressed? | **PARTIAL** — "send letter/package" ✓, "buy stamps" ✓, "exchange currency" ✓, "withdraw from ATM" ✓ — but plan-specified Monobank/Privat24/QR references missing |
| Russianisms? | **NONE** found |
| Colonial framing? | **NONE** found |
| Activity YAML root format? | **CORRECT** — Bare list at root, no `activities:` wrapper |
| Activity item count meets plan? | **YES** — 12+ items for each plan-specified activity type |
| Factual errors? | **NONE** found (1 typo, not factual) |
| IPA errors? | **YES** — 1 found: вкладати `ʍ` → `ʋ` |
| LLM Fingerprint patterns? | **YES** — "дуже" × 15, generic opener, quiz monotony |

---

## Verdict

**FAIL — 3 issues must be fixed before passing:**

1. **Fix grammatical error** «щоден життя» → «щоденне життя» (line 22)
2. **Fix IPA error** for вкладати: `ʍ` → `ʋ` (vocab YAML line 110)
3. **Add plan-required content**: Monobank, Privat24, QR codes to section «Банківські операції та цифрова екосистема»

**Strongly recommended (not blocking):**
4. Diversify quiz items — replace 5-6 of the 10 identical хотів/хотіла items with service vocabulary/case testing
5. Add ≥3 encouragement markers and ≥2 "don't worry" moments for beginner warmth
6. Replace unnatural example «Це мій старий білий лист.» (line 58)
7. Reduce "дуже" from 15 to ~5 occurrences