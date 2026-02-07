# A1 Full Rebuild - Continuation Prompt

## Current Status Summary

**Branch:** `copilot/a1-rebuild-clean` (on remote: b5495740c)
**Alternative branch:** `copilot/run-full-rebuild-core-workflow` (current workspace - has same research files)
**Repository:** learn-ukrainian/learn-ukrainian.github.io

## What Has Been Completed

### Phase 0: Research ✅ COMPLETE
- **41 research files** created in `curriculum/l2-uk-en/a1/audit/*-research.md`
- Each contains:
  - State Standard §references
  - Vocabulary frequency verification (lcorp.ulif.org.ua)
  - Cultural hooks from Ukrainian sources
  - Pedagogical notes for integration

### Current A1 Modules Status
- **44 module files** exist in `curriculum/l2-uk-en/a1/*.md`
- **44 status files** exist in `curriculum/l2-uk-en/a1/status/*.json`
- These appear to be from previous work and need to be rebuilt

## What Needs to Be Done

### Task: Complete A1 Full Rebuild (44 Modules)

Execute `/full-rebuild-core` workflow for all 44 A1 modules using the research files.

### Workflow Per Module

For each module (M01-44):
1. **Load research notes** from `curriculum/l2-uk-en/a1/audit/{slug}-research.md`
2. **Build content** using `/module` skill or `/full-rebuild-core a1 {num}`
3. **Content alignment** - Verify every research finding appears in prose
4. **Audit** - Run `scripts/audit_module.sh` until passes
5. **Deep review** - Use `/review-content-core-a` for quality check
6. **Verify** - Confirm status JSON shows pass

### Quality Requirements (NO SHORTCUTS!)

- ✅ **Word targets met** (95%+ minimum)
- ✅ **All outline sections** from plan included
- ✅ **Research findings integrated** (State Standard refs, cultural hooks, verified vocab)
- ✅ **Audit passes** (all gates green)
- ✅ **Deep review completed** (9/10+ quality score)

### Execution Strategy

**Option 1: Batch Processing (2 modules at a time)**
- Batch B01: M01-02
- Batch B02: M03-04
- ...through Batch B22: M43-44

**Option 2: Individual Sequential**
- Process M01, verify, commit
- Process M02, verify, commit
- Continue through M44

**Recommended:** Batch processing with subagents for efficiency

## Branch Situation

There are currently two branches:
1. **`copilot/a1-rebuild-clean`** - Clean branch based on main (PREFERRED)
2. **`copilot/run-full-rebuild-core-workflow`** - Old branch with unrelated history

**Action:** Use `copilot/a1-rebuild-clean` branch. Fetch and checkout:
```bash
git fetch origin copilot/a1-rebuild-clean
git checkout -b a1-work origin/copilot/a1-rebuild-clean
```

If that branch has issues, the research files exist on both branches, so work can proceed on current branch.

## Key Commands

```bash
# Fetch clean branch
git fetch origin copilot/a1-rebuild-clean
git checkout copilot/a1-rebuild-clean

# Verify research files
ls curriculum/l2-uk-en/a1/audit/*-research.md | wc -l  # Should show 41

# Run full rebuild for a module
/full-rebuild-core a1 {module_number}

# Or use task tool with subagent
/task general-purpose "Execute /full-rebuild-core a1 {num} with all phases"

# Audit a module
scripts/audit_module.sh curriculum/l2-uk-en/a1/{file}.md

# Check progress
npm run status:a1
```

## Important Notes

1. **Research files are the foundation** - Always load them before writing
2. **Phase 1.5 (Content Alignment) is CRITICAL** - Must verify research → prose
3. **Audit must pass** - Iterate until all gates green
4. **Old audits are obsolete** - Don't rely on existing audit files
5. **Quality over speed** - This is for Ukraine's education system

## Success Criteria

- [ ] All 44 modules rebuilt using research
- [ ] All 44 modules pass audit (9/10+ quality)
- [ ] All status files show "pass"
- [ ] Ready to merge to main

## Next Action

**Start with Batch B01 (M01-02):**

Execute the full rebuild workflow for the first two modules, ensuring all quality gates are met before proceeding to the next batch.

Would you like me to start with B01 now, or do you have questions about the approach?
