        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `knyazhna-anna-yaroslavna`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: knyazhna-anna-yaroslavna
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  knyazhna-anna-yaroslavna
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  7 Outline Compliance Errors
  Tone Error. Found 'Kiev'. Use 'Kyiv' (Ukrainian transliteration).
  failing gates:
    lesson: 3894/5000 (raw: 4243) | pedagogy: 2 violations | richness: 90% < 95% min (biography)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 5 violations (moderate)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/audit/knyazhna-anna-yaroslavna-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/status/knyazhna-anna-yaroslavna.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • 7 Outline Compliance Errors
    • Tone Error. Found 'Kiev'. Use 'Kyiv' (Ukrainian transliteration).

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/knyazhna-anna-yaroslavna-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/knyazhna-anna-yaroslavna.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

