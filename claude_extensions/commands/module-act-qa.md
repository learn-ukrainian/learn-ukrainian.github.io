# /module-act-qa

Validate activities against plan requirements.

> **🤝 COLLABORATION RULE:** Fix issues yourself. Ask the other agent for help (research, facts, validation) when stuck. Never guess or hallucinate - collaboration is faster than guessing wrong.

## Usage

```
/module-act-qa {level} {module_num}
```

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Phase Instructions

Read: `claude_extensions/phases/module-act-qa.md`

### Step 2: Load Files

> **Architecture v2.0:** Read activity types from plan.

**For tracks (b2-hist, c1-bio, lit, c1-hist, b2-pro):**

1. Look up slug from manifest:
   ```bash
   yq ".levels.\"{level}\".modules[{module_num-1}]" curriculum/l2-uk-en/curriculum.yaml
   ```

2. Load files:
   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml       # Plan (activity_hints)
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml       # Meta (naturalness)
   curriculum/l2-uk-en/{level}/activities/{slug}.yaml # Activities to validate
   ```

**For core levels (a1, a2, b1, b2, c1, c2):**

1. Determine slug from module number

2. Load files:
   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   curriculum/l2-uk-en/{level}/activities/{slug}.yaml
   ```

### Step 3: Run Validation

Validate against plan's `activity_hints`:

1. **Activity count** - Within min/max range for level
2. **Type coverage** - All required types present
3. **Item density** - Each activity has minimum items
4. **Schema compliance** - Valid YAML structure
5. **No mirroring** - Activities don't copy lesson verbatim

### Step 4: Update Status Cache

Run audit to update status cache:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

### Step 5: Output

**On PASS:**
```
ACT-QA: PASS

✓ Activity count: {count} (range: {min}-{max})
✓ Type coverage: {types_used}/{types_required}
✓ Item density: All activities ≥ minimum
✓ Schema: Valid YAML
✓ No mirroring detected

ACTIVITIES LOCKED. Proceed to: /module-vocab {level} {module_num}
```

**On FAIL:**
```
ACT-QA: FAIL

Violations:
1. [CHECK]: {issue}
2. [CHECK]: {issue}

Fix activities.yaml and re-run: /module-act-qa {level} {module_num}
```
