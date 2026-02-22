<!-- content-hash: aab5f4efe72e -->
**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review: All Cases Practice (a2-09)

## Scores

| # | Dimension | Score |
|---|-----------|-------|
| 1 | Lesson Quality | 6/10 |
| 2 | Richness | 6/10 |
| 3 | Immersion Balance | 8/10 |
| 4 | Language Quality | 7/10 |
| 5 | Factual Accuracy | 8/10 |
| 6 | Curriculum Fit | 8/10 |
| 7 | Activity Quality | 7/10 |
| 8 | LLM Fingerprint | 4/10 |
| 9 | Humanity & Warmth | 6/10 |

**Weighted Total: 6.4/10 — FAIL**

---

## Critical Issues Found

### CRITICAL 1: Colonial Framing — Ukrainian Vocative Defined via Russian (line 170)

Section «Культурний аспект: Кличний відмінок», line 170:

> «У російській мові він зник. In Russian, for instance, the vocative case disappeared completely. Але в українській мові він живе.»

This defines Ukrainian's vocative case by what Russian lacks. The research notes explicitly state: "Do not use Russian grammar as a point of comparison." This is textbook colonial framing — Ukrainian is presented as notable only because it has something Russian doesn't, rather than on its own terms as a preserved Proto-Slavic feature. **Must be rewritten** to present the vocative as a feature Ukrainian shares with other languages (Polish, Czech, Romanian, etc.) without Russian as the baseline.

### CRITICAL 2: Severe LLM Filler/Padding — Four Paragraphs of Vacuous Repetition

**Line 18** in section «Вступ: Важливість відмінкової системи»: A massive block of 17+ short sentences saying nothing new:

> «Ми будемо багато працювати разом. Ви навчитеся говорити дуже точно. Ваша розмовна мова стане набагато кращою. Це дуже цікавий процес вивчення. Кожен день ви робите новий крок уперед. Ви розумієте набагато більше слів. Ви говорите краще та швидше. Ваші українські друзі будуть дуже раді. Вони побачать ваш великий і швидкий прогрес. Ви будете дуже пишатися собою. Це ваша велика перемога.»

This is not "warmth" — this is an LLM generating short repetitive motivational sentences when it runs out of substantive content. Each sentence adds zero pedagogical value.

**Line 174** in section «Культурний аспект: Кличний відмінок»: Same pattern:

> «Кличний відмінок допомагає вам знайти нових друзів. Він робить вашу українську мову дуже красивою. Носії мови будуть приємно здивовані. Ви показуєте повагу до культури. Це ваша секретна зброя для спілкування. Українська мова любить емоції. Не бійтеся використовувати кличний відмінок кожного дня.»

**Line 205** in section «Практика та аналіз помилок»: Same again:

> «Практикуйте ці три правила кожного дня. Якщо ви будете знати їх, ви будете говорити ідеально. Ви будете говорити чітко та дуже впевнено. Це допоможе вам у будь-якій ситуації. Це ваша гарантія ідеальної граматики щодня. Ви зможете говорити без помилок. Ваша українська мова буде звучати дуже природно.»

**Line 336** in section «Діалоги та реальне застосування»: Same:

> «Ваша впевненість буде швидко зростати кожного дня. Ви зможете вирішити будь-яку проблему дуже швидко. Ваша граматика буде найкращою серед усіх ваших друзів. Говоріть сміливо.»

**Line 356** (Підсумок): «Система відмінків — це двигун української мови.» — "двигун" is a known LLM-typical metaphor flagged in the fingerprint guide.

These filler blocks collectively amount to ~150-200 words of zero-content padding. They also create a pattern of excessive promises ("you'll speak perfectly," "your grammar will be the best among all your friends") that borders on patronizing.

### CRITICAL 3: Incorrect Grammatical Terminology (line 292)

Section «Практика та аналіз помилок», line 292 — the paradigm table for "книга" uses incorrect column headers:

> «| Форма | Запитання | Одиниця | Багато | Приклад у тексті |»

"Одиниця" means "unit" (a numerical digit or unit of measurement), NOT "singular." The correct Ukrainian grammatical term is **"Однина"**. Similarly, "Багато" means "many/a lot" — the correct term is **"Множина"** (plural). The first paradigm table for "друг" (line 276) correctly uses "Однина" and "Множина," making this inconsistency even worse — a learner would be confused by the inconsistent terminology.

