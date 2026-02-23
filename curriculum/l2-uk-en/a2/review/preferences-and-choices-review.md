**Reviewed-By:** claude-opus-4-6

===REVIEW_START===

# Phase D.1 Review: preferences-and-choices (A2-20)

**Module:** Preferences and Choices
**Level:** A2, Sequence 20
**Persona:** Encouraging Cultural Guide / Sommelier
**Word count:** 4071 / 3000 (135.7%)
**Activities:** 12
**Vocabulary:** 25
**Engagement boxes:** 5
**Immersion:** 51.4% (target: 50-60%)

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | **Language Quality (Ukrainian)** | 6/10 | "Pronounа" Franken-word (line 156); 3 more untranslated "Pronoun" in Ukrainian text (lines 179, 205, 256); "більш велика"/"менш велика" unnatural analytical comparatives (lines 225-226); "культурної вільності" semantic error (line 283); incoherent generation artifact (line 285); inconsistent comma before «ніж» throughout |
| 2 | **Language Quality (English)** | 9/10 | Clear, B1-readable grammar explanations; well-scaffolded theory in section «Презентація»; minor over-formality in some transitions |
| 3 | **Lesson Quality** | 7/10 | Solid pedagogical arc but "Would I Continue?" test yields 3/5: instruction clarity degraded by code-switching in section «Практика»; no explicit learning preview ("Today you'll learn..."); 600+ words before any practice; closing section «Підсумок» lacks "You can now..." celebration |
| 4 | **Richness & Cultural Depth** | 8/10 | Lviv coffee culture hook is vivid and authentic; proverb «На колір і смак товариш не всяк» well-integrated with breakdown; 5 callout boxes with varied types; two full dialogues with analysis; no IPA in content body despite research notes requiring it |
| 5 | **Activity Quality** | 7/10 | 12 activities with excellent type variety (8 distinct types); but unnatural "більш велика" propagated to YAML lines 154 and 507; fill-in item line 139 has marked word order; all error-correction items are pedagogically sound |
| 6 | **Factual Accuracy** | 9/10 | Dative experiencer logic correctly explained per §4.2.2.3; любити/подобатися distinction accurate; Lviv coffee claims plausible; proverb correctly cited; "культурної вільності" is a semantic miscalculation, not a factual error |
| 7 | **LLM Fingerprint** | 7/10 | 3× "не просто"/"більше, ніж просто" pattern (lines 20, 25, 197); generation artifact line 285; "Давайте" opens 10+ subsections creating formulaic instructor voice; section «Практика» H3 headers all follow identical "Concept: Subtitle" format |
| 8 | **Warmth & Humanity** | 7/10 | "Ласкаво просимо" opener present; «Давайте» used encouragingly; «Ви успішно впоралися» (line 211); but zero explicit "don't worry" / "це нормально" reassurances; zero "Great!" / "Чудово!" mid-lesson praise markers; section «Підсумок» ends looking forward to "complex structures ahead" instead of celebrating progress — opposite of beginner emotional safety |
| 9 | **Immersion Balance** | 9/10 | 51.4% within 50-60% Band 1 target; English correctly used for grammar theory; Ukrainian for dialogues and examples; section «Презентація» appropriately in English |
| 10 | **Plan Compliance** | 8/10 | All 5 sections present; all vocabulary covered; all objectives addressed; BUT plan called for «більш солодкий»/«менш дорогий» as analytical comparative examples, content substituted «більш великий»/«менш великий» instead; Підсумок is H1 not H2 |

**Aggregate: 7.7/10**

---

## Critical Issues Found

### Issue 1: CRITICAL — "Pronounа" Franken-word and untranslated "Pronoun" in Ukrainian paragraphs

**Location:** Section «Практика», lines 156, 179, 205; Section «Діалоги», line 256

The English word "Pronoun" appears 4 times inside otherwise Ukrainian paragraphs. On line 156, it receives a Ukrainian genitive case ending — "Pronounа" — producing a non-word in either language.

**Evidence (verbatim):**

- Line 156: «Ця трансформація вимагає зміни як Pronounа, так і відмінка іменника.»
- Line 179: «Коли ви хочете висловити спонтанне "подобається", одразу використовуйте Pronoun у Dative.»
- Line 205: «Пам'ятайте, Pronoun у Dative залишається тим самим; ми просто додаємо заперечення до дієслова.»
- Line 256: «Він правильно використовує Dative Pronoun **йому**.»

