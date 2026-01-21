# /module-meta

Create module metadata sidecar.

## Usage

```
/module-meta {level} {module_num}
```

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Phase Instructions

Read: `claude_extensions/phases/module-meta.md`

### Step 2: Load Curriculum Plan

**For tracks (b2-hist, c1-bio, lit):**
```
docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md
```

Look up module by position in the plan.

### Step 3: Create Meta YAML

Write to: `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`

Follow schema from phase instructions exactly.

### Step 4: Output

```
META CREATED: curriculum/l2-uk-en/{level}/meta/{slug}.yaml

Next: Run /module-meta-qa {level} {module_num}
```
