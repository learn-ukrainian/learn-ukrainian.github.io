<!-- content-hash: dd487b8f3a30 -->
**Reviewed-By:** claude-opus-4-6

# Phase D.1 Review: Taking Transport (a1-40)

**Module:** `curriculum/l2-uk-en/a1/taking-transport.md`
**Level:** A1 · Sequence 40 · Phase A1.4 (Practical Scenarios)
**Persona:** Patient Supportive Tutor / Marshrutka Veteran
**Word count:** 2257 / 2000 (112.9%) — meets minimum ✓

---

## Scores

| # | Dimension | Score | Notes |
|---|-----------|-------|-------|
| 1 | Lesson Quality | 7/10 | Cold start, late first practice, missing warm-up from plan |
| 2 | Language Quality | 8/10 | One A1-inappropriate term; IPA stress error |
| 3 | Immersion | 9/10 | 38.3% within A1.4 target (20–40%) |
| 4 | Activity Quality | 7/10 | Duplicated answer, content-inconsistent unjumble item |
| 5 | Richness | 8/10 | Strong cultural hooks; persona never explicitly voiced |
| 6 | Humanity & Warmth | 6/10 | COLD_PEDAGOGY — <3 encouragement markers for A1 |
| 7 | LLM Fingerprint | 7/10 | Classic AI section opener + 4× "Let's..." pattern |
| 8 | Factual Accuracy | 9/10 | All verifiable claims check out |

**Weighted Average: ~7.6/10**

---

## Critical Issues Found

### CRITICAL 1: COLD_PEDAGOGY — Severely Insufficient Warmth for A1

**Severity:** Critical (auto-fail concern for Tier 1)
**Location:** Module-wide

Warmth marker audit against beginner requirements:

| Marker | Required | Found | Status |
|--------|----------|-------|--------|
| Direct address (you/ви) | ≥15 | ~60 | PASS |
| Encouragement phrases ("Great!", "Well done!") | ≥3 | 1 | FAIL |
| "Don't worry" moments | ≥2 | 1 | FAIL |
| "You can now..." validation | ≥2 | 1 | FAIL |

The only encouragement in the entire module is the word "Congratulations!" at line 319 in section «Підсумок». There is one "Don't worry"-adjacent moment in the `[!myth-buster]` box at line 263: "Don't be afraid!" — but this is buried in a callout, not integrated into the teaching flow.

There is no warm greeting (no "Привіт!", no "Welcome!"). Section «Вступ: Транспорт у місті» opens with a blockquote and then a second-person imaginary scenario, but no emotional safety landing. Section «Презентація: Види транспорту та оплата» opens with the flat "Now that we know *how* to move, let's learn..." Section «Практика: Орієнтування в місті» similarly opens with "Now let's use this vocabulary in real situations."

The "Would I Continue?" test scores 2/5:
- Did I feel overwhelmed? **Borderline** — lots of content before first practice
- Were instructions clear? **Pass**
- Did I get quick wins? **Fail** — first practice exercise appears at line 268
- Was Ukrainian scary? **Pass** — good scaffolding throughout
- Would I come back tomorrow? **Fail** — informative but not encouraging

**Required fix:** Inject 3+ encouragement markers distributed across sections. Add a warm opening line. Add "Don't worry" reassurance before the grammar-heavy sections. Add a "You can now..." celebration at the end of section «Практика: Орієнтування в місті» before the consolidation.

---

### CRITICAL 2: Missing Plan-Required Warm-Up

**Severity:** High
**Location:** Section «Вступ: Транспорт у місті» (lines 15–91)

The plan (`content_outline`) explicitly requires: "Warm-up: 'Як ви їздите на роботу/навчання?' — introduction of the 'Marshrutka Veteran' persona." The meta's content_outline also specifies: "Ask the learner: 'Як ви їздите на роботу?'"

This warm-up question does not appear anywhere in the content. A Grep search for `їздите` returns zero matches. The section jumps straight from the opening blockquote to describing transport types without any learner engagement or warm-up question.

Additionally, the Marshrutka Veteran persona is never explicitly introduced or voiced. The plan specifies this persona should give "street-smart tips" but the content reads like a standard textbook throughout. The marshrutka scenarios in section «Практика: Орієнтування в місті» are good content but don't carry a distinct persona voice.

**Required fix:** Add the warm-up question «Як ви їздите на роботу/навчання?» at the start of section «Вступ: Транспорт у місті». Introduce the Marshrutka Veteran persona explicitly (even one line like "Think of me as your marshrutka-riding friend who knows all the tricks").

---

### ISSUE 3: IPA Stress Error on «двері»

