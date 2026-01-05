# Review Content Quality

> **CRITICAL:** Follow this checklist EXACTLY. Do not improvise. Do not invent new criteria. Do not skip steps. Your goal is strict compliance verification.

> **⚠️ ALWAYS use `.venv/bin/python` - NEVER use `python3` or `python` directly!**

Evaluate module content for educational quality, coherence, and pedagogical soundness.

---

## 🎯 Critical Sections Index (DO NOT SKIP)

**Must-check sections in order of importance:**

1. **Section 0:** Template Compliance → Auto-fail if violated
2. **Section 8:** Activity Quality → AUTO-FAIL for structural errors, wrong answers
3. **Section 15:** Richness Red Flags → AUTO-FAIL for AI slop
4. **Section 17:** 0-10 Scoring System → Use for ALL dimension scores
5. **Section 9:** Red Flags → Multiple auto-fail conditions
6. **Section 13:** LLM Fingerprint Detection (10 subsections) → B1+ critical
7. **Section 10:** Content Richness → B1+ critical
8. **Sections 1-7:** Standard scoring criteria
9. **Section 12:** Dryness Flags → 2+ flags = rewrite
10. **Section 14:** Human Warmth → <2 markers = fail

**⚠️ CHECKPOINT REMINDER:** Before generating your report, verify you have evaluated ALL 10 critical sections above.

---

## Usage

```
/review-content [LEVEL]                    # Review all modules in level
/review-content [LEVEL] [MODULE_NUM]       # Review single module
/review-content [LEVEL] [START-END]        # Review range of modules
```

## Arguments

- `$ARGUMENTS` - One of:
  - `a1` - Review all A1 modules (1-34)
  - `a1 15` - Review module 15 only
  - `a1 10-20` - Review modules 10 through 20
  - `b2 1-10` - Review B2 modules 1 through 10

---

## Batch Mode (Multiple Modules)

**When reviewing a range or full level (e.g., `b1 2-5` or `a1`):**

Use the **subagent pattern** to process each module with fresh context:

```
For each module in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Agent prompt: "Run /review-content {level} {module_num} - review single module"
  3. Wait for agent completion
  4. Log result (score, issues)
  5. Continue to next module (fresh context)
```

**Why subagents?**

- Each module gets full context capacity
- Content review requires reading full module + templates
- Prevents context exhaustion on large batches

**Example batch execution:**

```
/review-content b1 2-5

→ Task agent: /review-content b1 2 → ✅ 5/5
→ Task agent: /review-content b1 3 → ⚠️ 4/5 (coherence)
→ Task agent: /review-content b1 4 → ✅ 5/5
→ Task agent: /review-content b1 5 → ⚠️ 3/5 (accuracy, examples)

Summary: 2/4 perfect, 2/4 need fixes
```

---

## Single Module Mode

## Instructions

Parse arguments: $ARGUMENTS

**Step 1: Determine Scope**

- If only LEVEL provided: Use batch mode (subagent per module)
- If LEVEL + NUMBER: Review single module directly
- If LEVEL + RANGE (e.g., "10-20"): Use batch mode (subagent per module)
- Find all matching files in `curriculum/l2-uk-en/{level}/`

**Step 2: For Each Module (Single Mode Only)**

### Extract Content

1. Read the module file
2. Extract lesson content (everything BEFORE `## Activities` or `## Вправи`)
   - Include: Summary, all instructional sections, examples, engagement boxes
   - Exclude: Activities, Self-Assessment (vocab/meta are in sidecars)
3. Extract metadata (title, level, module number, topic)

### Locate Activities (YAML-Mandatory Check)

**New Logic (STRICT ENFORCEMENT):**

1. **Check for YAML file** (`activities/{module-slug}.yaml`).
2. **REGARDLESS of identical YAML content**, you MUST scan the Markdown file for forbidden activity headers:
   - `## quiz`
   - `## match-up`
   - `## fill-in`
   - `## true-false`
   - `## anagram`
   - `## group-sort`
   - `## unjumble`
   - `## error-correction`
   - `## cloze`
   - `## mark-the-words`
   - `## dialogue-reorder`
   - `## select`
   - `## translate`
   - `## Activities`
   - `## Вправи`

**Scenario A (CRITICAL: Duplicate Activities):**

- **Condition:** YAML exists AND _any_ of the above headers exist in the Markdown.
- **Verdict:** ⚠️ **DUPLICATE DETECTED**
- **Action:** You MUST flag this as "Duplicate Activities".
- **Required Fix:** "Remove inline activities from Markdown (keep Vocabulary)" (Safe Fix).

**Scenario B (Legacy: Only Inline exists):**

- **Flag:** "Legacy Format"
- **Action Item:** "Migrate activities to YAML" (High Priority).
- **Note:** This is a blocking issue for finalization.

**Scenario C (Correct: Only YAML exists):**

- **Status:** ✅ PASS (Proceed to evaluate YAML content).

**Scenario D (Missing: Neither exists):**

- **Status:** ❌ FAIL (Missing activities).

**YAML Activity File Structure:**
For the **COMPLETE** schema of all 12+ activity types (quiz, match-up, fill-in, etc.), you **MUST** read:
`docs/l2-uk-en/YAML-ACTIVITY-WORKFLOW.md`

**Partial Example (Quiz only):**

```yaml
module: 11-aspect-in-imperatives
level: B1
activities:
  - type: quiz
    title: 'Вибір аспекту'
    items:
# ... (see YAML-ACTIVITY-WORKFLOW.md for full syntax)
```

### Evaluate Quality

**Step 0: Template Compliance Check**

Before scoring, verify the module follows the appropriate template:

**Template Selection by Level and Type:**

