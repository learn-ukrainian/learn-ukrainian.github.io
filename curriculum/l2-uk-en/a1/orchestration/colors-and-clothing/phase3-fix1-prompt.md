        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `colors-and-clothing`:

        ## Audit Output (last 60 lines)

        ```
             → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Dative case used at A1: 'вам'
     → FIX: Dative case not allowed until A2 (M31+). Restructure sentence.
  [GRAMMAR] Participle used before B1: 'улюблений'
     → FIX: Participles not allowed until B1. Use relative clauses or simple sentences.
  [GRAMMAR] Subordinate clause marker at A1: ', які в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'ь, що в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'ь, що м'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'о що н'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'р, коли м'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'ь коли й'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Якщо ц'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'якщо ц'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Щоб р'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Тепер коли ми знаємо кольори...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Уявіть що ви Києві на...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Після неї ми використовуємо слово...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Якщо це чоловічий рід неістота...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ви часто побачите жінок елегантних...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Коли ви говорите про те...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ви можете описати себе ви...'
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: дієслово
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.


🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 90/100)
   → 20 violations (severe - consider revision)
   → 12 grammar-level violations (fundamental)
   → Structure issue: Missing '## Summary'


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/colors-and-clothing-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/colors-and-clothing.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • Structure: Missing '## Summary'

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/colors-and-clothing-audit.log for details)

Prose-relevant failures:
  meta: Missing '## Summary'
  lesson: 1867/750 (raw: 1961) | pedagogy: 19 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

