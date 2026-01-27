# Status Index Maintenance Plan

## Overview

Status index files (`docs/{LEVEL}-STATUS.md`) provide module completion overview for all curriculum levels. This document explains how to keep them up to date.

## When to Regenerate

### Manual Triggers (Primary)

Run status generation whenever you need current overview:

```bash
# Single level
npm run status:b2-hist

# All levels (takes ~5-10 minutes)
npm run status:all

# Specific level after major changes
npm run status:a1
```

**Recommended times to regenerate:**
- ✅ After completing a module (via `/module` or `/module-fix`)
- ✅ Before planning work on a level (to see current state)
- ✅ After batch fixes (e.g., fixing 10 hydration errors)
- ✅ Weekly during active development
- ✅ Before/after merging major PRs

### Automated Triggers (Optional Future Enhancement)

**Option 1: Git Hook (Post-Commit)**
- Regenerate only if `curriculum/l2-uk-en/{level}/` changed
- Fast, local-only
- Could be added to `.husky/post-commit` (opt-in)

**Option 2: GitHub Actions (Post-Push)**
- Regenerate all levels on push to main
- Commit changes back to repo
- Slower, but keeps repo always current

**Option 3: On-Demand GitHub Action**
- Manual workflow dispatch
- Generate for specific level or all

**Decision:** Start with **manual-only**. Add automation later if needed.

## Git Strategy

### Option A: Commit to Repo (RECOMMENDED)

**Pros:**
- ✅ Status visible in GitHub without running scripts
- ✅ History of progress over time
- ✅ Works for collaborators without running locally

**Cons:**
- ❌ Diffs show up in PRs (minor noise)
- ❌ Need to remember to regenerate

**Implementation:**
```bash
# .gitignore - DO NOT ignore status files
# (they are committed)

# After regenerating:
git add docs/*-STATUS.md
git commit -m "chore: update level status indices"
```

### Option B: Gitignore (Auto-Generate)

**Pros:**
- ✅ No git noise
- ✅ Always fresh when regenerated

**Cons:**
- ❌ Not visible in GitHub
- ❌ Each developer must regenerate locally
- ❌ No history

**Implementation:**
```bash
# .gitignore
docs/*-STATUS.md
```

**DECISION:** Use **Option A (Commit to Repo)** because:
- These are documentation, not build artifacts
- Useful to see in GitHub issues/discussions
- Progress tracking over time is valuable

## Integration Points

### 1. NPM Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "status:a1": "python scripts/generate_level_status.py a1",
    "status:a2": "python scripts/generate_level_status.py a2",
    "status:b1": "python scripts/generate_level_status.py b1",
    "status:b2": "python scripts/generate_level_status.py b2",
    "status:c1": "python scripts/generate_level_status.py c1",
    "status:c2": "python scripts/generate_level_status.py c2",
    "status:b2-hist": "python scripts/generate_level_status.py b2-hist",
    "status:c1-bio": "python scripts/generate_level_status.py c1-bio",
    "status:c1-hist": "python scripts/generate_level_status.py c1-hist",
    "status:lit": "python scripts/generate_level_status.py lit",
    "status:all": "python scripts/generate_level_status.py all"
  }
}
```

### 2. Module Workflow Integration

**After `/module` completes:**

```markdown
MODULE DEPLOYED: b2-hist/scythians-sarmatians ✅

...

Next steps:
1. Run `npm run status:b2-hist` to update level overview
2. Commit changes: `git add docs/B2-HIST-STATUS.md`
```

**After batch fixes:**

```bash
# Fix 10 modules
/module-fix b2-hist 1
/module-fix b2-hist 2
...

# Update overview
npm run status:b2-hist
git add docs/B2-HIST-STATUS.md
git commit -m "fix: resolve 10 hydration errors in B2-HIST"
```

### 3. Documentation Links

Update main docs to reference status files:

**CLAUDE.md:**
```markdown
## Quick Reference

- Current status: See `docs/{LEVEL}-STATUS.md`
- B2-HIST progress: [docs/B2-HIST-STATUS.md](docs/B2-HIST-STATUS.md)
```

**Issue #463 (B2-HIST upgrade):**
Link to `docs/B2-HIST-STATUS.md` in issue description for live progress tracking.

## Performance Considerations

**Audit time per module:** ~1 second
**Total time estimates:**
- A1 (34 modules): ~30 seconds
- A2 (70 modules): ~1 minute
- B1 (92 modules): ~2 minutes
- B2-HIST (140 modules): ~3 minutes
- **All levels (~530 modules):** ~10 minutes

**Optimization options (if needed):**
1. Cache audit results (invalidate on file change)
2. Parallel auditing (multiprocessing)
3. Only regenerate changed levels

**Decision:** Start simple. Optimize only if 10min becomes a problem.

## Workflow Example

**Scenario: Working on B2-HIST modules**

```bash
# 1. Check current status
npm run status:b2-hist
cat docs/B2-HIST-STATUS.md  # See 21 failing modules

# 2. Fix modules
/module-fix b2-hist 5
/module-fix b2-hist 8
/module b2-hist 10

# 3. Regenerate status
npm run status:b2-hist

# 4. Commit changes
git add docs/B2-HIST-STATUS.md \
  curriculum/l2-uk-en/b2-hist/meta/*.yaml \
  curriculum/l2-uk-en/b2-hist/*.md
git commit -m "fix: resolve issues in B2-HIST M05, M08, M10"
```

## Future Enhancements

### Phase 1 (Now): Manual Generation ✅

- Script works
- NPM commands added
- Files committed to git
- Manual regeneration

### Phase 2 (Optional): Smart Regeneration

- Only regenerate if level files changed since last generation
- Add `--check` flag to see if stale

### Phase 3 (Optional): CI Integration

- GitHub Action to regenerate on push
- Commit back to repo automatically
- Weekly cron job for safety

### Phase 4 (Optional): Dashboard

- HTML version with charts
- Progress over time graphs
- Issue correlation (which modules block which features)

## Decision: Start Simple

**Initial implementation:**
- ✅ Manual regeneration only
- ✅ Commit status files to git
- ✅ Update on demand (developer responsibility)
- ✅ No automation yet

**Review after 2 weeks:**
- Are status files being updated regularly?
- Is manual process working?
- Do we need automation?

---

**Related:**
- Issue: #464
- Script: `scripts/generate_level_status.py`
- Output: `docs/{LEVEL}-STATUS.md`
