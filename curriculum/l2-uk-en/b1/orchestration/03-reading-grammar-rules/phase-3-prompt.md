# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

Before writing ANY YAML, confirm these targets:

| Target | Value |
|--------|-------|
| Skill identity | Patient & Supportive Ukrainian Tutor |
| Persona flavor | The Helpful Neighbor |
| Module persona | Senior Language & Culture Specialist, acting as Law Student |
| Activities required | 5–6 |
| Items per activity | ≥8 (quiz, fill-in, true-false, match-up), ≥6 (error-correction), ≥10 (mark-the-words) |
| Required types | mark-the-words, true-false, fill-in, match-up, quiz, error-correction |
| Priority types | quiz, match-up, fill-in, error-correction |
| Vocabulary items | 25 |

Keep this table visible as you write. Every activity and vocab item must serve these targets.

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
curriculum/l2-uk-en/b1/03-reading-grammar-rules.md
```

**Plan file** (vocabulary_hints — vocabulary list to follow):
```
curriculum/l2-uk-en/plans/b1/reading-grammar-rules.yaml
```

**Meta file** (activity count targets, pedagogy):
```
curriculum/l2-uk-en/b1/meta/03-reading-grammar-rules.yaml
```

**Activity schema** (CRITICAL — defines allowed fields per activity type):
```
schemas/activities-b1.schema.json
```

**Activity reference guide**:
```
docs/ACTIVITY-YAML-REFERENCE.md
```

## Your Task

Generate two YAML blocks: activities and vocabulary.

### Activities YAML Rules

1. **BARE LIST at root** — no `activities:` wrapper, no `module:` or `level:` headers
2. **Schema compliance** — only use fields defined in the schema. `additionalProperties: false` means unlisted fields cause audit failure.
3. **Activity count**: 6 activities (matching the 6 required types from the plan)
4. **Type variety**: Use all 6 types: mark-the-words, true-false, fill-in, match-up, quiz, error-correction
5. **Only `reading` type has `id` field** — do NOT add `id` to other types

### CRITICAL: Activity Type Constraints for b1

**ALLOWED types (use ONLY these):** quiz, match-up, fill-in, error-correction, mark-the-words, essay-response, critical-analysis, true-false, translate, select

**FORBIDDEN types (audit will auto-FAIL if you use these):** cloze, group-sort, unjumble, anagram

Using a forbidden type wastes the entire activity generation phase. Check the allowed list BEFORE writing each activity.

### Common Schema Mistakes (FIX BEFORE OUTPUT)

1. **Quiz `explanation` placement** — `explanation` goes at the QUESTION level, NOT inside an option.
2. **Quiz question text length** — Every `question` field must be ≥5 words.
3. **No extra fields** — The schema uses `additionalProperties: false`. ANY field not in the schema causes instant failure.
4. **Vocabulary YAML structure** — Use object with `items:` array wrapper. Each entry uses `lemma` (NOT `term`), `translation`, `pos`.

### Activity Quality Standards (MANDATORY)

1. **Production over recognition** — At least 2 activities must require the learner to PRODUCE language (fill-in, error-correction count as production)
2. **Plausible example sentences** — Every sentence must be something a real Ukrainian speaker might actually say or encounter in a grammar textbook
3. **mark-the-words minimum** — Must have at least 3 separate text passages
4. **Error-correction precision** — Each item must have exactly one clear error with one correct fix
5. **Item count consistency** — Activities of the same type should have similar item counts (±2)

### YAML Formatting Rules (HARD FAIL if violated)

**Do NOT use Ukrainian angular quotes «» in YAML values.** They break YAML parsing when combined with colons.

```yaml
❌ WRONG (guillemets + colon = YAML parse error):
  title: «Знайдіть пару: термін та його значення»

✅ RIGHT (plain strings, quote with single quotes if value contains colon):
  title: 'Знайдіть пару: термін та його значення'
```

**Rules:**
1. **Never use «» in YAML** — use plain text or single/double quotes
2. **Quote any value containing `:` ** with single quotes
3. **Double-check** every `title`, `question`, `sentence`, `explanation`, and `text` field

### Vocabulary YAML Rules

1. **Object with `items:` wrapper** — NOT a bare list
2. **Follow plan's vocabulary_hints** — include all 10 required items, plus 15 from recommended and related terms
3. **Each entry needs**: `lemma`, `translation`, `pos`
4. **Optional fields**: `ipa`, `gender` (for nouns: m/f/n), `aspect` (for verbs), `notes`, `usage`, `example`
5. **Count target**: 25 items

### mark-the-words format (IMPORTANT)

```yaml
- type: mark-the-words
  title: "Знайдіть інструкції"
  instruction: "Знайдіть і позначте всі слова-інструкції в тексті."
  text: "Гарний день приніс радість у серце. Маленька дитина грала в парку."
  answers: ["день", "радість", "серце", "дитина", "парку"]
```

### error-correction format (ALL 5 fields REQUIRED per item)

```yaml
- type: error-correction
  title: "Виправте помилку"
  items:
    - sentence: "Я кушаю яблуко кожен день."
      error: "кушаю"
      answer: "їм"
      options: ["їм", "їду", "їжу", "кусаю"]
      explanation: "Кушати — русизм, правильно їсти."
```

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Activities block (BARE LIST — no wrapper):

```
===ACTIVITIES_START===

- type: mark-the-words
  ...

- type: true-false
  ...

- type: fill-in
  ...

- type: match-up
  ...

- type: quiz
  ...

- type: error-correction
  ...

===ACTIVITIES_END===
```

Vocabulary block (OBJECT with `items:` wrapper):

```
===VOCABULARY_START===

items:
  - lemma: "використовується"
    translation: "is used"
    pos: "verb"
  ...

===VOCABULARY_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 3: Activities + Vocabulary
**Step**: {what you were doing when friction occurred, or "Full YAML generation"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT add fields not in the schema (check schema carefully!)
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT add `id` field to non-reading activities
- Do NOT request skills or delegate to Claude
