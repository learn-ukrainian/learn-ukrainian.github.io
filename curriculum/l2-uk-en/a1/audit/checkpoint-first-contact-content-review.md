# Content Review: checkpoint-first-contact

**Track:** a1 | **Sequence:** 7
**Mode:** core
**Tier:** 1-beginner
**Pipeline:** PASS (words: 1400, target: 1200) | Engagement gate: FAIL (0/1)
**Verdict:** B

## Plan Adherence

| Objective | Covered? | Section | Notes |
|-----------|----------|---------|-------|
| Demonstrate ability to read Ukrainian Cyrillic fluently | YES | Читання | Reading passage with aloud instructions |
| Hold a complete first conversation (greet → introduce → family) | YES | Діалог | Full-cycle dialogue Богдан↔Соломія |
| Self-assess knowledge of sounds, letters, greetings, introductions | YES | Що ми знаємо? | Bullet-point self-check covering M01–M06 |
| Combine all A1.1 skills in connected speech | YES | Діалог → Graduation Monologue | Monologue template ties everything together |

### Content Outline Adherence

| Plan Section | Content Section | Points Covered? | Notes |
|---|---|---|---|
| Що ми знаємо? (200w) | ✅ Present | YES — all self-check points (M01–M06) | Good |
| Читання (250w) | ✅ Present | YES — short text, aloud instructions, comprehension Qs | Follows Anna Ep10 review pattern |
| Граматика (200w) | ✅ Present | YES — all 6 patterns listed | Clean table-like presentation |
| Діалог (400w) | ✅ Present | YES — full cycle + graduation monologue | Setting differs from plan (see LOW #1) |
| Підсумок (150w) | ✅ Present | YES — final self-check, encouragement, preview of next | Good |

### Vocabulary Coverage

Plan says "All vocabulary from M01-M06 is recycled — no new required words." Recommended words:

| Recommended Word | In Prose? | In Vocab YAML? | In Activities? |
|---|---|---|---|
| ім'я | YES (§5 Grammar, §Summary) | YES (ім'я́) | YES (quiz-comprehensive-review) |
| прізвище | NO | YES (прі́звище) | NO — only in workbook match-up |

**Note:** прізвище appears in vocabulary YAML and workbook but not in the lesson prose. LOW — it's only a recommended word.

## Linguistic Accuracy

| Issue | Severity | Location | Details |
|-------|----------|----------|---------|
| Quiz conflates vowel sounds and vowel letters | **HIGH** | activities/quiz-sounds-vs-letters Q4 | Question asks "How many basic vowel **letters** does Ukrainian have?" → answer "6". WRONG. Ukrainian has 6 vowel **sounds** ([а],[о],[у],[е],[и],[і]) but 10 vowel **letters** (а,о,у,е,и,і,я,ю,є,ї). Textbooks (Большакова Gr2 p.34, Вашуленко Gr2 p.4) explicitly teach this distinction: "шість голосних звуків" + "десятьма буквами". Fix: change question to "How many basic vowel **sounds** does Ukrainian have?" |
| No Russianisms detected | — | Full scan | All Ukrainian text verified via VESUM. No ghost words. |
| Vocative forms correct | — | Діалог | Богдане (v_kly ✅), Соломіє (v_kly ✅) — verified against VESUM |
| Case forms correct | — | Throughout | Тернополя (gen of Тернопіль ✅), Дніпра (gen of Дніпро ✅), сестру (acc ✅), родину (acc ✅) |
| Content correctly says "Six vowel sounds" | — | Підсумок | "Six vowel sounds: а, е, и, і, о, у" — correct terminology in prose, contradicted by quiz |

## Pedagogical Quality

**Lesson Quality Score:** 9/10

### "Would I Continue?" Test (Tier 1)

| Question | Result | Notes |
|----------|--------|-------|
| Did I feel overwhelmed? | PASS | Comfortable pacing, review only — no new material |
| Were instructions clear? | PASS | Every task clearly explained |
| Did I get quick wins? | PASS | Self-check bullets are immediate confidence builders |
| Was Ukrainian scary? | PASS | Always paired with English, read-aloud supported |
| Would I come back tomorrow? | PASS | Encouraging close, clear preview of A1.2 |

**5/5 Pass → Lesson Quality 10/10** on the rubric, but docked 1 point for missing engagement callout boxes (no `[!tip]`, `[!cultural]`, `[!warning]` etc.) which makes the module feel slightly flat visually.

### Lesson Arc

```
WELCOME ✅ (warm self-check opening)
→ PREVIEW ⚠️ (implicit — no explicit "Today you'll..." but the self-check functions as preview)
→ PRESENT ✅ (reading passage + grammar summary)
→ PRACTICE ✅ (comprehension questions + activities)
→ CELEBRATE ✅ ("Graduation Monologue" + "A1.1 is complete" + "Цей монолог — твій підпис")
```

### Emotional Safety Mapping

| Beat | Present? | Location |
|------|----------|----------|
| Welcome/orientation | ✅ | "This module is not a test. It is a mirror." |
| Curiosity trigger | ✅ | "ти вже знаєш більше, ніж думаєш" |
| Quick wins (≥2) | ✅ | Self-check bullets, reading passage (all known words) |
| Encouragement (≥1) | ✅ | "if one or two feel shaky, that is perfectly normal" / "Навіть якщо ти читаєш повільно — це нормально" |
| Progress marker (≥1) | ✅ | "A1.1 is essentially complete" / "Цей монолог — твій підпис" |

