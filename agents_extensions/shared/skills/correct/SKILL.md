---
name: correct
description: Make a targeted correction to an identified defect or repeated mistake within the assigned worker's scope. Use for /correct or a specific correction request.
---

# Correct

Correct the reported behaviour with the smallest adequate change. This skill
authorizes no unrelated edits or expansion of the task's owned paths.

1. Identify the defect, affected acceptance criterion, reproducible input and
   expected result. For a repeated mistake, inspect relevant commits or findings
   to establish the common cause; do not mine unrelated or private history.
2. Confirm the authoring worker and owned paths. Reviewers remain read-only:
   return the finding and reproduction to the owner. Preserve other workers'
   changes. Scope conflicts or a required new architecture or policy decision
   go to the accountable driver for the applicable approval, before that work.
3. Fix the root cause using existing supported patterns. Prefer an existing
   ownership boundary, type constraint or actionable lint over another prose
   warning when it prevents the defect within approved scope. Do not weaken or
   delete tests, rewrite agent rules, or start a broad refactor to silence it.
4. **Prove it works:** exercise observable behaviour against the acceptance
   criteria. Run a regression test or reproduction that detects the original
   failure, then the corrected case and affected consumer tests. For a new
   guard, demonstrate rejection of the bad input and acceptance of valid input.
   Record the exact commands, revision, results and remaining unverified cases.
   Compilation or a clean diff alone does not prove the correction.
5. Inspect the final diff for scope and preserve the independent exact-head
   cross-family review and current-head CI gates in
   `agents_extensions/shared/rules/workflow.md`. A changed head needs fresh gates;
   this skill neither approves nor lands work. Escalate unresolved material
   findings through the driver under the repository's stopping policy.

Return the cause, changed paths, acceptance-criterion test evidence and any
residual with its owner. Distinguish a pushed correction from verified delivery.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.
