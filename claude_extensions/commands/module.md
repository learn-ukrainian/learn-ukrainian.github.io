# Module Management Command

Review, fix, or create Ukrainian curriculum modules using the module-architect skill.

## Usage

```
/module review [LEVEL] [MODULE]
/module fix [LEVEL] [MODULE]
/module create [LEVEL] [MODULE] [TITLE]
/module help
```

## Arguments

- `$ARGUMENTS` - The task mode and parameters

## Instructions

**This command uses the `module-architect` skill.** Invoke it first, then execute the task.

Parse the user's arguments: $ARGUMENTS

**Argument formats:**
- `review a1` - Review ALL modules in level
- `review a1 15` - Review single module
- `review a1 1-10` - Review range of modules (1 through 10)
- `fix a1 15` - Fix single module
- `create a2 51 "Title"` - Create new module
- `help` - Show usage information

### Step 1: Locate the Module(s)

Based on level and number/range, find the file(s):
- A1: `curriculum/l2-uk-en/a1/XX-*.md` (modules 01-30)
- A2: `curriculum/l2-uk-en/a2/XX-*.md` (modules 01-50)
- B1: `curriculum/l2-uk-en/b1/XX-*.md` (modules 01-80)
- B2: `curriculum/l2-uk-en/b2/XX-*.md` (modules 01-125)
- C1: `curriculum/l2-uk-en/c1/XX-*.md` (modules 01-115)
- C2: `curriculum/l2-uk-en/c2/XX-*.md` (modules 01-80)

**For ranges (e.g., `1-10`):** Parse start and end numbers, process each module.

### Step 2: Read Reference Documents

**CRITICAL: Read ALL of these before any task:**

1. `docs/l2-uk-en/module-architect-prompt.md` - Workflow, grammar constraints, fix strategies
2. `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` - Activity counts, complexity, templates, engagement boxes
3. `docs/MARKDOWN-FORMAT.md` - Activity syntax, vocabulary format
4. `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` - Vocabulary lists, grammar scope

### Step 3: Execute Task

**review**: Analyze module(s) against all constraints, output review report
- For ranges/all: Use parallel Task agents (batch 5-10 modules per agent) for efficiency
- Summarize violations at end

**fix**: Review first, then apply fixes, verify no new violations

**create**: Copy vocabulary from curriculum plan, write module, verify all words in scope

### Step 4: Model Selection

Per module-architect skill:
- **A1, A2, B1**: Use Sonnet
- **B2, C1, C2**: Use Opus

### Step 5: Output

Use the review report format from the module-architect skill.

## Examples

```
/module review a1           # Review all A1 modules
/module review a1 15        # Review single module
/module review a2 1-10      # Review modules 1-10
/module review a2 11-20     # Review modules 11-20
/module fix a1 15           # Fix violations in module
/module create a2 51 "New Topic"  # Create new module
/module help                # Show usage
```