### Pacing

| Metric | Status | Notes |
|--------|--------|-------|
| New words per section | ✅ | Zero new words — review only |
| Concepts before practice | ✅ | Grammar summary after reading practice |
| English support | ✅ | Present throughout, scaffolded |
| Visual aids | ⚠️ | Grammar uses numbered list, not table — functional but could be better |

## Activities Quality

| Activity | Type | Items | Issues |
|----------|------|-------|--------|
| quiz-comprehensive-review | quiz | 12 | ✅ All answers verified correct. Tests language patterns, not content recall. |
| quiz-sounds-vs-letters | quiz | 8 | ⚠️ Q4 factual error (vowel letters vs sounds). Also: no INJECT tag in content — won't render inline. |
| fill-in-self-intro | fill-in | 8 | ✅ All answers correct. Distractors plausible. Tests grammar patterns. |
| match-questions-answers | match-up | 8 | ✅ All pairs correct. Good Q→A mapping. |
| workbook: match-up | match-up | 8 | ✅ Word↔translation pairs correct. |
| workbook: group-sort (family/professions) | group-sort | 12 | ✅ Categorization correct. |
| workbook: true-false | true-false | 8 | ✅ All statements and explanations accurate. |
| workbook: group-sort (мій/моя) | group-sort | 12 | ✅ Gender assignments correct. |

**Activity variety:** quiz (2), fill-in (1), match-up (2), group-sort (2), true-false (1) — 5 types. ✅ Good variety.

**Schema compliance:** All activities follow correct YAML schema. `inline:` and `workbook:` sections properly separated.

## Engagement

| Metric | Count | Minimum | Status |
|--------|-------|---------|--------|
| Callout boxes (`[!tip]`, `[!cultural]`, etc.) | 0 | 3 | **FAIL** |
| Tables | 0 | — | Grammar uses numbered list instead |
| Videos embedded | 0 | — | N/A (plan doesn't reference videos) |
| Blockquotes (content) | 3 | — | Reading passage, dialogue, monologue template |

## Issues Found

### CRITICAL (blocks deployment)

None.

### HIGH (should fix before deployment)

1. **Quiz vowel letters vs sounds confusion** — `quiz-sounds-vs-letters` Q4 asks "How many basic vowel **letters** does Ukrainian have?" with answer "6". Ukrainian has 6 vowel **sounds** but 10 vowel **letters** (а, о, у, е, и, і, я, ю, є, ї). This is confirmed by Большакова Grade 2 p.34: "В українській мові є шість голосних звуків. Ти можеш позначити їх на письмі десятьма буквами." **Fix:** Change the question to "How many basic vowel **sounds** does Ukrainian have?" or change answer to "10" and update wording to "vowel letters."

### MEDIUM (fix if possible)

1. **No engagement callout boxes** — Zero `[!tip]`, `[!cultural]`, `[!myth-buster]`, `[!warning]` boxes found. Minimum for A1 is 3. The audit confirms this failure (engagement: 0/1). **Fix:** Add at least 3 callout boxes — e.g., a `[!tip]` about reading aloud strategy, a `[!cultural]` about Ukrainian naming conventions, a `[!myth-buster]` about the zero-copula pattern.

2. **Inline activity `quiz-sounds-vs-letters` not injected** — The activity exists in the YAML `inline:` section but has no corresponding `<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->` tag in the content markdown. It will not render in the lesson. **Fix:** Add an inject tag in the Підсумок section (where the alphabet review questions naturally belong) or merge its best items into `quiz-comprehensive-review`.

3. **Research gate warns about unaddressed learner errors** — Audit flags that research identified 3+ common learner errors but the content doesn't explicitly address them. **Fix:** Review research file and integrate common mistake warnings into the grammar summary or as `[!warning]` callout boxes.

### LOW (informational)

1. **Dialogue setting differs from plan** — Plan specifies "Conference coffee break — two professionals meet between sessions" but content uses "university gathering in Lviv" with two students. The content version is actually more appropriate for A1 vocabulary (студент/студентка vs. professional titles). No fix needed unless plan is canonical.

2. **No explicit learning preview** — Tier-1 rubric expects a "Today you'll learn to..." statement. The self-check opening functions as an implicit preview but doesn't explicitly list learning goals. Minor.

3. **Metalanguage term "рід" used without vocabulary entry** — Last sentence mentions "Речі мають рід" (Things Have Gender) as a preview of A1.2. The term "рід" (gender) is not in this module's vocabulary. Acceptable as a teaser, but could confuse learners who click ahead.

4. **Recommended word "прізвище" missing from prose** — Present in vocabulary YAML and workbook match-up, but never used in the lesson text. Only a recommended word, so not blocking.

## Grade Justification

**Grade: B** — This is a warm, well-structured checkpoint module with strong pedagogical arc, correct Ukrainian throughout (vocatives, cases, all VESUM-verified), natural dialogue, and excellent "graduation monologue" produce activity. The HIGH issue (vowel sounds vs letters confusion in the quiz) is a factual error that must be fixed — it directly contradicts what Ukrainian Grade 1-2 textbooks teach. The missing engagement callout boxes are the only audit-blocking issue. Both are straightforward fixes. After addressing the HIGH and the engagement gate, this module is deployment-ready.
