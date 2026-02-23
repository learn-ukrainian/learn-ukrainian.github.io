        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `telling-stories`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: telling-stories
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  telling-stories
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3942/3000 (raw: 4198) | pedagogy: 15 violations | immersion: 84.9% HIGH (target 60-75% (A2.2))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Diversify section openings. Each section should start with a unique approach: questions, examples, cultural hooks, direct instruction, comparisons — not the same template.


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 80/100)
     → 18 violations (severe - consider revision)
     → 7 grammar-level violations (fundamental)
     → Immersion 10% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/telling-stories-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/telling-stories.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/telling-stories-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/telling-stories.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

