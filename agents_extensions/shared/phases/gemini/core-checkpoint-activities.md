# Core Checkpoint Activities & Vocabulary

> **You are Gemini, executing the activities phase of a CHECKPOINT module rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## CHECKPOINT IDENTITY

**This is a CHECKPOINT module — activities must test INTEGRATION, not isolated skills.**

| Teaching Module Activities | Checkpoint Activities |
|---------------------------|----------------------|
| Test one skill at a time | Combine 2+ skills per activity |
| Practice newly introduced patterns | Review patterns from multiple prior modules |
| Drill specific grammar points | Test integrated language use |
| Focus on accuracy of new forms | Focus on fluency with known forms |

**Golden rule: Every activity should require combining skills from different prior modules.**

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

> **Every Ukrainian word in your activities MUST come from PRIOR modules that this checkpoint reviews.** Read the content file first. Do not introduce new Ukrainian vocabulary — only practice words from the reviewed block.

## Module Sequence Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

> **These constraints apply to activities too.** If verbs are banned, do NOT create items that use verb forms.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `{CONTENT_PATH}` | Checkpoint content to reinforce |
| `{PLAN_PATH}` | vocabulary_hints (all REVIEW words) |
| `{SCHEMA_PATH}` | Allowed fields per activity type (CRITICAL) |
| `docs/ACTIVITY-YAML-REFERENCE.md` | Activity reference guide |

---

## Checkpoint Activity Design Principles

### 1. Integration Over Isolation

Each activity should combine skills. Examples:

- **Quiz**: Questions requiring understanding of BOTH grammar concept A AND concept B
- **Fill-in**: Sentences requiring correct case ending AND correct word choice
- **Unjumble**: Sentences combining vocabulary and grammar from 2+ prior modules
- **Error-correction**: Errors that test whether the learner can distinguish between similar forms learned in different modules
- **Cloze**: Passages that weave together multiple grammar patterns

### 2. New Contexts, Familiar Words

Use all review vocabulary in situations the learner hasn't seen:
- Combine vocabulary from different thematic modules in realistic scenarios
- Create dialogues that require multiple grammar skills simultaneously

### 3. Realistic Scenarios

Frame activities around real situations:
- Travel scenarios (combines transport + directions + polite forms)
- Social events (combines introductions + descriptions + preferences)
- Daily routines (combines time + activities + frequency)

### 4. Progressive Difficulty

Start with simpler integration (2 skills) and build to more complex (3+ skills).

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
5. **Production over recognition** — At least 2 activities must require PRODUCING language
6. **Integration focus** — Each activity must combine 2+ skills from the reviewed block

### Activity Quality Standards

1. **Activities test LANGUAGE, not content** — Can the learner answer without reading the Ukrainian text? If YES, rewrite.
2. **Integration required** — Single-skill drills are not appropriate for checkpoints. Every activity combines skills.
3. **Plausible example sentences** — every sentence must be something a real Ukrainian speaker might say.
4. **Unjumble quality** — must test grammar knowledge across multiple patterns.
5. **Error-correction precision** — errors should involve confusing patterns from different modules.
6. **Group-sort accuracy** — every item belongs unambiguously to exactly one group.

### Allowed Activity Types

**ALLOWED:** {ALLOWED_ACTIVITY_TYPES}
**FORBIDDEN:** {FORBIDDEN_ACTIVITY_TYPES}

---

## Schema Reference

### quiz

```yaml
- type: quiz
  title: "Перевірте знання"
  items:  # minItems: 8, question >= 5 words
    - question: "Integration question combining skill A and skill B?"
      explanation: "Explanation connecting both skills."
      options:  # exactly 4, exactly 1 correct
        - text: "correct answer"
          correct: true
        - text: "distractor"
          correct: false
        - text: "distractor"
          correct: false
        - text: "distractor"
          correct: false
```

### unjumble

```yaml
- type: unjumble
  title: "Складіть речення"
  items:  # minItems: 6
    - words: ["мова", "українська", "красива"]
      answer: "Українська мова красива"
```

### fill-in (MUST include `options`)

```yaml
- type: fill-in
  title: "Заповніть пропуски"
  items:  # minItems: 6
    - sentence: "Мама купує ___."
      answer: "молоко"
      options: ["молоко", "молока", "молоку", "молоком"]
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

### group-sort

```yaml
- type: group-sort
  title: "Розподіліть за групами"
  groups:  # 2-4 groups
    - name: "Group A"
      items: ["item1", "item2"]
    - name: "Group B"
      items: ["item3", "item4"]
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

---

## Mandatory Self-Check

1. **QUIZ**: exactly 1 `correct: true` per item, question >= 5 words
2. **FILL-IN**: `answer` must appear in `options`
3. **UNJUMBLE**: single sentence per item
4. **ANAGRAM**: scrambled letters = answer letters, space-separated
5. **MARK-THE-WORDS**: every answer string appears verbatim in text
6. **Integration**: does each activity combine 2+ reviewed skills?

### Activity Count Check

Count your activities before outputting. You MUST generate {ACTIVITY_COUNT_TARGET} activities.

{SHARED_ACTIVITY_RULES}
