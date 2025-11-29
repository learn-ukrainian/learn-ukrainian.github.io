# CLAUDE.md - Project Instructions

## Project Overview

**Curricula Opus** is a language content factory generating educational curricula for multiple language pairs and contexts.

**Supported curriculum types:**
- **L2 (Second Language)**: For learners acquiring a new language
  - `l2-uk-en`: Ukrainian for English speakers
  - `l2-uk-es`: Ukrainian for Spanish speakers (future)
  - `l2-en-uk`: English for Ukrainian speakers (future)
- **L1 (First Language)**: For native speakers (literacy, literature, advanced study)
  - `l1-uk`: Ukrainian for native Ukrainian speakers (future)

**Output formats:**
- JSON (for Vibe app import)
- Markdown (human-readable textbooks)
- HTML (web-based viewing)

## Directory Structure

```
curricula-opus/
├── curriculum/                 # Source of truth (per language pair)
│   ├── l2-uk-en/              # Ukrainian L2 for English speakers
│   │   ├── master-plan.json   # CEFR structure, methodology
│   │   ├── modules-a1.json    # A1 module definitions
│   │   ├── modules-a2.json    # A2 module definitions
│   │   ├── modules-b1.json    # B1 module definitions
│   │   ├── modules-b2.json    # B2 module definitions
│   │   └── modules-c1.json    # C1 module definitions
│   ├── l2-uk-es/              # Ukrainian L2 for Spanish speakers (future)
│   └── l1-uk/                 # Ukrainian L1 (future)
├── vocabulary/                 # Vocabulary databases (per language pair)
│   ├── l2-uk-en/
│   │   ├── vocab-a1.json
│   │   ├── vocab-a2.json
│   │   └── ...
│   └── l1-uk/
├── schemas/                    # JSON schemas (shared)
│   └── vibe-schema.json
├── output/                     # Generated content
│   ├── json/
│   │   └── l2-uk-en/
│   ├── markdown/
│   │   └── l2-uk-en/
│   └── html/
│       └── l2-uk-en/
└── scripts/                    # Generation scripts
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

## JSON Schema Types

### 1. Lesson (`lesson.json`)
```json
{
  "id": "lesson-uk-A1-01",
  "moduleId": "mod-uk-A1-01",
  "title": "The Cyrillic Code I",
  "titleUk": "Кирилиця I",           // Ukrainian title (B1+)
  "level": "A1",
  "objectives": [...],
  "phases": [...]                     // PPP structure
}
```

### 2. Vocabulary (`vocabulary.json`)
```json
{
  "id": "v-stіl",
  "uk": "стіл",
  "uk_translit": "stil",              // Only in A1.1
  "ipa": "/stil/",
  "en": "table",
  "gender": "m",
  "pos": "noun",
  "declension": "2",
  "forms": { "gen_sg": "стола", ... },
  "level": "A1"
}
```

### 3. Activity (`activity-*.json`)
Types: `flash-cards`, `match-up`, `gap-fill`, `group-sort`, `unjumble`, `quiz`, `true-false`

## Key Rules

### Transliteration Strategy
- **Modules 1-10 (A1.1)**: Full transliteration `Слово (Slovo)`
- **Modules 11-20 (A1.2)**: Vocab lists only, sentences Cyrillic
- **Modules 21-30 (A1.3)**: First occurrence only
- **Modules 31+ (A2+)**: No transliteration

### Immersion Strategy
- **A1**: 95% English / 5% Ukrainian
- **A2**: 70% English / 30% Ukrainian
- **B1**: 40% English / 60% Ukrainian (instructions in Ukrainian)
- **B2**: 15% English / 85% Ukrainian
- **C1**: 5% English / 95% Ukrainian

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
# Generate ALL output (JSON + HTML) for all language pairs
npx ts-node scripts/generate.ts

# Generate only for a specific language pair
npx ts-node scripts/generate.ts l2-uk-en

# Generate only a specific module
npx ts-node scripts/generate.ts l2-uk-en 1
```

The generator script (`scripts/generate.ts`) reads from:
- `curriculum/{lang-pair}/master-plan.json`
- `curriculum/{lang-pair}/modules-*.json`

And outputs to:
- `output/json/{lang-pair}/module-XX/` (vocab.json, lesson.json, activities.json)
- `output/html/{lang-pair}/module-XX/` (lesson.html with interactive activities)

### Adding New Modules

1. Add module data to `MODULE_DATA` in `scripts/generate.ts`
2. Run the generator: `npx ts-node scripts/generate.ts`

## Workflow

1. Edit module definitions in `curriculum/modules-*.json`
2. Edit vocabulary in `vocabulary/vocab-*.json`
3. Run generation scripts
4. Output appears in `output/` directory

## Quality Checks

When generating content, verify:
- [ ] Vocabulary count matches module target
- [ ] All vocabulary IDs exist in vocab-*.json
- [ ] Activity content uses correct schema
- [ ] Transliteration mode matches module phase
- [ ] Ukrainian instructions only appear at correct levels (B1+)
