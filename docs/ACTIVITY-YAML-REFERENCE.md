# YAML Activity Format Reference

**Status:** CANONICAL - All levels (A1, A2, B1, B2, C1, C2)
**Purpose:** Single source of truth for activity YAML schemas
**Last Updated:** January 11, 2026

> ⚠️ **This replaces `ACTIVITY-MARKDOWN-REFERENCE.md`** - All activities MUST be in YAML format.

---

## Critical Rules (READ FIRST)

<critical>

### 1. Root Structure: MUST Be a Bare List

YAML activity files must have a **list at the root level**, NOT wrapped in a dictionary:

```yaml
# ✅ CORRECT - bare list at root
- type: quiz
  title: Quiz title
  items: [...]

- type: match-up
  title: Match title
  pairs: [...]
```

```yaml
# ❌ WRONG - dictionary wrapper (causes schema validation failure)
activities:
  - type: quiz
    title: Quiz title
```

**Why:** The JSON schema validates against a root array. A dictionary wrapper fails validation.

### 2. Property Names Must Match Schema

Use the exact property names defined in `schemas/activities-{level}.schema.json`:

| Activity | Correct Property | Wrong Property |
|----------|-----------------|----------------|
| unjumble | `jumbled` | `scrambled`, `words` |
| fill-in | `sentence` | `text`, `prompt` |
| mark-the-words | `text` + `answers` | `passage` + `correct_words` |
| cloze | `passage` | `text` |
| true-false | `statement` | `sentence`, `text` |

### 3. Mark-the-Words: Use `text` + `answers` Array

```yaml
# ✅ CORRECT - plain text with answers array
- type: mark-the-words
  title: Знайдіть іменники
  instruction: Клацніть на всі іменники в реченні.
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце
```

```yaml
# ❌ WRONG - asterisks in text (was deprecated format)
- type: mark-the-words
  text: Гарний *день* приніс *радість* у *серце*.
  answers: []  # Empty - relies on asterisk extraction
```

**Note:** The asterisk format was used historically but causes issues. Always use explicit `answers` array.

### 4. YAML Quoting for Quoted Text

**Problem:** Statements containing quoted words cause parse errors.

**Examples:**
```yaml
# ❌ WRONG - straight quotes conflict with YAML syntax
statement: Слово "лист" означає email.
# Error: "did not find expected key"

# ✅ CORRECT - Ukrainian guillemets
statement: Слово «лист» означає email.

# ✅ ALSO CORRECT - wrap entire string in single quotes
statement: 'Слово "лист" означає email.'
```

**Recommendation:** Use Ukrainian guillemets («») for quoted text - they're typographically correct and avoid YAML conflicts.

</critical>

---

## Overview

Instead of embedding activities in markdown, we split modules into:

```
curriculum/l2-uk-en/b1/
├── 52-abstract-concepts-ideas.md    # Prose content (no activities)
├── activities/                       # YAML activity files
│   └── 52-abstract-concepts-ideas.yaml
└── queue/                            # Grammar validation queues
    └── 52-abstract-concepts-ideas.yaml
```

**Benefits:**
- Schema validation catches errors before generation
- IDE autocomplete for activity structure
- Easier to review/edit activities separately
- Type-safe parsing with better error messages
- Consistent activity structure across modules

---

## File Structure

### Prose File (`.md`)

Contains everything EXCEPT activities:
- Frontmatter
- Motivation box
- Content sections (Вступ, Лексика, Використання, Читання, Діалоги)
- Підсумок
- Словник (vocabulary table)
- Resources callout

**Does NOT contain:** `## quiz:`, `## match-up:`, etc.

### Activities File (`activities/{module}.yaml`)

Contains all activities in YAML format:

```yaml
# activities/52-abstract-concepts-ideas.yaml

- type: quiz
  title: Розуміння абстрактних концепцій
  items:
    - question: Яке слово означає "opinion" українською?
      options:
        - text: ідея
          correct: false
        - text: думка
          correct: true
        - text: концепція
          correct: false
        - text: теорія
          correct: false
      explanation: "Думка" means opinion or thought.

- type: match-up
  title: Колокації з дієсловами
  pairs:
    - left: ідею
      right: мати
    - left: проблему
      right: вирішити
    # ... 10+ more pairs
```

---

## Creating a Module

### Step 1: Write Prose Content

