        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `ready-for-immersion`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: ready-for-immersion
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  ready-for-immersion
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  Review has only 2 Ukrainian citation(s) for 4930-word content (need at least 8). A proper review must cite specific Ukrainian sentences from the content to support its assessment. Quote the actual text with «» or "".
  Review only covers 1/10 (10%) content sections. Missed: Вступ: Нові правила гри, Діагностика: Що ми пам'ятаємо?, Система мови: Частини мови, Дієслово: Час і Вид, Стилістика: Як читати правила. A thorough review must address each major section of the content.
  Review is missing 'Reviewed-By:' metadata. Re-run Phase D to generate a review with proper provenance.
  failing gates:
    review: Review has only 2 Ukrainian citation(s) for 4930-word content (need at least 8). A proper review must cite specific Ukrainian sentences from the content to support its assessment. Quote the actual text with «» or "".

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    🎭 Review Gaming: 3 critical, 1 warnings
       ❌ [LOW_CITATION_DENSITY] Review has only 2 Ukrainian citation(s) for 4930-word content (need at least 8). A proper review must cite specific Ukrainian sentences from the content to support its assessment. Quote the actual text with «» or "".
       ❌ [REVIEW_LOW_SECTION_COVERAGE] Review only covers 1/10 (10%) content sections. Missed: Вступ: Нові правила гри, Діагностика: Що ми пам'ятаємо?, Система мови: Частини мови, Дієслово: Час і Вид, Стилістика: Як читати правила. A thorough review must address each major section of the content.
       ❌ [MISSING_REVIEWER_ID] Review is missing 'Reviewed-By:' metadata. Re-run Phase D to generate a review with proper provenance.
       ⚠️  [PHANTOM_SECTION_REFERENCE] Review references 1 section(s) not found in content: 'Минулий час'. Verify section names match actual content headers.
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/ready-for-immersion.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  Critical Failures:
    • Review has only 2 Ukrainian citation(s) for 4930-word content (need at least 8). A proper review must cite specific Ukrainian sentences from the content to support its assessment. Quote the actual text with «» or "".
    • Review only covers 1/10 (10%) content sections. Missed: Вступ: Нові правила гри, Діагностика: Що ми пам'ятаємо?, Система мови: Частини мови, Дієслово: Час і Вид, Стилістика: Як читати правила. A thorough review must address each major section of the content.
    • Review is missing 'Reviewed-By:' metadata. Re-run Phase D to generate a review with proper provenance.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/ready-for-immersion-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/ready-for-immersion.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/ready-for-immersion.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/ready-for-immersion.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

