        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `kniaz-sviatoslav`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: kniaz-sviatoslav
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  kniaz-sviatoslav
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Structure: Missing '## Vocabulary' header OR vocabulary sidecar
  failing gates:
    meta: Missing '## Vocabulary' header OR vocabulary sidecar

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Richness     ✅ 99% (biography)

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 20/100)
     → Structure issue: Missing '## Vocabulary' header OR vocabulary sidecar


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/audit/kniaz-sviatoslav-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/status/kniaz-sviatoslav.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Structure: Missing '## Vocabulary' header OR vocabulary sidecar

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/kniaz-sviatoslav-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/kniaz-sviatoslav.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/activities/kniaz-sviatoslav.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/vocabulary/kniaz-sviatoslav.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

