**Reviewed-By:** claude-opus-4-6

---

# Phase D.1 Review: Around the City (a1-15)

**Module**: a1-15 `around-the-city`
**Level**: A1.2 [Navigation]
**Persona**: Patient Supportive Tutor, acting as Taxi Driver
**Word count**: 2616 / 2000 (130.8%)
**Activities**: 10 | **Vocabulary**: 23 | **Engagement boxes**: 7

---

## Scores

| # | Dimension | Score | Notes |
|---|-----------|-------|-------|
| 1 | Lesson Quality | 7/10 | Informative but emotionally flat; reads as textbook not tutor |
| 2 | Language Quality | 8/10 | Ukrainian grammar correct, clear English; minor heading inconsistency |
| 3 | Immersion | 7/10 | 25.3% — at floor of audit target (25-40%), far below tier rubric A1.2 target (40-60%) |
| 4 | Activity Quality | 6/10 | 4 vocabulary items tested but never taught in content = testing before teaching |
| 5 | Richness | 8/10 | Good callout variety, strong cultural content; could use more visual aids |
| 6 | LLM Fingerprint | 8/10 | No AI clichés; one English-only heading; section intros somewhat repetitive |
| 7 | Factual Accuracy | 9/10 | Grammar rules accurate; Maidan etymology correct; no fabrications found |
| 8 | Humanity & Warmth | 6/10 | Zero encouragement phrases, no warm greeting, no "don't worry" moments — COLD_PEDAGOGY threshold |

---

## Critical Issues Found

### Issue 1: Testing Before Teaching — 4 Vocabulary Items in Activities but Absent from Content [CRITICAL]

The following words appear in activities (and in some cases the vocabulary file) but are **never introduced, explained, or even mentioned** in the content prose:

**a) "назад" (back)** — Vocabulary file line 81-84, activities lines 108, 134, 324. Used in match-up (line 108: `left: "назад"` / `right: "back"`), group-sort (line 134), and fill-in (line 324: `"_____ назад. Ми пропустили зупинку."`). Content file: zero occurrences. An A1 learner encounters this in 3 separate exercises with no reference point.

**b) "світлофор" (traffic light)** — Vocabulary file line 85-88, activity fill-in line 292: `"_____ направо на світлофорі."`. Content file: zero occurrences. The word never appears in the lesson text.

**c) "додому" (homeward/home)** — Activity group-sort line 130, fill-in line 308: `"Ми _____ додому."`. Content file: zero occurrences. Not in vocabulary file either — completely untaught and un-listed.

**d) "будинок" (building/house)** — Activity quiz line 411-421: `"Моя червона машина стоїть біля..."` with answer `"будинку"`. Content file: zero occurrences. Not in vocabulary file. A quiz item on Genitive case with a noun the learner has never seen.

**Why this is critical**: At A1, testing before teaching is a **red flag** per the tier rubric. A nervous beginner encountering unknown vocabulary in exercises has no way to succeed, violating the "quick wins" principle.

**Fix**: Either (a) add brief introductions of these words to the content in section «Лексика: Напрямки та місця» or section «Практика: Маршрути та діалоги», or (b) remove activities that use untaught vocabulary and replace with items using vocabulary from the lesson.

### Issue 2: Warmth Deficit — Module Fails COLD_PEDAGOGY Threshold [CRITICAL]

Per tier rubric, A1 modules require: ≥3 encouragement phrases, ≥2 "don't worry" moments, ≥2 "You can now..." validation markers, and ≥15 direct address (you/ви) markers.

**Actual counts:**
- Encouragement phrases ("Great!", "Well done!", "You've got this!"): **0** in the entire module body
- "Don't worry" / reassurance moments: **0**
- "You can now..." validation: **1** (line 336: "You can now distinguish between...")
- Warm greeting at opening: **absent** — module opens with a blockquote followed by an H2 header, no "Привіт!" or "Welcome!"

The module begins at line 11 with:
> «Чому це важливо?» → "Getting lost is part of the adventure..."

This sets context but is not a warm welcome. Compare to the A+ standard: "Привіт! Today you'll learn to navigate the city like a local..."

The closing at line 336 is the only warmth moment: "Today we unlocked the city. You learned that navigating Ukraine is not just about coordinates..." — this is good but one warm paragraph in 2600 words is insufficient.

