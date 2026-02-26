<!-- content-hash: 50d50e3e6cbc -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Weight | Weighted |
|---|-----------|-------|--------|----------|
| 1 | Language Quality | 7 | 2.0 | 14.0 |
| 2 | Lesson Quality | 7 | 2.0 | 14.0 |
| 3 | Factual Accuracy | 9 | 1.5 | 13.5 |
| 4 | Activity Quality | 7 | 1.5 | 10.5 |
| 5 | Immersion Balance | 9 | 1.0 | 9.0 |
| 6 | LLM Fingerprint | 8 | 1.0 | 8.0 |
| 7 | Richness | 8 | 1.0 | 8.0 |
| 8 | Humanity & Warmth | 6 | 1.5 | 9.0 |
| | **Weighted Total** | | **11.5** | **76.0 / 115 = 66.1%** |

---

### Dimension 1: Language Quality — 7/10

**Ukrainian grammar errors found:**

1. **Line 175** — «Відомий підприємець був мусив **закрити бізнес** через раптову світову фінансову кризу..» — The construction «був мусив» is grammatically non-standard. Standard Ukrainian uses either «мусив» (simple past) or «був змушений» (was forced). «Був мусив» is a malformed pluperfect attempt.

2. **Line 87** — «Я вчора **написав** довгого листа своєму другові..» — The genitive «довгого листа» with «написати» is non-standard. «Лист» is masculine inanimate; the accusative should match nominative: «написав довгий лист». Using genitive here is dialectal/archaic and confusing for A2 learners who are being taught grammar rules.

3. **Line 84** — Code-switch inside Ukrainian sentence: «Згідно з Державним стандартом української мови, глибоке розуміння aspectual pairs є абсолютно критичним для опанування рівня А2.» — The English term "aspectual pairs" sits untranslated inside a Ukrainian sentence. Should be «видових пар» with an English gloss in parentheses.

**Sentence fragmentation (4+ instances):**

4. **Line 64** — «Якщо ви зробили помилку в роботі. Або якщо результат вас не влаштовує. Вам потрібно зробити дію знову.» — Three sentence fragments using periods where commas are needed. An A2 grammar module should model correct sentence structure.

5. **Line 168** — «Коли українці чують фразу «закрити двері». Це звучить так само дивно, як «відкрити двері».» — Period after «двері» creates an incomplete subordinate clause.

6. **Line 179** — «Коли ви працюєте в сучасному офісі в Україні. Ви будете щодня чути про необхідність «закрити проект» або «закрити завдання».» — Same fragment pattern: subordinate clause terminated by period.

7. **Line 225** — «Ви більше ніколи не зробите помилку. Спілкуючись з вашими колегами чи друзями. Це надійна база вашої просторової орієнтації в українській мові.» — Dangling adverbial participle clause made into its own sentence.

**Systematic double-period formatting error:** 30+ lines end with `..` instead of `.` (lines 38, 41, 78, 87, 88, 108-111, 129-132, 146-150, 174-177, 191-194, 201-203, 265-267). This is a systematic proofreading failure.

---

### Dimension 2: Lesson Quality — 7/10

**"Would I Continue?" Test (A2 beginner):**

| Question | Result |
|----------|--------|
| Did I feel overwhelmed? | **FAIL** — Opening epigraph (lines 10-12) is dense Ukrainian prose for A2. No gentle onboarding. |
| Were instructions clear? | **PASS** — English explanations are generally clear, though some terms (e.g., "aspectual pairs" line 84) are unexplained. |
| Did I get quick wins? | **FAIL** — No practice until Section «Практика: Трансформація смислів» (line 209). That's ~2400 words of pure exposition before the learner does anything. |
| Was Ukrainian scary? | **PASS** — Ukrainian is introduced with English scaffolding throughout. |
| Would I come back tomorrow? | **PASS** — Content is interesting and the LEGO metaphor is engaging. |

**Result: 3/5 Pass → Lesson Quality base = 8, minus 1 for missing warm welcome = 7**

