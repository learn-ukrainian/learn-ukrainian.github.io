<!-- content-hash: 171fbbc6ea45 -->
**Reviewed-By:** claude-opus-4-6

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Compliance | 7/10 | Multiple plan items dropped: «бо»/«тому що» causal conjunctions (§4.3.2), «де?» locative review connecting to a1-30, green cross/«Аптечний пункт» distinction, «Я болю» error drill, «за рецептом» phrase, register comparison «Я захворів» vs «У мене симптоми...». Meta section title mismatch: meta says "Лексика: Вирази про здоров'я" but content has "Лексика: Здоров'я". |
| 2 | Language Quality | 8/10 | Ukrainian is generally correct. One stress error: content line 32 teaches «Спи́на» (stress on first syllable) but standard Ukrainian normative stress is «спина́» (final syllable). Vocabulary YAML `[ˈspɪnɑ]` reinforces the error. English is clear and accessible. No Russianisms or calques detected. No word salad. |
| 3 | Factual Accuracy | 9/10 | Grammar rules (болить/болять agreement, Dative state constructions) are accurately presented. Proverb «У здоровому тілі — здоровий дух» is real and correctly attributed. Cultural note about малина/калина/мед remedies is accurate. Minor: line 14 "It is the center of our thoughts and pain" is awkward but not factually wrong. |
| 4 | Lesson Quality | 7/10 | Clear PPP structure, logical progression from vocabulary → grammar → application → dialogues. But the persona "Polyclinic Nurse" is invisible — content reads as a generic textbook, not a supportive nurse character. No warm opening ("Привіт!" to the learner), no encouragement mid-lesson, no emotional arc. The "Would I Continue?" test: 4/5 pass (instructions clear, not overwhelming, quick wins present, Ukrainian introduced gently) but "Would I come back tomorrow?" is borderline due to cold tone. |
| 5 | Richness | 8/10 | Two good cultural hooks (proverb in Section «Розминка: Частини тіла», herbal remedies in Section «Лексика: В аптеці»). Four diverse dialogue scenarios in Section «Практикум: Діалоги про здоров'я» covering casual/formal/pharmacy/home contexts. Good plural table in subsection «Перевірка: Множина». Missing: green cross cultural detail, «Аптечний пункт» vs «Аптека» distinction from plan. |
| 6 | Activity Quality | 7/10 | 10 activities, ~100 items, 5 types. fill-in dominates at 4/10 activities (40%). Activity 5 "Що болить?" is highly repetitive (8 identical-pattern items testing only болить vs болять). Activity 7 "Симптоми та поради" match-up includes 4 phrases not taught in the lesson. Vocabulary YAML includes meta-grammatical terms «однина» and «множина» that don't belong in health vocabulary. |
| 7 | LLM Fingerprint | 8/10 | Section openings are varied — no 3+ identical patterns. No "In this lesson we will explore" rhetoric. No stacked abstract nouns. No AI clichés. Content feels somewhat mechanical/flat but not identifiably AI-generated. Callout titles are all unique (no monotony). |
| 8 | Humanity & Warmth | 5/10 | **COLD_PEDAGOGY.** Zero encouragement phrases (searched: "Great", "Well done", "Молодець", "Чудово" — only hit is vocabulary example «Я почуваю себе чудово» at line 163, not encouragement). Zero "don't worry" moments. Only 1 "You can now..." validation (line 376). No warm greeting directed at the learner — the intro starts with a question «Чому це важливо?» (line 3), not a welcome. The persona of "Patient Supportive Tutor / Polyclinic Nurse" is entirely absent from the prose voice. |
| 9 | Immersion | 7/10 | Audit reports 35.6% against target 35-55%. This is at the absolute floor. For an A1.3 consolidation module, more Ukrainian is expected. The dialogues in Section «Практикум: Діалоги про здоров'я» contribute most of the Ukrainian; the explanatory sections are almost entirely English. |

---

## Critical Issues Found

### Issue 1: COLD_PEDAGOGY — No Warmth Markers (Humanity & Warmth 5/10)

**Severity:** Critical — potential auto-fail per tier rubric (<3 warmth markers)

