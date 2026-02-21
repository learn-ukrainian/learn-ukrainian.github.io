        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `being-and-becoming`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: being-and-becoming
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  being-and-becoming
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  No Tier 1 (Beginner) review file at l2-uk-en/a2/review/being-and-becoming-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
  failing gates:
    review: No Tier 1 (Beginner) review file at l2-uk-en/a2/review/being-and-becoming-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/being-and-becoming-audit.md
    🕵️  Review Validation: 1 critical, 0 warnings
       ❌ [MISSING_REVIEW] No Tier 1 (Beginner) review file at l2-uk-en/a2/review/being-and-becoming-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/being-and-becoming.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • No Tier 1 (Beginner) review file at l2-uk-en/a2/review/being-and-becoming-review.md. REDO: DELETE the existing review file and regenerate from scratch. Run /review-content-core-a using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence + IPA transcription, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/being-and-becoming-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/being-and-becoming.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

