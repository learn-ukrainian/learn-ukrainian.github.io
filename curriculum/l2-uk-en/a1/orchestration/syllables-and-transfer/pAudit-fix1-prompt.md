        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `syllables-and-transfer`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: syllables-and-transfer
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  syllables-and-transfer
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3861/2000 (raw: 4034) | engagement: 0/3 | pedagogy: 2 violations | immersion: 5.8% LOW (target 10-25% (M05))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Participles not allowed until B1. Use relative clauses or simple sentences.
    [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (20 occurrences): (My cat is sleeping), (This is an old tree), (He is drinking milk) — breaks immersion target
       → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 3 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/syllables-and-transfer-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/syllables-and-transfer.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/syllables-and-transfer-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/syllables-and-transfer.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

