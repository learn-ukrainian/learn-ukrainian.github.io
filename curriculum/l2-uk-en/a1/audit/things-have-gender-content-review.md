# Content Review: things-have-gender

**Track:** a1 | **Sequence:** 8
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** (manual review — word count not injected)
**Verdict:** C

## Plan Adherence

| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Determine noun gender using він/вона/воно test | YES | Він, вона, воно (The Gender Test) | Clear step-by-step explanation |
| Recognize gender by word endings (consonant=m, -а/-я=f, -о/-е=n) | YES | Він, вона, воно (The Gender Test) | Matches Vashulenko p.112 |
| Name 20+ common objects with correct gender | YES | Предмети навколо | 17 nouns explicitly listed + extras in dialogues |
| Use У мене є with objects (extending from M06) | YES | Dialogues + Предмети навколо | Good M06 callback |

### Vocabulary Coverage

| Required Word | In Prose? | In Vocab YAML? | In Activities? | Notes |
|--------------|-----------|----------------|----------------|-------|
| стіл | YES | YES | YES | ✅ |
| книга | YES (книга) | NO (книжка instead) | NO (книжка instead) | ⚠️ Mismatch — see HIGH #1 |
| вікно | YES | YES | YES | ✅ |
| кімната | YES | YES | YES | ✅ |
| ліжко | YES | YES | YES | ✅ |
| стілець | YES | YES | YES | ✅ |
| лампа | YES | YES | YES | ✅ |
| телефон | YES | YES | YES | ✅ |
| комп'ютер | YES | YES | YES | ✅ |
| він, вона, воно | YES | PARTIAL — він missing | YES | ⚠️ він absent from vocab YAML |

### Content Outline Adherence

| Plan Section | Content Section | Match? | Notes |
|-------------|----------------|--------|-------|
| Діалоги (Dialogues) | Діалоги (Dialogues) | PARTIAL | ⚠️ Plan specifies pet shop setting; content uses room/bag setting |
| Він, вона, воно (The Gender Test) | Він, вона, воно (The Gender Test) | YES | Accurate textbook references |
| Предмети навколо (Objects Around Us) | Предмети навколо (Objects Around Us) | YES | Good gender-organized vocabulary |
| Підсумок — Summary | Підсумок — Summary | YES | Functional but lacks warmth |

### Dialogue Situation Deviation (HIGH)

The plan specifies: *"At a pet shop — looking at animals and their accessories. A кіт (m) sleeps in a кошик (m, basket), a рибка (f) swims in an акваріум (m), a черепаха (f, turtle) sits near a дзеркало (n, mirror)."*

The built content uses: *Video call showing a room (кімната, стіл, ліжко) + What's in your bag (книга, телефон, фото).*

None of the planned animal vocabulary (кіт, рибка, черепаха, кошеня, акваріум, кошик) appears. The room setting works pedagogically, but this is a significant plan deviation.

## Linguistic Accuracy

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| книга/книжка inconsistency | HIGH | Prose vs activities/vocab | Prose uses "книга" throughout; activities and vocabulary YAML use "книжка". These are different words. Learner sees one in the lesson, another in exercises. |
| він missing from vocab YAML | MEDIUM | vocabulary/things-have-gender.yaml | Plan requires він, вона, воно. Vocab has вона́ and воно́ but not він. |
| вона POS incorrect | LOW | vocabulary YAML line 108 | `pos: ім.` — вона is a pronoun (займ.), not a noun (ім.) |
| воно POS incorrect | LOW | vocabulary YAML line 114 | `pos: ім.` — воно is a pronoun (займ.), not a noun (ім.) |

**VESUM verification:** All 26 Ukrainian words checked — 26/26 FOUND ✅
**Russianisms scan:** None detected ✅
**Calque check (Антоненко-Давидович):** дерев'яний, зручний — no issues ✅
**Ghost words:** None ✅
**Grammar correctness:** Case endings, gender agreement all correct. "Моє крісло ду́же зру́чне!" — neuter agreement ✅. "Мій зо́шит нови́й" — masculine agreement ✅.

