        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `yesterday-past-tense`:

        ## Audit Output (last 60 lines)

        ```
             Граматика: Минулий час дієслів   877 / 1000  ⚠️ (-123)
     Практика: Спогади про вчора      393 /  600  ❌ (-207)
     ───────────────────────────────────────────────────────
     TOTAL                           1758 / 2000  ❌ (-242)
  ⏳ Content-only audit: activities/vocab gates DEFERRED

📚 IMMERSION TOO LOW (18.8% vs 35-55% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2001/2000 (raw: 2309)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 6/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 4 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 3 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 18.8% LOW (target 35-55% (M21))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [GRAMMAR] Perfective aspect used at A1: 'зробив'
     → FIX: Use imperfective forms at A1. Perfective taught at A2+.
  [GRAMMAR] Perfective aspect used at A1: 'надрукував'
     → FIX: Use imperfective forms at A1. Perfective taught at A2+.
  [GRAMMAR] Perfective aspect used at A1: 'зробив'
     → FIX: Use imperfective forms at A1. Perfective taught at A2+.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 45/100)
   → Revision recommended (severity 45/100)
   → 3 violations (minor)
   → 3 grammar-level violations (fundamental)
   → Immersion 16% off target


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/yesterday-past-tense-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/yesterday-past-tense.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 1 Outline Compliance Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/yesterday-past-tense-audit.log for details)

Prose-relevant failures:
  lesson: 2001/2000 (raw: 2309) | pedagogy: 3 violations | immersion: 18.8% LOW (target 35-55% (M21))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/yesterday-past-tense.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

