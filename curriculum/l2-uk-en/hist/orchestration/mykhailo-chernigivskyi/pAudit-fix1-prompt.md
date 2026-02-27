        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `mykhailo-chernigivskyi`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: mykhailo-chernigivskyi
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  mykhailo-chernigivskyi
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  3 Outline Compliance Errors
  failing gates:
    lesson: 4253/5000 (raw: 4582) | engagement: 3/5 | richness: 90% < 95% min (history)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/audit/mykhailo-chernigivskyi-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/status/mykhailo-chernigivskyi.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 3 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/mykhailo-chernigivskyi-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/mykhailo-chernigivskyi.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

