<!-- content-hash: 20653d473f6d -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | **Language Quality** | 7/10 | Multiple IPA errors (missing palatalization on сім, вісім), IPA inconsistency between lesson and vocab file, incorrect phonological term "м'якою голосною" |
| 2 | **Factual Accuracy** | 8/10 | All historical claims verified correct; phonological term "м'якою голосною" is factually wrong (Ukrainian has no "soft vowels") |
| 3 | **Lesson Quality** | 9/10 | Passes 5/5 on "Would I Continue?" test; warm opening, clear pacing, encouraging close |
| 4 | **Immersion** | 8/10 | 39.3% — just under the A1.2 target floor of 40%; adequate English scaffolding |
| 5 | **LLM Fingerprint** | 8/10 | One instance of «це не просто»; two pedagogically empty standalone sentences serve as filler |
| 6 | **Activity Quality** | 8/10 | Excellent variety and coverage; unjumble introduces untaught genitive forms; missing structural commas |
| 7 | **Richness** | 9/10 | Strong cultural hooks (hryvnia etymology, ₴ symbol, proverb), realistic dialogues, varied scenarios |
| 8 | **Humanity & Warmth** | 8/10 | Good warmth in opening/closing; theory-heavy middle sections have noticeably less encouragement |

---

## Critical Issues Found

### Issue 1: IPA errors — missing palatalization on "сім" and "вісім" (MEDIUM)

**Location:** Content file, lines 61-62

**Evidence:** Line 61: «**7 — сім** [sim]. Це сім.» — The consonant /s/ before /i/ is always palatalized in Ukrainian. Correct IPA: [sʲim]. Line 62: «**8 — вісім** [ˈʋisim]. Це вісім.» — Same issue: /s/ before /i/ must be [sʲ]. Minimum correct: [ˈʋisʲim].

**Impact:** These are the very first number IPA transcriptions a learner encounters. Teaching [sim] instead of [sʲim] trains learners to miss palatalization, which is phonemically contrastive in Ukrainian.

**Fix:** Line 61: change `[sim]` → `[sʲim]`. Line 62: change `[ˈʋisim]` → `[ˈʋisʲim]`.

---

### Issue 2: Incorrect phonological term "м'якою голосною" (MEDIUM)

**Location:** Content file, line 70

**Evidence:** «Це сигнал "твердої зупинки" перед м'якою голосною.» — Ukrainian phonology has no concept of "soft vowels" (м'які голосні). Vowels are neither hard nor soft — only consonants carry the hard/soft distinction. The vowel letters я, ю, є, ї after an apostrophe are called **йотовані** (iotated) because they represent [j] + vowel.

**Impact:** This teaches A1 learners a fundamentally wrong phonological concept they will carry into later modules. An A1 beginner learning that Ukrainian has "soft vowels" will be confused when encountering the real hard/soft consonant distinction later.

**Fix:** Change «перед м'якою голосною» → «перед йотованою голосною (я, ю, є, ї)» and add a brief English gloss: "(an iotated vowel — one that starts with a [j] sound)".

---

### Issue 3: IPA inconsistency between lesson and vocabulary file (MEDIUM)

**Location:** Content lines 80, 114, 259 vs. vocabulary file lines 25, 29, 45

**Evidence:**
- Lesson line 80: одинадцять `[ɔdɪˈnɑdt͡sʲɑtʲ]` vs. vocab line 25: `[ɔdɪˈnɑd͡zʲt͡sʲɑtʲ]` (lesson uses plain [d], vocab uses voiced affricate [d͡zʲ])
- Lesson line 114: двадцять `[ˈdʋɑdt͡sʲɑtʲ]` vs. vocab line 29: `[ˈdʋɑd͡zʲt͡sʲɑtʲ]` (same inconsistency)
- Lesson line 259: скільки `[ˈskilʲkɪ]` vs. vocab line 45: `[ˈsʲkʲilʲkɪ]` (lesson omits palatalization on с and к)

**Impact:** A learner who reviews the vocabulary list after the lesson will see different transcriptions for the same word, undermining trust in the material.

**Fix:** Align all IPA to one consistent transcription standard. The vocabulary file's narrower transcription (with palatalization marks and voiced affricates) is more phonetically accurate — update the lesson IPA to match.

---

### Issue 4: Double stress mark in vocabulary IPA for "коштувати" (LOW-MEDIUM)

**Location:** Vocabulary file, line 49

