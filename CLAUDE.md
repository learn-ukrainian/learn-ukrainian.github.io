# CLAUDE.md - Project Instructions

## Project Overview

**Curricula Opus** (CO) is a language content factory generating Ukrainian language learning curricula.

**Source of truth**: Markdown files in `curriculum/l2-uk-en/modules/`

**Output formats:**
- **HTML** (book-style) - Readable lessons for web viewing
- **JSON** (v2) - Structured data for Vibe app import

**Documentation:**
- `docs/ARCHITECTURE.md` - Full system architecture
- `docs/MARKDOWN-FORMAT.md` - Markdown syntax spec
- `docs/VIBE-IMPORT-INSTRUCTIONS.md` - JSON import guide

## Directory Structure

```
curricula-opus/
├── curriculum/                    # SOURCE OF TRUTH
│   └── l2-uk-en/
│       ├── modules/               # 190 markdown module files
│       │   ├── module-01.md       # A1: The Cyrillic Code I
│       │   ├── module-168.md      # B2: History: Kyivan Rus II
│       │   └── ...
│       └── vocabulary.csv         # Master vocabulary database
│
├── scripts/                       # GENERATOR CODE
│   ├── generate.ts                # Main entry point
│   └── lib/
│       ├── parsers/               # Markdown parsing
│       ├── renderers/             # HTML + JSON generation
│       └── utils/                 # Utilities
│
├── output/                        # GENERATED OUTPUT
│   ├── html/l2-uk-en/             # Web-viewable lessons (book)
│   └── json/l2-uk-en/             # Vibe import data
│
└── docs/                          # DOCUMENTATION
    ├── ARCHITECTURE.md
    ├── MARKDOWN-FORMAT.md
    └── VIBE-IMPORT-INSTRUCTIONS.md
```

## Language Pair Naming Convention

Format: `{type}-{target}-{source}`

| Code | Type | Target Language | Source Language | Description |
|------|------|-----------------|-----------------|-------------|
| `l2-uk-en` | L2 | Ukrainian | English | Ukrainian for English speakers |
| `l2-uk-es` | L2 | Ukrainian | Spanish | Ukrainian for Spanish speakers |
| `l2-en-uk` | L2 | English | Ukrainian | English for Ukrainian speakers |
| `l1-uk` | L1 | Ukrainian | - | Ukrainian for native speakers |
| `l1-en` | L1 | English | - | English for native speakers |

## JSON Schema (v2)

```json
{
  "lesson": {
    "id": "lesson-uk-B2-168",
    "moduleNumber": 168,
    "moduleType": "history",          // grammar, vocabulary, history, etc.
    "immersionLevel": 0.85,           // 0.0-1.0 (% Ukrainian)
    "title": "History: Kyivan Rus II",
    "level": "B2",
    "sections": [                     // Raw markdown sections
      { "name": "Вступ", "type": "intro", "content": "..." }
    ],
    "rawMarkdown": "..."              // Full source
  },
  "activities": [...],
  "vocabulary": {...}
}
```

### Module Types
| Type | Tags | Description |
|------|------|-------------|
| `grammar` | grammar, cases, verbs, aspect | Grammar lessons |
| `vocabulary` | vocabulary, vocab | Word-building |
| `checkpoint` | review, checkpoint | Assessment |
| `history` | history | Ukrainian history |
| `biography` | biography | Famous Ukrainians |
| `idioms` | idioms, phraseology | Expressions |
| `literature` | literature, poetry | Text analysis |

## Key Rules

### Transliteration Strategy
- **Modules 1-10 (A1.1)**: Full transliteration `Слово (Slovo)`
- **Modules 11-20 (A1.2)**: Vocab lists only, sentences Cyrillic
- **Modules 21-30 (A1.3)**: First occurrence only
- **Modules 31+ (A2+)**: No transliteration

