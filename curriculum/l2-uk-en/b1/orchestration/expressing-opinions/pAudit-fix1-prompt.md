        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `expressing-opinions`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: expressing-opinions
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  expressing-opinions
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4638/4000 (raw: 4883) | engagement: 0/5 | richness: 47% < 95% min (vocabulary) - REWRITE needed

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [CONTENT_REDUNDANCY] Redundant information detected in lesson (86% overlap): "* Цей фільм, **(кома)** на мою думку, **(кома)** заслуговує на найвищу нагороду.". Shares significant keywords with sentence at index 140.
       → FIX: Remove redundant paragraphs. Ensure each section adds new unique value.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/expressing-opinions-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/expressing-opinions.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/expressing-opinions-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/expressing-opinions.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

