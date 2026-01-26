# Planning Guide (Architecture v2.0)

This guide explains how to create and update module plans in the Learn Ukrainian curriculum.

## Overview

Plans are the **immutable source of truth** for what a module should contain. They are separate from the build artifacts to prevent semantic drift.

## Three-Layer Architecture

```
curriculum/l2-uk-en/
├── plans/                          # LAYER 1: SOURCE OF TRUTH (IMMUTABLE)
│   └── b1/
│       └── 01-grammar-talk.yaml    # What to build
│
├── b1/                             # LAYER 2: BUILD ARTIFACTS (MUTABLE)
│   ├── meta/
│   │   └── 01-grammar-talk.yaml    # How it was built
│   ├── 01-grammar-talk.md          # Content
│   ├── activities/
│   └── vocabulary/
│
└── b1/status/                      # LAYER 3: TRACKING (AUTO-GENERATED)
    └── 01-grammar-talk.json        # Current status
```

## Plan Structure

Module plans are stored in `curriculum/l2-uk-en/plans/{level}/{slug}.yaml`.

### Required Fields

| Field | Description |
|-------|-------------|
| `module` | Slug (matches filename) |
| `level` | CEFR level (a1, b2-hist, etc.) |
| `sequence` | Module number |
| `version` | Plan version |
| `title` | Ukrainian title |
| `focus` | Module focus (grammar, history, etc.) |
| `objectives` | List of learning goals |
| `content_outline` | Section-by-section breakdown with word targets |
| `word_target` | Total Ukrainian word count required |

### Optional Fields

| Field | Description |
|-------|-------------|
| `subtitle` | English subtitle |
| `word_tolerance` | Tolerance for word count (default: 0.10) |
| `vocabulary_hints` | Required and recommended words |
| `activity_hints` | Required activity types |
| `connects_to` | Module connections |
| `constraints` | Quality constraints |

### Example Plan

```yaml
module: kozatstvo-vytoky
level: b2-hist
sequence: 15
version: '1.0'
title: Виникнення козацтва
subtitle: Origins of the Cossacks

focus: history
pedagogy: seminar

objectives:
  - Learner can explain the origins of the Ukrainian Cossacks
  - Learner can describe the role of the Wild Fields
  - Learner can identify key early Cossack figures

content_outline:
  - section: Вступ
    words: 400
    subsections:
      - Historical context
      - The Wild Fields
  - section: Перші козаки
    words: 800
    subsections:
      - Origins and etymology
      - Early settlements
  - section: Січ
    words: 800
    subsections:
      - Formation of the Sich
      - Social structure

word_target: 4000
word_tolerance: 0.05

vocabulary_hints:
  required:
    - козак
    - січ
    - Запоріжжя
  recommended:
    - ватажок
    - кіш

activity_hints:
  types_required:
    - quiz
    - fill-in
    - match-up
    - reading
  min_items_per_type: 6
  total_min_items: 30

constraints:
  min_engagement_boxes: 6
  min_examples: 28
  naturalness_threshold: 8
```

## Focus Areas

| Focus | Description | Levels |
|-------|-------------|--------|
| `grammar` | Grammar-focused lessons | A1-B2 |
| `vocabulary` | Vocabulary expansion | A1-B2 |
| `cultural` | Cultural content | B1-C1 |
| `history` | Historical narratives | B2-HIST |
| `biography` | Famous Ukrainians | C1-BIO |
| `literature` | Literary analysis | LIT |
| `integration` | Review/consolidation | All |
| `checkpoint` | Assessment modules | All |

## How to Create a Plan

### 1. Manual Creation (Human)

Create a new YAML file in the `plans/` directory following the schema:

```bash
# Create new plan
touch curriculum/l2-uk-en/plans/b1/42-new-module.yaml
```

Edit the file with required fields and validate:

```bash
# Validate against schema
.venv/bin/python scripts/validate_plan.py plans/b1/42-new-module.yaml
```

### 2. Automated Extraction (Migration)

If a module already has planning data in its `meta.yaml`, extract it:

```bash
# Extract single module
.venv/bin/python scripts/extract_plans.py b1 42

# Extract all modules for a level
.venv/bin/python scripts/extract_plans.py b1

# Validate extracted plans
.venv/bin/python scripts/extract_plans.py --validate b1
```

## How to Update a Plan

1. **Modify the YAML file** in `plans/`
2. **Increment version** (e.g., '1.0' → '1.1')
3. **Commit the change** (human-only task)
4. **Re-audit**: Run `scripts/audit_module.py` to update the status cache

```yaml
# Before
version: '1.0'

# After
version: '1.1'
```

## Plan Immutability Rule

> **CRITICAL**: AI Agents are FORBIDDEN from modifying plan files.

If an agent determines that a plan requirement is unachievable:

1. **STOP** building
2. **REPORT** the issue: "Plan requires X but Y is not achievable because Z"
3. Human reviews and decides:
   - Update the plan
   - Grant a specific exception
   - Insist on the original target

See `claude_extensions/NON-NEGOTIABLE-RULES.md` Rule 7 for full details.

## Plan vs Meta

| Aspect | Plan | Meta |
|--------|------|------|
| **Location** | `plans/{level}/{slug}.yaml` | `{level}/meta/{slug}.yaml` |
| **Mutability** | IMMUTABLE (by agents) | MUTABLE |
| **Contains** | What to build | How it was built |
| **Updated by** | Humans only | Agents and humans |
| **Versioned** | Yes (`version` field) | No |

### What Goes Where

**Plan (IMMUTABLE):**
- `content_outline` - Section structure and word targets
- `word_target` - Total word count requirement
- `objectives` - Learning objectives
- `vocabulary_hints.required` - Required vocabulary
- `activity_hints.types_required` - Required activity types

**Meta (MUTABLE):**
- `naturalness.score` - Quality score from audit
- `naturalness.status` - PASS/FAIL status
- `build.last_modified` - Build timestamp

## Agent Workflow

```
1. READ plan:     plans/{level}/{slug}.yaml         # Source of truth
2. READ meta:     {level}/meta/{slug}.yaml          # Build config
3. WRITE content: {level}/{slug}.md                 # Content
4. WRITE activities: {level}/activities/{slug}.yaml # Activities
5. RUN audit:     audit_module.py                   # Validation
6. CACHE status:  {level}/status/{slug}.json        # Auto-generated
```

## Validation

### Schema Validation

```bash
# Validate single plan
.venv/bin/python scripts/validate_plan.py plans/b1/01-grammar-talk.yaml

# Validate all plans for a level
.venv/bin/python scripts/validate_plan.py plans/b1/
```

### Word Count Validation

The `content_outline` section words must sum to `word_target`:

```yaml
content_outline:
  - section: A
    words: 300
  - section: B
    words: 500
  - section: C
    words: 400

word_target: 1200  # 300 + 500 + 400 = 1200 ✓
```

## Related Documentation

- `docs/ARCHITECTURE-PLANS.md` - Three-layer architecture overview
- `docs/STATUS-SYSTEM.md` - Status caching system
- `schemas/module-plan.schema.json` - Plan schema
- `claude_extensions/NON-NEGOTIABLE-RULES.md` - Rule 7 (Plan Immutability)
