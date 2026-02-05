# Learn Ukrainian Architecture

> **See also:**
> - `docs/ARCHITECTURE-PLANS.md` - Detailed three-layer architecture
> - `docs/STATUS-SYSTEM.md` - Status caching system
> - `docs/PLANNING-GUIDE.md` - How to create/update plans

## Overview

Learn Ukrainian (CO) is a content factory that generates Ukrainian language learning materials from Markdown source files.

## Architecture v2.0 (Plan-Build-Status)

The curriculum follows a strict three-layer separation of concerns to ensure consistency and prevent semantic drift.

### 1. Plans (Immutable Source of Truth)

**Level plans:** `curriculum/l2-uk-en/plans/{level}.yaml` — Phases, scope, pedagogy notes
**Module plans:** `curriculum/l2-uk-en/plans/{level}/{slug}.yaml` — Individual module specs

- **Ownership**: Humans (Architects)
- **Content**: `content_outline`, `word_target`, `vocabulary_hints`, `activity_hints`, `sources`
- **Rule**: NEVER modified by build agents. If a plan is wrong, it must be updated by a human.
- **Human-readable view**: `docs/l2-uk-en/{LEVEL}-PLAN-GENERATED.md` (run `scripts/generate_plan_markdown.py`)

### 2. Build (Mutable Artifacts)

Located in `curriculum/l2-uk-en/{level}/`.
- **Ownership**: AI Agents (Builders)
- **Components**:
  - `{slug}.md`: Lesson prose (matches plan outline).
  - `activities/{slug}.yaml`: Interactive exercises.
  - `vocabulary/{slug}.yaml`: IPA, translations, and metadata for words.
  - `meta/{slug}.yaml`: Build-time metadata (naturalness score, last modified).

### 3. Status (Cached Audit Results)

Located in `curriculum/l2-uk-en/{level}/status/{slug}.json`.
- **Ownership**: System (Auditor)
- **Content**: Results of all 16+ audit gates, violation counts, and source file timestamps.
- **Benefit**: Enables instant status reporting without re-auditing every module.

```
┌─────────────────────────────────────┐    ┌──────────────────────────┐
│ plans/                              │    │ {level}/                 │
│   └── {slug}.yaml (Immutable Plan)  │───▶│   ├── {slug}.md          │
│       - content_outline             │    │   ├── activities/        │
│       - word_target                 │    │   └── vocabulary/        │
└─────────────────────────────────────┘    └────────────┬─────────────┘
                                                        │
                                                        ▼
                                           ┌──────────────────────────┐
                                           │ {level}/status/          │
                                           │   └── {slug}.json        │
                                           │       (Audit Cache)      │
                                           └──────────────────────────┘
```

## Directory Structure

