# Module Create (Full Pipeline)

Create a complete module through all 4 stages.

## Usage

```
/module-create [LEVEL] [MODULE_NUM]
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)

## Instructions

Parse arguments: $ARGUMENTS

This command runs the full module creation pipeline:

```
Stage 1 → Stage 2 → Stage 3 → Stage 4 (review/fix loop) → OUTPUT
```

### Pipeline

**Stage 1: Skeleton**
1. Read curriculum plan
2. Extract module section (title, vocabulary, grammar scope)
3. Create file with frontmatter + headers + vocabulary table

**Stage 2: Content**
1. Load skeleton from Stage 1
2. Write rich instructional content
3. Verify word count, examples, engagement boxes

**Stage 3: Activities**
1. Load content from Stage 2
2. Generate activities using vocabulary
3. Verify counts, types, syntax

**Stage 4: Review & Fix**
1. Run audit
2. Fix violations (or rebuild sections)
3. Loop until PASS
4. Generate MDX and JSON output

### Quick Reference (Read First)

1. **Quick-ref for level:** `claude_extensions/quick-ref/{level}.md` (~100 lines)
   - Frontmatter template, targets, activity mix, pre-flight checklist
2. **Philosophy guide:** `claude_extensions/quick-ref/philosophy.md` (~150 lines)
   - Soul standard, Truth standard, cultural specificity, linguistic purity

### Curriculum Plan (Extract Only Your Module)

**DO NOT read the entire curriculum plan file.** Use grep to extract only your module:

```bash
grep -A 50 "Module {NUM}:" docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md
```

This gives you ONLY the vocabulary and grammar scope for your specific module (~50 lines).

### Pre-flight Checklist

Before writing, confirm from quick-ref:
- [ ] All frontmatter fields ready (copy template)
- [ ] Vocabulary list from curriculum plan
- [ ] Activity count + types match level requirements
- [ ] Immersion target known
- [ ] No duplicate explanations planned

### Stage Instructions (if needed)

Only read stage docs for complex cases:
- `.claude/stages/stage-1-skeleton.md`
- `.claude/stages/stage-2-content.md`
- `.claude/stages/stage-3-activities.md`
- `.claude/stages/stage-4-review-fix.md`

### Output

On completion:
- Module file: `curriculum/l2-uk-en/{level}/{num}-{slug}.md`
- MDX: `docusaurus/docs/{level}/module-{num}.mdx`
- JSON: `output/json/l2-uk-en/{level}/module-{num}.json`

Status: APPROVED or NEEDS MANUAL REVIEW

## Individual Stage Commands

For manual control, use individual stage commands:

```
/module-stage-1 [LEVEL] [MODULE]   # Create skeleton
/module-stage-2 [LEVEL] [MODULE]   # Fill content
/module-stage-3 [LEVEL] [MODULE]   # Add activities
/module-stage-4 [LEVEL] [MODULE]   # Review & fix loop
```

## Examples

```
/module-create a1 15      # Create A1 module 15 (full pipeline)
/module-create b2 45      # Create B2 module 45 (full pipeline)

# Or step by step:
/module-stage-1 a1 15     # Create skeleton
/module-stage-2 a1 15     # Add content
/module-stage-3 a1 15     # Add activities
/module-stage-4 a1 15     # Review and fix until pass
```
