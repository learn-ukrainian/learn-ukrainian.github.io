        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `checkpoint-first-contact`:

        ## Audit Output (last 60 lines)

        ```
             → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Щоб в'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [GRAMMAR] Subordinate clause marker at A1: 'Щоб с'
     → FIX: Complex sentences not allowed at A1. Use simple SVO sentences.
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'не просто перевірка ваш пит...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Уявіть що ви тільки но...'
  [COMPLEXITY] Sentence too long for A1: 14 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ви вже знаєте літери можете...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ми постійно повертаємося до старого...'
  [COMPLEXITY] Sentence too long for A1: 19 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Пам ятайте що на цьому...'
  [COMPLEXITY] Sentence too long for A1: 20 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Вони можуть виглядати схоже на...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'вони можуть бути чоловічого він...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Такі слова таксі меню метро...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Деякі чоловічі імена та назви...'
  [COMPLEXITY] Sentence too long for A1: 12 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'першій групі інфінітив на ати...'
  [COMPLEXITY] Sentence too long for A1: 17 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Порядок слів може не змінюватися...'
  [COMPLEXITY] Sentence too long for A1: 16 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ця традиція йде від Юрія...'
  [COMPLEXITY] Sentence too long for A1: 11 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Тож коли ви єте віденську...'
  [COMPLEXITY] Sentence too long for A1: 13 words (max 10)
     → FIX: Break into shorter sentences. First 5 words: 'Ви можете сказати Дякую коли...'
  [METALANGUAGE] Metalanguage terms used but not in vocabulary: середній, рід, чоловічий, дієслово, жіночий
     → FIX: Add these grammar terms to vocabulary with translations, or use English equivalents.
  [LLM_FINGERPRINT_REPETITION] Repetitive LLM rhetorical patterns (4 total): 'не просто X, а Y' x4 — robotic prose
     → FIX: Vary sentence structures. Replace formulaic 'не просто X, а Y' with diverse rhetorical devices
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (4 occurrences): (He is not reading), (This is not a restaurant), (Thank you) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 70/100)
   → Revision recommended (severity 70/100)
   → 50 violations (severe - consider revision)
   → 33 grammar-level violations (fundamental)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/checkpoint-first-contact-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/checkpoint-first-contact.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 4 Outline Compliance Errors
  • Checkpoint Format Errors

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-first-contact-audit.log for details)

Prose-relevant failures:
  lesson: 2087/1500 (raw: 2317) | pedagogy: 49 violations
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-first-contact.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