```
learn-ukrainian/
├── curriculum/                    # SOURCE OF TRUTH
│   └── l2-uk-en/
│       ├── plans/                 # ⭐ IMMUTABLE PLANS (v2.0)
│       │   ├── a1.yaml            # Level plan (phases, scope)
│       │   ├── a1/                # Module plans
│       │   │   ├── 01-the-cyrillic-code-i.yaml
│       │   │   └── ...
│       │   ├── b2-hist.yaml       # Track level plan
│       │   ├── b2-hist/           # Track module plans
│       │   └── ...
│       ├── a1/                    # A1 build artifacts (34)
│       ├── a2/                    # A2 build artifacts (50)
│       ├── b1/                    # B1 build artifacts (85)
│       ├── b2/                    # B2 build artifacts (110)
│       ├── c1/                    # C1 build artifacts (160)
│       ├── c2/                    # C2 build artifacts (100)
│       ├── b2-hist/               # B2-HIST track (61)
│       ├── c1-bio/                # C1-BIO track (25)
│       ├── lit/                   # LIT modules (30) - post-C1 track
│       └── vocabulary.db          # SQLite vocabulary database
│
├── scripts/                       # GENERATOR CODE
│   ├── generate_mdx.py            # MDX generator (Python)
│   ├── generate_json.py           # JSON generator (Python)
│   ├── generate_plan_markdown.py  # ⭐ Plan → readable markdown
│   ├── audit_module.py            # Module quality checker
│   ├── calculate_richness.py      # Content richness scoring
│   ├── pipeline.py                # Full pipeline (lint → generate → validate)
│   ├── validate_mdx.py            # MDX content validation
│   ├── validate_html.py           # HTML rendering validation
│   └── audit/                     # Audit module components
│       ├── checks/                # Individual check modules
│       ├── cleaners.py            # Text preprocessing
│       └── report.py              # Report generation
│
├── docusaurus/                    # DOCUSAURUS PROJECT
│   ├── docs/                      # Generated MDX files
│   │   ├── a1/module-XX.mdx
│   │   └── ...
│   └── src/components/            # React activity components
│       ├── Quiz.tsx
│       ├── MatchUp.tsx
│       ├── FillIn.tsx
│       └── ...
│
├── output/                        # GENERATED OUTPUT
│   └── json/l2-uk-en/             # Vibe import data
│       ├── a1/module-01.json
│       └── ...
│
├── docs/                          # DOCUMENTATION
│   ├── ARCHITECTURE.md            # This file
│   ├── MARKDOWN-FORMAT.md         # Markdown syntax spec
│   └── SCRIPTS.md                 # Scripts reference
│
└── claude_extensions/             # CLAUDE CODE EXTENSIONS
    ├── commands/                  # Slash commands (/module, /module-stage-1, etc.)
    ├── skills/                    # Skills (grammar-check, vocab-enrichment, etc.)
    ├── stages/                    # Module creation workflow stages (1-4)
    └── quick-ref/                 # Level-specific quick references (a1.md, b1.md, etc.)
```

## Claude Extensions Architecture

The `claude_extensions/` directory contains configuration for Claude Code, organized into four layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER COMMANDS                             │
│    /module b1 10     /checkpoint b2 25     /review-content       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    COMMANDS (Orchestration)                      │
│                                                                 │
│   claude_extensions/commands/                                   │
│   - module.md              → Routes to correct stage            │
│   - module-stage-1.md      → Skeleton creation                  │
│   - module-stage-2.md      → Content writing                    │
│   - module-stage-3.md      → Activity creation                  │
│   - module-stage-4.md      → Review & fix                       │
│   - review-content.md      → Content quality review             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   TEMPLATES (Structure)  │     │   QUICK-REFS (Context)  │
│                         │     │                         │
│ docs/l2-uk-en/templates/│     │ claude_extensions/      │
│ - b1-grammar-template   │     │ quick-ref/              │
│ - b2-checkpoint-template│     │ - a1.md, a2.md          │
│ - lit-module-template   │     │ - b1.md, b2.md          │
│ - [26 total templates]  │     │ - c1.md, c2.md          │
└─────────────────────────┘     └─────────────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SKILLS (Cross-Cutting Utilities)               │
│                                                                 │
│   claude_extensions/skills/                                     │
│                                                                 │
│   UTILITY SKILLS:                                               │
│   - grammar-check           → CEFR grammar validation           │
│   - vocab-enrichment        → IPA, POS, usage notes             │
│   - prompt-engineering      → AI documentation optimization     │
│                                                                 │
│   MODULE ARCHITECT SKILLS:                                      │
│   - grammar-module-architect    → B1-B2 grammar modules         │
│   - vocab-module-architect      → B1 vocabulary expansion       │
│   - cultural-module-architect   → B1-C1 cultural modules        │
│   - history-module-architect    → B2 history, C1 biography      │
│   - integration-module-architect→ B1-B2 integration modules     │
│   - checkpoint                  → All levels checkpoint modules │
│   - literature-module-architect → LIT track modules             │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Purpose | Location | Invocation |
|-------|---------|----------|------------|
| **Commands** | Orchestrate multi-step workflows | `claude_extensions/commands/` | `/module`, `/checkpoint` |
| **Templates** | Define authoritative module structure | `docs/l2-uk-en/templates/` | Read by commands/stages |
| **Quick-Refs** | Provide level-specific constraints | `claude_extensions/quick-ref/` | Read by commands/skills |
| **Skills** | Handle cross-cutting concerns | `claude_extensions/skills/` | `/grammar-check`, `/vocab-enrichment` |