**Severity:** High
**Location:** Line 121

The IPA transcription reads: ``

The stress mark on «двері» is placed as `dʋɛˈri` (stress on second syllable). The correct stress is on the **first** syllable: `ˈdʋɛrʲi`. This is a pronunciation error that learners will directly copy.

**Required fix:** Change `dʋɛˈri` to `ˈdʋɛrʲi` on line 121.

---

### ISSUE 4: A1-Inappropriate Vocabulary

**Severity:** Medium
**Location:** Line 107

The sentence «Це велика будівля або інфраструктурний об'єкт» uses «інфраструктурний об'єкт» which is B2+ vocabulary. An A1 learner has no chance of understanding this Ukrainian term. The word «інфраструктурний» alone is 19 characters of abstract technical vocabulary.

**Required fix:** Replace with simpler phrasing, e.g., «Це велика будівля» is sufficient. If elaboration is needed: «Це велика будівля для метро або поїзда.»

---

### ISSUE 5: Activity — Unjumble Content Mismatch

**Severity:** Medium
**Location:** Activities file, lines 183–184

The unjumble item produces the sentence: «Обережно, двері зараз зачиняються.»

However, the content consistently teaches the phrase **without** «зараз»:
- Line 114: «Обережно, двері зачиняються. Наступна **станція** — Майдан Незалежності»
- Line 121: «Обережно, двері зачиняються»
- Line 301: «Обережно, двері зачиняються. Наступна станція — "Тараса Шевченка"»

The word «зараз» is not part of the standard metro announcement taught in the lesson. This will confuse learners who studied the phrase and now see an extra word in the exercise.

**Required fix:** Remove «зараз» from the unjumble: `words: ['Обережно,', 'двері', 'зачиняються', '.']` and `answer: 'Обережно, двері зачиняються.'`

---

### ISSUE 6: Activity — Duplicated Fill-In Answer

**Severity:** Medium
**Location:** Activities file, lines 152–155 and 164–167

Two fill-in items in the "Чим ви їдете?" activity both have «тролейбусом» as the answer:
- Line 152: `'Студенти часто їздять {{answer}}.'` → `тролейбусом`
- Line 164: `'Вона їде до школи {{answer}}.'` → `тролейбусом`

This duplication reduces variety. With 8 items in the activity, 25% test the exact same answer. One of these should test a different transport form (e.g., «трамваєм» or «поїздом» which are only tested once each).

**Required fix:** Change one of the тролейбусом items to use a different instrumental form.

---

### ISSUE 7: LLM Fingerprint — AI Section Opener

**Severity:** Medium
**Location:** Line 19

The sentence "In this section, we will look at the main types of transport and the grammar of movement." is a classic LLM-generated opener. Real tutors don't announce "in this section we will..." — they just start teaching.

Additionally, 4 instances of "Let's..." pattern as section/paragraph openers:
- Line 82: "Let's look at a comparison table..."
- Line 194: "Let's compare them:"
- Line 268: "Let's test your logic."
- Line 287: "Let's put everything together..."

While each individual "Let's" is fine, the repetition creates structural monotony.

**Required fix:** Replace line 19 with a more natural transition (e.g., "The main transport types first — and the grammar of movement along with them."). Vary at least 2 of the "Let's..." openers with different phrasing.

---

## Factual Verification

| Claim | Source/Verification | Status |
|-------|-------------------|--------|
| Arsenalna station is deepest in the world at 105.5m (line 46) | Widely verified; research notes confirm | ✓ Correct |
| Escalator ride ~5 minutes (line 46) | Most sources cite 3–5 min; "about 5 minutes" is the upper bound but defensible | ✓ Acceptable |
| Kyiv, Kharkiv, Dnipro have metro (line 26) | Correct — only 3 Ukrainian cities with metro | ✓ Correct |
| Kyiv Digital app for transport payment (line 156) | Current as of 2024–2025 | ✓ Correct |
| Marshrutkas still use cash (line 156) | Generally true, though some accept cards now; content correctly uses "still king" qualifier | ✓ Correct |
| Tokens no longer used in Kyiv metro (line 203–204, activity) | Жетони phased out 2020–2021 | ✓ Correct |
| «Метро» and «таксі» are indeclinable (line 78) | Standard Ukrainian grammar | ✓ Correct |

No factual errors detected.

---

## Verification Summary

### Plan Compliance