### CRITICAL 4: Incomplete Activity Error Correction (activities line 315-319)

The error-correction activity contains:

> `sentence: "Я пишу синя ручка."`
> `error: "ручка"` → `answer: "ручкою"`

This only corrects the noun to instrumental but leaves the adjective "синя" (nominative) uncorrected. The fully correct sentence is "Я пишу **синьою** ручкою." Teaching learners to fix the noun but ignore the adjective in the same phrase creates a false model — the "corrected" result «Я пишу синя ручкою» still contains a grammatical error. The error must be marked as "синя ручка" → "синьою ручкою" (phrase type).

---

## Other Issues

### Issue 5: Extreme Structural Monotony (lines 64-155)

Section «Презентація: Система та логіка» uses identical subheading structure for 5 of 7 cases:

- Line 64: **Як це працює:** / Line 67: **Коли використовувати:**
- Line 78: **Як це працює:** / Line 81: **Коли використовувати:**
- Line 95: **Як це працює:** / Line 98: **Коли використовувати:**
- Line 123: **Як це працює:** / Line 126: **Коли використовувати:**
- Line 151: **Як це працює:** / Line 154: **Коли використовувати:**

Then Accusative (line 109) uses "Функція:" and Locative (line 137) uses "Де це відбувається:". This is an assembly-line pattern where the LLM generated each case block from the same template. The monotony is deadening — 5 identical section openings in a row. Vary the approach: use a comparative table for some, dialogue examples for others, a mini-scenario for yet another.

### Issue 6: Implausible Example (line 283)

In the "друг" paradigm table, the Locative example:

> «Камера на **другові**.»

"A camera on a friend" is not something a Ukrainian speaker would naturally say. This reads like a fabricated example created to fill a table slot. Replace with something natural like «Я зупинився на **другові** поглядом» or restructure to «Він тримає камеру на **другові**» — though even that is awkward. A better Locative example would involve a preposition like "про": «Ми розповіли про **друга**» — wait, that's Accusative. Better: use "по" or rethink the example entirely.

### Issue 7: Questionable Pedagogical Choice — Vocative for Inanimate Noun (line 300)

> «| Кличний | - | **книго**! | **книги**! | Ой, моя **книго**! |»

While "книго" is technically a vocative form, using the vocative for an inanimate object is an extremely literary/poetic device, not standard conversational usage. At A2 level, this confuses learners about when the vocative is actually used. The vocative section explicitly teaches it's for "calling a person or animal" (line 152). This contradicts the paradigm table.

### Issue 8: Missing Plan Content — No Declension Group Summary

The meta's content_outline for section «Презентація: Система та логіка» requires: "Gender forms summary for singular and plural nouns, focusing on the structural 'Declension Group' approach." The actual content has only a brief `[!observe]` callout (lines 161-162) mentioning gender and stem types. There is no actual summary table or systematic presentation of declension groups. This plan point is unmet.

---

## Factual Verification

| Claim | Status | Notes |
|-------|--------|-------|
| Ukrainian has 7 cases (line 25-37) | **CORRECT** | Standard §4.2.2 confirmed |
| Locative always requires preposition (line 141) | **CORRECT** | Standard Ukrainian grammar |
| Animate masc. Acc = Gen (line 238) | **CORRECT** | Standard rule |
| Age expressed with Dative (line 261) | **CORRECT** | Standard Ukrainian construction |
| "немає" triggers Genitive (line 89) | **CORRECT** | |
| "суддя" vocative = "судде" (line 157) | **CORRECT** | |
| "друг" paradigm (lines 276-284) | **CORRECT** | All forms verified |
| "книга" paradigm (lines 292-301) | **PARTIALLY CORRECT** | Wrong column headers ("Одиниця"/"Багато"); forms correct |
| Ukrainian melodic due to case system (line 23) | **UNVERIFIABLE CLAIM** | The culture callout says "Українська мова відома у світі як дуже мелодійна мова" and attributes this to the case system. While Ukrainian is often described as melodic, attributing it specifically to the case system (rather than vowel harmony, prosody, etc.) is an oversimplification. Not wrong enough to fail, but should be softened. |
| Vocative preserved from Proto-Slavic (line 170) | **CORRECT** | But presented via colonial framing |
| "таксі" is indeclinable (activities line 310-314) | **CORRECT** | Foreign loanword, indeclinable |

---

