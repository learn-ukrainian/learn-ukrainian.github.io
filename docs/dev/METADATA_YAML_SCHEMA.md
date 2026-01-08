# Metadata YAML Schema

This schema defines the structure for `meta/{slug}.yaml` sidecar files used in A1-A2 and B1+ curriculum modules.

## File Location

- **Path**: `curriculum/l2-uk-en/{level}/meta/{module_slug}.yaml`
- **Example**: `curriculum/l2-uk-en/a2/meta/01-the-dative-i-pronouns.yaml`

## Schema Definition

```yaml
module: 'a2-01' # Required: Must match {level}-{num}
title: 'English Title' # Required: Display title in TOC and page
subtitle: 'English Sub' # Required: Displayed under title
version: '1.0' # Required: Major.Minor
phase: 'A2.1' # Required: CEFR sub-phase (A1.1-3, A2.1-3, etc)
pedagogy: 'PPP' # Required: PPP | TTT | CBI
duration: 60 # Required: Estimated duration in minutes
transliteration: none # Required: none | latin
focus: grammar # Required: grammar | vocabulary | history | biography | style | checkpoint
tags: # Optional: For search and grouping
  - cases
  - dative
grammar: # Required: Key grammar points taught
  - 'Dative pronouns'
  - 'Likes with подобатися'
objectives: # Required: Learning objectives (Learner can...)
  - 'Learner can use dative pronouns'
  - 'Learner can express likes'
vocabulary_count: 25 # Required: Total count of active vocabulary items
slug: '01-the-dative-i-pronouns' # Required: URL slug (minus level)
```

## Validation Rules

1. **Module/Slug Alignment**: `module` must match directory level and the number in `slug`.
2. **Pedagogy Match**:
   - A1/A2 must be `PPP`.
   - B1/B2/C1/C2 vary between `TTT` and `CBI`.
3. **Focus Verification**:
   - Modules with focus `history` must include history engagement boxes.
   - Modules with focus `biography` must follow biography naming conventions.
4. **Objective Count**: Minimum 3 objectives required.
5. **Vocabulary Count**: Must match the actual number of items in `vocabulary/{slug}.yaml`.

---

**Status:** Approved for A1-A2 standardization.
