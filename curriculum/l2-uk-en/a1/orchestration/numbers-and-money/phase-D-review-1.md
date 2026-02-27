**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|-----------------|
| 1 | **Lesson Quality** | 9/10 | Strong WELCOME→PREVIEW→PRESENT→PRACTICE→CELEBRATE arc. Warm opening «Вітаю!», clear goals at line 38, regular encouragement, good closing celebration at line 399. Deducted 1 point for slight gap between theory and first practice (long theory stretch from line 44 to line 252 without intermission). |
| 2 | **Language Quality** | 8/10 | Ukrainian is generally natural and accurate. Dialogues in section «Практика: У магазині» are natural-sounding. Correctly uses «решта» instead of the Russicism «здача» (notably correcting the plan's own vocabulary_hints). Deducted for: "це не просто" LLM pattern appearing twice (lines 70, 369); line 70 tip box uses imprecise term «м'якою голосною» when «йотованою голосною» would be more accurate. |
| 3 | **Factual Accuracy** | 9/10 | Hryvnia introduced 1996 — correct. ₴ symbol adopted 2004 — correct. Etymology from «грива» (mane/nape) → neck torques of Kyivan Rus' — correct. Proverb «Копійка береже гривню» — real and accurately glossed. Deducted 1 for minor IPA inconsistencies (see issues below). |
| 4 | **Immersion** | 9/10 | 37.8% Ukrainian is within the 25-40% target band for A1 module 17. Appropriate mix: English for grammar explanations, Ukrainian for examples and dialogues. Ukrainian increases naturally in section «Культурний контекст: Історія гривні» where entire paragraphs are in Ukrainian, appropriate for the module's position. |
| 5 | **Richness** | 7/10 | Audit reports 79% vs 95% threshold. Gaps: `cultural: 0/3` (only 1 `[!culture]` callout at line 391), `dialogues: 2/4`, `tables: 1/2` (only the visual summary table at line 233). The module has good content variety but needs more tagged cultural callouts and a second comparison table to meet the richness gate. |
| 6 | **LLM Fingerprint** | 8/10 | «Це не просто декор» (line 70) and «Гроші — це не просто папір, це історія» (line 369) — pattern appears twice, hitting the threshold. «Numbers are everywhere around us» (line 24) — confirmed generic filler flagged by D.0. No structural monotony; section openings are varied. No example batching issues beyond the natural number-list format. |
| 7 | **Humanity & Warmth** | 9/10 | Strong direct address throughout. Welcome: «Вітаю!» (line 18). Encouragement: «don't worry!» (line 20), «Let's start counting!» (line 42). Closing celebration: «Вітаю! Ви щойно відкрили світ українських чисел» (line 399). Progress markers and self-check questions at lines 414-421. |
| 8 | **Activity Quality** | 8/10 | 10 activities across 6 types (match-up, quiz, group-sort, fill-in, unjumble, true-false) — good variety. Thorough 1-2-5 rule practice. Deducted for: vocabulary file IPA double-stress error on «коштувати»; unjumble answer missing internal commas; quiz items in «Фінальний тест» overlap moderately with «Математика на базарі». |

---

## Critical Issues Found

### Issue 1: LLM Filler — Generic Opening (MEDIUM)
**Location:** Line 24, section «Розминка: Числа в житті»
**Text:** «Numbers are everywhere around us. Look at your environment right now. You might see a price tag, a bus number, a digital clock, or a page number in a book.»
**Problem:** D.0-confirmed filler. This sentence is pure generic padding that adds no Ukrainian language teaching. The very next paragraph (line 26-30) already does the same job but with Ukrainian vocabulary examples.
**Fix:** Delete line 24 or replace with a concrete Ukrainian mini-task (e.g., "Look at the price of your last coffee. Can you say that number in Ukrainian?").

### Issue 2: "Це не просто" LLM Pattern (MEDIUM)
**Location:** Lines 70 and 369
**Instances:**
- Line 70: «Це не просто декор.» (in `[!tip]` box)
- Line 369: «Гроші — це не просто папір, це історія.» (opening of section «Культурний контекст: Історія гривні»)
**Problem:** The "це не просто X, це Y" pattern is a known LLM rhetorical device. It appears twice, hitting the flagging threshold.
**Fix:** Line 70 could become «Це важливий знак.» or «Це сигнал зупинки.». Line 369 could become «Гроші мають свою історію.» or «Українська валюта — з тисячолітньою історією.»

### Issue 3: Vocabulary IPA — Double Stress Mark (MEDIUM)
**Location:** Vocabulary file `vocabulary/numbers-and-money.yaml`, line 49
**Text:** `ipa: ''`
**Problem:** Two primary stress marks (ˈ) in a single word. Ukrainian words have only one primary stress. The correct form is `` with stress on the third syllable only.
**Fix:** Change to `''`.

### Issue 4: Content IPA — Missing Palatalization on «скільки» (LOW)
**Location:** Lines 259, 279, section «Практика: У магазині»
**Text:** `` (content) vs `` (vocabulary file)
**Problem:** The content file omits palatalization of /s/ and /k/ before /i/ in «скільки». The vocabulary file correctly has ``. These should be consistent, and the vocabulary file is more accurate.
**Fix:** Update content IPA at lines 259 and 279 to match the vocabulary file: ``.

### Issue 5: Richness Below Threshold (HIGH)
**Location:** Module-wide
**Problem:** Richness is 79% against a 95% threshold. Specific gaps:
- **Cultural callouts:** 0/3 — only one `[!culture]` box (line 391, «Готівка чи Картка?»). Need 2 more.
- **Dialogues:** 2/4 — the module has 3 dialogues plus a scenario, but the audit counts only 2.
- **Tables:** 1/2 — only the Zone 1-2-3 summary table (line 233). Need one more comparison table.
**Fix Plan:**
1. Add a `[!culture]` callout in section «Розминка: Числа в житті» about how Ukrainians read phone numbers (alluded to at line 168 but not in a culture box).
2. Add a `[!culture]` callout in section «Теорія: Числа та гроші» about the origin of "сорок" (40) — already mentioned in passing at line 116 but could be a proper cultural note about the fur trade theory.
3. Add a second table in section «Практика: У магазині» — e.g., a "phrase cheat sheet" table mapping situations to phrases (asking price, paying, getting change).
4. The dialogue count discrepancy may be a tagging issue — ensure the three dialogues are structured in a way the audit can detect.

### Issue 6: Unjumble Answer Missing Internal Commas (LOW)
**Location:** Activities file, line 320
**Text:** `answer: "Ні дякую я зі своїм"`
**Problem:** The natural sentence requires commas: «Ні, дякую, я зі своїм.» While unjumble exercises typically strip final punctuation, the absence of the comma after «Ні» changes the parsing significantly. If the platform validates against this answer string, a learner who correctly orders the words would match, but the displayed answer lacks proper Ukrainian punctuation.
**Fix:** Update to `answer: "Ні, дякую, я зі своїм"` (if the platform supports commas in unjumble answers) or add a note in the explanation about the punctuation.

---

## Pre-Screen Verification

| D.0 Finding | Verdict | Notes |
|-------------|---------|-------|
| **[LLM_FILLER]** "Numbers are everywhere" ~line 21 | **CONFIRMED** (actual line 24) | Generic padding. The following paragraph (lines 26-30) already covers the same ground with Ukrainian vocabulary. Remove or replace with a concrete task. |

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| Hryvnia introduced in 1996 | Line 373, section «Культурний контекст: Історія гривні» | **CORRECT** — September 2, 1996 |
| ₴ symbol adopted in 2004 | Line 379, section «Культурний контекст: Історія гривні» | **CORRECT** — NBU adopted March 1, 2004 |
| «Гривня» from «грива» (mane/nape) | Line 373 | **CORRECT** — well-documented etymology |
| «Копійка береже гривню» proverb | Line 386 | **CORRECT** — real Ukrainian proverb |
| 40 = «сорок» from fur trade | Line 116, section «Теорія: Числа та гроші» | **PLAUSIBLE** — hedged appropriately with "some linguists trace it to ancient fur trade counting" |
| 1-2-5 rule: 11-19 always take Zone 3 | Lines 240-243 | **CORRECT** — teens always govern genitive plural |
| 100 копійок = 1 гривня | Activities true-false item (line 361-363) | **CORRECT** |

**Grammar rule check (1-2-5 rule):** All examples verified correct. Zone 1 (1 гривня), Zone 2 (2-4 гривні), Zone 3 (5+ гривень) are accurately presented. The teen exception (11-19 → Zone 3) is correctly flagged as a warning at line 240.

**Note on plan Russicism:** The plan's `vocabulary_hints.recommended` includes «здача (change)» which is a Russicism (should be «решта»). The content correctly uses «решта» throughout (lines 334, 344, 362, 421). This is a positive deviation from the plan.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing | **CLEAR** — No Russian comparisons found |
| Russicism scan | **CLEAR** — Content correctly uses «решта» not «здача»; uses «Повторімо» (line 405) and «Попрактикуймо» (line 156), both standard Ukrainian imperative forms (not Russianized «давайте повторимо/попрактикуємо») |
| LLM filler | **1 CONFIRMED** — "Numbers are everywhere" (line 24) |
| LLM fingerprint | **FLAGGED** — "це не просто" x2 (lines 70, 369) |
| Structural monotony | **CLEAR** — Section openings are varied |
| Callout monotony | **CLEAR** — 7 callouts using 6 different types |
| Plan compliance | **GOOD** — All 4 content_outline sections present, all objectives addressed, all grammar points covered |
| Vocabulary scope | **GOOD** — 20 vocabulary items covering all required and most recommended terms |
| Activity variety | **GOOD** — 6 unique types across 10 activities |
| "Would I Continue?" test | **PASS 5/5** — Comfortable pacing, clear instructions, quick wins, gentle Ukrainian introduction, encouraging throughout |

---

## Verdict

**PASS WITH REPAIRS**

The module is pedagogically strong. It has excellent pacing for A1, a warm and encouraging tutor voice, accurate grammar explanations, natural Ukrainian dialogues, and good cultural content. The 1-2-5 rule is taught clearly with a useful visual table. The dialogues in section «Практика: У магазині» are realistic and useful. The module correctly avoids the Russicism «здача» despite the plan recommending it.

**Required repairs before final approval:**

1. **Richness gap (HIGH priority):** Add 2 `[!culture]` callouts (one in «Розминка: Числа в житті», one in «Теорія: Числа та гроші») and 1 additional table in «Практика: У магазині» to close the 79% → 95% gap.
2. **LLM filler (MEDIUM priority):** Remove or rewrite «Numbers are everywhere around us» (line 24) with concrete teaching content.
3. **"Це не просто" x2 (MEDIUM priority):** Rephrase at least one of the two instances (lines 70, 369) to break the LLM pattern.
4. **Vocabulary IPA (MEDIUM priority):** Fix double-stress in `коштувати` IPA (vocab file line 49).
5. **Content IPA (LOW priority):** Align «скільки» IPA in content (lines 259, 279) with the vocabulary file's more accurate transcription.

**What NOT to change:** The overall structure, tone, dialogue quality, grammar explanations, and cultural section are all solid. Do not reduce content — the 2636-word count at 131.8% of target is appropriate.