**Missing lesson arc elements:**
- **WELCOME**: No "Привіт!" or warm greeting. The module opens with a philosophical Ukrainian epigraph about why prefixes matter. Cold start.
- **PREVIEW**: No clear "Today you'll learn..." statement in English. The `> **Чому це важливо?**` block (lines 10-12) serves this purpose but is entirely in Ukrainian and too abstract for A2.
- **CELEBRATE**: The summary (Section «Діалоги та підсумок», line 308) provides some celebration but is didactic rather than warm: «Сьогодні ми зробили великий крок» rather than "You can now..."

**Pacing failure:** The module presents approximately 15-20 new vocabulary items across sections «Вступ: Логіка LEGO в українських дієсловах», «Презентація: Світ префіксів пере-, до- та по-», and «Відчинити чи відкрити? Битва за простір» before any practice opportunity. The A2 maximum is ≤5-7 new words per section before practice.

---

### Dimension 3: Factual Accuracy — 9/10

**Grammar explanations verified:**
- Prefix пере- meanings (repetition, copying, transferring) — **Correct**
- Prefix до- completion semantics — **Correct**
- Prefix по- delimitative meaning — **Correct**
- Prefix за- three faces (closing, sudden start, excess) — **Correct**
- відчинити vs відкрити distinction — **Correct** per literary Ukrainian standard

**Cultural claims verified:**
- Line 47: «bread is the head of everything» — Accurate rendering of Ukrainian proverb «Хліб — усьому голова» ✓
- Line 56-58: Bread respect cultural practice (picking up fallen bread) — **Plausible**, well-documented cultural practice ✓

**One oversimplification (minor):**
- Line 138: The [!myth-buster] block states «В сучасній українській літературній мові це категорично неправильно» about «відкрити двері». While non-literary, calling it "категорично неправильно" is a pedagogical oversimplification — the SUM-11 dictionary and some modern sources do allow context-dependent use of «відкрити» for doors. For A2, the simplification is defensible but the tone «Ця груба помилка» is unnecessarily aggressive.

---

### Dimension 4: Activity Quality — 7/10

**Activity count:** 12 activities ✓ (quiz, error-correction, fill-in, match-up, unjumble ×2, group-sort, true-false, cloze, select, translate, mark-the-words)

**Critical issue — Translate activity title error:**
- Line 374: `title: "Переклад англійською"` (Translation to English) — but the activity presents English `source` sentences and asks learners to select Ukrainian translations. The title should be "Переклад українською" or "З англійської на українську". This will confuse learners about what they're supposed to do.

**Activity variety:** 12 distinct types — excellent variety (≥40% threshold easily met).

**Distractor quality:** Generally good. Error-correction and fill-in items have plausible wrong options that test specific prefix knowledge.

**Missing activity issue — no graduated difficulty:** All activities test roughly the same cognitive level (recognition/selection). No progression from easier to harder within or across activities. For A2 PPP methodology, activities should scaffold from controlled to freer practice.

**Cloze passage (lines 248-282):** Well-constructed with a coherent narrative and 10 blanks. Good contextual clues. This is the strongest activity.

---

### Dimension 5: Immersion Balance — 9/10

Pre-computed immersion: 71.3% (target: 60-75%). Within range. English is used consistently for grammatical explanations and instructions. Ukrainian is used for examples, dialogues, and cultural content. The balance is appropriate for A2 M38 (late A2, immersion band 60-75%).

One minor concern: Section «Вступ: Логіка LEGO в українських дієсловах» subsection «Культурний контекст: Повага до хліба та префікс до-» (lines 45-58) has a dense Ukrainian paragraph (lines 54-55) that may challenge A2 readers without inline glosses. But overall balance is solid.

---

### Dimension 6: LLM Fingerprint — 8/10

**Structural monotony test:** First lines of H2 sections are varied — no 3+ identical openers. ✓ Pass.

**"це не просто" / "це не лише" test:**
- Line 54: «Це не просто "їсти", це довести процес харчування до кінця.»
- Line 310: «Префікси — це не просто випадковий набір літер.»
- 2 instances — at the threshold. Both are pedagogically natural usages, not AI filler.

