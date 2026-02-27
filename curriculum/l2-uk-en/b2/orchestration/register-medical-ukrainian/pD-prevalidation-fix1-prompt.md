        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `register-medical-ukrainian`:

        ## Audit Output (last 60 lines)

        ```
          > Заповніть пропуски у медичних діалогах: 10 items (min 8)
  > Складіть медичні речення: 8 items (min 6)
  > Виправте мовні помилки та русизми: 8 items (min 6)
  > Правда чи хиба: правила медичного спілкування: 10 items (min 8)
  > Переклад медичних висловів: 8 items (min 6)
  > Оберіть усі правильні варіанти: 8 items (min 6)
  > Знайдіть відповідники: типи болю та їх опис: 10 items (min 8)
  > Первинне джерело: Філософія здоров`я Миколи Амосова: 3 items (min 3)
  > Опис симптомів для візиту до лікаря: 1 items (min 1)
  > Розподіліть слова за значенням: Відділ чи Відділення: 10 items (min 14)
  > Заповніть пропуски: Від перших симптомів до лікування: 16 items (min 14)

📊 ACTIVITIES WITH LOW DENSITY:
  ❌ Розподіліть слова за значенням: Відділ чи Відділення
     Current: 10 items | Required: 14 | Add: 4 more
     → Add 4 more items to sort into categories


--- STRICT GATES (Level B2) ---
Persona      ✅ Persona Defined
Words        ✅ 5956/4000 (raw: 6241)
Activities   ✅ 12/10
Density      ❌ 1 < 14
Unique_types ✅ 12/4 types
Priority     ✅ Priority types used
Engagement   ✅ 8/6
Audio        ℹ️ No audio
Vocab        ✅ 30/25
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 3 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality 📋 Quality validation available (optional)
Research     ✅ Content aligned with research
Immersion    🇺🇦 98.7% (target 90-100% (grammar))
Richness     ✅ 99% (style)

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY] match-up 'Знайдіть відповідники: типи болю та їх опис' has 10 pairs (target: 12-16)
     → FIX: Adjust number of pairs to 12-16.
  [COMPLEXITY] group-sort 'Розподіліть слова за значенням: Відділ чи Відділення' has 2 groups (target: 3-5)
     → FIX: Adjust number of sorting categories to 3-5.
  [COMPLEXITY] group-sort 'Розподіліть слова за значенням: Відділ чи Відділення' has 10 items (target: 14-999)
     → FIX: Adjust number of items to sort to 14-999.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
   → 3 violations (minor)
   → Activity density below minimum


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/audit/register-medical-ukrainian-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/status/register-medical-ukrainian.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/register-medical-ukrainian-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/register-medical-ukrainian.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/activities/register-medical-ukrainian.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b2/vocabulary/register-medical-ukrainian.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