### Design Decisions

**Two types of skills:**

1. **Utility Skills** (cross-cutting concerns):
   - `grammar-check` — Validate grammar against CEFR level
   - `vocab-enrichment` — Add IPA, POS, usage notes
   - `prompt-engineering` — Optimize AI documentation

2. **Module Architect Skills** (focus-area guidance):
   - `grammar-module-architect` — B1-B2 grammar modules
   - `vocab-module-architect` — B1 vocabulary expansion modules
   - `cultural-module-architect` — B1-C1 cultural modules
   - `history-module-architect` — B2 history, C1 biography modules
   - `integration-module-architect` — B1-B2 integration modules
   - `checkpoint` — All levels checkpoint modules
   - `literature-module-architect` — LIT track modules

**Skill vs Command vs Template:**
- **Skill**: Either utility (validation, enrichment) or module architect (focus-area guidance)
- **Command**: Multi-step workflow orchestration (`/module` runs stages 1-4)
- **Template**: Authoritative structure for a module type (always read first)

### Current Skills

**Utility Skills:**

| Skill | Purpose | Status |
|-------|---------|--------|
| `grammar-check` | CEFR grammar validation | ✅ Active |
| `vocab-enrichment` | IPA, POS, usage notes | ✅ Active |
| `prompt-engineering` | AI documentation optimization | ✅ Active |

**Module Architect Skills:**

| Skill | Focus Area | Levels | Status |
|-------|------------|--------|--------|
| `grammar-module-architect` | Grammar (aspect, motion, participles) | B1-B2 | ✅ Active |
| `vocab-module-architect` | Vocabulary expansion (collocations, synonymy) | B1 | ✅ Active |
| `cultural-module-architect` | Cultural modules (regions, music, cinema) | B1-C1 | ✅ Active |
| `history-module-architect` | History & biography modules | B2-C1 | ✅ Active |
| `integration-module-architect` | Integration & review modules | B1-B2 | ✅ Active |
| `checkpoint` | Checkpoint modules (phase-end assessment) | All | ✅ Active |
| `literature-module-architect` | LIT track (post-C1 literature) | LIT | ✅ Active |

## Module Types

| Type | Tags | Description | Levels |
|------|------|-------------|--------|
| `grammar` | grammar, cases, verbs, aspect | Grammar-focused lessons | A1-B1 |
| `vocabulary` | vocabulary, vocab | Word-building lessons | A1-B2 |
| `checkpoint` | review, checkpoint, assessment | Progress assessment | All |
| `history` | history | Ukrainian history narratives | B2+ |
| `biography` | biography | Famous Ukrainians | B2+ |
| `idioms` | idioms, phraseology | Idiomatic expressions | B2 |
| `literature` | literature, poetry, prose | Text analysis | C1 |
| `skills` | skills, academic, writing | Academic skills | C1 |
| `culture` | culture, regions, music | Cultural content | B2+ |
| `functional` | functional, dialogue, role-play | Practical communication | A2-B1 |

## JSON Output Schema (v2)

