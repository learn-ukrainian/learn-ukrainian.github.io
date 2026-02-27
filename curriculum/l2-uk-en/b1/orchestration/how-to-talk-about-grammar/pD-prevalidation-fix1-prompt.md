        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `how-to-talk-about-grammar`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: how-to-talk-about-grammar
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  how-to-talk-about-grammar
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Review is missing 'Reviewed-By:' metadata. Re-run Phase D to generate a review with proper provenance.
  failing gates:
    review: Review is missing 'Reviewed-By:' metadata. Re-run Phase D to generate a review with proper provenance.

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Richness     ✅ 99% (bridge)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/how-to-talk-about-grammar-audit.md
    🎭 Review Gaming: 1 critical, 2 warnings
       ❌ [MISSING_REVIEWER_ID] Review is missing 'Reviewed-By:' metadata. Re-run Phase D to generate a review with proper provenance.
       ⚠️  [REVIEW_LOW_SECTION_COVERAGE] Review covers 3/7 (43%) content sections. Consider addressing all major sections for a complete review.
       ⚠️  [PHANTOM_SECTION_REFERENCE] Review references 1 section(s) not found in content: 'Чергування звуків'. Verify section names match actual content headers.
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/how-to-talk-about-grammar.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Review is missing 'Reviewed-By:' metadata. Re-run Phase D to generate a review with proper provenance.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/how-to-talk-about-grammar-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/how-to-talk-about-grammar.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/how-to-talk-about-grammar.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