- **B1 M01-05 (Metalanguage):** `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`
- **B1 M06-51 (Grammar):** `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- **B1 Checkpoints (M15, M25, M34, M41, M51 — grammar phases only):** `docs/l2-uk-en/templates/b1-checkpoint-module-template.md`
- **B1 M52-71 (Vocabulary):** `docs/l2-uk-en/templates/b1-vocab-module-template.md`
- **B1 M72-81 (Cultural):** `docs/l2-uk-en/templates/b1-cultural-module-template.md`
- **B1 M82-86 (Integration):** `docs/l2-uk-en/templates/b1-integration-module-template.md`
- **B2:** `docs/l2-uk-en/templates/b2-module-template.md`
- **C1:** `docs/l2-uk-en/templates/c1-module-template.md`
- **C2:** `docs/l2-uk-en/templates/c2-module-template.md`
- **LIT:** `docs/l2-uk-en/templates/lit-module-template.md`

**Use Module Architect Skills for Focus-Area Review:**

| Module Type               | Skill                          | Review Focus                              |
| ------------------------- | ------------------------------ | ----------------------------------------- |
| Grammar (B1-B2)           | `grammar-module-architect`     | TTT pedagogy, aspect/motion verb teaching |
| Vocabulary (B1)           | `vocab-module-architect`       | Collocations, synonymy, register          |
| Cultural (B1-C1)          | `cultural-module-architect`    | Authentic materials, regional balance     |
| History/Biography (B2-C1) | `history-module-architect`     | Decolonization, primary sources           |
| Integration (B1-B2)       | `integration-module-architect` | Skill coverage, no new content            |
| Checkpoint (All)          | `checkpoint`                   | All skill groups tested, 16+ activities   |
| Literature (LIT)          | `literature-module-architect`  | 100% immersion, essays not drills         |

**Ukrainian Grammar Validation (MANDATORY):**

Validate ALL Ukrainian text against these sources:

- ✅ **Словник.UA** (slovnyk.ua) - standard spelling
- ✅ **Словарь Грінченка** - authentic Ukrainian forms
- ✅ **Антоненко-Давидович "Як ми говоримо"** - Russianisms guide
- ❌ **NOT TRUSTED:** Google Translate, Russian-Ukrainian dictionaries

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

**Verify:**

- [ ] Module structure matches template sections
- [ ] Word count meets template minimum (core prose only, excludes vocabulary/activities/tables)
- [ ] Activity count and types match template requirements
- [ ] Vocabulary count meets template specification
- [ ] Pedagogy (PPP/TTT/TBL/CBI) matches template
- [ ] Focus-area requirements from architect skill met

**If template compliance fails, flag as ❌ REWRITE regardless of other scores.**

Score each criterion 1-5:

**1. Coherence**

- Logical organization and flow
- Clear transitions between sections
- Progressive difficulty (simple → complex)
- Consistent terminology

**2. Relevance**

- Content matches module title
- Examples relate to topic
- Grammar focus appropriate for level
- Vocabulary used matches topic

**3. Educational Value**

- Clear, sufficient explanations
- Varied, meaningful examples
- Inductive discovery patterns (observe-first)
- Follows stated pedagogy (PPP/TBL)
- Engagement boxes add value (not filler)

**4. Language Quality**

- Clear, professional writing
- **Precision Check:** Uses exact synonyms (e.g., "completed" vs "finished" where nuanced). Avoids vague terms like "thing" or "stuff."
- No excessive repetition (same structure ≥5 times = flag)
- Grammatically correct Ukrainian (validate against Словник.UA, Грінченка, Антоненко-Давидович)
- Grammatically correct English explanations
- Consistent terminology
- **No Russisms/Surzhik:** Strictly standard Ukrainian. Auto-fail: кушать→їсти, да→так, кто→хто, нету→немає, приймати участь→брати участь, самий кращий→найкращий
- **No Calques:** Auto-fail: робити сенс→мати сенс, брати місце→відбуватися

**5. Pedagogical Correctness**

- **Sequence:** Does it teach A before B? (e.g., specific letters before reading words)
- **Scaffolding:** clear step-by-step instructions?
- **Cognitive Load:** Is it too much at once?
- **Accuracy:** Are grammar rules explained correctly?
- **The "Why":** Does the module explain *why* we are learning this right now? (Motivation/Relevance).

**6. Natural Immersion (Mixed Language Check)**

- **Natural Flow:** Mixing must feel intentional (e.g., "In Ukrainian, we say **так** for yes"), NOT forced.
- **Syntactic Integrity:** Do NOT break English syntax just to insert a Ukrainian word (e.g., "The **хлопець** goes to the **школа**" -> BAD).
- **No "Denglish":** Sentences should generally be fully English (explanation) or fully Ukrainian (example), with specific exceptions for target vocabulary insertion in clear contexts.
- **Contextual Clarity:** Does the mix help or confuse?
- **Exception:** Checkpoint modules (assessments) are exempt from strict immersion flow checks.

**7. Word Salad Check**
Flag if ANY true:

- Same sentence pattern repeated 5+ times
- Generic filler without substance
- Contradictory explanations
- Examples unrelated to explanations
- Clear auto-generation artifacts

---

> **⚠️ CHECKPOINT REMINDER #1:** You are now entering **Section 8: Activity Quality** - one of the most critical sections.
> **AUTO-FAIL conditions:** Wrong answers, multiple valid answers treated as incorrect, duplicate items, broken format.
> **DO NOT SKIP THIS SECTION.** Activities are the primary learning tool.

---

**8. Activity Quality** (Critical Check)

Review ALL activities from the appropriate source:

- **YAML file** (if `activities/{module-slug}.yaml` exists): Structured format, check YAML validity
- **MD file** (legacy): Check embedded activity sections after `## Activities` or `## Вправи`

For each activity, check:

**8a. Structural Integrity**

- No duplicate items (same question appears twice)
- No mixed activity types (e.g., `[!error]` syntax inside a `fill-in` activity)
- Correct callout format for activity type (see `docs/ACTIVITY-MARKDOWN-REFERENCE.md`)
- Item count matches level requirements

**8b. Answer Validity**

- **Single-answer activities:** Only ONE correct answer exists linguistically
  - Flag: "читати → прочитати" when "почитати" is also valid perfective
  - Flag: Fill-in where multiple grammatical options work
- **Multi-answer activities (`select`):** All valid answers are included
- **Error-correction:** The "error" is genuinely wrong, not just stylistic

**8c. Linguistic Accuracy**

- Ukrainian spelling is correct
- Grammar forms are correct (case endings, verb conjugations)
- Distractors are plausible but genuinely wrong (not trick questions)
- No Russisms in options or answers

**8d. Pedagogical Alignment**

