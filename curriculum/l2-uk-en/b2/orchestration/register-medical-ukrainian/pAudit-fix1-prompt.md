        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `register-medical-ukrainian`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: register-medical-ukrainian
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  register-medical-ukrainian
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5849/4000 (raw: 6134) | richness: 94% < 95% min (style)
  missing orchestration artifacts:
    no Phase 2 artifacts (section files or prompt)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Pedagogy     ✅ Level-appropriate
  Content_heavy ⏳ Deferred (content-only audit)
  Grammar      ℹ️ N/A (covered by naturalness)
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 98.7% (target 90-100% (grammar))
  Richness     ❌ 94% < 95% min (style)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/register-medical-ukrainian-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/register-medical-ukrainian.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/register-medical-ukrainian-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/register-medical-ukrainian.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

