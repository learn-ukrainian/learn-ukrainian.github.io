---
name: checkpoint
description: Use this skill when creating or reviewing checkpoint modules. Checkpoints are phase-end assessments that test all skill groups from preceding modules using TTT pedagogy.
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

> **PERSONA:** Embody the Ukrainian linguist & historian. See `claude_extensions/skills/_shared/persona.md`

# Checkpoint Module Skill

Create or review checkpoint modules using the appropriate level-specific template.

## Usage

```
/checkpoint [LEVEL] [MODULE_NUM]
/checkpoint b1 15
/checkpoint b2 10
/checkpoint review b1 15
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `b1 15`, `c1 20`)
- Optional `review` prefix to review existing checkpoint

## Checkpoint Locations by Level

| Level | Checkpoints | Template |
|-------|-------------|----------|
| A1 | M10, M20, M34 | (A1 uses different format) |
| A2 | M11, M24, M34, M43, M55 | (A2 uses different format) |
| **B1** | **M15, M25, M34, M41, M51** | `docs/l2-uk-en/templates/b1-checkpoint-module-template.md` |
| **B2** | **M10, M25, M40, M70, M95, M110** | `docs/l2-uk-en/templates/b2-checkpoint-module-template.md` |
| **C1** | **M20, M35, M100, M120, M145, M160** | `docs/l2-uk-en/templates/c1-checkpoint-module-template.md` |
| **C2** | **M20, M25, M40, M55, M75, M100** | `docs/l2-uk-en/templates/c2-checkpoint-module-template.md` |

## Instructions

Parse arguments: $ARGUMENTS

### Step 1: Validate Checkpoint

1. Extract LEVEL and MODULE_NUM from arguments
2. Verify MODULE_NUM is a valid checkpoint for this level (see table above)
3. If not a checkpoint module, STOP and inform user

### Step 2: Read the Template

**MANDATORY:** Read the checkpoint template for this level:

```
docs/l2-uk-en/templates/{level}-checkpoint-module-template.md
```

The template contains:
- **Required Skill Groups** - What each checkpoint must test
- **Skill Tables** - Specific abilities learners must demonstrate
- **Activity Requirements** - 16+ activities, skill-targeted design
- **Self-Assessment** - "Чи можете ви..." checklist format

### Step 3: Extract Skill Groups

From the template, find the skill groups for this specific checkpoint module.

Example for B1 M15 (Aspect Mastery):
| Skill Group | Source | What Learner Can Do |
|-------------|--------|---------------------|
| Aspect in Past | M06-07 | Choose correct aspect for completed vs ongoing |
| Aspect in Future | M08-09 | Distinguish буду + infinitive vs perfective |
| ... | ... | ... |

### Step 4: Create or Review

**If CREATING:**
1. Follow Stage 1-4 workflow using checkpoint template
2. Ensure TTT pedagogy (Test-Teach-Test)
3. Create activities targeting EACH skill group
4. Include self-assessment checklist

**If REVIEWING:**
1. Check template compliance
2. Verify all skill groups are tested
3. Verify 16+ activities
4. Verify 100% Ukrainian immersion
5. Run audit: `.venv/bin/python scripts/audit_module.py {file_path}`

### Step 5: Checkpoint-Specific Validation

- [ ] **Pedagogy:** TTT (Test-Teach-Test)
- [ ] **Word count:** 1200+ words
- [ ] **Vocabulary:** 30-40 items (review from ALL modules in phase)
- [ ] **Activities:** 16+ (more than regular modules)
- [ ] **Skill coverage:** Every skill group has dedicated activity
- [ ] **Self-assessment:** "Чи можете ви..." checklist present
- [ ] **Immersion:** 100% Ukrainian (English only in vocab translations)
- [ ] **No new content:** Checkpoints ONLY review existing knowledge

## Common Mistakes

1. **Teaching new content** - Checkpoints review, not teach
2. **Missing skill groups** - Must test ALL modules in phase
3. **Too few activities** - Need 16+, not 12
4. **Generic activities** - Each activity must target specific skill group
5. **Missing self-assessment** - Required at end

## Output

Report:
- Checkpoint level and number
- Phase being assessed
- Skill groups covered
- Activity count and types
- Validation status
