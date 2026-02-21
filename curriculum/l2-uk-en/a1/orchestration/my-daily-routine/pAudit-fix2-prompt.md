        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `my-daily-routine`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: my-daily-routine
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  my-daily-routine
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  No Tier 1 (Beginner) review file at l2-uk-en/a1/review/my-daily-routine-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
  failing gates:
    review: No Tier 1 (Beginner) review file at l2-uk-en/a1/review/my-daily-routine-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Activity_quality ⏳ Deferred (content-only audit)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 39.8% (target 35-55% (M25))

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/my-daily-routine-audit.md
    🕵️  Review Validation: 1 critical, 0 warnings
       ❌ [MISSING_REVIEW] No Tier 1 (Beginner) review file at l2-uk-en/a1/review/my-daily-routine-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/my-daily-routine.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • No Tier 1 (Beginner) review file at l2-uk-en/a1/review/my-daily-routine-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/my-daily-routine-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-daily-routine.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

