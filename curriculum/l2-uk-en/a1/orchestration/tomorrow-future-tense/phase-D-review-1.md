**Reviewed-By:** claude-opus-4-6

---

# Phase D.1 Review: Tomorrow - Future Tense (a1-22)

**Module:** `a1-22 / tomorrow-future-tense`
**Level:** A1.3 (Consolidation)
**Persona:** Patient Supportive Tutor / Event Planner
**Word count:** 2186 / 2000 (109.3%)
**Activities:** 10 | **Vocabulary:** 21 | **Engagement boxes:** 6

---

## Scores

| # | Dimension | Score | Notes |
|---|-----------|-------|-------|
| 1 | Plan Compliance | 6/10 | Synthetic future FYI missing; required collocations absent; persona/roleplay absent |
| 2 | Lesson Quality | 8/10 | 4/5 on "Would I Continue?" — warm, encouraging, but non-sequitur Ukrainian in section 1 |
| 3 | Language Quality | 8/10 | Ukrainian grammar accurate throughout; one premature imperative; proverb truncated |
| 4 | Activity Quality | 7/10 | "Сьогодні" error in group-sort contradicts lesson content; 3 orphan vocab items |
| 5 | Immersion Balance | 8/10 | 35.9% within configured target (35-55%); appropriate for grammar-heavy presentation |
| 6 | Richness | 7/10 | Good cultural hooks (proverb, Carpathians); but Event Planner persona invisible; missing planned collocations |
| 7 | Warmth & Humanity | 8/10 | LEGO analogy, regular encouragement, clear closing — but needs more "You can now..." beats |
| 8 | LLM Fingerprint | 8/10 | Uniform bullet-list example format across 5+ sections; one filler sentence |
| 9 | Factual Accuracy | 9/10 | Grammar rules, conjugation table, cultural notes all verified correct |

---

## Critical Issues Found

### Issue 1: ACTIVITY_ERROR — "сьогодні" classified as "Not Future" (activities YAML line 100)

**Location:** Activity 5 (group-sort "Коли це?"), YAML line 96-100

The group-sort activity places «сьогодні» in the "Не майбутнє (Not Future)" group. However, the lesson itself uses «сьогодні» in a future-tense context at content line 239:

> «Що ти **будеш робити** сьогодні ввечері?»

This directly contradicts the lesson's own dialogue in section «Практика: Діалоги про плани». A learner who correctly learned from Діалог 1 that "сьогодні" can appear in future-tense sentences will be marked wrong in this activity. "Сьогодні" is a time-neutral adverb that works with any tense — classifying it as inherently "not future" is factually wrong.

**Fix:** Remove «сьогодні» from the "Не майбутнє" group. Replace it with a genuinely past-only marker like «позавчора» (the day before yesterday).

### Issue 2: MISSING_PLAN_CONTENT — Synthetic future FYI entirely absent

**Location:** Applies to section «Граматика: Майбутній час (Я буду...)»

The plan (plans/a1/tomorrow-future-tense.yaml, line 25-26) explicitly requires:

> "Синтетичний майбутній час (працюватиму, працюватимеш) — ознайомчий огляд (FYI) для розпізнавання в автентичних текстах без глибокого вивчення на рівні A1."

The content SCOPE comment (line 4) says "Synthetic future forms (-му, -меш) → A2", actively contradicting the plan. A brief FYI note (e.g., a `[!note]` box saying "You may see forms like 'працюватиму' — this is another way to express the future. We will learn this at A2.") is required so learners aren't confused when they encounter these forms in authentic texts.

**Fix:** Add a brief `[!note]` box at the end of section «Граматика: Майбутній час (Я буду...)» introducing the synthetic forms as recognition-only, with 2-3 examples and a clear "you don't need to produce these yet" message.

### Issue 3: MISSING_PLAN_CONTENT — Required high-frequency time collocations

**Location:** Applies to section «Коли це буде? (Частина 1: Конкретний час)»

The plan's vocabulary_hints.required (line 48-49) lists:

> "завтра (tomorrow) — завтра вранці, завтра вдень, завтра ввечері; High frequency (Top 100)"

None of these three collocations appear anywhere in the content. These are among the most frequent future time expressions in spoken Ukrainian. The content presents «завтра» in isolation (lines 125, 129-132) but never teaches the natural collocations «завтра вранці», «завтра вдень», or «завтра ввечері».

**Fix:** Add a subsection within section «Коли це буде? (Частина 1: Конкретний час)» after line 132 presenting these three collocations with example sentences. They should also be added to the vocabulary YAML.

---

## Additional Issues

### Issue 4 (Major): ORPHAN_VOCABULARY — 3 vocab items unused in content or activities

**Location:** Vocabulary YAML lines 65-80

Three vocabulary items — «сподіватися» (to hope), «мріяти» (to dream), «обіцяти» (to promise) — appear in the vocabulary YAML but are never introduced, exemplified, or practiced in either the lesson content or the activities. Learners encounter these only if they browse the vocabulary list separately, with no context for understanding or retention.

