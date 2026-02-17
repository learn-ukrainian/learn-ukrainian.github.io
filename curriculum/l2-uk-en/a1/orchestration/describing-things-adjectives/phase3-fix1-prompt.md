        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `describing-things-adjectives`:

        ## Audit Output (last 60 lines)

        ```

  📊 Section Word Analysis:
     Основи: Рід і число прикметників            647 /  302  ✅ (+345)
     Характеристики: Опис предметів і простору   660 /  272  ✅ (+388)
     Практика: Діалоги про речі                  394 /  279  ✅ (+115)
     ──────────────────────────────────────────────────────────────────
     TOTAL                                      1701 /  853  ✅ (+848)
❌ Structure check failed: Missing '## Summary'
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (17.0% vs 35-55% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1603/853 (raw: 1836)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 3/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ❌ Missing '## Summary'
Ipa          ⚠️ 19 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Immersion    ❌ 17.0% LOW (target 35-55% (M26))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: прикметник
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 45/100)
   → Revision recommended (severity 45/100)
   → 1 violations (minor)
   → Immersion 18% off target
   → Structure issue: Missing '## Summary'


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/describing-things-adjectives-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/describing-things-adjectives.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • Structure: Missing '## Summary'

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/describing-things-adjectives-audit.log for details)

Prose-relevant failures:
  meta: Missing '## Summary'
  lesson: 1603/853 (raw: 1836) | immersion: 17.0% LOW (target 35-55% (M26))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/describing-things-adjectives.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