**Evidence:**
- **Zero encouragement phrases** anywhere in 388 lines. No "Great!", "You've got this!", "Молодець!", "Well done!" etc.
- **Zero "Don't worry" moments.** Grep for "Don't worry" / "don't worry" / "не хвилюй" returned no matches.
- **No warm greeting** to the learner. Line 3 opens with «Чому це важливо?» — a rhetorical question, not a welcome. The word "Привіт" only appears in Scenario 1 dialogue (line 335-336) between characters, not from the tutor to the learner.
- **Only 1 progress validation** at line 376: "You know body parts, how to say «У мене болить...», and how to speak with a doctor."
- The closing at line 378 «Бережіть себе!» is a nice cultural touch but it's the ONLY warm moment in 2400 words.

**Location:** Entire module, but most critically: opening (lines 1-9), section transitions, and mid-lesson check-ins are all absent.

**Required Fix:** Add warm greeting at opening, encouragement after each major section (especially after Section «Граматика: Конструкція «У мене болить...»» and Section «Лексика: Здоров'я»), at least 2 "don't worry" moments (e.g., after the agreement warning at lines 89-95), and expand the closing celebration at lines 374-378. The "Polyclinic Nurse" persona should shine through — imagine a kind nurse encouraging a nervous patient.

---

### Issue 2: Plan Compliance Gaps — Multiple Required Items Missing

**Severity:** Critical

**Missing from plan (plan YAML vocabulary_hints.required and content_outline):**

| Plan Item | Status |
|-----------|--------|
| Causal conjunctions «бо» / «тому що» (State Standard §4.3.2) | **MISSING** — content uses only «тому» (lines 320-328) |
| «де?» locative review connecting to a1-30 prepositions (на голові, на руках) | **MISSING** — no locative forms appear anywhere |
| Green cross / «Аптечний пункт» vs «Аптека» distinction | **MISSING** — search returned no matches |
| Learner error «Я болю» vs «Мені болить» | **MISSING** — not addressed |
| «за рецептом» (with prescription) phrase | **MISSING** — only «без рецепту» appears (line 245) |
| Register comparison «Я захворів» vs «У мене симптоми...» (from meta section 3) | **MISSING** |
| Collocation «записатися до лікаря» (from plan vocabulary_hints.required) | **MISSING** |

**Location:** Spans all sections but primarily affects Section «Лексика: Здоров'я» (missing register check) and Section «Ситуація: У лікаря» (missing causal conjunctions).

**Required Fix:** Add «бо» and «тому що» examples to the "Наслідки" subsection (line 319-328) alongside existing «тому» examples. Add «за рецептом» to Section «Лексика: В аптеці» near line 243-247. Add green cross / «Аптечний пункт» cultural note. Add brief «де?» locative review to Section «Розминка: Частини тіла». Add «Я болю» error to a warning box in Section «Граматика: Конструкція «У мене болить...»».

---

### Issue 3: Vocabulary YAML Missing ~8 Taught Words

**Severity:** Major

**Evidence:** Vocabulary YAML (22 items) is missing these words that appear in the content and/or are in the plan's recommended vocabulary:

| Word | Used In Content | In Plan |
|------|----------------|---------|
| здоровий | Line 25: «У здоровому тілі — здоровий дух» | ✅ recommended |
| малина | Line 252: «малиновий чай» (raspberry tea) | ✅ recommended |
| калина | Line 252: «калиновий чай» (viburnum tea) | ✅ recommended |
| мед | Line 252: «мед» (honey) | ✅ recommended |
| хворий | Lines 134-137: «Він хворий», «Я сьогодні хворий» | ✅ recommended |
| хворіти | Lines 141-144: «Я часто хворію» | ✅ recommended |
| таблетки | Line 230: «Табле́тки» (pills) | Taught in content |
| сироп | Line 231: «Сиро́п» (syrup) | Taught in content |

**Additionally:** Vocabulary YAML includes «однина» (singular, line 115) and «множина» (plural, line 121) — these are grammatical meta-terms, not health vocabulary. They inflate the item count without serving the module's communicative purpose.

**Location:** `/curriculum/l2-uk-en/a1/vocabulary/body-and-health.yaml`

**Required Fix:** Add the 8 missing vocabulary items with IPA, POS, and example sentences. Remove or replace «однина» and «множина» with health-relevant vocabulary items.

---

### Issue 4: Stress Error — «Спи́на» vs Normative «Спина́»

**Severity:** Major

**Evidence:** Content line 32 teaches «**Спи́на** (back)» with stress on the first syllable. The vocabulary YAML has IPA `[ˈspɪnɑ]` (stress on first syllable). Standard Ukrainian normative stress per SUM (Словник української мови) and the Орфоепічний словник is «спина́» [spɪˈnɑ] — stress on the final syllable. Teaching non-standard stress at A1 creates a pronunciation error that's hard to correct later.

**Location:** Content line 32; vocabulary YAML line 42 (`ipa: '[ˈspɪnɑ]'`).

**Required Fix:** Change to «Спина́» in content and `[spɪˈnɑ]` in vocabulary YAML.

---

### Issue 5: Activities Reference Untaught Vocabulary

**Severity:** Moderate

**Evidence:** Activity 7 "Симптоми та поради" (match-up, activities YAML lines 228-246) includes 4 advice phrases that do not appear anywhere in the lesson content:

- «Не пийте каву ввечері» (Don't drink coffee in the evening) — line 236
- «Не піднімайте важке» (Don't lift heavy things) — line 238
- «Їжте легку їжу» (Eat light food) — line 240
- «Купіть краплі для носа» (Buy nose drops) — line 242

None of these phrases appear in the lesson. Grep confirmed zero matches in the content file. For an A1 module, activities should reinforce taught material, not introduce new structures.

**Location:** Activities YAML lines 236-242.

**Required Fix:** Either add these phrases to the lesson content (e.g., expand the "Поради" subsection at lines 308-317 in Section «Ситуація: У лікаря»), or replace them with phrases that DO appear in the lesson (e.g., «Пийте теплий чай», «Приймайте ці ліки», «Спіть більше»).

---

### Issue 6: Dialogue Uses Untaught Form «Я замерз»

**Severity:** Moderate

**Evidence:** In Section «Практикум: Діалоги про здоров'я», Scenario 4 (line 368): «**Син:** Я замерз. (I am cold.)» — This uses the perfective past tense of «замерзнути», a form not taught in this lesson. The lesson explicitly teaches «Мені холодно» (line 172) as the A1-appropriate way to express being cold using the Dative impersonal construction. Using «Я замерз» in a practice dialogue contradicts the lesson's own teaching and introduces an untaught grammar pattern (perfective past).

**Location:** Content line 368 (Scenario 4 in Section «Практикум: Діалоги про здоров'я»).

**Required Fix:** Replace «Я замерз» with «Мені холодно» to align with the taught construction.

---

## Verification Summary

### Plan Compliance
- **Outline compliance:** 5/6 sections match meta H2 titles. Section «Лексика: Здоров'я» differs from meta "Лексика: Вирази про здоров'я" — title mismatch.
- **Vocabulary scope:** 8 recommended words from plan missing from vocabulary YAML.
- **Grammar scope:** No scope creep detected — all grammar stays within plan boundaries.
- **Objectives coverage:** All 4 objectives (name body parts, describe symptoms, communicate at doctor, ask for medicine) are addressed in content.
- **Plan items missing:** 7 items documented in Issue 2 above.

### Language Quality Checks
- **Russianisms:** None found. Searched for кушать, приймати участь, красивий, прекрасне — no matches.
- **Colonial framing:** None. English comparisons are appropriate for an English-audience course; no Russian comparisons used.
- **Word salad:** None. Each paragraph has a clear pedagogical point.
- **Grammar accuracy:** Agreement rules (болить/болять) correctly explained. Dative state construction (Мені погано) correctly presented with error drill.

### Factual Verification
- Proverb «У здоровому тілі — здоровий дух» (line 25) — real Ukrainian proverb, correctly rendered ✅
- Cultural note about «малиновий чай», «калиновий чай», «мед» (line 252) — accurately describes Ukrainian home remedy traditions ✅
- «Ліки» always plural (line 219) — correct ✅
- «Лікар» vs «Лікарня» distinction (lines 199-206) — accurate ✅
- Grammar: «У мене болить + singular subject» / «У мене болять + plural subject» — correctly explained with the body part as grammatical subject (lines 71-107) ✅
- Stress error «Спи́на» — documented as Issue 4 above ❌

### LLM Fingerprint Check
- **Structural monotony:** Section openings are varied (checked first 2 lines of each H2): "We begin with..." / "This is the most important..." / "Being 'sick'..." / "**Апте́ка** (Pharmacy)..." / "Visiting a doctor..." / "**Читайте діалоги.**" — no 3+ identical patterns ✅
- **Example batching:** Varied formats across sections (bullet lists, tables, dialogues, inline examples) ✅
- **Generic AI rhetoric:** No "це не просто", no stacked abstract nouns, no AI clichés detected ✅
- **Callout monotony:** All callout titles unique ([!culture] "Прислів'я", [!warning] "Типова помилка: Узгодження", [!observe] "Active Verb Usage", [!warning] "Типова помилка", [!warning] "False Friend: Лікар vs Лікарня", [!culture] "Природна аптека") ✅

### Warmth & Emotional Safety Mapping

| Required Moment | Present? | Evidence |
|-----------------|----------|----------|
| Welcome/orientation | ❌ | No "Привіт!" or warm greeting — starts with rhetorical question (line 3) |
| Curiosity trigger | ✅ | «Чому це важливо?» (line 3) sets context |
| Quick win (≥2) | ⚠️ | 1 found: "Point and speak" exercise (lines 52-62); second is debatable |
| Encouragement (≥1) | ❌ | None found in 388 lines |
| "Don't worry" (≥1) | ❌ | None found |
| Progress marker (≥1) | ✅ | Line 376: "You know body parts, how to say «У мене болить...»" |

### Activity Audit

| # | Type | Title | Items | Issues |
|---|------|-------|-------|--------|
| 1 | match-up | Частини тіла: переклад | 8 | None |
| 2 | group-sort | Рід іменників: частини тіла | 16 | None — all gender assignments verified correct |
| 3 | fill-in | Однина та множина | 8 | None |
| 4 | quiz | Правила про здоров'я | 8 | None |
| 5 | fill-in | Що болить? | 8 | Highly repetitive — all items test identical pattern |
| 6 | unjumble | Складіть речення | 6 | None |
| 7 | match-up | Симптоми та поради | 8 | 4 untaught phrases (Issue 5) |
| 8 | group-sort | Однина чи множина? | 12 | None |
| 9 | fill-in | Діалог у лікаря | 8 | None |
| 10 | fill-in | В аптеці | 8 | None |

**Activity type diversity:** 5 types used (match-up: 2, group-sort: 2, fill-in: 4, quiz: 1, unjumble: 1). fill-in at 40% — acceptable for A1 (repetition aids learning per rubric) but at the threshold.

---

## Verdict

**REVISE**

The module's core teaching material is pedagogically sound — the grammar explanations for «У мене болить...» construction are clear and accurate, the dialogue scenarios are well-structured, and the content covers the essential communicative skills. However, three issues require revision before passing:

1. **COLD_PEDAGOGY (Critical):** The complete absence of warmth markers is the most serious issue. The "Polyclinic Nurse" persona is invisible. The module needs encouragement phrases, a warm opening, "don't worry" moments, and mid-lesson validation. This is a wrapper issue, not a content rewrite.

2. **Plan compliance gaps (Critical):** 7 plan items are missing, most notably «бо»/«тому що» causal conjunctions (State Standard §4.3.2) and the «де?» locative review connecting to a1-30. These are scoped additions, not restructuring.

3. **Vocabulary YAML gaps (Major):** 8 taught words are missing from the vocabulary file. Straightforward additions.

**Estimated repair scope:** D.2 targeted repair — add warmth wrapper (opening, transitions, closing), add missing plan items as short subsections, fix «Спи́на» → «Спина́» stress, update vocabulary YAML. No full rewrite needed.