        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `body-and-health`:

        ## Audit Output (last 60 lines)

        ```
             → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: ', які в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'ь, що в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'є, що ф'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'ь, що в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'ь
Коли в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'а, коли у'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'в, коли х'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Якщо б'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Якщо б'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'якщо у'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'бо я'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Щоб п'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'щоб н'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Щоб пояснити проблему лікарю або...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Запам ятайте ці слова адже...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Це означає що фізичне здоров...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ви можете запитати про допомогу...'
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: множина, однина, дієслово, займенник
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 100/100)
   → 35 violations (severe - consider revision)
   → 30 grammar-level violations (fundamental)
   → Immersion 23% off target (major rebalancing needed)
   → Structure issue: Missing '## Summary'


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/body-and-health-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/body-and-health.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • Structure: Missing '## Summary'

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/body-and-health-audit.log for details)

Prose-relevant failures:
  meta: Missing '## Summary'
  lesson: 1803/820 (raw: 1956) | pedagogy: 34 violations | immersion: 78.2% HIGH (target 35-55% (M31))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

