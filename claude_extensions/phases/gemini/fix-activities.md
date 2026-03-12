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

**Plan file (SOURCE OF TRUTH):**
```yaml
{PLAN_CONTENT}
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

## Mandatory Self-Check (run BEFORE outputting)

After writing your fixed activities, perform these 5 structural checks mentally. Any failure here = audit will fail with a critical error.

**1. SELECT min_correct match**
For every `select` activity, every question's `min_correct` must equal the number of options with `correct: true`. Count them. They must match exactly.

**2. QUIZ single correct**
For every `quiz` activity, every question must have exactly 1 option with `correct: true`. Not 0, not 2. Exactly 1.

**3. FILL-IN answer in options**
For every `fill-in` activity, every item's `answer` value must appear verbatim in its `options` list. If the answer is not in the options, the student can never select it.

**4. TRANSLATE single correct**
For every `translate` activity, every item must have exactly 1 option with `correct: true`.

**5. MARK-THE-WORDS answers in text**
For every `mark-the-words` activity, every string in `answers` must appear verbatim in the `text` field. If an answer word is not in the text, the student cannot mark it.

**6. UNJUMBLE no run-ons**
For every `unjumble` activity, every `answer` must be a single sentence. If a capital letter appears mid-answer without preceding punctuation (`.  !  ?  :`), you have merged two sentences. Split into two separate items instead.

**7. UNJUMBLE vocabulary scope**
For every `unjumble` activity, every word in every `words` array must come from the plan's `vocabulary_hints` OR be a common function word (preposition, conjunction, particle). Do NOT introduce grammar forms not yet taught. If this module teaches dative PRONOUNS only, do not use possessive adjective dative forms (моїй, твоїй, нашій…) — those are dative NOUNS scope (a separate module).

If any check fails: fix it BEFORE outputting. Do not declare fixes complete if these checks fail.

## Boundaries

- Do NOT output content — this phase is ACTIVITIES/VOCABULARY ONLY
- Do NOT add fields not in the schema
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT add `id` field to non-reading activities (seminar tracks)
- Do NOT use FORBIDDEN activity types — they will cause audit failure
- If you cannot fix an error, explain why in "Fixes NOT Applied"
