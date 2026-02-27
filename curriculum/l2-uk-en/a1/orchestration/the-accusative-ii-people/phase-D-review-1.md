**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Justification |
|---|-----------|-------|---------------|
| 1 | Language Quality | 8/10 | IPA error for вчитель in vocabulary YAML (`` uses invalid phoneme ʍ and misplaces stress). Content line 74 incorrectly calls р in лікар a "soft consonant" — it is phonetically hard but lexically classified in the soft declension group. Lines 86 and 88 offer contradictory explanations (phonetic vs. lexical) for the same phenomenon. English prose is clear and accessible throughout. No Russianisms detected. No colonial framing. |
| 2 | Lesson Quality | 8/10 | Strong metaphors ("Heart Box," "Stone Box," "Greedy Masculine Rule") aid memorability. Good pacing with tables and visual aids. However: no warm greeting to the learner at the start (module opens with a blockquote, not "Привіт!"); no "Today you'll learn..." learning objectives preview; no "You can now..." celebration at the end (just «Дякую за увагу! До побачення!» at line 448). Scoring 4/5 on the "Would I Continue?" test — pacing comfortable, instructions clear, quick wins present, Ukrainian not scary, but warmth could be better. |
| 3 | Immersion | 8/10 | Measured at 27.3% against 25-40% target — within range but at the low end. For A1.2 phase, the tier guidance suggests 40-60%; the grammar-heavy content justifies more English for explanations, but Section «Культурний контекст: Друзі та імена» could carry more Ukrainian naturally. Dialogues in Section «Використання: Моя сім'я та друзі» are good immersion anchors. |
| 4 | Activity Quality | 6/10 | **Critical flaw**: Activity 8 ("Ситуації: Кого чи Що?", quiz, 12 items) has questions that give away answers — e.g., «Ви чекаєте друга. Як це сказати?» presents the correct accusative form "друга" in the question, and the student just matches it in the options. All 12 items follow this broken pattern. Unjumble activities (6 and 9) use 3-word sentences (e.g., "Я / бачу / брата") where only one arrangement is possible — zero challenge. Additionally, собака appears in Activity 5 fill-in but is never formally taught in the lesson content (only in a Common Mistakes table). |
| 5 | LLM Fingerprint | 8/10 | No generic AI clichés ("explore," "it is important to note"). No structural monotony — each H2 section opens differently. The "Червона Рута" reference at line 410 feels like a dropped cultural hook — mentioned briefly with no lyrics, no activity, no deeper engagement. The «historically soft declension — a lexical property of this specific word» phrasing at line 88 reads like an LLM hedging rather than confident teaching. No callout monotony issues. |
| 6 | Factual Accuracy | 8/10 | Grammar rules are correct overall. However, line 74 states «Soft sign (ь) or soft consonant (like р in лікар) adds -я» — the consonant р in лікар is NOT phonetically soft. The word belongs to the soft declension group (м'яка група) by lexical classification, not because р is soft. This creates a false rule: students might think any word ending in р takes -я, when in fact only specific lexemes do (лікар, секретар, etc.). The "Червона Рута" attribution to Volodymyr Ivasyuk at line 410 is correct. Name Day claim for Андрій on November 30th (line 406) is incorrect — Андрія celebrated December 13 (Gregorian) in Ukrainian tradition. |
| 7 | Richness | 8/10 | Good variety: grammar tables, dialogues (2 full dialogues in Section «Використання: Моя сім'я та друзі»), cultural context (друг vs знайомий), diminutives table, common mistakes gallery, polite address (Пан/Пані). The reading passage at line 225 is natural and engaging. Multiple callout types used (observe, tip, warning, myth-buster, context, dialogue, summary, quote, culture). Missing: recommended vocabulary item "дитина" (from plan) appears only once at line 206 and is absent from vocabulary YAML. |
| 8 | Humanity & Warmth | 7/10 | Below warmth minimums for A1. Encouragement phrases: "Good news" (line 99), "Don't Overthink It!" (line 113) — only 2 clear ones, minimum is ≥3. "Don't worry" moments: only "Don't Overthink It!" counts — minimum is ≥2. "You can now..." validation: «Сьогодні ми вивчили знахідний відмінок для істот» (line 435) is a summary, not celebration — minimum is ≥2. No warm opening greeting. Module persona role "HR Recruiter" has essentially zero manifestation in content framing. |

---

## Critical Issues Found

### Issue 1: Activity 8 Questions Give Away Answers (CRITICAL — Activity Design)

**Location:** Activities YAML, Activity 8 "Ситуації: Кого чи Що?" (quiz), lines 487-622

**Description:** All 12 quiz items follow the pattern «Ви [verb] [correct accusative form]. Як це сказати?» — the question already contains the correct accusative form, making the exercise pedagogically useless. The student merely matches the word from the question text to the option list.

**Examples (verbatim from file):**
- Line 499: «Ви чекаєте друга. Як це сказати?» → correct option «Я чекаю друга.» (the word "друга" already appears in the question)
- Line 510: «Ви бачите лікаря. Як це сказати?» → correct option «Я бачу лікаря.» (the word "лікаря" already appears in the question)
- Line 587: «Ви бачите кота. Як це сказати?» → correct option «Я бачу кота.» (the word "кота" already appears in the question)

**Fix:** Rewrite questions in English ("You see a doctor. How do you say this in Ukrainian?") or present the nominative form and ask for the accusative transformation ("Ви бачите ___. (лікар)").

### Issue 2: Unjumble Activities Have Zero Challenge (MAJOR — Activity Design)

**Location:** Activities YAML, Activity 6 "Складіть речення" (unjumble, lines 399-461) and Activity 9 "Запитайте про людей" (unjumble, lines 623-687)

**Description:** All unjumble items consist of only 3 words in strict SVO order (Subject-Verb-Object). With only 3 words and only one syntactically valid arrangement, the exercise provides no challenge whatsoever. Ukrainian word order does allow some variation, but with 3 words there's essentially only one natural arrangement.

**Examples (verbatim from file):**
- Line 401-405: words: `Я`, `бачу`, `брата` → answer: «Я бачу брата»
- Line 406-410: words: `Ми`, `знаємо`, `лікаря` → answer: «Ми знаємо лікаря»

**Fix:** Add more words to each item (4-5 minimum) — include adjectives, adverbs, or time expressions: e.g., "Я / добре / знаю / нашого / лікаря" or "Вчора / я / бачив / брата / в / парку".

### Issue 3: IPA Error for вчитель (MAJOR — Vocabulary)

**Location:** Vocabulary YAML, line 29

**Description:** The IPA transcription `` contains two errors:
1. The phoneme ʍ (voiceless labial-velar fricative) does not exist in Ukrainian. The correct representation of Ukrainian в before a consonant is [u̯] or [ʋ].
2. Stress is placed on the first syllable (ˈʍ), but вчи́тель has stress on the second syllable.

**Fix:** Correct IPA to ``.

### Issue 4: Misleading "Soft Consonant" Explanation for лікар (MAJOR — Grammar Accuracy)

**Location:** Content file, line 74 and lines 86-88

**Description:** Line 74 states: «Soft sign (ь) or soft consonant (like р in лікар) adds -я.» The consonant р in лікар is NOT phonetically soft — it is a hard consonant. The word лікар belongs to the soft declension group (м'яка група) by *lexical classification*, not because its final consonant is soft. This creates a false rule that could lead students to incorrectly apply -я to other words ending in р.

Lines 86-88 then contradictorily explain it as «a lexical property of this specific word» — which is more accurate but conflicts with the "soft consonant" claim two paragraphs earlier.

**Fix:** Remove the "soft consonant (like р in лікар)" claim from line 74. In the table at lines 91-96, add лікар with a note "memorize: лікар → лікаря (special word)." Simplify line 88 to: "Some words like лікар take -я even though they don't end in ь or й. You just need to memorize these."

### Issue 5: собака Used in Activities Without Being Taught (MODERATE)

**Location:** Content line 145, 191; Activities YAML lines 389-396

**Description:** The word "собака" appears in the Common Mistakes Gallery (line 145: «Я люблю собака.» → «Я люблю собаку.»), in a practice example (line 191: «Ти бачиш **собаку**.»), and in Activity 5 fill-in (line 389-396) with a full explanation. However, it is never formally introduced or taught. The lesson uses "пес" as the primary word for "dog" in its theory section (Section «Теорія: Як змінюються слова»). The behavior of собака (masculine noun with feminine-pattern declension due to -а ending) is a pedagogically interesting case that deserves explicit teaching, not just a passing error example.

**Fix:** Add a brief subsection or callout box in Section «Теорія: Як змінюються слова» explaining that собака is masculine but declines like feminine nouns because it ends in -а, contrasting it with пес.

### Issue 6: Insufficient Warmth Markers for A1 (MODERATE — Pedagogy)

**Location:** Throughout content file

**Description:** The module falls below minimum warmth thresholds for beginner content:
- Encouragement phrases: 2 found ("Good news" line 99, "Don't Overthink It!" line 113), minimum is ≥3
- "Don't worry" moments: 1 found ("Don't Overthink It!" line 113), minimum is ≥2
- "You can now..." validation: 0 clear instances, minimum is ≥2
- No warm greeting at module opening
- Module persona role "HR Recruiter" has zero manifestation

**Fix:** Add a "Привіт!" greeting at the top. Add "You've got this!" or "Great work!" between Section «Практика: Тренуємо форми» and Section «Використання: Моя сім'я та друзі». Add a "You can now..." celebration block before the final Підсумок listing what the learner has achieved.

### Issue 7: Name Day Date Possibly Incorrect (MINOR — Factual)

**Location:** Content file, line 406

**Description:** The content states «If your name is Андрій, your name day is November 30th.» In Ukrainian tradition, the feast of St. Andrew (Андрія Первозванного) is celebrated on December 13 (Gregorian calendar), not November 30. November 30 is the Old Style (Julian calendar) date. For a modern Ukrainian learner, December 13 is the more commonly referenced date (Андріїв день).

**Fix:** Change to "December 13th" or clarify "November 30th (December 13th in the modern calendar)."

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Colonial framing | PASS | No Russian comparisons found |
| Russianisms | PASS | No Russianisms detected |
| LLM fingerprints | PASS | No generic AI clichés; minor hedging at line 88 |
| Structural monotony | PASS | Each H2 section opens differently |
| Callout monotony | PASS | Varied callout types used |
| Grammar scope | PASS | Stays within accusative case for animate nouns |
| Plan vocabulary coverage | PARTIAL | All required items present; recommended item "дитина" missing from vocabulary YAML |
| Plan section coverage | PASS | All 5 meta outline sections present as H2 headers |
| Activity grammar | MOSTLY PASS | All accusative forms correct; собака explanation is accurate but untaught |
| Factual claims | PARTIAL | Червона Рута attribution correct; лікар "soft consonant" claim incorrect; Name Day date uses Julian calendar without clarification |

### "Would I Continue?" Test (Beginner Safety)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | PASS | Comfortable pacing, clear tables |
| Were instructions clear? | PASS | Always knew what to do |
| Did I get quick wins? | PASS | Animacy sorting, correction exercises |
| Was Ukrainian scary? | PASS | Always supported with English |
| Would I come back tomorrow? | BORDERLINE | Informative but could be warmer |

**Result:** 4.5/5 → Lesson Quality 8/10

---

## Verdict

**CONDITIONAL PASS — Requires targeted fixes before publication.**

The lesson prose is strong — the "Heart Box / Stone Box" and "Greedy Masculine Rule" metaphors are pedagogically excellent, grammar tables are clean and visual, dialogues in Section «Використання: Моя сім'я та друзі» feel natural, and the cultural content in Section «Культурний контекст: Друзі та імена» (друг vs знайомий, diminutives) is well-chosen.

**Must fix before passing (blocking):**
1. **Activity 8 quiz redesign** — questions must not give away answers (Critical)
2. **Unjumble activities** — add more words per item for actual challenge (Major)
3. **IPA for вчитель** — fix phoneme and stress placement (Major)
4. **лікар "soft consonant" explanation** — remove false phonetic claim, simplify to "memorize this word" (Major)

**Should fix (non-blocking):**
5. Teach собака explicitly before using it in activities
6. Add 2-3 warmth markers (greeting, encouragement, celebration)
7. Clarify Name Day date (Julian vs Gregorian)
8. Add "дитина" to vocabulary YAML (recommended in plan)