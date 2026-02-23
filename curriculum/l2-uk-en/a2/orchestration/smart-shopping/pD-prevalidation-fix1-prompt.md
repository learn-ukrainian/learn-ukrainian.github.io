        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `smart-shopping`:

        ## Audit Output (last 60 lines)

        ```
             Підсумок      401 /  400  ✅ (+1)
     ────────────────────────────────────
     TOTAL        3653 / 3000  ✅ (+653)
  📋 Found YAML activities file (12 activities)
  > Знайдіть пару: словник покупця: 8 items (min 8)
  > Розподіліть слова за категоріями: 10 items (min 8)
  > Знайдіть прикметники порівняння: 5 items (min 6)
  > Оберіть правильний варіант порівняння: 8 items (min 8)
  > Заповніть пропуски: фрази для шопінгу: 8 items (min 8)
  > Побудуйте правильні речення: 6 items (min 6)
  > Виправте граматичні помилки: 6 items (min 6)
  > Оберіть правильні варіанти: 6 items (min 6)
  > Правда чи брехня?: 8 items (min 8)
  > Оберіть правильний переклад: 6 items (min 6)
  > Заповніть пропуски в тексті: 14 items (min 8)
  > Доповніть фрази з ринку: 8 items (min 8)

📊 ACTIVITIES WITH LOW DENSITY:
  ❌ Знайдіть прикметники порівняння
     Current: 5 items | Required: 6 | Add: 1 more
     → Add 1 more words to mark in the text


--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 3850/3000 (raw: 4091)
Activities   ✅ 12/10
Density      ❌ 1 < 8
Unique_types ✅ 11/4 types
Priority     ✅ Priority types used
Engagement   ✅ 8/4
Audio        ℹ️ No audio
Vocab        ✅ 25/1
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Research     ✅ Content aligned with research
Immersion    🇺🇦 68.7% (target 60-75% (A2.2))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY] mark-the-words 'Знайдіть прикметники порівняння' has 5 items (minimum: 6)
     → FIX: Add more items. A2 mark-the-words requires at least 6 items.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 1 violations (minor)
   → Activity density below minimum


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/smart-shopping-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/smart-shopping.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/smart-shopping-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/smart-shopping.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/smart-shopping.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/smart-shopping.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

