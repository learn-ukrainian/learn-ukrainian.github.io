# Module Stage 1: Skeleton

Create the module skeleton with frontmatter, headers, and vocabulary.

## Usage

```
/module-stage-1 [LEVEL] [MODULE_NUM]
/module-stage-1 [LEVEL] [START]-[END]   # Batch mode
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)
- Batch ranges supported: `b1 2-5` processes modules 2, 3, 4, 5

---

## Batch Mode (Multiple Modules)

**When arguments contain a range (e.g., `b1 2-5`):**

Use the **subagent pattern** to process each module with fresh context:

```
For each module in range:
  1. Spawn Task agent with subagent_type="general-purpose"
  2. Agent prompt: "Run /module-stage-1 {level} {module_num}"
  3. Wait for agent completion
  4. Log result (PASS/FAIL)
  5. Continue to next module (fresh context)
```

---

## Single Module Mode

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Read Stage Instructions

Read: `claude_extensions/stages/stage-1-skeleton.md`

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

### Step 2b: Read Appropriate Template

**MANDATORY:** Read the template for this module type.

**For B1 modules:**
- Metalanguage (M01-05: Grammar terms in Ukrainian) → `docs/l2-uk-en/templates/b1-metalanguage-module-template.md`
- Grammar (M06-51: Aspect, Motion, Complex Sentences, Advanced Grammar) → `docs/l2-uk-en/templates/b1-grammar-module-template.md`
- Checkpoint (M15, M25, M34, M41, M51 — grammar phases only) → `docs/l2-uk-en/templates/b1-checkpoint-module-template.md`
- Vocabulary (M52-71: Abstract concepts, Opinions, Discourse markers) → `docs/l2-uk-en/templates/b1-vocab-module-template.md`
- Cultural (M72-81: Regions, Music, Cinema, Tech, Sports, Cuisine) → `docs/l2-uk-en/templates/b1-cultural-module-template.md`
- Integration (M82-86: Skills, Grammar/Vocab review, Capstone) → `docs/l2-uk-en/templates/b1-integration-module-template.md`

**For other levels:** Check curriculum plan for template references (B2+, C1+, C2+ templates will be available in Phase 3).

The template provides:
- Required structural sections
- Common pitfalls to avoid
- Pre-submission checklist
- Audit validation examples

### Step 2c: Use Module Architect Skill (Recommended)

For focus-area guidance beyond the template, use the appropriate architect skill:

| Module Type | Skill |
|-------------|-------|
| Grammar (B1-B2) | `grammar-module-architect` |
| Vocabulary (B1) | `vocab-module-architect` |
| Cultural (B1-C1) | `cultural-module-architect` |
| History/Biography (B2-C1) | `history-module-architect` |
| Integration (B1-B2) | `integration-module-architect` |
| Checkpoint (All) | `checkpoint` |
| Literature (LIT) | `literature-module-architect` |

These skills provide pedagogical guidance, activity priorities, and common mistakes to avoid.

### Step 2d: Detect Checkpoint

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
