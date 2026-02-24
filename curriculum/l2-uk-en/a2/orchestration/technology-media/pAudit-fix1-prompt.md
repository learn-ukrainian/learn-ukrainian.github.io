        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `technology-media`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: technology-media
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  technology-media
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    meta: Valid Structure | Lint: 1 Format Errors
    lesson: 4568/3000 (raw: 4886) | engagement: 0/4 | pedagogy: 14 violations | immersion: 77.7% HIGH (target 60-75% (A2.3))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 72/100)
     → Revision recommended (severity 72/100)
     → 16 violations (severe - consider revision)
     → 3 grammar-level violations (fundamental)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/technology-media-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/technology-media.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/technology-media-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/technology-media.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

