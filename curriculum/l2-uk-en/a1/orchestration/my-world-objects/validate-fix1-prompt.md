        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `my-world-objects`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: my-world-objects
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  my-world-objects
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 3571/3300 (raw: 3776) | engagement: 0/3 | pedagogy: 7 violations | immersion: 6.8% LOW (target 15-35% (M10))
    activities: 10/8 | density: 3 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/my-world-objects-audit.log for details)

  Running RAG word verification...
  Verifying: my-world-objects.md
    VESUM misses: 3 — querying RAG...
  [embed] Loading BGE-M3 from BAAI/bge-m3...

  Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
  Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 77961.04it/s]
  [embed] BGE-M3 loaded.
  You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
    Words: 201 | VESUM: 198 (98.5%) | RAG: 2 | Not found: 1
    Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/my-world-objects-rag-audit.md
  ⚠️  RAG verification found unverified words (see audit report)

VESUM: 198/201 (99%) verified
⚠️ VESUM not found (3): Анна, Борис, изба
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-world-objects.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/my-world-objects.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/my-world-objects.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

