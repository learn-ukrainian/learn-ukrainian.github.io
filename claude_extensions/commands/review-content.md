# Review Content Quality & Auto-Improve to 10/10

> **CRITICAL:** Follow this checklist EXACTLY. Do not improvise. Do not invent new criteria. Do not skip steps. Your goal is **elevating content to 10/10** - not just reporting issues.

> **⚠️ ALWAYS use `.venv/bin/python` - NEVER use `python3` or `python` directly!**

**MANDATE:** Evaluate module content for educational quality, coherence, and pedagogical soundness. **Then immediately fix all issues to achieve 10/10 scores.**

> **Complete workflow integration:** See **`docs/B1-PLUS-MODULE-WORKFLOW.md`** - Content Quality Review section for:
> - When to use content quality review (optional, recommended before release)
> - Integration with 4-stage module creation pipeline
> - How to interpret scores (0-10 scale, 8 dimensions)
> - Fixing content quality issues

---

## 🎯 Critical Sections Index (DO NOT SKIP)

**Must-check sections in order of importance:**

1. **Section 0:** Template Compliance (lines 148-214) → Auto-fail if violated
2. **Section 8:** Activity Quality (lines 276-337) → AUTO-FAIL for structural errors, wrong answers
3. **Section 15:** Richness Red Flags (lines 797-864) → AUTO-FAIL for AI slop
4. **Section 9:** Red Flags (lines 341-349) → Multiple auto-fail conditions
5. **Section 13:** LLM Fingerprint Detection (lines 534-762) → B1+ critical
6. **Section 10:** Content Richness (lines 350-458) → B1+ critical
7. **Sections 1-7:** Standard scoring criteria (lines 217-273)
8. **Section 12:** Dryness Flags (lines 512-528) → 2+ flags = rewrite
9. **Section 14:** Human Warmth (lines 765-793) → <2 markers = fail

**⚠️ CHECKPOINT REMINDER:** Before generating your report, verify you have evaluated ALL 9 critical sections above.

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
`docs/ACTIVITY-YAML-REFERENCE.md`

**Partial Example (Quiz only):**

```yaml
module: 11-aspect-in-imperatives
level: B1
activities:
  - type: quiz
    title: 'Вибір аспекту'
    items:
# ... (see ACTIVITY-YAML-REFERENCE.md for full syntax)
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

> **EXCEPTION:** If module explicitly teaches ABOUT Russianisms/Surzhyk (e.g., C1 metalanguage module), Russian forms are ALLOWED when marked as incorrect examples.

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

> **EXCEPTION:** If module explicitly teaches ABOUT calques (e.g., C1 stylistics module), calques are ALLOWED when marked as incorrect examples.

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
- **The "Why":** Does the module explain _why_ we are learning this right now? (Motivation/Relevance).

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
> **AUTO-FAIL conditions:** Wrong answers, multiple valid answers treated as incorrect, duplicate items, broken format, poor quality activities.
> **DO NOT SKIP THIS SECTION.** Activities are the primary learning tool.

---

**8. Activity Quality** (Critical Check - 5-Dimension Validation)

Review ALL activities from the appropriate source:

- **YAML file** (if `activities/{module-slug}.yaml` exists): Structured format, check YAML validity
- **MD file** (legacy): Check embedded activity sections after `## Activities` or `## Вправи`

**Deterministic Quality Checks:**

The system includes automated quality checks in `scripts/audit/checks/activity_quality.py`:
- `analyze_sentence_variety()` - detects mechanical repetition patterns
- `estimate_vocabulary_difficulty()` - flags vocabulary too easy/hard for level
- `analyze_distractor_quality()` - checks if options are plausible
- `check_natural_ukrainian_markers()` - detects pronoun overuse, calques, unnatural constructions
- `estimate_cognitive_load()` - evaluates task complexity

These checks provide instant feedback but don't replace human semantic validation below.

---

**8a. Structural Integrity** (Foundation - Auto-fail if violated)

- No duplicate items (same question appears twice)
- No mixed activity types (e.g., `[!error]` syntax inside a `fill-in` activity)
- Correct callout format for activity type (see `docs/ACTIVITY-YAML-REFERENCE.md`)
- Item count matches level requirements (see MODULE-RICHNESS-GUIDELINES-v2.md)
- YAML syntax valid (if using YAML format)