## Pedagogical Quality

**Lesson Quality Score:** 6/10

### Tier-1 "Would I Continue?" Test

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | PASS | Pacing is comfortable, concepts introduced gradually |
| Were instructions clear? | PASS | Gender test is clearly explained step-by-step |
| Did I get quick wins? | BORDERLINE | Activities provide practice, but no explicit celebration |
| Was Ukrainian scary? | PASS | Good English scaffolding, translations provided |
| Would I come back tomorrow? | BORDERLINE | Functional but feels like a textbook, not a tutor |

**Score: 3/5 Pass → Lesson Quality 8/10 by rubric... BUT:**

### Tier-1 Emotional Safety Mapping — FAIL

| Required Moment | Present? | Notes |
|----------------|----------|-------|
| ≥1 Welcome/orientation | ❌ NO | Module jumps straight into dialogues. No "Today you'll learn..." |
| ≥1 Curiosity trigger | ✅ YES | "Did you notice?" after first dialogue |
| ≥2 Quick wins | ❌ NO | No explicit "You got this!" or celebration moments |
| ≥1 Encouragement | ❌ NO | Zero encouragement phrases in the entire module |
| ≥1 Progress marker | ❌ NO | Summary is functional but no "Look how far you've come" |

**1/5 emotional beats present → COLD_PEDAGOGY**

The tier-1 rubric states: *"<3 markers → COLD_PEDAGOGY → Auto-fail"*. This drops Lesson Quality to **6/10**.

### Lesson Arc (Beginner)

| Element | Present? | Notes |
|---------|----------|-------|
| WELCOME | ❌ | No warm greeting, no context setting |
| PREVIEW | ❌ | No "Today you'll learn..." |
| PRESENT | ✅ | Clear grammar explanation with examples |
| PRACTICE | ✅ | Good inline activities |
| CELEBRATE | ❌ | Summary is dry, no encouragement |

### Specific Pedagogical Notes

**Strengths:**
- Gender test explanation follows exactly how Vashulenko (p.110) and Ponomarova (p.86) teach it — він/мій, вона/моя, воно/моє. Textbook-grounded pedagogy ✅
- Good use of "Did you notice?" after dialogues — examples before rules ✅
- М06 callback ("У мене є") creates curriculum continuity ✅
- Vocabulary organized by gender with example sentences — clear visual pattern

**Weaknesses:**
- Module reads like a reference page, not a guided lesson
- No direct address to the learner beyond the summary self-check
- Summary self-check is good but buried at the end — needs earlier quick wins

## Activities Quality

| Activity | Type | Items | Issues |
|----------|------|-------|--------|
| quiz-vin-vona-vono | quiz | 8 | ✅ Good. Uses книжка (see consistency issue) |
| group-sort-gender | group-sort | 17 (3 groups) | ✅ Good. Comprehensive sort. Uses книжка. |
| fill-in-possessive | fill-in | 8 | ✅ Well-designed. Tests мій/моя/моє. Uses книжка. |
| quiz-gender-by-ending | quiz | 6 | ✅ Good. Tests ending-based recognition. |
| match-up (workbook) | match-up | 9 | ✅ Clean noun→pronoun matching. |
| true-false (workbook) | true-false | 8 | ✅ Good explanations. Uses книжка. |
| error-correction (workbook) | error-correction | 7 | ✅ Excellent — tests active gender agreement. Uses книжка. |
| translate (workbook) | translate | 6 | ✅ Well-formed. Uses книжка. |
| observe (workbook) | observe | 12 examples | ✅ Good pattern-observation. Uses книжка. |

**Activity variety:** 8 different types — EXCELLENT ✅
**Language testing vs content testing:** All activities test language skills (gender recognition, possessive agreement) — PASS ✅
**Correct answers verified:** All correct ✅
**Distractors:** Plausible (мій/моя/моє always the three options) ✅

