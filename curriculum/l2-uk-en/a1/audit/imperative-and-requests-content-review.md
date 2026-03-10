# Content Review: imperative-and-requests

**Track:** a1 | **Sequence:** 47
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 1716, target: 1200)
**Verdict:** C

---

## Plan Adherence

| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Form imperatives from the 8 required verbs | YES | Вісім обов'язкових дієслів | All 8 verbs with ти/ви forms |
| Distinguish ти and ви imperative forms | YES | Наказовий спосіб + Практика | Clearly explained and drilled |
| Make polite requests using будь ласка and прошу | PARTIAL | Ввічливе прохання | **будь ласка** thoroughly covered. **прошу вас + infinitive** MISSING entirely. Plan says: "Прошу вас сісти (Please sit down). More formal than будь ласка." |
| Understand simple prohibitions | PARTIAL | Заборони | не + imperative covered, but personal vs public sign distinction MISSING |

### Missing Plan Points (CRITICAL/HIGH)

| Plan Point | Covered? | Severity |
|------------|----------|----------|
| "Прошу вас + infinitive" pattern | NO | **HIGH** — plan objective explicitly requires this |
| "Чи не могли б ви...?" indirect request preview | NO | **HIGH** — plan says "Preview of conditional mood" |
| Personal prohibition vs public sign prohibition (план: "Не чіпай!" vs "Не торкатися!") | NO | **MEDIUM** — plan explicitly contrasts personal vs sign register |
| Classroom commands context ("Пишіть у зошиті", "Слухайте уважно", "Дивіться на дошку") | NO | **MEDIUM** — plan gives specific classroom phrases; content uses only generic "тут/там/це" |
| Politeness escalation practice (Дай → Дайте, будь ласка → Чи не могли б ви дати?) | NO | **MEDIUM** — plan's Практика section requires escalation drill |

### Vocabulary Coverage

| Required Word | In Prose? | In Vocab YAML? | In Activities? |
|--------------|-----------|----------------|----------------|
| читати/читай | YES | YES | YES |
| писати/пиши | YES | YES | YES |
| сказати/скажи | YES | YES | YES |
| дати/дай | YES | YES | YES |
| іти/іди | YES | YES | YES |
| слухати/слухай | YES | YES | YES |
| дивитися/дивись | YES | YES | YES |
| стояти/стій | YES | YES | YES |

| Recommended Word | In Prose? | In Vocab YAML? | In Activities? |
|-----------------|-----------|----------------|----------------|
| показати/покажи | YES | YES | YES |
| допомогти/допоможи | YES | YES | YES |
| взяти/візьми | YES | YES | YES |
| чекати/чекай | YES | YES | YES |

All required and recommended vocabulary present. Good coverage.

---

## Linguistic Accuracy

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| Imperfective negative imperatives unexplained | MEDIUM | Заборони, lines 174-179 | Content shows `Не кажи́` (казати, impf) alongside `Скажи́!` (сказати, pf) and `Не бери́` (брати, impf) alongside `Візьми́!` (взяти, pf) without explaining the aspect switch. All forms are correct per VESUM but the learner has no idea why the verb changed. |
| "и" (Russian conjunction) reported by screen-result | RESOLVED | Activities | screen-result.json reports `и` as VESUM not-found, but current activities YAML does not contain it — fixed in a later validation pass. |
| "взяйте" / "стояй" in activities | N/A | Activities true-false | Used as FALSE statements with correct explanations. Pedagogically appropriate — tests learner recognition of wrong forms. |

### Stress Marks

Stress marks consistently applied throughout. Spot-checked:
- чита́й, слу́хай, чека́й (vowel stems)
- пиши́, іди́, скажи́ (consonant stems)
- пиші́ть, іді́ть, скажі́ть (formal forms)
- бу́дь ла́ска (both words stressed)

All correct.

### Russianisms

No Russianisms detected. The imperfective forms `кажи`/`бери`/`давай` in negative imperatives are correct Ukrainian aspect usage (confirmed via VESUM: кажи → казати, беріть → брати, давай → давати).

---

## Pedagogical Quality

**Lesson Quality Score:** 6/10

### Tier 1 "Would I Continue?" Test

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | PASS | Pacing is manageable, concepts introduced gradually |
| Were instructions clear? | PASS | Formation rules are clearly stated |
| Did I get quick wins? | FAIL | No practice until section 5. Sections 1-4 are all exposition with blockquote examples. |
| Was Ukrainian scary? | PASS | All Ukrainian has English translation |
| Would I come back tomorrow? | FAIL | Content is repetitive — same verbs with тут/там/це over and over. Feels like a drill, not a lesson. |

**Score: 3/5 Pass → Lesson Quality 8/10 by rubric, adjusted to 6/10 for content flatness.**

### Lesson Arc Analysis

| Element | Present? | Quality |
|---------|----------|---------|
| WELCOME | PARTIAL | "Чому це важливо?" box exists but generic |
| PREVIEW | NO | No "Today you'll learn to..." |
| PRESENT | YES | Clear rule presentation with examples |
| PRACTICE | WEAK | Section 5 "Практика" is just more blockquote examples, not interactive |
| CELEBRATE | WEAK | Підсумок is minimal — 4 Q&A lines, no "You can now..." |

### Emotional Safety Mapping

| Required Moment | Present? | Evidence |
|----------------|----------|---------|
| Welcome/orientation | PARTIAL | "Чому це важливо?" callout |
| Curiosity trigger | NO | — |
| Quick wins (≥2) | NO | No mini-exercises or "try this now" |
| Encouragement (≥1) | PARTIAL | [!tip] box gives advice, not encouragement |
| Progress marker (≥1) | NO | Підсумок doesn't celebrate progress |

