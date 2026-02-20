        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `what-time-is-it`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: what-time-is-it
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  what-time-is-it
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  No Tier 1 (Beginner) review file at l2-uk-en/a1/review/what-time-is-it-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
  failing gates:
    review: No Tier 1 (Beginner) review file at l2-uk-en/a1/review/what-time-is-it-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  Activity_quality ℹ️ Quality validation N/A (A1/A2)
  Research     ✅ Content aligned with research
  Immersion    🇺🇦 35.4% (target 35-55% (M23))

  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/what-time-is-it-audit.md
    🕵️  Review Validation: 1 critical, 0 warnings
       ❌ [MISSING_REVIEW] No Tier 1 (Beginner) review file at l2-uk-en/a1/review/what-time-is-it-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/what-time-is-it.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • No Tier 1 (Beginner) review file at l2-uk-en/a1/review/what-time-is-it-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/what-time-is-it-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-time-is-it.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/what-time-is-it.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/what-time-is-it.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

