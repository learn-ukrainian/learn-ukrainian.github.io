        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `the-dative-ii-nouns`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: the-dative-ii-nouns
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-dative-ii-nouns
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 3689/3000 (raw: 4021) | pedagogy: 5 violations

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [EUPHONY] Line 97: повторення і/й без «та» — «...х**а — Сва**с**і
  *   Стрі**х**а...»; використайте «та» для другого сполучника
       → FIX: Replace second «і»/«й» with «та» for conjunction variety


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 6 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/the-dative-ii-nouns-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/the-dative-ii-nouns.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-dative-ii-nouns-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-ii-nouns.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/the-dative-ii-nouns.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

