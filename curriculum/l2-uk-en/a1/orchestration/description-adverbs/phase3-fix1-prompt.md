        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `description-adverbs`:

        ## Audit Output (last 60 lines)

        ```
          [GRAMMAR] Subordinate clause marker at A1: 'е, що в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'е коли м'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'якщо в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Якщо о'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Якщо в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'щоб н'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Щоб о'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'щоб п'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'українській мові як англійській велика...'
  [COMPLEXITY] Sentence too long for A1: 19 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Іноді якщо ви хочете зробити...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ми знаємо як сказати що...'
  [COMPLEXITY] Sentence too long for A1: 16 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Адже наше життя складається не...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ці слова стоять безпосередньо перед...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Коли ми йдемо ресторан або...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Зверніть увагу як вони використовують...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Коли ви щось робите ви...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Це синонім до слова часто...'
  [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ви можете сказати що ви...'
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: прикметник, дієслово
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 100/100)
   → 35 violations (severe - consider revision)
   → 24 grammar-level violations (fundamental)
   → Immersion 24% off target (major rebalancing needed)
   → Structure issue: Missing '## Summary'


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/description-adverbs-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/description-adverbs.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • Structure: Missing '## Summary'

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/description-adverbs-audit.log for details)

Prose-relevant failures:
  meta: Missing '## Summary'
  lesson: 1562/750 (raw: 1632) | pedagogy: 34 violations | immersion: 78.5% HIGH (target 35-55% (M28))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