**Example formatting uniformity:** Sections «Презентація: Світ префіксів пере-, до- та по-» and «Відчинити чи відкрити? Битва за простір» both use identical `* sentence with **bolded verb**..` bullet format extensively. However, these are interspersed with tables (lines 115-119, 154-157, 217-224) and a dialogue (lines 281-287), providing sufficient format variation.

**Callout monotony:** 5 callouts use 5 different types ([!culture], [!warning], [!myth-buster], [!note], [!tip]) — no repetition. ✓ Pass.

**Verbosity/padding detection:** Line 279 contains a repeated sentence: «До дедлайну залишилося катастрофічно мало часу. До офіційного дедлайну залишилося катастрофічно мало часу.» — This is likely a copy-paste artifact, not intentional emphasis.

---

### Dimension 7: Richness — 8/10

**Cultural hooks:** The "Bread Respect" cultural section (lines 45-58) is well-developed and culturally authentic. The [!culture] callout about bread-kissing tradition is a strong engagement element.

**Tables:** 3 comparison tables (lines 115-119, 154-157, 217-224) provide visual organization. Good.

**Dialogue:** The Writer-Editor dialogue (Section «Діалоги та підсумок», lines 281-287) is contextually rich and demonstrates natural prefix usage. However, it's only 7 turns, not the 10 required by the plan.

**Missing elements:**
- No IPA pronunciation guidance anywhere in the content file. The vocabulary file has IPA, but learners reading the lesson see no pronunciation help.
- No images, no audio references, no mnemonics beyond the LEGO and "Hinges Rule" metaphors.

**Named Ukrainian references:** Хліб tradition, proverb «Хліб — усьому голова» (referenced in English translation), characters Тарас and Олена in dialogue. Adequate.

---

### Dimension 8: Humanity & Warmth — 6/10

**Warmth marker count:**

| Marker | Count | Minimum | Status |
|--------|-------|---------|--------|
| Direct address (you/ви) | ~20+ | ≥15 | ✓ Pass |
| Encouragement phrases | 2 | ≥3 | ✗ FAIL |
| "Don't worry" moments | 1 (line 284, in dialogue only) | ≥2 | ✗ FAIL |
| "You can now..." validation | 1 (line 312, weak) | ≥2 | ✗ FAIL |

**Total warmth markers: ~4 (borderline).** The module reads like a university textbook, not a patient tutor. The persona specified is "Encouraging Cultural Guide" acting as "Film Director" — the content delivers on "Cultural Guide" but not on "Encouraging."

**Specific coldness examples:**
- No greeting at all — the module opens with a Ukrainian philosophy paragraph
- Section «Практика: Трансформація смислів» office scenario (line 229) uses language like "Your professional task as a language expert" — this is formal, not warm
- Line 138 myth-buster uses «Ця груба помилка» (this crude mistake) — an aggressive phrasing for a nervous A2 learner
- The closing (lines 308-319) is summary-oriented, not celebratory

**This score approaches the COLD_PEDAGOGY threshold.** While not auto-fail (≥3 markers present), the module's emotional register is consistently cool and academic rather than warm and supportive.

---

## Critical Issues Found

### Issue 1: CRITICAL — Systematic sentence fragmentation (Language)

**Locations:** Lines 64, 168, 179, 225
**Pattern:** Subordinate clauses and adverbial participle phrases are terminated with periods instead of commas, creating grammatically incorrect sentence fragments.

**Example (line 64):** «Якщо ви зробили помилку в роботі. Або якщо результат вас не влаштовує. Вам потрібно зробити дію знову.»
**Should be:** «Якщо ви зробили помилку в роботі, або якщо результат вас не влаштовує, вам потрібно зробити дію знову.»

**Example (line 225):** «Ви більше ніколи не зробите помилку. Спілкуючись з вашими колегами чи друзями. Це надійна база вашої просторової орієнтації в українській мові.»
**Should be:** «Ви більше ніколи не зробите помилку, спілкуючись з вашими колегами чи друзями — це надійна база вашої просторової орієнтації в українській мові.»

**Impact:** A grammar module that models broken grammar is self-undermining. Requires fix in 4+ locations.

