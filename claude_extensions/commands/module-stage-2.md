# Module Stage 2: Content

Fill the skeleton with rich instructional content.

## Usage

```
/module-stage-2 [LEVEL] [MODULE_NUM]
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `.claude/stages/stage-2-content.md`

### Step 2: Load Existing Module

Read the module file created in Stage 1:
`curriculum/l2-uk-en/{level}/{number}-*.md`

If file doesn't exist or has no skeleton, STOP and report: "Run Stage 1 first."

### Step 3: Determine Targets

From the level, identify:
- Word count target
- Immersion percentage
- Example sentence minimum
- Engagement box minimum
- Mini-dialogue minimum

### Step 4: Write Content

Replace `[placeholder]` markers with rich content:

1. **Warm-up/Diagnostic**: Connect to prior knowledge, leading question
2. **Presentation/Analysis**: Grammar explanation, tables, examples
3. **Cultural Insight/Deep Dive**: History, culture, engagement boxes
4. **Practice**: Pattern drills, model exercises

Use ONLY vocabulary from:
- The module's vocabulary table
- Prior modules (cumulative)

### Step 5: Verify

- [ ] Word count meets target
- [ ] Example sentences meet minimum
- [ ] Engagement boxes meet minimum
- [ ] Mini-dialogues present
- [ ] No vocabulary violations
- [ ] Specific Ukrainian locations used
- [ ] Immersion % appropriate

### Step 6: Run Audit

```bash
python3 scripts/audit_module.py {file_path}
```

### Output

Report:
- Word count (instructional core)
- Example sentences count
- Engagement boxes count
- Immersion %
- Any violations found
- "Ready for Stage 3" or "Fix issues first"
