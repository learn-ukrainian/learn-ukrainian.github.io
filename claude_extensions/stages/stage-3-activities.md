# Stage 3: Activities (YAML-First)

Generate activities in YAML format, separate from the prose content.

> **CRITICAL:** See `docs/ACTIVITY-YAML-REFERENCE.md` for authoritative format reference.

<critical>

## ⚠️ YAML Structure Rules (MUST READ)

### 1. Root MUST Be a Bare List
```yaml
# ✅ CORRECT - bare list at root
- type: quiz
  title: Quiz title

- type: match-up
  title: Match title
```

```yaml
# ❌ WRONG - dictionary wrapper causes schema validation failure
activities:
  - type: quiz
```

### 2. Use Schema Property Names
| Activity | Correct | Wrong |
|----------|---------|-------|
| unjumble | `jumbled` | `scrambled`, `words` |
| mark-the-words | `text` + `answers` | `passage`, asterisks |
| true-false | `statement` | `sentence` |

### 3. Mark-the-Words Format
```yaml
# ✅ CORRECT
- type: mark-the-words
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце

# ❌ WRONG - asterisks deprecated
text: Гарний *день* приніс *радість*.
answers: []
```

</critical>

---

## ⚠️ Common Schema Errors (Auto-Fail)

**CRITICAL: Each level has different minimum item counts!**
- Check your level quick-ref (`claude_extensions/quick-ref/{level}.md`) for specific minimums
- Example: A2 quiz requires 8+ items, B2 quiz requires 10+ items

### Universal Field Name Rules

- ✅ `instruction` (singular) — REQUIRED
- ❌ `instructions` (plural) — Schema violation!
- ✅ `title` — REQUIRED for all activities
- ❌ `id` — NOT allowed in most activity types (`additionalProperties: false`)

### Fill-in Activity Requirements
```yaml
# ❌ WRONG - Missing options
- sentence: "Text [___] here"
  answer: correct

# ✅ CORRECT - Has options array
- sentence: "Text [___] here"
  answer: correct
  options: [correct, wrong1, wrong2, wrong3]  # REQUIRED, exactly 4
```

### Cloze Format Requirements
```yaml
# ❌ WRONG - Both inline AND blanks array
passage: "Text with {correct|wrong1|wrong2} choices"
blanks:
  - correct
  - wrong1

# ✅ CORRECT - Inline format only
passage: "Text with {correct|wrong1|wrong2|wrong3} choices"
# NO blanks array when using inline format

# ✅ ALSO CORRECT - Numbered format with blanks array
passage: "Text with {1} and {2} here"
blanks:
  - id: 1
    answer: correct
    options: [correct, wrong1, wrong2, wrong3]
```

### Ukrainian Text in YAML
```yaml
# ❌ WRONG - Single quotes conflict with apostrophe
answer: 'інтерв'ю'  # YAML parse error

# ✅ CORRECT - Use double quotes
answer: "інтерв'ю"
```

### Activity Type Names
- ✅ `essay-response` — Correct
- ❌ `writing` — Not valid, use `essay-response`

---

## ⚡ Direct YAML Creation (Recommended)

**For new modules or recreation, write activities directly in YAML:**

1. **Read the module content** (explanation sections) to understand the topic
2. **Study 1-2 similar modules** (see Reference table below) for YAML patterns
3. **Create `.activities.yaml` file** with 12+ activities (B1)
4. **Use the YAML Format Reference** below for correct structure
5. **Run audit** to verify compliance
6. **DO NOT** use md_to_yaml.py converter - write YAML directly!

**Why direct YAML?**

- ✅ **Faster** - No MD→YAML conversion step
- ✅ **No format errors** - Direct control over structure
- ✅ **Better quality** - Explicit syntax, no parsing ambiguity
- ✅ **Proven** - M22 took 8 minutes vs 36 minutes for MD approach

## Reference Existing Modules First

**Before writing activities, study 1-2 similar existing modules:**

