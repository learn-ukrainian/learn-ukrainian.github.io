<!-- content-hash: 5cd60688470c -->
**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review — `a2/checkpoint` (A2-35: Complex Sentences & Health)

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|-----------------|
| 1 | **Language Quality** | 6/10 | Multiple gender agreement errors in instructional headings and prose (L113, L117, L119). Typo in H3 heading. Excessive intensifier padding (~25 "дуже", 5 "надзвичайно", 3 "абсолютно" in 332 lines). |
| 2 | **Lesson Quality** | 7/10 | Warm opening and good cultural hooks, but the "який" nominative examples fail to demonstrate the taught concept (L124, L128). Mechanical stub sections (Модель/Практика/Самоперевірка) ×5 add no value. |
| 3 | **Activity Quality** | 6/10 | Unjumble answers systematically omit commas before subordinate conjunctions (L581, L590, L599) — directly contradicts the content's own comma rules. Unnatural quiz question at L503. |
| 4 | **Factual Accuracy** | 9/10 | Grammar rules accurately explained. Cultural claims verified. Minor overstatement: "брати ліки" framed as categorically wrong (L227) when it is merely non-preferred. |
| 5 | **LLM Fingerprint** | 7/10 | "не просто X, а Y" pattern ×2 (L16, L256). Excessive filler adjectives throughout. Inconsistent labeling: «Plural (Plural):» at L135 vs Ukrainian labels elsewhere. |
| 6 | **Richness** | 8/10 | Good cultural hooks (калина symbolism, Будьмо! toast). Realistic medical dialogue. 6 varied callout boxes. Missing the "який" declension table the plan specifies. |
| 7 | **Plan Compliance** | 7/10 | All 5 sections present. Missing the required "який" rule table (plan: "Provide a rule table demonstrating gender, number, and case agreement"). щоб vs що б "targeted drill" is explanation, not a drill. |
| 8 | **Immersion Balance** | 9/10 | 71.5% Ukrainian within 60-75% target. English used appropriately for syntax explanations. Medical examples fully Ukrainian. |
| 9 | **Humanity & Warmth** | 8/10 | Opening «Вітаємо вас на новому етапі!» is welcoming. Regular encouragement present. Direct address frequent. Slightly undermined by mechanical stub sections that feel template-generated. |
| 10 | **Vocabulary Coverage** | 9/10 | All required vocab present (голова, горло, температура, ліки, лікар, живіт, застуда). All recommended items covered (рука, нога, малина, калина, мед, щоб, бо). IPA provided in vocabulary YAML. |

---

## Critical Issues Found

### CRITICAL ISSUE 1: Gender Agreement Errors in Instructional Headings (L113, L117, L119)

**Section:** «Навичка 2: Опис та послідовність дій»

Three gender agreement errors in the section teaching "який" agreement — the irony is that this section *teaches* gender agreement while containing agreement violations itself:

1. **L113** — «Відносний слово: Який» → "слово" is neuter (середній рід), so the heading must be **«Відносне слово: Який»** (or better: **«Відносний займенник: Який»**).

2. **L117** — «Використовуйте цей універсальний слово» → Two errors: demonstrative "цей" (masculine) should be "це" (neuter); adjective "універсальний" (masculine) should be "універсальне" (neuter). Correct: **«Використовуйте це універсальне слово»**.

3. **L119** — «Узгодження словоа Який» → Typo: "словоа" must be **"слова"**.

**Severity:** Critical. Grammar errors in the teaching material about grammar agreement destroy learner trust and model incorrect Ukrainian. A section titled "Agreement of який" must itself demonstrate correct agreement.

**Fix:** Correct all three: rename heading to «Відносне слово: Який» or «Відносний займенник: Який»; fix L117 to «це універсальне слово»; fix typo «словоа» → «слова».

---

### CRITICAL ISSUE 2: "Який" Nominative Examples Don't Use "Який" (L124, L128)

**Section:** «Навичка 2: Опис та послідовність дій»

The nominative examples for masculine and feminine fail to demonstrate the relative pronoun they are supposed to teach:

1. **L124** — «Це новий лікар. Він працює в нашій сучасній лікарні.» — Two independent sentences. No «який» appears. The English translation says "who works" (relative clause), but the Ukrainian has «Він працює» (independent clause). Should be: **«Це новий лікар, який працює в нашій сучасній лікарні.»**

2. **L128** — «Ось та аптека. Вона завжди працює вночі.» — Same problem. No «яка». Should be: **«Ось та аптека, яка завжди працює вночі.»**

**Severity:** Critical. The section's pedagogical goal is to show how «який» creates relative clauses. Providing examples that DON'T use the relative pronoun defeats the entire purpose.

**Fix:** Merge each pair into a single relative clause using the appropriate form of «який/яка».

---

