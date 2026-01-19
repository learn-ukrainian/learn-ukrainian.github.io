# Module Management Command

> **Unified entry point** - auto-detects what to do based on module state.

## Usage

```
/module [LEVEL] [NUM]                # Auto-detect action
/module [LEVEL] [NUM] --review       # Review only (no fixes)
/module [LEVEL] [NUM] --fix          # Stage 4 only
/module [LEVEL] [NUM] --stage=N      # Force specific stage (1-4)
/module [LEVEL] [START]-[END]        # Batch mode
```

## Arguments

- `$ARGUMENTS` - Level, module number, and optional flags

## Examples

```
/module c1-bio 5           # Auto-detect and run
/module b1 22 --fix        # Just run Stage 4
/module a2 10-15           # Batch create/fix modules 10-15
/module b2 45 --stage=2    # Force Stage 2 (content)
/module c1-bio 5 --review  # Review without fixing
```

---

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Parse Input

Extract from arguments:
- `level`: The level code (a1, a2, b1, b2, c1, c2, b2-hist, c1-bio, c1-hist, lit)
- `num`: Module number (or range like `10-15`)
- `flags`: --review, --fix, --stage=N (optional)

**If batch range detected (e.g., `10-15`):** Jump to Batch Mode section.

### Step 2: Resolve Module Path

**For core levels (a1, a2, b1, b2, c1, c2):**
```bash
ls curriculum/l2-uk-en/{level}/{num:02d}-*.md 2>/dev/null
```

**For track levels (b2-hist, c1-bio, c1-hist, lit):**
```bash
slug=$(yq ".levels.\"{level}\".modules[{num-1}]" curriculum/l2-uk-en/curriculum.yaml)
ls curriculum/l2-uk-en/{level}/{slug}.md 2>/dev/null
```

Store: `module_path`, `slug`, `meta_path`, `activities_path`, `vocab_path`

### Step 3: Detect Module State

Check what exists:

```bash
# Check each file
test -f curriculum/l2-uk-en/{level}/meta/{slug}.yaml      # has_meta
test -f curriculum/l2-uk-en/{level}/{slug}.md             # has_content
test -f curriculum/l2-uk-en/{level}/activities/{slug}.yaml # has_activities

# If has_content, check if it's just skeleton or has real content
wc -w < {module_path}  # word_count
```

**State detection:**

| has_meta | has_content | has_activities | word_count | State |
|----------|-------------|----------------|------------|-------|
| No | No | No | - | `NEW` |
| Yes | No | No | - | `SKELETON_NEEDED` |
| Yes | Yes | No | < 500 | `SKELETON_ONLY` |
| Yes | Yes | No | >= 500 | `CONTENT_DONE` |
| Yes | Yes | Yes | - | `COMPLETE` |

### Step 4: Determine Action

**If flag provided, use it:**

| Flag | Action |
|------|--------|
| `--review` | Run audit only, report results, don't fix |
| `--fix` | Run Stage 4 |
| `--stage=1` | Run Stage 1 |
| `--stage=2` | Run Stage 2 |
| `--stage=3` | Run Stage 3 |
| `--stage=4` | Run Stage 4 |

**If no flag, auto-detect from state:**

| State | Action |
|-------|--------|
| `NEW` | Run Stages 1 → 2 → 3 → 4 |
| `SKELETON_NEEDED` | Run Stages 1 → 2 → 3 → 4 |
| `SKELETON_ONLY` | Run Stages 2 → 3 → 4 |
| `CONTENT_DONE` | Run Stages 3 → 4 |
| `COMPLETE` | Run audit; if PASS → done; if FAIL → Stage 4 |

### Step 5: Execute

**Delegate to existing stage commands.** Do NOT duplicate their logic.

For each stage to run:
1. Report: "Running Stage N..."
2. Follow instructions from `/module-stage-N`
3. If stage fails, stop and report

**Stage execution order:**
```
Stage 1 (skeleton) → Stage 2 (content) → Stage 3 (activities) → Stage 4 (review/fix)
```

### Step 6: Report

On completion:
```
Module: {level}/{slug}
State: {final_state}
Stages run: {list}
Audit: PASS/FAIL
MDX: docusaurus/docs/{level}/module-{num}.mdx (if generated)
```

---

## Batch Mode

**When input contains a range (e.g., `b1 10-15`):**

Use subagent pattern for context isolation:

```
For each module_num in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Prompt: "Run /module {level} {module_num} {flags}"
  3. Wait for completion
  4. Log result
  5. Continue to next
```

**Output summary:**
```
Batch: {level} {start}-{end}
Results:
  - {num}: PASS
  - {num}: PASS
  - {num}: FAIL (Stage 3 - activity count)
  - {num}: PASS

Summary: 3/4 passed
```

---

## Quick Reference

**Levels and paths:**

| Level | Path Pattern | Type |
|-------|--------------|------|
| a1, a2, b1, b2, c1, c2 | `{num:02d}-{slug}.md` | Core |
| b2-hist, c1-bio, c1-hist, lit | `{slug}.md` | Track (seminar) |

**Track detection:**
If level is `b2-hist`, `c1-bio`, `c1-hist`, or `lit` → seminar track → uses slug-based paths.

**Stage commands (for reference):**
- `/module-stage-1` - Skeleton creation
- `/module-stage-2` - Content generation
- `/module-stage-3` - Activity generation
- `/module-stage-4` - Review and fix loop
