# Module Create (Full Pipeline)

Create a complete module through all 4 stages.

## Usage

```
/module-create [LEVEL] [MODULE_NUM]
```

## Arguments

- `$ARGUMENTS` - Level and module number (e.g., `a1 15` or `b2 45`)

## 🚀 Fast Path (Gemini / Limited Context)
**Action:** Run the full pipeline in one sequence.
1. **Analyze:** Read `docs/l2-uk-en/{LEVEL}-CURRICULUM-PLAN.md` (grep module) & **appropriate template** from `docs/l2-uk-en/templates/`.
2. **Draft:** Create module file with full content **following template structure**.
3. **Audit:** `python3 scripts/audit_module.py ...`
4. **Fix:** Loop until PASS.
5. **Review:** `/review-content l2-uk-en {LEVEL} {MODULE_NUM}` (Quality Gate: 5/5).
6. **Finalize:** `npm run pipeline l2-uk-en {LEVEL} {MODULE_NUM}` && `npm run generate:json l2-uk-en {LEVEL} {MODULE_NUM}`

---

## Instructions

Parse arguments: $ARGUMENTS

This command runs the full module creation pipeline:

```
Stage 1 → Stage 2 → Stage 3 → Stage 4 (review/fix loop) → OUTPUT
```

### Pipeline

**Stage 1: Skeleton**
1. Read curriculum plan
2. **Read appropriate template** (see template selection in `/module-stage-1`)
3. Extract module section (title, vocabulary, grammar scope)
4. Create file with frontmatter + headers + vocabulary table **following template structure**

**Stage 2: Content**
1. Load skeleton from Stage 1
2. Write rich instructional content
3. Verify word count, examples, engagement boxes

**Stage 3: Activities**
1. Load content from Stage 2
2. Generate activities using vocabulary
3. Verify counts, types, syntax

**Stage 4: Review & Fix**
1. Run audit: `python3 scripts/audit_module.py curriculum/l2-uk-en/{LEVEL}/module-{MODULE_NUM}.md`
2. Fix violations until PASS
3. Run content review: `/review-content l2-uk-en {LEVEL} {MODULE_NUM}`
4. Fix quality issues until PASS (Score: 5/5)
5. Run pipeline: `npm run pipeline l2-uk-en {LEVEL} {MODULE_NUM}`
6. Generate JSON: `npm run generate:json l2-uk-en {LEVEL} {MODULE_NUM}`

### Quick Reference (Read First)

1. **Quick-ref for level:** `claude_extensions/quick-ref/{level}.md` (~100 lines)
   - Frontmatter template, targets, activity mix, pre-flight checklist
2. **Philosophy guide:** `claude_extensions/quick-ref/philosophy.md` (~150 lines)
   - Soul standard, Truth standard, cultural specificity, linguistic purity

### Module Architect Skills (Use for Focus-Area Guidance)

Select the appropriate architect skill based on module type:

| Module Type | Skill | When to Use |
|-------------|-------|-------------|
| Grammar (B1-B2) | `grammar-module-architect` | Aspect, motion verbs, participles, passive voice |
| Vocabulary (B1) | `vocab-module-architect` | Abstract concepts, collocations, synonymy |
| Cultural (B1-C1) | `cultural-module-architect` | Regions, music, cinema, folk culture |
| History/Biography (B2-C1) | `history-module-architect` | Ukrainian history, historical figures |
| Integration (B1-B2) | `integration-module-architect` | Level-end review and consolidation |
| Checkpoint (All) | `checkpoint` | Phase-end assessment modules |
| Literature (LIT) | `literature-module-architect` | Post-C1 Ukrainian literature track |

These skills provide focus-area pedagogical guidance beyond the template structure.

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
- [ ] External Resources (YouTube/Blogs) planned?
- [ ] **If checkpoint:** Read `docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md`

### Stage Instructions (if needed)

Only read stage docs for complex cases:
- `claude_extensions/stages/stage-1-skeleton.md`
- `claude_extensions/stages/stage-2-content.md`
- `claude_extensions/stages/stage-3-activities.md`
- `claude_extensions/stages/stage-4-review-fix.md`

### Output

On completion:
- Module file: `curriculum/l2-uk-en/{level}/{num}-{slug}.md`
- MDX: `docusaurus/docs/{level}/module-{num}.mdx`
- JSON: `output/json/l2-uk-en/{level}/module-{num}.json`

Status: APPROVED (pipeline passes) or NEEDS MANUAL REVIEW

**Pipeline validates:**
- Lint (MD format)
- Generate (MD → MDX)
- Validate MDX (no content loss)
- Validate HTML (browser rendering)

**Note:** HTML validation requires `cd docusaurus && npm start` running

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