### Immersion Strategy (immersionLevel field)
| Level | Ukrainian % | English % | immersionLevel |
|-------|-------------|-----------|----------------|
| A1 | 30% | 70% | 0.30 |
| A2 | 40% | 60% | 0.40 |
| A2+ | 50% | 50% | 0.50 |
| B1 | 60% | 40% | 0.60 |
| B2 | 85% | 15% | 0.85 |
| C1 | 95% | 5% | 0.95 |

### Vocabulary Targets
| Level | New Words | Cumulative |
|-------|-----------|------------|
| A1    | 750       | 750        |
| A2    | 1,050     | 1,800      |
| B1    | 1,500     | 3,300      |
| B2    | 2,200     | 5,500      |
| C1    | 2,500     | 8,000      |

### Module Types
- **G-Module (Grammar)**: 15-20 new words, grammar focus
- **V-Module (Vocabulary)**: 35-45 new words, vocab focus
- **F-Module (Function)**: 20-30 new words, real-world practice
- **R-Module (Review)**: 0-10 new words, assessment

## Generation Commands

```bash
# Generate ALL output (JSON + HTML)
npx ts-node scripts/generate.ts

# Generate specific language pair
npx ts-node scripts/generate.ts l2-uk-en

# Generate single module
npx ts-node scripts/generate.ts l2-uk-en 168
```

**Reads from:** `curriculum/l2-uk-en/modules/module-*.md`

**Outputs to:**
- `output/json/l2-uk-en/{level}/module-XX.json`
- `output/html/l2-uk-en/{level}/module-XX.html`

## Workflow

1. Edit markdown files in `curriculum/l2-uk-en/modules/`
2. Run generator: `npx ts-node scripts/generate.ts l2-uk-en`
3. Output appears in `output/`
4. Vibe imports JSON from `output/json/`

## Module Creation & Enrichment Workflow

### Creating New Modules (B1+)

When creating a new module, complete ALL steps before moving to next module:

1. **Write content** - lesson, grammar explanations, examples
2. **Create activities** - fill-in, unjumble, quiz, match-up
   - Fill-in sentences: 5-7 words with realistic context
   - Unjumble sentences: 6-8 words with complex structures
3. **Add basic vocab section** - all words used in module
4. **Run vocab enrichment**: `npm run vocab:enrich l2-uk-en [moduleNum]`
5. **Generate output**: `npx ts-node scripts/generate.ts l2-uk-en [moduleNum]`
6. **Verify** - spot-check HTML output

### Enrichment Methods

| Task | Method | Command |
|------|--------|---------|
| Activity enrichment | Manual (Claude) | - |
| Vocab enrichment | Script | `npm run vocab:enrich l2-uk-en [moduleNum]` |

### Batch Enrichment Status

Activity enrichment (manual, must be done before vocab enrichment):

| Range | Modules | Status |
|-------|---------|--------|
| A1 | 1-30 | ✅ Done |
| A2 | 31-60 | ⏳ Pending |
| A2+ | 61-80 | ⏳ Pending |
| B1.1 | 81-100 | ⏳ Pending |
| B1.2-B1.4 | 101-140 | ⏳ Pending |

After activity enrichment, run vocab enrichment for the range:
```bash
npm run vocab:enrich l2-uk-en
npx ts-node scripts/generate.ts l2-uk-en
```

### Vocabulary Section Formats

See `docs/MARKDOWN-FORMAT.md` for complete spec. Quick reference:

| Level | Modules | Header | Columns |
|-------|---------|--------|---------|
| A1-A2+ | 1-80 | `# Vocabulary` | Word \| IPA \| English \| POS \| Gender \| Note |
| B1 | 81-160 | `# Словник` | Слово \| Вимова \| Переклад \| ЧМ \| Примітка |
| B2+ | 161+ | `# Словник` | Слово \| Переклад \| Примітки |

## Markdown Format

See `docs/MARKDOWN-FORMAT.md` for full spec. Key patterns:

```markdown
# Answer syntax (hidden, toggleable)
> [!answer] **відповідь**

# Activity blocks
## quiz: Title
## match-up: Title
## group-sort: Title

# Section headers
# Вступ / # Introduction
# Практика / # Practice
# Словник / # Vocabulary
```