**Why this is critical:** The Ukrainian word for "pronoun" is **займенник**. Writing "Pronounа" (line 156) is a clear generation failure where the model produced an English word with a Ukrainian case suffix. This appears in the section «Практика» where the student is actively working in Ukrainian — encountering a non-word here is maximally confusing.

The broader pattern: section «Практика» inconsistently mixes English grammar terms ("Dative", "Nominative", "Accusative", "Pronoun") into Ukrainian sentences, while elsewhere using the correct Ukrainian terms: «давальний відмінок» (line 152), «називний» (line 174), «знахідний» (line 174). This inconsistency within a single section is pedagogically harmful at A2.

**Required fix:** Replace all "Pronoun" → «займенник» (declined appropriately: «займенника» for genitive on line 156). In Ukrainian paragraphs within section «Практика», standardize grammar term language: either all Ukrainian (давальний, називний, знахідний) or define English terms on first use with Ukrainian equivalents.

---

### Issue 2: CRITICAL — Unnatural analytical comparatives "більш велика" / "менш велика"

**Location:** Section «Практика», lines 225-226; Activities YAML lines 154, 507

The module uses «більш велика» and «менш велика» as teaching examples for analytical comparatives. For the extremely high-frequency adjective «великий», Ukrainian strongly prefers the synthetic comparative **більша** / **менша**. No native speaker would say «квартира більш велика».

**Evidence (verbatim):**

- Line 225: «"Квартира Б більш велика." (Apartment B is more large/bigger.)»
- Line 226: «"Квартира А менш велика." (Apartment A is less large.)»
- Activities YAML line 154: `"Квартира в центрі _____ велика, ніж у передмісті."` (answer: "менш")
- Activities YAML line 507: `"Квартира А більш велика, ніж квартира Б."`

**Why this is critical:** The plan explicitly calls for examples like «більш солодкий» and «менш дорогий» (plan lines 42-43) — multi-syllable adjectives where analytical forms are natural and practical. Using «більш великий» violates the plan's intent and teaches unnatural Ukrainian. Worse, this error is propagated into two activity items, meaning learners will be drilled on incorrect forms.

**Required fix:** In content, replace «більш велика» → «більша», «менш велика» → «менша» for the direct comparison. Then add separate examples with multi-syllable adjectives: «більш зручна» (more comfortable), «менш дорога» (less expensive) — to demonstrate the analytical form as the plan intended. Update activities YAML accordingly.

---

### Issue 3: CRITICAL — "# Підсумок" uses H1 instead of H2

**Location:** Line 289

All other main sections use H2 (`##`): «Вступ» (line 14), «Презентація» (line 44), «Практика» (line 150), «Діалоги» (line 234). Section «Підсумок» uses H1 (`#`), breaking document structure.

**Evidence (verbatim):**

- Line 289: `# Підсумок`
- Compare line 14: `## Вступ`, line 44: `## Презентація`

**Required fix:** Change `# Підсумок` to `## Підсумок`.

---

### Issue 4: MAJOR — Generation artifact / incoherent sentence

**Location:** Section «Діалоги», line 285

A passage describing how the proverb could be applied to the first dialogue contains a disconnected sentence and an orphaned English parenthetical.

**Evidence (verbatim):**

- Line 285: «У першому діалозі Максим та Олена не погодилися. Хтось із них міг би усміхнутися. (Well, to each their own), Вони визнають, що їхні особисті смаки докорінно відрізняються.»

**Problems:**
1. «Хтось із них міг би усміхнутися» — semantically disconnected; "someone could smile" doesn't logically follow from their disagreement
2. "(Well, to each their own)" — floating English parenthetical with no Ukrainian source; the proverb it translates is never quoted
3. «Вони» is capitalized after a comma — punctuation error
4. The passage clearly intended to show one speaker using the proverb to resolve disagreement, but the proverb citation itself is missing

**Required fix:** Rewrite to explicitly cite the proverb: «У першому діалозі Максим та Олена не погодилися щодо подарунка. Хтось із них міг би усміхнутися й сказати: "На колір і смак товариш не всяк." Так вони визнають, що їхні смаки різні, і продовжують шукати компроміс.»

---

### Issue 5: MAJOR — "культурної вільності" semantic error

**Location:** Section «Діалоги», line 283 (inside [!reflection] callout)

**Evidence (verbatim):**

