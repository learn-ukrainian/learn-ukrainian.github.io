**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Compliance | 7/10 | Missing required vocabulary "ставати" (imperfective); missing "програмувальник" formal variant note; missing "громадянин/громадянка" recommended vocab. Section structure compliant. |
| 2 | Language Quality | 8/10 | Ukrainian grammar is sound throughout. "Vladimir the Great" (Russian name form) at L273 for a Ukrainian historical figure in a Ukrainian curriculum is a naming/decolonization issue. English is warm and accessible. |
| 3 | Lesson Quality | 8/10 | "Would I Continue?" 4/5 — warm opening, good analogies, clear explanations. Practice section (L237) comes after ~180 lines of presentation, which is long for A2 before the first learner activity. |
| 4 | Activity Quality | 8/10 | 12 activities across 8 types — good variety. Fill-in L144 assumes masculine gender for "я". Cloze (Irina story) is excellent. Solid coverage of all grammar targets. |
| 5 | Richness | 9/10 | 8 callout boxes, 3 dialogues, Irina narrative, 5 historical figures, coworking culture note, feminitives context. Very rich for A2. |
| 6 | LLM Fingerprint | 7/10 | L17 "explore one of the most philosophical and beautiful aspects" and L46 "we will master the three magical verbs" are AI rhetoric. Historical figures section (L274-287) has severe structural monotony — 4 of 5 paragraphs start identically with "Він **був..." |
| 7 | Factual Accuracy | 8/10 | L283 «Вона врятувала оперу "Мадам Баттерфляй"» is an oversimplification (Krushelnytska performed in a successful revival, she didn't single-handedly save it). "Vladimir" name form. All other facts verified. |

**Overall: 7.9/10**

---

## Critical Issues Found

### Issue 1: Missing Required Vocabulary "ставати" (Plan Compliance — CRITICAL)

**Location:** Entire content file — absent

The plan (`vocabulary_hints.required`) lists **ставати (to be becoming)** as required vocabulary: "ставати (to be becoming) — ставати кращим; process of change; imperfective." This imperfective counterpart to **стати** is completely absent from both the content file and the vocabulary YAML. The content teaches only the perfective **стати** without ever mentioning that the process of becoming (imperfective aspect) uses a different verb. For A2 learners, understanding the perfective/imperfective pair is pedagogically important — you cannot fully teach "becoming" with only the perfective form.

**Fix:** Add a subsection or callout box in section «Презентація: Бути, стати, працювати» (near L164-172) introducing **ставати** as the imperfective counterpart. Example: «Я стаю кращим кожного дня.» (I am becoming better every day.) vs. «Я став кращим.» (I became better.) Also add "ставати" to the vocabulary YAML.

---

### Issue 2: "Vladimir the Great" — Russian Name Form (Decolonization)

**Location:** Line 273

The content reads: «**Володимир Великий** (Vladimir the Great)». The English parenthetical uses "Vladimir" which is the Russian transliteration of the name. The curriculum already correctly uses "Volodymyr" for Zelenskyy at L171: «Володимир Зеленський **став президентом** України.» Using "Vladimir" for the historical figure while "Volodymyr" for the president creates inconsistency and tacitly accepts the Russian naming convention for Ukrainian historical figures.

**Fix:** Change L273 to: `**Володимир Великий** (Volodymyr the Great)`.

---

### Issue 3: Structural Monotony in Historical Figures Section (LLM Fingerprint)

**Location:** Lines 274-287

All four male historical figure descriptions use an identical pattern: "Він **був [instrumental]**. Він [verb]. Він [verb]. Він [verb]." Verbatim from the file:

- L274: «Він **був великим князем київським**. Він охрестив Русь у 988 році. Він був могутнім правителем і мудрим політиком.»
- L277: «Він **був гетьманом України**. Він очолив Національно-визвольну війну проти Польщі. Він був талановитим полководцем і дипломатом.»
- L280: «Він **був мандрівним філософом** і поетом. Він ходив пішки по Україні та навчав людей мудрості. Він не хотів багатства чи влади.»
- L286: «Він **був не тільки поетом**, але й **талановитим художником**. Він був символом боротьби за свободу України. Він народився кріпаком, але став вільною людиною та національним героєм.»

Four consecutive paragraphs opening with "Він **був..." and consisting of 4-5 short sentences all beginning with "Він." This is textbook LLM monotonous generation. It also deprives the learner of seeing varied Ukrainian sentence structures — the very thing a reading passage at A2 should model.

**Fix:** Vary the openings. For example, start with a date ("У 988 році великий князь київський..."), a question ("Хто такий Богдан Хмельницький?"), or a different sentence structure ("Мандрівний філософ і поет — Григорій Сковорода — ходив пішки..."). Each figure should feel distinct, not copy-pasted.

---

### Issue 4: AI Rhetoric in Opening (LLM Fingerprint)

**Location:** Lines 17, 46

L17: "Today we are going to explore one of the most philosophical and beautiful aspects of the Ukrainian language: the fluidity of identity." — This reads like generic AI content generation. A real tutor would say something more direct and less grandiose.

L46: "In this extensive module, we will master the three magical verbs that trigger this transformation:" — "Extensive module," "master," "magical verbs," "trigger this transformation" — stacked AI-typical intensifiers.

**Fix:** Simplify to natural tutor voice. E.g., L17: "Today you'll learn how Ukrainian grammar changes based on whether you're talking about who you ARE vs. what role you PLAY." L46: "In this lesson, you'll learn to use three key verbs:"

---

### Issue 5: Missing "програмувальник" Formal Variant Note (Plan Compliance)

**Location:** Absent from content

The plan states: "mention formal програмувальник vs. universally used програміст." The research notes explicitly say: "The Standard uses програмувальник, but програміст is universally used in spoken/professional language. Teach програміст as primary, note програмувальник as formal variant." This note is absent from the content.

**Fix:** Add a brief note in section «Презентація: Бути, стати, працювати» near the IT/professions discussion (around L191-218 or in section «Діалоги: Кар'єра та робота» near L370), e.g.: "The official State Standard term is **програмувальник**, but in everyday speech everyone says **програміст**."

---

## Factual Verification

| # | Claim | Location | Verdict |
|---|-------|----------|---------|
| 1 | «Він охрестив Русь у 988 році.» | L274 | **Correct** — Baptism of Rus' dated 988 CE |
| 2 | «У 2019 році Володимир Зеленський **став президентом** України.» | L171 | **Correct** — Inaugurated May 20, 2019 |
| 3 | «Його знаменита фраза: "Світ ловив мене, але не спіймав".» | L280 | **Correct** — Famous epitaph on Skovoroda's gravestone |
| 4 | «Вона врятувала оперу "Мадам Баттерфляй" Джакомо Пуччіні.» | L283 | **Simplified** — Krushelnytska performed in the successful Brescia revival (1904) after the disastrous La Scala premiere. "Saved" is a commonly repeated cultural claim but overstates her role. She didn't single-handedly save it. |
| 5 | «Його портрет ви можете побачити на купюрі в 5 гривень.» | L277 | **Correct** — Khmelnytsky is on the 5 UAH banknote |
| 6 | «In 2019, the new Ukrainian orthography officially endorsed the widespread use of feminine forms.» | L224 | **Correct** — New Ukrainian orthography adopted 2019, aligned with research notes |
| 7 | «Він очолив Національно-визвольну війну проти Польщі.» | L277 | **Simplified** — The uprising was against the Polish-Lithuanian Commonwealth, not Poland alone. Acceptable simplification for A2. |
| 8 | «Він народився кріпаком, але став вільною людиною та національним героєм.» | L286 | **Correct** — Shevchenko was born a serf, freed in 1838 |

**Callout Box Check:**

| Box | Type | Location | Issue |
|-----|------|----------|-------|
| [!example] | Example | L78-80 | Clean |
| [!tip] "Rhythm of -ою" | Tip | L97-101 | Clean |
| [!warning] "Adjective Agreement" | Warning | L158-162 | Clean |
| [!context] "Temporary Work" | Context | L213-217 | Clean |
| [!note] | Note | L247-249 | Clean |
| [!tip] "Щасливою людиною" | Tip | L255-256 | Clean |
| [!history-bite] "Гетьман" | History | L288-291 | Clean — «Богдан Хмельницький став гетьманом у 1648 році.» Date correct. |
| [!insight] "Becoming calmer" | Insight | L446-449 | Clean |

No fabricated claims in callout boxes.

---

## Verification Summary

### Plan Compliance Gaps

| Plan Requirement | Status | Location |
|------------------|--------|----------|
| Section «Вступ» | Present | L15-52 |
| Section «Презентація» | Present | L55-235 |
| Section «Практика» | Present | L237-361 |
| Section «Діалоги» | Present | L364-462 |
| Required vocab: бути | Present | Throughout |
| Required vocab: стати | Present | Throughout |
| **Required vocab: ставати** | **MISSING** | Nowhere in content or vocab YAML |
| Required vocab: працювати | Present | Throughout |
| Required vocab: лікар/лікарка | Present | L75, L247, etc. |
| Required vocab: вчитель/вчителька | Present | L73, L138, etc. |
| Required vocab: програміст/програмістка | Present | L208, L388, etc. |
| Required vocab: айтішник/айтішниця | Present | L370-373 |
| Required vocab: інженер/інженерка | Present | L68, L133 |
| Required vocab: журналіст/журналістка | Present | L186, L408 |
| Required vocab: юрист/юристка | Present | L170, L437 |
| Recommended: менеджер/менеджерка | Present | L204, L227 |
| Recommended: спеціаліст/спеціалістка | Present | L156, L253 |
| **Recommended: громадянин/громадянка** | **MISSING** | Nowhere (State Standard example from research) |
| Recommended: директор/директорка | Present | L232, L325 |
| **"програмувальник" formal note** | **MISSING** | Research notes require this |

### Colonial Framing Check
- No "Unlike Russian..." or "Different from Russian..." patterns found
- **"Vladimir the Great"** (L273): Russian transliteration used for Ukrainian historical figure — inconsistent with "Volodymyr Zelenskyy" (L171)

### LLM Fingerprint Scan
- **Structural monotony**: Historical figures section (L274-287) — 4 of 5 paragraphs start "Він **був..." ✗
- **AI rhetoric**: L17 ("explore one of the most philosophical and beautiful aspects"), L46 ("we will master the three magical verbs that trigger this transformation") ✗
- **"Не просто" pattern**: Not found ✓
- **Generic AI clichés**: Not found ✓
- **Callout monotony**: No duplicate titles ✓
- **Example plausibility**: All examples are natural and plausible ✓

### "Would I Continue?" Test (A2 Beginner)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | **Pass** | Pacing is comfortable, good scaffolding |
| Were instructions clear? | **Pass** | Always clear what to do |
| Did I get quick wins? | **Partial** | First real practice (section «Практика: Від мрії до реальності») comes at L237 — after ~180 lines of presentation. The [!example] and [!tip] boxes provide some interaction earlier, but no learner-active exercise until halfway through. |
| Was Ukrainian scary? | **Pass** | Introduced gently with English support |
| Would I come back tomorrow? | **Pass** | Engaging, warm, encouraging |

**Result: 4/5 Pass → Lesson Quality 8-9 range**

### Warmth & Encouragement Check

| Marker | Count | Minimum |
|--------|-------|---------|
| Direct address ("you", "ви") | ~20+ | ≥15 ✓ |
| Encouragement phrases | ~4 ("Great!", "Congratulations!", etc.) | ≥3 ✓ |
| "Don't worry" moments | 1 (L41-42 "Nominative Trap" reassurance) | ≥2 ✗ (borderline) |
| "You can now..." validation | 2 (L51, L479) | ≥2 ✓ |

---

## Verdict

**Status: PASS WITH FIXES**

This is a solid A2 grammar module with strong pedagogical structure, rich cultural content, and well-crafted dialogues. The Irina narrative and the three dialogues are genuinely engaging. The costume analogy is effective. Activities are varied and comprehensive.

**Required fixes before approval:**

1. **Add "ставати"** (imperfective) to content and vocabulary — this is a required plan vocabulary item and a pedagogically important aspectual pair
2. **Fix "Vladimir" → "Volodymyr"** at L273 — decolonization compliance
3. **Vary historical figures section** (L274-287) — break the "Він **був..." monotony across all 4 male figure paragraphs
4. **Soften AI rhetoric** at L17 and L46 — replace with natural tutor voice
5. **Add "програмувальник" note** — research notes explicitly require this

**Recommended (non-blocking):**
- Add a quick mini-exercise or interactive moment earlier in section «Презентація: Бути, стати, працювати» (before L237) to break up the long presentation
- Add "громадянин/громадянка" with the State Standard example from research notes
- Qualify the Krushelnytska "saved" claim at L283