**Reviewed-By:** claude-opus-4-6

## Scores

| # | Dimension | Score | Evidence |
|---|-----------|-------|----------|
| 1 | **Plan Compliance** | 9 | All 5 plan sections present as H2 headers. All content_outline points covered. Minor gap: plan mentions «зайти» (§Prepositional Hooks) but content doesn't teach this form. Vocabulary coverage matches vocabulary_hints. |
| 2 | **Language Quality** | 7 | **Factual grammar error** in section «Презентація: В- та Ви-» at line 129: the [!fact] callout claims «входити» й «уходити» — це те саме слово», which is incorrect — «уходити» is NOT a standard euphonic variant of «входити». The в-/у- alternation applies to perfective forms (увійти/ввійти) but NOT to imperfective входити. Additionally, line 111 calls «їжджати» a base verb — it is not a standalone verb in Ukrainian; the actual bases are їздити (multidirectional) and їхати (unidirectional). **Systematic double periods** (..) appear in ~25 example sentences (lines 62, 65, 77, 78, 86-88, 94-96, 108-109, etc.). No Russianisms found. |
| 3 | **Activity Quality** | 8 | 12 activities, 8 unique types — solid variety. All activity types valid per A2 schema. Item content is well-scaffolded and directly mirrors lesson material. Minor issue: select activity at lines 336-347 asks «Які написи можна побачити на дверях у Києві?» and marks «В'їзд» as incorrect, but В'їзд is a real sign in Kyiv (on vehicle entrances/gates); the "на дверях" qualifier makes it defensible but could confuse learners. |
| 4 | **Richness** | 7 | Audit shows 77% (threshold 95%). Gaps: **cultural: 1/3** — only one [!culture] callout (line 25, «Свій і чужий простір»); the Threshold and Metro sections are cultural but lack [!culture] callout tags. **dialogues: 0/4** — section «Підсумок та діалоги» contains a first-person monologue (line 273, «Ранковий маршрут»), not a dialogue. Two micro-exchanges exist (lines 161-162, 177-178) but are embedded in cultural context, not structured dialogues. |
| 5 | **LLM Fingerprint** | 7 | **Structural monotony**: Sections «Культурний контекст», «Практика та помилки», and «Підсумок та діалоги» all open with abstract philosophical statements about language: «Граматика не існує у вакуумі» (line 155), «Теорія — це чудово, але мова живе у практиці» (line 189), «Мова найкраще засвоюється через історії та живе спілкування» (line 268). Three sections with identical opening pattern = structural monotony. **LLM cliché** confirmed: «Мова — це дзеркало культури» (line 155) — flagged by D.0. **"Це не просто"** pattern at line 21: «префікс — це не просто набір літер». |
| 6 | **Factual Accuracy** | 7 | **Critical error**: Line 129 states «Тому «входити» й «уходити» — це те саме слово (to enter)!» — this is factually wrong. «Уходити» is not a recognized euphonic variant of «входити» in standard Ukrainian. The euphonic в-/у- alternation operates on perfective forms like увійти/ввійти, not on imperfective входити. A learner reading this would incorrectly believe «уходити» means "to enter," when in some contexts it could be parsed as "to go away" (cf. Russian уходить). Line 111 presents «їжджати» as a standalone base verb — it only exists as a stem in prefixed forms, not as an independent verb. |
| 7 | **Lesson Quality** | 8 | **"Would I Continue?" test**: (1) Overwhelmed? No — pacing is comfortable with gradual introduction ✓ (2) Instructions clear? Yes, three-step algorithm at lines 230-232 is excellent ✓ (3) Quick wins? The box analogy and conjugation review provide early success ✓ (4) Ukrainian scary? Introduced with English scaffolding ✓ (5) Come back tomorrow? Engaging cultural content (threshold, metro) ✓ → 5/5 pass BUT warmth is mechanical. The "Taxi Driver" persona from the plan is completely absent — no personality, no character voice. Opening lacks warm greeting. Closing (line 306) is generic: «Рухайтеся впевнено» instead of a proper celebration. |
| 8 | **Immersion** | 9 | 70.9% Ukrainian — well within the A2 Band 2 target of 60-75%. English used appropriately for abstract grammar explanations (aspect, case logic). Ukrainian used for all examples, dialogues, and practice. Good graduated balance. |
| 9 | **Humanity & Warmth** | 7 | Direct address ("ви", "ваш") used throughout — good. However: **no warm greeting** at the module opening (starts with a philosophical quote box). Only **1 explicit encouragement** phrase at line 306 («Рухайтеся впевнено. Ваша українська стає кращою з кожним кроком!»). Missing the required minimum of ≥3 encouragement phrases, ≥2 "don't worry" moments, ≥2 "you can now" validation markers. The module reads like a thorough textbook, not a patient tutor. |

## Critical Issues Found

### Issue 1: FACTUAL_ERROR — False Euphony Claim (CRITICAL)

