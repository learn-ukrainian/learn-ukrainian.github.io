        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `the-cyrillic-code-ii`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: the-cyrillic-code-ii
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-cyrillic-code-ii
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 2315/2000 (raw: 2685) | pedagogy: 2 violations | immersion: 3.0% LOW (target 5-15% (M02))
    activities: 10/8 | density: 1 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-ii-audit.log for details)

  Running RAG word verification...
  Verifying: the-cyrillic-code-ii.md
    VESUM misses: 3 — querying RAG...
  [embed] Loading BGE-M3 from BAAI/bge-m3...

  Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
  Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 45606.79it/s]
  [embed] BGE-M3 loaded.
  You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
    Words: 49 | VESUM: 46 (93.9%) | RAG: 1 | Not found: 2
    Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-cyrillic-code-ii-rag-audit.md
  ⚠️  RAG verification found unverified words (see audit report)

VESUM: 46/49 (94%) verified
⚠️ VESUM not found (3): анан, ука, ім
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-ii.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

