# /activity-validate

**Multi-dimensional activity quality validation** for Ukrainian curriculum content.

Validates activities across 5 quality dimensions:
1. **Grammar** - Linguistic correctness
2. **Naturalness** - Authentic Ukrainian, not robotic
3. **Difficulty** - Appropriately challenging for CEFR level
4. **Engagement** - Culturally relevant and interesting
5. **Distractors** - Pedagogically sound incorrect options (for multiple-choice)

## Usage

```
/activity-validate <module-path>
/activity-validate curriculum/l2-uk-en/b1/17-motion-coming-going.md
/activity-validate b1/17        # Shorthand
/activity-validate b1 2-5       # Batch mode
```

---

## Batch Mode (Multiple Modules)

**When arguments contain a range (e.g., `b1 2-5`):**

Use the **subagent pattern** to process each module with fresh context:

```
For each module in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Agent prompt: "Run /activity-validate {level} {module_num} - validate single module"
  3. Wait for agent completion
  4. Log result (validated/pending/failed)
  5. Continue to next module (fresh context)
```

**Example batch execution:**
```
/activity-validate b1 2-5

→ Task agent: /activity-validate b1 2 → ✅ Validated (12/12 passed, 0 warnings)
→ Task agent: /activity-validate b1 3 → ✅ Validated (8/8 passed, 2 naturalness warnings)
→ Task agent: /activity-validate b1 4 → ⚠️ Validated (6/8, 2 deleted for poor distractors)
→ Task agent: /activity-validate b1 5 → ✅ Validated (10/10 passed, 1 engagement note)

Summary: 4/4 validated, 2 items deleted, 2 warnings logged
```

---

## Single Module Mode

## Purpose

Validate activity quality across **5 dimensions** using manual semantic validation with embedded quality rubrics.

**Workflow position:**
```
/module-create → /activity-validate → /review-content → /module-stage-4
```

## Instructions

### Step 1: Locate Queue File

Find the activity quality queue file for the specified module:
```
curriculum/l2-uk-en/{level}/queue/{module}-quality.yaml
```

If no queue file exists, run the generator:
```bash
.venv/bin/python scripts/generate_activity_quality_queue.py {module.md}
```
This will create the queue file in the `queue/` subfolder.

**Options:**
- `--sample 25` - Sample 25% of items for faster validation (useful for large modules)

**Supported activity types:**
- `error-correction` - Validates error/corrected sentence pairs + distractors
- `fill-in` - Validates complete sentences
- `cloze` - Validates complete passages
- `unjumble` - Validates answer sentences
- `quiz` - Validates questions and all options (distractors)
- `translate` - Validates Ukrainian sentences and options
- `true-false` - Validates statements
- `select` - Validates statements and all options (distractors)

### Step 2: Read Queue

Load the YAML queue file. Each item has this structure:

```yaml
items:
  - activity: error-correction
    title: "Activity title"
    sentence_with_error: "Я прийшов до Львова потягом."
    error: "прийшов"
    answer: "приїхав"
    options: ["прийшов", "приїхав", "відійшов", "перейшов"]
    sentence_corrected: "Я приїхав до Львова потягом."
    module_topic: "Motion verbs with при-/від-"
    level: "B1"

    validate:
      # DIMENSION 1: Grammar (existing)
      error_is_real_mistake: null
      corrected_sentence_valid: null
      explanation: null
      confidence: null
      error_type: null

      # DIMENSION 2: Naturalness
      naturalness_score: null          # 1-5 scale
      naturalness_rating: null         # robotic/unnatural/acceptable/natural/highly_natural
      naturalness_issues: []
      naturalness_suggestion: null

      # DIMENSION 3: Difficulty
      difficulty_appropriate: null     # too_easy/appropriate/too_hard
      difficulty_reason: null
      vocabulary_difficulty: null      # too_easy/appropriate/too_hard
      grammar_complexity: null         # too_easy/appropriate/too_hard
      cognitive_load: null             # low/medium/high

      # DIMENSION 4: Engagement
      engagement_score: null           # 1-5 scale
      engagement_type: null            # cultural/practical/pop_culture/personal/intellectual/creative
      cultural_relevance: null         # high/medium/low
      interest_level: null             # high/medium/low
      engagement_suggestion: null

      # DIMENSION 5: Distractors (for multiple-choice only)
      distractor_quality: null         # 1-5 scale (null for non-MC)
      distractor_issues: []
      distractor_suggestions: []
```