### Issue 2: CRITICAL — Missing warmth for A2 beginner module (Warmth)

**Pattern:** The module lacks a warm welcome, has insufficient encouragement phrases (<3), and reads like a textbook. No "Привіт!", no "Today you'll learn...", no "Don't worry, this is normal" outside the dialogue.

**Impact:** Fails the "Encouraging Cultural Guide" persona. A2 learners need emotional safety. The module's academic register risks discouraging fragile beginners.

### Issue 3: HIGH — Systematic double-period formatting error

**Locations:** Lines 38, 41, 78, 87, 88, 108-111, 129-132, 146-150, 174-177, 191-194, 201-203, 265-267 (30+ occurrences)
**Pattern:** Sentences end with `..` instead of `.`
**Example (line 78):** «Я дуже хочу **передати** теплий привіт моїй родині в Києві..»
**Impact:** Unprofessional appearance. Simple find-and-replace fix, but the volume indicates a systematic generation artifact.

### Issue 4: HIGH — Grammar error «був мусив» (Language)

**Location:** Line 175
**Text:** «Відомий підприємець був мусив **закрити бізнес** через раптову світову фінансову кризу..»
**Fix:** Replace «був мусив» with «мусив» or «був змушений».

### Issue 5: HIGH — Translate activity title is backwards (Activities)

**Location:** Activities YAML line 374
**Text:** `title: "Переклад англійською"` — but the activity translates FROM English TO Ukrainian.
**Fix:** Change to `title: "Переклад українською"` or `title: "З англійської на українську"`.

### Issue 6: MEDIUM — Non-standard genitive case with «написати» (Language)

**Location:** Line 87
**Text:** «Я вчора **написав** довгого листа своєму другові..»
**Fix:** Change to «Я вчора **написав** довгий лист своєму другу.» (accusative for masculine inanimate).

### Issue 7: MEDIUM — English term in Ukrainian sentence (Language)

**Location:** Line 84
**Text:** «Згідно з Державним стандартом української мови, глибоке розуміння aspectual pairs є абсолютно критичним для опанування рівня А2.»
**Fix:** Replace "aspectual pairs" with «видових пар (aspectual pairs)».

### Issue 8: MEDIUM — Scope gap: prefixes на- and роз- missing

**Evidence:** The meta file lists `prefix від-/роз- (opening)` and `prefix на- (accumulate)` in the grammar scope, but the content never addresses роз- or на-. The SCOPE comment (line 2) mentions від-/роз- but only від- is covered (briefly, via віддати in Section «Практика: Трансформація смислів»).

### Issue 9: MEDIUM — Dialogue is 7 turns, not 10 as planned

**Evidence:** The plan requires "a 10-line high-immersion dialogue" in Section «Діалоги та підсумок». The actual dialogue (lines 281-287) has only 7 turns. Needs 3 more turns to meet the plan specification.

### Issue 10: LOW — Duplicated sentence (Proofreading)

**Location:** Line 279
**Text:** «До дедлайну залишилося катастрофічно мало часу. До офіційного дедлайну залишилося катастрофічно мало часу.»
**Fix:** Remove the duplicate sentence.

### Issue 11: LOW — Vocabulary IPA error for відчинити

**Location:** Vocabulary YAML line 3
**Text:** `ipa: ''`
**Issue:** The cluster «дч» in від+чинити should yield [dt͡ʃ] or [t̚t͡ʃ], not [d͡ʒt͡ʃ]. The notation [d͡ʒ] implies a voiced postalveolar affricate (Ukrainian «дж») that is not present here.
**Fix:** Change to `''` or `''`.

---

## Colonial Framing Check

