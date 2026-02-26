        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `synonyms-place`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: synonyms-place
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  synonyms-place
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 5166/4000 (raw: 5401) | engagement: 0/6 | pedagogy: 1 violations | richness: 66% < 95% min (phraseology)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Replace invalid types with valid ones from: match-up, fill-in, quiz, true-false, group-sort, unjumble, error-correction, anagram, select, translate, cloze, mark-the-words, reading, essay-response, critical-analysis, comparative-study, authorial-intent, creative-writing, etymology-trace, transcription, grammar-identify, paleography-analysis, dialect-comparison, translation-critique, phonology-lab, grammar-lab, parallel-text, historical-writing, register-identify, loanword-trace, comparative-style
    [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (9 total): 'не просто X, а Y' x4, 'не лише X, а й Y' x5 — robotic prose
       → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 2 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/synonyms-place-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/synonyms-place.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/synonyms-place-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/synonyms-place.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

