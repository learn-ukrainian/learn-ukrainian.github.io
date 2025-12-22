# Module Stage 1: Skeleton

Create the module skeleton with frontmatter, headers, and vocabulary.

## Usage

```
/module-stage-1 [LEVEL] [MODULE_NUM]
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `.claude/stages/stage-1-skeleton.md`

### Step 2: Extract Module Plan

Read the curriculum plan for this level:
- `docs/l2-uk-en/A1-CURRICULUM-PLAN.md`
- `docs/l2-uk-en/A2-CURRICULUM-PLAN.md`
- `docs/l2-uk-en/B1-CURRICULUM-PLAN.md`
- `docs/l2-uk-en/B2-CURRICULUM-PLAN.md`
- `docs/l2-uk-en/C1-CURRICULUM-PLAN.md`
- `docs/l2-uk-en/C2-CURRICULUM-PLAN.md`

Find the section for the target module (search for `## Module {number}` or `### M{number}`).

Extract:
- Title
- Vocabulary list
- Grammar scope
- Objectives (if listed)

### Step 2b: Detect Checkpoint

Check if module is a checkpoint:
- Curriculum plan says "Checkpoint"
- Module number matches checkpoint pattern (e.g., M10, M20, M30...)
- Filename contains "checkpoint"

**If checkpoint**, follow A1 checkpoint format (`a1/10-checkpoint-first-contact.md`):

```markdown
# Checkpoint - [Name]

Intro with skills list.

## Skill 1: [Name]
### Model: [Title]
> Example content

### Practice: [Title]
Exercise items

### Self-Check
- Bullet list of questions

---

## Skill 2: [Name]
(repeat Model/Practice/Self-Check)

## Activities
(10+ activities)

## Vocabulary
(10+ words)
```

**Key requirements:**
- `# Checkpoint` H1 header (not `## Overview`)
- `## Skill N:` H2 headers
- `### Model:`, `### Practice:`, `### Self-Check` H3 headers
- Audit validates this format automatically

### Step 3: Create Skeleton

Create the file at: `curriculum/l2-uk-en/{level}/{number}-{slug}.md`

Following the stage-1 template:
1. YAML frontmatter with all required fields
2. Section headers matching pedagogy (PPP for A1-A2, TTT/CLIL for B1+)
3. `[placeholder]` markers in each section
4. Vocabulary table copied EXACTLY from the plan

### Step 4: Verify

- [ ] File created at correct path
- [ ] Frontmatter complete
- [ ] All section headers present
- [ ] Vocabulary copied exactly (no additions)

### Output

Report:
- File path created
- Module title
- Pedagogy type
- Vocabulary count
- "Ready for Stage 2"
