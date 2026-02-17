        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `weather-and-nature`:

        ## Audit Output (last 60 lines)

        ```
        Structure    ✅ Valid Structure
Ipa          ⚠️ 24 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 15 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Immersion    🇺🇦 44.3% (target 35-55% (M29))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [GRAMMAR] Dative case used at A1: 'мові'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Dative case used at A1: 'мові'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Dative case used at A1: 'нам'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Dative case used at A1: 'Вам'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Dative case used at A1: 'вам'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Dative case used at A1: 'Вам'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Instrumental case used at A1: 'з температурою'
     → FIX: Instrumental case not allowed until A2 (M36+). Restructure sentence.
  [GRAMMAR] Instrumental case used at A1: 'перед виходом'
     → FIX: Instrumental case not allowed until A2 (M36+). Restructure sentence.
  [GRAMMAR] Subordinate clause marker at A1: ', яка т'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'є, що у'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'и, що н'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'ь, що в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Якщо в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Щоб п'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Щоб поставити питання так ні...'
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: дієслово
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 70/100)
   → Revision recommended (severity 70/100)
   → 16 violations (severe - consider revision)
   → 14 grammar-level violations (fundamental)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/weather-and-nature-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/weather-and-nature.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/weather-and-nature-audit.log for details)

Prose-relevant failures:
  lesson: 1956/869 (raw: 2120) | pedagogy: 15 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/weather-and-nature.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

