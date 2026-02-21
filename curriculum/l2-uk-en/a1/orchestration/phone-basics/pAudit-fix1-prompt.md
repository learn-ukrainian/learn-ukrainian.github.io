        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `phone-basics`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: phone-basics
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  phone-basics
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    meta: Valid Structure | Lint: 2 Format Errors
    lesson: 2709/2000 (raw: 2890) | pedagogy: 5 violations | immersion: 10.3% LOW (target 35-55% (M41))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


  🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 77/100)
     → 5 violations (moderate)
     → 4 grammar-level violations (fundamental)
     → Immersion 25% off target (major rebalancing needed)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/phone-basics-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/phone-basics.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/phone-basics-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/phone-basics.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

