        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `the-cyrillic-code-iii`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: the-cyrillic-code-iii
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-cyrillic-code-iii
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2408/2000 (raw: 2513) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent, creative-writing, etymology-trace, transcription, grammar-identify, paleography-analysis, dialect-comparison, translation-critique, phonology-lab, grammar-lab, parallel-text, historical-writing, register-identify, loanword-trace, comparative-style
    [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'example sentence:...'.
       → FIX: Vary sentence structure.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-cyrillic-code-iii-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-cyrillic-code-iii.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-iii-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-iii.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