## Dimension Evidence

### 1. Lesson Quality: 6/10

**"Would I Continue?" Test:**
- Did I feel overwhelmed? **PASS** — pacing is comfortable, English scaffolding is present
- Were instructions clear? **PASS** — always knew what to do
- Did I get quick wins? **FAIL** — the first 18 lines are all theory/motivational filler before any practice. The actual reference table doesn't appear until line 29, and practice is at line 201
- Was Ukrainian scary? **PASS** — introduced with English support
- Would I come back tomorrow? **FAIL** — the repetitive motivational filler (line 18, 174, 205, 336) is patronizing rather than encouraging, and the assembly-line case presentations (identical structure ×5) are monotonous

**Score: 3/5 Pass → 8/10 from test, but deducted to 6/10** for the massive filler blocks that damage the lesson experience. A nervous beginner reading «Ваша граматика буде найкращою серед усіх ваших друзів» would find this patronizing, not encouraging.

The lesson arc is WELCOME → PRESENT → PRACTICE → PRESENT MORE → PRACTICE → DIALOGUE, which is reasonable. But the WELCOME is bloated with filler, and the CELEBRATE at the end (line 354-365) is just more filler plus self-check questions — no genuine celebration moment.

### 2. Richness: 6/10

**Strengths:**
- The court translator persona is engaging and maintained through the dialogues
- The courtroom simulation (lines 314-323) is genuinely excellent — it demonstrates all cases in a natural dialogue
- The bank scenario (lines 330-334) adds real-world variety

**Weaknesses:**
- Section «Презентація: Система та логіка» is extremely mechanical — 7 near-identical subsections with no cultural hooks, stories, or varied presentation
- The paradigm tables (lines 276-301) are dry reference material without any engaging context around them
- Missing the plan-required declension group summary
- The cultural section «Культурний аспект: Кличний відмінок» has good bones but is drowned in filler

### 3. Immersion Balance: 8/10

Pre-computed audit says 52.9%, target 50-60%. This is within range. The balance between English theory and Ukrainian examples is well-executed — English explains the "why," Ukrainian provides the examples. The dialogues (lines 314-334) are primarily Ukrainian with case annotations. The approach stated at line 20 is well-implemented.

Minor concern: the filler paragraphs (lines 18, 174, 205, 336) are all in Ukrainian but contain no substantive language teaching — this artificially inflates the Ukrainian percentage.

### 4. Language Quality: 7/10

**Colonial framing** on line 170 caps this at ≤7 per protocol.

**Ukrainian quality in non-filler sections:** Generally good. The example sentences are grammatically correct and natural (with the exception of «Камера на другові»). The courtroom and bank dialogues feel authentic.

**Incorrect terminology:** «Одиниця» / «Багато» instead of «Однина» / «Множина» at line 292 is a factual error in a teaching document about grammatical terms.

### 5. Factual Accuracy: 8/10

All grammar rules presented are correct. The case paradigms for "друг" and "книга" are accurate (modulo the column header terminology). The error analysis (Errors 1-3) is genuinely useful and correctly explained. The "melodic language" claim in the culture callout is an oversimplification but not factually wrong. No fabricated quotes, dates, or statistics found.

### 6. Curriculum Fit: 8/10

**Plan compliance:**
- ✅ All 5 H2 sections from meta content_outline present: «Вступ: Важливість відмінкової системи», «Презентація: Система та логіка», «Культурний аспект: Кличний відмінок», «Практика та аналіз помилок», «Діалоги та реальне застосування»
- ✅ Court Translator persona established and maintained
- ✅ All 7 cases covered with question words, functions, and examples
- ✅ Three learner errors covered as planned
- ✅ Courtroom simulation and summary checklist present
- ❌ Missing: "Gender forms summary for singular and plural nouns, focusing on the structural 'Declension Group' approach" — only a brief callout exists
- ✅ Vocabulary matches plan's required list (all 25 items present)
- ✅ Activities cover fill-in, quiz, match-up, and error correction as planned

### 7. Activity Quality: 7/10

**12 activities total, well-distributed across types:** fill-in (×2), quiz (×2), match-up, error-correction, unjumble, group-sort, true-false, mark-the-words, select, cloze. Good variety.

**Critical flaw:** The error-correction item «Я пишу синя ручка.» → «ручкою» leaves the adjective "синя" uncorrected (should be "синьою"). This teaches an incomplete correction.