Create the `.md` file with all content sections but NO activities:

```markdown
---
module: b1-52
title: "Абстрактні концепції: ідеї та думки"
# ... full frontmatter
---

# Абстрактні концепції: ідеї та думки

> 🎯 **Чому це важливо?**
> ...

## Вступ
...

## Лексика
...

## Використання
...

## Читання
...

## Діалоги
...

# Підсумок
...

# Словник
| Слово | Вимова | Переклад | ЧМ | Примітка |
...

> [!resources] 🎧 Зовнішні ресурси
> ...
```

### Step 2: Write Activities in YAML

Create the activity file in the `activities/` subfolder:

```yaml
# Activities for Module 52: Abstract Concepts I
# Level: B1 (requires 12+ activities)

- type: quiz
  title: Розуміння концепцій
  items:
    - question: Question text (12-20 words)?
      options:
        - text: Wrong answer
          correct: false
        - text: Correct answer
          correct: true
        - text: Wrong answer
          correct: false
        - text: Wrong answer
          correct: false
      explanation: Optional explanation.
    # ... 7+ more items (B1 needs 8)

- type: match-up
  title: Колокації
  pairs:
    - left: Ukrainian term
      right: English/definition
    # ... 11+ more pairs (B1 needs 12)

# ... 10+ more activities for 12 total
```

### Step 3: Validate

```bash
# Validate YAML structure
npm run validate:yaml curriculum/l2-uk-en/b1/activities/52-abstract-concepts-ideas.yaml

# Run module audit
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/52-abstract-concepts-ideas.md
```

### Step 4: Generate

```bash
# Full pipeline
npm run pipeline l2-uk-en b1 52
```

---

## Activity Type Reference

> **Note:** All activity types support an optional `instruction` field that displays custom instructions above the activity. Use this to provide context-specific guidance for the learner.

### quiz (8+ items for B1)

```yaml
- type: quiz
  title: Title
  instruction: Optional instruction text for the learner.
  items:
    - question: Question text?
      options:
        - text: Answer text
          correct: false
        - text: Correct answer
          correct: true
        - text: Answer text
          correct: false
        - text: Answer text
          correct: false
      explanation: Optional explanation
```

### match-up (12+ pairs for B1)

```yaml
- type: match-up
  title: Title
  instruction: Optional instruction text.
  pairs:
    - left: Left item
      right: Right item
```

### fill-in (12+ items for B1)

```yaml
- type: fill-in
  title: Title
  instruction: Optional instruction text.
  items:
    - sentence: Sentence with _____ blank.
      answer: correct
      options:
        - wrong1
        - correct
        - wrong2
        - wrong3
```

### true-false (12+ items for B1)

```yaml
- type: true-false
  title: Title
  instruction: Optional instruction text.
  items:
    - statement: Слово порекомендуєте є ввічливою формою.
      correct: true
      explanation: Так, це форма на ви.
```

> ⚠️ **Quoting:** Avoid embedding quotes in statements. Use Ukrainian quotation marks «слово» if needed, or rephrase.

### group-sort (16+ items for B1)

```yaml
- type: group-sort
  title: Title
  instruction: Optional instruction text.
  groups:
    - name: Category A
      items:
        - item1
        - item2
    - name: Category B
      items:
        - item3
        - item4
```

### unjumble (8+ items for B1)

```yaml
- type: unjumble
  title: Title
  instruction: Optional instruction text.
  items:
    - jumbled: words / in / disorder
      answer: Words in correct order.
```

### cloze (14+ blanks for B1)

```yaml
- type: cloze
  title: Title
  instruction: Optional instruction text.
  passage: |
    Сьогодні {гарна|гарна|погана|холодна} погода. Ми {йдемо|йдемо|їдемо|летимо} до парку.
```

> ⚠️ **Format:** `{correct|option2|option3|option4}` - First option is ALWAYS the correct answer. NO arrows (`→`), NO labels.

### error-correction (8+ items for B1)

```yaml
- type: error-correction
  title: Title
  instruction: Optional instruction text.
  items:
    - sentence: Sentence with error.
      error: wrong_word
      answer: correct_word
      options:
        - wrong_word
        - correct_word
        - distractor1
        - distractor2
      explanation: Why it's wrong.
```

**⚠️ Important Limitation:** The `error-correction` activity type is designed for **single-word corrections only**. The `answer` field expects a single word that replaces the `error` word.