**Evidence:** `ipa: '[ˈkɔʃtuˈʋɑtɪ]'` — This has two stress marks (ˈ before kɔ and before ʋɑ). Ukrainian words have only one primary stress. The word коштувати is stressed on the penultimate syllable: кошту**ва́**ти → `[kɔʃtuˈʋɑtɪ]`.

**Fix:** Remove the spurious initial stress mark: `[kɔʃtuˈʋɑtɪ]`.

---

### Issue 5: Unjumble activity introduces untaught genitive forms (LOW-MEDIUM)

**Location:** Activities file, lines 313-314

**Evidence:** The unjumble item `words: ["Яка", "ціна", "цього", "магніта"]` with answer `"Яка ціна цього магніта"` introduces the genitive forms "цього" (genitive of "цей") and "магніта" (genitive of "магніт"). The lesson teaches «Яка ціна?» (line 270-271) but never shows or practices these genitive forms. While Genitive I (a1-16) is a prerequisite, the specific forms "цього" and "магніта" were not modeled in this module.

**Fix:** Replace with a phrase that uses only forms taught in the lesson. For example: `words: ["Яка", "ціна", "цієї", "кави"]` → but that's still genitive. Better: replace entirely with `words: ["Можна", "карткою", "будь", "ласка"]` answer `"Можна карткою будь ласка"` which uses only lesson-taught vocabulary and structures.

---

### Issue 6: Unjumble answer missing structural commas (LOW)

**Location:** Activities file, line 320

**Evidence:** `answer: "Ні дякую я зі своїм"` — The source sentence in the lesson (line 290) is «Ні, дякую, я зі своїм.» The commas after "Ні" and "дякую" are structurally necessary; without them the sentence is ambiguous. If the unjumble format convention strips punctuation from answers, the words list should include comma tokens, or this sentence should be replaced with one that doesn't require internal punctuation for comprehension.

**Fix:** Either add comma tokens to the words list: `["Ні,", "дякую,", "я", "зі", "своїм"]` or replace with a simpler sentence: `["Ні", "дякую", "не", "потрібен"]` → `"Ні дякую не потрібен"`.

---

### Issue 7: Pedagogically empty standalone sentences (LOW)

**Location:** Content file, lines 375, 381

**Evidence:** «Це стародавня історія.» (line 375) and «Символ означає стабільність.» (line 381) are standalone bolded Ukrainian sentences in section «Культурний контекст: Історія гривні» that add no new vocabulary, grammar, or cultural content. They restate what the preceding English prose already said. They read as filler intended to inflate the Ukrainian immersion ratio.

**Fix:** Remove both, or replace with pedagogically useful Ukrainian sentences that introduce new vocabulary or provide practice opportunities. For example, at line 375: «Гривня — давня назва.» (The hryvnia is an ancient name) followed by «Знайте її походження!» (Know its origin!) — which are simpler and more A1-appropriate.

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| Hryvnia introduced in 1996 | Line 373 | **Correct** — September 2, 1996 |
| ₴ symbol adopted in 2004 | Line 379 | **Correct** — March 1, 2004 by NBU |
| "Грива" = mane/back of neck | Line 373 | **Correct** — standard etymology |
| Гривна = neck ring/torc of Kyivan Rus' | Line 373 | **Correct** |
| "Копійка береже гривню" = real proverb | Line 386 | **Correct** — well-attested Ukrainian proverb |
| "Сорок" linked to fur trade counting | Line 116 | **Correct** — established etymological theory (a bundle of 40 furs) |
| 1-2-5 rule (1=Nom.Sg, 2-4=Nom.Pl, 5+=Gen.Pl) | Lines 178-220 | **Correct** |
| Numbers 11-19 always take Gen.Pl (Zone 3) | Lines 240-243 | **Correct** |
| "Два" = M/N, "Дві" = F | Lines 198-199 | **Correct** |
| "Один" agrees in gender (один/одна/одне) | Lines 183-185 | **Correct** |
| "м'якою голосною" (soft vowel) | Line 70 | **Incorrect** — see Issue 2 |

**Factual accuracy summary:** All historical and cultural claims are verified. The 1-2-5 grammar rule is correctly explained. One factual error exists: the phonological term "м'якою голосною" is not a valid concept in Ukrainian phonology.

---

## Plan Verification

