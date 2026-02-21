        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `prepositions-direction-origin`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: prepositions-direction-origin
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  prepositions-direction-origin
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2280/2000 (raw: 2601) | pedagogy: 54 violations | immersion: 83.5% HIGH (target 35-55% (M30))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 100/100)
     → 55 violations (severe - consider revision)
     → 31 grammar-level violations (fundamental)
     → Immersion 29% off target (major rebalancing needed)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/prepositions-direction-origin-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/prepositions-direction-origin.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/prepositions-direction-origin-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/prepositions-direction-origin.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