- Line 283: «Це ключова фраза для демонстрації культурної вільності в Україні.»

**Problem:** «Вільність» means "freedom" or "liberty" — not "fluency" or "competence." The sentence reads as "a key phrase for demonstrating cultural freedom in Ukraine," which is semantically wrong in context. The intended meaning is "cultural fluency" or "cultural competence" — i.e., the ability to navigate social situations. The correct Ukrainian terms would be **культурної компетентності** (cultural competence) or **культурної обізнаності** (cultural awareness).

**Required fix:** Replace «культурної вільності» → «культурної компетентності» or «культурної обізнаності».

---

### Issue 6: MAJOR — "Центр — це краще ніж передмістя" grammatically awkward

**Location:** Section «Практика», line 222

**Evidence (verbatim):**

- Line 222: «"Центр — це краще ніж передмістя." (Використовуємо **краще** як загальний порівняльний прислівник для ситуації).»

**Problem:** «Центр» is a masculine noun. The module itself teaches (line 122) that as an adjective, «краще» changes endings: «кращий, краща, краще, кращі». Yet this example uses the neuter/adverbial form «краще» with a masculine subject. If comparing the nouns directly, the adjective should agree: «Центр кращий, ніж передмістя». If using the adverbial form, restructure: «У центрі краще, ніж у передмісті.» The parenthetical acknowledges this tension but doesn't resolve it — it actively contradicts the grammar just taught.

Also missing: comma before «ніж» (see Issue 7).

**Required fix:** Replace with «Центр кращий, ніж передмістя» (adjective agreement) or «У центрі краще, ніж у передмісті» (impersonal adverbial).

---

### Issue 7: MODERATE — Inconsistent punctuation: missing comma before «ніж»

**Location:** Lines 131, 222, 245, 267 vs. line 230

Standard Ukrainian punctuation requires a comma before the comparative conjunction «ніж». The module inconsistently applies this.

**Evidence of missing commas:**

- Line 131: «"Кава краща ніж чай."» → should be «Кава краща, ніж чай.»
- Line 245: «Квитки — це краще ніж м'яч.» → should be «Квитки — це краще, ніж м'яч.»
- Line 267: «Прогулянка — це краще ніж кіно.» → should be «Прогулянка — це краще, ніж кіно.»

**Evidence of correct commas:**

- Line 230: «Мені більше подобається квартира Б, ніж квартира А.»

**Why this matters:** The module presents «краще ніж» as a fixed grammatical unit (content line 129: "краще ніж (better than)"; summary line 315: same) without the comma. Learners will reproduce this punctuation error. For a grammar-focused language teaching module, this is significant.

**Required fix:** Add commas before all instances of «ніж» in comparative constructions. Update the grammar summary on line 315 to «краще, ніж».

---

### Issue 8: MODERATE — No IPA in content body

**Location:** Entire content file

The research notes (line 31) explicitly require: "IPA for new words on first occurrence only: ensure [ɔ] for о, [ɛ] for е, [t͡ʃ] for ч." The content body contains zero IPA transcriptions. All IPA exists only in the vocabulary YAML, which may not be rendered inline during the lesson.

Key vocabulary introduced without IPA on first occurrence: **подобатися** (line 52), **вибирати** (line 42), **краще** (line 117), **філіжанка** (line 22), **віддавати перевагу** (line 141).

**Required fix:** Add IPA in parentheses after each key vocabulary word on first occurrence.

---

### Issue 9: MODERATE — Opening paragraph uses B1+ Ukrainian for A2 learners

**Location:** Lines 10-12 (blockquote before section «Вступ»)

**Evidence (verbatim):**

- Line 12: «Опанувавши цю зміну, ви будете звучати природно.»

**Problem:** «Опанувавши» is a perfective adverbial participle (дієприслівник) — a structure typically introduced at B1 or later. An A2 learner encountering this as the very first Ukrainian sentence in the module would not understand it. The blockquote also contains complex structures like «вимагає невеликої зміни у тому, як ви граматично сприймаєте світ» — this is abstract, multi-clause Ukrainian inappropriate for the opening of an A2 module. The opening should establish emotional safety, not linguistic intimidation.

**Required fix:** Simplify the opening blockquote to A2-level Ukrainian. For example: «Коли ви знаєте, що вам подобається, і вмієте про це говорити — ви звучите природно.»

---

### Issue 10: MINOR — Fill-in activity awkward word order

**Location:** Activities YAML, line 139

