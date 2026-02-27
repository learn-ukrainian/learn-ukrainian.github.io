        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `mykhailo-kotsiubynsky`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: mykhailo-kotsiubynsky
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  mykhailo-kotsiubynsky
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4814/5000 (raw: 5316)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Pedagogy     ✅ Level-appropriate
  Content_heavy ⏳ Deferred (content-only audit)
  Grammar      ℹ️ N/A (covered by naturalness)
  Naturalness  ℹ️ PENDING — awaiting review
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ⚠️ Refresh recommended: Research has 5+ sources but content cites 0
  Immersion    🇺🇦 99.1% (target 95-100% (biography))
  Richness     ✅ 97% (biography)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/audit/mykhailo-kotsiubynsky-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/status/mykhailo-kotsiubynsky.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/mykhailo-kotsiubynsky-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/mykhailo-kotsiubynsky.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

