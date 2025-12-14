# CLAUDE.md - Project Instructions

## Current Work
**A1 COMPLETE.** All 34 modules pass audit, MDX validation, and HTML validation.

Ready for A2 enrichment or other tasks.

---

## Failure Log (December 2024)

<critical>
**This section documents a pattern of unreliable behavior. Read this first.**

### What Happened
Claude repeatedly failed to follow the documented workflow despite:
1. The workflow being explicitly written in this file
2. The workflow being repeated in SKILL.md
3. Multiple reminders from the user

### Specific Failures
- **Wrote modules from memory** instead of reading curriculum plans first
- **Added vocabulary not in the plan** ("helpful additions" that broke the system)
- **Skipped verification steps** (word counts, richness gates)
- **Didn't run the commands** that were documented as mandatory
- **Pushed forward when gates failed** instead of stopping

### The Core Problem
Claude wrote rules for itself, then ignored them. This is worse than having no rules - it creates false confidence that a process exists.

### What Gemini Did Better
- Read the referenced documents before generating content
- Followed the vocabulary lists exactly
- Created GEMINI.md to persist context and decisions
- Cleaned up redundant files instead of accumulating mess
- Did what was asked, not what it thought was better

### Lesson
**Following instructions > Being "helpful"**

If Claude cannot reliably follow a documented process, it should:
1. Refuse the task
2. Ask for clarification
3. NOT improvise and pretend it followed the process

The user switched to Gemini 2.5 Pro because it follows orders. Capability without reliability is worthless.
</critical>

---

## Module Writing Workflow

<critical>
**EVERY time you write or rewrite a module:**

1. **READ `docs/l2-uk-en/module-prompt.md`** - Grammar constraints, format rules, review checklist.
2. **READ `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md`** - Extract the EXACT vocabulary list and grammar scope.
3. **READ `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`** - Activity counts, sentence complexity, engagement boxes.
4. **WRITE the module** using ONLY the vocabulary and grammar from those documents.
5. **VERIFY** before delivering - check vocabulary matches the plan exactly.

**DO NOT:**
- Write from memory
- Add "helpful" words not in the plan
- Skip reading the prompts because you think you remember them

**The prompts exist because you forget. Read them every time.**
</critical>

## Project Overview

<context>
**Curricula Opus** (CO) is a language content factory generating Ukrainian language learning curricula.

- **Source of truth**: Markdown files in `curriculum/l2-uk-en/{level}/` folders
- **Output**: HTML (web lessons) + JSON (Vibe app import)
- **Current focus**: Ukrainian for English speakers (l2-uk-en)
</context>

## Critical Rules

<constraints>
### NEVER Do These
- NEVER keep old activities when enriching - DELETE ALL and recreate
- NEVER create activities with fewer items than level requirements
- NEVER write sentences shorter than level requirements
- NEVER use vocabulary words not in the module's vocabulary section

### ALWAYS Do These
- ALWAYS delete ALL existing activities before creating new ones
- ALWAYS verify activity answers are correct
- ALWAYS use vocabulary from the module's vocabulary section
- ALWAYS add vocabulary that the curriculum plan demands
</constraints>

## Parallel Module Creation

<instructions>
**Modules can be created in parallel.** Vocabulary validation is deferred to the end.

### Per-Module Workflow
1. **READ** the curriculum plan for vocabulary and grammar scope
2. **WRITE** the module with all required sections
3. **RUN AUDIT** to check structure, activities, pedagogy
4. **FIX** any issues until audit passes
5. **RUN PIPELINE** to validate and generate output

### After All Modules Complete
```bash
npm run vocab:rebuild    # Build master vocabulary database
```
This validates vocabulary across all modules at once.

### Generate & Validate Output
```bash
# Full pipeline (recommended) - validates at each step
npm run pipeline l2-uk-en a1 [moduleNum]

# Or separately:
npm run generate l2-uk-en a1 [moduleNum]      # MDX for Docusaurus
npm run generate:json l2-uk-en a1 [moduleNum] # JSON for Vibe app
npm run validate:mdx l2-uk-en a1 [moduleNum]  # Content integrity
npm run validate:html l2-uk-en a1 [moduleNum] # Browser rendering
```