**Auto-fail violations:**
- ❌ Duplicate items in same activity
- ❌ Wrong activity type syntax mixed in
- ❌ Broken YAML format
- ❌ Item count below minimum for level

---

**8b. Grammar & Linguistic Correctness + Naturalness** (Semantic Quality)

**Correctness Checks:**
- **Single-answer activities:** Only ONE correct answer exists linguistically
  - Flag: "читати → прочитати" when "почитати" is also valid perfective
  - Flag: Fill-in where multiple grammatical options work
- **Multi-answer activities (`select`):** All valid answers are included
- **Error-correction:** The "error" is genuinely wrong, not just stylistic
- Ukrainian spelling is correct
- Grammar forms are correct (case endings, verb conjugations)
- No Russisms in options or answers

**Naturalness Assessment (1-5 Scale):**

Evaluate if Ukrainian content sounds authentic vs robotic/translated:

**1 = Robotic/Translated**
- Direct English syntax patterns
- Calques ("робити сенс" instead of "мати сенс")
- Unnatural formality ("Яка є ціна?" instead of "Скільки коштує?")
- Example: "Яке слово є правильним для завершення речення?" (stiff, pedagogical)

**2 = Unnatural**
- Grammatically correct but stilted
- Overuse of subject pronouns (я, він, вона when unnecessary)
- Rigid SVO word order without variation
- Lack of natural discourse markers (ну, от, взагалі)
- Example: "Я маю книгу. Я маю машину. Я маю час." (repetitive, pronoun-heavy)

**3 = Acceptable**
- Functional Ukrainian, no major errors
- Minor unnaturalness but comprehensible
- Adequate for learning context
- Example: "Виберіть правильний варіант" (correct but formulaic)

**4 = Natural**
- Sounds like native speaker wrote it
- Natural word order variations
- Appropriate discourse markers
- Conversational tone when appropriate
- Example: "Як правильно сказати?" (natural, conversational)

**5 = Highly Natural**
- Perfectly idiomatic Ukrainian
- Stylistically appropriate for context
- Cultural authenticity
- Example: "Уявіть: ви на ринку..." (engaging, culturally grounded)

**Deterministic Naturalness Markers (from activity_quality.py):**
- Pronoun density >1.5 per sentence → unnatural
- Missing discourse markers in 50+ word texts → check if too formal
- Calques detected ("робити сенс", "в моїй думці") → flag
- "Я маю" possessive → suggest "У мене є"

**Rubric for Review:**

For each activity with Ukrainian content, rate naturalness 1-5 and note issues:

```yaml
activity: "quiz-aspect-pairs"
naturalness_score: 3
issues:
  - "Overuse of pronouns: 8 in 5 sentences"
  - "Question feels stiff: 'Яке слово потрібне?' → suggest 'Що підходить?'"
suggestions:
  - "Remove unnecessary pronouns"
  - "Use more conversational phrasing"
```

**Auto-fail violations:**
- ❌ Grammatically incorrect "correct" answer
- ❌ Multiple valid answers but only one accepted
- ❌ Russianisms in Ukrainian content
- ❌ Naturalness score 1 (robotic) for B2+ content

---

**8c. Difficulty Calibration** (CEFR-Appropriate Challenge)

**Pedagogical Alignment:**
- Activity tests what was TAUGHT in this module (not future content)
- Activity type suits the learning goal:
  - Grammar → fill-in, error-correction, unjumble
  - Vocabulary → match-up, quiz, translate
  - Comprehension → true-false, select, cloze
- Clear, unambiguous instructions

**Difficulty Assessment:**

Evaluate if vocabulary and grammar complexity match CEFR level:

**too_easy** - Content is 1+ level below target
- A2 activity using only A1 vocabulary/grammar
- B1 activity with obvious answers requiring no thought
- Example: B1 fill-in: "Я ___ студент" (obvious "є", this is A2)

**appropriate** - Matches level expectations
- Vocabulary from module's taught words
- Grammar from current or previous modules
- Cognitive load matches level (not overwhelming, not trivial)
- Example: B1 fill-in: "Я ___ цю книгу вчора" (require aspect knowledge: прочитав vs читав)