**Fix**: Add warm greeting at module start, insert 3-4 encouragement phrases after practice sections (e.g., after the direction phrases at line 225, after the dialogue at line 259), add 1-2 "don't worry" reassurances (e.g., after the grammar-heavy section «Граматика: Прийменники та рух» around line 168).

### Issue 3: Activity Title Mismatch — "Місця та дії" [MAJOR]

Activity 7 (activities file line 252) is titled «Місця та дії» (Places and **Actions**) but the pairs match places to **objects**, not actions:
- `аптека` → `ліки` (medicine — a thing, not an action)
- `пошта` → `лист` (letter — a thing)
- `парк` → `дерева` (trees — objects)
- `площа` → `центр міста` (city center — a concept)

No pair contains an actual action (verb). A more accurate title would be «Місця та їхні асоціації» (Places and Their Associations) or the pairs should be changed to include verbs (e.g., `аптека` → `купувати ліки`).

**Fix**: Rename to «Місця та асоціації» or restructure pairs to include verbs.

### Issue 4: Missing Plan Vocabulary — "перехрестя" (intersection) [MINOR]

The plan (`vocabulary_hints.recommended`) includes `перехрестя (intersection) — на перехресті (Locative)` but this word appears neither in the content nor the vocabulary file. Given it's "recommended" not "required," this is minor, but it's a missed opportunity for a navigation-focused module.

### Issue 5: English-Only H3 Heading Breaks Bilingual Convention [MINOR]

Content line 197: `### Example Scenarios` — every other H3 heading in the module follows the pattern `### Ukrainian (English)` (e.g., `### Серце міста (The Heart of the City)`, `### Де чи Куди? (Location vs. Direction)`). This lone English heading breaks consistency.

**Fix**: Rename to `### Приклади (Example Scenarios)`.

---

## Factual Verification

### Callout Box Verification

| Box | Location | Claim | Verdict |
|-----|----------|-------|---------|
| `[!warning]` | Line 34-35 | «Де ти йдеш?» is incorrect; should be «Куди ти йдеш?» for motion | **CORRECT** — standard grammar rule, де=location, куди=direction |
| `[!note]` | Line 37-38 | **Де** = dot on map, **Куди** = arrow | **CORRECT** — pedagogical analogy, not a factual claim |
| `[!tip]` | Line 74-75 | **наліво/ліворуч** interchangeable; *ліворуч* for static position, *наліво* for turning | **CORRECT** — standard Ukrainian usage distinction |
| `[!warning]` | Line 119-123 | **в** for closed buildings, **на** for open/functional spaces | **CORRECT** — standard preposition rules |
| `[!observe]` | Line 156-160 | **біля** and **навпроти** trigger Genitive: аптека→аптеки | **CORRECT** |
| `[!myth-buster]` | Line 193-195 | Locative = container, Accusative = target/arrow | **CORRECT** — pedagogical analogy |
| `[!context]` | Line 261-262 | **Вибачте** and **Перепрошую** used when approaching strangers | **CORRECT** — standard Ukrainian politeness |
| `[!culture]` | Line 329-330 | **Майдан** is of Persian origin via Turkic languages; Euromaidan 2013-2014 | **CORRECT** — the etymology is well-documented (Persian مَیدان → Turkic → Ukrainian); Euromaidan dates are accurate |

### Grammar Rule Verification

| Rule | Location | Verdict |
|------|----------|---------|
| Feminine -а → -и in Genitive (біля аптеки) | Line 136-139 | **CORRECT** |
| Feminine -я → -і in Genitive (біля площі) | Line 137 | **CORRECT** |
| Locative: вулиця→вулиці, аптека→аптеці | Line 110-118 | **CORRECT** |
| Де + Locative vs Куди + Accusative | Lines 170-195 | **CORRECT** |
| Inanimate Accusative = Nominative | Line 181 | **CORRECT** for masculine and neuter |

No factual errors found.

---

## Dimension Evidence

### Lesson Quality (7/10)

**"Would I Continue?" test:**
- Did I feel overwhelmed? **PASS** — pacing is comfortable, concepts introduced gradually
- Were instructions clear? **PARTIAL** — mostly clear, but untaught vocabulary in activities breaks trust
- Did I get quick wins? **FAIL** — no exercises appear until after all 6 H2 content sections; the first activity in the YAML comes after the entire lesson prose
- Was Ukrainian scary? **PASS** — well-scaffolded with English translations
- Would I come back tomorrow? **PARTIAL** — content is solid but tone is neutral, not encouraging