**Fix:** Either (a) integrate these verbs into section «Плани та наміри: Що ми будемо робити?» as additional ways to express plans (e.g., "Я мрію поїхати в Італію" — I dream of going to Italy; "Я сподіваюся, що все буде добре" — I hope everything will be fine), or (b) remove them from the vocabulary YAML if they're out of scope.

### Issue 5 (Major): NON_SEQUITUR_UKRAINIAN — Untaught imperative forms, line 27

**Location:** Section «Розминка: Час летить (Time Flies)», line 27

The sentence «Українська мова — це музика. Слухайте і говоріть.» appears mid-paragraph, disconnected from the surrounding explanation about «бу́ду» as a helper word. The imperative forms «слухайте» and «говоріть» have not been taught at this point in A1. For a nervous beginner, an untranslated imperative sentence dropped into an English explanation is jarring.

**Fix:** Remove this sentence or replace it with an encouraging English-only line. The translation in parentheses doesn't fully mitigate the issue — the imperative grammar is a distraction from the lesson's focus on future tense.

### Issue 6 (Major): TRUNCATED_PROVERB — Line 110

**Location:** Section «Плани та наміри: Що ми будемо робити?», line 110

The content gives «Не кажи 'гоп'!» but the plan specifically references the full proverb: «Не кажи 'гоп', поки не перескочиш». The truncated version loses the meaning ("Don't say 'hop' until you've jumped over"). The full form is the culturally important element.

**Fix:** Replace «Не кажи 'гоп'!» with the full proverb «Не кажи 'гоп', поки не перескочиш» and translate it fully.

### Issue 7 (Major): MISSING_COLLOCATIONS — zbиратися phrases absent

**Location:** Section «Плани та наміри: Що ми будемо робити?»

The plan (vocabulary_hints line 57) requires collocations "збиратися додому, збиратися в дорогу". The content uses «збиратися» with «читати книгу», «в кіно», «працювати», «спати», «гуляти» (lines 98-102) but never presents the plan-required collocations. «Збиратися додому» (to head home) and «збиратися в дорогу» (to prepare for a journey) are high-utility phrases absent from the lesson.

**Fix:** Add these two collocations to the examples in section «Плани та наміри: Що ми будемо робити?», subsection "Я збираюся...".

### Issue 8 (Minor): MISSING_DRILL_PATTERN — наступного понеділка vs у понеділок

**Location:** Section «Коли це буде? (Частина 1: Конкретний час)»

The meta's content_outline (line 33 in meta) specifies "Drill patterns: наступного понеділка vs у понеділок (future context)". This contrastive pair is entirely absent from the content. The genitive-of-time explanation (lines 135-146) covers тижня/року/разу/місяця but never shows the day-of-week pattern, which is arguably more common in everyday speech.

**Fix:** Add 2-3 examples contrasting «наступного понеділка» with «у понеділок» to section «Коли це буде? (Частина 1: Конкретний час)».

### Issue 9 (Minor): PERSONA_UNDERDEVELOPED — Event Planner invisible

**Location:** Module-wide

The meta specifies `persona.role: Event Planner` and the plan requires a "рольова гра 'Організатор подій'" (roleplay as Event Planner). Neither appears in the content. The module reads as a generic patient tutor — there is no event-planning framing, no "let's plan an event together" thread, no roleplay activity. Section «Наші плани: Вихідні та відпустка» comes closest but doesn't adopt the persona.

**Fix:** Thread an event-planning scenario through the lesson — e.g., "Imagine you are planning a party for a friend" as a recurring frame, culminating in a roleplay exercise.

---

## Factual Verification

### Callout Box Verification

| Callout | Location | Claim | Verdict |
|---------|----------|-------|---------|
| `[!tip]` "Teacher's Tip" (line 29) | Section «Розминка» | LEGO analogy for grammar building | **OK** — pedagogical analogy, no factual claim |
| `[!warning]` "Attention" (line 60) | Section «Граматика» | «буду» only with imperfective verbs | **CORRECT** — compound future (буду + infinitive) is indeed imperfective only per §4.2.4.1 |
| `[!cultural]` "Do not say hop" (line 108) | Section «Плани та наміри» | Proverb «Не кажи 'гоп'!» about not boasting early | **PARTIALLY CORRECT** — proverb exists but is truncated (see Issue 6) |
| `[!note]` "Observation" (line 148) | Section «Коли це буде? (Ч.1)» | -ого ending shows time of action | **CORRECT** — genitive case for temporal expressions is accurate |
| `[!quote]` "Folk Wisdom" (line 186) | Section «Коли це буде? (Ч.2)» | «Завтра буде новий день» as a phrase of hope | **CORRECT** — this is a well-known Ukrainian expression |
| `[!cultural]` "Carpathians" (line 228) | Section «Наші плани» | "Going to the mountains" = going to the Carpathians for Ukrainians | **CORRECT** — accurate cultural observation |

### Grammar Rule Verification