### Critical Pedagogical Issues

1. **Pedagogically flat (MEDIUM)**: Entire module is blockquote examples. No dialogues with context, no scenarios. Plan specifies "Classroom commands context" with "Пишіть у зошиті", "Слухайте уважно" — content uses only generic тут/там/це combinations.

2. **No practice until end (MEDIUM)**: 4 exposition sections before any practice. Practice section is itself just more blockquotes.

3. **Aspect switching unexplained (MEDIUM)**: Заборони shows `Не кажи` (impf) alongside `Скажи!` (pf) without any explanation. A1 learner will see completely different verbs for what seems like the same meaning.

4. **Missing "прошу вас" pattern (HIGH)**: Plan objective 3 requires this. Completely absent from content and activities.

---

## Activities Quality

| Activity | Type | Issues |
|----------|------|--------|
| 1. Match infinitive to imperative | match-up (12 pairs) | Clean. All forms VESUM-verified. |
| 2. Choose correct imperative in context | quiz (10 items) | Good. Plausible distractors (infinitive, indicative). |
| 3. Complete dialogue with imperative | fill-in (8 items) | Good. Tests production in context. |
| 4. Evaluate imperative usage | true-false (8 items) | Good. Includes irregular form traps. |
| 5. Sort ти/ви commands | group-sort (10 items) | Good variety. |
| 6. Unjumble polite requests | unjumble (8 items) | **Missing commas** — see below. |
| 7. Match command to English | match-up (8 pairs) | Simple but appropriate for A1. |
| 8. True/False: verb stem rules | true-false (8 items) | Good rule application testing. |

### Activity Issues

| Issue | Severity | Activity | Details |
|-------|----------|----------|---------|
| Missing commas in unjumble answers | HIGH | Activity 6 (all 8 items) | "Скажіть будь ласка" should be "Скажіть, будь ласка". Teaches incorrect punctuation. |
| No activity tests "прошу вас" | HIGH | All | Plan objective requires this pattern, zero activities test it. |
| Activity type variety | — | — | 6 unique types across 8 activities. Exceeds threshold. |
| Correct answers verified | — | — | All correct answers confirmed via VESUM. |

---

## Engagement

| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 3 | 3 | PASS ([!warning], [!tip], [!culture]) |
| Tables | 0 | — | FAIL — grammar rules in prose only |
| Dialogues | 0 | — | FAIL — blockquotes but no multi-turn dialogues |
| Real-world scenarios | 0 | — | FAIL — all examples use generic тут/там/це |
| Richness score | 49/95 | 70 | FAIL — well below A1 minimum |

---

## LLM Fingerprint

| Pattern | Found? | Location |
|---------|--------|----------|
| "In this lesson, we will explore..." | NO | — |
| Generic AI opening | NO | Opening is direct |
| Repetitive transitions | YES | "Here are..." pattern appears 3 times |
| Word salad | NO | Clean Ukrainian/English separation |

Low fingerprint. Content reads as functional textbook, not AI-generated fluff.

---

## Issues Found

### CRITICAL (blocks deployment)

None.

### HIGH (should fix before deployment)

1. **Missing "прошу вас + infinitive" pattern** — Plan objective 3 explicitly requires this. Section "Ввічливе прохання" should include "Прошу вас сісти" and similar examples. Zero activities test this.
2. **Missing "Чи не могли б ви...?" preview** — Plan explicitly says this is "Most polite option available at A1" and the practice section should include politeness escalation.
3. **Missing commas in unjumble activity answers** — All 8 items in activity 6 omit the comma before "будь ласка" ("Скажіть будь ласка" → "Скажіть, будь ласка"). Teaches incorrect punctuation.

### MEDIUM (fix if possible)

1. **No tables for grammar** — Formation rules (vowel stem → -й, consonant stem → -и) in prose only. A table would aid comprehension.
2. **No classroom context** — Plan specifies "Читайте текст", "Пишіть у зошиті", "Слухайте уважно", "Дивіться на дошку". Content uses only generic тут/там/це.
3. **Personal vs public prohibition missing** — Plan contrasts "Не чіпай!" (personal) vs "Не торкатися!" (sign/infinitive).
4. **Aspect switching unexplained** — Content shows `Скажи!` but `Не кажи!` without noting the verb change.
5. **Richness score 49/95** — Far below A1 minimum of 70.
6. **No quick wins or progress markers** — Tier 1 requires ≥2 quick wins and ≥1 progress marker.

### LOW (informational)

1. **Repetitive blockquote format** — Every section: prose sentence → 8-15 blockquote examples. Monotonous.
2. **No warm opening** — No "Привіт!" or similar. Tier 1 rubric flags cold starts.
3. **Підсумок is minimal** — No "You can now..." celebration.

---

## Grade Justification

**Grade C.** The module passes all pipeline audit gates and contains no Russianisms or critical linguistic errors. All 8 required verbs are correctly presented with accurate imperative forms (VESUM-verified). However, three HIGH issues prevent a higher grade: (1) the plan explicitly requires "прошу вас" and "Чи не могли б ви...?" patterns which are completely absent, (2) unjumble activities teach incorrect punctuation by omitting commas. The content is pedagogically flat — blockquote drills without dialogues, scenarios, or the classroom context the plan specifies. Richness score (49/95) is well below A1 minimum (70). A targeted rebuild addressing the HIGH issues and adding varied content formats would raise this to a B.

---

*Reviewed by Claude Opus 4.6 | Content Review #730 | 2026-03-10*
