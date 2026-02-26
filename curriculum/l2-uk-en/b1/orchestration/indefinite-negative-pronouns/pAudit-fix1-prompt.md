        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `indefinite-negative-pronouns`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: indefinite-negative-pronouns
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  indefinite-negative-pronouns
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3743/4000 (raw: 4348) | engagement: 0/5 | pedagogy: 2 violations | richness: 54% < 95% min (grammar) - REWRITE needed

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Break into shorter sentences. First 5 words: 'Ми чітко розрізняємо того хто...'
    [COMPLEXITY] Sentence too long for B1: 35 words (max 30)
       → FIX: Break into shorter sentences. First 5 words: 'Ви навчилися прив язувати частку...'


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/indefinite-negative-pronouns-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/indefinite-negative-pronouns.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/indefinite-negative-pronouns-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/indefinite-negative-pronouns.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

