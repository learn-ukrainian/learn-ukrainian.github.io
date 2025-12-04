# CLAUDE.md - Project Instructions

## Project Overview

<context>
**Curricula Opus** (CO) is a language content factory generating Ukrainian language learning curricula.

- **Source of truth**: Markdown files in `curriculum/l2-uk-en/modules/`
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

## Activity Requirements by Level

<format>
| Level | Modules | Activities | Items/Activity | Fill-in Words | Unjumble Words |
|-------|---------|------------|----------------|---------------|----------------|
| A1 | 1-30 | 8+ | 12+ | 5-8 | 5-8 |
| A2 | 31-60 | 10+ | 12+ | 6-9 | 6-9 |
| A2+ | 61-80 | 10+ | 12+ | 6-10 | 6-10 |
| B1 | 81-120 | 12+ | 14+ | 7-11 | 7-11 |
| B1+ | 121-160 | 12+ | 14+ | 8-12 | 8-12 |
| B2 | 161-200 | 14+ | 16+ | 9-14 | 9-14 |
| B2+ | 201-240 | 14+ | 16+ | 10-15 | 10-15 |
| C1 | 241+ | 16+ | 18+ | 12-18 | 12-18 |

### Activity Types Required
Each module needs variety. Include at least 4 different types:
- `fill-in` - Gap fill with options
- `unjumble` - Reorder words into sentence
- `quiz` - Multiple choice questions
- `match-up` - Match pairs
- `group-sort` - Sort items into categories
- `true-false` - True/false statements
</format>

## Content Quality Requirements

<format>
| Level | Examples | Engagement Boxes | Content Words | Immersion |
|-------|----------|------------------|---------------|-----------|
| A1 | 12+ | 3+ | 600+ | 30% Ukrainian |
| A2 | 15+ | 4+ | 700+ | 40% Ukrainian |
| A2+ | 18+ | 4+ | 800+ | 50% Ukrainian |
| B1 | 22+ | 5+ | 900+ | 60% Ukrainian |
| B1+ | 24+ | 5+ | 950+ | 70% Ukrainian |
| B2 | 26+ | 6+ | 1000+ | 85% Ukrainian |
| B2+ | 28+ | 6+ | 1050+ | 90% Ukrainian |
| C1 | 30+ | 7+ | 1100+ | 95% Ukrainian |

### Engagement Box Types
- 💡 **Did You Know** - Interesting facts
- 🎬 **Pop Culture Moment** - Movies, games, music references
- 🌍 **Real World** - Practical usage scenarios
- 🎯 **Fun Fact** - Memorable trivia
- 🎮 **Gamer's Corner** - Gaming references (S.T.A.L.K.E.R., Witcher)
</format>

## Directory Structure

```
curricula-opus/
├── curriculum/l2-uk-en/
│   ├── modules/           # SOURCE OF TRUTH - 240+ markdown files
│   └── vocabulary.csv     # Master vocabulary database
├── scripts/               # Generator code
├── output/                # Generated HTML + JSON
└── docs/                  # Documentation
    └── l2-uk-en/          # Ukrainian-specific docs
        └── MODULE-RICHNESS-GUIDELINES.md  # Quality standards
```

## Level Definitions

| Level | Modules | Description |
|-------|---------|-------------|
| A1 | 1-30 | Beginner - Cyrillic, basic phrases, simple grammar |
| A2 | 31-60 | Elementary - Cases intro, present tense, basic vocab |
| A2+ | 61-80 | Pre-Intermediate - All cases, past tense |
| B1 | 81-120 | Intermediate - Complex grammar, expanded vocab |
| B1+ | 121-160 | Upper-Intermediate - Refinement, nuance |
| B2 | 161-200 | Advanced - Complex structures, abstract topics |
| B2+ | 201-240 | Upper-Advanced - Near-native patterns |
| C1 | 241-400 | Proficient - Full complexity, specialized topics |

## Transliteration Strategy

- **Modules 1-10 (A1.1)**: Full transliteration `Слово (Slovo)`
- **Modules 11-20 (A1.2)**: Vocab lists only, sentences Cyrillic
- **Modules 21-30 (A1.3)**: First occurrence only
- **Modules 31+ (A2+)**: No transliteration

## Commands Reference

```bash
# Generate output
npx ts-node scripts/generate.ts l2-uk-en [moduleNum]

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
| A1-A2+ (1-80) | `# Vocabulary` | Word \| IPA \| English \| POS \| Gender \| Note |
| B1-B1+ (81-160) | `# Словник` | Слово \| Вимова \| Переклад \| ЧМ \| Примітка |
| B2-C1 (161+) | `# Словник` | Слово \| Переклад \| Примітки |

## Enrichment Status

| Range | Modules | Status |
|-------|---------|--------|
| A1 | 1-30 | ⏳ Needs full enrichment |
| A2 | 31-60 | ⏳ Needs full enrichment |
| A2+ | 61-80 | ⏳ Needs full enrichment |
| B1 | 81-120 | ⏳ Needs full enrichment |
| B1+ | 121-160 | ✅ Done |
| B2 | 161-200 | ⏳ Needs full enrichment |
| B2+ | 201-240 | ⏳ Needs creation |
| C1 | 241-400 | ⏳ Needs creation |

## Documentation Links

- `docs/ARCHITECTURE.md` - System architecture
- `docs/MARKDOWN-FORMAT.md` - Markdown syntax spec
- `docs/SCRIPTS.md` - Scripts reference
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES.md` - Quality standards
- `docs/l2-uk-en/claude-review-prompt.md` - Review prompts
