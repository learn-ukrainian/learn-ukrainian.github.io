# Three-Layer Architecture: Plans + Content + Status

This document describes the unified architecture for curriculum management.

## Overview

The curriculum uses a three-layer separation:

1. **Plans** (source of truth) - What to build
2. **Content** (build artifacts) - The built content
3. **Status** (tracking) - Where we are

## Layer 1: Plans (`curriculum/l2-uk-en/plans/`)

Plans are the **source of truth** for what each module should contain.

### Structure

```
plans/
├── b1.yaml                     # Level plan (optional)
└── b1/
    ├── 01-how-to-talk-about-grammar.yaml
    ├── 02-language-about-verbs.yaml
    └── ...
```

### Module Plan Schema

```yaml
module: 01-how-to-talk-about-grammar
level: b1
sequence: 1
version: '1.0'
title: Як говорити про граматику
subtitle: Learning grammar terminology in Ukrainian  # optional
focus: grammar  # grammar | vocabulary | cultural | history | biography | literature | integration | checkpoint
pedagogy: TTT   # TTT | PPP | seminar | workshop | review

objectives:
  - Learner can identify parts of speech using Ukrainian terminology
  - Learner can name all seven grammatical cases in Ukrainian

content_outline:
  - section: Introduction
    words: 200
    subsections:
      - Why learn grammar in Ukrainian
      - Connection to immersion learning
  - section: Parts of Speech
    words: 600
    subsections:
      - Nouns and verbs
      - Adjectives and adverbs

word_target: 1500
word_tolerance: 0.05  # ±5%

vocabulary:
  required:
    - дієслово (verb)
    - іменник (noun)
  recommended:
    - сполучник (conjunction)
  forbidden: []  # Words too advanced for this level

activities:
  types_required:
    - quiz
    - fill-in
    - match-up
  min_items_per_type: 6
  total_min_items: 30
  no_mirroring: true

connects_to:
  previous: null
  next: 02-language-about-verbs
  related:
    - 05-ready-for-immersion

constraints:
  min_engagement_boxes: 3
  min_examples: 10
  naturalness_threshold: 7
```

### What Plans Contain

- **Module identity**: slug, level, sequence, version
- **Learning goals**: title, objectives
- **Content structure**: content_outline with word counts
- **Vocabulary scope**: required, recommended, forbidden
- **Activity requirements**: types, minimums

### What Plans DON'T Contain

- Pedagogy details (handled by meta)
- Duration estimates
- Grammar point specifics
- Register/style guidance
- Prerequisites

## Layer 2: Content (`curriculum/l2-uk-en/{level}/`)

Content is the **built artifacts** generated from plans.

### Structure

```
b1/
├── meta/
│   └── 01-how-to-talk-about-grammar.yaml  # Build config
├── 01-how-to-talk-about-grammar.md        # Content prose
├── activities/
│   └── 01-how-to-talk-about-grammar.yaml  # Activity definitions
├── vocabulary/
│   └── 01-how-to-talk-about-grammar.yaml  # Vocabulary data
└── audit/
    └── 01-how-to-talk-about-grammar-review.md  # Audit results
```

### Meta Files

Meta files extend plans with build-specific configuration:

```yaml
# Everything from plan, plus:
pedagogy: PPP
duration: 60  # minutes
immersion: "75% Ukrainian"
register: розмовний

grammar:
  - Parts of speech names in Ukrainian
  - Case names in Ukrainian

naturalness:
  score: 9
  status: PASS
```

## Layer 3: Status (`curriculum/l2-uk-en/status/`)

Status tracks **where we are** in the build process.

### Structure

```
status/
├── a1.yaml
├── a2.yaml
├── b1.yaml
├── b2.yaml
├── c1.yaml
├── c2.yaml
├── b2-hist.yaml
├── c1-bio.yaml
├── c1-hist.yaml
└── lit.yaml
```

### Status Schema

```yaml
level: b1
updated: '2026-01-26T12:55:27+00:00'

summary:
  total: 92
  planned: 0      # Has plan only
  content: 0      # Has content MD
  activities: 0   # Has activities YAML
  reviewed: 92    # Passed naturalness check

modules:
  01-how-to-talk-about-grammar:
    status: reviewed
    plan_version: '1.0'
    content_words: 2241
    word_target: 3000
    activity_count: 16
    naturalness: 9
    last_updated: '2026-01-26'
```

### Status Stages

1. **planned** - Has plan file in `plans/{level}/`, no content
2. **content** - Has content MD file (>100 words)
3. **activities** - Has activities YAML file
4. **reviewed** - Has naturalness score >= threshold (default 7)

## Agent Workflow

```
1. READ plan:     plans/{level}/{slug}.yaml
2. READ meta:     {level}/meta/{slug}.yaml
3. WRITE content: {level}/{slug}.md
4. WRITE activities: {level}/activities/{slug}.yaml
5. UPDATE status: status/{level}.yaml
```

## Scripts

### Extract Plans from Meta Files

```bash
# Extract all plans for a level
.venv/bin/python scripts/extract_plans.py b1

# Extract single module
.venv/bin/python scripts/extract_plans.py b1 5

# Extract range
.venv/bin/python scripts/extract_plans.py b1 1-10

# Validate existing plans
.venv/bin/python scripts/extract_plans.py --validate b1
```

### Update Status

```bash
# Update all modules in a level
.venv/bin/python scripts/update_status.py b1

# Initialize status file from scratch
.venv/bin/python scripts/update_status.py --init b1

# Update all levels
.venv/bin/python scripts/update_status.py all
```

## Schemas

- `schemas/module-plan.schema.json` - Module plan validation
- `schemas/level-plan.schema.json` - Level plan validation
- `schemas/level-status.schema.json` - Status file validation

## Migration History

The three-layer architecture was implemented in January 2026 to:

1. **Separate concerns**: Plans (what) vs Meta (how) vs Status (where)
2. **Enable querying**: YAML status files instead of markdown
3. **Unify tracks**: Core levels and specialized tracks use same structure
4. **Support automation**: Scripts can read/update status programmatically

### Migration Steps

1. Created `schemas/level-status.schema.json`
2. Created `scripts/extract_plans.py` to extract plans from meta
3. Created `scripts/update_status.py` to generate status files
4. Extracted 736 module plans across all levels
5. Generated status files for all 10 levels
