        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `bigger-better-stronger`:

        ## Audit Output (last 60 lines)

        ```
          📋 Required activity types from meta: fill-in, match-up, quiz
  📋 Template: docs/l2-uk-en/templates/a2-module-template.md (pedagogy: PPP)

  📊 Section Word Analysis:
     Вступ: Арена порівняння           441 /  500  ⚠️ (-59)
     Презентація: Творення ступенів    737 /  800  ✅ (-63)
     Структури порівняння: ніж vs за   770 /  700  ✅ (+70)
     Практика: Рекорди України         738 /  600  ✅ (+138)
     Діалоги та Висновки               328 /  400  ⚠️ (-72)
     ────────────────────────────────────────────────────────
     TOTAL                            3014 / 3000  ✅ (+14)
  📋 Found YAML activities file (11 activities)
  > Знайдіть пару: прикметник і ступінь порівняння: 12 items (min 8)
  > Знайдіть пару: антоніми: 8 items (min 8)
  > Тест: Яка форма правильна?: 8 items (min 8)
  > Заповніть пропуски: форми прикметників: 8 items (min 8)
  > Складіть речення: 6 items (min 6)
  > Правда чи брехня?: 8 items (min 8)
  > Виправте помилки: 6 items (min 6)
  > Розподіліть слова за типом творення порівняння: 8 items (min 8)
  > Знайдіть ступені порівняння: 6 items (min 6)
  > Коментатор на стадіоні: 10 items (min 8)
  > Оберіть правильні варіанти: 6 items (min 6)

--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 3331/3000 (raw: 3617)
Activities   ✅ 11/10
Density      ✅ All > 8
Unique_types ✅ 10/4 types
Priority     ✅ Priority types used
Engagement   ✅ 8/4
Audio        ℹ️ No audio
Vocab        ✅ 2/1
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Research     ✅ Content aligned with research
Immersion    🇺🇦 52.9% (target 50-60% (A2.1))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY_WORD_COUNT] quiz 'Тест: Яка форма правильна?' Q4 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/bigger-better-stronger-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/bigger-better-stronger.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/bigger-better-stronger-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/bigger-better-stronger.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/bigger-better-stronger.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/bigger-better-stronger.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