- **Location**: Section «Презентація: В- та Ви-», line 129, [!fact] callout «Фонетична гнучкість»
- **Verbatim**: «Тому «входити» й «уходити» — це те саме слово (to enter)!»
- **Problem**: This is factually incorrect. The euphonic в-/у- alternation for prefixes applies to perfective forms (увійти → ввійти after vowel) but NOT to imperfective входити. The form «уходити» is NOT a recognized standard Ukrainian variant of «входити». It could be misread as related to Russian «уходить» (to leave/go away), creating exactly the kind of Russicism confusion this module should prevent.
- **Fix**: Rewrite the [!fact] callout to correctly state that the в-/у- alternation applies to the perfective pair увійти/ввійти. Remove the false claim about входити/уходити.

### Issue 2: FORMATTING — Systematic Double Periods (MEDIUM)

- **Location**: ~25 example sentences throughout all sections
- **Lines**: 62, 65, 77, 78, 86, 87, 88, 94, 95, 96, 108, 109, 112, 113, 116, 117, 135, 136, 139, 196, 199, 220, 223, 281, 284, 287
- **Example**: Line 62: «Він входить у коробку..» — double period instead of single
- **Fix**: Find-and-replace all instances of `..` with `.` in example sentences.

### Issue 3: LLM_STRUCTURAL_MONOTONY — Identical Section Openings (MEDIUM)

- **Location**: First lines of sections «Культурний контекст» (line 155), «Практика та помилки» (line 189), «Підсумок та діалоги» (line 268)
- **Pattern**: All three open with abstract philosophical statements about language/grammar:
  - «Граматика не існує у вакуумі. Мова — це дзеркало культури.» (line 155)
  - «Теорія — це чудово, але мова живе у практиці.» (line 189)
  - «Мова найкраще засвоюється через історії та живе спілкування.» (line 268)
- **Fix**: Rewrite section openings with varied hooks — a concrete situation, a question, a mini-scenario. Remove «Мова — це дзеркало культури» (LLM cliché).

### Issue 4: RICHNESS_GAP — Missing Dialogues (MEDIUM)

- **Location**: Section «Підсумок та діалоги», lines 270-275
- **Problem**: The plan specifies "Morning Routine Dialogue" but the content delivers a first-person monologue: «Доброго ранку! О сьомій годині я снідаю...». This is narration, not dialogue. The richness audit shows dialogues: 0/4.
- **Fix**: Convert the morning routine into a proper 2-person dialogue (e.g., a colleague asking about commute, or the Taxi Driver persona asking a passenger about their morning route). Add at least 2 more structured dialogue exchanges elsewhere (e.g., at the metro, at a building entrance).

### Issue 5: RICHNESS_GAP — Insufficient [!culture] Callouts (LOW)

- **Location**: Throughout section «Культурний контекст»
- **Problem**: Only 1 [!culture] callout (line 25, «Свій і чужий простір»). Richness requires 3. The Threshold section (lines 157-168) and Metro section (lines 170-178) contain cultural content but aren't tagged with [!culture].
- **Fix**: Add [!culture] callouts to the Threshold subsection and to the Metro/Urban navigation subsection.

### Issue 6: PEDAGOGICAL_ERROR — False Base Verb Reference (LOW)

