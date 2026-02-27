**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|-----------------|
| 1 | Language Quality | 7/10 | Two typos in Ukrainian (doubled word «це це» L29, misspelling «спрярована» L88), awkward preposition «прізвиська про свої дії» L137, non-standard «концепт» L133. English is clear but overused as parallel translation. |
| 2 | Lesson Quality | 8/10 | Good PPP arc with clear "Mirror Rule" and "Chameleon Rule" mental models. Clean grammar table at L48-53. But no warm greeting at start, and the four large English paraphrase blocks break the tutoring flow. 4/5 on "Would I Continue?" test. |
| 3 | Activity Quality | 9/10 | 12 activities with excellent type variety (fill-in, match-up, unjumble, quiz, error-correction, group-sort, select, cloze, translate, true-false, mark-the-words). All grammar is correct. The cloze activity (L329-375) is especially well-designed with a natural market dialogue. |
| 4 | Immersion Balance | 7/10 | Audit reports 71.7% (within 60-75% target), but the implementation is flawed. Sections «Презентація: Відмінювання та узгодження» (L110), «Культурний контекст та вибір» (L147), «Практика та типові помилки» (L220), and «Діалоги та підсумок» (L252) each end with a dense English paragraph paraphrasing the Ukrainian above — parallel translation rather than scaffolded immersion. |
| 5 | Richness & Engagement | 8/10 | Two proverbs, Котигорошко folk reference, Бессарабський ринок/Привоз cultural anchors, 6 varied callout boxes. But missing key plan collocations: «яка різниця?», «Які помідори найсолодші?», «Мені подобається той, який...». |
| 6 | Factual Accuracy | 9/10 | Бессарабський ринок and Привоз are real landmarks (✓). «Який пан, такий жупан» proverb correctly explained (✓). Котигорошко folk tale accurate (✓). All grammar rules are correct. No fabricated claims. |
| 7 | LLM Fingerprint | 7/10 | Main signal: four English blocks (L110, L147, L220, L252) follow an identical structural pattern — each section ends with a ~150-word English paragraph restating the Ukrainian content. This is textbook LLM bilingual padding. No "це не просто" patterns. Section openings are varied. |
| 8 | Warmth & Humanity | 8/10 | Some direct address and encouragement (e.g., «Це ваш перший крок до створення красивих, складних описів» L55). Missing warm greeting at start (no "Привіт!"). "Don't worry" moments exist but only in English blocks. Closing has «Ми зробили величезний крок уперед» L258 which is good. |
| 9 | Vocabulary IPA | 6/10 | Four IPA errors in vocabulary file: яка missing stress mark '[jɑkɑ]' → should be '' (vocab L9); відмінок wrong stress '' → should be '' (vocab L62); родовий double stress '' → should be '' (vocab L146); підозрюваний wrong stress '' → should be '' (vocab L89). |

---

## Critical Issues Found

### Issue 1: Typo — Doubled Word (CRITICAL)

**Location:** Content L29, Section «Вступ: Опис за межами прикметників»

**Citation:** «Прислів'я та приказки — це це справжнє відображення того, як працює наша мова та наше мислення.»

**Problem:** Doubled «це це» — obvious typo, should be single «це».

**Fix:** Replace «це це справжнє» with «це справжнє» at L29.

---

### Issue 2: Typo — Misspelling (CRITICAL)

**Location:** Content L88, Section «Презентація: Відмінювання та узгодження»

**Citation:** «Це книга, **яку** я зараз читаю. (Дія спрярована на книгу).»

**Problem:** «спрярована» is not a Ukrainian word. Should be «спрямована» (directed).

**Fix:** Replace «спрярована» with «спрямована» at L88.

---

### Issue 3: Structural — English Paraphrase Block Pattern (MAJOR)

**Location:** Content L110, L147, L220, L252 (across all major sections)

**Problem:** Each of the four main sections ends with a dense English paragraph (~120-170 words each) that paraphrases the Ukrainian content above. This is parallel translation, not scaffolded immersion. At A2 Band 2, English should be used for abstract grammar concepts (which lines 59-62 do well), not to repeat narrative content.