### Step 3: Multi-Dimensional Validation

For each item, validate across all 5 dimensions using the rubrics below.

---

## DIMENSION 1: Grammar (Existing)

### Validate the ERROR is a real mistake

Check if `sentence_with_error` contains a genuine error:

**Real errors (flag as `error_is_real_mistake: true`):**
- **Russianisms:** кушать → їсти, ложить → класти, кто/что → хто/що
- **Surzhyk:** mixed Ukrainian-Russian grammar
- **Case errors:** wrong case after verb/preposition
- **Agreement errors:** gender/case/number mismatch
- **Calques:** "робити сенс" (make sense → "мати сенс")
- **Aspect errors:** wrong aspect for context
- **Motion prefix errors:** прийшов (by foot) vs приїхав (by vehicle)
- **Spelling:** non-existent words

**NOT real errors (flag as `error_is_real_mistake: false`):**
- Pedagogical simplifications appropriate for the level
- Style/register differences (both forms acceptable)
- Regional variations (both standard Ukrainian)

### Validate the CORRECTED sentence is valid

Check if `sentence_corrected` is grammatically correct:

**Valid (`corrected_sentence_valid: true`):**
- Grammatically correct Ukrainian
- Natural word order
- Appropriate for the level
- No Russianisms/calques

**Invalid (`corrected_sentence_valid: false`):**
- Contains grammar errors
- Unnatural/awkward phrasing
- Contains Russianisms or calques
- Wrong case/aspect/agreement

### Grammar Confidence Levels

- **1.0** - Absolutely certain (clear Russianism, obvious case error)
- **0.9** - Very confident (standard grammar rules)
- **0.8** - Confident (context-dependent but clear)
- **0.7** - Somewhat confident (could be style choice)
- **< 0.7** - Flag for human review

---

## DIMENSION 2: Naturalness

**Goal:** Evaluate if the Ukrainian sounds authentic and conversational, not robotic or artificial.

### Scoring Scale (1-5)

* **5 - Highly Natural:** Sounds like native speaker conversation, idiomatic, flows naturally
* **4 - Natural:** Authentic Ukrainian, minor awkwardness acceptable for teaching
* **3 - Acceptable:** Grammatically correct but somewhat formal/stilted, pedagogically justifiable
* **2 - Unnatural:** Grammatically correct but sounds translated, overly literal, bookish
* **1 - Robotic:** Mechanically constructed, no native speaker would say this

### Rating Labels

* `highly_natural` (5)
* `natural` (4)
* `acceptable` (3)
* `unnatural` (2)
* `robotic` (1)

### Naturalness Red Flags

* Literal word-for-word translations from English
* Overuse of full pronouns when unnecessary
  - ❌ "Я хочу їсти. Я люблю їжу. Я завжди голодний."
  - ✅ "Хочу їсти. Люблю їжу. Завжди голодний."
* Bookish constructions in casual contexts
* Mechanical repetition of structures
* Lack of discourse markers where natural ("ну", "от", "взагалі")
* Unnatural word order (rigid SVO when Ukrainian is flexible)
* Overuse of passive voice (Ukrainian prefers active)

### Naturalness Boosters

* Idiomatic phrases: "як на мене" not "в моїй думці"
* Natural discourse markers: "ну", "от", "взагалі"
* Contextually appropriate register (casual vs formal)
* Natural ellipsis (omitting obvious subjects/objects)
* Ukrainian-specific constructions:
  - Dative-infinitive: "Мені треба йти" not "Я мушу йти"
  - Impersonal constructions: "Мені холодно" not "Я холодний"

### CEFR-Aware Naturalness Expectations

* **A1-A2:** Score 3+ acceptable (teaching explicit structures, simplification OK)
* **B1:** Score 3.5+ expected (transitioning to natural Ukrainian)
* **B2:** Score 4+ expected (should sound authentic)
* **C1-C2:** Score 4.5+ required (near-native naturalness)