Result: 2.5/5 Pass → Lesson Quality 7/10

**Lesson Arc assessment:**
- WELCOME: Missing warm greeting (no "Привіт!", no "Welcome!")
- PREVIEW: Present but implicit. Line 13: "Today, we turn the city into your map" — functional but not explicit objectives
- PRESENT: Strong. Clear grammar tables, good examples throughout sections «Лексика: Напрямки та місця» and «Граматика: Прийменники та рух»
- PRACTICE: Good dialogue and scenario variety in «Практика: Маршрути та діалоги»
- CELEBRATE: Partial. Line 336 has a closing summary but no "celebration" feeling

### Language Quality (8/10)

Ukrainian prose is grammatically correct throughout. Sample verified sentences:
- Line 18: «Центр міста — це серце життя. Тут ми зустрічаємось, гуляємо і п'ємо каву.» — natural, correct
- Line 25: «Це два різні питання.» — correct
- Line 41: «Українці малюють картину словами.» — natural metaphor
- Line 78: «Створімо ментальну карту міста. Знайдімо найважливіші місця: аптеку, вокзал, зупинку.» — correct imperative forms, correct accusative

English is clear and B1-accessible. No colonial framing found — the two "Unlike" instances (line 22: "Unlike some grid-based American cities"; line 310: "Unlike big municipal buses") compare to American cities and bus types, not Russian.

**Deduction**: One English-only heading at line 197 breaks the bilingual convention.

### Immersion (7/10)

Audit reports 25.3% Ukrainian against a 25-40% target. This is at the absolute floor. For an A1.2 module per the tier rubric (target 40-60%), this is significantly low.

Looking at the content structure: each section opens with 1-3 short Ukrainian sentences followed by 3-10 English sentences of explanation. The Ukrainian-to-English ratio is heavily skewed. For example, section «Вступ: Місто та орієнтири» has ~40 Ukrainian words vs ~180 English words.

The module teaches A1 learners, so heavy English scaffolding is reasonable. But more Ukrainian could be integrated through inline Ukrainian phrases within the English text or through more example sentences.

### Activity Quality (6/10)

**Positive:**
- 10 activities with good type variety (quiz, match-up, group-sort, fill-in, unjumble, true-false)
- Grammar exercises (Genitive with біля/навпроти, в/на prepositions) are well-constructed
- Difficulty progression within activities is appropriate

