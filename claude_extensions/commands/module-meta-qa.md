# /module-meta-qa

Validate module metadata before locking.

> **🤝 COLLABORATION RULE:** Fix issues yourself. Ask the other agent for help (research, facts, validation) when stuck. Never guess or hallucinate - collaboration is faster than guessing wrong.

## Usage

```
/module-meta-qa {level} {module_num}
```

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Phase Instructions

Read: `claude_extensions/phases/module-meta-qa.md`

### Step 2: Load Meta YAML

**For tracks (b2-hist, c1-bio, lit):**

1. Look up slug from manifest:
   ```bash
   yq ".levels.\"{level}\".modules[{module_num-1}]" curriculum/l2-uk-en/curriculum.yaml
   ```

2. Load meta file:
   ```
   curriculum/l2-uk-en/{level}/meta/{slug}.yaml
   ```

### Step 3: Run All Checks

Follow validation checklist from phase instructions.

### Step 4: Output

**On PASS:**
```
META-QA: PASS
META LOCKED.

Next: Run /module-lesson {level} {module_num}
```

**On FAIL:**
```
META-QA: FAIL
Violations: [list]

Fix and re-run: /module-meta-qa {level} {module_num}
```
