# Module Stage 4: Review & Fix

> **⚠️ ALWAYS use `.venv/bin/python` - NEVER use `python3` or `python` directly!**

Review module, fix violations, loop until PASS.

## Usage

```
/module-stage-4 [LEVEL] [MODULE_NUM]
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `claude_extensions/stages/stage-4-review-fix.md`

### Step 2: Load Module

Read the module file:
`curriculum/l2-uk-en/{level}/{number}-*.md`

### Step 3: Run Initial Audit

```bash
.venv/bin/python scripts/audit_module.py {file_path}
```

Capture all violations.

### Step 4: Review Loop

**IF NO VIOLATIONS:** Go to Step 6 (PASS)

**IF VIOLATIONS:**

Count violations by category:
- Grammar violations (use `grammar-check` skill for verification)
- Vocabulary violations
- Activity syntax issues
- Richness failures
- Linguistic purity issues

**Use architect skills for fix guidance:**

| Module Type | Skill for Fixes |
|-------------|-----------------|
| Grammar (B1-B2) | `grammar-module-architect` |
| Vocabulary (B1) | `vocab-module-architect` |
| Cultural (B1-C1) | `cultural-module-architect` |
| History/Biography (B2-C1) | `history-module-architect` |
| Integration (B1-B2) | `integration-module-architect` |
| Checkpoint (All) | `checkpoint` |
| Literature (LIT) | `literature-module-architect` |

**Decision Matrix:**

| Violations | Action |
|------------|--------|
| ≤3 total | Fix individually |
| >3 in content | Rebuild content (Stage 2) |
| >3 in activities | Rebuild activities (Stage 3) |
| >10 OR structural | Rebuild from Stage 1 |

### Step 5: Apply Fixes or Rebuild

**For individual fixes:**
- Edit the specific lines
- Re-run audit
- Loop back to Step 4

**For section rebuild:**
- Call appropriate stage command
- Then return to this stage

**Maximum 3 iterations.** If still failing:
- Report persistent issues
- Ask user for guidance

### Step 6: PASS - Run Full Pipeline

When audit passes, run the full validation pipeline:

```bash
# Full pipeline: lint → generate MDX → validate MDX → validate HTML
npm run pipeline l2-uk-en {level} {module_num}

# Also generate JSON for Vibe app
npm run generate:json l2-uk-en {level} {module_num}
```

**Note:** HTML validation requires dev server running:
```bash
cd docusaurus && npm start  # In separate terminal
```

If pipeline fails at any step, fix the issue and re-run.

### Output

**On PASS:**
```
MODULE APPROVED

Audit: PASS
Pipeline: PASS (lint ✓ generate ✓ validate_mdx ✓ validate_html ✓)
MDX: docusaurus/docs/{level}/module-{num}.mdx
JSON: output/json/l2-uk-en/{level}/module-{num}.json

Statistics:
- Word count: XXX
- Activities: XX
- Vocabulary: XX words
- Interactive elements: XX
```

**On FAIL (after 3 iterations):**
```
MODULE NEEDS MANUAL REVIEW

Persistent issues:
1. [issue]
2. [issue]

Recommendation: [rebuild from stage X / manual edit / user decision]
```