**Evidence (verbatim):**

- Line 139: `"Мені подобається чай більше _____ кава."` (answer: "ніж")

**Problem:** Standard word order places «більше» before the verb: «Мені більше подобається чай, ніж кава.» The current order (adverb after object) is possible but marked/emphatic — not what an A2 drill should teach as the default pattern.

**Required fix:** Rewrite to: «Мені більше подобається чай, _____ кава.»

---

## Factual Verification

### Grammar Rule Accuracy

| Rule | Location | Claimed | Verified | Status |
|------|----------|---------|----------|--------|
| подобатися requires Dative experiencer | Lines 52-56 | «the person who experiences the feeling... is NOT the active subject... the person must be in the **Dative case**» | Correct per State Standard §4.2.2.3 | PASS |
| Liked item stays in Nominative | Lines 56, 90-94 | «the thing that is causing the feeling (the book) is the active agent... Subjects must always be in the Nominative case» | Correct | PASS |
| любити uses Nominative-Accusative | Line 103 | «любити uses standard Nominative-Accusative grammar» | Correct | PASS |
| краще as both adjective and adverb | Lines 119-127 | «краще is incredibly flexible because it functions as both an adjective and an adverb» | Correct; adjective forms (кращий, краща, краще, кращі) accurately listed | PASS |
| віддавати перевагу requires Dative for preferred item | Line 143 | «the thing you are giving preference TO must be in the Dative case» | Correct | PASS |
| більш/менш + adjective for analytical comparative | Line 135 | «більш солодкий (more sweet), менш цікавий (less interesting)» | Correct per §4.3.1; but teaching example uses unnatural form | PARTIAL |

### Cultural Claims

| Claim | Location | Plausibility | Status |
|-------|----------|-------------|--------|
| Lviv has deep connection to coffee culture | Line 20 | Well-established — Lviv is known as Ukraine's coffee capital | PASS |
| «філіжанка» is traditional Galician word for coffee cup | Line 22 | Accurate — standard word in Western Ukrainian usage | PASS |
| «кава на піску» brewed in copper джезва on hot sand | Line 22 | Accurate — traditional Turkish-style brewing method found in Lviv cafés | PASS |
| Proverb «На колір і смак товариш не всяк» means "to each their own" | Lines 276-278 | Correct proverb, correct meaning, correct word-by-word breakdown | PASS |

### Callout Box Verification

| Callout | Location | Scrutiny | Status |
|---------|----------|----------|--------|
| [!culture] Львівська кава | Lines 24-25 | «Фраза **львівська кава** означає більше, ніж просто зерна» — Plausible cultural characterization; «обряд посвячення» (rite of initiation) is metaphorical but not fabricated | PASS |
| [!tip] "To Me" Mental Trick | Lines 67-68 | Pedagogical mnemonic, not factual claim | PASS |
| [!warning] Double Check Endings | Lines 96-97 | «Is the person in the Dative? Is the thing in the Nominative?» — Accurate grammar check | PASS |
| [!fact] Більш and Менш | Lines 134-135 | «більш солодкий (more sweet), менш цікавий (less interesting)» — Correct analytical comparative examples | PASS |
| [!reflection] Cultural Harmony | Lines 282-283 | «соціальне мастило» — stylistically bold but semantically valid metaphor; «культурної вільності» — semantic error (see Issue 5) | PARTIAL |

---

## Lesson Experience Audit

### "Would I Continue?" Test

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | **BORDERLINE** | Opening blockquote uses B1+ Ukrainian (Опанувавши); first 600+ words are expository before any practice |
| Were instructions clear? | **FAIL** | "Pronounа" non-word in section «Практика»; inconsistent code-switching between English and Ukrainian grammar terms within the same paragraphs |
| Did I get quick wins? | **BORDERLINE** | First actual practice starts at line 152 (section «Практика»); no mini-exercise in section «Вступ» or early in section «Презентація» |
| Was Ukrainian scary? | **PASS** | Well-scaffolded with English support for grammar; cultural hook eases into Ukrainian naturally |
| Would I come back tomorrow? | **PASS** | Lviv coffee hook is genuinely engaging; dialogues feel authentic and practical |

**Result: 3/5 Pass (2 borderline, 1 fail)** → Lesson Quality 7/10

### Lesson Arc

