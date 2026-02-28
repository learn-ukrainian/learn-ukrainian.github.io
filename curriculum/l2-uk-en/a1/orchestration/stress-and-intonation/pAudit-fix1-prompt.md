        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `stress-and-intonation`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: stress-and-intonation
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  stress-and-intonation
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 3782/2000 (raw: 3972) | pedagogy: 1 violations | immersion: 4.5% LOW (target 15-35% (M06))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (5 occurrences): (First syllable), (Last syllable), (First syllable) — breaks immersion target
       → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
     → 3 violations (minor)
     → Immersion 11% off target


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/stress-and-intonation-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/stress-and-intonation.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/stress-and-intonation-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/stress-and-intonation.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

