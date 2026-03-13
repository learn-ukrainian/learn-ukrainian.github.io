# Activity Build: Generate Activities from Plans + Textbook RAG

> **You are Gemini, executing the activities phase of the pipeline.**
> **Your task: Build complete activity YAML from the provided activity plans, using textbook exercises as source material.**

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

{DECODABLE_VOCABULARY}

## Activity Plans (Your Blueprint)

These plans were generated during the content phase. Build each one into a full activity:

```yaml
{ACTIVITY_PLANS}
```

## Textbook Exercise Examples (Adapt These)

The following real textbook exercises were found via RAG search. **Adapt** them to match the plan's type and focus — do NOT copy verbatim, but USE the exercise patterns, difficulty level, and pedagogical approach.

{TEXTBOOK_EXERCISES}

**Key rule**: You are ADAPTING real exercises, not inventing from scratch. Every activity should be traceable to either a plan + textbook source, or a plan + lesson content.

## Module Sequence Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

> **These constraints apply to activities too.** If verbs are banned, do NOT create fill-in or quiz items that use verb forms.

## Your Input

Read these files from disk:

**Lesson content** (activities must reinforce this content):
```
{CONTENT_PATH}
```

**Plan file (SOURCE OF TRUTH):**
```yaml
{PLAN_CONTENT}
```

{VOCAB_HINTS}

**Activity schema** (CRITICAL — defines allowed fields per activity type):
```
{SCHEMA_PATH}
```

**Activity reference guide**:
```
docs/ACTIVITY-YAML-REFERENCE.md
```

## Downstream Audit Gates

- **Schema violations**: `additionalProperties: false` means ANY unlisted field = instant fail
- **Item counts**: Check `minItems` in schema for each type
- **Russian characters**: ы, э, ё, ъ = hard fail
- **No IPA**: NEVER include IPA symbols or `ipa` fields

## CRITICAL: Activity Type Constraints for {TRACK}

**ALLOWED types (use ONLY these):** {ALLOWED_ACTIVITY_TYPES}

**FORBIDDEN types (audit will auto-FAIL):** {FORBIDDEN_ACTIVITY_TYPES}

---

## Your Task

For each plan entry, build a complete activity. Then generate the vocabulary YAML.

### Activities YAML Rules

1. **BARE LIST at root** — no `activities:` wrapper
2. **Schema compliance** — only fields defined in the schema
3. **Match each plan** — every plan entry should produce one activity
4. **Type variety**: at least 3 different activity types
5. **Activities test LANGUAGE, not content recall**

### Vocabulary YAML Rules

Generate vocabulary items that cover all Ukrainian words taught in the lesson content.

---

## Output Format

```
===ACTIVITIES_START===
- type: quiz
  title: "..."
  items:
    ...

- type: fill-in
  ...
===ACTIVITIES_END===
```

```
===VOCABULARY_START===
items:
  - lemma: "слово"
    translation: "word"
    pos: "noun"
    gender: "n"
    ...
===VOCABULARY_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Activity Build
**Step**: {what you were doing}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | PLAN_MISMATCH
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```
