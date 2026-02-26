        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `professional-email-advanced`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: professional-email-advanced
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  professional-email-advanced
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3619/5000 (raw: 4059) | engagement: 0/5 | richness: 62% < 95% min (grammar) - REWRITE needed

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (6 total): 'не просто X, а Y' x6 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/professional-email-advanced-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/professional-email-advanced.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/professional-email-advanced-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/professional-email-advanced.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

