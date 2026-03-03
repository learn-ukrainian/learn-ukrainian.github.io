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
  No Tier 1 (Beginner) review file at l2-uk-en/a1/review/my-world-objects-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run build_module.py Phase D (tier-1-beginner) using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence and stress mark, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
  failing gates:
    review: No Tier 1 (Beginner) review file at l2-uk-en/a1/review/my-world-objects-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run build_module.py Phase D (tier-1-beginner) using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence and stress mark, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/my-world-objects-audit.log for details)

  Running RAG word verification...
  Verifying: my-world-objects.md
    VESUM misses: 3 — querying RAG...
  [embed] Loading BGE-M3 from BAAI/bge-m3...

  Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
  Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 48247.36it/s]
  [embed] BGE-M3 loaded.
  You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
    Words: 317 | VESUM: 314 (99.1%) | RAG: 1 | Not found: 2
    Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/my-world-objects-rag-audit.md
  ⚠️  RAG verification found unverified words (see audit report)

VESUM: 314/317 (99%) verified
⚠️ VESUM not found (3): Ганна, Ганно, Тарас
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