| Plan Element | Status |
|-------------|--------|
| Section «Розминка: Числа в житті» present | Present (line 16) |
| Section «Теорія: Числа та гроші» present | Present (line 44) |
| Section «Практика: У магазині» present | Present (line 252) |
| Section «Культурний контекст: Історія гривні» present | Present (line 367) |
| Numbers 0-10 with pronunciation | Covered (lines 52-64) |
| Numbers 11-19 with -надцять pattern | Covered (lines 72-88) |
| Tens 20-100 | Covered (lines 106-150) |
| 1-2-5 Rule with visual table | Covered (lines 171-237) |
| "Скільки коштує?" | Covered (line 259) |
| "Скільки з мене?" | Covered (line 279) |
| Dialogues in shop | Covered (3 dialogues, lines 321-353) |
| Hryvnia history, ₴ symbol, proverb | All covered (lines 367-393) |
| All 4 learning objectives | All met |

**Plan compliance: Full.** All meta content_outline sections and all plan objectives are present.

---

## Vocabulary Coverage

| Required (plan) | In vocab file? | In lesson? |
|----------------|----------------|------------|
| один | Yes | Yes (line 55) |
| два | Yes | Yes (line 56) |
| три | Yes | Yes (line 57) |
| п'ять | Yes | Yes (line 59) |
| десять | Yes | Yes (line 64) |
| гривня | Yes | Yes (line 176) |
| скільки | Yes | Yes (line 259) |
| коштувати | Yes | Yes (line 262) |

| Recommended (plan) | In vocab file? | In lesson? |
|--------------------|----------------|------------|
| сто | Yes | Yes (line 148) |
| копійка | Yes | Yes (line 247) |
| ціна | Yes | Yes (line 270) |
| дорого | Yes | Yes (line 306) |
| дешево | Yes | Yes (line 307) |
| здача | Yes | Yes (line 334) |

**Vocabulary coverage: Full.** All required and recommended items present in both vocabulary file and lesson content. The vocabulary file adds 6 bonus items (чотири, одинадцять, двадцять, готівка, картка, пакет) — all contextually appropriate.

---

## Colonial Framing Check

No instances found. No references to Russian language or script as a comparison baseline. Clean.

---

## LLM Fingerprint Analysis

| Test | Result |
|------|--------|
| Structural monotony (same opening pattern 3+ sections) | **Pass** — all 4 H2 sections open differently |
| Example batching (identical format across 3+ sections) | **Pass** — formats vary: bullet lists, tables, dialogues, prose, scenario |
| "це не просто" / "це не лише" (2+ uses) | **Pass** — 1 use at line 369, below threshold |
| Stacked abstract nouns (3+ sentences) | **Pass** — none found |
| Generic AI clichés (діамант, двигун, дзеркало) | **Pass** — none found |
| "In this lesson, we will explore" | **Pass** — not found |
| Callout monotony (3+ same title) | **Pass** — all callout titles unique |
| Example plausibility | **Pass** — all dialogue examples are realistic shopping scenarios |
| Filler sentences | **Flag** — lines 375, 381 (see Issue 7) |

---

## Lesson Experience Audit

### "Would I Continue?" Test

| Question | Result | Evidence |
|----------|--------|----------|
| Did I feel overwhelmed? | **Pass** | Numbers introduced in small chunks (0-10, then 11-19, then tens); grammar taught via the single "1-2-5" framework |
| Were instructions clear? | **Pass** | Every section clearly states what it teaches; English used for all grammar explanations |
| Did I get quick wins? | **Pass** | Numbers 0-10 are immediately satisfying; math practice at line 156 gives instant feedback |
| Was Ukrainian scary? | **Pass** | Gentle introduction with English throughout; Ukrainian always translated |
| Would I come back tomorrow? | **Pass** | Dialogues are fun and practical; closing celebration at line 399 is motivating |

**5/5 Pass → Lesson Quality 9/10** (not 10 because the theory section is long — approximately 1200 words from line 44 to line 250 — before the practice dialogues begin)

### Emotional Safety Mapping

| Required Beat | Present? | Location |
|--------------|----------|----------|
| Welcome/orientation | Yes | «Вітаю! Welcome back.» (line 18) |
| Curiosity trigger | Yes | «In Ukrainian, numbers are a bit more... alive.» (line 21) |
| Quick win #1 | Yes | Numbers 0-10 (line 52) — easy memorization |
| Quick win #2 | Yes | Simple math examples (line 162) |
| Encouragement | Yes | «But don't worry! We will build this step-by-step.» (line 21) |
| "Don't worry" moment | Yes | Line 21; also line 212 «just treat it as a special "counting form"» |
| Progress marker | Yes | «Вітаю! Ви щойно відкрили світ українських чисел.» (line 399) |
| "You can now..." | Yes | «Тепер ви можете рахувати. Ви можете питати про ціни.» (lines 400-401) |