### Example Validation

```yaml
naturalness_score: 2
naturalness_rating: unnatural
naturalness_issues:
  - "Overly literal translation: 'Я маю три книги' sounds translated"
  - "Native speakers prefer: 'У мене три книги' or 'У мене є три книги'"
naturalness_suggestion: "Replace with natural possessive: 'У мене є три книги'"
```

---

## DIMENSION 3: Difficulty Calibration

**Goal:** Assess if the activity difficulty matches the target CEFR level (not too easy, not too hard).

### Appropriateness Ratings

* `too_easy` - Below target level, no challenge
* `appropriate` - Matches level expectations
* `too_hard` - Above target level, frustrating

### Vocabulary Difficulty Benchmarks

* **A1:** ~750 cumulative words, everyday concrete nouns/verbs (хліб, вода, їсти, спати)
* **A2:** ~1,800 cumulative, basic abstract concepts (радість, думка, вчитися)
* **B1:** ~3,300 cumulative, discourse markers, idioms (втім, на жаль, мати на увазі)
* **B2:** ~5,940 cumulative, specialized vocabulary (геополітика, суверенітет, колонізація)
* **C1-C2:** ~12,000 cumulative, literary, professional (мовознавство, постколоніалізм)

### Grammar Complexity Benchmarks

* **A1:** Present tense, basic cases (nominative, accusative, locative)
* **A2:** All 6 cases, aspect basics, past/future tense
* **B1:** Aspect mastery, motion verbs, complex sentences
* **B2:** Passive voice, participles, all registers
* **C1-C2:** Stylistic nuances, literary constructions

### Cognitive Load Assessment

* `low` - Single-step task, familiar pattern recognition
* `medium` - Multi-step reasoning, some novelty, integration
* `high` - Complex integration, creative application, nuanced judgment

### Example Validation

```yaml
difficulty_appropriate: too_hard
difficulty_reason: "Uses C1-level vocabulary ('геополітичний', 'суверенітет') in B1 module. Grammar structures are B1-appropriate, but lexical density too high."
vocabulary_difficulty: too_hard
grammar_complexity: appropriate
cognitive_load: high
```

**Action:** Replace advanced vocabulary or flag for module revision.

---

## DIMENSION 4: Engagement & Cultural Relevance

**Goal:** Assess if the activity is interesting, motivating, and culturally relevant to Ukrainian language learners.

### Engagement Scoring Scale (1-5)

* **5 - Highly Engaging:** Culturally rich, personally relevant, emotionally resonant
* **4 - Engaging:** Interesting topic, good cultural connection
* **3 - Neutral:** Generic but acceptable, functional
* **2 - Boring:** Mechanical drill, no context, dated references
* **1 - Disengaging:** Culturally inappropriate, offensive, or demotivating

### Engagement Types

