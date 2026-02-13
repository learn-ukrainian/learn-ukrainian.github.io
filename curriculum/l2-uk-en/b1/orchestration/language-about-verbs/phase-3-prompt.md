# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

Before writing ANY YAML, confirm these targets:

| Target | Value |
|--------|-------|
| Skill identity | Senior Language & Culture Specialist |
| Module persona | Senior Language & Culture Specialist, acting as Ukrainian Tutor |
| Activities required | 12–14 |
| Items per activity | ≥8 (varies by type, see schema) |
| Required types | fill-in, match-up, quiz, true-false, group-sort, unjumble, error-correction, cloze, mark-the-words, select, translate |
| Priority types | fill-in (2+), unjumble (2+), error-correction (2+), cloze (1+) |
| Vocabulary items | 25+ |

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
3. **Core track style**: Focus on grammar terminology practice — matching terms to definitions, sorting by category, fill-in terminology, error correction of misused terms.
4. **Activity count**: 12-14 activities
5. **Type variety**: Use at least 5 different activity types
6. **Item counts per type (B1 minimums)**:
   - quiz: 8 items
   - fill-in: 8 items (must have `options: [...]` with 4 per item)
   - true-false: 8 items
   - match-up: 8 pairs
   - cloze: 14 blanks (use inline `{a|b|c}` format)
   - unjumble: 6 items
   - error-correction: 6 items
   - select: 6 items
   - translate: 6 items
   - group-sort: no fixed minimum, use 15+ items for richness
   - mark-the-words: use `text` (no asterisks) + `answers` array

7. **mark-the-words format example**:
```yaml
- type: mark-the-words
  text: Гарний день приніс радість у серце.
  answers:
    - день
    - радість
    - серце
```

### Vocabulary YAML Rules

1. **Root structure**: `items:` key containing list of entries
2. **Follow plan's vocabulary_hints** — include all required items, optionally include recommended
3. **Each entry needs**: `lemma`, `translation`, `ipa`, `pos` (part of speech)
4. **IPA must have correct stress** — verify stress placement
5. **Count target**: 25+ items
6. **Gender field**: Include `gender` for nouns (m, f, n)

### Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return TWO YAML blocks with clear delimiters:

```
===ACTIVITIES_START===
- type: group-sort
  title: "..."
  instruction: "..."
  groups:
    - name: "..."
      items: [...]
    - name: "..."
      items: [...]

- type: match-up
  title: "..."
  instruction: "..."
  pairs:
    - left: "..."
      right: "..."
  # ... 8+ pairs

# ... more activities (12-14 total)
===ACTIVITIES_END===
```

```
===VOCABULARY_START===
items:
  - lemma: вид
    ipa: /wɪd/
    translation: aspect
    pos: noun
    gender: m
  - lemma: доконаний вид
    ipa: /doˈkɔnɐnɪj wɪd/
    translation: perfective aspect
    pos: noun phrase
  # ... 25+ items
===VOCABULARY_END===
```

## Friction Report (MANDATORY)

After your YAML blocks, include:

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
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys (activities are BARE LIST, vocabulary uses `items:`)
- Do NOT request skills or delegate to Claude
