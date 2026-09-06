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

## Step 3: Classify Fixes and Check Existing Authorization

Classify fixes to identify the evidence and decision they require; the category
does not reopen an operator decision already made.

| Category | Examples | Handling |
|----------|----------|----------|
| **SAFE** | Version format, YAML quoting, a verified typo or ghost vocabulary item | Apply within the requested review-fix scope after checking the report against the current plan. |
| **STRUCTURAL** | Increase word_target, add/remove sections, modify content_outline or objectives | Apply when the requested change is already authorized; otherwise prepare the exact diff and identify the missing scope decision. |
| **SEMANTIC** | Change grammar scope, pedagogical approach, or decolonization framing | Verify the evidence and existing operator decision; apply the authorized change or present the unresolved alternatives. |

Use required linguistic sources for Ukrainian word, stress, or morphology
claims. The report's recommendation alone does not prove linguistic validity.

## Step 4: Make Pending Decisions Concrete

Read current plans and prepare the applicable edits before requesting a missing
decision. Group proposed changes by plan, with severity, category, and the
relevant old/new YAML. Apply independently authorized fixes and report them.

For a structural or semantic change already covered by operator authorization,
proceed; do not add another approval round merely because of its category.
If a change introduces an unapproved scope decision, an unresolved conflict, or
a removal lacking explicit authorization, show the concrete diff and ask only
for that decision. Hold the dependent edit until an actual answer arrives.
Never write “applying unless you object” or interpret silence, elapsed time,
or an unanswered question as approval.

Example pending diff:

```diff
 # curriculum/l2-uk-en/plans/{track}/{slug}.yaml
-word_target: 3500
+word_target: 5000
```

State what authorization is missing for this change. A generic category label
is not a reason to pause work that the operator already ordered.

## Step 5: Apply Fixes

When applying fixes to a plan:

1. **Read the current plan** with the Read tool
2. **Bump the version** — increment the minor version (e.g., `'2.0'` → `'2.1'`). This is MANDATORY for any change.
3. **Apply all authorized fixes** to the plan in one Edit call
4. **Verify the result** — re-read the file and check YAML validity

**NEVER:**
- Change word_target downward (even if the review suggests it — reviews never suggest this, but guard against it)
- Remove content_outline sections without explicit user authorization (earlier authorization still applies)
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
| {slug} | CRITICAL | Increased word_target 3500→5000 | STRUCTURAL |
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
- **Multiple conflicting fixes for same field** — Follow an existing operator decision if it resolves the conflict; otherwise prepare the alternatives and ask for that decision
- **Fix would make plan inconsistent** (e.g., removing a section but objectives still reference it) — Flag as deferred, don't apply partial fix
