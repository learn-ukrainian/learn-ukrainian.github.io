# Phase 1: module-meta

Create the module metadata sidecar file (`meta/{slug}.yaml`).

## Usage

```
/module-meta {level} {module_num}
```

## Input Required

1. **Curriculum plan**: `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`
2. **Module position**: Which module number in the sequence
3. **Previous vocabulary**: For tracks, cumulative from A1→B2 core

## Output

Single file: `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`

## Schema

```yaml
# Required fields
module: {level}-{num}           # e.g., b2-hist-01
id: {level}-{num}
title: "Назва українською"      # Ukrainian title
subtitle: "English subtitle"
slug: {slug}                    # kebab-case, no numbers for tracks
version: '2.0'
phase: {phase from plan}        # e.g., B2-HIST.1 [Витоки]
focus: history|grammar|vocabulary|cultural|biography|integration
pedagogy: seminar|TTT|PPP|CLIL
register: публіцистичний|науковий|розмовний
duration: 150                   # minutes
transliteration: none           # for B2+

# Learning objectives (3-5, in Ukrainian)
objectives:
  - "Учень може [measurable verb]..."
  - "Учень може [measurable verb]..."

# Grammar focus (2-4 points)
grammar:
  - "Grammar point 1"
  - "Grammar point 2"

# Content structure with word targets
word_target: 4000               # total for module
content_outline:
  - section: "Назва секції"
    words: 200
    points:
      - Key point 1
      - Key point 2

# Vocabulary guidance
vocabulary_hints:
  required:                     # Must appear in content
    - word1 (translation)
    - word2 (translation)
  recommended:                  # May appear
    - word3 (translation)

# Activity planning
activity_hints:
  - type: reading
    focus: "What to read"
    source: "Where from"
  - type: quiz
    focus: "What to test"
    items: 12+

# Sources (minimum 2)
sources:
  - name: "Source title"
    url: "https://..."
    type: reference|primary|academic
    notes: "Why this source"

# Module connections
prerequisites:
  - "What learner needs first"
connects_to:
  - "Related modules"
```

## Measurable Verbs for Objectives

Use Bloom's taxonomy verbs:
- **Remember**: describe, identify, list, name
- **Understand**: explain, summarize, compare
- **Apply**: demonstrate, use, illustrate
- **Analyze**: analyze, differentiate, examine
- **Evaluate**: evaluate, argue, justify
- **Create**: create, design, construct

## Word Targets by Level

| Level | Target Range |
|-------|-------------|
| B2-HIST | 3000-5000 |
| C1-BIO | 4000-6000 |
| LIT | 5000-8000 |
| C2 | 4000-6000 |

## Process

1. Read the curriculum plan for this module
2. Extract title, phase, focus from plan
3. Write 3-5 measurable objectives in Ukrainian
4. Create content_outline with word targets summing to word_target
5. List vocabulary_hints from plan (required vs recommended)
6. Plan activity types matching pedagogy
7. Add 2+ credible sources
8. Write prerequisites and connections

## Validation (Next Phase)

This file will be validated by `module-meta-qa`. Do not proceed to content until meta passes QA.

## Example Command

```bash
# For B2-HIST module 5
/module-meta b2-hist 5
```

---

**Next phase:** `module-meta-qa` → validates this file before locking
