# Scripts & Workflow Reference

This document describes all scripts and workflows for module creation, validation, and generation.

> **🚀 For B1+ module creation (B1, B2, C1, C2):**
>
> - **👤 Human users:** See **`docs/HUMAN-WORKFLOW-B1-PLUS.md`** - Shows exactly what commands YOU run
> - **🤖 AI agents:** See **`docs/B1-PLUS-MODULE-WORKFLOW.md`** - Comprehensive reference
>
> This document (SCRIPTS.md) is a **detailed reference** for individual scripts and commands.

---

## Module Creation Pipeline

The complete module creation and validation pipeline:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. WRITE       │ ──▶ │  2. AUDIT       │ ──▶ │  3. GENERATE    │ ──▶ │  4. VALIDATE    │
│  Module content │     │  audit_module   │     │  MDX + JSON     │     │  MDX + HTML     │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Full Pipeline Command

```bash
# Run complete pipeline: lint → generate MDX → validate MDX → validate HTML
npm run pipeline l2-uk-en a1 5

# Also generate JSON for Vibe app
npm run generate:json l2-uk-en a1 5
```

**Note:** HTML validation requires Docusaurus dev server running:
```bash
cd docusaurus && pnpm start  # In separate terminal
```

### Step 1: Audit Module

```bash
# Audit single module (Python)
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/05-my-world-objects.md

# Audit range (shell loop)
for i in {1..20}; do
  python3 scripts/audit_module.py curriculum/l2-uk-en/a1/$i-*.md
done
```

### Step 2: Generate Output

```bash
# Generate MDX (Docusaurus)
npm run generate l2-uk-en a1 5

# Generate JSON (Vibe app)
npm run generate:json l2-uk-en a1 5
```

### Step 3: Validate

```bash
# Validate MDX (content integrity)
npm run validate:mdx l2-uk-en a1 5

# Validate HTML (browser rendering) - requires dev server
npm run validate:html l2-uk-en a1 5
```

### Step 4: Verify

