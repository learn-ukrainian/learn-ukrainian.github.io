# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

Before writing ANY YAML, confirm these targets:

| Target | Value |
|--------|-------|
| Skill identity | Patient & Supportive Ukrainian Tutor |
| Persona flavor | The Helpful Neighbor |
| Module persona | Senior Language & Culture Specialist, acting as Ukrainian Tutor |
| Activities required | 4–6 |
| Items per activity | ≥6 |
| Required types | quiz, match-up |
| Priority types | quiz, match-up, fill-in, error-correction, mark-the-words, essay-response, critical-analysis |
| Vocabulary items | 25 |

Keep this table visible as you write. Every activity and vocab item must serve these targets.

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
curriculum/l2-uk-en/b1/language-about-verbs.md
```

**Plan file** (vocabulary_hints — vocabulary list to follow):
```
curriculum/l2-uk-en/plans/b1/language-about-verbs.yaml
```

**Meta file** (activity count targets, pedagogy):
```
curriculum/l2-uk-en/b1/meta/language-about-verbs.yaml
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
3. **Activity count**: 5 activities (minimum 4, maximum 6)
4. **Type variety**: Use at least 3 different activity types
5. **Only `reading` type has `id` field** — do NOT add `id` to other types

### CRITICAL: Activity Type Constraints

**ALLOWED types (use ONLY these):** quiz, match-up, fill-in, error-correction, mark-the-words, essay-response, critical-analysis, true-false, translate, select

**FORBIDDEN types (audit will auto-FAIL if you use these):** cloze, group-sort, unjumble, anagram, reading, comparative-study, authorial-intent

Using a forbidden type wastes the entire activity generation phase. Check the allowed list BEFORE writing each activity.

### Common Schema Mistakes (FIX BEFORE OUTPUT)

1. **Quiz `explanation` placement** — `explanation` goes at the QUESTION level, NOT inside an option.
2. **Quiz question text length** — Every `question` field must be ≥5 words.
3. **No extra fields** — The schema uses `additionalProperties: false`. ANY field not in the schema causes instant failure.
4. **Vocabulary YAML structure** — Use object with `items:` array wrapper.
5. **error-correction requires ALL 5 fields per item:** `sentence`, `error`, `answer`, `options` (4), `explanation`
6. **mark-the-words requires `instruction` field** — it is REQUIRED, plus `text` + `answers`

### Activity Quality Standards

1. **Production over recognition** — At least 2 activities must require the learner to PRODUCE language (fill-in, error-correction, translate, mark-the-words).
2. **Plausible example sentences** — Every sentence must be something a real Ukrainian speaker might say or encounter. FORBIDDEN: philosophical/motivational statements, meta-sentences about learning.
3. **Error-correction precision** — Each item must have exactly one clear error with one correct fix. The error must be a plausible learner mistake.

### Language Quality

- **Typography**: ALWAYS use Ukrainian angular quotes «...» (never straight quotes "...")
- **No Russianisms**: кушати→їсти, приймати участь→брати участь
- **No Russian characters**: ы, э, ё, ъ must NEVER appear

### Vocabulary YAML Rules

1. **Object with `items:` wrapper** — NOT a bare list
2. **Follow plan's vocabulary_hints** — include all required items (вид, доконаний вид, недоконаний вид, час, теперішній час, минулий час, майбутній час, дія, процес, результат, заперечення, наказова форма), plus recommended items
3. **Each entry needs**: `lemma`, `translation`, `pos`
4. **Optional fields**: `ipa`, `gender`, `aspect`, `notes`, `usage`, `example`
5. **Count target**: 25 items

## Output Format

Activities block (BARE LIST — no wrapper):

```
===ACTIVITIES_START===

- type: match-up
  title: "..."
  pairs:
    ...

- type: quiz
  title: "..."
  items:
    ...

===ACTIVITIES_END===
```

Vocabulary block (OBJECT with `items:` wrapper):

```
===VOCABULARY_START===

items:
  - lemma: "вид"
    translation: "aspect"
    pos: "noun"
    gender: "m"
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
- Do NOT wrap activities in `activities:` dictionary key
- Do NOT add `id` field to non-reading activities
- Do NOT request skills or delegate to Claude
