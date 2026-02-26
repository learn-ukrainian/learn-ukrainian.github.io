        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `register-technical-scientific`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: register-technical-scientific
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  register-technical-scientific
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4466/4000 (raw: 4883) | richness: 89% < 95% min (grammar)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Pedagogy     ✅ Level-appropriate
  Content_heavy ⏳ Deferred (content-only audit)
  Grammar      ℹ️ N/A (covered by naturalness)
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ⚠️ Refresh recommended: Research has 2+ cultural hooks but content has no cultural section
  Immersion    🇺🇦 99.7% (target 90-100% (grammar))
  Richness     ❌ 89% < 95% min (grammar)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/register-technical-scientific-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/register-technical-scientific.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/register-technical-scientific-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/register-technical-scientific.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