| Level | Module Type | Reference Examples | Look For                                   |
| ----- | ----------- | ------------------ | ------------------------------------------ |
| B1    | Grammar     | M06-10 (Aspect)    | Activity variety, sequencing, quiz prompts |
| B1    | Vocabulary  | M52-53             | YAML format, cloze passage structure       |
| A2    | All types   | M01-10             | Activity patterns, engagement integration  |

**Pattern extraction steps:**

1. Read the `.md` file for activity section structure
2. Read the `.activities.yaml` file (if exists) for YAML patterns
3. Note: quiz question length, fill-in sentence structure, error types
4. Adapt patterns to new content (don't copy actual items)

---

## Output Files

For each module, create:

```
curriculum/l2-uk-en/{level}/
├── {num}-{slug}.md                    # Prose only (no activities)
└── activities/{num}-{slug}.yaml       # All activities in YAML
```

**Example for A1 Module 35 "At the Café":**
- `curriculum/l2-uk-en/a1/35-at-the-cafe.md`
- `curriculum/l2-uk-en/a1/activities/35-at-the-cafe.yaml`

**CRITICAL:** Activity files MUST include the module number prefix (e.g., `35-at-the-cafe.yaml`, NOT `at-the-cafe.yaml`).

## Migrating Existing Embedded Activities

**If MIGRATING an old module that has embedded activities:**

| Old Format                                          | Extract                                 | Put in YAML                               |
| --------------------------------------------------- | --------------------------------------- | ----------------------------------------- |
| `## quiz:` questions                                | Keep exact questions + options          | `items[].question`, `items[].options`     |
| `## match-up:` table rows                           | Keep all pairs                          | `pairs[].left`, `pairs[].right`           |
| `## fill-in:` sentences                             | Keep sentences + answers                | `items[].sentence`, `items[].answer`      |
| `## true-false:` statements                         | Keep statements + T/F                   | `items[].statement`, `items[].correct`    |
| `## group-sort:` categories                         | Keep groups + items                     | `groups[].name`, `groups[].items`         |
| `## unjumble:` scrambled                            | Keep scrambled + answer                 | `items[].jumbled`, `items[].answer`       |
| `## cloze:` passage with `[___:1]` blanks + options | Convert `[___:N]` → `{ans\|opt1\|opt2}` | `passage` with inline `{ans\|opt1\|opt2}` |
| `## error-correction:`                              | Keep sentence + error + fix             | `items[].sentence/error/answer`           |
| `## mark-the-words:`                                | Keep text + answers                     | `text` + `answers[]` array                |
| `## select:` questions                              | Keep questions + all options            | `items[].question`, `items[].options`     |
| `## translate:` sentences                           | Keep source + options                   | `items[].source`, `items[].options`       |

**CRITICAL - Cloze Format:**

The MD format for cloze activities MUST use **numbered blanks** with option lists:

```markdown
## cloze: Title

> Instructions

Passage with [___:1] blank and [___:2] another blank.

1. opt1 | opt2 | opt3 | opt4

   > [!answer] correct_answer

2. opt1 | opt2 | opt3 | opt4
   > [!answer] correct_answer
```

**DO NOT use named blanks** like `[___:answer]` - the parser does not support this format.

See `docs/ACTIVITY-YAML-REFERENCE.md` for complete format specifications.

---

**Then:**

1. Add missing explanations (required for quiz, error-correction)
2. Add items if below minimum count
3. Add activity types if below level variety requirement
4. Delete embedded activities from `.md` after YAML created

## Activity Count Requirements (Relaxed)

| Level | Target | WARN | FAIL | Items/Activity | Types |
| ----- | ------ | ---- | ---- | -------------- | ----- |
| A1    | 8+     | <8   | <6   | 12+            | 4+    |
| A2    | 10+    | <10  | <8   | 12+            | 5+    |
| B1    | 12+    | <12  | <8   | 14+            | 5+    |
| B2    | 14+    | <14  | <10  | 16+            | 5+    |
| C1    | 16+    | <16  | <12  | 18+            | 5+    |
| C2    | 16+    | <16  | <12  | 18+            | 5+    |

**WARN** = Passes with warning. **FAIL** = Blocks approval.

## Naturalness & Discourse Quality Requirements

<critical>

**Quality Threshold:** All prose activities (cloze, fill-in, unjumble) MUST score **>= 8/10** for naturalness.

**Common Failures (Score < 8):**

1. **Random subject shifts** without context:
   ```yaml
   # ❌ BAD - disconnected subjects (я → вона → він)
   - sentence: Я читаю книгу.
     answer: читаю
   - sentence: Вона пише листа.
     answer: пише
   - sentence: Він малює картину.
     answer: малює
   ```

2. **Missing discourse markers** (connectors):
   ```yaml
   # ❌ BAD - no connectors between sentences
   Я прокинувся. Я поснідав. Я пішов.

   # ✅ GOOD - добрано connectors
   Спочатку я прокинувся. Потім я поснідав. Нарешті я пішов до школи.
   ```

3. **Incoherent topic jumps**:
   ```yaml
   # ❌ BAD - school → coffee with no transition
   - Я йду до школи щодня.
   - Кава без цукру будь ласка.

   # ✅ GOOD - unified spatial context
   - Я йду до школи щодня.
   - Школа знаходиться біля великого парку.
   ```

4. **Redundant or contradictory statements**:
   ```yaml
   # ❌ BAD - repetitive without purpose
   - Я завжди снідаю.
   - Я зазвичай снідаю.
   - Я щодня снідаю.
   ```

**Fixes (How to Reach >= 8/10):**

| Issue | Solution | Ukrainian Connectors |
|-------|----------|---------------------|
| Subject shifts | Unify context (family, day, location) | я → моя сестра, мій брат, мама |
| No flow | Add discourse markers | спочатку, потім, після того, нарешті |
| Topic jumps | Create mini-narrative | а, але, тому, і |
| Drill format | Keep focused practice, don't force complex plots | Use simple family/daily contexts |

**Vocabulary Constraints:**

- **ONLY use vocabulary from** `docs/l2-uk-en/{A1\|A2\|B1}-CURRICULUM-PLAN.md`
- **Check module number:** Don't use vocabulary from later modules
  - Example: Module 07 (Spatial Prepositions) must NOT use Module 08 prepositions (без, для, через, про)

**Pedagogical Correctness:**

- **Preserve grammar point** being taught
- **Don't sacrifice drill focus** for narrative complexity
- **Maintain CEFR level** (A1 = simple, A2 = connected, B1 = coherent)

**Testing Naturalness:**

Use MCP tool to validate fixes:
```bash
# Via MCP server
mcp__ukrainian-validator__check_naturalness(
  content="Учора я читав книгу. Потім моя сестра написала листа.",
  level="A2",
  context="fill-in activity about aspect"
)
```

**Target:** Score >= 8/10 (natural Ukrainian discourse)

</critical>

---

## Special Requirements: Content-Heavy Modules

**Content-heavy modules** (B2 History, C1 Literature/Biography/Folk/Arts) have **different requirements**:

| Aspect         | Standard Module | Content-Heavy Module        |
| -------------- | --------------- | --------------------------- |
| Activity Count | 14+ (B2/C1)     | **10-12** (reduced)         |
| Activity Mix   | All types       | **Comprehension-focused**   |
| Quiz Questions | General         | **MUST reference text**     |
| Purpose        | Drill practice  | **Language comprehension**  |

### The Golden Rule for Content-Heavy Modules

<critical>

**"Can the learner answer this without reading the Ukrainian text?"**

- **If YES** → Rewrite (tests content knowledge, not language)
- **If NO** → Keep (tests Ukrainian comprehension)

</critical>

### Activity Mix for Content-Heavy Modules (10-12 total)

| Activity Type        | Count | Key Requirement                                                  |
| -------------------- | ----- | ---------------------------------------------------------------- |
| quiz                 | 4-5   | MUST start with "Згідно з текстом..."                            |
| fill-in / cloze      | 3-4   | Test collocations (чинити спротив, відіграти роль, брати участь) |
| error-correction     | 2-3   | Fix GRAMMAR errors, NOT factual inaccuracies                     |
| match-up             | 1-2   | Ukrainian term ↔ Ukrainian definition                            |
| select / mark-words  | 1-2   | Find grammatical features in text                                |

### Forbidden vs Required Patterns (Quiz Questions)

❌ **FORBIDDEN** (Tests Content Recall):
- "У якому році..." (dates)
- "Хто був..." (names)
- "Скільки..." (numbers)
- "Що символізує..." (interpretation without text reference)

✅ **REQUIRED** (Tests Ukrainian Language):
- "Згідно з текстом, як автор..."
- "У тексті модуля автор характеризує..."
- "Яку функцію автор підкреслює..."
- "Який аргумент автор наводить..."

### Self-Check Before Delivering

For EVERY quiz question in content-heavy modules:

1. Can learner answer without reading Ukrainian module text?
2. If YES → You're testing history/literature. STOP and rewrite.
3. If NO → You're testing Ukrainian. Proceed.

### Applies To

| Level  | Module Range | Focus                     |
| ------ | ------------ | ------------------------- |
| **B2** | M71-131      | History (61 modules)      |
| **C1** | M146-160     | Literature (15 modules)   |
| **C1** | M36-100      | Biography (65 modules)    |
| **C1** | M121-145     | Folk Culture (25 modules) |
| **C1** | Various      | Fine Arts expansion       |

---

## Seminar Tracks: Reading-Analysis Pairs (LIT, HIST, BIO)

**Seminar tracks** use a fundamentally different pedagogy from standard tracks. Instead of gamified drills, they use **academic reading → analytical response** workflow.

### Affected Tracks

| Track | Level | Activity Count | Essay Length |
|-------|-------|----------------|--------------|
| **LIT** | post-C1 | 3-6 | 300-500 words |
| **C1-HIST** | C1 | 3-6 | 300-500 words |
| **C1-BIO** | C1 | 3-5 | 250-400 words |
| **B2-HIST** | B2 | 3-6 | 150-250 words (transitional) |

### Core Principle: Reading-Analysis Pairs

Every analytical activity MUST have an associated reading source:

```
reading (INPUT) → essay-response / critical-analysis / comparative-study (OUTPUT)
```

### Allowed Activity Types (Seminar)

| Type | Role | Required |
|------|------|----------|
| `reading` | Source text input | ✅ Yes (at least 1) |
| `essay-response` | Extended written response | ✅ Yes (at least 1) |
| `critical-analysis` | Targeted text analysis | Recommended |
| `comparative-study` | Compare/contrast items | Optional |
| `true-false` | Comprehension check | B2-HIST only |

### Forbidden Activity Types (Seminar)

❌ quiz, match-up, fill-in, unjumble, anagram, cloze, mark-the-words, group-sort, select, error-correction, translate

### YAML Structure: Paired Activities

<critical>

**Reading activities MUST have `id` field and use ONE of two formats:**

**Format 1: Inline Text (for poems, short excerpts)**
```yaml
- type: reading
  id: reading-testament            # REQUIRED for linking
  title: 'Джерело: Заповіт'
  source: 'Тарас Шевченко (1845)'  # Attribution (author, year)
  text: |
    Як умру, то поховайте
    Мене на могилі...
  tasks:
    - 'Які образи використовує поет?'
```

**Format 2: External Resource (for biographies, full texts)**
```yaml
- type: reading
  id: reading-bio                  # REQUIRED for linking
  title: 'Біографія письменника'
  resource:
    type: Biography
    url: https://www.ukrlib.com.ua/bio/printit.php?tid=1646  # VERIFY THIS!
    title: 'Нечуй-Левицький. Життя і творчість'
  tasks:
    - 'Як вплинуло дитинство на творчість?'
    - 'Які стосунки були з сучасниками?'
```

**⚠️ URL VERIFICATION (MANDATORY):**
Before using external URLs, you MUST:
1. Open the URL in a browser
2. Verify the page is about the correct author/work
3. Check the page title matches the expected content

Common UkrLib biography IDs (always verify!):
- Котляревський: tid=1672
- Шевченко: tid=57
- Куліш: tid=1621
- Нечуй-Левицький: tid=1646 (NOT 1815!)
- Франко: tid=71

**Analytical activities MUST reference their source:**
```yaml
- type: critical-analysis
  title: 'Аналіз: Заповіт'
  source_reading: reading-testament  # ← Links to reading above
  target_text: 'Як умру, то поховайте...'
  questions:
    - 'Чому автор обрав наказовий спосіб?'
```

</critical>

### Self-Validation Checklist (MANDATORY)

<critical>

**Before outputting activities, YOU MUST verify against your knowledge:**

1. **External URL Verification**
   - Do you know this URL from your training data?
   - Is the author/topic correct for this URL?
   - If unsure, DO NOT use the URL - use inline text format instead
   - Example: "Is UkrLib tid=1646 the correct ID for Nechuy-Levytsky?" → Verify before using

2. **Reading-Analysis Coherence**
   - Does the `target_text` in critical-analysis actually appear in the source reading?
   - Do the `questions` relate directly to the reading content?
   - Does the `prompt` in essay-response engage meaningfully with the source?
   - Would a student be able to answer using ONLY the reading provided?

3. **Model Answer Quality**
   - Does the model answer actually address the prompt/questions?
   - Does it reference specific elements from the reading?
   - Is it at the appropriate academic level (B2/C1/post-C1)?

4. **Factual Accuracy**
   - Are dates, names, and historical facts correct?
   - Are literary attributions accurate (author, year, work title)?
   - Do biographical claims match known facts about the author?

**If you cannot verify any of the above, STOP and ask the user for clarification.**

</critical>

### Valid Pairing Combinations

| Input (reading) | Valid Outputs |
|-----------------|---------------|
| Primary source (poem, speech) | critical-analysis, essay-response |
| Historical document | essay-response, comparative-study |
| Two contrasting sources | comparative-study |

### Example: Complete Seminar Module

```yaml
# 1. Primary reading
- type: reading
  id: reading-testament
  title: 'Джерело: Заповіт'
  source: 'Тарас Шевченко (1845)'
  text: |
    Як умру, то поховайте...

# 2. Analytical response (references reading)
- type: critical-analysis
  title: 'Аналіз символіки'
  source_reading: reading-testament
  target_text: 'Поховайте та вставайте, кайдани порвіте...'
  questions:
    - 'Яку функцію виконує імперативний спосіб?'
    - 'Як \"кайдани\" символізують політичний стан?'

# 3. Extended response
- type: essay-response
  title: 'Есе: Націотворча роль'
  source_reading: reading-testament
  prompt: 'Проаналізуйте, як «Заповіт» сформував українську національну ідентичність.'
  min_words: 300

# 4. (Optional) Comparative study with second reading
- type: reading
  id: reading-context
  title: 'Історичний контекст'
  text: |
    У 1845 році Шевченко написав «Заповіт» під час...

- type: comparative-study
  title: 'Порівняння: Романтики vs Шевченко'
  source_reading: reading-context
  items_to_compare:
    - 'Європейський романтизм'
    - 'Шевченківський месіанізм'
  criteria:
    - 'Роль поета'
    - 'Ставлення до народу'
```

### Validation Rules (Enforced by Audit)

1. **Every analytical activity must have `source_reading`** pointing to a valid reading `id`
2. **Every reading should be referenced** by at least one analytical activity
3. **Orphan readings** (unreferenced) trigger WARNING
4. **Orphan analyses** (missing source) trigger ERROR

### B2-HIST Transitional Rules

B2-HIST is a stepping stone to C1-level seminar work:

- ✅ Shorter essays (150-250 words)
- ✅ `true-false` allowed for basic comprehension checks
- ✅ Simpler critical questions
- ❌ Still forbidden: quiz, match-up, fill-in, etc.

---

## Activity Matrix by Level

| Activity         | A1          | A2  | B1  | B2  | C1  | C2  |
| ---------------- | ----------- | --- | --- | --- | --- | --- |
| fill-in          | 2+          | 2+  | 2+  | 3+  | 2+  | 2+  |
| match-up         | 2+          | 1+  | 1+  | 1+  | 1+  | 1+  |
| quiz             | 1+          | 1+  | 1+  | 1+  | 1+  | 1+  |
| true-false       | 1+          | 1+  | 1+  | 1+  | -   | -   |
| group-sort       | 1+          | 1+  | 1+  | 1+  | 1+  | 1+  |
| anagram          | 2+ (M01-10) | -   | -   | -   | -   | -   |
| unjumble         | 2+ (M11+)   | 2+  | 2+  | 2+  | 2+  | 2+  |
| error-correction | -           | 1+  | 2+  | 2+  | 3+  | 3+  |
| cloze            | -           | 1+  | 1+  | 1+  | 3+  | 3+  |
| mark-the-words   | -           | 1+  | 1+  | 1+  | -   | -   |
| select           | -           | opt | 1+  | 1+  | 1+  | 1+  |
| translate        | -           | opt | 1+  | 1+  | 2+  | 2+  |

## YAML Format Reference

> [!IMPORTANT]
> See `docs/ACTIVITY-YAML-REFERENCE.md` for complete format with examples.

### Common Activity Structures

```yaml
# Quiz (8+ items for B1)
- type: quiz
  title: Quiz title
  instruction: Select the correct answer.
  items:
    - question: Яке слово є синонімом до "великий"?
      options:
        - text: малий
          correct: false
        - text: величезний
          correct: true
        - text: швидкий
          correct: false
        - text: повільний
          correct: false
      explanation: "Величезний" означає дуже великий.

# Match-up (12+ pairs for B1)
- type: match-up
  title: Match title
  instruction: Match the pairs.
  pairs:
    - left: іти
      right: to go (on foot)
    - left: їхати
      right: to go (by vehicle)

# Fill-in (12+ items for B1)
- type: fill-in
  title: Fill-in title
  instruction: Choose the correct word.
  items:
    - sentence: Вона [___] до магазину, щоб купити хліб.
      answer: пішла
      options:
        - пішла
        - їхала
        - летіла
        - бігла

# True-false (12+ items for B1)
- type: true-false
  title: True/False title
  instruction: Determine if the statement is true or false.
  items:
    - statement: Дієслово "іти" означає рух пішки.
      correct: true
      explanation: Так, "іти" — це рух пішки, на відміну від "їхати" (транспортом).

# Group-sort (16+ total items, 3-5 categories for B1)
- type: group-sort
  title: Sorting title
  instruction: Sort items into categories.
  groups:
    - name: Дієслова руху пішки
      items:
        - іти
        - бігти
    - name: Дієслова руху транспортом
      items:
        - їхати
        - летіти
    - name: Не дієслова руху
      items:
        - читати
        - писати

# Unjumble (6+ items for B1, 12-16 words per sentence)
- type: unjumble
  title: Unjumble title
  instruction: Put the words in the correct order.
  items:
    - jumbled: Вона / до / пішла / магазину
      answer: Вона пішла до магазину.

# Cloze (14+ blanks for B1)
- type: cloze
  title: Cloze title
  instruction: Fill in the blanks.
  passage: 'Марія {пішла|поїхала|полетіла} до школи, а потім {зайшла|виїхала|прибігла} до бібліотеки.'

# Error-correction (6+ items for B1)
- type: error-correction
  title: Error correction title
  instruction: Find and fix the ONE error in each sentence.
  items:
    - sentence: Вона пішла до магазин, щоб купити хліб.
      error: магазин
      answer: магазину
      options:
        - магазин
        - магазину
        - магазином
        - магазині
      explanation: Після прийменника "до" потрібен родовий відмінок — "магазину".

# Mark-the-words (6+ correct words for B1)
- type: mark-the-words
  title: Mark words title
  instruction: Знайдіть усі іменники.
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце

# Select (6+ items for B1)
- type: select
  title: Select title
  instruction: Select ALL correct answers for each question.
  items:
    - question: Які з цих слів є дієсловами руху?
      options:
        - text: іти
          correct: true
        - text: бігти
          correct: true
        - text: стіл
          correct: false
        - text: великий
          correct: false
      explanation: Іти та бігти означають рух, стіл — іменник, великий — прикметник.

# Translate (6+ items for B1)
- type: translate
  title: Translate title
  instruction: Choose the correct Ukrainian translation.
  items:
    - source: She went to the store.
      options:
        - text: Вона пішла до магазину.
          correct: true
        - text: Вона їхала до магазину.
          correct: false
        - text: Вона біжить до магазину.
          correct: false
        - text: Вона йде до магазину.
          correct: false
      explanation: "Went" — минулий час, тому "пішла".
```

## YAML Quoting Rules (CRITICAL)

When a string contains special characters, quote it properly:

1. **Quoted speech in cloze/mark-the-words** → use Ukrainian guillemets `«»`, NOT escaped quotes:

   ```yaml
   # ✅ CORRECT - guillemets work in MDX/JSX
   passage: "Викладач сказав: «{Не забувай} читати щодня!»"
   text: "Він відповів: «Я *не* розумію.»"

   # ❌ WRONG - escaped quotes break MDX compilation
   passage: "Викладач сказав: \"{Не забувай} читати щодня!\""
   ```

   **Why:** Cloze `passage` and mark-the-words `text` become JSX attributes. Escaped `\"` causes "Unexpected character" errors during MDX build.

2. **Strings with embedded quotes (other fields)** → wrap in single quotes, double internal quotes:

   ```yaml
   explanation: '"Думка" means opinion.'
   statement: '"Рішення" та "розв''язання" — різні слова.'
   ```

3. **Strings with colons** → wrap in quotes:

   ```yaml
   explanation: 'Правильно: так і ні.'
   ```

4. **Strings with apostrophes** → double the apostrophe inside single quotes:

   ```yaml
   statement: 'Слово "розв''язання" має інше значення.'
   ```

5. **Numeric option values** → quote as strings:

   ```yaml
   # ✅ CORRECT
   - text: '5'
     correct: false

   # ❌ WRONG - causes 'int' object has no attribute 'replace'
   - text: 5
     correct: false
   ```

## Activity Sequencing

Flow: Easy → Medium → Hard

### A1

```
match-up → group-sort → quiz → true-false → fill-in → anagram/unjumble
```

### A2-B1

```
[recognition] mark-the-words → match-up → group-sort
[discrimination] quiz → true-false → select
[controlled] fill-in → cloze → error-correction
[production] unjumble → translate
```

### B2-C2

```
[discrimination] select (nuanced)
[controlled] fill-in → cloze → error-correction ×2-3
[production] translate → unjumble ×2-3
```

## Vocabulary Constraint (CRITICAL)

Activities MUST use ONLY:

1. Words from the current module's vocabulary table
2. Words from prior modules (cumulative vocabulary)
3. Common function words (я, ти, він, це, і, а, але, etc.)

NEVER use words not taught yet.

## Validation

After writing the YAML file:

```bash
# Validate YAML structure
npm run validate:yaml curriculum/l2-uk-en/{level}/{file}.activities.yaml

# Run module audit
python3 scripts/audit_module.py curriculum/l2-uk-en/{level}/{file}.md
```

## Checklist

- [ ] Created `.activities.yaml` file (NOT embedded in `.md`)
- [ ] Activity count meets level requirement
- [ ] Items per activity meets minimum
- [ ] Activity variety (4-5+ types)
- [ ] Proper sequencing (easy → hard)
- [ ] Valid YAML syntax (run validator)
- [ ] All answers are correct
- [ ] Uses ONLY vocabulary from YAML + prior modules
- [ ] Strings with quotes/colons properly escaped

## DO NOT

- Embed activities in the `.md` file
- Use vocabulary not in YAML or prior modules
- Write fewer than required activities
- Create activities with fewer than minimum items
- Leave quotes/colons unescaped in YAML strings
