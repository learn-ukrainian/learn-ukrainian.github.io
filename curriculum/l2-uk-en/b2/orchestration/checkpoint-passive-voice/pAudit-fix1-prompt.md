        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `checkpoint-passive-voice`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: checkpoint-passive-voice
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  checkpoint-passive-voice
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  Checkpoint Format Errors
  failing gates:
    lesson: 3919/4000 (raw: 4329) (81 short) | engagement: 0/4 | pedagogy: 2 violations | richness: 54% < 85% min (checkpoint)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 4 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/checkpoint-passive-voice-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/checkpoint-passive-voice.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Checkpoint Format Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-passive-voice-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/checkpoint-passive-voice.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