**Pipeline validates:**
1. **Lint** - MD format compliance
2. **Generate** - Creates MDX for Docusaurus
3. **Validate MDX** - Ensures no content loss
4. **Validate HTML** - Headless browser check (requires dev server)
</instructions>

## Activity & Content Requirements

> **Single source of truth:** See `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` for all richness parameters including:
> - Activity counts and items per activity
> - Content quality (examples, engagement boxes, immersion)
> - Sentence complexity (fill-in/unjumble word counts)
> - Time and vocabulary targets

### Activity Types (13 Total)

**Core Activities (All Levels):**
- `quiz` - Multiple choice (single answer)
- `match-up` - Match pairs (Ukrainian ↔ English)
- `fill-in` - Gap fill with dropdown options
- `true-false` - Statement validation
- `group-sort` - Sort items into categories
- `unjumble` - Reorder words into sentence

**A1-Only Activity:**
- `anagram` - Letter unscrambling (M01-10 only, Cyrillic scaffolding)

**A2+ Activities:**
- `error-correction` - Find and fix grammatical errors
- `cloze` - Passage completion with multiple blanks
- `mark-the-words` - Click words matching criteria (nouns, verbs, etc.)
- `dialogue-reorder` - Put conversation lines in order
- `select` - Multi-checkbox (multiple correct answers)
- `translate` - Translation multiple choice

**Note:** `observe-first` is a pedagogical content pattern (inline `> [!observe]` callout), not an activity type. Use it before grammar explanations for inductive pattern discovery.

### Activity Matrix

> **Full matrix:** See `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` for the complete activity requirements by level.

| Activity | A1 | A2 | B1+ |
|----------|----|----|-----|
| quiz, match-up, fill-in, group-sort, unjumble | ✓ | ✓ | ✓ |
| true-false | ✓ | ✓ | ✓ (opt C1+) |
| anagram | M01-10 | ❌ | ❌ |
| error-correction, cloze, mark-the-words, dialogue-reorder | ❌ | ✓ | ✓ |
| select, translate | ❌ | opt | ✓ |

### Anagram Phaseout (A1 Only)
- **A1 Modules 01-10**: Allowed (scaffolding for Cyrillic learners)
- **A1 Modules 11-20**: Reduce usage (transition period)
- **A1 Modules 21-34**: Avoid (use unjumble instead)
- **A2+**: NOT ALLOWED

### Engagement Box Types
- 💡 **Did You Know** - Interesting facts
- 🎬 **Pop Culture Moment** - Movies, games, music references
- 🌍 **Real World** - Practical usage scenarios
- 🎯 **Fun Fact** - Memorable trivia
- 🎮 **Gamer's Corner** - Gaming references (S.T.A.L.K.E.R., Witcher)

## Directory Structure

```
curricula-opus/
├── curriculum/l2-uk-en/
│   ├── a1/               # A1 modules (34 modules)
│   ├── a2/               # A2 modules (50 modules)
│   ├── b1/               # B1 modules (80 modules)
│   ├── b2/               # B2 modules (125 modules)
│   ├── c1/               # C1 modules (115 modules)
│   ├── c2/               # C2 modules (80 modules)
│   ├── vocabulary.db     # Master vocabulary database (SQLite)
│   └── module-mapping.json  # Old→new path mapping reference
├── scripts/              # Generator code
├── output/               # Generated HTML + JSON
└── docs/                 # Documentation
    └── l2-uk-en/         # Ukrainian-specific docs
        └── MODULE-RICHNESS-GUIDELINES-v2.md  # Quality standards (consolidated)
```

**Note:** Level structure follows the Ukrainian State Standard 2024 which defines 6 official levels: A1, A2, B1, B2, C1, C2 (no "plus" levels).

### Module File Naming

Modules use level-relative numbering with slugified titles:
- `a1/01-the-cyrillic-code-i.md` (first A1 module)
- `a1/34-checkpoint-a1.md` (last A1 module)
- `b1/01-dative-case.md` (first B1 module)

Level and module number are derived from the file path, not frontmatter.

## Level Definitions (Ukrainian State Standard 2024)

