        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `the-cyrillic-code-i`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: the-cyrillic-code-i
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-cyrillic-code-i
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 3659/2000 (raw: 3779) | pedagogy: 5 violations | immersion: 2.1% LOW (target 5-15% (M01))
    activities: 10/8 | density: 1 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-i-audit.log for details)

  Running RAG word verification...
  Verifying: the-cyrillic-code-i.md
    VESUM misses: 11 — querying RAG...
  [embed] Loading BGE-M3 from BAAI/bge-m3...

  Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
  Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 241979.08it/s]
  [embed] BGE-M3 loaded.
  You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
    Words: 57 | VESUM: 46 (80.7%) | RAG: 6 | Not found: 5
    Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-cyrillic-code-i-rag-audit.md
  ⚠️  RAG verification found unverified words (see audit report)

VESUM: 46/57 (81%) verified
⚠️ VESUM not found (11): АЛ, АМ, АН, Африка, ЛУ, МА-МА, СА, СУ, УЛ, УН
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-i.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-i.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-i.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