### Pacing Analysis

| Metric | Observed | Verdict |
|--------|----------|---------|
| New words per section | 10-13 in Теорія (numbers), 5-7 in Практика | Теорія is slightly heavy but numbers are a natural batch |
| Concepts before practice | 2 (number formation + 1-2-5 rule) before dialogues | Acceptable, but Теорія runs ~1200 words before Практика |
| English support | Present throughout theory; dialogues have translation | Good |
| Visual aids | Table at line 233, consistent formatting | Good |

---

## Activity Detailed Review

| # | Type | Title | Items | Issues |
|---|------|-------|-------|--------|
| 1 | match-up | Числа 0–10: Основи | 8 pairs | Clean |
| 2 | match-up | Числа 11–100: Великі числа | 13 pairs | Clean |
| 3 | quiz | Математика на базарі | 12 items | Clean; arithmetic verified correct |
| 4 | group-sort | Правило 1–2–5 | 3 groups, 11 items | Clean; "дванадцять" correctly in Zone 3 |
| 5 | fill-in | Рахуємо гривні | 12 items | Clean; all zone assignments correct |
| 6 | fill-in | Рахуємо копійки | 12 items | Clean |
| 7 | unjumble | Діалоги в магазині | 6 items | **Issues 5 & 6** (genitive scope, missing commas) |
| 8 | match-up | Корисні фрази | 11 pairs | Clean |
| 9 | true-false | Логіка чисел | 12 items | Clean |
| 10 | quiz | Фінальний тест | 12 items | Clean |

**Activity variety:** 6 types across 10 activities = 60%. Good.
**Total items:** ~109. Very thorough coverage.
**Key strength:** The fill-in activities (5 & 6) systematically drill every zone of the 1-2-5 rule with both гривня and копійка — excellent pedagogical design.

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from meta outline present | Yes |
| All learning objectives addressed | Yes |
| All required vocabulary covered | Yes |
| No Russianisms detected | Clean |
| No colonial framing | Clean |
| No scope creep (grammar from later modules) | Clean (1-2-5 rule is appropriate for this module) |
| IPA accuracy | **3 errors in lesson, 1 error in vocab, inconsistency between files** |
| Factual claims | **1 error** (phonological term "м'якою голосною") |
| Activity correctness | **2 issues** in unjumble activity |
| Engagement box count | 7 (healthy) |
| Word count | 2622/2000 (131.1%) — exceeds minimum, not padded |

---

## Fix Plan

| Priority | Issue | Fix | Location |
|----------|-------|-----|----------|
| **P1** | IPA "сім" [sim] | Change to [sʲim] | Content line 61 |
| **P1** | IPA "вісім" [ˈʋisim] | Change to [ˈʋisʲim] | Content line 62 |
| **P1** | "м'якою голосною" wrong term | Replace with «йотованою голосною (я, ю, є, ї)» + English gloss | Content line 70 |
| **P2** | IPA inconsistency lesson↔vocab | Align lesson IPA to vocab file's narrower standard for одинадцять, двадцять, скільки | Content lines 80, 114, 259 |
| **P2** | Vocab IPA double stress | Remove spurious ˈ from [ˈkɔʃtuˈʋɑtɪ] → [kɔʃtuˈʋɑtɪ] | Vocab line 49 |
| **P2** | Unjumble genitive scope | Replace "Яка ціна цього магніта" with phrase using only lesson-taught forms | Activities line 313-314 |
| **P3** | Unjumble missing commas | Add comma tokens or replace sentence | Activities line 319-320 |
| **P3** | Filler sentences | Remove or replace «Це стародавня історія.» and «Символ означає стабільність.» | Content lines 375, 381 |

---

## Verdict

**PASS WITH FIXES**

The module is pedagogically strong — warm, well-paced, and thorough. The 1-2-5 rule explanation with visual table is excellent. Dialogues are realistic and engaging. Activity coverage is comprehensive with 109 items across 6 types. All plan objectives and vocabulary requirements are fully met.

The issues are concentrated in IPA accuracy (missing palatalization marks, inconsistency between lesson and vocabulary file) and one phonological terminology error. None of these are auto-fail, but the IPA issues should be fixed before the module ships — learners will use these transcriptions as pronunciation reference, and missing [sʲ] vs [s] is a phonemically contrastive distinction in Ukrainian.

No critical issues. No Russianisms. No colonial framing. No significant LLM fingerprinting.