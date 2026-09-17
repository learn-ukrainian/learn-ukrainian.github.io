---
type: Module
title: Content Pipeline and Build Runtime
description: Architectural specification of the lesson generation pipeline, build orchestration, and config-as-policy knobs.
tags: [pipeline, mdx, build, config-as-policy, generation]
---

# Content Pipeline and Build Runtime

> [!NOTE]
> OpenWiki is a non-authoritative locator. The authoritative sources for pipeline behavior are executable scripts under [`scripts/generate_mdx/`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/generate_mdx/), [`scripts/build/`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/build/), and configuration policy in [`scripts/config.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/config.py).

## Pipeline Overview

The content pipeline transforms structured lesson specifications (YAML, dialogue scripts, vocabulary records) into production-ready MDX pages rendered by the Astro site.

```mermaid
flowchart LR
    INPUT["Lesson Blueprint / YAML"] --> BUILD["scripts/build/ (Assembler)"]
    BUILD --> MDX_GEN["scripts/generate_mdx/"]
    MDX_GEN --> GATES["scripts/audit/ (QA Gates)"]
    GATES --> SITE["site/src/content/docs/"]
```

---

## Core Components

### 1. Generation Subsystem (`scripts/generate_mdx/`)
- [`core.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/generate_mdx/core.py): Orchestrates template filling and component assembly.
- [`converters.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/generate_mdx/converters.py): Converts internal lesson DSL nodes into JSX/Astro-compatible components (`<DialogueBox>`, `<VocabCard>`, `<FlashcardDeck>`).
- [`wire_navigation.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/generate_mdx/wire_navigation.py): Automates forward and backward lesson sequencing and breadcrumb links.
- [`generate_seo.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/generate_mdx/generate_seo.py): Emits OpenGraph metadata and structured schema tags.

### 2. Build Orchestration (`scripts/build/`)
- [`v7_build.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/build/v7_build.py): Primary build entrypoint for V7 curriculum authoring.
- [`lesson_assembler.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/build/lesson_assembler.py): Aggregates dialogue sections, grammar breakdowns, and interactive exercises.
- [`activity_renderer.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/build/activity_renderer.py): Renders interactive quizzes, fill-in-the-blank cards, and audio listening checks.
- [`lesson_gates.py`](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/scripts/build/lesson_gates.py): Enforces structural integrity, component order, and vocabulary constraints prior to committing output.

---

## Config-as-Policy (`scripts/config.py`)

All pedagogical parameters, CEFR track configurations, and immersion floors are defined in code as policy:

- **`TRACK_CONFIG`:** Specifies track personas, model choices (Flash vs Pro), and baseline immersion thresholds:
  - `a1`: Target immersion `[0.10, 0.50]`, Persona "The Helpful Neighbor".
  - `a2`: Target immersion `[0.50, 0.90]`, Persona "The Cultural Guide".
  - `b1`–`c2`: Advanced immersive tracks with progressive native Ukrainian ratios.
- **`IMMERSION_POLICIES`:** Authoritative structural sub-gates (`_l2_exposure_floor_gate`, `_long_uk_ceiling_gate`, `_component_density_gate`).

> [!TIP]
> Per [docs-authority-lifecycle.md](file:///home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot/docs/architecture/docs-authority-lifecycle.md), if any narrative document asserts immersion rules differing from `scripts/config.py`, the configuration values in `scripts/config.py` are the authoritative source of truth.