| Element | Present? | Quality |
|---------|----------|---------|
| **WELCOME** | Yes — «Ласкаво просимо до нашої теми про вподобання та вибір!» (line 16) | Warm but generic |
| **PREVIEW** | Weak — blockquote (lines 10-12) hints at importance but no "Today you'll learn to..." list | Missing explicit learning objectives in learner-facing language |
| **PRESENT** | Strong — Section «Презентація» (line 44) | Thorough, well-structured with named error traps, good examples |
| **PRACTICE** | Good — Section «Практика» (line 150) | Multiple scenarios, guided progression; marred by code-switching |
| **CELEBRATE** | Weak — Section «Підсумок» (line 289) | Self-check questions present, but closing sentence (line 329) says "Mastering these concepts prepares you for the more complex grammatical structures ahead" — forward-looking rather than celebratory |

### Emotional Safety Markers

| Marker Type | Minimum | Found | Status |
|-------------|---------|-------|--------|
| Direct address (ви/you) | ≥15 | >30 | PASS |
| Encouragement phrases | ≥3 | 2 — «Ви успішно впоралися» (line 211), «Це чудова ідея» (line 270, in dialogue) | FAIL |
| "Don't worry" reassurances | ≥2 | 0 | FAIL |
| "You can now..." validation | ≥2 | 1 — "You now have the linguistic foundation" (line 329) | FAIL |

**Warmth markers below threshold. This contributes to Warmth score of 7/10.**

---

## Colonial Framing Check

**PASS — No colonial framing detected.** The module explains Dative experiencer logic as a Ukrainian grammatical feature compared to English (appropriate for L2 instruction). No references to Russian as baseline. The research notes instructed decolonized framing, and this was followed correctly.

---

## LLM Fingerprint Analysis

### Structural Monotony Test

First 2 lines of each H2 section:

- Section «Вступ» (line 16): «Ласкаво просимо до нашої теми про вподобання та вибір! Як ваш викладач, я хочу запросити вас у подорож.»
- Section «Презентація» (line 46): "Now that we have set the scene and learned how to politely initiate a request, we need to tackle the core grammatical shift..."
- Section «Практика» (line 152): «Час застосувати ці теорії на практиці. Єдиний спосіб переналаштувати ваш мозок...»
- Section «Діалоги» (line 236): «Щоб по-справжньому засвоїти ці структури, ми повинні побачити їх у дії.»

**Verdict:** Reasonably varied languages and approaches. No 3+ identical openings. PASS.

### "не просто" / "більше, ніж просто" Pattern

- Line 20: «Тут замовлення кави — це не поспішна ранкова необхідність»
- Line 25: «означає більше, ніж просто зерна»
- Line 197: «Ви не просто цитуєте граматику»

**3 instances of "не просто" family → threshold of 2+ breached → LLM Fingerprint ≤ 7**

### "Давайте" Subsection Opener Density

«Давайте» appears as a transitional opener in 10+ places: lines 158, 173, 183, 194, 201, 221, 224, 228, 252, 264, 280. While individually natural (Ukrainian tutors do say "Давайте..."), the density means virtually every new subsection/drill begins with the same word. This creates a formulaic rhythm noticeable to attentive readers.

### Example Format Uniformity

Section «Презентація» sub-sections consistently use the same example format: Ukrainian sentence in quotes + English translation in parentheses + commentary. This is repeated across 5+ subsections identically. However, the Практика section varies format (step-by-step, scenario narration, dialogue), providing sufficient overall variety. **Borderline.**

### Generation Artifact

Line 285: «Хтось із них міг би усміхнутися. (Well, to each their own), Вони визнають...» — Clear generation failure (see Issue 4).

### Callout Monotony

5 callouts use 5 different types: [!culture], [!tip], [!warning], [!fact], [!reflection]. **No monotony. PASS.**

---

## Plan Compliance

### Section Coverage

| Plan Section | Content H2 | Present? | Word Target | Notes |
|-------------|-----------|----------|-------------|-------|
| Вступ (400w) | Section «Вступ» (line 14) | Yes | Exceeded | Lviv coffee hook ✓, "Would Like" bridge ✓ |
| Презентація (950w) | Section «Презентація» (line 44) | Yes | Exceeded | All 4 sub-points (Dative logic, error traps, intensity mismatch, comparatives, formal preference) covered ✓ |
| Практика (700w) | Section «Практика» (line 150) | Yes | Exceeded | Transformation drills ✓, Decision scenarios ✓, Comparative drills ✓ |
| Діалоги (550w) | Section «Діалоги» (line 234) | Yes | Exceeded | Gift dialogue ✓, Activity dialogue ✓, Proverb ✓ |
| Підсумок (400w) | `# Підсумок` (line 289) | Yes (wrong heading level) | Met | Dative recap ✓, Vocab summary ✓, Self-check ✓ |