**Critical flaw:** 4 vocabulary items tested but never taught (see Critical Issue #1). This alone drops the score significantly because at A1, encountering unknown words in exercises is discouraging and violates "teach before test."

**Additional issues:**
- Activity 7 title «Місця та дії» doesn't match content (pairs are place→object, not place→action)
- Activity 3 (group-sort) includes "додому" which is completely absent from both content and vocabulary file

### Richness (8/10)

**Strengths:**
- 7 callout boxes with no duplicate types: [!warning]×2, [!note], [!tip], [!observe], [!myth-buster], [!context], [!culture]
- Cultural content in section «Культура: Українська навігація» is engaging and authentic (marshrutka etiquette, landmark navigation, Maidan culture)
- Taxi driver roleplay in section «Творче завдання: Ваш шлях» aligns with persona
- Grammar tables at lines 110-118 and 188-191 are clear and scannable

**Weaknesses:**
- Only 2 grammar tables — more visual aids would help (e.g., a diagram for Де vs Куди, a visual comparison of Genitive endings)
- Missing "перехрестя" from plan's recommended vocabulary is a small richness gap

### LLM Fingerprint (8/10)

**Structural monotony test**: Sections 1-6 all follow the same pattern: Ukrainian H3 intro (1-3 sentences) → English explanation paragraph. This is *consistent* but 6/6 identical openings is borderline. It serves pedagogy (preview in target language) so I score leniently.

**Generic AI rhetoric**: No instances of "це не просто", "діамант", "двигун прогресу", or similar AI clichés.

**Callout monotony**: All 7 callouts use different types — good variety.

**Example plausibility**: All example sentences are natural. «Давай зустрінемось на площі» (line 20), «Банк біля аптеки» (line 143), «Вибачте, де метро?» (line 244) — all plausible everyday Ukrainian.

**One flag**: Line 197 `### Example Scenarios` heading in English only — feels like a generic AI heading inserted without the usual bilingual treatment.

### Factual Accuracy (9/10)

All grammar rules verified correct. Maidan etymology verified. Preposition usage rules accurate. No fabricated claims found in any callout box.

### Humanity & Warmth (6/10)

**Direct address count**: "you/your/ви" appears frequently in the English text — estimated ≥20 instances. ✓

**But critical markers are missing:**
- Encouragement phrases ("Great!", "Well done!", "Чудово!"): **0**
- "Don't worry" / reassurance: **0**
- "You can now..." validation: **1** (line 336 only)
- Warm greeting: **absent**
- Mid-lesson check-ins: **absent**

The module is informative and well-organized, but **emotionally flat**. A beginner reading this module feels instructed, not coached. The Ukrainian intros (e.g., line 277: «Тепер ваша черга. Розкажіть про ваш шлях до магазину або парку. Використовуйте прості речення. Ви знаєте слова. Ви знаєте граматику. Спробуйте!») come closest to encouragement, but the "Спробуйте!" (Try it!) is the only truly encouraging word in 2600 words.

With <3 warmth markers, this approaches the **COLD_PEDAGOGY** threshold for A1.

---

## Fix Plan

### Fix 1: Add Warm Opening and Encouragement Markers [Humanity]
**Location**: Content lines 9-14 (module opening), and after key practice sections
**Action**:
- Add a warm greeting before the blockquote (e.g., "Welcome back! You've already learned so much..." or begin with "Привіт!")
- Insert encouragement after the direction phrases (~line 225): "Great work! You now have the key phrases to guide anyone through a city."
- Insert reassurance after the grammar section (~line 168): "Don't worry if the Instrumental case sounds intimidating—we're only introducing it. For now, focus on **біля** and **навпроти**."
- Add a second "You can now..." marker in the closing

### Fix 2: Introduce "назад", "світлофор", "додому", "будинок" in Content [Activities]
**Location**: Section «Лексика: Напрямки та місця» (around lines 47-123)
**Action**: Add brief introductions:
- "назад" alongside прямо/наліво/направо in the "Основні напрямки" subsection (~line 49)
- "світлофор" in the "Інфраструктура міста" subsection (~line 77), perhaps after "зупинка"
- "додому" as a direction marker, perhaps after the "Куди?" concept in section «Граматика: Прийменники та рух»
- "будинок" in the infrastructure section or remove the activity item that uses it

### Fix 3: Fix Activity 7 Title [Activities]
**Location**: Activities file line 252
**Action**: Change `title: "Місця та дії"` to `title: "Місця та асоціації"` or restructure pairs to include verb phrases.

### Fix 4: Fix English-Only Heading [Language]
**Location**: Content line 197
**Action**: Change `### Example Scenarios` to `### Приклади (Example Scenarios)`

### Fix 5 (Optional): Boost Immersion [Immersion]
**Location**: Throughout English explanation paragraphs
**Action**: Increase inline Ukrainian by embedding key terms in English sentences. For example, at line 52: "To move through the city, you need a few core **слова напрямку** (direction words)." This gradually increases immersion toward the 40-60% A1.2 target.

---

## Verification Summary

| Check | Result |
|-------|--------|
| Russianisms | None found |
| Calques | None found |
| Colonial framing | None — "Unlike" references compare to American cities and bus types, not Russian |
| Grammar scope violations | None — Locative, Accusative, Genitive all within A1 scope |
| Activity errors | 4 items use untaught vocabulary |
| Factual errors | None found |
| LLM fingerprints | Borderline structural monotony in section openings; 1 English-only heading |
| COLD_PEDAGOGY | **TRIGGERED** — <3 warmth markers |
| Testing before teaching | **TRIGGERED** — назад, світлофор, додому, будинок in activities but absent from content |
| Plan compliance | Missing "перехрестя" from recommended vocabulary |

---

## Verdict

**NEEDS REVISION**

The content is pedagogically sound in its grammar explanations and cultural sections. Ukrainian language quality is correct, callout variety is good, and no factual errors were found. However, two critical issues prevent a PASS:

1. **Testing before teaching**: 4 vocabulary items appear in activities but were never introduced in the lesson. At A1, this creates confusion and discouragement.
2. **COLD_PEDAGOGY**: The module reads like a well-organized textbook, not a patient, supportive tutor. Zero encouragement phrases and no warm opening fail the A1 emotional safety requirements.

These are both fixable with targeted additions (not rewrites). The content skeleton is strong — it needs warmth injected and vocabulary gaps closed.