# /module-vocab-qa

Validate vocabulary against plan requirements.

> **🤝 COLLABORATION RULE:** Fix issues yourself. Ask the other agent for help (research, facts, validation) when stuck. Never guess or hallucinate - collaboration is faster than guessing wrong.

## Usage

```
/module-vocab-qa {level} {module_num}
```

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Phase Instructions

Read: `claude_extensions/phases/module-vocab-qa.md`

### Step 2: Load Files

> **Architecture v2.0:** Read vocabulary scope from plan.

**For tracks (b2-hist, c1-bio, lit, c1-hist, b2-pro):**

1. Look up slug from manifest:
   ```bash
   yq ".levels.\"{level}\".modules[{module_num-1}]" curriculum/l2-uk-en/curriculum.yaml
   ```

2. Load files:
   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml       # Plan (vocabulary_hints)
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml       # Meta
   curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml # Vocabulary to validate
   ```

**For core levels (a1, a2, b1, b2, c1, c2):**

1. Determine slug from module number

2. Load files:
   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   curriculum/l2-uk-en/{level}/vocabulary/{slug}.yaml
   ```

### Step 3: Run Validation

Validate against plan's `vocabulary_hints` and level requirements:

1. **Word count** - Meets minimum for level (20+ for B1+)
2. **Required vocab present** - All plan-specified words included
3. **IPA transcription** - All entries have pronunciation
4. **Part of speech** - Valid POS tags
5. **No duplicates** - Each word unique
6. **Translations** - English translations present

### Step 4: Update Status Cache

Run audit to update status cache:

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{level}/{slug}.md
```

### Step 5: Output

**On PASS:**
```
VOCAB-QA: PASS

✓ Word count: {count} (minimum: {min})
✓ Required vocabulary: All present
✓ IPA transcription: Complete
✓ Part of speech: Valid tags
✓ No duplicates

VOCABULARY LOCKED. Module complete!
Run: /module-fix {level} {module_num} for final validation
```

**On FAIL:**
```
VOCAB-QA: FAIL

Violations:
1. [CHECK]: {issue}
2. [CHECK]: {issue}

Fix vocabulary.yaml and re-run: /module-vocab-qa {level} {module_num}
```