### CRITICAL ISSUE 3: Unjumble Activity Answers Model Incorrect Punctuation (L581, L590, L599)

**Section:** Activities — «Побудуйте складні речення»

The complex sentence unjumble answers systematically omit commas before subordinate conjunctions. The content explicitly teaches comma placement rules before these conjunctions, but the activity answers contradict this:

1. **L581** — «Я почекаю тут поки ти п'єш чай» → Missing comma before «поки». Should be: **«Я почекаю тут, поки ти п'єш чай»**.

2. **L590** — «Вона п'є сироп який дав їй лікар» → Missing comma before «який». Should be: **«Вона п'є сироп, який дав їй лікар»**.

3. **L599** — «Ми йшли додому коли почався сильний дощ» → Missing comma before «коли». Should be: **«Ми йшли додому, коли почався сильний дощ»**.

**Severity:** Critical. Teaching punctuation rules in prose but modeling incorrect punctuation in practice activities creates contradictory learning. The activities must either include comma tiles or use the fill-in format for complex sentences.

**Fix:** Add commas to all three answers. If the unjumble format doesn't support punctuation tiles, consider changing these items to fill-in or error-correction type.

---

### ISSUE 4: Unnatural Activity Question (L503)

**Section:** Activities — «Оберіть правильний займенник "який"»

**L503** — «Де моє хворе горло, ___ сьогодні так сильно болить?» — "Where is my sick throat that hurts so badly today?" is not a natural Ukrainian sentence. No native speaker would ask "Where is my throat?" This is an implausible utterance that wouldn't occur in real communication.

**Severity:** Moderate. Unnatural example sentences undermine the teaching material's credibility.

**Fix:** Replace with a natural sentence, e.g.: «Це моє хворе горло, ___ сьогодні так сильно болить.» or «У мене хворе горло, ___ сьогодні так сильно болить.»

---

### ISSUE 5: Missing "Який" Declension Table (Plan Compliance)

**Section:** «Навичка 2: Опис та послідовність дій»

The plan specifies: *"Provide a rule table demonstrating gender, number, and case agreement with the antecedent noun."* The content provides scattered examples organized by gender, but no actual table. At A2, learners need a clean, visual reference table, not just examples. The meta outline (L24-25 in meta) also calls for "a rule table."

**Severity:** Moderate. Visual grammar tables are critical for beginner comprehension per Tier 1 rubrics.

**Fix:** Add a declension table before the examples showing який/яка/яке/які across nominative and accusative cases (at minimum).

---

### ISSUE 6: Excessive Intensifier Padding (LLM Fingerprint)

Throughout the content, nearly every noun is modified by one or more intensifiers that add no pedagogical value:

- «дуже сильно та довго болить» (L206) — three modifiers for one verb
- «надзвичайно просте, але критично важливе» (L146) — two superlatives for one concept
- «абсолютно критично важливо» (L194) — triple-stacked intensifiers
- «вкрай слабким» (L277), «надзвичайно хворе» (L208), «суворе граматичне правило, яке не можна порушувати» (L85)

The word «дуже» alone appears approximately 25 times in 332 lines (~1 per 13 lines). «Надзвичайно» appears 5 times. This over-modification is a hallmark LLM pattern and inflates word count without adding pedagogical content.

**Severity:** Moderate. Inflated prose obscures the teaching points and models unnatural Ukrainian writing for learners.

**Fix:** Remove 40-60% of intensifiers. A2 text should be direct and simple, not maximally modified.

---

### ISSUE 7: "Не просто X, а Y" LLM Rhetoric Pattern (L16, L256)

**L16** — «Ви навчитеся не просто говорити короткі базові фрази, а будувати складні, глибокі логічні речення.»

**L256** — «Калина — це не просто корисна червона ягода.»

Per rubric: "це не просто / це не лише / не просто X, а Y used 2+ times → ≤ 7."

**Severity:** Moderate. Two occurrences reach the threshold.

**Fix:** Rephrase one or both to avoid the pattern. E.g., L16 could become: «Ви навчитеся будувати складні логічні речення замість коротких фраз.»

---

### ISSUE 8: Inconsistent Label "Plural (Plural):" (L135)

**Section:** «Навичка 2: Опис та послідовність дій»

**L135** — «**Plural (Plural):**» — Redundant English-English label. The other gender categories use Ukrainian: «Чоловічий рід», «Жіночий рід», «Середній рід». This should be **«Множина:»** for consistency.

**Severity:** Minor. Inconsistency, not a serious error.

**Fix:** Replace with «Множина:».

---

## Factual Verification

