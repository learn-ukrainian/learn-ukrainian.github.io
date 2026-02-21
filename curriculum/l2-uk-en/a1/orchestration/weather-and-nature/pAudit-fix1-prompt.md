        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `weather-and-nature`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: weather-and-nature
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  weather-and-nature
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  1 Outline Compliance Errors
  failing gates:
    meta: Valid Structure | Lint: 1 Format Errors
    lesson: 2068/2000 (raw: 2303) | pedagogy: 8 violations | immersion: 20.0% LOW (target 35-55% (M29))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
     → Revision recommended (severity 72/100)
     → 8 violations (significant)
     → 7 grammar-level violations (fundamental)
     → Immersion 15% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/weather-and-nature-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/weather-and-nature.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 1 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/weather-and-nature-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/weather-and-nature.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

