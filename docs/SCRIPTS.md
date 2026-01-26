# Scripts & Workflow Reference

This document describes all scripts and workflows for module creation, validation, and generation.

> **🚀 Module Creation Workflow:**
>
> Use `/module {level} {num}` as the main entry point. See [9-Phase Workflow](#9-phase-module-workflow-rfc-001) below.
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
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/05-my-world-objects.md

# Audit range (shell loop)
for i in {1..20}; do
  .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/$i-*.md
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
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/05-*.md
```

---

## Plans & Status Management (v2.0)

Learn Ukrainian v2.0 uses a three-layer architecture: **Plans** (Immutable) → **Build** (Mutable) → **Status** (Cached).

### View Module Status (Cached)

Instant status reporting using the audit cache.

```bash
# View status of a single module
/module-status b1 5

# View status of entire level
/level-status b1
```

### Update Status Cache

The cache is updated automatically whenever `audit_module.py` is run.

```bash
# Force update cache for a module by running audit
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/05-*.md
```

### Plan Management

Plans are the immutable source of truth for module requirements.

```bash
# Extract plans from existing meta files (migration)
.venv/bin/python scripts/migrate_to_v2.py b1

# Validate plans against schema
.venv/bin/python scripts/validate_plan_yaml.py --level b1
```

### Generate Human-Readable Plan Markdown

Convert YAML plans to readable markdown for review and comparison.

```bash
# Generate readable plan for specific level
.venv/bin/python scripts/generate_plan_markdown.py b2-hist

# Generate plans for all levels
.venv/bin/python scripts/generate_plan_markdown.py --all
```

**Output:** `docs/l2-uk-en/{LEVEL}-PLAN-GENERATED.md`

**What it includes:**
- Level overview (title, target, prerequisites)
- Vocabulary focus areas
- Pedagogy notes (including decolonization guidance)
- Phase structure with module sequences
- Per-module details: title, focus, word target, objectives, grammar
- Content outline preview for each module

**Use cases:**
- Review curriculum scope before building modules
- Compare old curriculum plans with new YAML-based plans
- Generate documentation for stakeholder review

### Legacy Status Scripts (Deprecated)

The following scripts are kept for backward compatibility but are superseded by the JSON cache system:
- `scripts/update_status.py` (Updates level-wide YAML status)
- `scripts/generate_level_status.py` (Updates `docs/*-STATUS.md` - now uses cache!)

---

## Related Documentation

| Document                                         | Purpose                                                                                                  |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| `claude_extensions/phases/module-*.md`           | **9-Phase workflow** - Current module creation process (RFC-001)                                         |
| `claude_extensions/commands/module*.md`          | Module commands reference (`/module`, `/module-sync`, etc.)                                              |
| `docs/ARCHITECTURE.md`                           | System architecture and quality validation overview                                                      |
| `docs/ARCHITECTURE-PLANS.md`                     | **Three-layer architecture** - Plans, content, status separation                                         |
| `docs/l2-uk-en/claude-review-prompt.md`          | Review prompts for Claude - Use these to fix audit issues                                                |
| `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Quality standards by level (consolidated)                                                                |
| `docs/MARKDOWN-FORMAT.md`                        | Markdown syntax specification                                                                            |
| `docs/CONTENT-QUALITY-AUDIT.md`                  | Content quality review system (LLM-based)                                                                |
| `claude_extensions/commands/review-content-*.md` | Content quality review commands (`/review-content-scoring`, etc.)                                        |

---

## Content Quality Review Commands

> **When to use:** After `audit_module.py` passes structural gates. Review-content focuses on **pedagogical quality** (coherence, engagement, naturalness).

### Available Commands

| Command | Purpose | Size |
|---------|---------|------|
| `/review-content-scoring` | **Primary** - Compact post-audit quality review with 0-10 scoring | 13k |
| `/review-content-scoring-0-10` | Detailed 0-10 rubric reference (dimensions, examples) | 23k |
| `/review-content-enhancements` | AI slop detection & humanity checks (optional addon) | 16k |

### Archived (Obsolete)

| Command | Reason |
|---------|--------|
| `review-content.md` | Superseded by `-scoring` version (was 74k, too bloated) |
| `review-content-v2.md` | Orphaned consolidation attempt |

### Usage

```bash
/review-content-scoring b2-hist 5      # Review single module
/review-content-scoring b2-hist 1-10   # Review range (uses subagents)
```

### Key Criteria (9 Critical Sections)

1. Template Compliance (auto-fail if violated)
2. Activity Quality (auto-fail for structure/wrong answers)
3. Richness Red Flags (auto-fail for AI slop)
4. Red Flags (multiple auto-fails)
5. Content Richness (B1+ critical)
6. Humanity & Flow Audit
7. Dryness Flags (rewrite if 2+)
8. Human Warmth Checklist (<2 markers = fail)
9. LLM Fingerprint Detection (B1+ critical)

**Scoring:** Only 9-10/10 is acceptable. Everything below 9 requires fixes.

---

## 9-Phase Module Workflow (RFC-001)

> **NEW:** For track levels (b2-hist, c1-bio, c1-hist, c1-pro, b2-pro, lit) and C2, use the 9-phase workflow.
>
> **See:** GitHub issue #444 for full RFC discussion and implementation status.

### Which Command Should I Use?

| Situation | Command | What it does |
|-----------|---------|--------------|
| **New module from scratch** | `/module b2-hist 5` | Full build: phases 1-7 |
| **Module exists, meta needs update** | `/module-sync b2-hist 5` | Syncs meta to markdown reality |
| **Rebuild meta+activities, keep content** | `/module b2-hist 5 --refresh` | Regenerates via architect, preserves .md |
| **Resume after fixing lesson** | `/module b2-hist 5 --from=lesson` | Starts at phase 3 |
| **Just check status** | `/module b2-hist 5 --check` | Reports current state |

**Key difference:**
- `--refresh`: Uses **architect skill** to regenerate outline (plan-driven)
- `/module-sync`: **Extracts from markdown** to update meta (reality-driven)

### /module Command

Unified entry point for building modules. Auto-detects state and runs appropriate phases.

**Usage:**

```bash
/module {level} {num}               # Build single module (phases 1-7)
/module {level} {start}-{end}       # Batch build
/module {level} {num} --from=PHASE  # Resume from specific phase
/module {level} {num} --refresh     # Refresh meta+activities (preserves .md)
/module {level} {num} --check       # Check status only
```

**Examples:**

```bash
/module b2-hist 5               # Build module 5 (content + skeleton deploy)
/module b2-hist 1-5             # Build modules 1-5
/module b2-hist 5 --from=lesson # Resume from phase 3 (lesson)
/module b2-hist 5 --refresh     # Refresh meta+activities keeping lesson content
/module c1-bio 12 --check       # Show which phases are complete
```

### Phase Reference

| Phase | Command           | Creates                    | Validates                 |
| ----- | ----------------- | -------------------------- | ------------------------- |
| 1     | /module-meta      | meta/{slug}.yaml           | -                         |
| 2     | /module-meta-qa   | -                          | Meta validity             |
| 3     | /module-lesson    | {slug}.md                  | -                         |
| 4     | /module-lesson-qa | -                          | Content quality           |
| 5     | /module-act       | activities/{slug}.yaml     | -                         |
| 6     | /module-act-qa    | -                          | Activity schema           |
| 7     | /module-integrate | MDX for Docusaurus         | Cross-file alignment      |
| 8     | /module-vocab     | vocabulary/{slug}.yaml     | -                         |
| 9     | /module-vocab-qa  | -                          | Vocabulary validity       |

### Resume Flags

| --from value | Starts at Phase | Use when...                                |
| ------------ | --------------- | ------------------------------------------ |
| `meta`       | 1               | Fresh build from scratch                   |
| `lesson`     | 3               | Meta is locked, need to regenerate content |
| `act`        | 5               | Content is locked, need new activities     |
| `integrate`  | 7               | Activities locked, deploy to website       |
| `vocab`      | 8               | Module deployed, batch vocab enrichment    |

### /module-sync Command

Sync meta.yaml to match existing markdown content. Use this when markdown exists and is good, but meta needs updating.

```bash
/module-sync b2-hist 1      # Sync meta to existing trypillian-civilization.md
```

**What it does:**
1. Reads existing markdown (source of truth - PRESERVED)
2. Extracts actual H2 sections with word counts
3. Updates meta.yaml content_outline to match reality
4. Validates and fixes activities if needed
5. Loops until all audit gates pass
6. Deploys when clean

**Important:** Markdown is NEVER regenerated. Meta is updated to match reality.

### /module-fix Command

Comprehensive check-and-fix loop for a complete module. Orchestrates all QA checks and fixes issues until ALL gates pass.

```bash
/module-fix b1 12           # Fix B1 module 12
/module-fix b2-hist 5       # Fix B2-HIST module 5
```

**What it does:**
1. Runs comprehensive audit (`audit_module.py --fix`)
2. Categorizes violations by component (meta, lesson, activities, vocab, naturalness)
3. Fixes by category using existing QA phase docs
4. Loops until ALL audit gates show ✅
5. Runs pipeline when complete

**Decision matrix:**
| Violations | Action |
|-----------|--------|
| ≤3 total | Fix individually |
| >3 in one component | Rebuild that component |
| >10 or structural | Consider full rebuild |

**Related QA phases:**
- `phases/module-meta-qa.md` - Meta validation
- `phases/module-lesson-qa.md` - Lesson validation
- `phases/module-act-qa.md` - Activities validation
- `phases/module-vocab-qa.md` - Vocabulary validation

### /meta-fix Command

Check and fix invalid activity types in meta.yaml files across the curriculum.

```bash
/meta-fix                   # Dry-run on all levels
/meta-fix b1                # Dry-run on B1 only
/meta-fix b2-hist --apply   # Fix B2-HIST modules
/meta-fix --apply           # Fix all levels
```

**What it checks:** Invalid activity types in `activity_hints` section.

**Valid activity types:** match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent

**Common invalid types and mappings:**
| Invalid | Action | Rationale |
|---------|--------|-----------|
| transform | → fill-in | Verb transformation |
| conjugation | → fill-in | Verb conjugation |
| dialogue | REMOVE | Content type, not activity |
| roleplay | REMOVE | Content type, not activity |
| flashcards | → match-up | Memorization |
| discussion | REMOVE | Content type, not activity |

**Script:** `scripts/fix_invalid_activity_types.py`

### Batch Mode

When building multiple modules, the command runs each through all phases and reports a summary:

```
Batch: b2-hist 1-5
Results:
  - 1: DEPLOYED
  - 2: DEPLOYED
  - 3: FAIL at phase 4 (lesson-qa: word count)
  - 4: DEPLOYED
  - 5: DEPLOYED

Summary: 4/5 deployed
```

### Vocabulary Enrichment (Batch Processing)

For batch vocabulary enrichment across a track after modules are content-complete:

```bash
/module-vocab-enrich b2-hist    # Enrich vocab M1→MN in order
```

This command:

- Processes modules **sequentially** (M1 → M2 → ... → MN)
- Adds IPA, translations, POS tags to skeleton vocabulary
- Deduplicates (only NEW words per module)
- Updates vocabulary.db

**When to use:** After Phase 7 (module-vocab) creates skeleton entries, use this for batch enrichment. For single modules, Phase 7-8 handles vocabulary creation and validation.

**Phase files:** `claude_extensions/phases/module-*.md`
**Command files:** `claude_extensions/commands/module-*.md`

---

## Scripts Quick Reference

### Core Pipeline (Python)

| Script                  | Purpose                        | Command                                                      |
| ----------------------- | ------------------------------ | ------------------------------------------------------------ |
| `pipeline.py`           | Full validation pipeline       | `npm run pipeline l2-uk-en a1 5`                             |
| `generate_mdx.py`       | Generate MDX for Docusaurus    | `npm run generate l2-uk-en a1 5`                             |
| `generate_json.py`      | Generate JSON for Vibe app     | `npm run generate:json l2-uk-en a1 5`                        |
| `validate_mdx.py`       | Validate MDX content integrity | `npm run validate:mdx l2-uk-en a1 5`                         |
| `validate_html.py`      | Validate browser rendering     | `npm run validate:html l2-uk-en a1 5`                        |
| `audit_module.py`       | Module quality checker         | `.venv/bin/python scripts/audit_module.py <file>`            |
| `validate_meta_yaml.py` | Meta YAML schema validation    | `.venv/bin/python scripts/validate_meta_yaml.py --level lit` |

### Meta & Vocabulary (Python)

| Script                        | Purpose                        | Command                                                                |
| ----------------------------- | ------------------------------ | ---------------------------------------------------------------------- |
| `validate_meta_yaml.py`       | Meta YAML schema validation    | `.venv/bin/python scripts/validate_meta_yaml.py --level lit`           |
| `fix_invalid_activity_types.py` | Fix invalid activity types in meta | `.venv/bin/python scripts/fix_invalid_activity_types.py [--level b1] [--apply]` |
| `check_hydration.py`          | Fractal outline status checker | `.venv/bin/python scripts/fractal/check_hydration.py --hydrate <file>` |
| `vocab_init.py`               | Create fresh vocabulary DB     | `npm run vocab:init`                                                   |
| `populate_vocab_db.py`        | Populate DB from modules       | `npm run vocab:scan`                                                   |

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

### validate_meta_yaml.py

**Purpose:** Validates meta YAML files against the schema and reports missing fields. Supports auto-detection of full (agent spec) vs minimal (stub) schemas.

**Schemas:**

- `schemas/meta-module.schema.json` - Full agent spec (requires content_outline, sources, vocabulary_hints, activity_hints)
- `schemas/meta-module-minimal.schema.json` - Minimal stub (requires only title, slug, focus)

**Usage:**

```bash
# Validate all levels
.venv/bin/python scripts/validate_meta_yaml.py

# Validate specific level
.venv/bin/python scripts/validate_meta_yaml.py --level lit
.venv/bin/python scripts/validate_meta_yaml.py --level b2-hist

# Show only errors (hide warnings)
.venv/bin/python scripts/validate_meta_yaml.py --level lit --errors-only

# Auto-fix missing optional fields
.venv/bin/python scripts/validate_meta_yaml.py --level lit --fix

# Verbose mode (show all files)
.venv/bin/python scripts/validate_meta_yaml.py --level lit --verbose
```

**Checks:**

- Required fields present per schema
- JSON Schema validation
- `content_outline` word sum vs `word_target`
- `activity_hints` count (recommends 4+)
- `module` vs `id` normalization

**Auto-fix (`--fix`):**

- Adds missing optional fields with defaults (duration: 120, transliteration: none, etc.)
- Copies `id` to `module` if `module` is missing

**Common Issues:**

- **Unquoted colons:** Use `'Text: more text'` for strings containing colons
- **ASCII quotes:** Replace `"..."` with `«...»` for Ukrainian text
- **Missing fields:** Run with `--fix` to add defaults

---

### check_hydration.py

**Purpose:** Fractal hydration checker. Verifies if a Meta YAML has a detailed `content_outline` required for fractal generation. If missing, it provides instructions for the `architect` skill.

**Usage:**

```bash
.venv/bin/python scripts/fractal/check_hydration.py --hydrate curriculum/l2-uk-en/b2-hist/meta/afhanistan.yaml
```

**Logic:**

1. **Check Existence:** Ensures `content_outline` field is present and non-empty.
2. **Template Match:** Locates the corresponding pedagogical template in `docs/l2-uk-en/templates/`.
3. **Action:** If missing, outputs a set of instructions for the AI Agent to activate the `architect` skill to "hydrate" the skeleton with a plan.

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
- **Meta YAML Validation (Seminar Modules):** Enforces strict adherence to `schemas/meta-module.schema.json`.
- **Activity Hints Enforcement:** Reads `activity_hints` from `meta.yaml` and **FAILS** if any specified activity types are missing from `activities.yaml`. This ensures activities match the meta specification.

**Usage:**

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/06-*.md
```

**Issue Categories:**

- **FAIL (Must Fix):** Grammar violations, missing sections, activity syntax, **Missing/Invalid Meta YAML**, **Missing required activity types from meta**
- **WARN (Should Fix):** Richness, variety, word count
- **INFO (Consider):** Optional improvements

**Activity Hints Enforcement Example:**

If `meta.yaml` specifies:
```yaml
activity_hints:
  - type: reading
  - type: quiz
  - type: essay-response
```

And `activities.yaml` only has `quiz` and `fill-in`, the audit will FAIL:
```
❌ Missing required activity types from meta.yaml: essay-response, reading
```

---

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
  planned: 145 # Total modules planned
  status: auto # 'auto' or 'complete'
  description: '...' # For intro.mdx table
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
1. auto_vocab_extract.py          →  Extract new words from module content (Python)
2. enrich_yaml_vocab.py            →  Enrich YAML with IPA and translations (Python)
3. cross_file_integrity (audit)    →  Validate words in activities exist in vocab (Python) [NEW]
4. vocab_init.py                   →  Create empty database (Python)
5. populate_vocab_db.py            →  Populate from module markdown (Python)
```

### auto_vocab_extract.py (NEW)

**Purpose:** Automatically extract Ukrainian vocabulary from module content and create skeleton YAML entries.

**Solves:** Manual vocabulary identification bottleneck for B2-HIST expansion (117 skeleton modules).

```bash
# Extract vocabulary from a module
.venv/bin/python scripts/auto_vocab_extract.py curriculum/l2-uk-en/b2-hist/volodymyr-monomakh.md

# Dry run (preview only)
.venv/bin/python scripts/auto_vocab_extract.py curriculum/l2-uk-en/b2-hist/volodymyr-monomakh.md --dry-run
```

**What it does:**

1. Extracts Ukrainian text from markdown (skips frontmatter, code blocks, tables, English)
2. Tokenizes into individual words
3. Filters out common words (prepositions, pronouns, basic verbs)
4. Loads vocabulary from all prior modules in the level
5. Identifies NEW words not in prior vocabulary
6. Detects POS (noun/verb/adj/adv) using morphology heuristics
7. Creates skeleton YAML entries with empty IPA and translation fields

**Output:** Creates/updates `curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml`

**Example output:**

```yaml
- lemma: лихварство
  ipa: '' # Empty - fill with enrichment
  translation: '' # Empty - fill with enrichment
  pos: noun
  gender: n

- lemma: реформи
  ipa: ''
  translation: ''
  pos: noun

- lemma: видатним
  ipa: ''
  translation: ''
  pos: adj
```

**Next step:** Run enrichment to fill IPA and translations (see `enrich_yaml_vocab.py` below).

**Time savings:** 30 minutes → 5 minutes per module (83% reduction)

---

### cross_file_integrity.py (Audit Check)

**Purpose:** Validate that Ukrainian words used in activities exist in vocabulary YAML files.

**Integration:** Runs automatically as part of `audit_module.py` (integrated check).

```bash
# Runs automatically during module audit
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b2-hist/aneksiia-krymu.md

# Output includes vocabulary integrity violations
```

**What it checks:**

1. Extracts Ukrainian words from activities YAML (`activities/{slug}.yaml`)
2. Loads cumulative vocabulary (current module + all prior modules)
3. Compares used words against available vocabulary
4. Reports violations with actionable fix suggestions

**Example output:**

```
❌ Vocabulary integrity violations: 482
   ✓ Smart matching enabled: 356/838 words matched
     (including 281 inflected forms via stem/fuzzy matching)

   ❌ [VOCABULARY_NOT_DEFINED] Word 'автентику' used in activities...
      Checked: exact match, stem match, fuzzy match - all failed.
      Add to: curriculum/l2-uk-en/b2-hist/vocabulary/aneksiia-krymu.yaml
      Example:
      - lemma: автентику
        ipa: ''
        translation: ''
        pos: noun
```

**✨ SMART MATCHING:** Uses corpus-based fuzzy matching (no external dependencies!)

- **Stem extraction:** Strips Ukrainian case endings (агресії → агрес)
- **Prefix matching:** Handles word families (військовими → військовий)
- **Fuzzy matching:** Edit distance (80% similarity threshold)
- **Performance:** Reduces false positives by 36.8% compared to exact matching

**Accuracy:**

- A1-A2: ~90% accuracy (simple inflection)
- B1-B2: ~60% accuracy (moderate inflection)
- C1-C2: ~50% accuracy (complex inflection)

Remaining false positives are typically irregular forms, diminutives, or prefixed verbs. Manual review recommended for B2+ content.

**Documentation:** See `docs/CROSS-FILE-INTEGRITY.md` for technical details and performance metrics.

---

### outline_compliance.py (Audit Check)

**Purpose:** Validate that markdown content follows content_outline structure from meta YAML.

**Integration:** Runs automatically as part of `audit_module.py` (integrated check).

**What it checks:**

1. All outline sections exist as ## headers in markdown
2. Word count per section meets minimum (-10% warning, -20% error). Over target is acceptable.
3. Extra sections in markdown not in outline

**Example output:**

```
⚠️  Outline compliance: 7 errors, 8 warnings
   ❌ [MISSING_OUTLINE_SECTION] Section 'Повчання Мономаха' not found...
   ❌ [SECTION_LENGTH_MISMATCH] Section 'Вступ' is 82% under target.
   ⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Деколонізаційний погляд' not in outline...
```

**When it activates:**

- Only for modules with `content_outline` in meta YAML
- Gracefully skips modules without outlines
- Common for B2-HIST modules using fractal generation

**Fuzzy matching features:**

- Normalizes section names (em-dashes, punctuation, case)
- 60% similarity threshold via SequenceMatcher
- Handles variations: "Вступ" matches "Вступ — Останній великий князь"

**Thresholds (only for sections UNDER target):**

- **10% under** = WARNING starts
- **20% under** = ERROR starts
- Over target = Acceptable (no violation)

**Documentation:** See `docs/OUTLINE-COMPLIANCE.md` for complete technical details.

---

### vocab_init.py

**Purpose:** Initialize a fresh SQLite vocabulary database with proper schema.

```bash
npm run vocab:init                  # Create database
npm run vocab:init:force            # Force recreate (deletes existing)
.venv/bin/python scripts/vocab_init.py l2-uk-en --force  # Direct invocation
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

> **When to use:** Recommended for high-stakes content (C1/C2, pre-publication).

### Workflow Overview

1. **Generate Queue:** Pre-populate deterministic quality checks for manual validation
2. **Manual Validation:** Human reviewer fills in semantic quality scores
3. **Finalize:** Evaluate CEFR-specific quality gates and generate report
4. **Integrate:** Optional quality report shown in audit output (INFO gate)

### Quality Dimensions (5-Dimension Model)

| Dimension              | Scale    | Measures                                                    |
| ---------------------- | -------- | ----------------------------------------------------------- |
| **Naturalness**        | 1-5      | Robotic → Unnatural → Acceptable → Natural → Highly Natural |
| **Difficulty**         | 3-option | too_easy \| appropriate \| too_hard                         |
| **Distractor Quality** | 1-5      | Nonsense → Weak → Acceptable → Good → Excellent             |
| **Engagement**         | 1-5      | Boring → Low → Neutral → Engaging → Highly Engaging         |
| **Variety**            | 0-100%   | Mechanical pattern detection score                          |

### CEFR Quality Gates

| Level  | Min Naturalness | Max Difficulty Inappropriate | Min Engagement | Min Distractor Quality | Min Variety |
| ------ | --------------- | ---------------------------- | -------------- | ---------------------- | ----------- |
| A1, A2 | None            | None                         | None           | None                   | None        |
| B1     | 3.5             | ≤20%                         | 3.0            | 4.0                    | 60%         |
| B2     | 4.0             | ≤15%                         | 3.5            | 4.2                    | 65%         |
| C1     | 4.5             | ≤10%                         | 4.0            | 4.5                    | 70%         |
| C2     | 4.8             | ≤5%                          | 4.5            | 5.0                    | 75%         |

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

## Level Status Generation

### generate_level_status.py

**Purpose:** Generate status index files showing module completion overview for a level.

**Usage:**

```bash
# Full level (audits all modules)
npm run status:a2              # Generate A2 status
npm run status:b2-hist         # Generate B2-HIST status
npm run status:all             # Generate all levels

# Filtered modules (faster - only audits specified modules)
.venv/bin/python scripts/generate_level_status.py a2 5        # Single module
.venv/bin/python scripts/generate_level_status.py a2 1-4      # Range
.venv/bin/python scripts/generate_level_status.py a2 1-4,6-10 # Multiple ranges
```

**Filter Syntax:**
- `5` - Single module
- `1-4` - Range (modules 1, 2, 3, 4)
- `1-4,6-10` - Multiple ranges (modules 1-4 and 6-10)
- `1,3,5,7-9` - Mixed (modules 1, 3, 5, 7, 8, 9)

**Behavior with filter:**
- Only audits specified modules (faster)
- Preserves existing status for non-filtered modules
- Updates totals based on combined data

**Output:** `docs/{LEVEL}-STATUS.md`

---

## NPM Scripts Summary

```bash
# Level Status
npm run status:a2             # Generate A2 status index
npm run status:b2-hist        # Generate B2-HIST status index
npm run status:all            # Generate all level status indices

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
# Option 1: Use /module command (recommended - runs full 7-phase workflow)
/module b2-hist 5

# Option 2: Manual pipeline after writing content
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/05-*.md
npm run pipeline l2-uk-en a1 5
npm run generate:json l2-uk-en a1 5
```

### Review Module Range

```bash
# 1. Audit multiple modules
for i in {1..20}; do
  .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/$i-*.md
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

Review files are generated in `audit/` subdirectories alongside source modules. They consolidate all validation results in one place.

**Location:** `curriculum/l2-uk-en/{level}/audit/{module-slug}-review.md`

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

| Section        | Status | Count | Notes               |
| -------------- | ------ | ----- | ------------------- |
| **Intro**      | ✅     | 85    | Included in Core    |
| **quiz: Test** | 🎮     | 10    | Activity (10 items) |

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
│       ├── pedagogy.py
│       └── meta_validator.py  # Meta YAML validation (NEW)
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
