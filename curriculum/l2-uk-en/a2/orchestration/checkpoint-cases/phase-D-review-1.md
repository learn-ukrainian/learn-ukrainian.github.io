**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Plan Compliance | 7/10 | All 5 H2 sections present and matching the meta `content_outline`. Vocabulary coverage is complete (all 15 required items appear). However: word count is 2573/3000 (85.8%, below minimum target), zero IPA transcriptions despite research notes requiring them on first occurrence, and immersion is 18% vs 50-60% spec. |
| 2 | Language (Ukrainian) | 7/10 | Ukrainian example sentences are grammatically correct. However, **colonial framing** on line 181 defines Ukrainian's vocative by explicit contrast with Russian — outside any myth-buster or decolonization callout. Per rules: capped at ≤7. Minor: inconsistent case annotations mixing "(Орудний)" with English abbreviations (Acc, Gen, Loc). |
| 3 | Language (English) | 6/10 | Overly formal throughout: "let us" appears 8 times (lines 20, 38, 58, 124, 158, 183, 198, 233) instead of the rubric-recommended "Let's." Zero contractions ("it is", "do not", "let us") when the rubric explicitly allows and encourages them for beginner warmth. Reads like an academic textbook, not an encouraging tutor. |
| 4 | Immersion Balance | 3/10 | Audit shows 18.0% Ukrainian; target is 50-60%. The module is essentially an English grammar lecture with Ukrainian example sentences. All theory, transitions, introductions, and explanations are in English. Only dialogues (lines 206-223), the historical passage (line 239), and isolated example sentences provide Ukrainian text. This is a 32+ percentage-point deficit. |
| 5 | Lesson Quality | 6/10 | "Would I Continue?" test: Overwhelmed? No (Pass). Instructions clear? Yes (Pass). Quick wins? First practice doesn't come until deep into Section «Навичка 1: Відмінки в дії: Давальний та Орудний» after long theory blocks (Fail). Was Ukrainian scary? No, too little of it (Pass). Would I come back? Feels like a textbook chapter, not a tutor session (Fail). 3/5 = 8, but formal tone and weak emotional arc drop it to 6. |
| 6 | Activity Quality | 7/10 | Excellent variety (10 types across 12 activities). Comprehensive case coverage. But two errors: (1) "через проблеми" marked incorrect (activities line 551-552) when it's valid Accusative plural; (2) fabricated distractor "еконовив" (activities line 724). Pedagogically questionable: "дивитися на картину" grouped under "Напрямок руху" (line 331) — looking at something isn't physical motion. |
| 7 | Richness | 8/10 | Strong cultural hooks: Diia app context in Section «Навичка 3: Сервіси та цифрова Україна», stamps-as-currency historical reading in Section «Історичний виклик та підсумок». Good tables (preposition matrix line 42, Acc vs. Loc comparison line 171, summary matrix line 253). Practical dialogues with inline case annotations are pedagogically useful. Could benefit from mnemonic devices or visual mnemonics. |
| 8 | LLM Fingerprint | 5/10 | **Structural monotony**: "Let us" opens or appears in 8 different paragraphs. **Generic AI rhetoric**: Line 18 — "When we talk about the Ukrainian language, we see a system that is incredibly flexible and expressive" is classic LLM filler. Line 122 — "is arguably the most frequently used oblique case" is hedging filler. Formal voice throughout ("it is time to bring all the pieces together", "this concept is called 'prepositional governance'") feels generated, not authored. |
| 9 | Humanity & Warmth | 4/10 | **COLD_PEDAGOGY triggered.** Encouragement count: 1 "do not worry!" (line 34). "You can now..." validation: 0 (the closing at line 269 says "You have successfully completed" but doesn't list concrete abilities). "Don't worry" moments: 1 total. Required minimums: ≥3 encouragement, ≥2 "don't worry", ≥2 "You can now..." — fails all three. No warm Ukrainian greeting (opens with English "Welcome"). |
| 10 | Factual Accuracy | 9/10 | Stamps-as-currency 1918 is historically documented. Diia app digital passport claim (line 225) is accurate. Grammar explanations are correct throughout. All case function descriptions are accurate. Minor: the quote «Ходить нарівні з дзвінкою монетою» on line 239 matches historical sources. |

---

## Critical Issues Found

### Issue 1: Colonial Framing (CRITICAL — Auto-flag)

**Location:** Line 181, Section «Навичка 2: Граматичні тонкощі: Родовий, Знахідний та Кличний», subsection «Самоперевірка: Кличний відмінок»

**Text:** «While many languages (including Russian) have lost their vocative case, Ukrainian has preserved and nurtured it.»

**Problem:** This defines Ukrainian's vocative case by explicit contrast with Russian. The parenthetical "(including Russian)" singles out Russian as the comparison baseline. This is **not** inside a `[!myth-buster]` or `[!decolonization]` callout — it's in regular prose. Per colonial framing rules, this is a flag.

**Fix:** Remove the Russian reference entirely. Present the vocative as a living feature of Ukrainian on its own terms:
> "The Vocative case (Кличний відмінок) is a living, vibrant feature of Ukrainian. It is used exclusively for addressing someone directly — a sign of politeness, respect, and natural fluency."

---

### Issue 2: Catastrophic Immersion Deficit (CRITICAL)

**Location:** Entire module

**Problem:** Immersion is 18.0% vs. the 50-60% target for A2 Band 1. The module is structured as an English grammar lecture with Ukrainian relegated to example sentences and dialogues only. All section introductions, theory explanations, transitions, and meta-commentary are in English. For a checkpoint module reviewing content learners have already studied, this is especially problematic — learners should be ready for more Ukrainian at this stage.

**Fix:** Convert substantial portions of theory text to Ukrainian with English glosses. For example, the opening of Section «Огляд та самооцінка» (lines 16-18) should lead with Ukrainian, not English. The self-assessment checklist (lines 26-32) could be bilingual. Section transitions should use Ukrainian with English support rather than pure English.

---

### Issue 3: Activity Error — Valid Answer Marked Incorrect (CRITICAL)

**Location:** Activities file line 549-552, select activity «Які слова використовуємо для вираження причини зі словом "через"?»

**Text:** The option «через проблеми» is marked `correct: false`.

**Problem:** "Проблеми" is the Accusative plural of "проблема" (feminine noun). "Через" governs Accusative. Therefore "через проблеми" (because of problems) is grammatically correct Ukrainian. Marking it false teaches learners that a valid Ukrainian construction is wrong.

**Fix:** Either mark «через проблеми» as `correct: true` (and adjust `min_correct`), or replace the distractor with a genuinely incorrect form like «через проблемою» (Instrumental, clearly wrong case).

---

### Issue 4: Fabricated Distractor Word (HIGH)

**Location:** Activities file line 724, cloze activity blank #10

**Text:** Distractor option «еконовив»

**Problem:** The word "еконовив" does not exist in Ukrainian. The verb "економити" conjugates to past tense "економив" (not "еконовив"). Distractors should be plausible but wrong Ukrainian forms — fabricated non-words undermine the activity's pedagogical value and look unprofessional.

**Fix:** Replace «еконовив» with «зекономив» (perfective past, which would be the wrong aspect for this context) or «економило» (wrong gender agreement).

---

### Issue 5: Zero IPA in Content (HIGH)

**Location:** Entire content file

**Problem:** Research notes (line 32) explicitly state: "Use IPA only on the first occurrence of each new vocabulary word." The content file contains zero IPA transcriptions. The vocabulary file has IPA, but learners need it inline in the prose on first encounter of key terms.

**Fix:** Add IPA for at least the high-frequency vocabulary on first occurrence: відмінок, прийменник, допомагати, подобатися, etc.

---

### Issue 6: Vocabulary IPA Errors — Double Stress Marks (HIGH)

**Location:** Vocabulary file lines 12 and 95

**Text:**
- Line 12: «родовий» → `` (two stress marks)
- Line 95: «помилка» → `` (two stress marks)

**Problem:** Ukrainian words have exactly one primary stress. "Родовий" should be (stress on final syllable). "Помилка" should be (stress on мі).

**Fix:** Remove the spurious stress marks: `` and ``.

---

### Issue 7: LLM Voice — "Let us" × 8 (MEDIUM)

**Location:** Lines 20, 38, 58, 124, 158, 183, 198, 233

**Problem:** "Let us" is used 8 times throughout the module. This is a strong LLM fingerprint — real tutors and teachers say "Let's." The review rubric explicitly marks ✅ "Let's start with..." and flags formal AI voice. Combined with zero contractions elsewhere ("it is", "do not", "you must"), the module reads as machine-generated.

**Fix:** Replace all "Let us" with "Let's." Convert "it is" → "it's", "do not" → "don't", "you have been" → "you've been" throughout. This alone would significantly improve the natural, warm tutoring voice.

---

### Issue 8: COLD_PEDAGOGY — Insufficient Warmth (MEDIUM)

**Location:** Throughout

**Problem:** The module has only 1 "don't worry" moment (line 34: «do not worry!»), 0 "You can now..." validation statements, and minimal encouragement phrases. The closing paragraph (line 269) says «You have successfully completed» but doesn't tell learners what specific abilities they've gained. Required minimums for beginner modules: ≥3 encouragement, ≥2 "don't worry", ≥2 "You can now..." — all three thresholds are missed. No warm Ukrainian opening (missing "Привіт!").

**Fix:**
1. Add a Ukrainian greeting to the opening: "Привіт! Welcome to your checkpoint!"
2. Add encouragement after the first practice subsection in «Навичка 1: Відмінки в дії: Давальний та Орудний»: "Great work! You're using cases correctly."
3. Add "don't worry" moments at the start of sections «Навичка 2» and «Навичка 3».
4. Rewrite the closing to explicitly list abilities: "You can now: express age using the Dative, describe your profession using the Instrumental..."

---

### Issue 9: Inconsistent Case Annotation Labels (LOW)

**Location:** Lines 50, 207, 239 vs. lines 159-161, 173-177, 207-222

**Problem:** The Instrumental case is annotated as "(Орудний)" in Ukrainian (lines 50, 207, 239), while all other cases use English abbreviations: (Acc), (Gen), (Loc), (Nom). This inconsistency could confuse learners.

**Fix:** Standardize to either all English abbreviations (Inst) or all Ukrainian names. Given the immersion deficit, using Ukrainian names for all annotations would help increase Ukrainian exposure.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Colonial framing | **FOUND** | Line 181: Ukrainian vocative defined by contrast with Russian |
| Russianisms | CLEAN | No кушати, із-за, красивий, etc. in prose. Note: activity line 261 tests "кушаю" as an error to correct — this is pedagogically appropriate |
| Grammar accuracy | CLEAN | All case explanations and example sentences are grammatically correct |
| Factual claims | VERIFIED | Stamps-as-currency 1918, Diia app claims are accurate |
| LLM fingerprint | **FOUND** | "Let us" × 8, generic rhetoric on line 18, zero contractions |
| Activity errors | **FOUND** | "через проблеми" false positive (line 552), "еконовив" fabricated (line 724) |
| IPA | **MISSING** | Zero IPA in content; 2 double-stress errors in vocabulary file |
| Immersion | **FAIL** | 18% vs 50-60% target |
| Warmth markers | **FAIL** | COLD_PEDAGOGY: 1 encouragement, 0 "You can now", 1 "don't worry" |
| Section coverage | PASS | All 5 H2 sections present and match plan outline |
| Word count | **BELOW TARGET** | 2573/3000 (85.8%) |
| Engagement boxes | PASS | 6-7 callout boxes ([!tip], [!culture], [!warning] ×2, [!myth-buster], [!fact]) |

---

## Verdict

**FAIL — Needs D.2 Repair**

The module has strong structural bones: all plan sections are covered, activities show excellent variety (10 types), cultural hooks are well-chosen (Diia, stamps-as-currency), and Ukrainian grammar accuracy is solid throughout. The preposition governance table and Acc/Loc comparison table are genuinely useful pedagogical tools.

However, three systemic issues require repair before this module can pass:

1. **Immersion crisis** (18% vs 50-60%): The module is an English grammar lecture, not a Ukrainian learning experience. This requires substantial rewriting to shift theory sections into bilingual Ukrainian-with-English-support format.

2. **Cold pedagogy**: The formal academic tone ("Let us", zero contractions, minimal encouragement) is inappropriate for A2 beginners who need warmth and reassurance. Every section opening should be rewritten for warmth.

3. **Activity errors**: The "через проблеми" false positive is a genuine grammar teaching error that must be fixed. The "еконовив" fabricated word must be replaced.

Secondary issues (colonial framing, missing IPA, word count deficit, vocabulary IPA errors) should be fixed concurrently.

**Priority for D.2 repair:**
1. Fix activity errors (через проблеми, еконовив) — surgical fixes
2. Remove colonial framing on line 181
3. Rewrite English for warmth (contractions, "Let's", encouragement markers)
4. Increase immersion to ≥50% by converting theory sections to bilingual format
5. Add IPA on first occurrence of key vocabulary
6. Expand content to meet 3000-word minimum