**Not suitable for:**
- Full sentence corrections
- Style/register transformations (informal → formal)
- Multi-word phrase corrections

**For sentence-level corrections**, use `quiz` instead:
```yaml
- type: quiz
  title: Офіційний варіант неформальних фраз
  instruction: Як правильно написати офіційно?
  items:
    - prompt: Як офіційно написати: «Привіт, Іване»?
      options:
        - Шановний Іване
        - Добрий день, Іване
        - Привіт, Іване
        - Вітаю, Іване
      answer: Шановний Іване
```

### mark-the-words (6+ correct words for B1)

```yaml
- type: mark-the-words
  title: Title
  instruction: Знайдіть усі іменники.
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце
```

> **Format:** Plain text without asterisks + explicit `answers` array. The answers must appear exactly as written in the text.

### select (8+ items for B1)

```yaml
- type: select
  title: Title
  instruction: Optional instruction text.
  items:
    - question: Select ALL correct answers.
      options:
        - text: Correct 1
          correct: true
        - text: Correct 2
          correct: true
        - text: Wrong
          correct: false
```

### translate (8+ items for B1)

```yaml
- type: translate
  title: Title
  instruction: Optional instruction text.
  items:
    - source: English sentence.
      options:
        - text: Wrong translation
          correct: false
        - text: Correct translation
          correct: true
        - text: Wrong translation
          correct: false
        - text: Wrong translation
          correct: false
```

### anagram (A1 only, modules 1-10)

```yaml
- type: anagram
  title: Title
  instruction: Optional instruction text.
  items:
    - scrambled: "л и т е р и"
      answer: "літери"
      hint: "Letters"
```

> ⚠️ **Level restriction:** Anagram is only allowed in A1 modules 1-10 (scaffolding for Cyrillic learners).

---

## Seminar Track Activities (LIT, HIST, BIO)

Seminar tracks use academic-style activities for deeper engagement with literary and historical content.

### reading (Required for seminar tracks)

Two formats supported: **inline text** (primary source in YAML) or **external resource** (link to external URL).

#### Format 1: Inline Primary Source Text

Use when the text is short enough to include directly:

```yaml
- type: reading
  id: reading-01                    # REQUIRED: unique ID for linking
  title: 'Джерело: Заповіт'
  source: 'Тарас Шевченко (1845)'   # Attribution (author, year)
  text: |
    Як умру, то поховайте
    Мене на могилі,
    Серед степу широкого,
    На Вкраїні милій...
  tasks:                            # Reading comprehension questions
    - 'Де просить поет поховати його?'
    - 'Яка емоція переважає в уривку?'
```

#### Format 2: External Resource Link

Use when referring to longer external materials:

```yaml
- type: reading
  id: reading-bio
  title: 'Біографія письменника'
  resource:
    type: 'Biography'               # Type label (Biography, Article, etc.)
    url: 'https://www.ukrlib.com.ua/bio/printit.php?tid=1815'
    title: 'Іван Нечуй-Левицький. Життя і творчість'
  tasks:
    - 'Яким було повсякденне життя письменника в Києві?'
    - 'Чому сучасники називали його "самітником"?'
    - 'Які стосунки склалися у нього з "громадами"?'
```

<critical>

**Field Reference:**

| Field | Format 1 (inline) | Format 2 (external) | Description |
|-------|-------------------|---------------------|-------------|
| `id` | REQUIRED | REQUIRED | Unique ID for linking to analytical activities |
| `title` | REQUIRED | REQUIRED | Display title |
| `text` | REQUIRED | - | Inline primary source text (Ukrainian) |
| `source` | Optional | - | Attribution (e.g., "Тарас Шевченко (1845)") |
| `resource` | - | REQUIRED | External link object |
| `resource.url` | - | REQUIRED | Full URL to external material |
| `resource.title` | - | Optional | Display title for the link |
| `resource.type` | - | Optional | Type label (Biography, Article, etc.) |
| `tasks` | REQUIRED | REQUIRED | Array of reading comprehension questions |

