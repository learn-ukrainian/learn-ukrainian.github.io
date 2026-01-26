# /module-meta

Initialize module metadata from existing plan.

## Usage

```
/module-meta {level} {module_num}
```

## Architecture v2.0 Note

> **Plans are now separate and immutable.**
>
> - **Plan** (`plans/{level}/{slug}.yaml`): Created separately, contains content_outline, word_target, objectives
> - **Meta** (`{level}/meta/{slug}.yaml`): Mutable build config - naturalness, version, timestamps
>
> This command initializes meta.yaml from an existing plan. It does NOT create plans.

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Phase Instructions

Read: `claude_extensions/phases/module-meta.md`

### Step 2: Load Plan

**For tracks (b2-hist, c1-bio, lit, c1-hist):**

1. Look up slug from manifest:
   ```bash
   yq ".levels.\"{level}\".modules[{module_num-1}]" curriculum/l2-uk-en/curriculum.yaml
   ```

2. Load plan file:
   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml
   ```

**For core levels (a1, a2, b1, b2, c1, c2):**

1. Determine slug from module number

2. Load plan file:
   ```
   curriculum/l2-uk-en/plans/{level}/{slug}.yaml
   ```

If plan doesn't exist, STOP:
```
ERROR: Plan not found for {level}/{slug}

Plans must be created separately. Check:
  curriculum/l2-uk-en/plans/{level}/{slug}.yaml
```

### Step 3: Create Meta YAML

Initialize meta.yaml with mutable fields:

```yaml
module: {from plan}
level: {from plan}
slug: {from plan}
version: "2.0"
naturalness:
  score: null
  status: PENDING
build:
  last_modified: {today's date}
```

Write to: `curriculum/l2-uk-en/{level}/meta/{slug}.yaml`

### Step 4: Output

```
META INITIALIZED: curriculum/l2-uk-en/{level}/meta/{slug}.yaml

Plan: curriculum/l2-uk-en/plans/{level}/{slug}.yaml
  - Word target: {word_target}
  - Sections: {section_count}
  - Focus: {focus}

Next: Run /module-lesson {level} {module_num}
```

## Related Commands

| Command | Purpose |
|---------|---------|
| `/module-meta-qa` | Validate meta.yaml |
| `/module-lesson` | Generate lesson from plan |