```json
{
  "$schema": "../../../schemas/vibe-module.schema.json",
  "lesson": {
    "id": "lesson-uk-B2-168",
    "moduleId": "mod-uk-B2-168",
    "languagePair": "l2-uk-en",
    "moduleNumber": 168,
    "moduleType": "history",
    "immersionLevel": 0.85,
    "title": "History: Kyivan Rus II",
    "titleUk": "Київська Русь II: Золота доба",
    "level": "B2",
    "phase": "B2.2",
    "objectives": ["..."],
    "tags": ["history", "kyivan-rus", "culture"],
    "totalDuration": 50,
    "transliterationMode": "none",
    "sections": [
      {
        "id": "section-intro",
        "name": "Вступ",
        "nameEn": "Introduction",
        "type": "intro",
        "content": "raw markdown content..."
      }
    ],
    "rawMarkdown": "full source markdown...",
    "version": 2
  },
  "activities": [...],
  "vocabulary": {...}
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `moduleType` | enum | Inferred from tags (grammar, history, etc.) |
| `immersionLevel` | float | 0.0-1.0, percentage of Ukrainian content |
| `sections` | array | Sections with raw markdown content |
| `rawMarkdown` | string | Full source markdown for reference |

### Immersion Levels by CEFR

| Level | Modules | Folder | Immersion |
|-------|---------|--------|-----------|
| A1 | M01-34 | `a1/` | 10-40% (graduated) |
| A2 | M01-50 | `a2/` | 40-50% |
| B1 | M01-85 | `b1/` | 65% (M01-05) → **100%** (M06+) |
| B2 | M01-110 | `b2/` | **100%** |
| C1 | M01-160 | `c1/` | **100%** |
| C2 | M01-100 | `c2/` | **100%** |
| LIT | M01-30 | `lit/` | **100%** |

**Note:** B1 M01-05 are transitional "Bridge" modules (~65% immersion) that teach grammar metalanguage. B1 M06+ and all B2/C1/C2 use 100% Ukrainian immersion. English is only allowed in vocabulary table translations.

## Docusaurus Web Output

The web interface uses Docusaurus with custom React components for interactive activities.

### Activity Components

Located in `docusaurus/src/components/`:

| Component | Activity Type | Description |
|-----------|--------------|-------------|
| `Quiz.tsx` | quiz | Multiple choice with single answer |
| `MatchUp.tsx` | match-up | Drag & drop pair matching |
| `FillIn.tsx` | fill-in | Gap fill with dropdowns |
| `GroupSort.tsx` | group-sort | Sort items into categories |
| `Unjumble.tsx` | unjumble | Reorder words into sentences |
| `TrueFalse.tsx` | true-false | Statement validation |
| `Anagram.tsx` | anagram | Letter unscrambling (A1 only) |
| `ErrorCorrection.tsx` | error-correction | Find and fix errors (A2+) |
| `Cloze.tsx` | cloze | Passage completion (A2+) |
| `Select.tsx` | select | Multi-checkbox selection |
| `Translate.tsx` | translate | Translation multiple choice |

### Features

- **Interactive activities**: All activities with immediate feedback
- **Answer shuffling**: Options randomized on each page load
- **Progress tracking**: Visual feedback for correct/incorrect
- **Mobile responsive**: Works on all device sizes
- **GitHub Pages**: Deployed to krisztiankoos.github.io/learn-ukrainian

## Markdown Format

See `docs/MARKDOWN-FORMAT.md` for the complete spec.

### Key Patterns

```markdown
# Section Headers
## warm-up | Розминка
## presentation | Презентація
## practice | Практика
# Вправи (Activities)
# Словник (Vocabulary)

# Answer Syntax
> [!answer] **відповідь**

# Activity Blocks
## quiz: Title
1. Question?
   - [ ] Wrong
   - [x] Correct
   > Explanation

## match-up: Title
| Left | Right |
|------|-------|
| word | слово |
```

## Quality Validation Systems

Learn Ukrainian uses a multi-layered quality validation approach with four complementary systems:

### 1. Audit (Required)

**Purpose**: Structural compliance, pedagogy, format, richness validation

**Script**: `scripts/audit_module.py`

**What it checks**:
- Structure (required sections, headers, frontmatter)
- Pedagogy (PPP/TTT compliance, activity sequencing)
- Format (markdown syntax, activity YAML schemas)
- Richness (examples count, engagement boxes, variety metrics)
- Vocabulary (plan compliance, no duplicates across modules)
- Immersion percentage (CEFR-appropriate UK/EN ratio)

**Usage**:
```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{num}-*.md
```

**Output**: Terminal report + optional markdown report in `audit/` directory

**Gates**: Blocks pipeline generation if FAIL

### 2. Grammar Validation (Recommended for B1+)

**Purpose**: Ukrainian language correctness validation

**Type**: LLM-based (Gemini API)

**Skill**: `/grammar-validate` (Claude Code)

**What it checks**:
- **Russianisms**: кушать → їсти, кофе → кава, обязательно → обов'язково
- **Calques**: робити сенс → мати сенс, мати місце → відбуватися
- **Surzhyk**: Mixed Ukrainian-Russian forms
- **Unnatural word order**: Influenced by English/Russian structure
- **Case/gender/number agreement**: Morphological correctness
- **CEFR appropriateness**: Complexity matches level

**Usage**:
```bash
# Automated (requires GEMINI_API_KEY)
.venv/bin/python scripts/audit_module.py {file} --validate-grammar