**Common Mistakes:**
```yaml
# ❌ WRONG - duplicate 'title' key
- type: reading
  title: 'First title'
  source: 'UkrLib'          # Wrong: 'source' is for attribution, not website
  title: 'Second title'     # YAML error: duplicate key
  instruction: '...'        # Wrong: use 'tasks' array instead

# ❌ WRONG - URL in text field
- type: reading
  text: 'Read at: https://example.com/...'  # Wrong: use resource.url

# ✅ CORRECT
- type: reading
  id: reading-01
  title: 'Біографія'
  resource:
    url: 'https://example.com/bio'
    title: 'Біографія письменника'
  tasks:
    - 'Question 1?'
    - 'Question 2?'
```

</critical>

### essay-response

```yaml
- type: essay-response
  title: 'Есе: Національна ідентичність'
  source_reading: reading-01        # Links to reading activity
  prompt: |
    Проаналізуйте, як образ України у «Заповіті» Шевченка формує
    національну ідентичність. Розгляньте символіку могили, степу та Дніпра.
  min_words: 300                    # Required: minimum word count
  model_answer: |                   # Optional: reference answer
    Шевченко у «Заповіті» створює...
```

> **Track-specific word counts:**
> - LIT: 300-500 words
> - C1-HIST: 300-500 words
> - C1-BIO: 250-400 words
> - B2-HIST: 150-250 words (transitional)

### critical-analysis

```yaml
- type: critical-analysis
  title: 'Аналіз: Символіка Заповіту'
  source_reading: reading-01        # Links to reading activity
  target_text: |                    # Specific excerpt to analyze
    Поховайте та вставайте,
    Кайдани порвіте...
  questions:                        # 2-4 analytical questions
    - 'Яку функцію виконує імперативний спосіб?'
    - 'Як «кайдани» символізують політичний стан України?'
  model_answers:                    # Optional: reference answers
    - 'Імперативний спосіб створює...'
    - 'Кайдани символізують...'
```

### comparative-study

```yaml
- type: comparative-study
  title: 'Порівняння: Шевченко і Куліш'
  source_reading: reading-context   # Optional: can link to reading
  items_to_compare:
    - 'Тарас Шевченко (емоційний підхід)'
    - 'Пантелеймон Куліш (раціональний підхід)'
  criteria:
    - 'Ставлення до козацтва'
    - 'Роль поета в суспільстві'
    - 'Бачення майбутньої України'
  model_answer: |
    Шевченко і Куліш представляють...
```

### Reading-Analysis Pairing Rules

<critical>

**Every analytical activity MUST reference a reading:**
```yaml
- type: reading
  id: reading-01          # ← Unique ID
  ...

- type: essay-response
  source_reading: reading-01  # ← Links to reading above
  ...
```

**Validation rules (enforced by audit):**
1. Every `critical-analysis`, `essay-response`, and `comparative-study` **must** have `source_reading`
2. `source_reading` must reference a valid `id` in a `reading` activity in the same file
3. Orphan readings (unreferenced) trigger **WARNING** (info severity)
4. Missing `source_reading` on analytical activity triggers **CRITICAL** (audit fails)
5. Invalid `source_reading` reference (points to non-existent id) triggers **CRITICAL**

**Valid pairings:**
| Reading Type | Valid Outputs |
|--------------|---------------|
| Primary source (poem, speech) | critical-analysis, essay-response |
| Historical document | essay-response, comparative-study |
| Two contrasting sources | comparative-study |

</critical>

---

## B1 Activity Requirements

| Activity Type | Min Items | Notes |
|--------------|-----------|-------|
| Total activities | 12 | Per module |
| quiz items | 8 | Per activity |
| match-up pairs | 12 | Per activity |
| fill-in items | 12 | Per activity |
| true-false items | 12 | Per activity |
| group-sort items | 16 | Total across groups |
| unjumble items | 8 | 12-16 words each |
| cloze blanks | 14 | Per passage |
| error-correction | 8 | Per activity |
| mark-the-words | 6 | Correct words |
| select items | 8 | Per activity |
| translate items | 8 | Per activity |

---

## Validation

### Schema Validation (IDE)

With VS Code + YAML extension:
- Autocomplete for activity structure
- Errors highlighted as you type
- Schema: `schemas/activities-b1.schema.json`

### CLI Validation

```bash
# Single file
npm run validate:yaml path/to/activities/file.yaml

# All YAML files
npm run validate:yaml --all

# Specific level
npm run validate:yaml --dir curriculum/l2-uk-en/b1/activities --level b1
```

### Audit Validation