**Note:** Activities consistently use **книжка** while prose uses **книга**. Every single activity with "book" uses книжка. This reinforces the inconsistency issue.

## Engagement

| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes | 0 | 3+ | ❌ FAIL |
| Tables | 1 | — | OK (summary table) |
| Inline activities | 4 | — | Good |
| Videos embedded | 0 | 0 | N/A (none in plan) |

**Zero callout boxes.** No `> [!tip]`, `> [!cultural]`, `> [!myth-buster]`, `> [!warning]` anywhere. This is a significant engagement gap for an A1 module. Opportunities:
- `> [!tip]` for the ending shortcut (consonant=m, -а=f, -о=n)
- `> [!cultural]` for how Ukrainian children learn gender in Grade 3
- `> [!tip]` for "фото never changes its ending"
- `> [!warning]` for exceptions (soft-sign nouns come later)

## Issues Found

### CRITICAL (blocks deployment)

None.

### HIGH (should fix before deployment)

1. **книга/книжка inconsistency** — Prose uses **книга** (6 occurrences); activities YAML and vocabulary YAML use **книжка** (12+ occurrences). The plan's required vocabulary says "книга (book, f)". Decision needed: either update prose to книжка everywhere, or update activities/vocab to книга. Both are valid Ukrainian words (книга is more formal/standard, книжка is colloquial/diminutive). For A1 consistency, pick one and use it everywhere. Recommend **книжка** since it better demonstrates the -а ending pattern (книжк**а**) and is already in 9 activity files.
2. **Dialogue setting deviates from plan** — Plan specifies pet shop (кіт, рибка, черепаха, кошеня, акваріум). Built content uses room/bag. This requires either (a) rebuilding dialogues to match the plan, or (b) a plan version bump to ratify the room setting. Per non-negotiable rule 7: *"When build can't meet plan → STOP → report → propose new plan version."*
3. **COLD_PEDAGOGY — zero warmth** — Module has 1/5 required emotional beats. No welcome, no encouragement, no celebration. Tier-1 rubric says <3 markers = auto-concern. The module needs: (a) a welcome paragraph before the dialogues, (b) 2-3 encouragement callouts between sections, (c) a "You can now..." celebration in the summary.

### MEDIUM (fix if possible)

1. **він missing from vocabulary YAML** — Plan requires він, вона, воно as a unit. Only вона and воно are in the vocabulary YAML.
2. **Zero callout boxes** — Minimum 3+ for A1. Add tip/cultural/warning boxes at natural breakpoints.
3. **No preview/orientation** — First sentence dives into content. Add 2-3 sentences: "Every Ukrainian noun has a gender — like a family it belongs to. Today you'll learn to spot which family any noun is in, using two simple tests."

### LOW (informational)

1. **POS tags wrong for вона/воно in vocab YAML** — Tagged as `ім.` (noun) instead of `займ.` (pronoun).
2. **дзеркало is A2 per PULS** — Used in an A1 module. Acceptable as a concrete household noun, but worth noting.
3. **місто mentioned in plan (Vashulenko endings list) but absent from content** — Not required vocab, minor omission.

## Grade Justification

**Grade: C** — The module is linguistically accurate, pedagogically grounded in real textbook methodology (Vashulenko p.110-112, Ponomarova p.86), and has excellent activity variety (8 types). However, three issues prevent a higher grade: (1) the книга/книжка split between prose and activities creates a confusing learner experience, (2) the dialogue setting completely deviates from the plan without a version bump, and (3) the module reads like a cold reference page rather than a warm A1 lesson — zero callout boxes, zero encouragement markers, no welcome or celebration. The content is *correct* but not *inviting*. For a beginner module, warmth is not optional.

---

*Reviewed by Claude · Reference: #730 · Date: 2026-04-01*