# Manual (Claude Code)
/grammar-validate
[paste module content]
```

**Output**: JSON report with violations, severity, corrections

**Gates**: Informational (doesn't block audit)

**Trusted Sources**:

| Source | Type | Use For |
|--------|------|---------|
| **Словник.UA** (slovnyk.ua) | Online dictionary | Standard spelling |
| **Словарь Грінченка** | Historical dictionary | Authentic Ukrainian forms |
| **Антоненко-Давидович "Як ми говоримо"** | Style guide | Russianisms vs authentic |

**NOT Trusted:** Google Translate, Russian-Ukrainian dictionaries

### 3. Content Quality Review (Optional)

**Purpose**: Pedagogical quality assessment

**Type**: LLM-based (Gemini API)

**Skill**: `/review-content` (Claude Code)

**What it checks** (8 dimensions, 0-10 scale):
1. **Pedagogical Coherence**: Objectives ↔ activities alignment, scaffolding
2. **Example Quality**: Authenticity, cultural relevance, CEFR appropriateness
3. **Engagement & Interest**: Boring vs interesting, repetitive vs varied
4. **Cultural Context**: Ukrainian-specific vs generic, historical accuracy
5. **Explanation Quality**: Clarity, visual aids, progressive disclosure
6. **Narrative Flow**: Logical progression, transitions, cohesion
7. **Vocabulary Usage**: Frequency, contextualization, reinforcement
8. **Activity Quality**: Naturalness, difficulty, distractors, engagement, variety

**Usage**:
```bash
# Automated (requires GEMINI_API_KEY + AUDIT_CONTENT_QUALITY=true)
AUDIT_CONTENT_QUALITY=true .venv/bin/python scripts/audit_module.py {file}

# Manual (Claude Code)
/review-content
[paste module content]
```

**Output**: Markdown report with scores (0-10) and recommendations

**Gates**: Informational (doesn't block audit)

**Documentation**: `docs/CONTENT-QUALITY-AUDIT.md`

### 4. Activity Quality Validation (Optional)

**Purpose**: Activity-specific quality assessment

**Type**: Hybrid (deterministic + manual validation)

**What it checks** (5 dimensions):
- **Naturalness** (1-5): Robotic → Highly Natural
- **Difficulty** (3-option): too_easy | appropriate | too_hard
- **Distractor Quality** (1-5): Nonsense → Excellent
- **Engagement** (1-5): Boring → Highly Engaging
- **Variety** (0-100%): Mechanical pattern detection

**CEFR Quality Gates**:

| Level | Min Naturalness | Min Variety | Min Distractors | Max Inappropriate |
|-------|-----------------|-------------|-----------------|-------------------|
| B1 | 3.5 | 60% | 4.0 | ≤20% |
| B2 | 4.0 | 65% | 4.2 | ≤15% |
| C1 | 4.5 | 70% | 4.5 | ≤10% |
| C2 | 4.8 | 75% | 5.0 | ≤5% |

**Workflow**:
```bash
# 1. Generate queue with deterministic checks
npm run quality:generate l2-uk-en b1 50

# 2. Manual validation (fill in YAML fields)
# Edit: curriculum/l2-uk-en/b1/audit/50-{slug}-quality-queue.yaml

