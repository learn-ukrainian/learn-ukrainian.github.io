        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `register-practice-cross-register-rewriting`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: register-practice-cross-register-rewriting
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  register-practice-cross-register-rewriting
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 4101/4000 (raw: 4487) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
    [STRUCTURAL_MONOTONY] 4 of 52 section openers share >70% lexical overlap. Sections: ### Самоперевірка; ### Самоперевірка; ### Самоперевірка... Opener pattern: "**Чекліст:**..."
       → FIX: Diversify section openings. Each section should start with a unique approach: questions, examples, cultural hooks, direct instruction, comparisons — not the same template.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/register-practice-cross-register-rewriting-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/register-practice-cross-register-rewriting.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/register-practice-cross-register-rewriting-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/register-practice-cross-register-rewriting.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