- Activity tests what was TAUGHT in this module (not future content)
- Difficulty matches level (A1 activities shouldn't require case knowledge untaught)
- Activity type suits the learning goal:
  - Grammar → fill-in, error-correction, unjumble
  - Vocabulary → match-up, quiz, translate
  - Comprehension → true-false, select, cloze
- Clear, unambiguous instructions

**8d-ii. Content vs. Language Testing (B2/C1 History/Biography)**

**CRITICAL for content modules (Issue #359):** Activities must test **language skills**, not content recall.

**The Golden Rule:** "Can the learner answer without reading the Ukrainian text?" → If YES, FAIL

**RED FLAGS (deduct from Pedagogy score):**
- Quiz: "У якому році...", "Хто був...", "Хто написав..." WITHOUT "Згідно з текстом"
- Fill-in: Answer is a year/date (1932, 1814)
- Match-up: Author → Work title (tests facts, not language)

**GREEN FLAGS (correct):**
- Quiz: "Згідно з текстом, як автор пояснює..."
- Fill-in: Collocations/vocabulary from text
- Match-up: Ukrainian term → Ukrainian definition

**Scoring deduction:** 1-2 violations (-1), 3-4 violations (-2), 5+ violations (-3 points)

**8e. External Resources**

**NOTE:** Resources are stored in `docs/resources/external_resources.yaml` (NOT in markdown files).

When reviewing, check the YAML file for this module's resources:

- YouTube videos are relevant to module topic
- URLs are valid and accessible
- Resources match level (A1 shouldn't link C1 content)
- No duplicate resources across modules without reason
- Blog/article links are from reputable Ukrainian learning sources

If you find `> [!resources]` in a markdown file, it's stale (remove it - will be regenerated from YAML at build time).

**Activity Red Flags (Auto-fail):**

- ❌ **Spoiler Hints:** The hint gives away the answer (e.g., `Answer: cat`, `Hint: It is a c_t`).
- ❌ **Nonsense Options:** Distractors are illogical or obviously wrong without linguistic knowledge (e.g., `Select: Apple`, Options: `Apple`, `Car`, `Moon`, `Sock` - too easy).
- ❌ Multiple valid answers but only one accepted
- ❌ Wrong activity type syntax mixed in
- ❌ Grammatically incorrect "correct" answer
- ❌ Testing untaught material
- ❌ Duplicate items in same activity
- ❌ Broken/unrelated external resources

**9. Red Flags (Auto-fail)**
Flag if:

- **Forced Mixing:** "I want to **їсти** the **яблуко**." (Syntactic breakage)
- **Undefined Terms:** Using concepts not yet taught.
- **False Friends:** Using high-level grammar (cases) in A1 without explanation.
- **Russianisms/Surzhik:** Any detection of mixed Ukrainian-Russian forms (unless explicitly teaching _about_ Surzhik).
- **Inline Activities:** Activities defined in Markdown (Scenario B) instead of YAML. (Exception: If actively migrating).

**10. Content Richness Quality (B1+ Critical)**

This is not about counts. This is about whether the content is ALIVE or DEAD.

**10a. Engagement Quality (Entertainment Value)**

- **Check:** Is this boring? Does it feel like a chore to read?
- **Pass:** Uses humor, intrigue, or storytelling.
- **Fail:** Dry recitation of rules without soul.

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

💡 **Чому це важливо?**
Українці чують цю різницю одразу. Неправильний вид —
і речення звучить... дивно. Як фальшива нота в пісні.
```

**10b. Variety Check**

Count unique sentence starters in each section. If >50% of sentences start the same way, flag as DRY.

❌ DRY pattern:

```markdown
Доконаний вид означає...
Доконаний вид використовується...
Доконаний вид показує...
Доконаний вид має...
```

✅ RICH pattern:

```markdown
Коли дія завершена — це доконаний вид.
Українці кажуть «я прочитав книгу», бо книга закінчена.
А якщо ще читаю? Тоді «читаю» — без результату.
Порівняйте: «він писав лист» vs «він написав лист».
```

**10c. Emotional Hooks**

Each major section needs at least one of:

- Metaphor or analogy (як фальшива нота, як різниця між X і Y)
- Real-world scenario (уявіть: ви на співбесіді...)
- Cultural connection (українці кажуть так, бо...)
- Surprise or contrast (але тут є сюрприз!)
- Question to reader (а що якщо...? чому так?)

❌ No hooks = textbook voice = learner falls asleep
✅ Has hooks = conversation voice = learner stays engaged

**10d. Cultural Depth (B1+)**

Each module should include:

- [ ] At least 1 named Ukrainian place (Львів, Карпати, Дніпро)
- [ ] At least 1 cultural reference (traditional, historical, or contemporary)
- [ ] Real-world context showing WHY this grammar/vocab matters

❌ Generic: "Людина купує хліб у магазині."
✅ Specific: "Оксана купує паляницю на Бесарабському ринку в Києві."

**10e. Proverbs & Idioms (B1+ Grammar Modules)**

Each grammar module should include 1-2 proverbs or idioms that:

- Naturally demonstrate the grammar point
- Are woven into content, not just listed
- Have cultural context explained

Example for aspect:

```markdown
Українці кажуть: «Не кажи гоп, поки не перескочиш».
Зверніть увагу: **перескочиш** — доконаний вид.
Чому? Бо йдеться про результат: перестрибнув чи ні.
```

**10f. Richness Score Calculation**

For each section, score:

| Criterion       | 0                   | 1                | 2                         |
| --------------- | ------------------- | ---------------- | ------------------------- |
| Engagement      | Textbook voice      | Some personality | Conversational, memorable |
| Variety         | Repetitive starters | Mixed            | Varied, rhythmic          |
| Hooks           | None                | 1-2              | 3+ per section            |
| Cultural depth  | Generic examples    | Some specifics   | Rich, placed content      |
| Proverbs/idioms | None                | 1 (forced)       | 1-2 (natural)             |

**Total 0-4:** ❌ REWRITE section
**Total 5-7:** ⚠️ ENRICH section
**Total 8-10:** ✅ PASS

**11. Humanity & Flow Audit (The "Robot Test")**

**Goal:** Ensure content doesn't just pass structural rules but feels like a human teacher speaking to a human learner.

**11a. Cohesion Index (The "Glue" Test)**
- **Check:** Do paragraphs flow logically or are they just stacked lists?
- **Pass:** Uses transitional phrases (*However, For example, In this context, Consequently*).
- **Fail:** Abrupt topic shifts without signaling. Paragraphs that start with definitions immediately after unconnected examples.

**11b. Naturalness Metric (The "Uncanny Valley" Check)**
- **Check (English Instructions):** Does it sound like a friendly tutor or a database export?
  - ❌ *Robotic:* "Do not use this form. It is incorrect."
  - ✅ *Human:* "Avoid this form—it sounds unnatural to native ears."
- **Check (Ukrainian Content):** **Euphony (Милозвучність).**
  - ❌ *Clunky:* "В учителі є..." (Vowel clash)
  - ✅ *Euphonic:* "У вчителя є..." (Alternation rules respected)

**11c. Cognitive Load (Lexical Density)**
- **Check:** Is the text too dense with bolded terms/jargon without breathing room?
- **Pass:** Balance of new information vs. explanations/examples.
- **Fail:** >3 new concepts introduced in a single paragraph without example breakdown.

**11d. Sentence Variety (Rhythm)**
- **Check:** Variation in sentence length.
- **Fail:** 5 consecutive sentences of roughly equal length (e.g., S-V-O format).
- **Pass:** Mix of short, punchy sentences and longer, complex explanations.

**11e. Figurative Language (The "Soul" Check)**
- **Check (B1+):** Presence of idioms, metaphors, or colorful language.
- **Fail:** 100% literal, dry description.
- **Pass:** Uses analogies to explain grammar (e.g., "Think of cases like role tags in a play").

**11f. Readability & Tone Check (English Instructions)**
- **Contraction Usage:** Ensure natural use of contractions.
  - ❌ *Robotic:* "It is important that you do not forget..."
  - ✅ *Human:* "It's important that you don't forget..."
- **Instruction Simplicity:** English explanations should be simple (B1/B2 level).
  - ❌ *Dense:* "The semantic properties of the aspectual pair denote..."
  - ✅ *Simple:* "This pair shows us the difference between..."

**11g. Cultural Authenticity Check**
- **Check:** Does the content reflect Ukrainian reality or is it a translated English concept?
- **Pass:** Uses culturally relevant names (Oksana, Taras), foods (borshch, varenyky), and places (Kyiv, Carpathians).
- **Fail:** "John eats a hamburger in New York" translated to Ukrainian.

**11h. "Aha!" Moment Check**
- **Check:** Does the module facilitate a moment of discovery?
- **Pass:** "Now you see why..." or "That explains..." moments.

**11i. Accessibility & Inclusivity Check**
- **Check:** Is the language inclusive and avoiding stereotypes?
- **Pass:** Gender-neutral phrasing where possible, diverse examples.

**12. Dryness Flags**

Flag content as DRY if ANY of these are true:

| Flag                  | Pattern                                                       | Excluded Module Types                  |
| --------------------- | ------------------------------------------------------------- | -------------------------------------- |
| TEXTBOOK_VOICE        | No questions, metaphors, or emotional hooks in 300+ words     | —                                      |
| ROBOTIC_TRANSITIONS   | No transitional phrases between paragraphs                    | —                                      |
| REPETITIVE            | Same sentence structure >5 times in section                   | —                                      |
| GENERIC_EXAMPLES      | No named people, places, or specific scenarios                | —                                      |
| LIST_DUMP             | Explanation is just a list without narrative flow             | —                                      |
| NO_CULTURAL_ANCHOR    | Grammar taught without Ukrainian cultural context             | —                                      |
| ENGAGEMENT_BOX_FILLER | 💡 boxes just restate what was already said                   | —                                      |
| WALL_OF_TEXT          | >500 words without engagement box, example block, or dialogue | History, Biography, Literature modules |
| EUPHONY_VIOLATION     | >3 detected euphony errors (u/v, i/y alternations)            | —                                      |

**If 2+ dryness flags: Section needs REWRITE, not just fix.**

**Note:** A1/A2 modules focus on scaffolding (Cyrillic, basic grammar). Richness scoring applies primarily to B1+ where full immersion enables engaging content.

---

> **⚠️ CHECKPOINT REMINDER #2:** You are now entering **Section 13: LLM Fingerprint Detection** (9 subsections).
> **B1+ CRITICAL:** AI-generated content that passes structural checks but lacks human voice, cultural authenticity, or pedagogical warmth.
> **Take your time with this section.** Check ALL 9 subsections (13a-13i).

---

## Section 13: LLM Fingerprint Detection

**Goal:** Flag content that exhibits telltale signs of lazy AI generation.

### 13a. Overused AI Phrases (Auto-flag)

**Common LLM Clichés to Flag:**

English:
- ❌ "It's important to note that..."
- ❌ "It's worth noting that..."
- ❌ "As we've seen..."
- ❌ "Let's dive into..."
- ❌ "In today's lesson..." (when module isn't time-bound)
- ❌ "Mastering [X] is crucial for..."
- ❌ "This will help you unlock..."
- ❌ "Think of it as..." (overused analogy starter)
- ❌ "In conclusion..." (textbook ending)
- ❌ "To summarize..." (unless checkpoint/integration)
- ❌ "Additionally, ..." "Furthermore, ..." "Moreover, ..." (stacked transitions without necessity)
- ❌ "Now that we've covered..."

Ukrainian:
- ❌ "Важливо зазначити, що..."
- ❌ "Як ми вже бачили..."
- ❌ "Давайте заглибимось у..."
- ❌ "У сьогоднішньому уроці..."
- ❌ "Оволодіння [X] є важливим для..."

**Check:** If 3+ of these phrases appear in one module, flag as **LLM_CLICHE_OVERUSE**.

**Fix:** Rewrite with natural Ukrainian/English teaching voice.

---

### 13b. False Specificity (The "Generic Disguise" Test)

**Pattern:** AI claims specificity but stays vague.

❌ **Fake Specific (AI-generated):**
```markdown
Уявіть собі ситуацію: ви йдете до магазину і купуєте їжу.
```
- **Issue:** "магазин" (generic store), "їжа" (generic food) - no actual detail.

✅ **Real Specific (Human):**
```markdown
Уявіть: ви на Бесарабському ринку в Києві. Продавець пропонує вам свіжу паляницю — ще теплу! Ви кажете: «Візьму дві».
```
- **Why it works:** Named place (Бесарабський ринок, Київ), specific item (паляниця), sensory detail (ще теплу), dialogue.

**Check:**
- Count named places, people, foods, cultural references
- If module has <3 specific Ukrainian references (place names, traditional foods, cultural practices), flag as **FALSE_SPECIFICITY**

---

### 13c. Certainty Overload (The "AI Overconfidence" Test)

**Pattern:** AI uses absolute statements where humans would hedge.

❌ **Robotic (AI certainty):**
```markdown
Дієслова руху завжди використовуються з префіксами.
Цей вираз ніколи не вживається в розмовній мові.
```

✅ **Human (natural qualification):**
```markdown
Дієслова руху часто використовуються з префіксами.
Цей вираз рідко зустрічається в розмовній мові — українці віддають перевагу простішим формам.
```

**Check:** Count absolutes (завжди, ніколи, всі, жоден, кожен, must, never, always, every).
- If >5 unqualified absolutes in a section, flag as **OVERCONFIDENCE**

**Fix:** Add hedging (часто, зазвичай, generally, typically, often) and reasoning (чому? бо...).

---

### 13d. Anecdotal Absence (The "Teacher Story" Test)

**Goal:** Real teachers tell stories. AI lists facts.

**Check:**
- Does the module include at least ONE:
  - Personal anecdote ("Коли я вперше...") [if teacher voice]
  - Student scenario with stakes ("Уявіть: ви на співбесіді і забули, як сказати...")
  - Cultural story ("В Україні кажуть, що...")
  - Historical context with narrative ("У 1991 році, коли...")

**Pass:** Module has ≥1 narrative moment (story arc: setup → conflict/question → resolution).
**Fail:** Module is 100% expository (just facts, no storytelling).

**Flag as:** **NO_NARRATIVE_VOICE** (B1+ only; A1/A2 exempt due to language limitations).

---

### 13e. Predictability Test (The "Surprise Factor")

**Pattern:** AI is formulaic. Human teaching has unexpected turns.

**Check:** Does the module have ANY of these?
- [ ] Surprising fact that challenges assumptions ("Але тут є сюрприз!")
- [ ] Counterintuitive example ("Здається дивно, але...")
- [ ] Playful contradiction ("Ви думаєте, що X? Насправді...")
- [ ] Unexpected cultural insight ("Українці роблять інакше, ніж ви очікуєте...")
- [ ] Grammar "trick" reveal ("Ось секрет, який спрощує все...")

**Fail:** Module follows 100% predictable path (definition → table → example → practice). Zero surprises.
**Pass:** Module has ≥1 moment where learner thinks "Oh! I didn't expect that!"

**Flag as:** **PREDICTABLE_PEDAGOGY**

---

### 13f. Emotional Flatness (The "Boredom Detector")

**Pattern:** AI rarely expresses emotion. Humans do.

**Check for Emotional Markers:**
- Exclamations: ! (excitement, surprise)
- Rhetorical questions: ? (engagement, challenge)
- Emphatic words: дуже, really, especially, particularly
- Evaluative language: beautiful, clever, tricky, surprising
- Direct address: ти/ви (you), давайте (let's)

**Density Check:**
- Count emotional markers per 100 words
- **Fail:** <1 per 100 words (flat, robotic)
- **Pass:** 2-4 per 100 words (conversational)
- **Overboard:** >6 per 100 words (too gimmicky)

**Flag as:** **EMOTIONAL_FLATNESS** (if fail threshold).

---

### 13g. Teacher Voice Consistency

**Goal:** Ensure a consistent pedagogical persona throughout.

**Check:**
- Does the voice shift between formal/informal without reason?
- Does the teacher persona stay consistent (encouraging vs. strict vs. playful)?
- Are pronouns consistent (ви/formal vs. ти/informal)?

❌ **Inconsistent:**
```markdown
Paragraph 1: "Давайте розглянемо..." (we together - inclusive)
Paragraph 3: "Вам потрібно запам'ятати..." (you - distant)
```

✅ **Consistent:**
```markdown
All paragraphs: "Ми розглянемо..." "Ми запам'ятаємо..." (consistent "we" voice)
```

**Check:** Flag if pronouns/tone shift >2 times without pedagogical reason.

**Flag as:** **INCONSISTENT_VOICE**

---

### 13h. Depth of Explanation (The "Why Depth" Test)

**Pattern:** AI stops at surface. Humans dig into "why."

**Example:**

❌ **Shallow (AI):**
```markdown
Perfective aspect shows completed action. Use it for results.
```

✅ **Deep (Human):**
```markdown
Why do Ukrainians care so much about aspect?

Because the verb form tells you whether to mentally "close the file" or not.

"Я писав лист" → File still open. Maybe I'm still writing, maybe I stopped but didn't finish.
"Я написав лист" → File closed. The letter exists now. Result achieved.

English doesn't force this choice. Ukrainian does. Every. Single. Time.
```

**Check:** For each grammar concept, verify:
- [ ] **What:** Definition provided
- [ ] **How:** Usage examples provided
- [ ] **Why it matters:** Cultural/linguistic reason explained
- [ ] **Common mistake:** What learners get wrong and why

**Fail:** Module teaches "what" and "how" but never "why."

**Flag as:** **MISSING_WHY_LAYER**

---

### 13i. Cultural Resonance (The "Soul" Test)

**Goal:** Ensure Ukrainian culture is woven in, not sprinkled on.

**Superficial Integration (AI):**
```markdown
🎬 Pop Culture Moment: Ukrainians like borshch!
```
- **Issue:** Random fact without connection to grammar/vocab.

**Deep Integration (Human):**
```markdown
Українці кажуть: "Не той борщ, що в горщик, а той, що в роті" (It's not the soup in the pot that counts, but the one in your mouth).

Зверніть увагу: **в горщик** (Accusative), **в роті** (Locative).

Чому різні відмінки? Бо один — куди кладуть (напрямок), інший — де знаходиться (місце).

Ця різниця — суть української граматики.
```

**Check:**
- [ ] Cultural content connects to grammar lesson (not random)
- [ ] Proverbs/idioms demonstrate grammatical structure
- [ ] Examples use Ukrainian reality (not translated Western scenarios)

**Fail:** Culture is decorative (random facts in boxes). Grammar is separate.
**Pass:** Culture IS the vehicle for teaching grammar.

**Flag as:** **DECORATIVE_CULTURE** (if fail).

---

### 13j. Narrative Completeness & Pacing (The "Third Act" Test)

**Goal:** Prevent "Wikipedia Summary" endings where the death or resolution is rushed.

**The "30-40-30" Rule:**
- **30% Setup:** Early life / Context
- **40% Conflict:** The Main Struggle / Career Peak
- **30% Resolution & Legacy:** The "Third Act" (see header guidance below)

**Third Act Headers (Living vs Deceased):**

| Subject Type | Appropriate Headers |
|--------------|---------------------|
| **Deceased** | `## Останні роки та Спадщина`, `## Смерть і пам'ять`, `## Наслідки` |
| **Living**   | `## Вплив і сучасна роль`, `## Внесок у сьогодення`, `## Значення для сучасної України` |

**For living persons:** The Third Act must cover their current impact, ongoing contributions, and what they represent for modern Ukraine — NOT just stop after "career achievements."

**Check:**
- Does the final section (Legacy, Impact, or Current Role) have the same level of detail/sensory richness as the beginning?
- Is the death/resolution/current impact summarized in 1-2 sentences while setup took 3 paragraphs? (Bad)
- Does the Main Body Text finish the story **before** the `# Summary` (Підсумок) section starts?
- Is there an "Echo" connecting the event/person to modern (2024) Ukraine?
- **For living persons:** Does the Third Act show their current significance, not just past achievements?

**Flag as:** **ABRUPT_ENDING** (if resolution is <15% of total length or feels rushed).

---

## Section 14: Human Warmth Checklist

**Goal:** Quantify teacher presence using pattern matching (not subjective judgment).

### 14a. Direct Address (Pattern Match)

**Search for these patterns:**
- English: `you`, `your`, `you'll`, `you're`, `let's`, `we'll`, `we're`, `we can`
- Ukrainian: `ти`, `ви`, `твій`, `твоя`, `ваш`, `ваша`, `давайте`, `ми`, `можемо`

**Count:** How many direct address patterns appear?
- **Pass:** ≥10 instances in module
- **Fail:** <10 instances

**Why 10?** Average 2,000-word module should have ~1 direct address per 200 words (5% density).

### 14b. Encouragement (Exact Phrase Match)

**Search for encouraging phrases (case-insensitive):**

English patterns:
- `you've got this` / `you got this`
- `don't worry` / `no worries`
- `with practice` / `after practice`
- `this becomes [natural/easier/clear]`
- `you'll master this` / `you'll get it`

Ukrainian patterns:
- `не хвилю(й|йся|йтеся)`
- `це зрозумі(є|ють) (кожен|всі)`
- `з практикою`
- `ви впораєтесь`
- `ви зможете`

**Count:** How many encouraging phrases?
- **Pass:** ≥1 encouraging phrase
- **Fail:** 0 encouraging phrases

### 14c. Anticipates Confusion (Pattern Match)

**Search for anticipation patterns:**
- `you might think` / `you may think`
- `you might be wondering` / `you may wonder`
- `students often confuse`
- `common mistake` / `typical error`
- `learners usually` / `people often`
- `don't confuse X with Y`
- `careful:` / `watch out:` / `note:`

Ukrainian:
- `ви можливо думаєте`
- `часто плутають`
- `типова помилка`
- `зверніть увагу:`
- `обережно:`

**Count:** How many anticipation patterns?
- **Pass:** ≥2 instances
- **Fail:** <2 instances

### 14d. Real-World Validation (Pattern Match)

**Search for relevance patterns:**
- `after this module, you` / `after this lesson, you`
- `this lets you` / `this allows you` / `this enables you`
- `you'll be able to` / `you can now`
- `in real life` / `in real conversation` / `in daily life`
- `when you [visit/travel/speak]`

Ukrainian:
- `після цього модуля`
- `це дозволить вам`
- `ви зможете`
- `у реальному житті`
- `в повсякденному спілкуванні`

**Count:** How many validation patterns?
- **Pass:** ≥1 instance
- **Fail:** 0 instances

---

### 14e. Human Warmth Score Calculation

**Scoring Formula:**
```
Warmth Score = (Direct Address ≥10 ? 1 : 0) +
               (Encouragement ≥1 ? 1 : 0) +
               (Anticipation ≥2 ? 1 : 0) +
               (Validation ≥1 ? 1 : 0)
```

| Score | Rating | Action         |
|-------|--------|----------------|
| 4/4   | ✅ Excellent | Pass - warm, human voice |
| 3/4   | ✅ Good | Pass - acceptable warmth |
| 2/4   | ⚠️ Adequate | ENRICH - add missing patterns |
| 1/4   | ❌ Cold | REWRITE - lacks teacher presence |
| 0/4   | ❌ Robotic | REWRITE - pure AI voice |

**Flag as:** **COLD_PEDAGOGY** if score ≤1/4.

**Example Report:**
```
Human Warmth: 2/4 (⚠️ ENRICH)
- Direct Address: ✅ 15 instances
- Encouragement: ❌ 0 instances (add encouraging phrases)
- Anticipation: ✅ 3 instances
- Validation: ❌ 0 instances (add real-world connection)
```

---

## Section 15: Richness Red Flags (AUTO-FAIL)

**These are fatal flaws that indicate AI slop:**

### 15a. The "ChatGPT Default Voice"

**Pattern Recognition:**
```markdown
Welcome to Module X! In this lesson, we'll explore...
First, let's understand... Then, we'll dive deeper into...
By the end of this module, you'll be able to...
```

**Why it's bad:** This is GPT's default scaffolding template. Zero personality.

**Auto-fail if:** Module opens with this exact structure.

### 15b. The "Bullet Point Barrage"

**Pattern:**
```markdown
Here are 5 key points:
- Point 1
- Point 2
- Point 3
- Point 4
- Point 5

Now let's look at 3 examples:
- Example 1
- Example 2
- Example 3
```

**Why it's bad:** No narrative flow. Just a list generator.

**Auto-fail if:** >50% of module is bullet lists without prose paragraphs.

### 15c. The "Wikipedia Copy-Paste" Syndrome

**Pattern:**
```markdown
The Dative case (Ukrainian: давальний відмінок) is a grammatical case
used in the Ukrainian language to indicate the indirect object of a verb.
```

**Why it's bad:** Encyclopedic tone. No teaching warmth. Passive voice overload.

**Auto-fail if:** Module uses encyclopedic definitions without rewriting for learner voice.

### 15d. The "Engagement Box Faker"

**Pattern:**
```markdown
💡 Did You Know?
Ukrainian has 7 cases!

💡 Pro Tip:
Remember to use the Dative case with these verbs.

💡 Cultural Note:
Ukrainians value hospitality.
```

**Why it's bad:** Boxes contain obvious/useless info. Padding, not value.

**Auto-fail if:** >50% of engagement boxes just restate what body text already said.

---

## Section 16: Fix Strategies for AI-Generated Content

**When you detect AI slop, apply these fixes:**

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

## Implementation Checklist for Sections 13-16

**For each module review, add these steps AFTER Section 12:**

**Step 13: Run LLM Fingerprint Detection**
- [ ] Check for overused AI phrases (13a)
- [ ] Verify real specificity vs. fake (13b)
- [ ] Count certainty markers (13c)
- [ ] Look for narrative moments (13d)
- [ ] Check for surprises (13e)
- [ ] Measure emotional density (13f)
- [ ] Verify voice consistency (13g)
- [ ] Check "why" depth (13h)
- [ ] Assess cultural integration (13i)
- [ ] Check narrative completeness & pacing (13j)

**Step 14: Human Warmth Audit**
- [ ] Direct address present? (14a)
- [ ] Encouragement included? (14b)
- [ ] Confusion anticipated? (14c)
- [ ] Real-world validation? (14d)

**Step 15: Richness Red Flags**
- [ ] No ChatGPT default voice? (15a)
- [ ] No bullet barrage? (15b)
- [ ] No Wikipedia tone? (15c)
- [ ] Engagement boxes add value? (15d)

**LLM Fingerprint Scoring:**
- **5/5:** All checks pass. Content feels authentically human.
- **4/5:** 1-2 minor flags. Mostly human, slight AI traces.
- **3/5:** 3-4 flags. Noticeably AI-generated but salvageable.
- **2/5:** 5+ flags. Heavy AI fingerprint. Needs rewrite.
- **1/5:** Auto-fail red flags present. Pure AI slop. Complete rewrite.

---

> **⚠️ FINAL CHECKPOINT:** Before writing your report, verify you have completed ALL sections:
> - ✅ Section 0: Template Compliance
> - ✅ Sections 1-7: Standard scoring (Coherence, Relevance, Educational, Language, Pedagogy, Immersion, Word Salad)
> - ✅ Section 8: Activity Quality (AUTO-FAIL if errors)
> - ✅ Section 9: Red Flags
> - ✅ Section 10: Content Richness (B1+)
> - ✅ Section 11: Humanity & Flow
> - ✅ Section 12: Dryness Flags
> - ✅ Section 13: LLM Fingerprint Detection (9 subsections, B1+ critical)
> - ✅ Section 14: Human Warmth (pattern match scoring)
> - ✅ Section 15: Richness Red Flags (AUTO-FAIL)
>
> **If you skipped any section above, GO BACK NOW and complete it before proceeding.**

---

## Section 17: 0-10 Scoring System

**CRITICAL INSTRUCTION:** Use this 0-10 scale for ALL dimension scores. High scores require justification. Perfect scores (10/10) should be rare.

### Scoring Philosophy

**Score Distribution:**
- **0-4 = FAIL** → Auto-fail gates, critical issues, must fix before passing
- **5-6 = PASS (Minimum)** → Meets gates, acceptable quality, has noticeable weaknesses
- **7-8 = GOOD** → Solid quality, minor improvements possible, above minimum standards
- **9-10 = EXCELLENT** → Exceptional quality, reference-worthy, innovative or exemplary

**Mandatory Justification Rule:**
- **For scores ≥8:** Explain what would make it higher (or why it's already 10/10)
- **For scores ≤6:** Explain specific weaknesses and what's missing
- **For score 7:** Explain both: what's good AND what could be better

### Dimension Rubrics

**1. Coherence (0-10)** - Logical flow, section transitions, narrative structure
- 0-4: Incoherent structure, contradictory statements, missing sections
- 5-6: Basic structure, some awkward transitions, occasional jumps
- 7-8: Clear flow, logical progression, smooth transitions
- 9-10: Seamless narrative, perfect flow, exemplary structure

**2. Relevance (0-10)** - Alignment with module goals, curriculum plan
- 0-4: Off-topic, wrong grammar focus, doesn't match curriculum plan
- 5-6: On-topic but loose, includes tangents
- 7-8: Focused, follows plan, all content serves learning goals
- 9-10: Laser-focused, every sentence advances learning, no filler

**3. Educational (0-10)** - Clear explanations, useful examples
- 0-4: Confusing or wrong information, unclear explanations
- 5-6: Adequate but dry, examples uninspiring
- 7-8: Strong explanations, good examples, covers edge cases
- 9-10: Outstanding pedagogy, memorable examples, "aha moments"

**4. Language (0-10)** - Ukrainian quality, euphony, naturalness
- 0-4: Multiple Russianisms, calques, broken grammar
- 5-6: Mostly correct, 1-2 minor Russianisms, occasional unnatural phrasing
- 7-8: Natural Ukrainian, no Russianisms, good euphony
- 9-10: Native-level mastery, flawless, beautiful euphony

**5. Pedagogy (0-10)** - Teaching approach, scaffolding, TTT/CBI alignment
- 0-4: Wrong approach, no scaffolding, violates TTT/CBI principles
- 5-6: Basic pedagogy, follows template loosely
- 7-8: Proper structure, good scaffolding, level-appropriate
- 9-10: Exemplary teaching, perfect template adherence, innovative

**5a. CRITICAL: Content vs. Language Testing (B2/C1 History/Biography)**

**The Golden Rule (Issue #359):** "Can the learner answer without reading the Ukrainian text?"
- If YES → Tests content recall (BAD) - Deduct 1-3 points from Pedagogy score
- If NO → Tests Ukrainian comprehension (GOOD)

**RED FLAGS (Content Recall):**
- Quiz: "У якому році...", "Хто був...", "Хто написав..." WITHOUT "Згідно з текстом"
- Fill-in: Answer is a year/date (1932, 1814, etc.)
- Match-up: Author → Work title (tests literature facts, not language)

**GREEN FLAGS (Language Testing):**
- Quiz: "Згідно з текстом, як автор пояснює..."
- Fill-in: Collocations/vocabulary from module text
- Match-up: Ukrainian term → Ukrainian definition

**Scoring Deduction:**
- 1-2 violations: -1 point
- 3-4 violations: -2 points
- 5+ violations: -3 points (max 5/10)

**6. Immersion (0-10)** - Ukrainian-to-English ratio for level
- 0-4: Wrong immersion level (A1 with 90% UK, B2 with 30% EN)
- 5-6: Slightly off target (within 5-10% of target)
- 7-8: Hits target range, appropriate scaffolding
- 9-10: Optimal balance, perfect for level

**7. Activities (0-10)** - Quality, density, variety, correct answers
- 0-4: Wrong answers, broken format, <minimum activities
- 5-6: Meets minimum count, some low density (<14 items)
- 7-8: Good count, all ≥14 items, good variety (6+ types)
- 9-10: High count, high density (16+ items), exceptional variety (8+ types)

**8. Richness (0-10)** - Examples, engagement, cultural refs, proverbs
- 0-4: Below minimum richness score for module type
- 5-6: Meets minimum, feels thin
- 7-8: 5-10% above minimum, solid content
- 9-10: 15%+ above minimum, exceptional variety

**9. Humanity (0-10)** - Teacher voice, warmth, encouragement
- 0-4: Robotic, zero direct address, no encouragement
- 5-6: 5-9 direct address, minimal encouragement
- 7-8: 10-15 direct address, good encouragement, warm voice
- 9-10: 20+ direct address, frequent encouragement, inspiring

**10. LLM Fingerprint (0-10)** - AI patterns vs authentic human writing
- 0-4: AI slop, auto-fail patterns, zero specificity
- 5-6: Some AI patterns, limited specificity
- 7-8: Mostly authentic, good specifics, minimal AI patterns
- 9-10: Zero AI fingerprint, exceptional specificity, authentic

### Overall Score Calculation

**Use weighted average (recommended):**
```
Overall = (
    Coherence × 1.0 +
    Relevance × 1.0 +
    Educational × 1.2 +  // Core learning value
    Language × 1.1 +     // Ukrainian quality critical
    Pedagogy × 1.2 +     // Teaching approach critical
    Immersion × 0.8 +    // Binary (right level or not)
    Activities × 1.3 +   // Primary learning tool
    Richness × 0.9 +
    Humanity × 0.8 +
    LLM Fingerprint × 1.1  // AI detection critical for B1+
) / 10.4
```

**Rounding:** Round to nearest 0.5 (e.g., 7.3 → 7.0, 7.6 → 8.0, 7.5 → 8.0)

### Common Scoring Mistakes to Avoid

1. **Anchoring to 10/10** - Don't assume perfect and deduct. Start neutral.
2. **Ignoring small issues** - "Mostly good" ≠ 9/10. Issues = 7-8/10.
3. **Not using low scores** - If problems exist, give 5-6/10.
4. **Missing justifications** - Every score ≥8 or ≤6 needs explanation.
5. **False equivalence** - "Meets gates" ≠ 8/10. Gates = 5-6/10.

**If you find yourself giving mostly 9-10s, you're being too generous. Recalibrate.**

**For full rubrics with examples, see:** `claude_extensions/commands/review-content-scoring-0-10.md`

---

**Step 3: Generate Summary Report**

For each module, output:

```
## Module {num}: {title}

**Template:** {template_name} | **Compliance:** ✅ PASS / ❌ FAIL
**Scores:** Coherence {X}/10 | Relevance {X}/10 | Educational {X}/10 | Language {X}/10 | Pedagogy {X}/10 | Immersion {X}/10 | Activities {X}/10 | Richness {X}/10 | **Humanity {X}/10** | **LLM Fingerprint {X}/10** | **Overall {X}/10**
**Status:** ✅ PASS / ⚠️ NEEDS WORK / ❌ REWRITE

**AI Detection Flags:** {list any triggered: LLM_CLICHE_OVERUSE, FALSE_SPECIFICITY, OVERCONFIDENCE, NO_NARRATIVE_VOICE, PREDICTABLE_PEDAGOGY, EMOTIONAL_FLATNESS, INCONSISTENT_VOICE, MISSING_WHY_LAYER, DECORATIVE_CULTURE, COLD_PEDAGOGY}

{If not PASS, list 2-3 main issues}
```

**Step 4: Apply Safe Fixes (Mandate: Aim for 8+/10)**

> **CRITICAL MANDATE:** Your goal is **8+/10** quality (GOOD to EXCELLENT). Do not settle for barely passing (5-6/10).
> Humans detect even "minor" friction points (robotic transitions, slight repetition, lack of "glue").
> **If you see a minor issue, FIX IT immediately.** Do not just report it.
> **Note:** 10/10 is rare (exceptional, reference quality). 8-9/10 is the target for solid modules.

For each module, apply fixes to elevate quality:

**Safe Fixes (Auto-apply NOW):**

- **Structure (Duplicate Activities):** If YAML activities file exists (Scenario A), **DELETE** the inline `## Activities` section from the Markdown file.
- **Flow & Humanity:** Add transitional sentences between abrupt sections (the "Glue" test).
- **Tone:** Rewrite robotic/dry sentences to be conversational.
- **Euphony:** Fix vowel clashes (у/в, і/й) to ensure natural Ukrainian flow.
- **Cleanliness:**
  - Remove leftover editing notes/meta-commentary.
  - Fix typos and repetition errors.
  - Delete redundant paragraphs (exact duplicates).
  - Clean up formatting artifacts.
- **Accuracy:** Remove or correct factually incorrect statements.

**Risky Fixes (Report only):**

- Major structural changes (moving entire sections).
- Rewriting >50% of the module.
- Changing the core pedagogical focus.

For safe fixes:

1. Apply the fix to the module file.
2. **If removing activities:** Verify YAML file exists and is valid first.
3. Run `.venv/bin/python scripts/audit_module.py {file_path}` to verify still passes.
4. If audit fails, revert the fix.
5. Mark fix status in review: ✅ FIXED or ❌ SKIPPED

**Step 5: Save Review Files**

For each module, save detailed review to:
`curriculum/l2-uk-en/{level}/review/{module_number}-{slug}-review.md`

Example: `curriculum/l2-uk-en/a1/review/03-the-gender-code-review.md`

**Step 6: Generate Final Summary**

After reviewing all modules in scope:

```
# Content Quality Summary

**Level:** {level}
**Modules Reviewed:** {count}
**Date:** {today}

---

## Overview

| Status | Count | Modules |
|--------|-------|---------|
| ✅ EXCELLENT (9-10/10) | {count} | {list} |
| ✅ GOOD (7-8/10) | {count} | {list} |
| ✅ PASS (5-6/10) | {count} | {list} |
| ❌ FAIL (0-4/10) | {count} | {list} |

---

## Module Reports

{Full report for each module}

---

## Detailed Module: {module_number} - {title}

**Overall Score:** {X}/10 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ (show X stars)
**Template:** {template_name} | **Compliance:** ✅ PASS / ❌ FAIL

### Scores Breakdown
- Template Compliance: ✅ PASS / ❌ FAIL {reason}
- **Coherence:** {X}/10 - {Brief description + justification if ≥8 or ≤6}
- **Relevance:** {X}/10 - {Brief description + justification if ≥8 or ≤6}
- **Educational:** {X}/10 - {Brief description + justification if ≥8 or ≤6}
- **Language:** {X}/10 - {Brief description + justification if ≥8 or ≤6}
- **Pedagogy:** {X}/10 - {Brief description + justification if ≥8 or ≤6}
- **Immersion:** {X}/10 - {Brief description + immersion %}
- **Activities:** {X}/10 - {Count, density, variety + justification if ≥8 or ≤6}
- **Richness:** {X}/10 - {Richness % + justification if ≥8 or ≤6} (B1+ only, N/A for A1/A2)
- **Humanity:** {X}/10 - {Pattern counts + justification if ≥8 or ≤6}
- **LLM Fingerprint:** {X}/10 - {AI patterns + justification if ≥8 or ≤6} (B1+ critical, A1/A2 informational)
- Word Salad: ❌ No / ⚠️ Yes
- Dryness Flags: {list any triggered flags}
- AI Detection Flags: {list any triggered: LLM_CLICHE_OVERUSE, FALSE_SPECIFICITY, OVERCONFIDENCE, NO_NARRATIVE_VOICE, PREDICTABLE_PEDAGOGY, EMOTIONAL_FLATNESS, INCONSISTENT_VOICE, MISSING_WHY_LAYER, DECORATIVE_CULTURE, COLD_PEDAGOGY}

### Strengths
- {strength 1}
- {strength 2}
- {strength 3}

### Issues
- **[Category]** {specific issue with line/example}
- **[Category]** {specific issue with line/example}

### Examples
{Quote 1-2 specific problematic or exemplary passages}

> "{quoted text}"
- Issue: {what's wrong}
- Fix: {how to fix}

### Recommendation
{✅ PASS / ⚠️ NEEDS IMPROVEMENT / ❌ REWRITE}

### Action Items
1. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)
2. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)
3. {specific, actionable fix} [SAFE/RISKY]
   - ✅ FIXED / ❌ SKIPPED / ⏳ MANUAL (if risky)

---

{Repeat for each module}

---

## Priority Fixes

### Critical (Must Fix)
{List modules with score < 3 or word salad}

### Important (Should Fix)
{List modules with score = 3}

### Optional (Nice to Have)
{List modules with score = 4 but minor issues}

---

## Patterns Across Level

### Common Strengths
- {pattern seen in multiple modules}
- {pattern seen in multiple modules}

### Common Issues
- {pattern seen in multiple modules}
- {pattern seen in multiple modules}

### Recommendations
1. {level-wide improvement suggestion}
2. {level-wide improvement suggestion}
3. {level-wide improvement suggestion}
```

## Scoring Scale

| Score | Rating     | Meaning                                   |
| ----- | ---------- | ----------------------------------------- |
| 5     | Excellent  | No issues, exemplary quality              |
| 4     | Good       | Minor issues, overall strong              |
| 3     | Acceptable | Several issues, needs improvement         |
| 2     | Poor       | Major issues, requires significant rework |
| 1     | Critical   | Fundamental flaws, complete rewrite       |

## Example Usage

```bash
# Review all A1 modules
/review-content a1

# Review single module
/review-content a2 19

# Review range
/review-content b1 1-10

# Review checkpoint modules in A1
/review-content a1 10 20 34
```

## Performance Notes

- **Single module:** ~30 seconds
- **10 modules:** ~5 minutes
- **Full level (34 modules):** ~15 minutes
- **Full level (80 modules):** ~40 minutes

For large batches, the command will show progress:

```
Reviewing A1...
[1/34] Module 01... ✅ PASS (4.5/5)
[2/34] Module 02... ⚠️ NEEDS WORK (3/5)
...
```

## What Gets Checked

✅ **Checked:**

- Lesson content (instructional text)
- Examples and explanations
- Engagement boxes
- Topic consistency
- Language quality
- Pedagogical approach
- **Activities** (structural integrity, answer validity, linguistic accuracy)
- **External resources** (relevance, accessibility - checked in `docs/resources/external_resources.yaml`)
- **Vocabulary coverage** (B2+: content vocabulary exists in YAML)

❌ **Not Checked:**

- Vocabulary YAML enrichment quality (separate audit)
- Metadata YAML (separate audit)
- Self-assessment sections

---

## Vocabulary Coverage Check (B2+)

**For B2+ modules (no embedded vocabulary tables):**

### Step: Verify Vocabulary Alignment

1. **Check YAML exists:**
   ```bash
   ls curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
   ```

2. **Identify content vocabulary:**
   - Extract key Ukrainian terms from module content
   - Focus on: new terminology, example sentences, dialogues

3. **Compare against YAML:**
   - All content vocabulary should exist in YAML
   - Flag missing terms as action items

4. **Action Items for Missing Vocabulary:**
   ```yaml
   # Add to {level}/vocabulary/{slug}.yaml
   - lemma: missing_word
     ipa: ''
     translation: ''
     pos: noun
     gender: m
   ```

5. **After adding, run:**
   ```bash
   .venv/bin/python scripts/enrich_yaml_vocab.py path/to/file.yaml
   .venv/bin/python scripts/global_vocab_audit.py --level {level}
   ```

**Note:** This is a SAFE FIX - vocabulary can be added without affecting module content.

## Important Notes

1. **Focus on teaching quality**, not just format
2. **Be specific** - quote actual problematic text
3. **Provide actionable fixes** - not vague suggestions
4. **Score honestly** - don't inflate for "effort"
5. **Check both languages** - Ukrainian examples AND English explanations
6. **Context matters** - what's good at A1 may be weak at C1
7. **Auto-fix safe issues** - apply safe fixes, run audit, verify pass
8. **Save to review/ folder** - don't append to audit/ folder (that's for automated audit reports)

## Red Flags (Auto-fail)

These trigger automatic REWRITE recommendation:

- ❌ **Template compliance failure:** Module doesn't follow appropriate template structure
- ❌ Word salad detected
- ❌ Overall score < 2/5
- ❌ Teaching wrong grammar for level
- ❌ Examples completely unrelated to topic
- ❌ No actual teaching content (just filler)
- ❌ Contradictory explanations
- ❌ **Unnatural Language Mixing:** (e.g., "The **чоловiк** is walking" -> BAD. "The word for man is **чоловік**" -> GOOD).
- ❌ **Pedagogical Leaps:** Testing material that wasn't taught.
- ❌ **Activity Structural Errors:** Duplicate items, mixed syntax, broken format
- ❌ **Multiple Valid Answers:** Activity accepts only one answer when others are linguistically valid
- ❌ **Incorrect "Correct" Answer:** The marked answer is grammatically wrong
- ❌ **Unrelated Resources:** YouTube/blog links don't match module topic
- ❌ **Dry Content (B1+):** 2+ dryness flags triggered (textbook voice, no cultural anchors, generic examples)
- ❌ **AI Slop (Section 15):** ChatGPT default voice, bullet point barrage (>50%), Wikipedia tone, engagement box faker (>50% restate content)
- ❌ **LLM Fingerprint Score 1/5 (B1+):** Auto-fail red flags from Section 15 detected

## Common Activity Issues (Examples)

### Issue 1: Multiple Valid Answers

```markdown
## fill-in: Transform to Perfective

1. читати → [___]
   > [!answer] прочитати
   > [!options] прочитати | читати | почитати
```

**Problem:** "почитати" is ALSO a valid perfective (means "to read for a while"). Activity wrongly treats it as incorrect.
**Fix:** Rephrase to "Give the COMPLETIVE perfective" or add note "result-focused form".

### Issue 2: Mixed Activity Syntax

```markdown
## fill-in: Transform to Perfective

7. говорити | \_\_\_ (suppletive pair)
   > [!error] suppletive pair
   > [!answer] сказати
   > [!explanation] Говорити/сказати use different roots.
```

**Problem:** `[!error]` and `[!explanation]` are error-correction syntax, not fill-in syntax.
**Fix:** Use only `[!answer]` and `[!options]` for fill-in activities.

### Issue 3: Duplicate Items

```markdown
7. розуміти → [___]
8. готувати → [___]
9. розуміти → [___] ← DUPLICATE
10. готувати → [___] ← DUPLICATE
```

**Problem:** Items 7-8 appear twice (copy-paste error).
**Fix:** Remove duplicates.

### Issue 4: Unrelated External Resources

**NOTE:** Resources are in `docs/resources/external_resources.yaml`, NOT markdown.

```yaml
# In external_resources.yaml
a1-09-food-and-drinks:
  youtube:
    - title: "Cat Videos Compilation"  # ← UNRELATED
      url: "https://youtube.com/..."
      relevance: "high"
```

**Problem:** Resource has nothing to do with Ukrainian learning.
**Fix:** Edit `external_resources.yaml` - replace with relevant Ukrainian learning content or remove the entry.