# 3. Finalize quality report
npm run quality:finalize l2-uk-en b1 50
```

**Output**: Markdown report in `audit/` directory, shown in audit output

**Gates**: Informational (doesn't block audit)

**Documentation**: `docs/SCRIPTS.md` - Activity Quality Validation section

### When to Use Which System

| Stage | Audit | Grammar | Content Review | Activity Quality |
|-------|-------|---------|----------------|------------------|
| **After Stage 1 (Skeleton)** | ✅ Structure | ❌ No content | ❌ No content | ❌ No activities |
| **After Stage 2 (Content)** | ✅ Full | ✅ Yes | ✅ Optional | ❌ No activities |
| **After Stage 3 (Activities)** | ✅ Full | ✅ Yes | ✅ Optional | ✅ Optional |
| **After Stage 4 (Review/Fix)** | ✅ Must PASS | ✅ Recommended | ✅ Recommended | ✅ High-stakes |
| **Before Release** | ✅ Must PASS | ✅ Recommended | ✅ Recommended | ⚠️ C1/C2 only |

### Complete B1+ Workflow

For the complete end-to-end workflow including all validation systems:

**👤 Human users:** See **`docs/DEVELOPER-GUIDE.md`** - Human workflow guide

**🤖 AI agents:** See **`CLAUDE.md`** - Module workflow section (lines 118-153)

**Workflow covers:**
- What commands you execute (copy-paste ready)
- What Claude does automatically
- Decision tree (when to run what)
- Typical session workflow

**AI guide** covers:
- 4-stage module creation (skeleton → content → activities → review/fix)
- All quality validation systems (audit, grammar, content, activity quality)
- Pipeline generation (MDX + JSON)
- Troubleshooting and checklists

## Generator Usage

```bash
# Generate MDX for Docusaurus
npm run generate                    # All modules
npm run generate l2-uk-en a1        # Specific level
npm run generate l2-uk-en a1 5      # Single module

# Generate JSON for Vibe app
npm run generate:json               # All modules
npm run generate:json l2-uk-en a1   # Specific level
npm run generate:json l2-uk-en a1 5 # Single module
```

## Vocabulary Management

```bash
# Initialize fresh SQLite database
npm run vocab:init

# Scan all modules and populate database
npm run vocab:scan

# Enrich modules with new/review vocabulary splits
npm run vocab:enrich

# Force re-process all modules (even those with Review sections)
npm run vocab:enrich:force

# Full rebuild: init + scan
npm run vocab:rebuild
```

The vocabulary system tracks:
- **Lemmas**: 2,000+ individual words with IPA, translations, POS
- **Expressions**: 250+ multi-word units (idioms, collocations)
- **First module**: Where each word first appears in curriculum
- **New/Review split**: Vocabulary sections show new words with full details, review words with module references

## External Resources Management

**Single source of truth:** `docs/resources/external_resources.yaml`

External resources (podcasts, YouTube videos, articles, books, websites) are NOT stored in markdown files. They are:
1. Defined once in `external_resources.yaml` (YAML-first architecture)
2. Loaded at build time by `generate_mdx.py` and `generate_json.py`
3. Injected into MDX output as `[!resources]` callout blocks
4. Added to JSON output as `external_resources` field

**Module ID format:** `{level}-{filename}` (e.g., `a1-09-food-and-drinks`)

**Resource types:**
- `podcasts` - Ukrainian Lessons Podcast, Ukrainian with Olena, etc.
- `youtube` - YouTube videos
- `articles` - Blog posts, online articles
- `books` - Physical/digital books
- `websites` - Web resources

**Architecture benefits:**
- ✅ Single source of truth (no duplication between markdown and YAML)
- ✅ Resources updated centrally (247 modules updated by editing one file)
- ✅ Consistent formatting (emoji template applied at generation time)
- ✅ Matches proven activities pattern (YAML → inject at build time)

**Important:** Markdown files should NOT contain `> [!resources]` sections. If you see one, it's stale and should be removed.

**Viewing resources for a module:**
```bash
# View resources for a specific module (e.g., a1-09)
yq '.resources.a1-09-food-and-drinks' docs/resources/external_resources.yaml
```

**Migration notes:**
- Issue #353: Extracted resources from markdown to YAML (Jan 2026)
- Issue #354: Refactored to YAML-first architecture (Jan 2026)
- Deprecated script: `scripts/generate_resource_sections.py` (kept for reference only)

## Content Creation Workflow

### Creating or Rewriting Modules

When creating new modules or rewriting existing ones:

```
1. WRITE MODULE CONTENT
   ├── Write lesson content (intro, presentation, practice, production)
   ├── Add engagement elements (Чи знали ви?, Міф vs Факт)
   ├── Create activities (quiz, match-up, etc.)
   ├── Leave Словник section empty: <!-- Generated by vocab:enrich -->
   └── Keep Review Vocabulary section (will be updated by enrich)

