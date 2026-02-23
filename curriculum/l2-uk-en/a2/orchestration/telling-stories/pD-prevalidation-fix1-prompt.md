        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `telling-stories`:

        ## Audit Output (last 60 lines)

        ```
             Продукція та підсумок                525 /  600  ⚠️ (-75)
     ───────────────────────────────────────────────────────────
     TOTAL                               4359 / 3000  ✅ (+1359)
  📋 Found YAML activities file (12 activities)
  > Знайдіть переклад: 8 items (min 8)
  > Правда чи брехня?: 8 items (min 8)
  > Оберіть правильне слово: 8 items (min 8)
  > Виправте помилки в реченнях: 6 items (min 6)
  > Перевірте свої знання: 8 items (min 8)
  > Складіть правильні речення: 6 items (min 6)
  > Розподіліть слова за значенням: 8 items (min 8)
  > Оберіть усі правильні варіанти: 6 items (min 6)
  > Знайдіть маркери часу: 5 items (min 6)
  > Побудуйте речення з новими словами: 6 items (min 6)
  > Перекладіть українською: 6 items (min 6)
  > Заповніть пропуски в історії: 10 items (min 8)

📊 ACTIVITIES WITH LOW DENSITY:
  ❌ Знайдіть маркери часу
     Current: 5 items | Required: 6 | Add: 1 more
     → Add 1 more words to mark in the text


--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 4701/3000 (raw: 4957)
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
Immersion    🇺🇦 72.7% (target 60-75% (A2.2))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY] mark-the-words 'Знайдіть маркери часу' has 5 items (minimum: 6)
     → FIX: Add more items. A2 mark-the-words requires at least 6 items.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 1 violations (minor)
   → Activity density below minimum


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/telling-stories-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/telling-stories.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/telling-stories-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/telling-stories.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/telling-stories.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/telling-stories.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