The audit script checks:
1. Activity file exists in `activities/` subfolder
2. YAML parses correctly
3. Meets level requirements (12+ activities, correct item counts)

---

## Migration from Embedded Activities

To convert existing modules:

```bash
# Extract activities from MD to YAML
npm run convert:md-to-yaml path/to/module.md

# Review and fix the generated YAML
# Then remove activities from the MD file
```

---

## Generator Integration

The MDX generator:
1. Read prose from `.md` file
2. Read activities from `activities/{module}.yaml` file (if exists)
3. Fall back to embedded activities if no YAML file
4. Merge and generate MDX output

This allows gradual migration—old modules keep working.

---

## Lessons Learned (January 2026)

### The 711-File Fix (Root Structure Issue)

**Problem:** AI agents generated YAML with `activities:` wrapper instead of bare list:
```yaml
# Generated (wrong)
activities:
  - type: quiz
    ...
```

**Impact:** 711 files failed schema validation. VSCode showed errors, but YAML syntax validators passed because the YAML itself was valid - only the structure violated the JSON schema.

**Root Cause:**
1. Stage-3 documentation showed examples with wrapper
2. AI agents followed the documentation literally
3. Schema expected root array but got root object

**Fix Applied:**
1. Updated `claude_extensions/stages/stage-3-activities.md` with correct examples
2. Batch-fixed all 711 files to remove wrapper
3. Added auto-fix function in `scripts/yaml_schema_validation.py`

**Prevention:**
- This document now has Critical Rules section at top
- CLAUDE.md references this as authoritative source
- Schema validation runs in CI/CD

### Property Name Mismatches

**Problem:** AI agents used intuitive but wrong property names:
- `words` instead of `jumbled` (unjumble)
- `passage` instead of `text` (mark-the-words)
- `scrambled` instead of `jumbled` (unjumble)

**Root Cause:** Documentation used inconsistent examples, and agents filled in "sensible" names.

**Fix:** Added property name table to Critical Rules section. Auto-fix function renames common mistakes.

### Mark-the-Words Asterisk Format

**Problem:** Documentation recommended asterisks in text with empty answers array:
```yaml
text: Гарний *день* приніс *радість* у *серце*.
answers: []
```

**Issue:** This format required parser-side asterisk extraction, which was fragile and caused MDX build errors when asterisks weren't properly handled.

**Fix:** Updated to explicit format:
```yaml
text: Гарний день приніс радість у серце.
answers: [день, радість, серце]
```

---

## Best Practices for YAML Sidecar Files

1. **Validate early:** Run `npm run validate:yaml` before committing
2. **Check schema:** Use VSCode YAML extension with schema association
3. **Root = list:** Every activity file starts with `- type:` at column 0
4. **Match property names:** Refer to schema, not intuition
5. **Quote strings with colons:** `explanation: 'Правильно: так.'`
6. **Use Ukrainian guillemets:** `«текст»` not `"текст"` in passages
7. **Test generation:** Run `npm run pipeline` to catch MDX issues

---

## Validation Architecture

### Two-Level Validation System

**Level 1: JSON Schema (Structure)**
- **Location:** `schemas/activities-{level}.schema.json`
- **Purpose:** Validates YAML syntax and structure
- **Checks:** Property names, types, required fields, item structure
- **Does NOT enforce:** Activity counts, CEFR requirements

**Level 2: Audit Script (Quality)**
- **Location:** `scripts/audit/config.py` → `LEVEL_CONFIG`
- **Purpose:** Enforces CEFR pedagogical requirements
- **Checks:** Min activities, min items per activity, activity variety

**Why Separated?**
- Schema validation runs in IDE (real-time feedback)
- YAML files with 1 activity are structurally valid but pedagogically incomplete
- Audit catches incomplete modules during quality gate, not parse time
- Allows incremental development (write 1 activity, validate structure, add more)

**Activity Count Requirements (from config.py):**
| Level | min_activities | Enforcement |
|-------|----------------|-------------|
| A1 | 8 | Audit |
| A2 | 10 | Audit |
| B1 | 8 | Audit |
| B2 | 10 | Audit |
| C1 | 12 | Audit |
| C2 | 16 | Audit |

These values are enforced by `audit_module.py`, not the JSON schema.

---

**Last Updated:** 2026-01-11
**Status:** Canonical (Issue #394, updated for YAML lessons learned)
