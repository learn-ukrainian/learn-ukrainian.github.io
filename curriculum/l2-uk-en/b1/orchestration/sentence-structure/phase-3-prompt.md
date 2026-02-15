# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

Before writing ANY YAML, confirm these targets:

| Target | Value |
|--------|-------|
| Module persona | Senior Language & Culture Specialist, acting as Construction Architect |
| Activities required | 6 |
| Items per activity | ≥8 |
| Required types | mark-the-words, match-up, quiz, fill-in, true-false, error-correction |
| Forbidden types | cloze, group-sort, unjumble, anagram, essay-response, critical-analysis |
| Vocabulary items | 25 |

Keep this table visible as you write. Every activity and vocab item must serve these targets.

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
curriculum/l2-uk-en/b1/04-sentence-structure.md
```

**Plan file** (vocabulary_hints — vocabulary list to follow):
```
curriculum/l2-uk-en/plans/b1/sentence-structure.yaml
```

**Meta file** (activity count targets, pedagogy):
```
curriculum/l2-uk-en/b1/meta/sentence-structure.yaml
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

1. **BARE LIST at root** — no `activities:` wrapper
2. **Schema compliance** — only use fields defined in the schema. `additionalProperties: false` means unlisted fields cause audit failure.
3. **Activity count**: 6 activities
4. **Type variety**: Use all 6 required types (mark-the-words, match-up, quiz, fill-in, true-false, error-correction)
5. **Only allowed types** — do NOT use cloze, group-sort, unjumble, anagram, essay-response, critical-analysis

### Common Schema Mistakes (FIX BEFORE OUTPUT)

1. **Quiz `explanation` placement** — `explanation` goes at the QUESTION level, NOT inside an option:
```yaml
explanation: "Пояснення чому ця відповідь правильна"
options:
  - text: "відповідь"
    correct: true
```

2. **Quiz question text length** — Every `question` field must be ≥5 words.

3. **No extra fields** — `additionalProperties: false`. ANY field not in the schema causes instant failure.

4. **mark-the-words format** — Use `text` (single string, no asterisks) + `answers` array + REQUIRED `instruction` field:
```yaml
- type: mark-the-words
  title: "Знайдіть підмети"
  instruction: "Знайдіть і позначте всі підмети в реченнях."
  text: "Sentence one. Sentence two. Sentence three."
  answers: ["word1", "word2", "word3"]
```

5. **error-correction** — ALL 5 fields REQUIRED per item: `sentence`, `error`, `answer`, `options` (4), `explanation`

6. **match-up** — needs `pairs` array with `left` and `right` fields, minimum 8 pairs

### YAML Formatting Rules (HARD FAIL if violated)

**Do NOT use Ukrainian angular quotes `«»` in YAML values.** They break YAML parsing.

```yaml
❌ WRONG: title: «Знайдіть пару»
✅ RIGHT: title: 'Знайдіть пару: термін та його значення'
```

**Rules:**
1. Never use `«»` in YAML
2. Quote any value containing `:` with single quotes
3. Double-check every `title`, `question`, `sentence`, `explanation`, and `text` field

### Vocabulary YAML Rules

1. **Object with `items:` wrapper** — NOT a bare list
2. **Follow plan's vocabulary_hints** — include all 10 required items + 5 recommended + fill to 25
3. **Each entry needs**: `lemma`, `translation`, `pos`
4. **Optional fields**: `ipa`, `gender` (for nouns: m/f/n), `notes`, `usage`, `example`

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Activities block (BARE LIST — no wrapper):

```
===ACTIVITIES_START===

- type: quiz
  title: "..."
  items:
    ...

- type: mark-the-words
  title: "..."
  ...

===ACTIVITIES_END===
```

Vocabulary block (OBJECT with `items:` wrapper):

```
===VOCABULARY_START===

items:
  - lemma: "підмет"
    translation: "subject"
    ipa: "/pidˈmɛt/"
    pos: "noun"
    gender: "m"

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
- Do NOT add fields not in the schema
- Do NOT wrap in `activities:` dictionary key
- Do NOT request skills or delegate to Claude