| Plan Element | Present? | Notes |
|--------------|----------|-------|
| Section «Вступ: Транспорт у місті» | ✓ | Lines 15–91 |
| Section «Презентація: Види транспорту та оплата» | ✓ | Lines 92–201 |
| Section «Практика: Орієнтування в місті» | ✓ | Lines 203–283 |
| Section «Закріплення: Подорож метром» | ✓ | Lines 285–313 |
| Section «Підсумок» | ✓ | Lines 317–329 |
| Warm-up question «Як ви їздите на роботу?» | ✗ | Missing — plan violation |
| Marshrutka Veteran persona | ✗ | Never introduced/voiced |
| іти vs їхати contrast | ✓ | Lines 48–67 |
| Instrumental case for transport | ✓ | Lines 68–91 |
| Зупинка vs Станція | ✓ | Lines 96–116 |
| Metro announcements | ✓ | Lines 117–132 |
| Payment vocabulary | ✓ | Lines 134–156 |
| Transfer logic | ✓ | Lines 158–175 |
| Locative vs Accusative | ✓ | Lines 176–201 |
| Marshrutka scenarios | ✓ | Lines 234–264 |
| Narrative consolidation | ✓ | Lines 289–307 |
| All required vocabulary | ✓ | 26 items cover all required + recommended |

### Activity Coverage

| Activity Type | Count | Issues |
|---------------|-------|--------|
| group-sort | 1 (12 items) | Clean |
| match-up | 2 (8 + 8 items) | Minor: "Передайте за проїзд" → "Pass the fare, **please**" adds "please" not in Ukrainian |
| quiz | 2 (8 + 8 items) | Clean |
| fill-in | 3 (8 + 8 + 8 items) | Duplicate тролейбусом; good otherwise |
| unjumble | 1 (6 items) | «зараз» mismatch |
| true-false | 1 (8 items) | Clean |
| **Total** | **10 activities (74 items)** | 3 issues flagged |

### Section-by-Section Assessment

**Section «Вступ: Транспорт у місті»** — Solid content introducing transport types with good cultural hooks. Missing the warm-up question and persona introduction. The iти/їхати contrast is well explained. The `[!culture]` box about Arsenalna is engaging. The Instrumental case table at lines 84–90 is clean and visual.

**Section «Презентація: Види транспорту та оплата»** — The зупинка/станція distinction (lines 96–116) is well done. The `[!tip]` box with metro vs bus announcement comparison is excellent pedagogically. Payment vocabulary is current and practical. The Locative vs Accusative comparison table (lines 196–201) is clear. However, line 107 uses «інфраструктурний об'єкт» which is far too complex for A1.

**Section «Практика: Орієнтування в місті»** — The marshrutka scenarios (lines 234–264) are the strongest part of the module — authentic, practical, and immersive. The dialogue at lines 224–232 is natural and useful. The `[!myth-buster]` box at line 262 provides genuine reassurance. The fill-in exercise at lines 266–283 is a good practice element.

**Section «Закріплення: Подорож метром»** — The narrative text (lines 291–307) is excellent — vivid, uses all target vocabulary naturally, includes cultural details (giving up seat, musician in passage). Comprehension questions are well targeted.

**Section «Підсумок»** — Functional summary that hits the main points. The self-check questions are useful. However, the opening "Congratulations!" is the only encouragement marker in the entire module, which is insufficient.

### Vocabulary File

- 26 items covering all required and recommended vocabulary ✓
- IPA issue: «вхід» transcribed as `[ʍxʲid]` — the ʍ (voiceless labial-velar fricative) is non-standard for Ukrainian phonological transcription. Expected: `[ʋxʲid]` or `[fxʲid]` (with devoicing assimilation).
- All other IPA transcriptions spot-checked as correct.

---

## Verdict

**REVISE** — The module has strong bones: excellent cultural content, accurate grammar explanations, engaging marshrutka scenarios, and a compelling metro narrative. However, it fails the A1 warmth requirements (COLD_PEDAGOGY), is missing a plan-required warm-up element, and has an IPA stress error that would teach incorrect pronunciation. The activity file has a content-inconsistent unjumble item and a duplicated answer.

**Fix priority:**
1. **Warmth injection** (Critical) — Add ≥3 encouragement markers, warm greeting, "Don't worry" moments
2. **Add warm-up question** (High) — «Як ви їздите на роботу?» per plan
3. **Fix IPA** (High) — `dʋɛˈri` → `ˈdʋɛrʲi` on line 121
4. **Simplify vocabulary** (Medium) — Replace «інфраструктурний об'єкт» on line 107
5. **Fix unjumble** (Medium) — Remove «зараз» from activity line 183
6. **Fix duplication** (Medium) — Change one тролейбусом fill-in to different transport
7. **Reduce LLM fingerprint** (Medium) — Rewrite line 19, vary "Let's" openers