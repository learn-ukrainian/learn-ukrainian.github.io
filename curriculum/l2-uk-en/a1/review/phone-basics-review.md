<!-- content-hash: 93601a4f4ccd -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score |
|---|-----------|-------|
| 1 | Lesson Quality | 8 / 10 |
| 2 | Language Quality (Ukrainian) | 8 / 10 |
| 3 | Language Quality (English) | 8 / 10 |
| 4 | Activity Quality | 7 / 10 |
| 5 | Vocabulary Quality | 7 / 10 |
| 6 | Immersion Balance | 9 / 10 |
| 7 | Richness | 8 / 10 |
| 8 | Humanity & Warmth | 7 / 10 |
| 9 | LLM Fingerprint | 8 / 10 |
| 10 | Factual Accuracy | 9 / 10 |
| 11 | Plan Compliance | 7 / 10 |

---

## Critical Issues Found

### Issue 1 (CRITICAL): Activities Test Untaught Content — Plan Point Missing from Lesson

**Location:** Content file — Section «Презентація: Основні структури» (lines 99-121); Activities file (lines 52-58, 365-367)

The plan (line 26) explicitly requires: "Asking for contact: Using simple phrases like «Чи можу я поговорити з...?»". However, the phrase «Чи можу я поговорити з...?» **never appears in the content file**. A Grep for "поговорити" in the content file returns **zero matches**.

Despite this, the activities file tests this phrase in two places:
- Fill-in item (line 52): `Чи ___ я поговорити з Анною?` (answer: можу)
- True-false item (line 365): `To ask 'May I speak with Anna?', you say 'Чи можу я поговорити з Анною?'.` (marked correct)

Additionally, the unjumble activity (line 220-223) uses «Я хочу поговорити з директором» — a phrase also never presented in the lesson.

This is a **PPP violation**: Practice before Presentation. Learners are being tested on material they were never taught. The plan required this phrase to be presented in Section «Презентація: Основні структури», and it was omitted.

**Fix:** Add «Чи можу я поговорити з Анною?» / «Чи можу я поговорити з...?» as a taught example in the "Asking to Speak with Someone" subsection (after line 105), with English translation and usage explanation.

### Issue 2 (MAJOR): Unjumble Answers Missing Required Punctuation

**Location:** Activities file, unjumble activity (lines 229, 235)

Two unjumble answers omit commas that are present in the source content:

1. Line 229: `answer: Вибачте я помилився номером` — Missing comma after "Вибачте". The content (line 172) has «Вибачте, я помилився номером.»
2. Line 235: `answer: Залиште будь ласка повідомлення` — Missing commas around "будь ласка". The content (line 198) has «Залиште, будь ласка, біля дверей.»

For A1 learners, commas around "будь ласка" and after "Вибачте" are important punctuation patterns to internalize. Unjumble answers that omit them teach incorrect habits.

**Fix:** Update the unjumble answers to: `Вибачте, я помилився номером` and `Залиште, будь ласка, повідомлення`.

### Issue 3 (MAJOR): Three Vocabulary IPA Entries Missing Stress Marks

**Location:** Vocabulary file (lines 47, 63, 85)

Three vocabulary items have IPA transcriptions with no stress mark at all:

1. Line 47: `помилитися` — IPA: `[pɔmɪlɪtɪsʲɑ]`. Should be `` (stress on third syllable: помили́тися)
2. Line 63: `до зв'язку` — IPA: `[dɔ zʋjɑzku]`. Should be `` (stress on last syllable: до зв'язку́). Note: the content file (line 149) correctly uses `` with the stress mark, so the vocabulary file is inconsistent.
3. Line 85: `зв'язок` — IPA: `[zʋjɑzɔk]`. Should be `` (stress on first syllable: зв'я́зок)

Stress marks in IPA are critical for A1 learners who cannot yet infer stress from orthography.

**Fix:** Add the missing stress marks (ˈ) to all three IPA transcriptions.

### Issue 4 (MODERATE): Repetitive Superlative Adverbs in English Prose

**Location:** Content file, lines 73, 149, 264

The word "incredibly" appears three times in the English prose:
- Line 73: «Mastering this small detail will make your Ukrainian sound incredibly natural and fluid!»
- Line 149: «It is incredibly popular right now»
- Line 264: «these high-frequency collocations that will make you sound incredibly natural»

The word "wonderful" appears twice (lines 33, 231). Combined with the triple "incredibly," this creates a pattern of over-enthusiastic English that reads as formulaic rather than genuinely warm. A human tutor would vary their encouragement more naturally.

**Fix:** Replace at least 2 of the 3 "incredibly" instances with varied phrasing (e.g., "very," "really," "remarkably," or restructure the sentence entirely).

### Issue 5 (MODERATE): Warmth Markers Below Beginner Threshold

**Location:** Across all sections

The module has minimal direct encouragement for a beginner lesson:
- No instances of "Great!", "Well done!", "You've got this!" or equivalent
- Only 1 "Don't worry" moment (line 231: «If you feel nervous about calling...»)
- No explicit "You can now..." celebration statements in English. The closest is Ukrainian at line 237: «Ви можете представити себе. Ви можете вирішити проблеми.» — but the warmth rubric requires ≥2 "You can now..." validations and ≥3 encouragement phrases

The Summary section (Section «Продукція та підсумок») ends with self-check questions (lines 267-271) rather than celebration. A nervous beginner finishes the lesson with a test rather than validation.

**Fix:** Add 2-3 explicit encouragement phrases (in English or bilingual) throughout the lesson, and reframe the final paragraph to celebrate progress before the self-check questions.

---

## Factual Verification

**Grammar rules:** The explanation of the formal imperative ending -іть/-йте (line 138) is correct. The description of «дз» as a single affricate (line 62) is accurate. The correction of «Я є Олена» to «Це Олена» (lines 81-94) is accurate and well-explained.

**Cultural claims:**
- «Слухаю» as professional phone greeting: Accurate, confirmed in research notes (line 17)
- «До зв'язку» as modern sign-off: Accurate, confirmed in research notes (line 18)
- Telegram and Viber as main Ukrainian messaging platforms (line 216): Accurate and current

**Callout boxes:**
- `[!culture]` (line 35-36): «Слово "слухаю" показує активну увагу. Це не просто привітання.» — Accurate claim, no fabrication
- `[!tip]` (line 55-56): «Студенти часто роблять помилку. Вони використовують "ти" з кур'єром.» — Plausible and supported by research notes (line 23)
- `[!fact]` (line 140-141): «Український наказовий спосіб має чітку структуру. Формальне закінчення відповідає займеннику "Ви".» — Accurate grammatical claim
- `[!observe]` (line 211-212): «Ці розмови дуже прямі. В Україні люди цінують ясність.» — Reasonable cultural observation, not a factual claim requiring verification

**No factual errors found.** All claims are accurate or grounded in the research notes.

---

## Dimension Evidence

### Lesson Quality (8/10)

**"Would I Continue?" test:**
- Did I feel overwhelmed? **Pass** — pacing is comfortable, English scaffolding present throughout
- Were instructions clear? **Fail** — Activities test «Чи можу я поговорити з Анною?» which was never taught (Issue 1)
- Did I get quick wins? **Pass** — early example phrases with translations in Section «Вступ та етикет»
- Was Ukrainian scary? **Pass** — introduced gently with support
- Would I come back? **Pass** — lesson feels approachable overall

4/5 passes → 9/10 baseline, minus 1 for the untaught-content problem → **8/10**

**Lesson arc:** WELCOME (line 16 "Вітаємо!") → PREVIEW (line 10-12 "Чому це важливо?" block) → PRESENT (sections 1-2) → PRACTICE (section 3 scenarios) → CELEBRATE (section 4 summary table + dialogues). Arc is well-structured but the CELEBRATE element is weak — ends on a quiz rather than encouragement.

### Language Quality — Ukrainian (8/10)

Ukrainian sentences are grammatically correct and appropriate for A1 throughout. No Russianisms found. No colonial framing found (Grep for "Russian" in content returned zero matches).

Minor issues:
- Line 40: «Вибір між **Ви** та **ти** дуже важливий.» — When using pronouns as metalinguistic objects, they should be in quotation marks: між «Ви» та «ти». This is a typographic rather than grammatical issue.
- Line 101: «Ви маєте ввічливо попросити потрібну особу.» — The phrase "попросити потрібну особу" is slightly unnatural in phone context. More natural: "попросити до телефону потрібну людину" or simply "попросити потрібну людину до телефону."
- Line 218: «Ви почуєте слово **за́йнятий**.» — Somewhat odd phrasing. The learner wouldn't "hear the word зайнятий" literally; they'd hear "Лінія зайнята" or get a busy tone. Rephrase to clarify context.

### Language Quality — English (8/10)

English is clear and accessible at B1 readability. Contractions are used naturally ("you'll", "don't"). Explanations are well-structured.

Issues:
- "incredibly" × 3, "wonderful" × 2 — repetitive superlative language (Issue 4)
- Line 33: «Using the polite option shows deep respect for the caller.» — "deep respect" is slightly over-elevated for a phone greeting
- Line 94: «The second option, adding your name before the verb for listening, is especially elegant when answering business calls.» — "especially elegant" is over-the-top for a functional phrase
- Overall, the English register skews slightly too elevated/enthusiastic rather than the warm-but-grounded voice of a patient tutor

### Activity Quality (7/10)

**Variety:** 6 activity types (match-up, true-false, fill-in ×2, quiz ×2, unjumble, group-sort) = excellent variety.

**Item count:** 10 activities with many items each — well above minimum.

**Issues:**
1. PPP violation — fill-in and true-false test untaught phrase «Чи можу я поговорити з Анною?» (Issue 1)
2. Unjumble punctuation errors (Issue 2)
3. Fill-in item (line 59-65): «Скажіть» vs. distractor «Кажіть» — "Кажіть" (imperfective imperative of казати) is grammatically plausible in context, making it a potentially confusing distractor for A1 learners who cannot distinguish perfective/imperfective aspect
4. Unjumble activity «Я хочу поговорити з директором» (line 220-223) — phrase "поговорити з директором" never taught in content

### Vocabulary Quality (7/10)

20 items with good topical coverage. Appropriate for the module scope.

**Issues:**
- 3 IPA entries missing stress marks (Issue 3)
- `слухаю` is listed as pos: "verb" (line 40) but it's a conjugated first-person present form, not a lemma. The lemma should be "слухати" with "слухаю" as a derived form or key phrase. However, since it's taught as a fixed phone greeting formula, listing the conjugated form is arguably justified for A1.

### Immersion Balance (9/10)

36.4% Ukrainian immersion. For A1.4 (module 41, late A1), the target per audit metrics is 35-55%. The module lands at the low end, which is appropriate for a practical-scenario module where English scaffolding is critical for explaining cultural nuances and grammar patterns. Good use of bilingual dialogues. No issues.

### Richness (8/10)

4 callout boxes with varied types: `[!culture]`, `[!tip]`, `[!fact]`, `[!observe]`. Summary table in Section «Продукція та підсумок» (lines 241-248) is clean and useful. Two dialogue simulations (formal clinic call, informal friend call) provide good contrast. Self-check questions (lines 267-271) are well-targeted. Three scenario-based subsections provide real-world grounding (wrong number, courier, messaging).

Could be richer with a pronunciation audio reference or a callout box in Section «Практика: Життєві ситуації».

### Humanity & Warmth (7/10)

**Direct address:** Frequent use of "Ви" and "you" — ≥15 instances. **Pass.**

**Encouragement phrases:** The module encourages through future-benefit statements ("will make you sound natural") rather than present-tense validation ("Great job!", "You've got this!"). Only line 231 directly addresses learner anxiety. **Below threshold** — needs ≥3 encouragement phrases.

**"Don't worry" moments:** 1 (line 231). Threshold: ≥2. **Below threshold.**

**"You can now..." validation:** Line 237 in Ukrainian: «Ви можете представити себе. Ви можете вирішити проблеми.» counts as 1 combined instance. Threshold: ≥2. **Below threshold.**

Missing warmth at the beginner-critical level. The module is informative but not as emotionally warm as it should be for A1.

### LLM Fingerprint (8/10)

**Structural monotony:** Section openings are varied — no 3+ identical patterns. **Pass.**

**Example batching:** Examples across sections use a consistent `*   **Ukrainian.** / *   English.` format, but this is standard bilingual formatting, not monotonous. Dialogue formats vary (inline, mini-dialogue, full simulation). **Pass.**

**Repetitive word choice:** "incredibly" × 3 is the main concern. Not a classic AI cliché, but the repetition is noticeable.

**"Це не просто" pattern:** 1 instance (line 36). Below 2+ threshold. **Pass.**

**Generic AI rhetoric:** No instances of "In this lesson, we will explore" or "It is important to note." **Pass.**

**Callout monotony:** 4 callouts with 4 different types — no repetition. **Pass.**

### Factual Accuracy (9/10)

All grammar explanations verified. All cultural claims grounded in research notes. No fabricated claims in callout boxes. No issues found.

### Plan Compliance (7/10)

**Content outline compliance:**
- Section «Вступ та етикет»: All 3 points covered (Алло vs. Слухаю, Ви vs. ти, pronunciation дз). **✓**
- Section «Презентація: Основні структури»: 3 of 4 points covered. **Missing:** «Чи можу я поговорити з...?» from the "Asking for contact" point (plan line 26). The content uses «А Анна є?» and «Скажіть, будь ласка, де Олег?» but omits the explicit "Can I speak with...?" formula. **✗**
- Section «Практика: Життєві ситуації»: All 3 scenario points covered. **✓**
- Section «Продукція та підсумок»: All 3 points covered (summary table, dialogue simulations, collocations recap). **✓**

**Grammar scope:** Plan lists "Could you... (Чи могли б ви...)" as a grammar point. This conditional form is absent from the content. This may be intentionally excluded as too complex for A1, but it's a plan deviation.

**Vocabulary scope:** All 8 required and 7 recommended vocabulary items from the plan are present in the vocabulary file.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Colonial framing | **CLEAN** — no Russian comparisons found |
| Russianisms | **CLEAN** — no Russianisms detected |
| Factual accuracy | **PASS** — all claims verified |
| LLM fingerprint | **MINOR** — "incredibly" × 3 |
| Activity errors | **FAIL** — untaught content tested, punctuation errors |
| IPA accuracy | **FAIL** — 3 vocab items missing stress marks |
| Plan compliance | **FAIL** — key plan phrase missing from content |
| Word count | **PASS** — 2121/2000 (106%) |
| Warmth threshold | **FAIL** — below ≥3 encouragement, ≥2 "don't worry" thresholds |

---

## Verdict

**REVISE** — The module has a solid structural foundation with good scenario-based teaching, accurate Ukrainian, and appropriate immersion balance. However, it requires revision for three blocking issues:

1. **PPP violation:** The phrase «Чи можу я поговорити з...?» must be added to the content before it can be tested in activities (Issue 1).
2. **Activity punctuation:** Unjumble answers must include correct punctuation (Issue 2).
3. **Vocabulary IPA:** Three items need stress marks added (Issue 3).

Secondary improvements needed: warmth injection (Issue 5), English repetitiveness reduction (Issue 4), and minor Ukrainian phrasing fixes (lines 101, 218).