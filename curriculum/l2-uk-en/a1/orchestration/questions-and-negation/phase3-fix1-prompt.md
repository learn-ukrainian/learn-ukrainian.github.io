        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `questions-and-negation`:

        ## Audit Output (last 60 lines)

        ```
             Вступ: Мистецтво ставити питання              433 /  300  ✅ (+133)
     Граматика: Питальні речення                   706 /  800  ⚠️ (-94)
     Практика: Інтонація та конструктор            293 /  400  ❌ (-107)
     Застосування: Діалоги в кафе                  263 /  300  ⚠️ (-37)
     Культурний контекст: Від «Альфа» до етикету   214 /  200  ✅ (+14)
     ────────────────────────────────────────────────────────────────────
     TOTAL                                        1909 / 2000  ❌ (-91)
  ⏳ Content-only audit: activities/vocab gates DEFERRED
  ✨ Purity violations found: 1
     ❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'find the...'.
  ✨ Prose quality violations found: 1
     ❌ [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (9 occurrences): (Word order is flexible), (Pitch goes down), (Pitch goes up high) — breaks immersion target

📚 IMMERSION TOO LOW (7.8% vs 15-35% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 2287/2000 (raw: 2456)
Activities   ⏳ Deferred (content-only audit)
Density      ⏳ Deferred (content-only audit)
Unique_types ⏳ Deferred (content-only audit)
Priority     ⏳ Deferred (content-only audit)
Engagement   ✅ 4/3
Audio        ℹ️ No audio
Vocab        ⏳ Deferred (content-only audit)
Structure    ✅ Valid Structure
Ipa          ⚠️ 9 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ⏳ Deferred (content-only audit)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ⏳ Deferred (content-only audit)
Research     ✅ Content aligned with research
Immersion    ❌ 7.8% LOW (target 15-35% (M07))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'find the...'.
     → FIX: Vary sentence structure.
  [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (9 occurrences): (Word order is flexible), (Pitch goes down), (Pitch goes up high) — breaks immersion target
     → FIX: Remove inline English translations. Use context clues, Ukrainian definitions, or move translations to vocabulary section


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 2 violations (minor)
   → Immersion 7% off target (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/questions-and-negation-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/questions-and-negation.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/questions-and-negation-audit.log for details)

Prose-relevant failures:
  lesson: 2287/2000 (raw: 2456) | pedagogy: 2 violations | immersion: 7.8% LOW (target 15-35% (M07))
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

