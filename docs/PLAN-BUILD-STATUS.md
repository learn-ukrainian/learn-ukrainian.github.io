# Plan-Build-Status System

> **Status:** Draft (Epic #465)
> **Last Updated:** 2025-01-26

## Overview

This document describes the Plan-Build-Status architecture with clear separation of:

1. **Plans** (immutable) - What we intend to build
2. **Build** (mutable) - What we actually built
3. **Status** (cached) - Current state of each module

## Sources of Truth

Plans are NOT created from thin air. They must be grounded in authoritative sources.

### Core Levels (A1-C2)

| Source | Purpose |
|--------|---------|
| **Ukrainian State Standard 2024** | Grammar scope, vocabulary frequency, CEFR mapping |
| **CEFR Guidelines** | Level descriptors, can-do statements, complexity targets |
| **docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md** | Level-specific vocabulary and grammar scope |

### Quality Standards (All Levels)

| Standard | Document | Purpose |
|----------|----------|---------|
| **Module Richness** | `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Activity counts, engagement boxes, examples |
| **Patriotic Content** | Embedded in templates | Ukrainian identity, pride, cultural awareness |
| **Decolonization** | Embedded in templates | Counter Russian imperial narratives |
| **Propaganda Busting** | Embedded in templates | Expose and counter Russian disinformation |

### Specialized Tracks

| Track | Source of Truth | Status |
|-------|-----------------|--------|
| **hist** (Cossack Era) | `docs/references/textbooks/`, Ukrainian Wikipedia, Claude corpus | 🟡 50% - modules in progress |
| **istoriohrafiia** (Historiography) | Ukrainian university history programs (TBD), Ukrainian Wikipedia | ⚠️ Needs planning - specific sources to be identified |
| **bio** (Biographies) | Claude's training data + Ukrainian internet verification (each person researched individually) | ✅ Almost done |
| **lit** (Literature) | **ukrlib** (Ukrainian digital library) | ✅ Done |
| **b2-pro** (Professional) | TBD - domain-specific Ukrainian resources | ⚠️ Needs planning - scope and sources to be defined |
| **c1-pro** (Professional) | TBD - domain-specific Ukrainian resources | ⚠️ Needs planning - scope and sources to be defined |

**Note on Ukrainian Wikipedia:** The Ukrainian Wikipedia editorial team maintains high standards. While vigilance is always needed, it's considered a reliable source for Ukrainian historical and biographical content.

**For tracks marked ✅:**
- Create plans from original sources (not reverse-engineered from builds)
- Plans define what MUST be covered based on authoritative sources
- Audit catches gaps/errors in existing content

**For tracks marked 🟡 or ⚠️:**
- Proper research from authentic Ukrainian sources required
- Verification against Russian propaganda influences
- Detailed module-level planning with primary sources identified
- Human review and approval before agent use

### External Resources & References

#### Freely Available Content (`docs/resources/`)

| Type | Examples | Usage |
|------|----------|-------|
| YouTube | Educational videos | ✅ USE freely, **must cite source** |
| Ukrainian Lessons Podcast | ULP episodes | ✅ USE freely, **must cite source** |
| Internet articles | Blogs, Wikipedia | ✅ USE freely, **must cite source** |

**No permission needed** for freely available content - just attribute properly.

Managed in `docs/resources/external_resources.yaml`.

#### Reference Materials (`docs/references/`)

| Folder | Content | Usage |
|--------|---------|-------|
| `textbooks/` | Ukrainian high school history textbooks | Source of truth for hist |
| `textbooks-txt/` | Text versions for searching | Same as above |
| `dobra-forma/` | Language learning resource | Reference material |
| `private/` | **Purchased materials** (gitignored) | ⚠️ Learn from, **NEVER copy** |

**Private folder rule:** Materials in `private/` were purchased. Standard academic citation applies:

| ✅ We CAN | ❌ We CANNOT |
|-----------|--------------|
| Reference with citation: *"In Anna Ohoiko's book, p. 45, she explains that..."* | Copy/paste text verbatim |
| Paraphrase concepts in our own words | Reproduce tables, diagrams, exercises |
| Learn methodology and approaches | Claim ideas as our own without citation |

This is standard academic practice - cite sources, paraphrase, attribute ideas.

### Why This Matters

Without proper sources of truth:
- Agents "fill gaps" with generic content or hallucinations
- Russian propaganda narratives leak into history content
- Biographies repeat Soviet-era distortions
- Literature analysis lacks Ukrainian critical perspective

**The plan is only as good as its sources.**

## Problem Statement

The previous architecture conflated planning and building:

| Issue | Impact |
|-------|--------|
| Plans stored in `meta.yaml` | Agents corrupt plans during building |
| Status requires full re-audit | Slow, wasteful |
| Track plans are thin | Agents "fill gaps" inconsistently |
| Sources of truth undefined | Content quality varies wildly |

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PLAN-BUILD-STATUS SYSTEM                            │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────┐
    │   HUMAN AUTHORED    │
    │   (Source of Truth) │
    └──────────┬──────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PLANS (IMMUTABLE)                                  │
│                                                                              │
│  curriculum/l2-uk-en/plans/                                                  │
│  ├── b1.yaml                    # Level plan (scope, phases, vocabulary)     │
│  ├── b1/                                                                     │
│  │   ├── 01-how-to-talk-about-grammar.yaml   # Module plan (outline, targets)│
│  │   ├── 02-language-about-verbs.yaml                                        │
│  │   └── ...                                                                 │
│  ├── hist.yaml                                                            │
│  ├── hist/                                                                │
│  │   ├── kozatstvo-vytoky.yaml                                               │
│  │   └── ...                                                                 │
│  └── ...                                                                     │
│                                                                              │
│  RULES:                                                                      │
│  - Created by humans (or approved by humans)                                 │
│  - NEVER modified by build agents                                            │
│  - Validated against JSON schema                                             │
└─────────────────────────────────────────────────────────────────────────────┘
               │
               │ Agents READ plans
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUILD (MUTABLE)                                    │
│                                                                              │
│  curriculum/l2-uk-en/{level}/                                                │
│  ├── {slug}.md                  # Lesson content                             │
│  ├── activities/{slug}.yaml     # Activities                                 │
│  ├── vocabulary/{slug}.yaml     # Vocabulary                                 │
│  └── meta/{slug}.yaml           # Build metadata (NOT planning data)         │
│                                                                              │
│  meta/{slug}.yaml contains ONLY:                                             │
│  - naturalness score (agent-evaluated)                                       │
│  - last_modified timestamp                                                   │
│  - build-time flags                                                          │
│                                                                              │
│  RULES:                                                                      │
│  - Created and modified by agents                                            │
│  - Must conform to plan requirements                                         │
│  - Validated by audit system                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
               │
               │ Audit validates build against plan
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           STATUS (CACHED)                                    │
│                                                                              │
│  curriculum/l2-uk-en/{level}/status/                                         │
│  ├── {slug}.json                # Cached audit results per module            │
│  └── _level.json                # Aggregated level status                    │
│                                                                              │
│  {slug}.json contains:                                                       │
│  - gate statuses (meta, lesson, activities, vocab, naturalness)              │
│  - violation counts and blocking issues                                      │
│  - source file mtimes (for cache invalidation)                               │
│  - last audit timestamp                                                      │
│                                                                              │
│  RULES:                                                                      │
│  - Generated by audit system                                                 │
│  - Updated incrementally (only when source changes)                          │
│  - Read by status commands for fast reporting                                │
└─────────────────────────────────────────────────────────────────────────────┘
               │
               │ Status commands read cache
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REPORTS (GENERATED)                                │
│                                                                              │
│  curriculum/l2-uk-en/{level}/{level}-status.md   # Human-readable status     │
│  curriculum/l2-uk-en/{level}/audit/{slug}-review.md  # Detailed audit report │
│                                                                              │
│  RULES:                                                                      │
│  - Generated from status cache                                               │
│  - Never edited manually                                                     │
│  - Regenerated on demand (fast, from cache)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## File Formats

### Level Plan (`plans/{level}.yaml`)

```yaml
# plans/b1.yaml
level: b1
track: core                    # core | history | biography | literature
version: "2.0"

# High-level scope
overview:
  total_modules: 91
  description: "Intermediate Ukrainian with focus on aspect, motion verbs, and cultural immersion"
  prerequisites: [a1, a2]

# Vocabulary scope
vocabulary:
  cumulative_from: [a1, a2]    # Build on these levels
  new_words: 3000              # Target new vocabulary
  sources:
    - "docs/l2-uk-en/B1-CURRICULUM-PLAN.md"

# Grammar scope
grammar:
  - "Verbal aspect (perfective/imperfective)"
  - "Motion verbs with prefixes"
  - "Complex sentence structures"
  - "Passive voice introduction"

# Module phases
phases:
  - name: "Metalanguage"
    modules: [1, 5]
    focus: "Grammar terminology in Ukrainian"

  - name: "Aspect System"
    modules: [6, 15]
    focus: "Complete verbal aspect"

  - name: "Motion Verbs"
    modules: [16, 25]
    focus: "Determinate/indeterminate, prefixes"

  # ... more phases

# Constraints for all modules in this level
constraints:
  min_word_target: 3000
  max_word_target: 5000
  min_engagement_boxes: 5
  min_examples: 24
  immersion_target: 0.98
  naturalness_threshold: 8
```

### Module Plan (`plans/{level}/{slug}.yaml`)

```yaml
# plans/b1/01-how-to-talk-about-grammar.yaml
module: 01-how-to-talk-about-grammar
level: b1
sequence: 1
version: "2.0"

# Metadata
title: "Як говорити про граматику"
subtitle: "Ukrainian Grammatical Terminology"
focus: grammar
pedagogy: TTT

# Learning objectives
objectives:
  - "Master Ukrainian names for parts of speech"
  - "Understand grammatical categories in Ukrainian"
  - "Read grammar explanations written in Ukrainian"

# Content structure (IMMUTABLE after approval)
content_outline:
  - section: "Частини мови"
    words: 600
    subsections:
      - "Іменник, дієслово, прикметник"
      - "Прислівник, займенник, числівник"
    key_concepts:
      - іменник
      - дієслово
      - прикметник

  - section: "Граматичні категорії"
    words: 800
    subsections:
      - "Рід, число, відмінок"
      - "Час, вид, спосіб"
    key_concepts:
      - рід
      - число
      - відмінок

  - section: "Читання граматичних правил"
    words: 1000
    subsections:
      - "Typical rule structure"
      - "Practice reading real rules"

  - section: "Практика"
    words: 600
    subsections:
      - "Identify parts of speech"
      - "Parse grammatical information"

# Word targets
word_target: 3500              # Total (excluding summary)
word_tolerance: 0.05           # ±5% acceptable

# Vocabulary scope
vocabulary:
  required:                    # MUST appear in content
    - іменник
    - дієслово
    - прикметник
    - прислівник
    - займенник
    - числівник
    - рід
    - число
    - відмінок
  recommended:                 # MAY appear
    - морфема
    - корінь
    - суфікс
    - префікс
  forbidden:                   # Must NOT appear (too advanced)
    - дієприкметник
    - дієприслівник

# Activity requirements
activities:
  types_required:
    - quiz
    - fill-in
    - match-up
  min_items_per_type: 8
  total_min_items: 30
  no_mirroring: true           # Activities must not copy lesson verbatim

# Connections
connects_to:
  previous: null
  next: 02-language-about-verbs
  related:
    - 03-reading-grammar-rules
    - 04-sentence-structure

# Constraints (override level defaults if needed)
constraints:
  min_engagement_boxes: 5
  min_examples: 24
  immersion_target: 0.98
  naturalness_threshold: 8
```

### Build Metadata (`{level}/meta/{slug}.yaml`)

```yaml
# curriculum/l2-uk-en/b1/meta/01-how-to-talk-about-grammar.yaml
# NOTE: This file contains ONLY build-time metadata, NOT planning data

module: 01-how-to-talk-about-grammar
level: b1

# Build status
build:
  created: "2025-01-15"
  last_modified: "2025-01-26"

# Agent-evaluated scores
naturalness:
  score: 9
  status: PASS
  evaluated_by: "claude-opus-4-5"
  evaluated_at: "2025-01-26T14:30:00Z"

# Build flags
flags:
  needs_review: false
  has_warnings: false
```

### Status Cache (`{level}/status/{slug}.json`)

```json
{
  "module": "01-how-to-talk-about-grammar",
  "level": "b1",
  "plan_version": "2.0",

  "last_audit": "2025-01-26T14:30:00Z",
  "audit_duration_ms": 1250,

  "source_mtimes": {
    "plan": "2025-01-15T10:00:00Z",
    "md": "2025-01-26T14:00:00Z",
    "meta": "2025-01-26T14:30:00Z",
    "activities": "2025-01-26T14:00:00Z",
    "vocabulary": "2025-01-26T12:00:00Z"
  },

  "gates": {
    "meta": {
      "status": "pass",
      "violations": 0,
      "checks": ["yaml_valid", "required_fields", "naturalness_present"]
    },
    "lesson": {
      "status": "pass",
      "violations": 0,
      "word_count": 3520,
      "word_target": 3500,
      "word_percentage": 100.6,
      "checks": ["structure", "word_count", "engagement_boxes", "examples", "immersion"]
    },
    "activities": {
      "status": "fail",
      "violations": 2,
      "checks": ["schema", "item_counts", "type_coverage", "no_mirroring"],
      "failed_checks": [
        {"check": "schema", "message": "quiz item 3 missing options array"},
        {"check": "item_counts", "message": "fill-in has 6 items, minimum is 8"}
      ]
    },
    "vocabulary": {
      "status": "pass",
      "violations": 0,
      "item_count": 45,
      "checks": ["schema", "ipa_present", "required_vocab", "no_duplicates"]
    },
    "naturalness": {
      "status": "pass",
      "score": 9,
      "threshold": 8
    }
  },

  "overall": {
    "status": "fail",
    "pass_count": 4,
    "fail_count": 1,
    "blocking_issues": [
      "ACTIVITY_SCHEMA_ERROR: quiz item 3 missing options",
      "ACTIVITY_ITEM_COUNT: fill-in has 6 items, minimum is 8"
    ]
  }
}
```

## Workflow

### Creating a New Module

```
1. HUMAN: Create/approve plan
   plans/{level}/{slug}.yaml

2. AGENT: Generate content (reads plan, never modifies)
   /module-lesson {level} {num}
   → Creates {level}/{slug}.md

3. AGENT: Generate activities
   /module-act {level} {num}
   → Creates {level}/activities/{slug}.yaml

4. AGENT: Enrich vocabulary
   /module-vocab {level} {num}
   → Creates {level}/vocabulary/{slug}.yaml

5. AUDIT: Validate build against plan
   audit_module.py {level}/{slug}.md
   → Updates {level}/status/{slug}.json
   → Generates {level}/audit/{slug}-review.md

6. AGENT: Fix issues (if any)
   /module-fix {level} {num}
   → Reads plan + status cache
   → Fixes build files
   → Re-audits, updates cache

7. REPORT: View status
   /module-status {level} {num}
   → Reads from cache (fast)
   → Shows current state
```

### Status Update Flow

```
Source file changes
       │
       ▼
   Audit runs
       │
       ├──► Updates {slug}.json (cache)
       │
       ├──► Updates {slug}-review.md (detailed report)
       │
       └──► Triggers _level.json update (aggregated)

Status query
       │
       ▼
   Reads from cache
       │
       ├──► Check mtime: source > cache?
       │         │
       │         ├── Yes: Re-audit this module only
       │         │
       │         └── No: Return cached status
       │
       └──► Return status (< 1 second)
```

## Agent Rules

### MUST DO

1. **Always read plan** before generating content
2. **Follow plan exactly** - section names, word targets, vocabulary scope
3. **Update status cache** after every audit
4. **Report mismatches** - "Plan requires X but build has Y"

### MUST NOT DO

1. **Never modify plan files** - Plans are immutable
2. **Never add unplanned content** - Stick to plan scope
3. **Never skip cache update** - Status must stay current
4. **Never guess plan intent** - Ask if unclear

### SHOULD DO

1. **Check cache first** - Avoid unnecessary re-audits
2. **Batch fixes by component** - Use smart batching strategy
3. **Validate against plan** - Not just against build

## Migration from v1

See #468 for migration details. Summary:

1. Extract plans from existing `meta.yaml` → `plans/`
2. Strip planning data from `meta.yaml` → keep only runtime
3. Generate status cache from existing audit results
4. Update commands to use new paths

## Related Documents

### This Document Covers

- Plan/Build/Status separation
- File formats for plans and status cache
- Agent rules for plan consumption
- Workflow for creating modules from plans

### For Operational Details, See

- **`docs/ARCHITECTURE.md`** - Full system architecture (generators, components, validation)
- **`docs/SCRIPTS.md`** - Script reference (audit, generate, vocab)
- **`docs/MARKDOWN-FORMAT.md`** - Markdown syntax specification
- **`docs/ACTIVITY-YAML-REFERENCE.md`** - Activity format reference

### GitHub Issues

- [Epic #465: Plan-Build-Status System](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/465)
- [M1: Design Plan Schema #466](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/466)
- [JSON Schemas](../schemas/)
