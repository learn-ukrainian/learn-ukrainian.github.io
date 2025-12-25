# Module Stage 3: Activities

Generate activities based on the module content.

## Usage

```
/module-stage-3 [LEVEL] [MODULE_NUM]
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `.claude/stages/stage-3-activities.md`

### Step 2: Load Module

Read the module file:
`curriculum/l2-uk-en/{level}/{number}-*.md`

Verify content is present (not just `[placeholder]` markers).
If content incomplete, STOP and report: "Run Stage 2 first."

### Step 3: Extract Vocabulary

From the module's vocabulary table and prior modules, build the allowed word list.

### Step 4: Determine Requirements

From the level:
- Activity count minimum
- Items per activity minimum
- Required activity types
- Sequencing rules

**Use the appropriate architect skill** for activity priorities:

| Module Type | Skill | Activity Focus |
|-------------|-------|----------------|
| Grammar (B1-B2) | `grammar-module-architect` | fill-in, error-correction, cloze |
| Vocabulary (B1) | `vocab-module-architect` | match-up, group-sort, select |
| Cultural (B1-C1) | `cultural-module-architect` | quiz, true-false, cloze |
| History/Biography (B2-C1) | `history-module-architect` | comprehension, primary source analysis |
| Integration (B1-B2) | `integration-module-architect` | comprehensive review activities |
| Checkpoint (All) | `checkpoint` | 16+ skill-targeted activities |
| Literature (LIT) | `literature-module-architect` | essays, deep reading (no drills) |

### Step 5: Write Activities Section

Add `# Activities` section with:

1. **Recognition stage**: match-up, group-sort, mark-the-words
2. **Discrimination stage**: quiz, true-false, select
3. **Controlled stage**: fill-in, cloze, error-correction
4. **Production stage**: unjumble, dialogue-reorder, translate

Use ONLY vocabulary from:
- The module's vocabulary table
- Prior modules (cumulative)

### Step 6: Verify Syntax

- [ ] Fill-in uses `___` (three underscores)
- [ ] Fill-in has `> [!options]` and `> [!answer]` blocks
- [ ] Unjumble uses ` / ` separators
- [ ] Anagram uses spaces (A1 M01-10 only)
- [ ] Match-up uses `::` separator
- [ ] Quiz uses `- [ ]` and `- [x]` checkboxes

### Step 7: Run Audit

```bash
python3 scripts/audit_module.py {file_path}
```

### Step 8: Generate Output

```bash
npm run generate l2-uk-en {level} {module_num}
npm run generate:json l2-uk-en {level} {module_num}
```

### Output

Report:
- Activity count
- Activity types used
- Items per activity (min/max)
- Vocabulary violations (if any)
- Audit result
- "Module complete" or "Fix issues"
