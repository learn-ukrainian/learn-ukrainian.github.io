# Apply Plan Fixes Prompt

You are applying fixes from plan review reports to plan YAML files. You MUST follow the plan versioning protocol — plans are the source of truth and require careful handling.

## Step 1: Find Review Reports

For each plan in the selected range, look for:
- `curriculum/l2-uk-en/{track}/audit/{slug}-plan-review.md`

If a review report doesn't exist for a plan, skip it and note it in the summary.

If a review report exists but has verdict PASS with no issues, skip it.

## Step 2: Parse Issues and Fixes

Read each review report. Extract:

1. **Issues by severity** — CRITICAL, HIGH, MEDIUM, LOW
2. **Suggested Fixes** — The concrete old/new YAML edits

Filter by the severity flag:
- Default: CRITICAL + HIGH + MEDIUM
- `--severity CRITICAL` : CRITICAL only
- `--severity CRITICAL,HIGH` : CRITICAL + HIGH (no MEDIUM)
- `--all-fixes` : all severities including LOW

## Step 3: Classify Fixes

Categorize each fix as one of:

| Category | Examples | Risk | Approval |
|----------|----------|------|----------|
| **SAFE** | Fix version string, fix YAML quoting, remove ghost words from vocab, fix typos in Ukrainian text | Low | Apply directly |
| **STRUCTURAL** | Change word_target, add/remove sections, modify content_outline, change objectives | Medium | Show diff, ask user |
| **SEMANTIC** | Rewrite objectives, change decolonization framing, modify grammar scope, alter pedagogical approach | High | Show diff, ask user |

## Step 4: Present Changes for Approval

**For SAFE fixes:** List them all, then apply in batch. Tell the user what you did.

**For STRUCTURAL and SEMANTIC fixes:** Present each one as a diff:

```
## Plan: {slug} (sequence {N})

### Fix 1: {description} [{severity}] — STRUCTURAL

File: curriculum/l2-uk-en/plans/{track}/{slug}.yaml

```yaml
# Line ~{N}: OLD
word_target: 3500

# NEW
word_target: 5000
```

Apply? [Applying unless you object]
```

Group by plan file. Apply all SAFE fixes first, then present STRUCTURAL/SEMANTIC for each plan.

## Step 5: Apply Fixes

When applying fixes to a plan:

1. **Read the current plan** with the Read tool
2. **Bump the version** — increment the minor version (e.g., `'2.0'` → `'2.1'`). This is MANDATORY for any change.
3. **Apply all approved fixes** to the plan in one Edit call
4. **Verify the result** — re-read the file and check YAML validity

**NEVER:**
- Change word_target downward (even if the review suggests it — reviews never suggest this, but guard against it)
- Remove content_outline sections without explicit user approval
- Modify fields not mentioned in the review report
- Skip the version bump

## Step 6: Summary

After processing all plans, output:

```markdown
# Apply Plan Fixes Summary: {track} {range}

**Plans processed:** X
**Plans with reviews:** Y
**Plans with fixes applied:** Z
**Plans skipped (PASS):** W

## Changes Applied

| Plan | Severity | Fix | Category |
|------|----------|-----|----------|
| {slug} | CRITICAL | Fixed word_target 3500→5000 | SAFE |
| {slug} | HIGH | Removed ghost word "казновий" | SAFE |
| {slug} | HIGH | Rewrote objective for analysis | SEMANTIC |

## Skipped (no review report)
- {slug-1}
- {slug-2}

## Deferred (user review needed)
- {slug}: {description of fix needing manual judgment}
```

## Edge Cases

- **Plan has no review report** — Skip, note in summary
- **Review says PASS** — Skip, note in summary
- **Review says FAIL but no suggested fixes** — Flag for manual review, don't modify
- **Multiple conflicting fixes for same field** — Present both to user, let them choose
- **Fix would make plan inconsistent** (e.g., removing a section but objectives still reference it) — Flag as deferred, don't apply partial fix