| Rule | Location | Verdict |
|------|----------|---------|
| Compound future = буду + infinitive | Line 40-42 | **CORRECT** |
| Conjugation table: буду, будеш, буде, будемо, будете, будуть | Lines 54-58 | **CORRECT** — all 6 forms accurate |
| «Буду» only with imperfective verbs | Lines 60-63 | **CORRECT** |
| Genitive of time: наступного тижня/року | Lines 135-146 | **CORRECT** |
| Reflexive verb збиратися conjugation | Lines 96-104 | **CORRECT** — збираюся, збираєшся, збирається all accurate |

**No factual errors found in grammar rules or cultural notes.**

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing | **CLEAR** — No Ukrainian-defined-via-Russian patterns found |
| Russianisms | **CLEAR** — No кушати, приймати участь, красивий, прекрасне detected |
| LLM fingerprint — section openings | **PASS** — 8 sections, all open differently |
| LLM fingerprint — example batching | **MARGINAL** — 5 sections use identical `* **Ukrainian** ... (English.)` bullet format; acceptable for A1 grammar |
| LLM fingerprint — AI rhetoric | **PASS** — No "це не просто", "In this lesson we will explore" patterns |
| Callout monotony | **PASS** — 6 callouts, all different types |
| Factual accuracy | **PASS** — All grammar rules verified correct |
| Activity error | **FAIL** — "сьогодні" in "Not Future" contradicts lesson content |
| Plan compliance — synthetic future | **FAIL** — Required FYI absent |
| Plan compliance — time collocations | **FAIL** — завтра вранці/вдень/ввечері absent |
| Plan compliance — persona | **FAIL** — Event Planner roleplay absent |
| Orphan vocabulary | **FAIL** — 3 items in vocab YAML not used in content or activities |

### "Would I Continue?" Test (Beginner Safety)

| Question | Result |
|----------|--------|
| Did I feel overwhelmed? | **PASS** — comfortable pacing, manageable chunks |
| Were instructions clear? | **PASS** — always knew what to do |
| Did I get quick wins? | **PASS** — formula + examples early, practice follows |
| Was Ukrainian scary? | **MARGINAL** — mostly gentle, but line 27 imperative is jarring |
| Would I come back tomorrow? | **PASS** — encouraging tone, satisfying closing |

**Result: 4/5 PASS → Lesson Quality 8**

### Emotional Safety Mapping

| Required Beat | Present? | Location |
|---------------|----------|----------|
| Welcome/orientation | **YES** | Lines 11-13 ("We have already learned...") |
| Curiosity trigger | **YES** | Line 25 ("I have great news for you") |
| Quick win #1 | **YES** | Lines 45-49 (formula + first examples) |
| Quick win #2 | **YES** | Lines 68-76 (sentences in action) |
| Encouragement | **YES** | Line 31 ("Do not be afraid to make mistakes") |
| Progress marker | **YES** | Lines 293-300 (summary list) |
| "You can now..." | **PARTIAL** | Line 293 says "Now you can speak about..." but could be stronger |

---

## Section Coverage

All 8 H2 sections reviewed:

1. **Section «Розминка: Час летить (Time Flies)»** — Warm opening, good timeline visual, but line 27 non-sequitur issue (Issue 5)
2. **Section «Граматика: Майбутній час (Я буду...)»** — Clear formula, accurate conjugation table, good examples; missing synthetic future FYI (Issue 2)
3. **Section «Плани та наміри: Що ми будемо робити?»** — Good want/intend/will comparison table; truncated proverb (Issue 6), missing collocations (Issue 7)
4. **Section «Коли це буде? (Частина 1: Конкретний час)»** — Genitive-of-time well explained; missing завтра вранці/вдень/ввечері (Issue 3), missing drill pattern (Issue 8)
5. **Section «Коли це буде? (Частина 2: Абстрактний час)»** — Good скоро/незабаром distinction, word order note; adequate
6. **Section «Наші плани: Вихідні та відпустка»** — Good vocabulary, model sentences, Carpathians hook; closest to Event Planner persona but doesn't commit (Issue 9)
7. **Section «Практика: Діалоги про плани»** — Three natural dialogues with named characters; good progression from informal (evening) to practical (holidays to family weekend)
8. **Section «Практика: Мій ідеальний день завтра»** — Two narrative texts plus analysis; effective comprehension practice

---

## Verdict

**NEEDS_REVISION**

The module has strong foundations — accurate grammar, warm tutoring voice, good dialogue practice, and correct factual content. However, it has significant plan compliance gaps (synthetic future FYI, required collocations, Event Planner persona/roleplay) and one clear activity error ("сьогодні" in "Not Future"). These issues affect scope coverage and could confuse learners. A targeted D.2 repair pass should address the 9 issues above without requiring a full rebuild.

**Priority fixes for D.2:**
1. Fix "сьогодні" in group-sort activity (Issue 1) — quick fix, high impact
2. Add synthetic future FYI note to grammar section (Issue 2) — plan compliance
3. Add завтра вранці/вдень/ввечері collocations (Issue 3) — plan compliance
4. Integrate or remove orphan vocabulary items (Issue 4) — consistency
5. Remove/replace line 27 non-sequitur (Issue 5) — beginner safety