**Examples:**
- Section «Презентація: Відмінювання та узгодження» L110: English paragraph repeats the dual-check agreement system already explained in Ukrainian
- Section «Культурний контекст та вибір» L147: English paragraph repeats the market culture description already given in Ukrainian
- Section «Практика та типові помилки» L220: English paragraph restates the «хто» vs «який» distinction and comma rule
- Section «Діалоги та підсумок» L252: English paragraph provides a generic module summary

**Fix:** Remove or drastically shorten these English blocks. Redistribute any unique content (if any) as brief English scaffolding notes inline within the Ukrainian flow. This would also reduce the word count overshoot from 110.6% toward the target while improving pedagogical quality.

---

### Issue 4: Vocabulary IPA Errors (MAJOR)

**Location:** Vocabulary file, 4 items

**Problems:**
1. **яка** (vocab L9): IPA `[jɑkɑ]` — missing stress mark. Яка́ is stressed on second syllable → ``
2. **відмінок** (vocab L62): IPA `` — stress on wrong syllable, impossible consonant cluster `dʲm`. Відмі́нок → ``
3. **родовий** (vocab L146): IPA `` — two stress marks (impossible). Родови́й → ``
4. **підозрюваний** (vocab L89): IPA `` — stress on wrong syllable. Підозрю́ваний → ``

**Fix:** Correct all four IPA transcriptions in the vocabulary file.

---

### Issue 5: Awkward Ukrainian Phrasing (MODERATE)

**Location:** Content L137, Section «Культурний контекст та вибір»

**Citation:** «Герої отримують цікаві прізвиська про свої дії.»

**Problem:** The preposition «про» does not collocate naturally with «прізвиська» in this context. Natural Ukrainian would use «за» (for/based on) — «прізвиська за свої дії» or a different construction: «прізвиська, пов'язані з їхніми діями».

**Fix:** Replace «прізвиська про свої дії» with «прізвиська за свої дії» at L137.

---

### Issue 6: Missing Plan Vocabulary Collocations (MODERATE)

**Location:** Affects Section «Культурний контекст та вибір» and Section «Діалоги та підсумок»

**Problem:** The plan's `vocabulary_hints.required` specifies key collocations that are absent from the content:
- «яка різниця?» — listed as a required collocation for яка (plan L98-99), nowhere in content
- «Які помідори найсолодші?» — listed in both plan content_outline and meta (meta L31), nowhere in content
- «Мені подобається той, який...» — listed as a dialogue prompt in plan (plan L64), nowhere in content

**Fix:** Integrate these collocations into the market dialogue (Section «Культурний контекст та вибір» L120-126) and the shopping dialogue (Section «Діалоги та підсумок» L238-249). For example, the market dialogue could include a vendor asking «Які помідори найсолодші?» and a customer responding «Яка різниця? Дайте ті, які найбільші».

---

### Issue 7: Non-Standard Word «концепт» (MINOR)

**Location:** Content L133, Section «Культурний контекст та вибір»

**Citation:** «Це дуже важливий концепт.»

**Problem:** «Концепт» is a non-standard anglicism/borrowing. At A2 level, the standard Ukrainian word «поняття» (concept) is more appropriate and more natural.

**Fix:** Replace «Це дуже важливий концепт» with «Це дуже важливе поняття» at L133 (note: поняття is neuter, so the adjective changes to «важливе»).

---

## Factual Verification

| Claim | Location | Verified? | Notes |
|-------|----------|-----------|-------|
| «Який пан, такий жупан» — proverb about status reflecting in clothing | L29-31 | ✓ | Real Ukrainian proverb, correctly explained |
| Жупан — traditional Ukrainian outer garment, status symbol | L31 | ✓ | Historically accurate |
| Бессарабський ринок у Києві | L129 | ✓ | Real market, central Kyiv |
| Привоз в Одесі | L129 | ✓ | Real and famous market |
| «Як ви човен назвете, так він і попливе» | L133 | ✓ | Real proverb; most common variant uses «корабель» but «човен» is a legitimate variant |
| Котигорошко — хлопець, який народився з горошини | L137 | ✓ | Accurate folk tale summary |
| Grammar: Accusative masc inanimate = Nominative form | L69-70 | ✓ | Correct rule |
| Grammar: Accusative masc animate = якого | L73-74 | ✓ | Correct rule |
| Grammar: Comma always before який | L168 | ✓ | Correct punctuation rule |
| Grammar: «Який» not «хто» for describing people | L155 | ✓ | Correct rule |

