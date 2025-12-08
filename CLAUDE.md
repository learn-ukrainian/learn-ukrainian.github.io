# CLAUDE.md - Project Instructions

## Current Work
A1 modules complete. Ready for A2 enrichment or other tasks.

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
- NEVER add activities without rebuilding vocabulary first
- NEVER keep old activities when enriching - DELETE ALL and recreate
- NEVER skip the 3-step enrichment workflow
- NEVER create activities with fewer items than level requirements
- NEVER write sentences shorter than level requirements
- NEVER use vocabulary words not in the module's vocabulary section

### ALWAYS Do These
- ALWAYS follow the 3-step enrichment workflow in exact order
- ALWAYS delete ALL existing activities before creating new ones
- ALWAYS run vocab:enrich after narrative changes
- ALWAYS verify activity answers are correct
- ALWAYS use vocabulary from the module's vocabulary section
</constraints>

## Module Enrichment Workflow

<instructions>
**This is the ONLY correct way to enrich a module. No shortcuts.**

### Step 1: ENRICH NARRATIVE CONTENT
- Make lesson rich with examples, engagement boxes, explanations
- Add: 💡 Did You Know, 🎬 Pop Culture Moment, 🌍 Real World, etc.
- Ensure 12+ example sentences for A1, more for higher levels
- DO NOT touch activities section yet

### Step 2: REBUILD VOCABULARY
```bash
npm run vocab:enrich l2-uk-en [moduleNum]
```
- Captures ALL words from enriched lesson
- Must run AFTER narrative changes, BEFORE activities
- **If vocab:enrich made changes**, also run:
```bash
npm run vocab:rebuild
```
- This rebuilds the master vocabulary database (vocabulary.csv)

### Step 3: COMPLETELY RECREATE ALL ACTIVITIES
- **DELETE every existing activity** - no exceptions
- Create fresh activities using ONLY vocabulary from Step 2
- Meet all quality requirements (see Activity Requirements below)
- Verify every answer is correct

### Step 4: GENERATE AND VERIFY
```bash
npx ts-node scripts/generate.ts l2-uk-en [moduleNum]
```
- Check HTML output in browser
- Verify activities work correctly
</instructions>

## Activity & Content Requirements

> **Single source of truth:** See `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` for all richness parameters including:
> - Activity counts and items per activity
> - Content quality (examples, engagement boxes, immersion)
> - Sentence complexity (fill-in/unjumble word counts)
> - Time and vocabulary targets

### Activity Types
- `fill-in` - Gap fill with options
- `unjumble` - Reorder words into sentence
- `quiz` - Multiple choice questions
- `match-up` - Match pairs
- `group-sort` - Sort items into categories
- `true-false` - True/false statements

### Anagram Activity Rules
- `anagram` - Letter unscrambling (A1 ONLY, phased out)
  - **A1 Modules 01-10**: Allowed (scaffolding for Cyrillic learners)
  - **A1 Modules 11-20**: Reduce usage (transition period)
  - **A1 Modules 21-30**: Avoid (use unjumble instead)
  - **A2+**: NOT ALLOWED - use `unjumble` for word ordering practice

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
│   ├── a1/               # A1 modules (30 modules)
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
- `a1/30-checkpoint-a1.md` (last A1 module)
- `b1/01-dative-case.md` (first B1 module)

Level and module number are derived from the file path, not frontmatter.

## Level Definitions (Ukrainian State Standard 2024)

| Level | Folder | Modules | Vocab Target | Description |
|-------|--------|---------|--------------|-------------|
| A1 | `a1/` | 30 | ~750 | Beginner - Cyrillic, basic phrases, simple grammar |
| A2 | `a2/` | 50 | ~1,050 | Elementary - All 7 cases, aspect basics, comparison |
| B1 | `b1/` | 80 | ~1,500 | Intermediate - Aspect mastery, motion verbs, complex sentences |
| B2 | `b2/` | 125 | ~2,900 | Advanced - Literature, academic, professional |
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
- **Modules 21-30 (A1.3)**: First occurrence only
- **A2+ (modules 31+)**: No transliteration

## Commands Reference

```bash
# Generate all levels
npx ts-node scripts/generate.ts l2-uk-en

# Generate specific level
npx ts-node scripts/generate.ts l2-uk-en a1

# Generate specific module (level + module number)
npx ts-node scripts/generate.ts l2-uk-en a1 5

# Enrich vocabulary
npm run vocab:enrich l2-uk-en [moduleNum]

# Run audit
npx ts-node scripts/module-audit.ts l2-uk-en [moduleNum]

# Deploy Claude skills
npm run claude:deploy
```

## Vocabulary Section Formats

| Level | Header | Columns |
|-------|--------|---------|
| A1, A2 | `# Vocabulary` | Word \| IPA \| English \| POS \| Gender \| Note |
| B1 | `# Словник` | Слово \| Вимова \| Переклад \| ЧМ \| Примітка |
| B2, C1, C2 | `# Словник` | Слово \| Переклад \| Примітки |

## Enrichment Status

| Level | Modules | Status |
|-------|---------|--------|
| A1 | 01-30 | ✅ Complete |
| A2 | 01-50 | ⏳ Needs full enrichment |
| B1 | 01-80 | ⏳ Needs creation |
| B2 | 01-125 | ⏳ Needs creation |
| C1 | 01-115 | ⏳ Needs creation |
| C2 | 01-80 | ⏳ Needs creation |

## Documentation Links

- `docs/ARCHITECTURE.md` - System architecture
- `docs/MARKDOWN-FORMAT.md` - Markdown syntax spec
- `docs/SCRIPTS.md` - Scripts reference
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Quality standards (consolidated)
- `docs/l2-uk-en/claude-review-prompt.md` - Review prompts
