        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `reading-grammar-rules`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: reading-grammar-rules
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  reading-grammar-rules
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Only 1/9 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-2-core.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Did I Learn?' test from the tier-2 guide, (4) score each dimension honestly — justify any 10/10 with evidence, (5) list at least 1 real issue (no module is perfect).
  failing gates:
    review: Only 1/9 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-2-core.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Did I Learn?' test from the tier-2 guide, (4) score each dimension honestly — justify any 10/10 with evidence, (5) list at least 1 real issue (no module is perfect).

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 98.8% (target 60-100% (B1.0 Bridge))
  Richness     ✅ 99% (grammar)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/reading-grammar-rules-audit.md
    🕵️  Review Validation: 1 critical, 0 warnings
       ❌ [UNVERIFIED_CITATIONS] Only 1/9 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-2-core.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Did I Learn?' test from the tier-2 guide, (4) score each dimension honestly — justify any 10/10 with evidence, (5) list at least 1 real issue (no module is perfect).
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/reading-grammar-rules.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Only 1/9 Ukrainian citations in the review were found in the source module. The reviewer may be quoting from memory rather than from the actual content. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-v4 using claude_extensions/commands/review-tiers/tier-2-core.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) cite specific Ukrainian sentences with issues (quote them with «»), (3) apply the 'Did I Learn?' test from the tier-2 guide, (4) score each dimension honestly — justify any 10/10 with evidence, (5) list at least 1 real issue (no module is perfect).

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/reading-grammar-rules-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/reading-grammar-rules.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/reading-grammar-rules.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/reading-grammar-rules.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

