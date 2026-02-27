        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `panteleimon-kulish`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: panteleimon-kulish
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  panteleimon-kulish
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  3 Outline Compliance Errors
  failing gates:
    lesson: 4234/5000 (raw: 4690) | pedagogy: 1 violations | richness: 94% < 95% min (biography)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 4 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/audit/panteleimon-kulish-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/status/panteleimon-kulish.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 3 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/panteleimon-kulish-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/panteleimon-kulish.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

