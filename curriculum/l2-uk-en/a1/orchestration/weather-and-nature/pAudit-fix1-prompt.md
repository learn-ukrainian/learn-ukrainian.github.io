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
  failing gates:
    lesson: 4303/2000 (raw: 4488) | pedagogy: 12 violations | immersion: 28.2% LOW (target 35-55% (M43))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Rewrite in neutral educational voice. Remove first-person teacher persona.


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 80/100)
     → 13 violations (severe - consider revision)
     → 11 grammar-level violations (fundamental)
     → Immersion 7% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/weather-and-nature-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/weather-and-nature.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

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

