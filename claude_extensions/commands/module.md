# Module Management Command

Review, fix, or create Ukrainian curriculum modules using the module-architect skill.

## Usage

```
/module review [LEVEL] [MODULE_NUMBER]
/module fix [LEVEL] [MODULE_NUMBER]
/module create [LEVEL] [MODULE_NUMBER] [TITLE]
```

## Arguments

- `$ARGUMENTS` - The task mode and parameters

## Instructions

**This command uses the `module-architect` skill.** Invoke it first, then execute the task.

Parse the user's arguments: $ARGUMENTS

### Step 1: Locate the Module

Based on level and number, find the file:
- A1: `curriculum/l2-uk-en/a1/XX-*.md` (modules 01-30)
- A2: `curriculum/l2-uk-en/a2/XX-*.md` (modules 01-50)
- B1: `curriculum/l2-uk-en/b1/XX-*.md` (modules 01-80)
- B2: `curriculum/l2-uk-en/b2/XX-*.md` (modules 01-125)
- C1: `curriculum/l2-uk-en/c1/XX-*.md` (modules 01-115)
- C2: `curriculum/l2-uk-en/c2/XX-*.md` (modules 01-80)

### Step 2: Read Reference Documents

**CRITICAL: Read ALL of these before any task:**

1. `docs/l2-uk-en/module-architect-prompt.md` - Workflow, grammar constraints, fix strategies
2. `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES.md` - Activity counts, complexity, engagement boxes
3. `docs/MARKDOWN-FORMAT.md` - Activity syntax, vocabulary format
4. `docs/l2-uk-en/ACTIVITY-GUIDELINES.md` - Templates, examples, common mistakes
5. `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` - Vocabulary lists, grammar scope

### Step 3: Execute Task

**review**: Analyze module against all constraints, output review report
**fix**: Review first, then apply fixes, verify no new violations
**create**: Copy vocabulary from curriculum plan, write module, verify all words in scope

### Step 4: Output

Use the review report format from the module-architect skill.

## Examples

```
/module review a1 11
/module fix a1 15
/module create a2 31 "The Dative I"
```
