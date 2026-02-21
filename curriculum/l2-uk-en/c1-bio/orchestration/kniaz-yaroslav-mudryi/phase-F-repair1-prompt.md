        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `kniaz-yaroslav-mudryi`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: kniaz-yaroslav-mudryi
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  kniaz-yaroslav-mudryi
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Only 12/41 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-3-seminar.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Would I Stay?' test from the tier-3 seminar guide, (4) score each of 12 dimensions honestly — if giving 10/10, justify with a specific quote from the content, (5) list at least 1 real issue (no module is perfect), (6) check decolonization perspective and primary sources.
  failing gates:
    review: Only 12/41 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-3-seminar.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Would I Stay?' test from the tier-3 seminar guide, (4) score each of 12 dimensions honestly — if giving 10/10, justify with a specific quote from the content, (5) list at least 1 real issue (no module is perfect), (6) check decolonization perspective and primary sources.

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 99.7% (target 95-100% (biography))
  Richness     ✅ 95% (biography)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/audit/kniaz-yaroslav-mudryi-audit.md
    🕵️  Review Validation: 1 critical, 0 warnings
       ❌ [UNVERIFIED_CITATIONS] Only 12/41 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-3-seminar.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Would I Stay?' test from the tier-3 seminar guide, (4) score each of 12 dimensions honestly — if giving 10/10, justify with a specific quote from the content, (5) list at least 1 real issue (no module is perfect), (6) check decolonization perspective and primary sources.
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/status/kniaz-yaroslav-mudryi.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Only 12/41 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-3-seminar.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Would I Stay?' test from the tier-3 seminar guide, (4) score each of 12 dimensions honestly — if giving 10/10, justify with a specific quote from the content, (5) list at least 1 real issue (no module is perfect), (6) check decolonization perspective and primary sources.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/kniaz-yaroslav-mudryi-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/kniaz-yaroslav-mudryi.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/activities/kniaz-yaroslav-mudryi.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/vocabulary/kniaz-yaroslav-mudryi.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

