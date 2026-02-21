        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `the-dative-i-pronouns`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: the-dative-i-pronouns
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-dative-i-pronouns
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 3493/3000 (raw: 3821) | pedagogy: 15 violations

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [METALANGUAGE] Metalanguage terms used but not in vocabulary: називний, займенник, прикметник, давальний, іменник
       → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
     → Revision recommended (severity 50/100)
     → 16 violations (severe - consider revision)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/the-dative-i-pronouns-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/the-dative-i-pronouns.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-dative-i-pronouns-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-i-pronouns.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/the-dative-i-pronouns.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/the-dative-i-pronouns.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

