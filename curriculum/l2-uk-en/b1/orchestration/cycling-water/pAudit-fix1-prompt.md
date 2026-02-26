        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `cycling-water`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: cycling-water
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  cycling-water
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5007/4000 (raw: 5405) | pedagogy: 17 violations | richness: 76% < 95% min (cultural)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [COMPLEXITY] Sentence too long for B1: 33 words (max 30)
       → FIX: Break into shorter sentences. First 5 words: 'Ми дуже детально крок за...'


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 50/100)
     → Revision recommended (severity 50/100)
     → 17 violations (severe - consider revision)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/cycling-water-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/cycling-water.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/cycling-water-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/cycling-water.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

