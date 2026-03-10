# Core Activities & Vocabulary Generation

> **You are Gemini, executing the activities phase of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

| Target | Value |
|--------|-------|
| Skill identity | {SKILL_IDENTITY} |
| Module persona | {PERSONA_VOICE}, acting as {PERSONA_ROLE} |
| Activities required | {ACTIVITY_MIN}–{ACTIVITY_MAX} |
| Required types | {REQUIRED_TYPES} |
| Priority types | {PRIORITY_TYPES} |
| Vocabulary items | {VOCAB_COUNT_TARGET} |

### Minimum Items Per Activity Type (HARD FAIL if under)

{ITEM_MINIMUMS_TABLE}

{TEXTBOOK_ACTIVITY_EXAMPLES}

{DECODABLE_VOCABULARY}

## Vocabulary Scope

> **Every Ukrainian word in your activities MUST come from the lesson content you are reinforcing.** Read the content file first. Do not introduce new Ukrainian vocabulary in activities — only practice words that appear in the lesson. If you need a concept not covered in the content, use English instead.

## Module Sequence Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

> **These constraints apply to activities too.** If verbs are banned, do NOT create items that use verb forms.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `{CONTENT_PATH}` | Lesson content to test/reinforce |
| `{PLAN_PATH}` | vocabulary_hints |
| `{META_PATH}` | Activity count targets |
| `{SCHEMA_PATH}` | Allowed fields per activity type (CRITICAL) |
| `docs/ACTIVITY-YAML-REFERENCE.md` | Activity reference guide |

## Audit Gates

- **Schema violations**: `additionalProperties: false` means ANY unlisted field = instant fail
- **Item counts**: Check `minItems` in schema per type
- **Russian characters**: ы, э, ё, ъ = hard fail
- **Ukrainian quotes**: do NOT use «» in YAML values — they break parsing
- **No IPA**: NEVER include IPA symbols or `ipa` fields

---

## Activities YAML Rules

1. **BARE LIST at root** — no `activities:` wrapper
2. **Schema compliance** — only fields from the schema
3. **Activity count**: {ACTIVITY_COUNT_TARGET} activities
4. **Type variety**: At least 3 different types
5. **Production over recognition** — At least 2 activities must require PRODUCING language (translate, fill-in, unjumble, error-correction, cloze)

### Activity Quality Standards

1. **Activities test LANGUAGE, not content** — Can the learner answer without reading the Ukrainian text? If YES → rewrite.
2. **Plausible example sentences** — every sentence must be something a real Ukrainian speaker might say. No philosophical statements or meta-sentences about learning.
3. **Unjumble quality** — must test grammar knowledge (word order, case agreement). Each sentence must have exactly one correct grammatical order.
4. **Error-correction precision** — exactly one clear error with one correct fix. Must be a plausible learner mistake.
5. **Group-sort accuracy** — every item belongs unambiguously to exactly one group.

### Allowed Activity Types

**ALLOWED:** {ALLOWED_ACTIVITY_TYPES}
**FORBIDDEN:** {FORBIDDEN_ACTIVITY_TYPES}

---

## Schema Reference

### quiz

```yaml
- type: quiz
  title: "Перевірте знання"
  items:  # minItems: 8, question ≥5 words
    - question: "Яка частина мови позначає дію або стан предмета?"
      explanation: "Дієслово позначає дію або стан."
      options:  # exactly 4, exactly 1 correct
        - text: "дієслово"
          correct: true
        - text: "іменник"
          correct: false
        - text: "прикметник"
          correct: false
        - text: "прислівник"
          correct: false
```

### unjumble

```yaml
- type: unjumble
  title: "Складіть речення"
  items:  # minItems: 6
    - words: ["мова", "українська", "красива"]  # Array of strings
      answer: "Українська мова красива"          # Correct sentence
```

### anagram (scrambled letters — SPACE-SEPARATED)

```yaml
- type: anagram
  title: "Розшифруйте слова"
  items:  # minItems: 8
    - scrambled: "О М Т Е Р"    # SPACE-SEPARATED — NOT concatenated!
      answer: "МЕТРО"
```

### group-sort

```yaml
- type: group-sort
  title: "Розподіліть за групами"
  groups:  # 2-4 groups
    - name: "Іменники"
      items: ["книга", "стіл"]
    - name: "Дієслова"
      items: ["читати", "писати"]
```

### mark-the-words (requires `instruction`)

```yaml
- type: mark-the-words
  title: "Знайдіть іменники"
  instruction: "Знайдіть і позначте всі іменники."  # REQUIRED
  text: "Гарний день приніс радість у серце."
  answers: ["день", "радість", "серце"]
```

### cloze (minItems: 14 blanks)

```yaml
- type: cloze
  title: "Заповніть пропуски"
  passage: "Це {{1}} з пропусками."
  blanks:  # minItems: 14
    - id: 1
      answer: "текст"
      options: ["текст", "слово", "речення", "абзац"]
```

### error-correction (ALL 5 fields REQUIRED)

```yaml
- type: error-correction
  title: "Виправте помилку"
  items:  # minItems: 6
    - sentence: "Я кушаю яблуко кожен день."
      error: "кушаю"
      answer: "їм"
      options: ["їм", "їду", "їжу", "кусаю"]
      explanation: "«Кушати» — русизм, правильно «їсти»."
```

### reading (core tracks — with comprehension tasks)

```yaml
- type: reading
  title: "Первинне джерело"
  text: |
    Actual passage text here...
  tasks:
    - "Comprehension question 1?"
    - "Comprehension question 2?"
```

---

## Mandatory Self-Check

1. **QUIZ**: exactly 1 `correct: true` per item, question ≥5 words
2. **FILL-IN**: `answer` must appear in `options`
3. **UNJUMBLE**: single sentence per item, words from vocabulary_hints
4. **ANAGRAM**: scrambled letters = answer letters (same count, same chars), space-separated
5. **MARK-THE-WORDS**: every answer string appears verbatim in text
6. **SELECT**: `min_correct` matches count of `correct: true` options

### Activity Count Check

Count your activities before outputting. You MUST generate {ACTIVITY_COUNT_TARGET} activities.

{SHARED_ACTIVITY_RULES}
