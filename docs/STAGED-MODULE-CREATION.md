# Staged Module Creation System

A 4-stage pipeline for creating curriculum modules with review/fix loops.

## Why Stages?

1. **Token efficiency**: Each stage loads only what it needs
2. **File-as-memory**: The module file persists state between stages
3. **Incremental review**: Catch issues early, fix before moving forward
4. **Scalability**: Works for all levels (A1-C2) with different complexity

## Pipeline Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   STAGE 1       │     │   STAGE 2       │     │   STAGE 3       │     │   STAGE 4       │
│   Skeleton      │ ──▶ │   Content       │ ──▶ │   Activities    │ ──▶ │   Review/Fix    │
│                 │     │                 │     │                 │     │                 │
│ • Frontmatter   │     │ • Narratives    │     │ • 8-16 acts     │     │ • Audit         │
│ • Headers       │     │ • Examples      │     │ • Vocabulary    │     │ • Fix/Rebuild   │
│ • Vocabulary    │     │ • Dialogues     │     │ • Sequencing    │     │ • Loop → PASS   │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                                                │
                                                                                ▼
                                                                        ┌─────────────────┐
                                                                        │    APPROVED     │
                                                                        │ • MDX output    │
                                                                        │ • JSON output   │
                                                                        └─────────────────┘
```

## Usage

### Full Pipeline (Recommended)

```bash
/module-create a1 15
```

Creates module 15 for A1 level, running all 4 stages automatically.

### Individual Stages

For manual control or resuming work:

```bash
/module-stage-1 a1 15    # Create skeleton with vocabulary
/module-stage-2 a1 15    # Fill in content
/module-stage-3 a1 15    # Generate activities
/module-stage-4 a1 15    # Review and fix until PASS
```

## Stage Details

### Stage 1: Skeleton

**Input**: Curriculum plan section for the module

**Creates**:
- YAML frontmatter (module, title, pedagogy, objectives)
- Section headers based on pedagogy (PPP/TTT/CLIL)
- Vocabulary table copied EXACTLY from plan
- `[placeholder]` markers in each section

**Output**: `curriculum/l2-uk-en/{level}/{num}-{slug}.md`

### Stage 2: Content

**Input**: Skeleton from Stage 1

**Creates**:
- Rich instructional content
- Example sentences (12-32+ by level)
- Engagement boxes (3-8+ by level)
- Mini-dialogues (2-5+ by level)
- Grammar explanations and tables

**Constraints**:
- Word count targets (300-2000+ by level/module)
- Immersion percentages (15-100% by level)
- Uses ONLY vocabulary from table + prior modules

### Stage 3: Activities

**Input**: Content from Stage 2

**Creates**:
- 8-16+ activities (by level)
- 12-18+ items per activity
- 4-5+ activity types
- Proper sequencing (easy → hard)

**Activity Types**:
| Level | Required | Optional |
|-------|----------|----------|
| A1 | fill-in, match-up, quiz, true-false, group-sort, anagram/unjumble | - |
| A2 | fill-in, unjumble, cloze, error-correction, mark-the-words | select, translate |
| B1+ | All above + translate, select | - |

### Stage 4: Review & Fix

**Input**: Complete module from Stages 1-3

**Process**:
1. Run audit: `python3 scripts/audit_module.py {file}`
2. Count violations
3. Decision:
   - ≤3 violations → Fix individually
   - >3 in section → Rebuild section (call earlier stage)
   - >10 or structural → Rebuild from Stage 1
4. Loop until PASS (max 3 iterations)
5. Generate output:
   - MDX: `npm run generate l2-uk-en {level} {num}`
   - JSON: `npm run generate:json l2-uk-en {level} {num}`

## File Structure

```
claude_extensions/           # Git-tracked source
├── stages/
│   ├── stage-1-skeleton.md
│   ├── stage-2-content.md
│   ├── stage-3-activities.md
│   └── stage-4-review-fix.md
└── commands/
    ├── module-create.md     # Full pipeline
    ├── module-stage-1.md
    ├── module-stage-2.md
    ├── module-stage-3.md
    └── module-stage-4.md

.claude/                     # Deployed (auto-generated)
├── stages/                  # Copied from claude_extensions
├── commands/                # Copied from claude_extensions
└── skills/                  # Skills (module-architect, etc.)
```

## Deployment

The `start-claude.sh` script automatically deploys at startup.

Manual deployment:
```bash
npm run claude:deploy
```

This copies `claude_extensions/*` to `.claude/*`.

## Development Workflow

1. **Edit source files** in `claude_extensions/`
2. **Deploy** with `npm run claude:deploy`
3. **Test** by running the commands in Claude Code

Never edit `.claude/` directly - changes will be overwritten.

## Integration with Module Architect

The staged system uses the same constraints as the `module-architect` skill:
- Grammar constraints from `{LEVEL}-CURRICULUM-PLAN.md`
- Richness requirements from `MODULE-RICHNESS-GUIDELINES-v2.md`
- Format rules from `MARKDOWN-FORMAT.md`
- Linguistic purity from `LINGUISTIC-PURITY-GUIDE.md`

The difference is stages break the work into smaller, token-efficient chunks.

## Troubleshooting

### "Run Stage X first"
The module file doesn't have content from the previous stage. Run stages in order.

### Stage 4 loops forever
After 3 fix iterations, the system stops and reports persistent issues. Options:
- Rebuild from an earlier stage
- Manual intervention
- Check if constraints are too strict for this module

### Vocabulary violations
Activities can only use:
1. Words from the module's vocabulary table
2. Words from prior modules (cumulative database)
3. Common function words

If getting violations, check vocabulary.db sync:
```bash
python3 scripts/audit_module.py {file}  # Syncs vocab automatically
```

## Examples

### Create A1 Module 15
```bash
# Full pipeline
/module-create a1 15

# Or step by step
/module-stage-1 a1 15
/module-stage-2 a1 15
/module-stage-3 a1 15
/module-stage-4 a1 15
```

### Create B2 Module 45
```bash
# B2 uses Opus model (complex grammar)
/module-create b2 45
```

### Resume from Stage 3
If content is done but activities need work:
```bash
/module-stage-3 b1 30    # Regenerate activities
/module-stage-4 b1 30    # Review and approve
```
