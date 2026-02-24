        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `proverbs-work-wisdom-character`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: proverbs-work-wisdom-character
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  proverbs-work-wisdom-character
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3669/4000 (raw: 3974) | immersion: 83.3% LOW (target 90-100% (vocab))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [STATE_STANDARD_LOW_IMMERSION] Module 45 has 83.3% immersion (target: 90.0%+)
       → FIX: Add more Ukrainian content to reach 90.0%+ immersion


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 4 violations (moderate)
     → Immersion 7% off target (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/proverbs-work-wisdom-character-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/proverbs-work-wisdom-character.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/proverbs-work-wisdom-character-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/proverbs-work-wisdom-character.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