| Level | Folder | Modules | Vocab Target | Description |
|-------|--------|---------|--------------|-------------|
| A1 | `a1/` | 34 | ~750 | Beginner - Cyrillic, basic phrases, simple grammar |
| A2 | `a2/` | 50 | ~1,050 | Elementary - All 7 cases, aspect basics, comparison |
| B1 | `b1/` | 80 | ~1,500 | Intermediate - Aspect mastery, motion verbs, complex sentences |
| B2 | `b2/` | 135 | ~2,900 | Advanced - Literature, academic, professional |
| C1 | `c1/` | 115 | ~2,800 | Proficient - Full complexity, specialized topics |
| C2 | `c2/` | 80 | ~2,000 | Mastery - Native-level proficiency |

**Vocabulary Progression:**
- A1: ~750 cumulative
- A2: ~1,800 cumulative
- B1: ~3,300 cumulative
- B2: ~6,200 cumulative
- C1: ~9,000 cumulative
- C2: ~11,000 cumulative

## Transliteration Strategy

- **Modules 1-10 (A1.1)**: Full transliteration `Слово (Slovo)`
- **Modules 11-20 (A1.2)**: Vocab lists only, sentences Cyrillic
- **Modules 21-34 (A1.3)**: First occurrence only
- **A2+ (modules 31+)**: No transliteration

## Commands Reference

```bash
# Full Pipeline (recommended) - lint → generate → validate MDX → validate HTML
npm run pipeline l2-uk-en a1           # All modules in level
npm run pipeline l2-uk-en a1 5         # Specific module

# Generate MDX (Docusaurus web lessons) - Python
npm run generate l2-uk-en              # All levels
npm run generate l2-uk-en a1           # Specific level
npm run generate l2-uk-en a1 5         # Specific module

# Generate JSON (Vibe app import) - Python
npm run generate:json l2-uk-en         # All levels
npm run generate:json l2-uk-en a1      # Specific level
npm run generate:json l2-uk-en a1 5    # Specific module

# Validation (standalone)
npm run validate:mdx l2-uk-en a1       # Check MDX content integrity
npm run validate:html l2-uk-en a1      # Browser rendering check (needs dev server)

# Run audit
python3 scripts/audit_module.py {file_path}

# Vocabulary
npm run vocab:enrich l2-uk-en [moduleNum]
npm run vocab:rebuild                  # Rebuild vocabulary database

# Deploy Claude skills
npm run claude:deploy
```

**Note:** HTML validation requires Docusaurus dev server: `cd docusaurus && npm start`

## Vocabulary Section Formats

| Level | Header | Columns |
|-------|--------|---------|
| A1, A2 | `# Vocabulary` | Word \| IPA \| English \| POS \| Gender \| Note |
| B1 | `# Словник` | Слово \| Вимова \| Переклад \| ЧМ \| Примітка |
| B2, C1, C2 | `# Словник` | Слово \| Переклад \| Примітки |

## Level Status

| Level | Modules | Status | Pipeline | Next Step |
|-------|---------|--------|----------|-----------|
| A1 | 34/34 | ✅ Complete | ✅ All pass | Ready |
| A2 | 5/50 | ⏳ In progress | ⏳ | Continue enrichment |
| B1 | 5/80 | ⏳ In progress | ⏳ | Waiting for A2 |
| B2 | 0/125 | ❌ Not started | ❌ | Waiting for B1 |
| C1 | 0/115 | ❌ Not started | ❌ | Waiting for B2 |
| C2 | 0/80 | ❌ Not started | ❌ | Waiting for C1 |

**Per-level workflow:**
1. Build all modules (stages 1-3)
2. Run audit, fix issues until pass
3. Run pipeline: `npm run pipeline l2-uk-en {level}`
4. Generate JSON: `npm run generate:json l2-uk-en {level}`
5. Finalize vocabulary → `npm run vocab:rebuild`
6. THEN next level can begin

## Documentation Links

- `docs/ARCHITECTURE.md` - System architecture
- `docs/MARKDOWN-FORMAT.md` - Markdown syntax spec (all activity formats)
- `docs/ACTIVITY-MARKDOWN-REFERENCE.md` - **Activity syntax patterns for AI agents** (READ THIS when writing activities)
- `docs/SCRIPTS.md` - Scripts reference
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards + activity matrix
- `docs/l2-uk-en/claude-review-prompt.md` - Review prompts
- `docusaurus/docs/activity-test.mdx` - Interactive activity demo (live preview)