* `cultural` - Ukrainian history, traditions, festivals, cuisine (Holodomor, vyshyvanka, borscht)
* `practical` - Real-world scenarios (shopping at Silpo, Kyiv metro, ordering at кав'ярня)
* `pop_culture` - Modern Ukrainian music, cinema, games (S.T.A.L.K.E.R., The Witcher, Jamala, Onuka)
* `personal` - Family, hobbies, emotions, relationships
* `intellectual` - Ideas, philosophy, social issues (language policy, decolonization)
* `creative` - Storytelling, humor, wordplay

### Cultural Relevance Assessment

* **High:** Contemporary Ukraine, authentic references
  - Zhadan, Vakarchuk, Kurkov (literature)
  - Jamala, Skofka, Onuka (music)
  - Borshch, varenyky, salo, horilka (cuisine)
  - Vyshyvanka, pysanka, Tryzub (symbols)

* **Medium:** Universal topics with Ukrainian context
  - Family → Ukrainian naming traditions (patronymics)
  - Food → Ukrainian cuisine and meal customs

* **Low:** Generic scenarios with no cultural specificity
  - "I have a book" (no context)
  - "The weather is good" (generic)

### Age Appropriateness

* `children` - Elementary school (avoid in adult curriculum)
* `teens` - High school interests
* `adults` - Work, politics, philosophy, war, history
* `universal` - All ages

### Engagement Red Flags (Boring/Inappropriate)

* **Soviet-era clichés:** "pioneer", "kolkhoz", "комсомол"
* **Russian cultural references:** Moscow, Pushkin, Russian holidays
* **Outdated stereotypes:** Ukraine as "breadbasket", villagers in traditional dress
* **Culturally inappropriate:** Praising Russian imperialism, trivializing Holodomor
* **Boring drills:** "Translate: the book, the table, the chair, the pen, the notebook"
* **No context:** Random sentences with no thematic connection

### Engagement Boosters

* **Contemporary culture:** Jamala winning Eurovision 2016, Ukrainian IT sector, S.T.A.L.K.E.R. game
* **Historical depth:** Cossacks, Kyivan Rus, Mazepa, Shevchenko, Independence
* **Real-world utility:** Ordering at Lviv Coffee Manufacture, navigating Kyiv metro
* **Humor and wordplay:** Ukrainian puns, idioms (як сніг на голову)
* **Emotional resonance:** National pride, family traditions, wartime resilience

### Example Validation

```yaml
engagement_score: 5
engagement_type: pop_culture
cultural_relevance: high
interest_level: high
engagement_suggestion: "Excellent! Uses S.T.A.L.K.E.R. game reference that resonates with adult learners interested in Ukrainian gaming culture."
```

---

## DIMENSION 5: Distractor Quality (Multiple-Choice Only)

**Goal:** Evaluate if incorrect options (distractors) are pedagogically sound - plausible but wrong.

**Note:** This dimension only applies to activities with multiple-choice options:
- `quiz`
- `select`
- `translate`
- `error-correction` (when using [!options] callout)

For other activities (`fill-in`, `unjumble`, `cloze`, `true-false`), set all distractor fields to `null`.

### Quality Scoring (1-5)

* **5 - Excellent:** All distractors plausible, target common errors, same word class
* **4 - Good:** Most distractors plausible, some target errors
* **3 - Acceptable:** Distractors functional, some weak ones
* **2 - Weak:** Several nonsense options, too easy to eliminate
* **1 - Poor:** Nonsense distractors, random words, different word class

### Distractor Principles

#### 1. Same Word Class

* ✅ **Good:** книгу (Acc), книга (Nom), книги (Gen) ← all nouns, different cases
* ❌ **Bad:** книгу (noun), читати (verb), швидко (adverb) ← mixed classes, too obvious

#### 2. Target Common Errors

* **Aspect confusion:** прочитав vs читав
* **Case errors:** дати книгу другу vs дати книгу друг (nominative error)
* **Agreement errors:** моя книга vs мій книга (gender agreement)
* **Calques:** робити сенс vs мати сенс
* **Motion prefixes:** прийти vs приїхати (foot vs vehicle)

#### 3. Plausible but Wrong

* ✅ **Good:** "Я був в кіно вчора" vs "Я буду в кіно вчора" (tense error, plausible)
* ❌ **Bad:** "Я кіт в кіно вчора" (nonsense, no learner would choose)

#### 4. Appropriate Difficulty

* **A1-A2:** Distractors should be similar forms
  - книга/книгу/книги (case endings)
  - читав/читаю/читатиму (tense variations)

* **B1-B2:** Distractors should test nuances
  - прочитав/читав (aspect pairs)
  - прийшов/приїхав (motion prefix variations)

* **C1-C2:** Distractors should test stylistic choices
  - робити/виконувати/здійснювати (register/synonymy)

#### 5. Avoid

* Random words unrelated to context
* Multiple correct answers (both right)
* Distractors from wrong word class
* Trivially easy eliminations
* Nonsense non-words (unless testing spelling)

### Example: Excellent Distractors

```yaml
distractor_quality: 5
distractor_issues: []
distractor_suggestions: []
distractor_analysis: "All distractors are perfective/imperfective aspect pairs, targeting the most common B1 learner confusion. 'прочитав' (perfective past) vs 'читав' (imperfective past) tests aspect mastery. Other options ('прочитаю', 'читатиму') are future forms, plausible but wrong tense."
```

### Example: Poor Distractors

```yaml
distractor_quality: 2
distractor_issues:
  - "Distractor 'кіт' is a noun, not a verb - wrong word class"
  - "Distractor 'швидко' is an adverb - nonsense in this context"
  - "Only 1 of 3 distractors is plausible ('читатиму')"
distractor_suggestions:
  - "Replace 'кіт' with 'читатиму' (future tense, same verb)"
  - "Replace 'швидко' with 'прочитаю' (perfective future, aspect confusion)"
```

---

## Step 4: Apply Quality Gates

After validating all items, check if the module passes quality thresholds for the level:

### B1 Quality Gates

* `min_naturalness_avg`: **3.5** (acceptable+)
* `max_difficulty_inappropriate`: **20%** (no more than 20% activities too easy/hard)
* `min_engagement_avg`: **3.0** (neutral+)
* `min_distractor_quality` (for MC activities): **4.0** (good)

### B2 Quality Gates

* `min_naturalness_avg`: **4.0** (natural)
* `max_difficulty_inappropriate`: **15%**
* `min_engagement_avg`: **3.5**
* `min_distractor_quality`: **4.2**

### C1 Quality Gates

* `min_naturalness_avg`: **4.5** (highly natural)
* `max_difficulty_inappropriate`: **10%**
* `min_engagement_avg`: **4.0**
* `min_distractor_quality`: **4.5**

### C2 Quality Gates

* `min_naturalness_avg`: **4.8** (near-native)
* `max_difficulty_inappropriate`: **5%**
* `min_engagement_avg`: **4.5**
* `min_distractor_quality`: **5.0**

**If gates fail:** Module needs revision before passing validation.

---

## Step 5: Finalize using Python Script

**Do NOT write the audit file manually.** Use the provided Python script:

```bash
.venv/bin/python scripts/finalize_activity_quality.py {queue_file_path} "{notes}"
```

**Example:**
```bash
.venv/bin/python scripts/finalize_activity_quality.py \
  curriculum/l2-uk-en/b1/queue/17-motion-coming-going-quality.yaml \
  "2 items deleted (poor distractors), 1 naturalness warning"
```

The script will:
1. Generate the audit file with correct metadata
2. Preserve your validation notes and fixes
3. Auto-update the Review Report status
4. Clean up the queue file
5. Calculate quality gate scores

---

## Step 6: Apply Fixes (When Validation Finds Problems)

### Fix Actions by Problem Type

| Problem | Action | Example |
|---------|--------|---------|
| `error_is_real_mistake: false` | DELETE the item | Fake error |
| `corrected_sentence_valid: false` | FIX the answer only | Wrong correction |
| `naturalness_score < 2` (robotic) | REWRITE or FLAG | Sounds like Google Translate |
| `difficulty: too_hard` | SIMPLIFY vocabulary/grammar | C1 words in B1 module |
| `difficulty: too_easy` | INCREASE complexity or DELETE | A1 level in B2 module |
| `engagement_score < 2` (boring) | ADD context or REPLACE | Generic drill → Cultural context |
| `distractor_quality < 3` (weak) | FIX distractors | Wrong word class → Same class |
| `confidence < 0.7` | FLAG for human review | Uncertain, don't fix |

### Naturalness Fixes

**Robotic (score 1-2) - REWRITE:**
```yaml
# BEFORE:
sentence: "Я маю три книги і я читаю їх кожен день."

# AFTER (more natural):
sentence: "У мене три книги, читаю їх щодня."

# Changes:
- "Я маю" → "У мене" (natural possessive)
- Removed redundant "я" (ellipsis)
- "кожен день" → "щодня" (more natural)
```

### Difficulty Fixes

**Too Hard (C1 in B1) - SIMPLIFY:**
```yaml
# BEFORE:
sentence: "Геополітичне становище України впливає на економічний розвиток."

# AFTER (B1-appropriate):
sentence: "Міжнародне становище України впливає на економіку."

# Changes:
- "Геополітичне" → "Міжнародне" (B1 vocabulary)
- "економічний розвиток" → "економіку" (simpler)
```

### Engagement Fixes

**Boring (score 1-2) - ADD CULTURAL CONTEXT:**
```yaml
# BEFORE (generic):
sentence: "Я читаю книгу."

# AFTER (engaging):
sentence: "Я читаю новий роман Жадана 'Месопотамія'."

# Changes:
- Added contemporary Ukrainian author (cultural relevance)
- Specific book title (concrete context)
```

### Distractor Fixes

**Poor Distractors - FIX WORD CLASS:**
```yaml
# BEFORE (mixed word classes):
options:
  - читати (verb - infinitive)
  - книга (noun)
  - швидко (adverb)
  - читав (verb - past)

# AFTER (all same tense/aspect variations):
options:
  - читав (impf past)
  - прочитав (pf past)
  - читатиму (impf future)
  - прочитаю (pf future)

# Changes:
- All are forms of "читати"
- Tests aspect and tense understanding
- Plausible learner confusion
```

---

## Step 7: Required Reporting (CRITICAL)

**You MUST provide explicit reporting of all changes.** Do not just summarize - show exactly what you did.

### Report Format

```markdown
## Activity Quality Validation Report: B1-M17

### Summary
- **Items validated:** 14
- **Passed all dimensions:** 10
- **Warnings:** 3 (naturalness)
- **Deleted:** 1 (poor distractors)
- **Fixed:** 0

### Quality Gate Scores
- **Naturalness avg:** 3.8 / 3.5 required ✅
- **Difficulty appropriate:** 93% / 80% required ✅
- **Engagement avg:** 3.4 / 3.0 required ✅
- **Distractor quality avg:** 4.2 / 4.0 required ✅

**Result:** Module PASSES all quality gates for B1.

### Warnings (show specific items)

**Item 5** - Naturalness Warning (score 2.5)
- Sentence: "Я маю багато друзів і я завжди з ними спілкуюсь."
- Issue: Overuse of "я", sounds translated
- Suggestion: "У мене багато друзів, завжди з ними спілкуюсь."
- Action: Logged warning, acceptable for B1 teaching context

**Item 8** - Engagement Note (score 2.0)
- Sentence: "Я бачу стіл і стілець."
- Issue: Generic furniture drill, no context
- Suggestion: Add real-world context: "У кав'ярні 'Львівська копальня кави' я бачу дерев'яні столи і старовинні крісла."
- Action: Logged note for future revision

### Deleted Items (show full content)

**Item 12** - DELETED (distractor quality: 1)
- Sentence: "Я ___ до Києва потягом."
- Options: ["приїхав", "кіт", "швидко", "книга"]
- Issue: 3 of 4 distractors are wrong word class (noun, adverb)
- Action: Removed from `activities/17-motion-coming-going.yaml` lines 456-461

### Files Modified
1. `curriculum/l2-uk-en/b1/activities/17-motion-coming-going.yaml` - deleted 1 item
2. `curriculum/l2-uk-en/b1/audit/17-motion-coming-going-quality.yaml` - created

### Regeneration
✅ Ran: `npm run generate l2-uk-en b1 17`
```

---

## Checklist

Before completing validation:

- [ ] All items validated across all 5 dimensions
- [ ] Each item has all applicable `validate` fields filled
- [ ] Naturalness scores assigned (1-5)
- [ ] Difficulty assessed (too_easy/appropriate/too_hard)
- [ ] Engagement scores assigned (1-5)
- [ ] Distractor quality scores assigned (for MC activities)
- [ ] Explanations provided for low scores
- [ ] Quality gate thresholds calculated
- [ ] Module passes/fails gates determined
- [ ] Fixes applied where needed
- [ ] Output saved to `audit/{module}-quality.yaml`
- [ ] Queue file deleted from `queue/` folder
- [ ] MDX regenerated if changes made

---

## Integration with Pipeline

**After this command completes:**

1. Quality audit file created: `audit/{module}-quality.yaml`
2. Audit system will check for this file in future runs
3. Module can proceed to `/review-content` if all gates pass
4. If gates fail, module needs revision before Stage 4

**Next steps:**
```
/activity-validate → /review-content → /module-stage-4
```
