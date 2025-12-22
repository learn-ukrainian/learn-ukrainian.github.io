# Curricula-Opus Architecture

## Overview

Curricula-Opus (CO) is a content factory that generates Ukrainian language learning materials from Markdown source files.

```
┌─────────────────────────────────────────────────────────────────┐
│                     SOURCE (Markdown)                           │
│                                                                 │
│   curriculum/l2-uk-en/{level}/*.md                              │
│   - Frontmatter (YAML metadata)                                 │
│   - Lesson content (sections)                                   │
│   - Activities (## quiz:, ## match-up:, etc.)                   │
│   - Vocabulary tables                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   generate-mdx.ts       │     │   generate_json.py      │
│   (TypeScript)          │     │   (Python 3.12)         │
└───────────┬─────────────┘     └───────────┬─────────────┘
            ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│     MDX OUTPUT          │     │     JSON OUTPUT         │
│     (Docusaurus)        │     │     (For Vibe)          │
│                         │     │                         │
│ docusaurus/docs/{level}/│     │ output/json/l2-uk-en/   │
│ - Interactive lessons   │     │ - moduleType            │
│ - React components      │     │ - immersionLevel        │
│ - Live activities       │     │ - sections (raw md)     │
└───────────┬─────────────┘     └───────────┬─────────────┘
            ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│     DOCUSAURUS WEB      │     │     VIBE APP            │
│                         │     │                         │
│ - Static site           │     │ - Extracts activities   │
│ - GitHub Pages          │     │ - Creates flash cards   │
│ - krisztiankoos.github  │     │ - Interactive workbook  │
│   .io/curricula-opus    │     │                         │
└─────────────────────────┘     └─────────────────────────┘
```

## Directory Structure

```
curricula-opus/
├── curriculum/                    # SOURCE OF TRUTH
│   └── l2-uk-en/
│       ├── a1/                    # A1 modules (30)
│       ├── a2/                    # A2 modules (50)
│       ├── b1/                    # B1 modules (80)
│       ├── b2/                    # B2 modules (125)
│       ├── c1/                    # C1 modules (115)
│       ├── c2/                    # C2 modules (80)
│       ├── vocabulary.db          # SQLite vocabulary database
│       └── *-CURRICULUM-PLAN.md   # Level planning docs
│
├── scripts/                       # GENERATOR CODE
│   ├── generate-mdx.ts            # MDX generator (Docusaurus)
│   ├── generate_json.py           # JSON generator (Python)
│   ├── module-audit.ts            # Module quality checker
│   ├── vocab-*.ts                 # Vocabulary scripts
│   └── lib/
│       ├── parsers/               # Markdown parsing
│       │   ├── frontmatter.ts
│       │   ├── sections.ts
│       │   ├── vocabulary.ts
│       │   └── activities/
│       ├── renderers/
│       │   └── json.ts            # JSON renderer (legacy TS)
│       ├── utils/
│       │   └── markdown.ts
│       └── types.ts
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
└── docs/                          # DOCUMENTATION
    ├── ARCHITECTURE.md            # This file
    ├── MARKDOWN-FORMAT.md         # Markdown syntax spec
    └── SCRIPTS.md                 # Scripts reference
```

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

| Level | Modules | Immersion | English % | Ukrainian % |
|-------|---------|-----------|-----------|-------------|
| A1 | 1-30 | 0.30 | 70% | 30% |
| A2 | 31-60 | 0.40 | 60% | 40% |
| A2+ | 61-80 | 0.50 | 50% | 50% |
| B1 | 81-120 | 0.60 | 40% | 60% |
| B1+ | 121-160 | 0.70 | 30% | 70% |
| B2 | 161-200 | 0.85 | 15% | 85% |
| B2+ | 201-240 | 0.90 | 10% | 90% |
| C1 | 241+ | 0.95 | 5% | 95% |

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
- **GitHub Pages**: Deployed to krisztiankoos.github.io/curricula-opus

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

| Level | Modules | EN % | UK % | Notes |
|-------|---------|------|------|-------|
| A1 | 1-30 | 70% | 30% | Transliteration in early modules |
| A2 | 31-60 | 60% | 40% | Bilingual headers |
| A2+ | 61-80 | 50% | 50% | Transition phase |
| B1 | 81-120 | 40% | 60% | Ukrainian headers, some Ukrainian instructions |
| B1+ | 121-160 | 30% | 70% | More Ukrainian, English for complex grammar |
| B2 | 161-200 | 0% | 100% | Full immersion |
| B2+ | 201-240 | 0% | 100% | Full immersion |
| C1 | 241+ | 0% | 100% | Full immersion (native) |

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

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2024-12-02 | moduleType, immersionLevel, simplified sections |
| 1.0 | 2024-11-30 | Initial JSON format |