One instance found in the [!myth-buster] block (line 138): «Ця груба помилка прийшла в українську мову через російський вплив. Де слово «открыть» використовується для всього.» This references Russian but is within a legitimate surzhyk-debunking callout — **exempt per review protocol**. No other colonial framing detected. However, the tone «Ця груба помилка» is unnecessarily harsh for A2 learners.

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections present per plan | ✓ All 5 sections present |
| Section «Вступ: Логіка LEGO в українських дієсловах» | ✓ Present, covers LEGO metaphor, phrasal verbs, bread culture |
| Section «Презентація: Світ префіксів пере-, до- та по-» | ✓ Present, covers all 3 prefixes with examples |
| Section «Відчинити чи відкрити? Битва за простір» | ✓ Present, covers hinges rule, closing pairs, за- triple function |
| Section «Практика: Трансформація смислів» | ✓ Present, has table, 8 office scenarios, "Give" family |
| Section «Діалоги та підсумок» | ✓ Present, but dialogue under-length (7/10 turns) |
| Vocabulary scope vs plan | ✓ All required + recommended items present |
| Grammar scope vs meta | ✗ Missing на- (accumulate) and роз- entirely |
| Word count | ✓ 3865/3000 (128.8%) — above minimum |
| Activity count | ✓ 12 activities |
| Engagement boxes | ✓ 5 boxes, 5 different types |
| Immersion | ✓ 71.3% within 60-75% target |
| Russianisms | None detected |
| Colonial framing | Exempt instance only (myth-buster block) |
| Double periods (..) | ✗ 30+ occurrences — systematic formatting error |
| Sentence fragments | ✗ 4+ locations — grammar modeling error |
| Warm welcome | ✗ Missing |
| "Would I Continue?" | 3/5 Pass |

---

## Fix Plan

### Priority 1: Language Quality fixes (target: 7→8)
1. **Fix all sentence fragments** at lines 64, 168, 179, 225 — join clauses with commas or dashes
2. **Fix «був мусив»** at line 175 → «мусив» or «був змушений»
3. **Fix «написав довгого листа»** at line 87 → «написав довгий лист»
4. **Fix code-switch** at line 84 → «видових пар (aspectual pairs)»
5. **Fix all double periods** — global find-replace `..` → `.` on all example lines
6. **Remove duplicate sentence** at line 279

### Priority 2: Humanity & Warmth injection (target: 6→8)
1. **Add warm welcome** before line 10: a "Привіт!" greeting with English learning objectives ("Today you'll learn how to transform basic verbs using prefixes")
2. **Add 3+ encouragement phrases** throughout: after the LEGO intro ("This is simpler than it looks!"), after the bread culture section ("You're already thinking like a Ukrainian speaker!"), after the practice section ("Great job!")
3. **Add 2+ "Don't worry" moments**: after the пере- section ("Don't worry if these feel similar — context will always tell you which one to use"), and before the за- triple function
4. **Soften aggressive language** at line 138: change «Ця груба помилка» to something like «Ця поширена помилка»
5. **Add celebration closing**: change the summary (line 308+) to include "You can now..." statements

### Priority 3: Activity fixes (target: 7→8)
1. **Fix translate title** at activities line 374: change «Переклад англійською» → «Переклад українською»

### Priority 4: Scope compliance
1. **Add brief coverage of на-** (even 2-3 examples: написати → написати, набрати) in Section «Презентація: Світ префіксів пере-, до- та по-» or as a callout
2. **Expand dialogue** in Section «Діалоги та підсумок» from 7 to 10 turns
3. **Fix IPA** for відчинити in vocabulary: `` → ``

---

## Verdict

**FAIL — Requires D.2 repair.**

The module has strong pedagogical content: the LEGO metaphor is effective, the відчинити/відкрити distinction is well-taught, the cultural bread hook is authentic, and the activity variety is excellent. However, three categories of issues prevent a pass:

1. **Language modeling errors** (sentence fragments in a grammar module, non-standard case usage, systematic double periods) undermine the module's core teaching mission.
2. **Insufficient warmth** for an A2 beginner module — the "Encouraging Cultural Guide" persona is not delivered. The module reads like a university textbook, not a patient tutor.
3. **Activity title error** and **scope gaps** (missing на-, роз-) reduce completeness.

The D.2 repair should focus on: (a) fixing all sentence fragments and grammar errors, (b) injecting warmth throughout with a greeting, encouragement phrases, and celebration, (c) fixing the activity title, and (d) adding brief на- coverage and extending the dialogue.