**No factual errors found.** All cultural references and grammar rules are accurate.

---

## Verification Summary

### Plan Compliance
- **Sections:** All 5 required H2 sections present: «Вступ: Опис за межами прикметників» ✓, «Презентація: Відмінювання та узгодження» ✓, «Культурний контекст та вибір» ✓, «Практика та типові помилки» ✓, «Діалоги та підсумок» ✓
- **Grammar scope:** Covers який declension in Nominative, Accusative, and Genitive (Genitive is minor scope creep but brief and useful)
- **Objectives:** All 4 objectives addressed — connecting sentences ✓, declining який ✓, describing people/objects ✓, punctuation ✓
- **Missing items:** 3 required collocations absent (яка різниця?, Які помідори найсолодші?, Мені подобається той, який...)

### Colonial Framing Check
**PASS** — No instances of defining Ukrainian by contrast with Russian. Grammar is presented on its own terms.

### LLM Fingerprint Summary
- No «це не просто» / «це не лише» patterns ✓
- No generic AI clichés (діамант, двигун прогресу, etc.) ✓
- Section openings are varied ✓
- **FAIL:** Structural monotony in English blocks — all 4 major sections end with identical pattern (dense English paraphrase paragraph). This is bilingual padding.
- Callout titles are all unique ✓

### "Would I Continue?" Test (Beginner)
| Question | Result |
|----------|--------|
| Did I feel overwhelmed? | **PASS** — Grammar introduced progressively with clear mental models |
| Were instructions clear? | **PASS** — Mirror Rule and Chameleon Rule are excellent pedagogical analogies |
| Did I get quick wins? | **PASS** — Nominative forms table at L48-53 provides immediate success |
| Was Ukrainian scary? | **PASS** — Scaffolded with English for abstract concepts |
| Would I come back tomorrow? | **BORDERLINE** — Dense English blocks at section ends feel like a textbook, not a tutor |

**Result: 4/5 → Lesson Quality 8-9/10** (scored 8 due to missing warm opening)

### Emotional Safety
- ✓ Curiosity trigger: «Чому це важливо?» block at opening
- ✗ Warm welcome: No "Привіт!" or equivalent
- ✓ Quick wins: Nominative form table
- ✓ Encouragement: «Це ваш перший крок» L55, «Результат вартий зусиль» L218
- ✓ Progress marker: «Ми зробили величезний крок уперед» L258

---

## Verdict

**FAIL — Requires targeted repairs.**

**Blocking issues (must fix before pass):**
1. **Two Ukrainian typos** — «це це» (L29) and «спрярована» (L88) are errors that would undermine learner trust
2. **4 IPA errors in vocabulary** — wrong stress marks, double stress, and impossible consonant clusters
3. **Missing plan collocations** — 3 required items from vocabulary_hints absent

**High-priority improvements (strongly recommended):**
4. **English paraphrase blocks** — restructure the 4 dense English paragraphs (L110, L147, L220, L252) into brief inline scaffolding notes; this also addresses the LLM fingerprint issue
5. **Awkward Ukrainian** — fix «прізвиська про свої дії» → «прізвиська за свої дії» (L137) and «концепт» → «поняття» (L133)

**What works well:**
- Excellent activity suite (12 activities, outstanding type variety)
- "Mirror Rule" and "Chameleon Rule" pedagogical analogies are memorable and effective
- Cultural integration (proverbs, market culture, Котигорошко) is authentic
- Grammar accuracy is flawless across content and activities
- No colonial framing, no Russianisms