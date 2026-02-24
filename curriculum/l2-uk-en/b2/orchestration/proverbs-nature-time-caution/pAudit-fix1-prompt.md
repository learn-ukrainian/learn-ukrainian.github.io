        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `proverbs-nature-time-caution`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: proverbs-nature-time-caution
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  proverbs-nature-time-caution
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 7413/4000 (raw: 7772) | engagement: 0/6 | richness: 65% < 95% min (phraseology)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace «і» with «й» (between vowels)
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (7 total): 'не просто X, а Y' x5, 'не лише X, а й Y' x2 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/proverbs-nature-time-caution-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/proverbs-nature-time-caution.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/proverbs-nature-time-caution-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/proverbs-nature-time-caution.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