**Minor issue:** The unjumble item «Добрий день шановний пане судде» (activities line 474) is missing a comma after "день" — the correct sentence is «Добрий день, шановний пане судде!» In a module teaching precision, punctuation matters.

**Strengths:** The cloze passage (courtroom scenario) is excellent — it contextualizes case practice in a coherent narrative. The group-sort (animate vs. inanimate) is pedagogically smart for A2. The select activities provide good practice with multiple correct answers.

### 8. LLM Fingerprint: 4/10

This dimension is severely impacted:

1. **Structural monotony:** 5 case subsections using identical «Як це працює:» / «Коли використовувати:» structure (lines 64-155)
2. **Filler blocks:** 4 paragraphs of repetitive short motivational sentences (lines 18, 174, 205, 336) — classic LLM padding when running out of content
3. **LLM cliché:** «Система відмінків — це двигун української мови» (line 356) — "двигун" is flagged as an LLM-typical metaphor
4. **Implausible examples:** «Камера на другові» (line 283) is not something a real Ukrainian speaker would say
5. **Callout monotony:** Not present — callout types vary ([!culture], [!tip], [!observe], [!warning], [!fact], [!myth-buster])

The combination of structural monotony + 4 filler blocks + "двигун" cliché pushes this to 4/10.

### 9. Humanity & Warmth: 6/10

**Counting warmth markers:**
- Direct address (ви): Very frequent (>20 instances) ✅
- Encouragement phrases: Technically present but overwhelmingly in the filler blocks — «Ви будете дуже пишатися собою», «Це ваша велика перемога», «Говоріть сміливо» — none of these feel earned or genuine
- "Don't worry" moments: «Все буде добре» (line 18) ✅
- "You can now..." validation: The summary checklist (lines 345-350) acts as this ✅

The fundamental problem: the module confuses **quantity of encouragement** with **quality of warmth**. Repeating «you'll speak perfectly, your friends will be amazed, your grammar will be the best» is not warmth — it's hollow flattery. Real warmth is specific: "You just learned all 7 cases — that's more than most learners manage in a month" or "The vocative might feel strange at first, but next time you say 'Друже!' a native speaker will smile." The filler blocks feel machine-generated, not human-tutored.

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Colonial framing | **FOUND** | Line 170: Russian used as baseline for vocative comparison |
| Russianisms | Not found | No vocabulary-level Russianisms detected |
| Calques | Not found | |
| Grammar scope violations | Not found | All content within A2 scope |
| Activity errors | **FOUND** | "синя ручка" → "ручкою" incomplete (should fix adjective too) |
| Incorrect terminology | **FOUND** | "Одиниця"/"Багато" instead of "Однина"/"Множина" (line 292) |
| LLM fingerprint | **SEVERE** | 5-section structural monotony + 4 filler blocks + "двигун" cliché |
| Implausible examples | **FOUND** | «Камера на другові» (line 283) |
| Plan compliance | **PARTIAL** | Missing declension group summary |
| Callout fabrication | Not found | Cultural claims are plausible |

---

## Verdict

**FAIL — Requires D.2 Repair**

The module has strong pedagogical bones: correct grammar throughout, well-structured dialogues, and varied activities. However, it is severely undermined by:

1. **Colonial framing** (line 170) — must be rewritten
2. **~150-200 words of LLM padding** across 4 paragraphs (lines 18, 174, 205, 336) — must be replaced with substantive content or removed
3. **Incorrect terminology** ("Одиниця"/"Багато") — must be corrected to "Однина"/"Множина"
4. **Incomplete activity correction** ("синя ручка") — must fix both adjective and noun
5. **Assembly-line case presentation** (5 identical subsections) — must be varied

**Fix priorities (D.2):**
1. Rewrite line 170 to present vocative without Russian comparison
2. Delete or replace all 4 filler paragraphs with substantive content (additional examples, mini-scenarios, cultural notes)
3. Fix line 292 column headers: "Одиниця" → "Однина", "Багато" → "Множина"
4. Fix activity "Я пишу синя ручка": error should be "синя ручка" → "синьою ручкою" (error_type: "phrase")
5. Vary the case presentation structure — don't use identical "Як це працює"/"Коли використовувати" for every case
6. Replace «Камера на другові» with a natural example
7. Add the missing declension group summary per plan
8. Remove «двигун» cliché from line 356