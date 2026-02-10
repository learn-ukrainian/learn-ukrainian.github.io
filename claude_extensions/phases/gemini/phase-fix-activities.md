# Phase Fix-Activities: Activities-Only Fixes

> **You are Gemini, executing a targeted activities fix.**
> **Your ONLY task: Fix the ACTIVITIES and/or VOCABULARY files based on audit errors.**
> **Do NOT output content — only fixed activities and vocabulary.**

## Your Input

Read these files from disk:

**Current activities** (the file you are fixing):
```
{ACTIVITIES_PATH}
```

**Current vocabulary** (fix if audit mentions vocabulary issues):
```
{VOCAB_PATH}
```

**Plan file** (source of truth for vocabulary scope):
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

**Lesson content** (reference for activity alignment):
```
{CONTENT_PATH}
```

## Audit Errors to Fix

The following audit errors were found. Fix ALL of them:

```
{AUDIT_ERRORS}
```

## Activity Rules

1. **BARE LIST at root** — no `activities:` wrapper
2. **Schema compliance** — only use fields defined in the schema
3. **Only `reading` type has `id` field** in seminar tracks — do NOT add `id` to other types
4. **`essay-response` rubric fields**: `criteria` / `description` / `points` (NOT `criterion` / `weight`)
5. **`mark-the-words` format**: Use `text` (no asterisks) + `answers` array

### CRITICAL: Activity Type Constraints for {TRACK}

**ALLOWED types (use ONLY these):** {ALLOWED_ACTIVITY_TYPES}

**FORBIDDEN types (audit will auto-FAIL if you use these):** {FORBIDDEN_ACTIVITY_TYPES}

### Examples of Correct Format

{ACTIVITY_EXAMPLES}

## Output Format

**CRITICAL: Output fixed files between delimiter lines. Only output files that need changes.**

**Activity fixes:**

===ACTIVITIES_START===
(complete fixed activities YAML — bare list at root, NO `activities:` wrapper)
===ACTIVITIES_END===

**Vocabulary fixes** (only if audit flagged vocabulary issues):

===VOCABULARY_START===
(complete fixed vocabulary YAML)
===VOCABULARY_END===

**After all files, report what you changed:**

===CHANGES_START===
## Applied Fixes

1. Activity "{title}": {what changed} — {which audit error this addresses}
2. Vocabulary: {what changed} — {which audit error}

## Fixes NOT Applied (explain why)

- {If any fix was unclear or contradictory, explain here}
===CHANGES_END===

## Boundaries

- Do NOT output content — this phase is ACTIVITIES/VOCABULARY ONLY
- Do NOT add fields not in the schema
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT add `id` field to non-reading activities (seminar tracks)
- Do NOT use FORBIDDEN activity types — they will cause audit failure
- If you cannot fix an error, explain why in "Fixes NOT Applied"
