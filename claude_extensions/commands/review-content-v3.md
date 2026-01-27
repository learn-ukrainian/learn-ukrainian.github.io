# Review-Content-Scoring Prompt: 0-10 Quality Rubric (Post-Audit)

---

## 🎯 TOP PRIORITY: LECTURE EXPERIENCE CHECK

> **THIS IS THE MOST IMPORTANT SECTION. EVALUATE FIRST.**
>
> Before checking technical dimensions, ask: **"Would I want to attend this lecture?"**
> A module can pass all technical gates and still be a boring, forgettable experience.
> Our goal is **A+ seminar quality** — content that engages, surprises, and transforms.

---

## ⚠️ MANDATORY OUTPUT FORMAT — NO EXCEPTIONS

**READ THIS FIRST. FOLLOW EXACTLY. NO VARIATIONS.**

### File Naming (EXACT)
```
{slug}-review.md
```
Examples: `12-aspect-pairs-essential-40-review.md`, `trypillian-civilization-review.md`

**FORBIDDEN names:** `-review-v3.md`, `-content-review.md`, `-llm-review.md`, `.review.md`, `-review-claude.md`

### Save Location (EXACT)
```
curriculum/l2-uk-en/{level}/review/{slug}-review.md
```

**NEVER save to:** `audit/` folder (that's for automated audit_module.py output only)

### Header Format (COPY EXACTLY)
```markdown
# Module {NUM}: {Ukrainian Title}

**Template:** {template-name}.md | **Compliance:** ✅ PASS / ❌ FAIL
**Overall Score:** {X.X}/10
**Status:** ✅ PASS / ❌ FAIL
**Generated:** {YYYY-MM-DD HH:MM:SS}
**Reviewer:** Claude / Gemini

## Scores Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Lecture Quality** | X/10 | {note} ← TOP PRIORITY |
| Coherence | X/10 | {note} |
| Relevance | X/10 | {note} |
| Educational | X/10 | {note} |
| Language | X/10 | {note} |
| Pedagogy | X/10 | {note} |
| Immersion | X/10 | {note} |
| Activities | X/10 | {note} |
| Richness | X/10 | {note} |
| Humanity | X/10 | {note} |
| LLM Fingerprint | X/10 | {note} |
| Linguistic Accuracy | X/10 | {note} |
```

**MANDATORY elements:**
- Title MUST be `# Module {NUM}: {Ukrainian Title}` (not "Content Review", not "Review V3")
- Timestamp MUST include time: `2026-01-24 20:43:15` (not just date)
- Scores table MUST use pipe format (not bullet list)
- ALL 12 dimensions MUST be scored (**Lecture Quality** FIRST, then 11 others)

---

## 🎓 SECTION 0: LECTURE EXPERIENCE AUDIT (DO THIS FIRST)

> **CRITICAL:** This is NOT a spot-check. Read the ENTIRE module as a student would.
> Evaluate the complete lecture experience from first word to last.

### 0a. The "Would I Stay?" Test

**Read the module from start to finish.** Time yourself. Ask:

| Question | Pass | Fail |
|----------|------|------|
| Did I want to keep reading? | Genuinely curious what's next | Skimmed or got bored |
| Did I learn something surprising? | At least 2 "I didn't know that!" moments | Everything predictable |
| Could I retell this to a friend? | Clear narrative arc I remember | Jumbled facts |
| Did I feel something? | Connection, curiosity, pride, amusement | Nothing, flat |
| Would I recommend this? | "You should read this module" | "It covers the topic" |

**Scoring:**
- 5/5 Pass → Lecture Quality 10/10
- 4/5 Pass → Lecture Quality 9/10
- 3/5 Pass → Lecture Quality 8/10 (needs work)
- 2/5 Pass → Lecture Quality 7/10 (significant revision)
- 0-1/5 Pass → Lecture Quality ≤6/10 (rewrite required)

### 0b. Narrative Arc Analysis

**Every great lecture has a story structure:**

```
HOOK → TENSION → JOURNEY → CLIMAX → RESOLUTION → CALL TO ACTION
```

**Check each element:**

| Element | What to Look For | Red Flag |
|---------|------------------|----------|
| **HOOK** (first 100 words) | Grabs attention, poses question, creates stakes | Generic intro, "In this module we will..." |
| **TENSION** | Problem to solve, mystery to uncover, conflict to resolve | No driving question, just facts |
| **JOURNEY** | Progressive revelation, building complexity | Random fact dump, no progression |
| **CLIMAX** | Key insight, turning point, "aha!" moment | No peak, everything equally weighted |
| **RESOLUTION** | Answers the hook, ties threads together | Abrupt ending, unresolved questions |
| **CALL TO ACTION** | "Now you can...", "Try this...", connection to life | Generic "practice more" |

**Score:** Each element 0-2 points. Total /12 → convert to /10.

### 0c. Pacing & Breathing Room

**Dense walls of text kill lectures.** Check:

| Metric | A+ Standard | Fail |
|--------|-------------|------|
| Max paragraph length | ≤150 words | >200 words without break |
| Engagement breaks | Every 300-400 words | >500 words without callout/question/example |
| Sentence variety | Mix of 10-word and 40-word sentences | All sentences same length |
| White space | Visual rhythm on page | Intimidating text blocks |

### 0d. Emotional Journey Mapping

**Mark emotional beats through the module:**

```
😐 Neutral → 🤔 Curious → 😮 Surprised → 😊 Satisfied → 💪 Empowered
```

**Required emotional moments:**
- ≥1 **Curiosity trigger** (question, mystery, "but why?")
- ≥1 **Surprise/delight** (unexpected fact, counterintuitive insight)
- ≥1 **Pride/connection** (Ukrainian identity, cultural resonance)
- ≥1 **Empowerment** ("now you can...", practical application)

**If any category missing → Flag for enrichment**

### 0e. The "So What?" Test

**For each major section, answer: "Why should the learner care?"**

| Section | Has Clear "So What?" | Missing "So What?" |
|---------|---------------------|-------------------|
| ✅ Good | "Understanding this helps you read historical texts" | ❌ Bad: Just presents facts |
| ✅ Good | "This is why Ukrainians today still..." | ❌ Bad: "Here is information about X" |
| ✅ Good | "Without this, you'll misunderstand..." | ❌ Bad: Academic description |

**Count sections missing "so what" → >30% missing = Lecture Quality -2 points**

### 0f. Weak Moment Detection & Mandatory Rewrite

**CRITICAL: Find ALL weak moments and FIX them.**

**Weak Moment Categories:**

| Category | Pattern | Example | Required Fix |
|----------|---------|---------|--------------|
| **DEAD_INTRO** | Generic opening | "Слов'яни — це група народів..." | Replace with hook, question, or vivid scene |
| **WALL_OF_FACTS** | >3 facts without interpretation | "X happened. Then Y. Then Z." | Add "why this matters" after 2 facts |
| **FORCED_CONNECTION** | Superficial modern parallel | "This is like modern startups" | Make genuine or remove |
| **ENERGY_DROP** | Section where interest dies | Long technical explanation | Add example, break up, or cut |
| **ANTICLIMAX** | Weak ending after strong content | "In conclusion, X was important" | End with resonance, not summary |
| **ORPHAN_FACT** | Interesting fact that goes nowhere | "Interestingly, they also..." | Connect to main narrative or cut |
| **TEXTBOOK_VOICE** | Academic passive tone | "It should be noted that..." | Rewrite as direct address |
| **MISSING_STAKES** | No reason to care | "There were many tribes" | Add consequence: "Without unity, they faced..." |

**Process:**
1. Read module completely
2. Mark EVERY weak moment with category
3. Write specific rewrite for each
4. Apply fixes
5. Re-read to verify improvement

### 0g. A+ Seminar Standard Checklist

**For History/Cultural/Biography modules (CBI pedagogy):**

| Criterion | A+ Standard | B Standard | C or Below |
|-----------|-------------|------------|------------|
| **Opening** | Vivid scene, provocative question, or personal stake | Clear topic introduction | Generic "In this module..." |
| **Primary Sources** | Woven into narrative, analyzed, voices heard | Present but separate | Missing or token |
| **Narrative Thread** | Clear protagonist(s), conflict, resolution | Events in order | Random fact collection |
| **Decolonization** | Integrated perspective, not preachy | Section present | Missing or superficial |
| **Emotional Peak** | Moment of genuine impact | Some engagement | Flat throughout |
| **Modern Relevance** | Organic connection to today | Mentioned at end | Missing |
| **Closing** | Memorable, quotable, actionable | Summarizes content | Abrupt or generic |
| **Overall Experience** | "I'll remember this" | "I learned something" | "I read it" |

**Scoring:**
- 8/8 A+ → Lecture Quality 10/10
- 7/8 A+ → Lecture Quality 9/10
- 5-6/8 A+ → Lecture Quality 8/10
- 3-4/8 A+ → Lecture Quality 7/10 (needs enrichment)
- <3/8 A+ → Lecture Quality ≤6/10 (major revision)

### 0h. Lecture Quality Score (NEW DIMENSION #12)

**Add to scores table:**

```markdown
| Lecture Quality | X/10 | {note} |
```

**Rubric:**

| Score | Description | Action |
|-------|-------------|--------|
| 10 | Exceptional — memorable, engaging, would recommend | None |
| 9 | Excellent — compelling throughout, minor polish only | Light touch-ups |
| 8 | Good — solid but missing 1-2 "wow" moments | Add emotional peaks |
| 7 | Adequate — informative but forgettable | Significant enrichment needed |
| 6 | Weak — technically correct but boring | Major narrative restructure |
| ≤5 | Poor — fails as educational experience | Full rewrite |

**Weight in overall score: 1.5 (same as Linguistic Accuracy)**

---

## 🔧 LECTURE IMPROVEMENT STRATEGIES

When Lecture Quality < 9, apply these fixes:

### Strategy L1: Inject Drama

**Before (flat):**
> Антський союз існував протягом IV-VII століть.

**After (dramatic):**
> Уявіть: IV століття. Готські орди прокотилися Європою, залишаючи попіл. Але на берегах Дніпра щось вистояло — Антський союз, конфедерація, що проіснує триста років і закладе фундамент майбутньої України.

### Strategy L2: Create Stakes

**Before (no stakes):**
> Слов'яни практикували народоправство.

**After (with stakes):**
> Слов'яни практикували народоправство — і це врятувало їх від знищення. Коли готи стратили князя Божа разом із 70 старійшинами, вони вірили, що обезголовили народ. Але вже за рік союз обрав нових лідерів. Влада не належала одній людині — вона належала закону громади.

### Strategy L3: Add the "Why It Matters Now"

**Before (orphan fact):**
> Слов'яни цінували дане слово понад усе.

**After (connected):**
> Слов'яни цінували дане слово понад усе. Ця етика "людей слова" пройшла крізь тисячоліття — від антського віча до козацької присяги і до сучасного волонтерського руху, де довіра є основою всього.

### Strategy L4: Break Up Dense Sections

**Before (wall):**
> [200 words of continuous historical description]

**After (with breathing room):**
> [100 words of description]
>
> > 💡 **Чи знали ви?**
> > [Surprising fact that illustrates the point]
>
> [100 words continuing the narrative]

### Strategy L5: End Sections with Forward Momentum

**Before (dead end):**
> Так закінчився антський період.

**After (momentum):**
> Антський союз зник з карт — але не з історії. Його традиції, його віче, його дух свободи — все це ввійшло в кров народу, що незабаром побудує Київську Русь.

---

> **PERSONA:** Embody the Ukrainian linguist & historian. See `claude_extensions/skills/_shared/persona.md`

---

**MANDATE:** Evaluate module for educational quality, coherence, soundness. Immediately fix to 10/10 scores.

**IPA RULE:** All phonetics MUST use IPA (no Latin transliteration). IPA is sole standard.

**PYTHON ONLY:** Use `.venv/bin/python` (never `python3`).

**CRITICAL WORKFLOW NOTE:** This is for **manual quality review AFTER audit_module.py passes**. audit_module.py validates structure (word counts, activity counts, richness metrics, immersion %). This focuses on pedagogical quality AND linguistic accuracy.

**Skill Metadata:**

```yaml
---
name: review-content-v3
description: 0-10 scoring rubric with A+ seminar lecture quality assessment
version: '4.0'
category: quality
dependencies: audit_module.py
changelog: v4.0 - Added Lecture Experience Audit as TOP PRIORITY (dimension 12)
---
```

## Critical Sections Index (DO NOT SKIP)

0. **🎓 LECTURE EXPERIENCE AUDIT (DO FIRST)** ← TOP PRIORITY
1. Template Compliance (auto-fail if violated)
2. **Linguistic Accuracy (auto-fail for factual errors)**
3. Activity Quality (auto-fail for structure/wrong answers)
4. Richness Red Flags (auto-fail for AI slop)
5. Red Flags (multiple auto-fails)
6. Content Richness (B1+ critical)
7. Humanity & Flow Audit
8. Dryness Flags (rewrite if 2+)
9. Human Warmth Checklist (<2 markers = fail)
10. LLM Fingerprint Detection (B1+ critical)

**CHECKPOINT:** Evaluate ALL 11 sections. START with Lecture Experience.

## Module Number to Slug Lookup

**CRITICAL:** Before reviewing, determine the exact module slug from the curriculum.yaml manifest.

1. **Locate Manifest:** `curriculum/l2-uk-en/curriculum.yaml`
2. **Find Level Section:** Look for the `[LEVEL]:` entry (e.g., `b2-hist:`)
3. **Get Slug by Index:** Modules are 1-indexed. For module number N, take the (N-1)th item in the `modules:` list.
4. **Example for B2-HIST Module 1:**
   ```
   b2-hist:
     type: track
     modules:
       - trypillian-civilization  # [1] Index 0
       - scythians-sarmatians     # [2] Index 1
   ```
   Module 1 = `trypillian-civilization`
5. **File Path:** `curriculum/l2-uk-en/{level}/{slug}.md`

**If number > module count:** Return error "Module {num} not found in {level} (max {count})".

## Usage

```
/review-content-v3 [LEVEL]              # Review all in level
/review-content-v3 [LEVEL] [MODULE_NUM] # Single module
/review-content-v3 [LEVEL] [START-END]  # Range
```

## Batch Mode (Multiple Modules)

Use subagents for each module (fresh context per module to avoid exhaustion).

```
For each module in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Agent prompt: "Run /review-content-v3 {level} {module_num}"
  3. Wait for agent completion
  4. Log result (score, issues)
  5. Continue to next module (fresh context)
```

## Single Module Mode

### Extract Content

- Lesson content: Everything before ## Activities (include summaries, examples, boxes; exclude activities/vocab sidecars)
- Metadata: Title, level, module num, topic

### Locate Activities (YAML-Mandatory)

**Logic:**

- Check for `activities/{slug}.yaml`.
- Scan Markdown for forbidden headers: ## quiz, ## match-up, etc.
- **Duplicate Activities:** YAML exists + headers exist → ⚠️ DUPLICATE (Safe fix: Remove inline, keep vocab)
- **Legacy:** Only headers → "Migrate to YAML" (blocking)
- **Correct:** Only YAML → ✅ Proceed
- **Missing:** Neither → ❌ Fail

**YAML Schema:** See docs/ACTIVITY-YAML-REFERENCE.md for 12+ types (quiz, match-up, etc.).

### Evaluate Quality

**Step 0: Template Compliance (Auto-fail if violated)**

Verify against level template:

| Level/Type | Template |
|------------|----------|
| B1 M01-05 (Metalanguage) | b1-metalanguage-module-template.md |
| B1 M06-51 (Grammar) | b1-grammar-module-template.md |
| B1 Checkpoints | b1-checkpoint-module-template.md |
| B1 M52-71 (Vocabulary) | b1-vocab-module-template.md |
| B1 M72-81 (Cultural) | b1-cultural-module-template.md |
| B1 M82-86 (Integration) | b1-integration-module-template.md |
| B2 | b2-module-template.md |
| B2-HIST | b2-history-module-template.md |
| C1 | c1-module-template.md |
| C2 | c2-module-template.md |
| LIT | lit-module-template.md |

**Module Architect Skills Reference:**

| Module Type | Skill | Review Focus |
|-------------|-------|--------------|
| Grammar (B1-B2) | `grammar-module-architect` | TTT pedagogy, aspect/motion verb teaching |
| Vocabulary (B1) | `vocab-module-architect` | Collocations, synonymy, register |
| Cultural (B1-C1) | `cultural-module-architect` | Authentic materials, regional balance |
| History/Biography (B2-C1) | `history-module-architect` | Decolonization, primary sources |
| Integration (B1-B2) | `integration-module-architect` | Skill coverage, no new content |
| Checkpoint (All) | `checkpoint` | All skill groups tested, 16+ activities |
| Literature (LIT) | `literature-module-architect` | 100% immersion, essays not drills |

**Ukrainian Grammar Validation Sources:**

- ✅ **Trusted:** Словник.UA, Словарь Грінченка, Антоненко-Давидович "Як ми говоримо", Ohoiko "500+ Ukrainian Verbs"
- ✅ **Local Reference:** `docs/references/private/ohoiko-500-ukrainian-verbs.pdf` (if available)
- ❌ **NOT Trusted:** Google Translate, Russian-Ukrainian dictionaries

**Auto-fail Russianisms:**

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| кушать | їсти |
| да | так |
| кто | хто |
| нету | немає |
| приймати участь | брати участь |
| самий кращий | найкращий |
| слідуючий | наступний |
| на протязі | протягом |

**Auto-fail Calques:**

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| робити сенс | мати сенс |
| брати місце | відбуватися |
| дивитися вперед | чекати з нетерпінням |

---

## NEW: Section 1 — Linguistic Accuracy (AUTO-FAIL for factual errors)

**CRITICAL CHECK for Grammar Modules:** Verify that all linguistic claims are factually correct.

### 1a. Aspectual Pair Verification (Grammar Modules)

**Definition:** An aspectual pair consists of two verbs with the **SAME core meaning** that differ ONLY in aspect (imperfective = process, perfective = result).

**Verification Rule:** For each claimed aspectual pair, confirm:
1. Both verbs share the same core semantic meaning
2. They differ only in aspect, not in fundamental meaning
3. Cross-reference with authoritative sources: Ohoiko "500+ Ukrainian Verbs", Dobra Forma, slovnyk.ua

**Common Error Pattern — Semantic Complement Confusion:**

| ❌ WRONG (different meanings) | ✅ CORRECT (same meaning) |
|-------------------------------|---------------------------|
| шукати / знайти (search / find) | шукати / пошукати (search / search-PFV) |
| | знаходити / знайти (find / find-PFV) |
| питати / відповідати (ask / answer) | питати / запитати (ask / ask-PFV) |
| | відповідати / відповісти (answer / answer-PFV) |
| починати / закінчувати (begin / finish) | починати / почати (begin / begin-PFV) |
| | закінчувати / закінчити (finish / finish-PFV) |

**Test:** Can you search (шукати) without finding (знайти)? YES → They are NOT aspectual pairs, they are semantic complements.

**Auto-fail if:** Module claims semantically different verbs are aspectual pairs.

### 1b. Grammar Rule Accuracy

Verify grammar explanations against authoritative sources:
- Case usage rules
- Verb conjugation patterns
- Agreement rules
- Word order claims

**Auto-fail if:** Grammar rule is incorrectly stated.

### 1c. Etymology/Historical Claims

For modules making historical or etymological claims:
- Verify dates and facts
- Check against scholarly sources
- Flag unsupported claims

### 1d. Linguistic Accuracy Score

| Score | Meaning |
|-------|---------|
| 10 | All claims verified correct |
| 7-9 | Minor inaccuracies (terminology, edge cases) |
| 4-6 | Significant errors requiring correction |
| 0-3 | Fundamental errors (wrong aspectual pairs, incorrect rules) → AUTO-FAIL |

---

**Score each dimension 0-10 (see Scoring Philosophy below):**

1. **🎓 Lecture Quality (0-10):** Overall experience as a lecture — engaging, memorable, worth attending. **EVALUATE FIRST.**
2. **Coherence (0-10):** Logical flow, transitions, progressive difficulty, consistent terminology.
3. **Relevance (0-10):** Alignment with module goals, curriculum plan, level targets.
4. **Educational (0-10):** Clear explanations, useful examples, learning effectiveness.
5. **Language (0-10):** Ukrainian quality, absence of Russianisms/calques, euphony, naturalness.
6. **Pedagogy (0-10):** Teaching approach, scaffolding, level-appropriateness, TTT/CBI/PPP alignment.
7. **Immersion (0-10):** Ukrainian-to-English ratio, appropriate scaffolding for level.
8. **Activities (0-10):** Quality, density, variety, correct answers, format compliance.
9. **Richness (0-10):** Examples, engagement boxes, cultural references, proverbs, dialogues, visuals.
10. **Humanity (0-10):** Teacher voice, direct address, encouragement, warmth, real-world validation.
11. **LLM Fingerprint (0-10):** AI-generated patterns vs. authentic human writing.
12. **Linguistic Accuracy (0-10):** Factual correctness of all grammar rules, verb pairs, linguistic claims.

---

## Activity Quality Sub-Checks (Critical for Dimension 7)

### 7a. Structural Integrity (Auto-fail if violated)

- No duplicate items (same question twice)
- No mixed activity types (e.g., `[!error]` in fill-in)
- Correct callout format for activity type
- Item count matches level requirements
- YAML syntax valid

### 7b. Grammar & Linguistic Correctness + Naturalness

**Correctness Checks:**
- **Single-answer activities:** Only ONE correct answer exists linguistically
  - Flag: "читати → прочитати" when "почитати" is also valid perfective
  - Flag: Fill-in where multiple grammatical options work
- **Multi-answer activities (`select`):** All valid answers are included
- **Error-correction:** The "error" is genuinely wrong, not just stylistic
- Ukrainian spelling is correct
- Grammar forms are correct (case endings, verb conjugations)
- No Russianisms in options or answers

**Naturalness Assessment (1-10 Scale):**

| Score | Level | Description |
|-------|-------|-------------|
| 1-2 | Robotic | Direct English syntax, calques, unnatural formality |
| 3-4 | Unnatural | Grammatically correct but stilted, pronoun overuse |
| 5-6 | Functional | Minor unnaturalness, comprehensible |
| 7-8 | Natural | Good word order, appropriate markers |
| 9-10 | Native | Perfectly idiomatic, stylistically appropriate |

**Level Gates:** A1-A2 ≥5; B1+ ≥8

### 7c. Difficulty Calibration

| Level | Description |
|-------|-------------|
| too_easy | Content 1+ level below target |
| appropriate | Matches level, uses taught material |
| too_hard | Content 1+ level above target |

### 7d. Distractor Quality (1-5 Scale)

| Score | Quality |
|-------|---------|
| 1 | Nonsense - different word class, unrelated |
| 2 | Weak - same class but obviously wrong |
| 3 | Acceptable - plausible but not challenging |
| 4 | Good - targets common errors |
| 5 | Excellent - all options plausible in different contexts |

### 7e. Engagement Quality

- Cultural relevance
- Interesting topics
- Age-appropriate for adult learners
- No generic "textbook" examples

### 7f. Variety & Repetition

- Variety Score 0-100%
- <40% = Mechanical (same pattern repeated)
- 60-80% = Good variety
- >80% = Excellent

### 7g. External Resources

Check `docs/resources/external_resources.yaml`:
- URLs valid and accessible
- Resources match module topic
- Level-appropriate

**CEFR Quality Gates (ALL Levels):**

- Naturalness avg ≥5.0 (B1+ ≥8.0)
- Difficulty inappropriate ≤0%
- Engagement avg ≥3.5
- Distractor quality avg ≥4.2
- Variety avg ≥65%

**Activity Red Flags (Auto-fail):**

- ❌ Duplicate items
- ❌ Wrong format/broken YAML
- ❌ Wrong answer marked correct
- ❌ Multiple valid answers but only one accepted
- ❌ Russianisms in content
- ❌ Testing untaught material
- ❌ Nonsense distractors
- ❌ Spoiler hints
- ❌ Naturalness 1-2 for B2+
- ❌ Variety <40%

---

## Common Activity Issues (Examples)

### Issue 1: Multiple Valid Answers

```yaml
- type: fill-in
  prompt: "читати → ___"
  answer: прочитати
  options: [прочитати, читати, почитати]
```

**Problem:** "почитати" is ALSO a valid perfective (means "to read for a while"). Activity wrongly treats it as incorrect.
**Fix:** Rephrase to "Give the COMPLETIVE perfective" or add note "result-focused form".

### Issue 2: Mixed Activity Syntax

```yaml
- type: fill-in
  prompt: "говорити → ___ (suppletive pair)"
  error: suppletive pair  # ← WRONG - this is error-correction syntax
  answer: сказати
```

**Problem:** `error` field is error-correction syntax, not fill-in syntax.
**Fix:** Use only `answer` and `options` for fill-in activities.

### Issue 3: Duplicate Items

```yaml
items:
  - prompt: "розуміти → ___"
  - prompt: "готувати → ___"
  - prompt: "розуміти → ___"  # ← DUPLICATE
  - prompt: "готувати → ___"  # ← DUPLICATE
```

**Problem:** Items appear twice (copy-paste error).
**Fix:** Remove duplicates.

### Issue 4: Unrelated External Resources

**NOTE:** Resources are in `docs/resources/external_resources.yaml`.

```yaml
a1-09-food-and-drinks:
  youtube:
    - title: 'Cat Videos Compilation'  # ← UNRELATED
      url: 'https://youtube.com/...'
```

**Problem:** Resource has nothing to do with Ukrainian learning.
**Fix:** Replace with relevant content or remove entry.

---

## Content Richness Quality (B1+ Critical)

### 10a. Engagement Quality

❌ **DRY (robot wrote this):**
```markdown
Доконаний вид показує завершену дію.
Недоконаний вид показує незавершену дію.
Дивіться таблицю нижче.
```

✅ **RICH (learner will remember this):**
```markdown
Уявіть: ви читаєте книгу весь вечір — це процес, недоконаний вид.
Але ось ви закрили книгу — готово! Результат. Доконаний вид.

Це як різниця між «я йшов додому» (може, ще йду) і «я прийшов» (точка, фініш).
```

### 10b. Variety Check

Count unique sentence starters. Flag if >50% same pattern.

### 10c. Emotional Hooks (≥1 per section)

- Metaphor or analogy
- Real-world scenario
- Cultural connection
- Surprise or contrast
- Question to reader

### 10d. Cultural Depth

- ≥1 named Ukrainian place
- ≥1 cultural reference
- Real-world context for grammar/vocab

### 10e. Proverbs/Idioms (Grammar Modules)

≥1 proverb demonstrating the grammar point, woven naturally.

### 10f. Richness Score per Section

| Total | Action |
|-------|--------|
| 0-4 | ❌ REWRITE section |
| 5-7 | ⚠️ ENRICH section |
| 8-10 | ✅ PASS |

---

## Humanity & Flow Audit (The "Robot Test")

**Goal:** Ensure content feels like a human teacher speaking to a human learner.

### 11a. Cohesion Index (The "Glue" Test)

- **Check:** Do paragraphs flow logically or are they just stacked lists?
- **Pass:** Uses transitional phrases (_However, For example, In this context, Consequently_).
- **Fail:** Abrupt topic shifts without signaling.

### 11b. Naturalness Metric (The "Uncanny Valley" Check)

- **Check (English):** Friendly tutor or database export?
  - ❌ _Robotic:_ "Do not use this form. It is incorrect."
  - ✅ _Human:_ "Avoid this form—it sounds unnatural to native ears."
- **Check (Ukrainian):** Euphony (Милозвучність)
  - ❌ _Clunky:_ "В учителі є..." (Vowel clash)
  - ✅ _Euphonic:_ "У вчителя є..." (Alternation respected)

### 11c. Cognitive Load (Lexical Density)

- **Check:** Too dense with bolded terms/jargon without breathing room?
- **Pass:** Balance of new information vs. explanations/examples.
- **Fail:** >3 new concepts in a paragraph without example breakdown.

### 11d. Sentence Variety (Rhythm)

- **Check:** Variation in sentence length.
- **Fail:** 5 consecutive sentences of roughly equal length (S-V-O format).
- **Pass:** Mix of short, punchy sentences and longer, complex explanations.

### 11e. Figurative Language (The "Soul" Check)

- **Check (B1+):** Presence of idioms, metaphors, or colorful language.
- **Fail:** 100% literal, dry description.
- **Pass:** Uses analogies ("Think of cases like role tags in a play").

### 11f. Readability & Tone (English Instructions)

- **Contractions:**
  - ❌ _Robotic:_ "It is important that you do not forget..."
  - ✅ _Human:_ "It's important that you don't forget..."
- **Simplicity:** English explanations should be B1/B2 level.
  - ❌ _Dense:_ "The semantic properties of the aspectual pair denote..."
  - ✅ _Simple:_ "This pair shows us the difference between..."

### 11g. Cultural Authenticity

- **Check:** Ukrainian reality or translated English concept?
- **Pass:** Uses Oksana, Taras (not John, Mary), борщ, вареники, Kyiv, Carpathians.
- **Fail:** "John eats a hamburger in New York" translated to Ukrainian.

### 11h. "Aha!" Moment Check

- **Check:** Does the module facilitate a moment of discovery?
- **Pass:** "Now you see why..." or "That explains..." moments.

---

## Dryness Flags (Rewrite if 2+)

| Flag | Pattern |
|------|---------|
| TEXTBOOK_VOICE | No questions/hooks in 300+ words |
| ROBOTIC_TRANSITIONS | No phrases between paragraphs |
| REPETITIVE | Same pattern 5+ times |
| GENERIC_EXAMPLES | No named people/places |
| LIST_DUMP | Explanations as lists only |
| NO_CULTURAL_ANCHOR | Grammar without Ukrainian context |
| ENGAGEMENT_BOX_FILLER | Boxes just restate content |
| WALL_OF_TEXT | >500 words without boxes/dialogue |
| EUPHONY_VIOLATION | >3 u/v or i/y alternation errors |

---

## LLM Fingerprint Detection (Detailed)

### 15a. Overused AI Phrases (Flag 3+ → LLM_CLICHE_OVERUSE)

**English:**
- ❌ "It's important to note that..."
- ❌ "Let's dive into..."
- ❌ "Mastering [X] is crucial for..."
- ❌ "In conclusion..." / "To summarize..."
- ❌ "Additionally..." / "Furthermore..." / "Moreover..."

**Ukrainian:**
- ❌ "Важливо зазначити, що..."
- ❌ "Давайте заглибимось у..."
- ❌ "Оволодіння [X] є важливим для..."

### 15b. False Specificity (<3 Ukrainian refs → FALSE_SPECIFICITY)

❌ **Fake Specific:** "Уявіть: ви йдете до магазину і купуєте їжу."
✅ **Real Specific:** "Уявіть: ви на Бесарабському ринку в Києві. Продавець пропонує свіжу паляницю."

### 15c. Certainty Overload (>5 absolutes → OVERCONFIDENCE)

❌ "Дієслова руху завжди використовуються з префіксами."
✅ "Дієслова руху часто використовуються з префіксами."

### 15d. Anecdotal Absence (No narratives → NO_NARRATIVE_VOICE)

Module needs ≥1:
- Student scenario with stakes
- Cultural story
- Historical context with narrative

### 15e. Predictability (No surprises → PREDICTABLE_PEDAGOGY)

Module needs ≥1:
- Surprising fact
- Counterintuitive example
- Grammar "trick" reveal

### 15f. Emotional Flatness (<1 marker/100 words → EMOTIONAL_FLATNESS)

Check for: !, ?, emphatic words, evaluative language, direct address.

### 15g. Voice Consistency (Shifts >2 → INCONSISTENT_VOICE)

Consistent use of ви/formal or ти/informal throughout.

### 15h. Depth of Explanation (No "why" → MISSING_WHY_LAYER)

For each grammar concept verify:
- ✅ What (definition)
- ✅ How (examples)
- ✅ Why it matters
- ✅ Common mistake

### 15i. Cultural Resonance (Random facts → DECORATIVE_CULTURE)

Culture should BE the vehicle for teaching, not decoration.

---

## Human Warmth Checklist

### 16a. Direct Address (≥10 instances)

Search for: you, your, let's, we'll (English); ти, ви, давайте, ми (Ukrainian)

### 16b. Encouragement (≥1 phrase)

- "You've got this" / "З практикою це стане природним"
- "Don't worry" / "Не хвилюйтеся"

### 16c. Anticipates Confusion (≥2 instances)

- "You might think..." / "Студенти часто плутають..."
- "Common mistake..." / "Типова помилка..."

### 16d. Real-World Validation (≥1 instance)

- "After this module, you'll be able to..."
- "In real conversation..." / "У реальному житті..."

**Warmth Score:** Count passed checks (0-4). <2 → COLD_PEDAGOGY

---

## Richness Red Flags (AUTO-FAIL)

### 17a. ChatGPT Default Voice
```
Welcome to Module X! In this lesson, we'll explore...
First, let's understand... Then, we'll dive deeper...
```
→ **Auto-fail** if module opens with this structure.

### 17b. Bullet Point Barrage

>50% bullets without prose → **Auto-fail**

### 17c. Wikipedia Tone

Encyclopedic passive voice → **Auto-fail**

### 17d. Engagement Box Faker

>50% boxes just restate content → **Auto-fail**

---

## Scoring Philosophy

- **0-4 FAIL** (fix immediately)
- **5-6 FAIL** (below standard, fix)
- **7-8 INSUFFICIENT** (improve to 9+)
- **9-10 PASS** (acceptable)

**ONLY 9-10 IS ACCEPTABLE. Everything below requires fixes.**

**Justification Rule:**
- ≥8: Explain why not higher
- ≤6: Explain weaknesses
- 7: Explain both good and missing

---

## Dimension Rubrics (0-10 Scale)

### 0. Lecture Quality (TOP PRIORITY)
- 0-4: FAIL - Unreadable (boring, confusing, no narrative)
- 5-6: FAIL - Forgettable (technically correct but no engagement)
- 7-8: INSUFFICIENT - Adequate (informative but missing emotional peaks)
- 9-10: PASS - Memorable (compelling, would recommend to others)

**Key indicators for 9-10:**
- Clear narrative arc (hook → tension → climax → resolution)
- ≥2 genuine "I didn't know that!" moments
- Emotional engagement throughout
- Organic modern connections
- Memorable closing that resonates

### 1. Coherence
- 0-4: FAIL - Incoherent (missing sections, jumps)
- 5-6: FAIL - Basic (present, awkward transitions)
- 7-8: INSUFFICIENT - Clear (logical, smooth)
- 9-10: PASS - Seamless (perfect flow)

### 2. Relevance
- 0-4: FAIL - Off-topic (wrong focus)
- 5-6: FAIL - Loose (tangents)
- 7-8: INSUFFICIENT - Focused (serves goals)
- 9-10: PASS - Laser-focused

### 3. Educational
- 0-4: FAIL - Confusing/wrong
- 5-6: FAIL - Adequate, uninspiring
- 7-8: INSUFFICIENT - Clear/helpful
- 9-10: PASS - Outstanding ("aha" moments)

### 4. Language
- 0-4: FAIL - Major errors (Russianisms, calques)
- 5-6: FAIL - Functional, unnatural
- 7-8: INSUFFICIENT - Natural, good euphony
- 9-10: PASS - Native-level, elegant

### 5. Pedagogy
- 0-4: FAIL - Broken (wrong approach)
- 5-6: FAIL - Basic (template loose)
- 7-8: INSUFFICIENT - Solid (proper TTT/CBI)
- 9-10: PASS - Exemplary (innovative)

### 6. Immersion
- 0-4: FAIL - Wrong level
- 5-6: FAIL - Slightly off
- 7-8: INSUFFICIENT - Hits target
- 9-10: PASS - Optimal

**Ranges:** A1.1: 20-40%; A1.2: 40-60%; A1.3: 60-80%; A2: 40-70%; B1.1: 70-85%; B1.2+: 85-100%; B2+: 98-100%

### 7. Activities
- 0-4: FAIL - Broken (wrong answers, format)
- 5-6: FAIL - Functional (low density/variety)
- 7-8: INSUFFICIENT - Solid (good count/variety)
- 9-10: PASS - Outstanding (high density, creative)

### 8. Richness
**Min scores:** Grammar 95%, Vocab 92%, Cultural 90%, History 95%, Integration 88%
- 0-4: FAIL - Below min
- 5-6: FAIL - Meets min, thin
- 7-8: INSUFFICIENT - Above min, solid
- 9-10: PASS - Rich/varied (15%+ above)

### 9. Humanity
**Thresholds:** Direct Address ≥10, Encouragement ≥1, Anticipation ≥2, Validation ≥1
- 0-4: FAIL - Robotic
- 5-6: FAIL - Occasional warmth
- 7-8: INSUFFICIENT - Warm teacher voice
- 9-10: PASS - Exceptional warmth

### 10. LLM Fingerprint
- 0-4: FAIL - AI slop (multiple patterns)
- 5-6: FAIL - Some patterns
- 7-8: INSUFFICIENT - Minimal patterns
- 9-10: PASS - Human mastery

### 11. Linguistic Accuracy
- 0-4: FAIL - Fundamental errors (wrong verb pairs, incorrect rules) → AUTO-FAIL
- 5-6: FAIL - Significant errors requiring correction
- 7-8: INSUFFICIENT - Minor inaccuracies
- 9-10: PASS - All claims verified correct

---

## Fix Categories (Apply ALL Safe Fixes)

### Category 1: Structure & Format (ALWAYS SAFE)

- Remove duplicate activities (keep YAML, delete markdown)
- Fix typos, markdown artifacts
- Fix broken tables
- Fix euphony (у/в, і/й alternation)

### Category 2: Language Quality (ALWAYS SAFE)

- Replace Russianisms with correct Ukrainian
- Replace calques with idiomatic expressions
- Fix grammar errors (case endings, conjugations)
- Fix spelling errors

### Category 3: Pedagogy & Flow (SAFE IF <30% CHANGE)

- Add transitions between sections
- Rewrite robotic sentences to conversational
- Replace generic examples with Ukrainian cultural references
- Add "why" layer to explanations

### Category 4: Content Enrichment (SAFE IF <40% CHANGE)

- Add sensory detail
- Name specific places, foods, people
- Add proverbs/idioms
- Add surprise moments

### Category 5: Activity Quality (SAFE IF FIXING ERRORS)

- Fix wrong answers
- Rephrase ambiguous questions
- Improve distractor quality
- Add variety to sentence patterns

### Category 6: Human Warmth (ALWAYS SAFE)

- Add direct address (ви, давайте)
- Add encouragement phrases
- Add confusion anticipation
- Add real-world validation

### Category 7: AI Slop Removal (ALWAYS SAFE)

- Remove LLM clichés
- Break up bullet barrages
- Rewrite encyclopedic definitions
- Replace useless engagement boxes

### Category 8: Linguistic Accuracy (CRITICAL - Fix Immediately)

- Correct aspectual pair errors (semantic complements → true pairs)
- Fix incorrect grammar rules
- Verify claims against authoritative sources
- Add notes clarifying common misconceptions

**Risky Fixes (Require User Approval):**
- Rewriting >50% of content
- Changing pedagogical approach
- Removing entire sections

---

## Fix Strategies for AI-Generated Content

**When you detect AI slop, apply these concrete fixes:**

### Strategy 1: Add Sensory Detail

❌ **Generic:** "Людина готує їжу"
✅ **Vivid:** "Запах борщу наповнює кухню — бурячки, часник, кріп"

### Strategy 2: Name Everything

❌ **Vague:** "Я купив хліб у магазині"
✅ **Specific:** "Я купив паляницю в булочній 'Хлібний дім' на вулиці Хрещатик"

### Strategy 3: Add "Why" Layer

❌ **Shallow:** "Use perfective for results"
✅ **Deep:** "Чому важливо? Бо українець почує 'я робив' і запитає: 'І що? Зробив чи ні?' Недоконаний вид залишає питання відкритим."

### Strategy 4: Replace Certainty with Reality

❌ **Absolute:** "Це завжди неправильно"
✅ **Nuanced:** "Більшість українців скаже інакше. Хоч технічно обидва варіанти існують, один звучить природніше."

### Strategy 5: Inject Story

❌ **Factual:** "Genitive shows possession"
✅ **Narrative:** "Марія йде до мами. Чому 'мами', а не 'мама'? Бо це — мамин дім, мамина вулиця, мамине місто. Родовий відмінок створює зв'язок: не просто 'йти до', а 'йти до когось свого'."

---

## Overall Score Calculation

**Weighted:**

```
Overall = (Lecture_Quality × 1.5 + Coherence × 1.0 + Relevance × 1.0 + Educational × 1.2 +
          Language × 1.1 + Pedagogy × 1.2 + Immersion × 0.8 + Activities × 1.3 +
          Richness × 0.9 + Humanity × 0.8 + LLM × 1.1 + Linguistic_Accuracy × 1.5) / 13.4
```

**Note:** Lecture Quality and Linguistic Accuracy have highest weight (1.5 each) because:
- A boring lecture fails regardless of technical quality
- Factual errors destroy credibility

**Round:** Nearest 0.5.

---

## Final Report Format

**⚠️ USE THE MANDATORY FORMAT FROM THE TOP OF THIS FILE.**

There is ONE format. No variations. See "⚠️ MANDATORY OUTPUT FORMAT" section above.

**Quick reference:**
- File: `{slug}-review.md`
- Location: `curriculum/l2-uk-en/{level}/review/`
- Header: `# Module {NUM}: {Ukrainian Title}`
- Scores: Table format with all 11 dimensions
- Timestamp: Full datetime `YYYY-MM-DD HH:MM:SS`

### Additional Sections (after scores table)

```markdown
## Lecture Experience Analysis

**Narrative Arc:** {HOOK ✅/❌} → {TENSION ✅/❌} → {JOURNEY ✅/❌} → {CLIMAX ✅/❌} → {RESOLUTION ✅/❌}
**Emotional Beats:** {Count curiosity/surprise/pride/empowerment moments}
**Pacing Issues:** {List sections with walls of text or energy drops}

## Weak Moments & Rewrites

### Weak Moment 1: {Category}
**Location:** Line {X} / Section "{name}"
**Original:**
> {Quote the weak text}

**Problem:** {Why it's weak}

**Rewrite:**
> {Improved version}

### Weak Moment 2: {Category}
...

## Linguistic Accuracy Issues

- {Quote} → {Correction} — {Source}

## Strengths

- {3-5 specific strengths}

## Issues

- {All issues by category}

## Recommendation

{✅ PASS / ❌ FAIL} — {One-line summary}

## Action Items

1. {Fix description} — ✅ APPLIED / ⏳ MANUAL
```

---

## Batch Summary Format (Level-Wide Reviews)

When reviewing multiple modules, generate a summary:

```markdown
# Content Quality Summary - {Level}

**Modules Reviewed:** {count}
**Generated:** {YYYY-MM-DD HH:MM:SS}

## Results

| Status | Count | % |
|--------|-------|---|
| ✅ 9-10 (PASS) | {n} | {%} |
| ⚠️ 7-8 (INSUFFICIENT) | {n} | {%} |
| ❌ 0-6 (FAIL) | {n} | {%} |

**Average Score:** {avg}/10

## Patterns Across Level

### Common Strengths
- {pattern 1}
- {pattern 2}

### Common Issues
- {pattern 1} (affects {n} modules)
- {pattern 2} (affects {n} modules)

### Priority Fixes
1. **Critical:** {modules with score <5}
2. **Important:** {modules with linguistic accuracy issues}
3. **Enhancement:** {modules scoring 7-8}

## Module Scores

| # | Module | Score | Status | Key Issue |
|---|--------|-------|--------|-----------|
| 1 | {slug} | {X}/10 | ✅/⚠️/❌ | {issue} |
...
```

---

## Calibration Examples

**4/10:** Major linguistic errors (wrong aspectual pairs), AI slop, poor structure.
**6/10:** Scores 6.2, repetition, generic, minor accuracy issues.
**8/10:** Scores 8.3, strong but gaps in warmth or variety.
**10/10:** Scores 10.0, all claims verified, reference quality.

## Common Mistakes

- Anchoring to 10/10 without verification
- Ignoring linguistic accuracy (assuming content is correct)
- Not using low scores when warranted
- Missing justifications
- Inconsistent standards
- Not cross-referencing grammar claims with sources

**High scores earned, not given. Verify linguistic claims. Recalibrate if mostly 9-10s.**

---

## Important Notes

1. **Be specific** - Quote actual problematic text, don't describe vaguely
2. **Provide actionable fixes** - Not "improve this" but "change X to Y"
3. **Auto-fix safe issues** - Apply Categories 1-2, 6-7 immediately, run audit, verify pass
4. **Save to review/ folder** - Don't append to audit/ folder (that's for automated audit reports)
