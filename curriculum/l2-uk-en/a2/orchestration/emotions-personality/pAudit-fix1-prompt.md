        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `emotions-personality`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: emotions-personality
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  emotions-personality
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5528/3000 (raw: 6111) | engagement: 0/4 | pedagogy: 41 violations | immersion: 83.5% HIGH (target 60-75% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace «і» with «й» (between vowels)


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 80/100)
     → 43 violations (severe - consider revision)
     → 6 grammar-level violations (fundamental)
     → Immersion 9% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/emotions-personality-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/emotions-personality.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/emotions-personality-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/emotions-personality.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