**too_hard** - Content is 1+ level above target
- A2 activity using B1+ grammar not taught
- B1 activity using C1 abstract vocabulary
- Example: B1 fill-in: "Якби я ___ багатим..." (requires subjunctive, that's B2+)

**Deterministic Difficulty Markers (from activity_quality.py):**
- Average word length too short/long for level → flag
- Advanced vocabulary markers in lower levels → flag
  - C1+ markers in A1-B2: геополітичн, суверенітет, колоніаліз, мовознавство
- Cognitive load estimate: low/medium/high based on:
  - Text length
  - Sentence complexity (subordinate clauses)
  - Activity type complexity

**Rubric for Review:**

For each activity, assess difficulty appropriateness:

```yaml
activity: "fill-in-aspect-practice"
difficulty: "appropriate"
reasoning: "Uses taught aspect pairs (читати/прочитати), vocabulary from module, sentences 8-12 words (B1 target)"
vocab_difficulty_check: "appropriate"  # from deterministic check
cognitive_load: "medium"               # from deterministic check
```

**Flag if:**
- ⚠️ Difficulty mismatch: "too_easy" or "too_hard" for >20% of activities
- ⚠️ Testing untaught material (grammar or vocabulary not in module or prior modules)
- ⚠️ Cognitive load "high" for A1-A2 activities

**Auto-fail violations:**
- ❌ Testing untaught material (grammar not covered)
- ❌ B2+ grammar in A1-A2 activities

---

**8d. Distractor Quality** (Multiple-Choice Plausibility)

For activities with options (quiz, fill-in, error-correction, translate, select):

**Distractor Requirements:**
- Distractors are plausible but genuinely wrong
- Same word class as correct answer (all verbs, all nouns, etc.)
- Target common learner errors (not random words)
- Appropriate difficulty (not obviously wrong without linguistic knowledge)

**Distractor Quality Scale (1-5):**

**1 = Nonsense**
- Different word class from answer
- Completely unrelated words
- Example: Question needs verb, options include nouns/adjectives
  - "Я ___ до Києва" → Options: їду (verb), стіл (noun), зелений (adj) ❌

**2 = Weak**
- Same word class but obviously wrong
- No plausible connection to correct answer
- Example: "Я ___ до Києва" → Options: їду, сплю, плаваю, кричу (all verbs but nonsense choices)

**3 = Acceptable**
- Plausible but not challenging
- Basic error types
- Example: "Я ___ до Києва" → Options: їду ✓, ходжу (walk, not ride), біжу (run), плаваю (swim)

**4 = Good**
- Targets common errors
- Requires grammatical knowledge to eliminate
- Example: "Я ___ до Києва" → Options: їду ✓, їжджу (habitual vs single trip), йду (on foot), піду (future)

**5 = Excellent**
- Pedagogically sound distractors
- All options are plausible in different contexts
- Tests fine-grained distinctions
- Example: "Вчора я ___ книгу" → Options: прочитав ✓ (perfective), читав (imperfective), почитав (perfective but different meaning), дочитав (finished reading)

**Deterministic Distractor Analysis (from activity_quality.py):**
- Word class matching: checks if verbs/nouns/adjectives mixed → flags mismatches
- Length plausibility: checks if distractors are similar length to answer
- Root relation: checks if distractors share roots with answer (good for aspect pairs)

**Rubric for Review:**

For each multiple-choice activity, rate distractor quality 1-5:

```yaml
activity: "quiz-aspect-choice"
distractor_quality: 4
analysis:
  - "All options are verbs (good)"
  - "Targets perfective/imperfective confusion (pedagogically sound)"
  - "One distractor (почитав) is plausible but wrong meaning (good challenge)"
deterministic_check:
  word_class_match: true
  length_plausible: true
  related_to_answer: 3/3 distractors share root
issues: []
```

**Auto-fail violations:**
- ❌ **Spoiler Hints:** The hint gives away the answer
  - Example: `Answer: cat`, `Hint: It is a c_t` ❌
- ❌ **Nonsense Options:** Distractors illogical or obviously wrong (quality score 1)
  - Example: `Select: Apple`, Options: `Apple`, `Car`, `Moon`, `Sock` ❌

**Exception: Gender Agreement Hints (ALLOWED)**

English hints for possessives like `(my)`, `(his)`, `(her)`, `(our)`, `(their)`, `(your formal/plural)` are **allowed** when the activity tests **gender agreement**. These hints tell the student WHICH possessive to use, but they must still select the correct GENDER form.

Example of allowed hint:
- `Це ___ книга. (my)` → Options: `мій`, `моя`, `моє`, `мої`
- The hint `(my)` is needed because without it, the sentence could use any possessive
- The student must still know that `книга` is feminine → `моя`

---

**8e. Engagement Quality** (Cultural Relevance & Interest)

**NEW DIMENSION:** Evaluate if activities are interesting and culturally relevant.

**Engagement Scale (1-5):**

**1 = Boring/Generic**
- Disconnected from Ukrainian culture
- Generic "textbook" examples with no context
- Example: "The table is big." / "John eats an apple." (culturally neutral, no interest)

**2 = Low Engagement**
- Functional but uninspiring
- No cultural context
- Example: "Виберіть правильний варіант" without interesting sentence content

**3 = Neutral**
- Adequate content, some context
- Minor cultural references
- Example: "Я їду до Києва" (mentions Ukrainian city but no deeper context)

**4 = Engaging**
- Culturally relevant content
- Interesting topics (history, culture, contemporary issues)
- Relatable scenarios
- Example: "Київське метро — одне з найглибших у світі" (cultural fact, interesting)

**5 = Highly Engaging**
- Deeply rooted in Ukrainian culture
- Memorable topics (surprises, humor, contemporary relevance)
- Age-appropriate for adult learners
- Example: "Знаєте, чому українці кажуть 'на Україні' чи 'в Україні'? Це не просто граматика..." (cultural/political depth)

**Engagement Evaluation:**

For each activity, assess engagement level:

```yaml
activity: "translate-cultural-facts"
engagement_score: 4
reasoning: "Uses Ukrainian cultural references (борщ, вареники), mentions Carpathians, contemporary context"
cultural_authenticity: true
age_appropriate: true
issues: []
```

**Boring Patterns to Flag:**
- Generic English examples translated literally ("The book is on the table")
- No cultural names (use Oksana, Taras, not John, Mary)
- No cultural foods/places (use борщ, Київ, Карпати)
- Abstract grammar drills without context

**Engaging Patterns to Reward:**
- Ukrainian cultural references
- Contemporary topics relevant to learners
- Humor or surprising facts
- Real-world scenarios

---

**8f. Variety & Repetition** (Avoiding Mechanical Patterns)

**NEW DIMENSION:** Detect mechanical, repetitive sentence patterns.

**Variety Assessment:**

**Variety Score: 0-100%**
- **<40% = Mechanical** - Same structure repeated constantly
- **40-60% = Low Variety** - Noticeable repetition
- **60-80% = Good Variety** - Healthy mix of structures
- **80-100% = Excellent Variety** - Diverse, natural patterns

**Deterministic Variety Check (from activity_quality.py):**
- Analyzes sentence structure diversity (first 2 words + length)
- Flags if same pattern appears >30% of the time
- Flags if multiple sentences have identical length (mechanical)

**Example - MECHANICAL (Variety <40%):**
```
1. Я їду до Києва.
2. Я їду до Львова.
3. Я їду до Одеси.
4. Я їду до Харкова.
```
- Pattern "я_їду__4w" appears 4/4 times (100%)
- All sentences 4 words
- Variety score: ~25%

**Example - VARIED (Variety >70%):**
```
1. Я їду до Києва на потязі.
2. Вона летить до Львова завтра.
3. Ми приїхали до Одеси вчора.
4. Вони подорожують до Харкова щомісяця.
```
- Different subjects (я, вона, ми, вони)
- Different verbs (їду, летить, приїхали, подорожують)
- Different sentence lengths (6, 6, 6, 5 words - acceptable variation)
- Variety score: ~100%

**Rubric for Review:**

For each activity with 5+ sentences, assess variety:

```yaml
activity: "fill-in-motion-verbs"
variety_score: 65
patterns:
  - "я_їду__6w: appears 2/8 times (25%)"
  - "він_поїхав__5w: appears 2/8 times (25%)"
issues:
  - "Slight repetition of 'я їду' pattern"
suggestions:
  - "Vary subjects more (use ми, вони, вона)"
overall: "Acceptable variety, minor repetition"
```

**Flag if:**
- ⚠️ Variety score <40% (mechanical)
- ⚠️ Same sentence starter used 5+ times in a row
- ⚠️ All sentences identical length (indicates template generation)

---

**8g. External Resources**

**NOTE:** Resources are stored in `docs/resources/external_resources.yaml` (NOT in markdown files).

When reviewing, check the YAML file for this module's resources:

- YouTube videos are relevant to module topic
- URLs are valid and accessible
- Resources match level (A1 shouldn't link C1 content)
- No duplicate resources across modules without reason
- Blog/article links are from reputable Ukrainian learning sources

If you find `> [!resources]` in a markdown file, it's stale (remove it - will be regenerated from YAML at build time).

---

**CEFR-Specific Quality Gates**

After evaluating all activities, check if module meets quality thresholds:

**B1 Quality Gates:**
- Minimum naturalness average: **3.5** (Acceptable+)
- Maximum difficulty inappropriate: **20%** (≤20% of activities too_easy or too_hard)
- Minimum engagement average: **3.0** (Neutral+)
- Minimum distractor quality average: **4.0** (Good)
- Minimum variety score average: **60%** (Good Variety)

**B2 Quality Gates:**
- Minimum naturalness average: **4.0** (Natural)
- Maximum difficulty inappropriate: **15%**
- Minimum engagement average: **3.5** (Neutral to Engaging)
- Minimum distractor quality average: **4.2** (Good+)
- Minimum variety score average: **65%**

**C1 Quality Gates:**
- Minimum naturalness average: **4.5** (Highly Natural)
- Maximum difficulty inappropriate: **10%**
- Minimum engagement average: **4.0** (Engaging)
- Minimum distractor quality average: **4.5** (Good to Excellent)
- Minimum variety score average: **70%**

**C2 Quality Gates:**
- Minimum naturalness average: **4.8** (Near-Native)
- Maximum difficulty inappropriate: **5%**
- Minimum engagement average: **4.5** (Highly Engaging)
- Minimum distractor quality average: **5.0** (Excellent)
- Minimum variety score average: **75%**

**A1-A2 Quality Gates:**
- No strict quality gates (scaffolding phase)
- Focus on correctness over naturalness
- Engagement/variety encouraged but not required

**Gate Evaluation:**

If module FAILS quality gates, note in report:

```yaml
quality_gate_evaluation:
  level: B2
  naturalness_avg: 3.8  # FAIL (need 4.0)
  difficulty_appropriate: 78%  # PASS (need ≥85%)
  engagement_avg: 3.6  # PASS (need 3.5)
  distractor_quality_avg: 4.3  # PASS (need 4.2)
  variety_avg: 68%  # PASS (need 65%)

  result: FAIL
  failed_gates: ["naturalness"]
  recommendation: "Rewrite activities with robotic/translated phrasing (scores 1-2)"
```

---

**Activity Red Flags (Auto-fail Summary):**

- ❌ **Structural:** Duplicate items, wrong syntax, broken format
- ❌ **Correctness:** Wrong answer, multiple valid answers not accepted
- ❌ **Linguistic:** Russianisms, spelling errors, grammar errors in correct answer
- ❌ **Difficulty:** Testing untaught material, B2+ grammar in A1-A2
- ❌ **Distractors:** Nonsense options (quality score 1), spoiler hints
- ❌ **Naturalness:** Score 1 (robotic) for B2+ content
- ❌ **Variety:** Score <40% (mechanical repetition)
- ❌ **Resources:** Broken URLs, irrelevant content

---

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
- **Pass:** Uses transitional phrases (_However, For example, In this context, Consequently_).
- **Fail:** Abrupt topic shifts without signaling. Paragraphs that start with definitions immediately after unconnected examples.

**11b. Naturalness Metric (The "Uncanny Valley" Check)**

- **Check (English Instructions):** Does it sound like a friendly tutor or a database export?
  - ❌ _Robotic:_ "Do not use this form. It is incorrect."
  - ✅ _Human:_ "Avoid this form—it sounds unnatural to native ears."
- **Check (Ukrainian Content):** **Euphony (Милозвучність).**
  - ❌ _Clunky:_ "В учителі є..." (Vowel clash)
  - ✅ _Euphonic:_ "У вчителя є..." (Alternation rules respected)

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
  - ❌ _Robotic:_ "It is important that you do not forget..."
  - ✅ _Human:_ "It's important that you don't forget..."
- **Instruction Simplicity:** English explanations should be simple (B1/B2 level).
  - ❌ _Dense:_ "The semantic properties of the aspectual pair denote..."
  - ✅ _Simple:_ "This pair shows us the difference between..."

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

| Score | Rating       | Action                           |
| ----- | ------------ | -------------------------------- |
| 4/4   | ✅ Excellent | Pass - warm, human voice         |
| 3/4   | ✅ Good      | Pass - acceptable warmth         |
| 2/4   | ⚠️ Adequate  | ENRICH - add missing patterns    |
| 1/4   | ❌ Cold      | REWRITE - lacks teacher presence |
| 0/4   | ❌ Robotic   | REWRITE - pure AI voice          |

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
>
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

**Step 3: Generate Initial Assessment**

For each module, first evaluate current state:

```
## Module {num}: {title}

**INITIAL SCORES (before fixes):**
Coherence {X}/5 | Relevance {X}/5 | Educational {X}/5 | Language {X}/5 | Pedagogy {X}/5 | Immersion {X}/5 | Activities {X}/5 | Richness {X}/5 | Humanity {X}/5 | LLM Fingerprint {X}/5 | **Overall {X}/5**

**Template:** {template_name} | **Compliance:** ✅ PASS / ❌ FAIL

**AI Detection Flags:** {list any triggered}

**Issues Identified:**
1. {Category} - {specific issue with quote}
2. {Category} - {specific issue with quote}
3. {Category} - {specific issue with quote}

**Planned Fixes:** {count} changes from Categories 1-7
```

**Step 4: Apply ALL Fixes to Achieve 10/10**

> **CRITICAL MANDATE:** Your goal is a perfect **10/10** score (5/5 on every criterion).
> Do not settle for "PASS" (4/5) or "GOOD" - aim for **EXCELLENT**.
> **Every identified issue MUST be fixed immediately.** Do not just report it.

**NEW PHILOSOPHY:**
- ❌ OLD: "Report issues, apply only safe fixes"
- ✅ NEW: "Fix everything to 10/10, verify with audit"

---

### Fix Categories

**Category 1: Structure & Format (ALWAYS SAFE - Apply NOW)**

- **Duplicate Activities:** If YAML activities file exists, **DELETE** inline `## Activities` section
- **Cleanliness:** Remove editing notes, fix typos, delete exact duplicate paragraphs
- **Formatting:** Fix markdown artifacts, broken tables, inconsistent headers
- **Euphony:** Fix vowel clashes (у/в, і/й alternation)
- **Activity Syntax:** Fix mixed activity types, add missing callouts

**Category 2: Language Quality (ALWAYS SAFE - Apply NOW)**

> **EXCEPTION:** If module explicitly teaches ABOUT Russianisms/Surzhyk/Calques (e.g., C1 metalanguage), these forms are ALLOWED when clearly marked as incorrect examples.

- **Russianisms:** Replace all detected Russianisms with correct Ukrainian
  - кушать → їсти, да → так, кто → хто, нету → немає
  - Skip if module is teaching about Russianisms as pedagogical content
- **Calques:** Replace English loan translations
  - робити сенс → мати сенс, брати місце → відбуватися
  - Skip if module is teaching about calques as pedagogical content
- **Grammar Errors:** Fix case endings, verb conjugations, agreement
- **Spelling:** Correct all Ukrainian/English spelling errors
- **Precision:** Replace vague terms (thing, stuff) with specific vocabulary

**Category 3: Pedagogy & Flow (SAFE IF <30% CHANGE - Apply NOW)**

- **Transitions:** Add connecting phrases between abrupt section jumps
- **Tone:** Rewrite robotic sentences to conversational (keep facts, change voice)
- **Examples:** Replace generic examples with specific Ukrainian cultural references
  - "магазин" → "Бесарабський ринок у Києві"
  - "John" → "Тарас", "Mary" → "Оксана"
- **Explanations:** Add "why" layer to surface-level definitions
- **Emotional Hooks:** Add questions, metaphors, real-world scenarios
- **Encouragement:** Add direct address, validation phrases (you can do this!)

**Category 4: Content Enrichment (SAFE IF <40% CHANGE - Apply NOW)**

- **Sensory Detail:** Replace vague descriptions with vivid imagery
  - "готує їжу" → "Запах борщу наповнює кухню"
- **Cultural Depth:** Add Ukrainian place names, traditions, historical context
- **Storytelling:** Transform dry facts into narrative moments
- **Proverbs/Idioms:** Weave in relevant Ukrainian sayings (natural, not forced)
- **Surprise Moments:** Add counterintuitive insights, unexpected connections
- **Engagement Boxes:** Replace filler boxes with valuable insights

**Category 5: Activity Quality (SAFE IF FIXING ERRORS - Apply NOW)**

- **Correct Answers:** Fix grammatically wrong "correct" answers
- **Multiple Valid Options:** Rephrase questions or mark all valid answers correct
- **Distractor Quality:** Replace nonsense options with plausible challenges
- **Naturalness:** Rewrite robotic Ukrainian to idiomatic phrasing
- **Variety:** Diversify sentence patterns (subjects, verbs, lengths)
- **Engagement:** Replace generic examples with cultural content
- **Duplicate Items:** Remove exact duplicates

**Category 6: Human Warmth & Voice (SAFE - Apply NOW)**

- Add direct address markers (you, ти/ви, давайте)
- Add encouragement phrases (з практикою це стане природним)
- Add confusion anticipation (студенти часто плутають...)
- Add real-world validation (після цього модуля ви зможете...)
- Fix certainty overload (завжди → часто, never → rarely + explanation)
- Add hedging where appropriate (generally, typically, often)

**Category 7: AI Slop Removal (SAFE - Apply NOW)**

- Remove LLM clichés:
  - "It's important to note that..." → direct statement
  - "Let's dive into..." → conversational intro
  - "In conclusion..." → natural transition
- Remove ChatGPT scaffolding ("Welcome to Module X! In this lesson...")
- Break up bullet point barrages (>5 in a row) with narrative prose
- Rewrite encyclopedic definitions in teaching voice
- Remove/replace useless engagement boxes

---

### Risky Fixes (REQUIRE USER APPROVAL - Flag Only)

**Only report these for manual review:**

- Rewriting >50% of module content
- Changing core pedagogical approach (PPP → TBL)
- Moving entire sections (structural reorganization)
- Changing module focus/topic
- Removing entire sections (>200 words)

---

### Fix Application Workflow

**For EACH criterion scored <5/5:**

1. **Identify specific issues** (quote problematic text)
2. **Apply appropriate fix** from Categories 1-7 above
3. **Verify fix doesn't break structure** (check markdown validity)
4. **Continue to next issue**

**After ALL fixes applied:**

5. Run `.venv/bin/python scripts/audit_module.py {file_path}`
6. If audit FAILS → Revert last batch of changes, debug
7. If audit PASSES → Mark all fixes ✅ APPLIED
8. Re-score module (should now be 10/10 or close)

---

### Fix Status Tracking

For each fix applied, mark:

- ✅ **APPLIED** - Fix successful, audit passes
- ⚠️ **PARTIAL** - Fix applied but didn't fully resolve (needs iteration)
- ❌ **REVERTED** - Fix broke audit, rolled back
- ⏳ **FLAGGED** - Risky fix, needs user approval

---

**Step 5: Re-Score After Fixes & Generate Final Report**

After applying all fixes, re-evaluate the module:

```
## Module {num}: {title} - FINAL REPORT

**FINAL SCORES (after fixes):**
Coherence {X}/5 (was {Y}) | Relevance {X}/5 (was {Y}) | Educational {X}/5 (was {Y}) | Language {X}/5 (was {Y}) | Pedagogy {X}/5 (was {Y}) | Immersion {X}/5 (was {Y}) | Activities {X}/5 (was {Y}) | Richness {X}/5 (was {Y}) | Humanity {X}/5 (was {Y}) | LLM Fingerprint {X}/5 (was {Y}) | **Overall {X}/5** ⬆️ from {Y}/5

**Status:** ✅ 10/10 ACHIEVED / ⚠️ 9/10 (1 minor issue remains) / ⏳ 8/10 (needs manual review)

**Fixes Applied:** {count} changes
- ✅ {Category 1}: {brief description} (e.g., "Removed 8 LLM clichés, added conversational tone")
- ✅ {Category 2}: {brief description} (e.g., "Fixed 3 Russianisms, corrected case endings")
- ✅ {Category 3}: {brief description} (e.g., "Added transitions between 5 sections")
- ✅ {Category 4}: {brief description} (e.g., "Enriched 7 generic examples with Ukrainian culture")
- ✅ {Category 5}: {brief description} (e.g., "Fixed 2 wrong answers, improved distractor quality")
- ✅ {Category 6}: {brief description} (e.g., "Added 12 direct address markers, 3 encouragement phrases")
- ✅ {Category 7}: {brief description} (e.g., "Removed ChatGPT scaffolding, broke up bullet barrages")

**Remaining Issues (if any):**
- ⏳ {Risky fix description} - needs user approval
- ⚠️ {Minor issue} - acceptable at current level

**Audit Status:** ✅ PASSED (`.venv/bin/python scripts/audit_module.py {file_path}`)
```

**Step 6: Save Review Files**

For each module, save detailed review to:
`curriculum/l2-uk-en/{level}/review/{module_number}-{slug}-review.md`

Example: `curriculum/l2-uk-en/a1/review/03-the-gender-code-review.md`

**Step 7: Generate Final Summary**

After reviewing and fixing all modules in scope:

```
# Content Quality Summary - Auto-Improvement Report

**Level:** {level}
**Modules Processed:** {count}
**Date:** {today}

---

## Results

| Status | Before Fixes | After Fixes | Improvement |
|--------|--------------|-------------|-------------|
| ✅ 10/10 (5/5 all criteria) | {count} | {count} | +{delta} |
| ⚠️ 9/10 (4.5+/5 avg) | {count} | {count} | +{delta} |
| ⏳ 8/10 (needs manual review) | {count} | {count} | +{delta} |
| ❌ <8/10 (incomplete) | {count} | {count} | -{delta} |

**Average Score Improvement:** {before_avg}/5 → {after_avg}/5 (↑ {delta})

**Total Fixes Applied:** {count}
- Category 1 (Structure): {count} fixes
- Category 2 (Language): {count} fixes
- Category 3 (Pedagogy): {count} fixes
- Category 4 (Enrichment): {count} fixes
- Category 5 (Activities): {count} fixes
- Category 6 (Warmth): {count} fixes
- Category 7 (AI Slop): {count} fixes

---

## Module Reports

{Full report for each module}

---

## Detailed Module: {module_number} - {title}

**Overall Score:** {X}/5 {stars}
**Template:** {template_name} | **Compliance:** ✅ PASS / ❌ FAIL

### Scores Breakdown
- Template Compliance: ✅ PASS / ❌ FAIL {reason}
- Coherence: {X}/5 {reason}
- Relevance: {X}/5 {reason}
- Educational: {X}/5 {reason}
- Language: {X}/5 {reason}
- Pedagogy: {X}/5 {reason}
- Immersion: {X}/5 {reason}
- Activities: {X}/5 {reason}
- Richness: {X}/5 {reason} (B1+ only, N/A for A1/A2)
- Humanity: {X}/5 {reason}
- LLM Fingerprint: {X}/5 {reason} (B1+ critical, A1/A2 informational)
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
    - title: 'Cat Videos Compilation' # ← UNRELATED
      url: 'https://youtube.com/...'
      relevance: 'high'
```

**Problem:** Resource has nothing to do with Ukrainian learning.
**Fix:** Edit `external_resources.yaml` - replace with relevant Ukrainian learning content or remove the entry.
