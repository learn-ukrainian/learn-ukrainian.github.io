        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `knyahynia-olha`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: knyahynia-olha
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  knyahynia-olha
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  4 Outline Compliance Errors

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Naturalness  ✅ 10/10 (High)
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 99.5% (target 95-100% (biography))
  Richness     ✅ 95% (biography)

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/audit/knyahynia-olha-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/status/knyahynia-olha.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 4 Outline Compliance Errors

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/knyahynia-olha-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/knyahynia-olha.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

