        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `mine-and-yours`:

        ## Audit Output (last 60 lines)

        ```
             → FIX: Break into shorter sentences. First 5 words: 'Ми зробимо це крок за...'
  [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Тому що саме питання вже...'
  [COMPLEXITY] Sentence too long for A1: 20 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Якщо ви знаєте правильне питання...'
  [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Коли ми використовуємо присвійні займенники...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Це може здаватися складним на...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Якщо іменник робить крок жіночого...'
  [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Вони змінюються як хамелеони щоб...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Він працює точно так само...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ці слова теж змінюються за...'
  [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'українській мові слова які ніколи...'
  [COMPLEXITY] Sentence too long for A1: 17 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Використання форми їх наприклад це...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'якщо ви хочете сказати беру...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Коли ви хочете сказати ваш...'
  [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Це здається повільним зараз але...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'коли закінчення змінюється це не...'
  [COMPLEXITY] Sentence too long for A1: 18 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Якщо ви пишете імейл листівку...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Якщо ви пишете до групи...'
  [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ви показуєте що ви вчите...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Тепер ви знаєте як сказати...'
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: іменник, множина, прикметник, займенник
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
  [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'якщо ми...'.
     → FIX: Vary sentence structure.
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (11 occurrences): (Genitive case), (Masculine item), (Feminine item) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


🔄 RECOMMENDATION: REWRITE FROM SCRATCH (severity 100/100)
   → 52 violations (severe - consider revision)
   → 29 grammar-level violations (fundamental)
   → Immersion 41% off target (major rebalancing needed)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/mine-and-yours-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/mine-and-yours.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/mine-and-yours-audit.log for details)

Prose-relevant failures:
  lesson: 2451/2000 (raw: 2625) | pedagogy: 51 violations | immersion: 81.1% HIGH (target 25-40% (M14))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/mine-and-yours.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

