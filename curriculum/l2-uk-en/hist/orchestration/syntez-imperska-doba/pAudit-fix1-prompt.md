        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `syntez-imperska-doba`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: syntez-imperska-doba
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  syntez-imperska-doba
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5209/5000 (raw: 5658) | richness: 93% < 95% min (history)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:
    ⚠️ [MISSING_REQUIRED_CALLOUT] Missing required callout '[!history-bite]' per template 'history-module-template.md'
       → FIX: Add a `> [!history-bite]` box as specified in the template. This enhances module quality.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/syntez-imperska-doba-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/syntez-imperska-doba.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/syntez-imperska-doba-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/syntez-imperska-doba.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

