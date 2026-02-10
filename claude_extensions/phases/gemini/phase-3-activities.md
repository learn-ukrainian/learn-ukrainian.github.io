# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
{CONTENT_PATH}
```

**Plan file** (vocabulary_hints — vocabulary list to follow):
```
{PLAN_PATH}
```

**Meta file** (activity count targets, pedagogy):
```
{META_PATH}
```

**Activity schema** (CRITICAL — defines allowed fields per activity type):
```
{SCHEMA_PATH}
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
3. **Seminar style** ({TRACK}): Reading Input → Analytical Output. Focus on comprehension, analysis, and critical thinking — NOT drill exercises.
4. **Activity count**: {ACTIVITY_COUNT_TARGET} activities (4-9 for seminar tracks)
5. **Type variety**: Use at least 3 different activity types
6. **Only `reading` type has `id` field** in seminar tracks — do NOT add `id` to other types
7. **`essay-response` rubric fields**: `criteria` / `description` / `points` (NOT `criterion` / `weight`)
8. **`mark-the-words` format**: Use `text` (no asterisks) + `answers` array

### CRITICAL: Activity Type Constraints for {TRACK}

**ALLOWED types (use ONLY these):** {ALLOWED_ACTIVITY_TYPES}

**FORBIDDEN types (audit will auto-FAIL if you use these):** {FORBIDDEN_ACTIVITY_TYPES}

Using a forbidden type wastes the entire activity generation phase. Check the allowed list BEFORE writing each activity.

### Vocabulary YAML Rules

1. **BARE LIST at root** — no `vocabulary:` wrapper
2. **Follow plan's vocabulary_hints** — include all required items, optionally include recommended
3. **Each entry needs**: `term`, `translation`, `ipa`, `pos` (part of speech)
4. **IPA must have correct stress** — verify stress placement
5. **Count target**: {VOCAB_COUNT_TARGET} items

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return TWO YAML blocks with clear delimiters:

{ACTIVITY_EXAMPLES}

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT add fields not in the schema (check schema carefully!)
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT add `id` field to non-reading activities (seminar tracks)
- Do NOT request skills or delegate to Claude
- If you're unsure about a schema field, add:
  `NEEDS_HELP: Cannot determine correct schema for {activity_type} field "{field_name}"`
  `HELP_TYPE: yaml_schema`
