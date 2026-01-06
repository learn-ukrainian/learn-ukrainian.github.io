# YAML Activity Format Reference

**Status:** CANONICAL - All levels (A1, A2, B1, B2, C1, C2)
**Purpose:** Single source of truth for activity YAML schemas

> ⚠️ **This replaces `ACTIVITY-MARKDOWN-REFERENCE.md`** - All activities MUST be in YAML format.

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

> ⚠️ **IMPORTANT:** Do NOT use `*asterisks*` in text. Use the `answers` array to specify correct words.

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

**Last Updated:** 2026-01-06
**Status:** Canonical (Issue #394)
