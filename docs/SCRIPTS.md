# Scripts & Workflow Reference

This document describes all scripts and the recommended workflow for module creation, review, and enrichment.

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
cd docusaurus && npm start  # In separate terminal
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
| `docs/l2-uk-en/claude-review-prompt.md` | **Review prompts for Claude** - Use these to fix audit issues |
| `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Quality standards by level (consolidated) |
| `docs/MARKDOWN-FORMAT.md` | Markdown syntax specification |

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

### Vocabulary (TypeScript)

| Script | Purpose | Command |
|--------|---------|---------|
| `vocab-init.ts` | Create fresh vocabulary DB | `npm run vocab:init` |
| `vocab-scan.ts` | Populate DB from modules | `npm run vocab:scan` |
| `vocab-enrich.ts` | Enrich module vocab sections | `npm run vocab:enrich` |
| `vocab-audit.ts` | Find unknown/premature words | `npx ts-node scripts/vocab-audit.ts` |

### Legacy (TypeScript)

| Script | Purpose | Command |
|--------|---------|---------|
| `module-audit.ts` | Find issues in modules | `npx ts-node scripts/module-audit.ts` |
| `enrich-activities.ts` | Generate activity scaffolds | `npx ts-node scripts/enrich-activities.ts` |
| `generate-exercises.ts` | Generate exercise templates | `npx ts-node scripts/generate-exercises.ts` |

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

**Requires:** Docusaurus dev server running (`cd docusaurus && npm start`)

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
- Activity count matches source markdown
- Vocabulary table preserved
- Section headers intact
- No content loss during conversion

**Usage:**
```bash
npm run validate:mdx l2-uk-en a1    # Validate entire level
npm run validate:mdx l2-uk-en a1 5  # Validate single module
```

---

### validate_html.py

**Purpose:** Browser rendering validation using Playwright headless browser.

**Checks:**
- Page loads without errors
- React components render correctly
- No JavaScript errors in console
- Ukrainian text present
- Interactive elements functional

**Usage:**
```bash
npm run validate:html l2-uk-en a1   # Validate entire level
npm run validate:html l2-uk-en a1 5 # Validate single module
```

**Requires:**
- Docusaurus dev server running (`cd docusaurus && npm start`)
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
python3 scripts/audit_module.py curriculum/l2-uk-en/a1/05-*.md
```

**Issue Categories:**
- **FAIL (Must Fix):** Grammar violations, missing sections, activity syntax
- **WARN (Should Fix):** Richness, variety, word count
- **INFO (Consider):** Optional improvements

---

### module-audit.ts (Legacy)

**Purpose:** TypeScript module quality checker. Being replaced by `audit_module.py`.

**Usage:**
```bash
npx ts-node scripts/module-audit.ts l2-uk-en           # Audit all modules
npx ts-node scripts/module-audit.ts l2-uk-en 41-65     # Audit range
npx ts-node scripts/module-audit.ts l2-uk-en 81-90 --fix  # Generate fix prompts
```

**Options:**
- `--fix` - Generate actionable fix prompts for Claude

---

## Vocabulary Pipeline

The vocabulary system uses SQLite (`vocabulary.db`) to track all words across modules.

### Workflow Order

```
1. vocab-init    →  Create empty database
2. vocab-scan    →  Populate from module markdown
3. vocab-enrich  →  Fill in missing IPA, POS, etc.
4. vocab-audit   →  Find problems
```

### vocab-init.ts

**Purpose:** Initialize a fresh SQLite vocabulary database with proper schema.

```bash
npm run vocab:init                  # Create database
npm run vocab:init:force            # Force recreate (deletes existing)
```

**Creates:** `curriculum/{lang}/vocabulary.db`

### vocab-scan.ts

**Purpose:** Scans all module markdown files and populates the SQLite database.

```bash
npm run vocab:scan                  # Scan all modules
npx ts-node scripts/vocab-scan.ts l2-uk-en 82    # Scan single module
```

### vocab-enrich.ts

**Purpose:** Enriches module markdown vocabulary sections from the database.

```bash
npm run vocab:enrich                # Enrich all modules
npm run vocab:enrich:dry            # Preview changes (no write)
npx ts-node scripts/vocab-enrich.ts l2-uk-en 82  # Single module
```

### vocab-audit.ts

**Purpose:** Scans Ukrainian text in modules and checks against vocabulary database.

```bash
npx ts-node scripts/vocab-audit.ts l2-uk-en 81     # Audit single module
npx ts-node scripts/vocab-audit.ts l2-uk-en 81-100 # Audit range
npx ts-node scripts/vocab-audit.ts l2-uk-en        # Audit all modules
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

# Claude Skills
npm run claude:deploy         # Deploy skills to .claude/

# Development
cd docusaurus && npm start    # Start Docusaurus dev server (for HTML validation)
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
cd docusaurus && npm start  # In terminal 1
npm run pipeline l2-uk-en a1 5  # In terminal 2
```

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
