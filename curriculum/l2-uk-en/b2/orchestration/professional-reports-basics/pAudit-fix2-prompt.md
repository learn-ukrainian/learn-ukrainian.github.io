        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `professional-reports-basics`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: professional-reports-basics
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  professional-reports-basics
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 6221/4000 (raw: 6633) | engagement: 0/6 | pedagogy: 1 violations | richness: 74% < 80% min (skills)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [RUSSICISM_DETECTED] Found 3 Russicism(s) in content: 'приймати участь' → брати участь; 'самий кращий' → найкращий; 'слідуючий' → наступний
       → FIX: Replace Russicisms with standard Ukrainian equivalents. These are Russian calques that have standard Ukrainian forms. See Phase B prompt 'Russianisms Pre-Output Scan' table.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/professional-reports-basics-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/professional-reports-basics.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/professional-reports-basics-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/professional-reports-basics.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