### Vocabulary Scope (Required)

| Vocabulary | In Content? | Location |
|-----------|------------|----------|
| подобатися | ✓ | Lines 52, 63, 108+ |
| вибирати | ✓ | Lines 42, 192 |
| краще | ✓ | Lines 117-131 |
| хотів би / хотіла би | ✓ | Lines 29-31, 37-40 |
| перевага / віддавати перевагу | ✓ | Lines 139-148 |
| філіжанка | ✓ | Line 22 |
| смак | ✓ | Lines 280, 309 |

### Plan Deviation

The plan (lines 42-43) specifies analytical comparative examples: «більш солодкий» and «менш дорогий». The content substituted «більш великий» and «менш великий» — adjectives where the synthetic form is standard. The [!fact] callout (line 135) does use the plan's correct examples («більш солодкий», «менш цікавий»), but the practice section and activities use the unnatural forms.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Colonial framing | PASS | No Russian comparisons found |
| Russianisms | PASS | No кушати, получати, приймати участь found |
| Grammar scope violations | PASS | No grammar from later modules (no full conditional theory, appropriately deferred to M22) |
| Word salad | PARTIAL FAIL | Line 285 is incoherent generation artifact; rest is well-structured |
| Factual accuracy | PASS | All grammar rules verified; cultural claims plausible |
| Plan compliance | PARTIAL FAIL | Section structure present but Підсумок heading wrong; analytical comparative examples deviate from plan |
| Activity count | PASS | 12 activities (requirement met) |
| Immersion target | PASS | 51.4% within 50-60% Band 1 target |
| Engagement boxes | PASS | 5 boxes, varied types, no fabricated claims |
| H2 structure | FAIL | Section «Підсумок» is H1, not H2 |
| Punctuation | FAIL | Inconsistent comma before «ніж» (missing in 4+ instances) |
| Term consistency | FAIL | "Pronoun"/"Pronounа" in Ukrainian text (4 instances) |
| IPA in content | FAIL | Zero IPA transcriptions in content body; research notes require them |
| Warmth markers | FAIL | Below threshold for encouragement phrases (2/3), "don't worry" (0/2), "you can now" (1/2) |

---

## Verdict

**NEEDS REVISION**

The module has genuine pedagogical strengths: the Dative experiencer logic is thoroughly and correctly explained, the Lviv coffee culture hook is engaging and authentic, the activity variety is excellent (8 distinct types across 12 items), and the dialogues model realistic Ukrainian social interactions. The plan is well-executed structurally.

However, the following issues require D.2 repair before the module can pass:

### Blocking Issues (must fix)

1. **"Pronounа" / "Pronoun" in Ukrainian text** (Issue 1) — 4 instances of untranslated/malformed English in Ukrainian paragraphs. A clear generation failure that confuses learners.
2. **"більш велика" / "менш велика"** (Issue 2) — Unnatural analytical comparatives for a common adjective, propagated into 2 activity items. Teaches incorrect natural Ukrainian and deviates from the plan's specified examples.
3. **H1 Підсумок** (Issue 3) — Structural heading error.

### Should-Fix Issues (strongly recommended)

4. **Generation artifact line 285** (Issue 4) — Incoherent sentence with orphaned parenthetical.
5. **"культурної вільності"** (Issue 5) — Semantic error in callout box.
6. **"Центр — це краще ніж передмістя"** (Issue 6) — Grammar inconsistency with module's own teaching.
7. **Missing commas before «ніж»** (Issue 7) — Teaches incorrect punctuation.
8. **Missing IPA in content** (Issue 8) — Violates research notes requirement.
9. **B1+ Ukrainian in opening** (Issue 9) — «Опанувавши» is above A2 level.

### Nice-to-Fix

10. **Fill-in word order** (Issue 10) — Minor activity naturalness improvement.
11. **Add warmth markers** — Increase explicit encouragement to meet beginner thresholds.

**Estimated repair scope:** Moderate — all issues are localized substitutions, additions, or rewrites. No structural overhaul needed. A D.2 pass should address blocking + should-fix issues within the existing framework.

===REVIEW_END===