- **Location**: Section «Презентація: В- та Ви-», line 111
- **Verbatim**: «ви використовуєте базу "їжджати"»
- **Problem**: «Їжджати» is not a standalone Ukrainian verb — it only exists as a stem within prefixed forms (в'їжджати, виїжджати). The actual base verbs are їздити (multidirectional) and їхати (unidirectional), both of which are correctly listed in section «Вступ». Calling «їжджати» a "base" contradicts the module's own earlier presentation.
- **Fix**: Rewrite to: «ви використовуєте основу на -їздити/-їхати» or explain that the stem changes when a prefix is added.

### Issue 7: WARMTH_DEFICIT — Missing Encouragement Markers (LOW)

- **Location**: Throughout all sections
- **Problem**: Only 1 encouragement phrase found (line 306). Required minimums: ≥3 encouragement phrases, ≥2 "don't worry" moments, ≥2 "you can now" validations. Module reads like a textbook rather than a warm tutoring session.
- **Fix**: Add 2-3 brief encouragement beats between subsections (e.g., after the conjugation review in «Вступ», after the first practice exercise in «Практика та помилки»). Add a "don't worry" moment in the aspect section. End with a "You can now..." celebration listing specific skills gained.

## D.0 Pre-Screen Verification

| # | D.0 Finding | Verdict | Notes |
|---|-------------|---------|-------|
| 1 | `[LLM_FILLER]` «дзеркало культури» at ~line 140 | **CONFIRMED** | Found at line 155: «Мова — це дзеркало культури» — generic LLM metaphor. Part of broader structural monotony issue (Issue #3). |

## Factual Verification

| Claim | Source | Verdict |
|-------|--------|---------|
| Threshold taboo (не вітатися через поріг) | Research notes: "traditionally forbidden to greet someone, shake hands, or pass money across the threshold" | ✅ VERIFIED |
| «Вхід» and «Вихід» signs in Kyiv Metro | Research notes: "'Вхід' (Entrance) and 'Вихід' (Exit) are ubiquitous signs" | ✅ VERIFIED |
| «Не притулятися» warning on metro doors | Research notes: "common on automatic doors" | ✅ VERIFIED |
| «входити» and «уходити» are the same word | Standard Ukrainian orthography (Правопис 2019) | ❌ INCORRECT — euphonic в-/у- prefix alternation does NOT apply to imperfective входити |
| «їжджати» as a standalone base verb | Ukrainian grammar references | ❌ MISLEADING — «їжджати» is a stem, not an independent verb |
| Aspectual pairs: входити/увійти, виходити/вийти, в'їжджати/в'їхати, виїжджати/виїхати | Research notes, State Standard | ✅ VERIFIED |
| «Входити в моду» idiom | Common Ukrainian idiom | ✅ VERIFIED |
| «Виходити заміж» — woman "exits" her family | Standard etymological explanation | ✅ VERIFIED |

## Colonial Framing Check

Line 212 references Russian: «замість суржику «слідуючого разу» чи «приймати участь»» — this is within a [!warning] callout explicitly warning against surzhyk. This is **legitimate** anti-Russicism pedagogy, not colonial framing. No instances of Ukrainian defined by contrast with Russian as baseline found. **PASS**.

## Verification Summary

| Check | Result |
|-------|--------|
| All H2 sections from plan present? | ✅ Yes: «Вступ», «Презентація: В- та Ви-», «Культурний контекст», «Практика та помилки», «Підсумок та діалоги» |
| Vocabulary hints covered? | ✅ All required (входити, виходити, в'їжджати, виїжджати) and recommended (вхід, вихід, поріг, увійти) present |
| Grammar scope clean? | ✅ No scope creep beyond в-/ви- prefixes (line 161 uses «заходьте» but as a formulaic expression, acceptable) |
| Russianisms found? | ✅ None found. Warning against surzhyk at line 212 is appropriate |
| Colonial framing? | ✅ None found |
| Factual errors? | ❌ 1 critical (line 129: входити/уходити false equivalence), 1 minor (line 111: їжджати as base verb) |
| Activity schema valid? | ✅ All 12 activities use valid A2 types |
| Immersion in range? | ✅ 70.9% (target 60-75%) |
| Double periods? | ❌ ~25 instances of systematic formatting error |
| LLM fingerprints? | ❌ Structural monotony in 3 section openings; «дзеркало культури» cliché; «це не просто» pattern |
| Dialogue requirement met? | ❌ No structured dialogues despite section title «Підсумок та діалоги» |

## Fix Plan

### Priority 1 — Critical Fixes

1. **Rewrite [!fact] callout at line 127-129** (section «Презентація: В- та Ви-»): Remove the false claim that «входити» and «уходити» are the same word. Replace with accurate explanation of the увійти/ввійти alternation after consonant/vowel-ending words. Keep the general euphony principle but correct the specific example.

2. **Fix all double periods** (all sections): Replace `..` with `.` across ~25 example sentences. Lines 62, 65, 77, 78, 86-88, 94-96, 108-109, 112-113, 116-117, 135-136, 139, 196, 199, 220, 223, 281, 284, 287.

### Priority 2 — Medium Fixes

3. **Rewrite 3 section openings** to eliminate structural monotony:
   - Section «Культурний контекст» (line 155): Replace «Граматика не існує у вакуумі. Мова — це дзеркало культури.» with a concrete hook (e.g., a scene at a Ukrainian household threshold).
   - Section «Практика та помилки» (line 189): Replace «Теорія — це чудово, але мова живе у практиці.» with a direct address (e.g., jump into the first common error immediately).
   - Section «Підсумок та діалоги» (line 268): Replace «Мова найкраще засвоюється через історії та живе спілкування.» with dialogue framing.

4. **Convert morning routine monologue to dialogue** (section «Підсумок та діалоги», line 273): Rewrite as a 2-person dialogue with at least 6-8 turns. Add 2-3 more mini-dialogues (metro scene, building entrance) to reach the richness target of 4 dialogues.

5. **Add 2 [!culture] callouts** (section «Культурний контекст»): Tag the Threshold subsection (~line 157) and the Metro Navigation subsection (~line 170) with [!culture] callouts to reach the 3/3 richness target.

### Priority 3 — Low Fixes

6. **Fix «їжджати» reference at line 111** (section «Презентація: В- та Ви-»): Clarify that the stem changes from їздити to -їжджати when a prefix is attached, rather than calling «їжджати» a "base."

7. **Add warmth markers** throughout: Insert 2-3 encouragement phrases (after «Вступ» conjugation review, after first practice drill in «Практика та помилки»). Add 1 "don't worry" moment in the aspect subsection. Rewrite closing (line 306) as a proper "You can now..." celebration with specific skills listed.

## Verdict

**NEEDS_REVISION** — 1 critical factual error (false euphony claim), systematic formatting bugs (double periods), structural LLM fingerprints, and richness gaps (dialogues 0/4, cultural callouts 1/3) require targeted fixes before this module can pass.