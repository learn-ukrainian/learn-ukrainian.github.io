        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `spatial-prepositions`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: spatial-prepositions
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  spatial-prepositions
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  3 Outline Compliance Errors
  failing gates:
    meta: Valid Structure | Lint: 4 Format Errors
    lesson: 2890/3000 (raw: 3101) | pedagogy: 3 violations | immersion: 23.5% LOW (target 50-60% (A2.1))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
     → Revision recommended (severity 65/100)
     → 4 violations (moderate)
     → Immersion 26% off target (major rebalancing needed)
     → 4 format errors


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/spatial-prepositions-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/spatial-prepositions.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 3 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/spatial-prepositions-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/spatial-prepositions.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