| Claim | Location | Verdict |
|-------|----------|---------|
| «тому що» requires comma before it | L26 | **Correct** — standard Ukrainian punctuation |
| «бо» requires comma before it | L39 | **Correct** — subordinate conjunction comma rule |
| «через» requires Accusative case | L53 | **Correct** — standard government |
| «щоб» + past tense when subjects differ | L75 | **Correct** — Ukrainian syntax rule per State Standard §4.4.2 |
| «Будьмо!» = imperative of «бути» | L293 | **Correct** — hortative imperative (1st person plural) |
| «Будьмо!» literally "Let us be!" | L293 | **Correct** |
| Калина as national symbol | L256 | **Correct** — well-established cultural fact |
| «брати ліки» is categorically wrong | L227 | **Slightly overstated** — it exists marginally in colloquial Ukrainian, but «приймати/пити» are overwhelmingly preferred. Pedagogically acceptable overstatement at A2. |
| Малина, калина, мед as folk cold remedies | L241-253 | **Correct** — well-documented Ukrainian folk medicine tradition |
| Grammar rule: який declines like hard-stem adjective | L121 | **Correct** |

**Callout box check:**
- `[!tip]` L48-49: Register advice (бо vs тому що) — **Accurate**
- `[!warning]` L84-85: щоб + past tense rule — **Accurate**
- `[!observe]` L139-140: Gender agreement advice — **Accurate** (though ironic given L113/L117 errors)
- `[!fact]` L175-176: B1 bridge (якби) — **Accurate**, correctly scoped
- `[!warning]` L236-237: "Брати ліки" correction — **Accurate** (slightly overstated, see above)
- `[!culture]` L255-256: Калина symbolism — **Accurate**, culturally verified

**No fabricated facts, dates, or attributions found.** No colonial framing detected. No Russianisms detected.

---

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from plan present | **PASS** — All 5 sections present as H2 headers |
| Vocabulary scope match | **PASS** — All required and recommended items covered |
| Grammar scope (no creep) | **PASS** — No B1+ grammar introduced; якби correctly deferred |
| Colonial framing | **PASS** — No Ukrainian-via-Russian comparisons found |
| Russianisms | **PASS** — No Russianisms detected |
| Factual accuracy | **PASS** — All claims verified; minor overstatement on «брати ліки» |
| LLM fingerprint | **WARN** — "не просто" ×2, excessive intensifiers, Plural(Plural) label |
| Word count | **PASS** — 3570 / 3000 (119%, above minimum) |
| Immersion | **PASS** — 71.5% within 60-75% target |
| "Would I Continue?" test | 3/5 PASS — Warm opening (✓), clear instructions (✓), quick wins (✓), Ukrainian not scary (✓ with scaffolding), but «який» section with grammar errors is discouraging (✗) |
| Grammar errors in content | **FAIL** — 3 gender agreement errors in section teaching gender agreement (Critical Issues 1-2) |
| Activity punctuation | **FAIL** — 3 unjumble answers model incorrect punctuation (Critical Issue 3) |
| Missing plan elements | **FAIL** — No «який» declension table despite plan requirement |

### Section Coverage

- Section «Вступ та цілі» — Warm and well-structured opening with clear objectives. Immersion note present. Over-modified prose.
- Section «Навичка 1: Синтаксис логіки: Причина та Мета» — Strong pedagogical structure covering тому що, бо, через, щоб+inf, щоб+past, щоб vs що б. Good examples. Slightly dense but acceptable for a checkpoint.
- Section «Навичка 2: Опис та послідовність дій» — Contains the worst errors (gender agreement mistakes in headings, missing «який» in nominative examples, no declension table). Коли/поки/після того як are well-taught.
- Section «Навичка 3: Медицина, тіло та народні методи» — Good vocabulary integration. Pain expression taught correctly. "Приймати vs пити vs брати" distinction is useful. Folk medicine cultural hook is engaging.
- Section «Навичка 4: Практичне застосування та підсумок» — Medical dialogue effectively integrates all taught structures. «Будьмо!» cultural hook is well-researched and appropriate. Summary is comprehensive.

---

## Verdict

**NEEDS REPAIR** — The module has solid pedagogical structure and good cultural content, but Critical Issues 1-3 require mandatory fixes before approval:

1. **Gender agreement errors in the «який» section** — Grammar errors in material teaching grammar agreement are auto-fail quality. Three fixes needed (L113, L117, L119).
2. **Nominative "який" examples missing the pronoun** — The two examples meant to teach «який/яка» in nominative don't use them (L124, L128). Must be merged into actual relative clauses.
3. **Unjumble answers missing commas** — Three activity answers model incorrect punctuation before subordinate conjunctions (L581, L590, L599), directly contradicting the content's comma rules.
4. **Missing "який" declension table** — Required by plan, critical for A2 visual learning.

Secondary fixes: Replace unnatural quiz question (L503), add «Множина:» label (L135), reduce intensifier padding, rephrase one "не просто" instance.

**Estimated repair scope:** D.2 targeted fix (no full rewrite needed). ~15 specific line-level changes.