2. BATCH COMPLETION
   └── Repeat step 1 for all modules in the batch (e.g., B1.1: 81-100)

3. VOCABULARY PROCESSING
   ├── npm run vocab:scan     # Scan modules, update vocabulary.db
   └── npm run vocab:enrich   # Generate Словник sections from database

4. OUTPUT GENERATION
   ├── npm run generate l2-uk-en       # Generate MDX for Docusaurus
   └── npm run generate:json l2-uk-en  # Generate JSON for Vibe app
```

### Why This Order?

1. **vocab:scan** must run after content is written to detect new vocabulary
2. **vocab:enrich** generates consistent Словник sections with correct IPA and first-module tracking
3. **generate** produces MDX for web, **generate:json** produces JSON for Vibe app

### Module Quality Checklist

When rewriting modules, apply these standards:

- [ ] Ukrainian subtitle in frontmatter
- [ ] Ukrainian objectives
- [ ] Ukrainian section headers (Зміст уроку, Розминка, Презентація, etc.)
- [ ] Engaging narrative intro (not "Welcome to X!")
- [ ] 2-3 "Чи знали ви?" boxes per module
- [ ] At least 1 "Міф vs Факт" box
- [ ] Correct immersion ratio for level (see table below)
- [ ] Cultural/historical context where relevant
- [ ] Empty Словник placeholder (for vocab:enrich)

### Immersion Levels by Level

| Level | Modules | UK % | Notes |
|-------|---------|------|-------|
| A1 | M01-34 | 10-40% | Transliteration graduated (full → first-only) |
| A2 | M01-50 | 40-50% | Bilingual explanations |
| B1 | M01-85 | 65% → **100%** | M01-05 bridge (~65%), M06+ full immersion |
| B2 | M01-110 | **100%** | Full immersion |
| C1 | M01-160 | **100%** | Full immersion |
| C2 | M01-100 | **100%** | Full immersion |
| LIT | M01-30 | **100%** | Post-C1 literature track |

## Vibe Integration

CO outputs simple JSON. Vibe handles extraction:

| CO Provides | Vibe Extracts |
|-------------|---------------|
| `sections[].content` (raw md) | `> [!answer]` → gap-fill |
| `sections[].content` (raw md) | `## quiz:` → quiz activity |
| `activities[]` (parsed) | Pre-parsed activities |
| `vocabulary.words[]` | Flash card data |
| `rawMarkdown` | Anything else needed |

See `vibe/docs/CO-VIBE-INTEGRATION.md` for the full spec.

## Related Documentation

### Workflows & Guides

- **`CLAUDE.md`** - Module workflow (lines 118-153) - Current 9-phase workflow
- **`docs/RESEARCH-FIRST-WORKFLOW.md`** - Research-first workflow for seminar tracks
- **`docs/MODULE-AUDIT-GUIDE.md`** - Audit guide

### Quality Validation

- **`docs/CONTENT-QUALITY-AUDIT.md`** - Content quality review system (LLM-based)
- **`docs/SCRIPTS.md`** - Complete scripts reference including activity quality validation
- **`docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`** - Quality standards and targets

### Markdown & Format

- **`docs/MARKDOWN-FORMAT.md`** - Complete markdown syntax specification
- **`docs/ACTIVITY-YAML-REFERENCE.md`** - Activity format reference for AI agents

### Claude Code Extensions

- **`claude_extensions/quick-ref/`** - Level-specific quick references (a1.md, b1.md, b2.md, c1.md, c2.md)
- **`claude_extensions/phases/`** - Stage instruction documents
- **`claude_extensions/commands/`** - Slash commands (/module, /module-stage-*, /review-content)
- **`claude_extensions/skills/`** - Skills (grammar-check, vocab-enrichment, module architects)

### Templates

- **`docs/l2-uk-en/templates/`** - 26 authoritative module templates by level and type

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2024-12-02 | moduleType, immersionLevel, simplified sections |
| 1.0 | 2024-11-30 | Initial JSON format |
