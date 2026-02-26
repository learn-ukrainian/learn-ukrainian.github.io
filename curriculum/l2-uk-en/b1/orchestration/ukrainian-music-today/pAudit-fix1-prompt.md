        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `ukrainian-music-today`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: ukrainian-music-today
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  ukrainian-music-today
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5735/4000 (raw: 6193) | engagement: 4/5 | pedagogy: 32 violations | richness: 73% < 95% min (cultural)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (3 occurrences): (Classical music history), (Locative case), (Accusative case) — breaks immersion target
       → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
     → Revision recommended (severity 50/100)
     → 35 violations (severe - consider revision)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/ukrainian-music-today-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/ukrainian-music-today.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/ukrainian-music-today-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/ukrainian-music-today.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

