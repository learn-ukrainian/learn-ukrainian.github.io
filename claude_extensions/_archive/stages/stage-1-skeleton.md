# Stage 1: Skeleton

Create the module skeleton with frontmatter, section headers, and vocabulary table.

## Input Required

- **Level**: A1, A2, B1, B2, C1, C2
- **Module number**: 01-XX (depends on level)
- **Curriculum plan section**: Extracted from `{LEVEL}-CURRICULUM-PLAN.md`

## Output

Three files:

1. `meta/{num}-{slug}.yaml`: Module configuration (formerly frontmatter)
2. `vocabulary/{num}-{slug}.yaml`: Structured vocabulary data
3. `{num}-{slug}.md`: Pure content (headers + placeholders)

**Example for A1 Module 35 "At the Café":**
- `meta/35-at-the-cafe.yaml`
- `vocabulary/35-at-the-cafe.yaml`
- `35-at-the-cafe.md`

## Metadata YAML Template (`meta/{num}-{slug}.yaml`)

```yaml
id: { number }
slug: '{slug}'
title: '{title from plan}'
subtitle: '{subtitle if applicable}'
version: '2.0'
phase: '{phase}'
pedagogy: '{PPP|TTT|CLIL}'
objectives:
  - 'Learner can...'
  - 'Learner can...'
# Note: vocabulary_count is dynamic, no longer needed in meta
```

## Vocabulary YAML Format (`vocabulary/{num}-{slug}.yaml`)

Refer to `docs/dev/VOCAB_YAML_SCHEMA.md` for full details.

```yaml
config:
  standard: '2024'
items:
  - lemma: слово
    ipa: /ˈsɫɔwɔ/
    translation: word
    pos: noun
    gender: n
    tags: []
```

## Section Structure by Pedagogy (`{num}-{slug}.md`)

### PPP (A1-A2)

```markdown
# {title}

## Warm-up

[placeholder]

## Presentation

[placeholder]

## Practice

[placeholder]

## Production

[placeholder]

## Cultural Insight

[placeholder]

---

## Summary

[placeholder]
```

### TTT (B1+ grammar)

```markdown
# {title}

## Diagnostic

[placeholder]

## Analysis

[placeholder]

## Deep Dive

[placeholder]

## Practice

[placeholder]

---

## Summary

[placeholder]
```

### CLIL/Narrative (B1+ vocabulary/culture)

```markdown
# {title}

## Introduction

[placeholder]

## Immersive Narrative

[placeholder]

## Analysis

[placeholder]

## Grammar in Context

[placeholder]

---

## Summary

[placeholder]
```

## Validation

Before completing:

- [ ] Metadata YAML created valid ID, slug, and Objectives
- [ ] Vocabulary YAML created with valid Schema (POS, Gender)
- [ ] Module MD created with NO Frontmatter and NO Vocabulary table
- [ ] All section headers present in MD
- [ ] File naming conventions followed completely

## File Naming

- `curriculum/l2-uk-en/{level}/meta/{number}-{slugified-title}.yaml`
- `curriculum/l2-uk-en/{level}/vocabulary/{number}-{slugified-title}.yaml`
- `curriculum/l2-uk-en/{level}/{number}-{slugified-title}.md`