```bash
# Re-run audit to confirm all passes
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/05-*.md
```

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| **`docs/B1-PLUS-MODULE-WORKFLOW.md`** | **Complete B1+ workflow** - End-to-end guide for B1/B2/C1/C2 modules with all quality validation systems |
| `docs/ARCHITECTURE.md` | System architecture and quality validation overview |
| `docs/STAGED-MODULE-CREATION.md` | 4-stage creation pipeline overview |
| `docs/l2-uk-en/claude-review-prompt.md` | Review prompts for Claude - Use these to fix audit issues |
| `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Quality standards by level (consolidated) |
| `docs/MARKDOWN-FORMAT.md` | Markdown syntax specification |
| `docs/CONTENT-QUALITY-AUDIT.md` | Content quality review system (LLM-based) |

---

## Scripts Quick Reference

### Core Pipeline (Python)

| Script | Purpose | Command |
|--------|---------|---------|
| `pipeline.py` | Full validation pipeline | `npm run pipeline l2-uk-en a1 5` |
| `generate_mdx.py` | Generate MDX for Docusaurus | `npm run generate l2-uk-en a1 5` |
| `generate_json.py` | Generate JSON for Vibe app | `npm run generate:json l2-uk-en a1 5` |
| `validate_mdx.py` | Validate MDX content integrity | `npm run validate:mdx l2-uk-en a1 5` |
| `validate_html.py` | Validate browser rendering | `npm run validate:html l2-uk-en a1 5` |
| `audit_module.py` | Module quality checker | `python3 scripts/audit_module.py <file>` |

### Staged Generation (Python)

| Script | Purpose | Command |
|--------|---------|---------|
| `generate_skeleton.py` | Generate module skeleton | `python3 scripts/generate_skeleton.py l2-uk-en b1 43` |
| `check_gate.py` | Hard gate checker | `python3 scripts/check_gate.py <stage> <file>` |
| `calculate_richness.py` | Richness score (0-100) | `python3 scripts/calculate_richness.py <file>` |
| `extract_for_activities.py` | Extract content for activities | `python3 scripts/extract_for_activities.py <file>` |

### Vocabulary (Python)

| Script | Purpose | Command |
|--------|---------|---------|
| `vocab_init.py` | Create fresh vocabulary DB | `npm run vocab:init` |
| `populate_vocab_db.py` | Populate DB from modules | `npm run vocab:scan` |

---

## Core Scripts

### pipeline.py

**Purpose:** Unified validation pipeline that runs all checks in sequence.

**Pipeline Stages:**
1. **Lint** - Markdown format compliance
2. **Generate** - Creates MDX for Docusaurus
3. **Validate MDX** - Ensures no content loss during conversion
4. **Validate HTML** - Headless browser check for rendering errors

**Usage:**
```bash
npm run pipeline l2-uk-en a1        # Validate entire level
npm run pipeline l2-uk-en a1 5      # Validate single module
```

**Requires:** Docusaurus dev server running (`cd docusaurus && pnpm start`)

---

### generate_mdx.py

**Purpose:** Generates MDX files for Docusaurus web lessons (Python 3.12).

**Usage:**
```bash
npm run generate l2-uk-en           # Generate all levels
npm run generate l2-uk-en a1        # Generate specific level
npm run generate l2-uk-en a1 5      # Generate single module
```

**Input:** `curriculum/{lang}/{level}/*.md`

**Output:** `docusaurus/docs/{level}/module-XX.mdx`

**Note:** Requires Python 3.12 venv (`.venv/bin/python`)

---

### generate_json.py

**Purpose:** Generates Vibe-format JSON for app import (Python 3.12).

**Usage:**
```bash
npm run generate:json l2-uk-en      # Generate all levels
npm run generate:json l2-uk-en a1   # Generate specific level
npm run generate:json l2-uk-en a1 5 # Generate single module
```

**Input:** `curriculum/{lang}/{level}/*.md`

**Output:** `output/json/{lang}/{level}/module-XX.json`

**Note:** Requires Python 3.12 venv (`.venv/bin/python`)

---

### validate_mdx.py

**Purpose:** Validates MDX content integrity after generation.

**Checks:**
- Activity types present in MDX match source markdown
- Vocabulary words from first column preserved
- Ukrainian text content maintained
- No content loss during conversion

**Usage:**
```bash
npm run validate:mdx l2-uk-en a1    # Validate entire level
npm run validate:mdx l2-uk-en a1 5  # Validate single module
```

**Review File Integration:**
Results are automatically written to review files in `gemini/` folders:
```markdown
## MDX VALIDATION
✅ No issues found
```
Or with issues:
```markdown
## MDX VALIDATION
### Errors
- ❌ Activity types missing in MDX: cloze
### Warnings
- ⚠️ Some Ukrainian content may be missing (15/50 words)
```

---

### validate_html.py

**Purpose:** Browser rendering validation using Playwright headless browser.

**Checks:**
- Page loads without HTTP errors
- React components render (no error boundary)
- No serious JavaScript errors in console
- Ukrainian text present (sanity check)
- Interactive activity elements render with content

**Usage:**
```bash
npm run validate:html l2-uk-en a1   # Validate entire level
npm run validate:html l2-uk-en a1 5 # Validate single module
```

**Graceful Skip:**
When the dev server is not running, validation skips gracefully with exit code 0:
```
ℹ️  Docusaurus dev server not running - skipping HTML validation
   To enable: cd docusaurus && pnpm start
```
This allows the pipeline to continue without failing.

**Review File Integration:**
Results are automatically written to review files in `gemini/` folders:
```markdown
## HTML VALIDATION
✅ Renders correctly (10 interactive elements)
```
Or with issues:
```markdown
## HTML VALIDATION
### Errors
- ❌ Activity not rendering: Match Vocabulary (MatchUp)
- ❌ 2 JS errors
```

**Requires:**
- Docusaurus dev server running (`cd docusaurus && pnpm start`)
- Playwright installed (`playwright install`)

---

### audit_module.py

**Purpose:** Comprehensive module quality checker (Python). Validates against MODULE-RICHNESS-GUIDELINES-v2.md requirements.

**Checks:**
- Frontmatter validity (module, title, pedagogy, objectives)
- Required sections present
- Activity count and diversity
- Vocabulary section format
- Sentence complexity
- Grammar constraints by level
- Linguistic purity (no Surzhyk)

**Usage:**
```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/06-*.md
```

**Issue Categories:**
- **FAIL (Must Fix):** Grammar violations, missing sections, activity syntax
- **WARN (Should Fix):** Richness, variety, word count
- **INFO (Consider):** Optional improvements

---

## Staged Generation Scripts

These scripts support the staged module generation workflow where modules are built incrementally with hard gates between stages.

### Workflow Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  SKELETON    │ ──▶ │  CONTENT     │ ──▶ │  ACTIVITIES  │ ──▶ │  AUDIT       │ ──▶ │  OUTPUT      │
│  Stage 1     │     │  Stage 2     │     │  Stage 3     │     │  Stage 4     │     │  Stage 5     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       ▼                    ▼                    ▼
  check_gate.py        check_gate.py        check_gate.py
   skeleton             content              activities
```

Each gate returns exit code 0 (PASS) or 1 (FAIL). Agent has NO discretion to override FAIL.

---

### generate_skeleton.py

**Purpose:** Generate module skeleton from curriculum plan and template.

**Usage:**
```bash
python3 scripts/generate_skeleton.py l2-uk-en b1 43
```

**Inputs:**
- `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` - Extracts title, focus, grammar, vocab
- `docs/l2-uk-en/templates/{level}-{type}-module-template.md` - Structure guide

**Output:** `curriculum/l2-uk-en/{level}/{NN}-skeleton.md`

**Features:**
- Determines module type based on level and number
- Generates frontmatter with pedagogy, phase, word targets
- Creates section headers from template
- Adds activity placeholders with specs
- Includes vocabulary table structure

---

### check_gate.py

**Purpose:** Hard gate checker for staged generation. Returns exit codes for CI/automation.

**Usage:**
```bash
python3 scripts/check_gate.py skeleton curriculum/l2-uk-en/b1/43-*.md
python3 scripts/check_gate.py content curriculum/l2-uk-en/b1/43-*.md
python3 scripts/check_gate.py activities curriculum/l2-uk-en/b1/43-*.md
```

**Gate Checks:**

| Stage | Checks |
|-------|--------|
| `skeleton` | Frontmatter present, required sections, vocabulary section |
| `content` | Word count, engagement boxes, examples, dialogues, immersion, vocabulary count |
| `activities` | Activity count, type variety, priority types, item counts |

**Exit Codes:**
- `0` - PASS
- `1` - FAIL (with failure reasons printed)

---

### calculate_richness.py

**Purpose:** Calculate 10-component richness score (0-100) for content quality.

**Usage:**
```bash
python3 scripts/calculate_richness.py curriculum/l2-uk-en/b1/43-*.md
```

**Components (Weighted):**

| Component | Weight | What It Measures |
|-----------|--------|------------------|
| Engagement | 15% | 💡🎬🌍🎯🎮 boxes |
| Examples | 20% | Ukrainian example sentences |
| Dialogues | 15% | А:/Б: or speaker patterns |
| Variety | 10% | Sentence starter diversity |
| Cultural | 10% | Cultural references |
| Real-world | 10% | Practical usage scenarios |
| Questions | 5% | Rhetorical questions |
| Proverbs | 5% | Ukrainian sayings |
| Visual | 5% | Tables and formatting |
| Paragraph variation | 5% | Length diversity |

**Dryness Flags:**
- `NO_ENGAGEMENT` - Zero engagement boxes
- `WALL_OF_TEXT` - All paragraphs similar length
- `REPETITIVE_STARTERS` - Same sentence beginnings

**Output:**
```
Richness: 87/100 (threshold: 70)
Components: engagement=12/15, examples=18/20, ...
Flags: []
```

---

### extract_for_activities.py

**Purpose:** Extract content elements for activity generation.

**Usage:**
```bash
python3 scripts/extract_for_activities.py curriculum/l2-uk-en/b1/43-*.md
python3 scripts/extract_for_activities.py curriculum/l2-uk-en/b1/43-*.md output.json
```

**Extracts:**

| Element | Description |
|---------|-------------|
| `vocabulary` | Ukrainian-English pairs from vocabulary table |
| `sentences` | Example sentences from content |
| `dialogues` | А/Б dialogue pairs |
| `paragraphs` | Content paragraphs for cloze/comprehension |
| `proverbs` | Ukrainian sayings and proverbs |
| `tables` | Grammar tables for reference |

**Output Format (JSON):**
```json
{
  "module": "b1-43",
  "title": "...",
  "vocabulary": [{"uk": "слово", "en": "word", "ipa": "/.../"}, ...],
  "sentences": ["Це речення.", ...],
  "dialogues": [{"a": "Привіт!", "b": "Вітаю!"}, ...],
  "paragraphs": ["...", ...],
  "stats": {
    "vocabulary_count": 25,
    "sentence_count": 60,
    ...
  }
}
```

---

### Staged Generation Quick Reference

```bash
# Stage 1: Generate skeleton
python3 scripts/generate_skeleton.py l2-uk-en b1 43
python3 scripts/check_gate.py skeleton curriculum/l2-uk-en/b1/43-skeleton.md

# Stage 2: Fill content (agent fills in skeleton)
python3 scripts/check_gate.py content curriculum/l2-uk-en/b1/43-*.md
python3 scripts/calculate_richness.py curriculum/l2-uk-en/b1/43-*.md

# Stage 3: Generate activities
python3 scripts/extract_for_activities.py curriculum/l2-uk-en/b1/43-*.md
# (agent generates activities from extracted content)
python3 scripts/check_gate.py activities curriculum/l2-uk-en/b1/43-*.md

# Stage 4: Full audit
python3 scripts/audit_module.py curriculum/l2-uk-en/b1/43-*.md

# Stage 5: Pipeline output
npm run pipeline l2-uk-en b1 43
```

---

## Landing Page Sync

### sync_landing_pages.py

**Purpose:** Auto-updates website landing pages with accurate module counts and status.

**Updates:**
- `docusaurus/docs/intro.mdx` - Main curriculum overview table
- `docusaurus/docs/{level}/index.mdx` - Level landing pages

**Usage:**
```bash
npm run sync:landing           # Apply changes
npm run sync:landing:dry       # Preview only (dry run)
```

**Status Logic:**
| Completion | Status | Meaning |
|------------|--------|---------|
| 100% | 🔍 In QA | All modules exist, needs final review |
| 10-99% | 🚧 In Progress | Actively being built |
| <10% | 📋 Planned | Curriculum plan only |
| Manual | ✅ Complete | Manually verified (in STATUS_OVERRIDES) |

**Data Sources:**
- Config file: `docs/l2-uk-en/level-status.yaml` (planned counts, status overrides)
- Ready counts: MDX files in `docusaurus/docs/{level}/module-*.mdx`

**Config File (`level-status.yaml`):**
```yaml
b2:
  planned: 145        # Total modules planned
  status: auto        # 'auto' or 'complete'
  description: "..."  # For intro.mdx table
```

**Integration:**
Run after completing a batch of modules to update the website:
```bash
npm run pipeline l2-uk-en b2    # Build modules
npm run sync:landing            # Update landing pages
```

---

## Vocabulary Pipeline

The vocabulary system uses SQLite (`vocabulary.db`) to track all words across modules.

### Workflow Order

```
1. vocab_init.py        →  Create empty database (Python)
2. populate_vocab_db.py →  Populate from module markdown (Python)
```

### vocab_init.py

**Purpose:** Initialize a fresh SQLite vocabulary database with proper schema.

```bash
npm run vocab:init                  # Create database
npm run vocab:init:force            # Force recreate (deletes existing)
python3 scripts/vocab_init.py l2-uk-en --force  # Direct invocation
```

**Creates:** `curriculum/{lang}/vocabulary.db`

### populate_vocab_db.py

**Purpose:** Scans all module markdown files and populates the SQLite database.

```bash
npm run vocab:scan                  # Scan all modules
python3 scripts/populate_vocab_db.py  # Direct invocation
```

---

## Activity Scripts

### enrich-activities.ts

**Purpose:** Uses vocabulary database to generate activity scaffolds with proper vocabulary data.

```bash
npx ts-node scripts/enrich-activities.ts l2-uk-en 1-100
```

**Level Configuration:**
| Level | Activities | Items/Activity | Refresher % | Complexity |
|-------|------------|----------------|-------------|------------|
| A1 | 6 | 10 | 10% | simple |
| A2 | 6 | 12 | 15% | medium |
| A2+ | 7 | 12 | 20% | medium |
| B1/B1+ | 8 | 12 | 25% | complex |
| B2/B2+ | 8 | 12 | 30% | advanced |

### generate-exercises.ts

**Purpose:** Generates additional activity templates based on vocabulary and grammar patterns.

```bash
npx ts-node scripts/generate-exercises.ts              # All modules
npx ts-node scripts/generate-exercises.ts 1-80         # Pre-B1 only
npx ts-node scripts/generate-exercises.ts 5            # Single module
```

**Activity Types:**
- **Type A (Easy):** match-up, true-false, group-sort
- **Type B (Medium):** fill-in, quiz
- **Type C (Hard):** unjumble, transform

---

## Activity Quality Validation

**Purpose:** Optional manual validation workflow for B1+ activity quality using deterministic checks + human semantic assessment.

> **For complete workflow integration**, see **`docs/B1-PLUS-MODULE-WORKFLOW.md`** - Activity Quality Validation section, which includes:
> - When to use activity quality validation (recommended for high-stakes content: C1/C2, pre-publication)
> - Step-by-step queue → validate → finalize workflow
> - How to interpret CEFR gates and fix failed activities
> - Integration with full module creation pipeline

### Workflow Overview

1. **Generate Queue:** Pre-populate deterministic quality checks for manual validation
2. **Manual Validation:** Human reviewer fills in semantic quality scores
3. **Finalize:** Evaluate CEFR-specific quality gates and generate report
4. **Integrate:** Optional quality report shown in audit output (INFO gate)

### Quality Dimensions (5-Dimension Model)

| Dimension | Scale | Measures |
|-----------|-------|----------|
| **Naturalness** | 1-5 | Robotic → Unnatural → Acceptable → Natural → Highly Natural |
| **Difficulty** | 3-option | too_easy \| appropriate \| too_hard |
| **Distractor Quality** | 1-5 | Nonsense → Weak → Acceptable → Good → Excellent |
| **Engagement** | 1-5 | Boring → Low → Neutral → Engaging → Highly Engaging |
| **Variety** | 0-100% | Mechanical pattern detection score |

### CEFR Quality Gates

| Level | Min Naturalness | Max Difficulty Inappropriate | Min Engagement | Min Distractor Quality | Min Variety |
|-------|----------------|------------------------------|----------------|------------------------|-------------|
| A1, A2 | None | None | None | None | None |
| B1 | 3.5 | ≤20% | 3.0 | 4.0 | 60% |
| B2 | 4.0 | ≤15% | 3.5 | 4.2 | 65% |
| C1 | 4.5 | ≤10% | 4.0 | 4.5 | 70% |
| C2 | 4.8 | ≤5% | 4.5 | 5.0 | 75% |

### Scripts

#### generate_activity_quality_queue.py

**Purpose:** Run deterministic quality checks and generate queue file for manual validation.

```bash
# Generate queue for specific module
npm run quality:queue l2-uk-en b1 52

# Or directly:
.venv/bin/python scripts/audit/generate_activity_quality_queue.py l2-uk-en b1 52
```

**Output:** `curriculum/l2-uk-en/b1/queue/52-module-slug-quality.yaml`

**Deterministic Checks Run:**
- `analyze_sentence_variety()` - Pattern repetition detection
- `estimate_vocabulary_difficulty()` - Word length heuristics per CEFR
- `analyze_distractor_quality()` - Word class matching, plausibility
- `check_natural_ukrainian_markers()` - Pronoun overuse, calques
- `estimate_cognitive_load()` - Task complexity assessment

**Queue File Structure:**
```yaml
module: 52-module-slug
level: B1
activities:
  - activity_id: quiz-example
    deterministic_checks:
      variety_score: 85
      vocabulary_difficulty: appropriate
      cognitive_load: medium
      naturalness_issues: []
      distractor_quality_avg: 4.2
    # Manual validation (empty, to be filled):
    naturalness: null
    difficulty: null
    engagement: null
    distractor_score: null
    variety_score: null
```

#### finalize_activity_quality.py

**Purpose:** Read completed queue file, evaluate quality gates, generate report.

```bash
# After manual validation completed
npm run quality:finalize l2-uk-en b1 52

# Or directly:
.venv/bin/python scripts/audit/finalize_activity_quality.py l2-uk-en b1 52
```

**Output:** `curriculum/l2-uk-en/b1/audit/52-module-slug-quality.md`

**Report Includes:**
- Pass/Fail status against CEFR gates
- Quality scores summary table
- Difficulty breakdown (too easy/appropriate/too hard)
- Failed gates details with recommendations
- Incomplete validation warnings

### Integration with Audit Pipeline

Quality validation is **optional and informational** (does not block audit pass/fail).

When quality report exists, audit output shows:
```
Activity_quality ⚠️ Quality gates: 1 failed (see report)
Activity_quality ✅ Quality gates: All passed
Activity_quality 📋 Quality validation available (optional)
```

### Manual Validation Workflow

1. **Generate queue:**
   ```bash
   npm run quality:queue l2-uk-en b1 52
   ```

2. **Open queue file:**
   ```bash
   open curriculum/l2-uk-en/b1/queue/52-module-slug-quality.yaml
   ```

3. **Fill in manual scores for each activity:**
   - `naturalness:` 1-5 (How natural does the Ukrainian sound?)
   - `difficulty:` too_easy | appropriate | too_hard
   - `engagement:` 1-5 (How engaging is the content?)
   - `distractor_score:` 1-5 (How plausible are the wrong options?)
   - `variety_score:` 1-5 (Manual assessment of variety)

4. **Finalize and generate report:**
   ```bash
   npm run quality:finalize l2-uk-en b1 52
   ```

5. **Review report:**
   ```bash
   cat curriculum/l2-uk-en/b1/audit/52-module-slug-quality.md
   ```

6. **Fix issues if needed and regenerate activities**

### Related Files

- **`scripts/audit/checks/activity_quality.py`** - Deterministic quality check functions
- **`scripts/audit/generate_activity_quality_queue.py`** - Queue generation
- **`scripts/audit/finalize_activity_quality.py`** - Report generation
- **`tests/test_activity_quality.py`** - Unit tests (36 tests, all passing)
- **Issue #355** - Activity Quality Validation Expansion

---

## NPM Scripts Summary

```bash
# Full Pipeline (Python)
npm run pipeline              # Run full validation pipeline
npm run pipeline l2-uk-en a1  # Pipeline for specific level
npm run pipeline l2-uk-en a1 5  # Pipeline for single module

# Generation (Python)
npm run generate              # Generate MDX for Docusaurus
npm run generate:json         # Generate JSON for Vibe app

# Validation (Python)
npm run validate:mdx          # Validate MDX content integrity
npm run validate:html         # Validate browser rendering (needs dev server)

# Vocabulary Database (TypeScript)
npm run vocab:init            # Create fresh database
npm run vocab:init:force      # Force recreate database
npm run vocab:scan            # Populate from modules
npm run vocab:enrich          # Enrich module vocab sections
npm run vocab:enrich:dry      # Preview enrichment changes
npm run vocab:rebuild         # Full rebuild (init:force + scan)

# Landing Page Sync
npm run sync:landing          # Update landing pages with current stats
npm run sync:landing:dry      # Preview changes without applying

# Claude Skills
npm run claude:deploy         # Deploy skills to .claude/

# Development
cd docusaurus && pnpm start    # Start Docusaurus dev server (for HTML validation)
```

---

## Common Workflows

### New Module Creation (Full Pipeline)

```bash
# 1. Write module content (use /module-create command or manually)

# 2. Audit the module
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/05-*.md

# 3. Fix any issues, then run full pipeline
npm run pipeline l2-uk-en a1 5

# 4. Generate JSON for Vibe app
npm run generate:json l2-uk-en a1 5

# 5. Verify all passes
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/05-*.md
```

### Review Module Range

```bash
# 1. Audit multiple modules
for i in {1..20}; do
  python3 scripts/audit_module.py curriculum/l2-uk-en/a1/$i-*.md
done

# 2. Fix issues in failing modules

# 3. Run pipeline for the level
npm run pipeline l2-uk-en a1

# 4. Generate JSON
npm run generate:json l2-uk-en a1
```

### Fix Vocabulary Duplicates

```bash
# 1. Rebuild vocabulary database (validates cross-module)
npm run vocab:rebuild

# 2. Remove duplicates from later modules (per audit output)

# 3. Re-run vocab:rebuild to verify
npm run vocab:rebuild
```

### Validate After Changes

```bash
# Quick validation (no dev server needed)
npm run validate:mdx l2-uk-en a1 5

# Full validation (requires dev server)
cd docusaurus && pnpm start  # In terminal 1
npm run pipeline l2-uk-en a1 5  # In terminal 2
```

---

## Review Files

Review files are generated in `gemini/` subdirectories alongside source modules. They consolidate all validation results in one place.

**Location:** `curriculum/{lang}/{level}/gemini/{module-slug}-review.md`

**Structure:**
```markdown
# Audit Report: 05-my-world-objects.md
**Phase:** A1 | **Level:** A1 | **Pedagogy:** "PPP" | **Target:** 600
**Overall Status:** ✅ PASS

## Gates
- **Words:** ✅ 650/600
- **Activities:** ✅ 8/6
- **Vocab:** ✅ 20/15
- ...

## MDX VALIDATION
✅ No issues found

## HTML VALIDATION
✅ Renders correctly (8 interactive elements)

## Section Audit
| Section | Status | Count | Notes |
|---------|--------|-------|-------|
| **Intro** | ✅ | 85 | Included in Core |
| **quiz: Test** | 🎮 | 10 | Activity (10 items) |
...
```

**Section Order:**
1. **Header** - Module info and overall status
2. **Gates** - Audit gate results (word count, activities, etc.)
3. **MDX VALIDATION** - Content integrity check results
4. **HTML VALIDATION** - Browser rendering check results
5. **Section Audit** - Per-section breakdown

**Generation:**
- `audit_module.py` creates/updates Gates and Section Audit
- `validate_mdx.py` adds/updates MDX VALIDATION section
- `validate_html.py` adds/updates HTML VALIDATION section

Each validator updates only its section, preserving other content.

---

## Library Structure

```
scripts/
├── # Python Pipeline (Primary)
├── pipeline.py           # Unified validation pipeline
├── generate_mdx.py       # MDX generator for Docusaurus
├── generate_json.py      # Vibe JSON generator
├── validate_mdx.py       # MDX content validator
├── validate_html.py      # Browser rendering validator (Playwright)
├── audit_module.py       # Module quality checker
│
├── audit/                # Python audit library
│   ├── __init__.py
│   ├── core.py           # Main audit logic
│   ├── config.py         # Level-specific constraints
│   ├── cleaners.py       # Text cleaning utilities
│   ├── report.py         # Review file generation and updates
│   └── checks/           # Individual check modules
│       ├── activities.py
│       ├── grammar.py
│       └── pedagogy.py
│
├── # TypeScript (Vocabulary + Legacy)
├── vocab-*.ts            # Vocabulary scripts
├── module-audit.ts       # Module quality checker (legacy)
├── generate-mdx.ts       # MDX generator (legacy, kept for reference)
└── lib/
    ├── index.ts          # Main exports
    ├── types.ts          # TypeScript types (Level, ModuleType, etc.)
    ├── vocab-sqlite.ts   # SQLite vocabulary helpers
    ├── utils/
    │   ├── index.ts      # Utility exports
    │   ├── files.ts      # File operations
    │   └── markdown.ts   # Markdown parsing helpers
    └── parsers/
        ├── index.ts      # Parser exports
        ├── frontmatter.ts    # YAML frontmatter parsing
        ├── sections.ts       # Section parsing
        ├── vocabulary.ts     # Vocabulary table parsing
        └── activities/       # Activity type parsers
```

**Note:** Core pipeline has been ported to Python for reliability and maintainability. TypeScript vocabulary scripts remain active. Python requires `.venv/bin/python` (Python 3.12).
