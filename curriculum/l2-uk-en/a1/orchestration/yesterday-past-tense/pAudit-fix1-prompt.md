        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `yesterday-past-tense`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: yesterday-past-tense
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  yesterday-past-tense
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    meta: Valid Structure | Lint: 1 Format Errors
    lesson: 2882/2000 (raw: 3015) | pedagogy: 5 violations | immersion: 11.5% LOW (target 35-55% (M36))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Rewrite in neutral educational voice. Remove first-person teacher persona.


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 77/100)
     → 6 violations (moderate)
     → 4 grammar-level violations (fundamental)
     → Immersion 23% off target (major rebalancing needed)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/yesterday-past-tense-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/yesterday-past-tense.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/yesterday-past-tense-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

