        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `health-basics`:

        ## Audit Output (last 60 lines)

        ```
             Вступ: Здоров’я — це скарб                    364 /  300  ✅ (+64)
     Частини тіла та анатомія                      401 /  500  ⚠️ (-99)
     Конструкція «У мене болить»: Граматика болю   818 /  700  ✅ (+118)
     Симптоми, хвороби та народна медицина         584 /  600  ✅ (-16)
     У поліклініці та аптеці                       425 /  500  ⚠️ (-75)
     Практика: Що трапилося?                       364 /  400  ✅ (-36)
     ────────────────────────────────────────────────────────────────────
     TOTAL                                        2956 / 3000  ❌ (-44)
  📋 Found YAML activities file (12 activities)
  > Частини тіла: 8 items (min 8)
  > Медична лексика: 8 items (min 8)
  > Однина чи множина?: 8 items (min 8)
  > Хворіти чи боліти?: 8 items (min 8)
  > Ваш фізичний стан: 8 items (min 8)
  > Медична культура в Україні: 8 items (min 8)
  > Виправте помилки: 6 items (min 6)
  > Складіть речення: 6 items (min 6)
  > Знайдіть частини тіла: 6 items (min 6)
  > Симптоми чи частини тіла?: 9 items (min 8)
  > Правда чи брехня?: 8 items (min 8)
  > Оберіть правильні фрази: 6 items (min 6)

--- STRICT GATES (Level A2) ---
Persona      ✅ Persona Defined
Words        ✅ 3315/3000 (raw: 3627)
Activities   ✅ 12/10
Density      ✅ All > 8
Unique_types ✅ 9/4 types
Priority     ✅ Priority types used
Engagement   ✅ 12/4
Audio        ℹ️ No audio
Vocab        ✅ 30/1
Structure    ✅ Valid Structure
Ipa          ✅ Clean IPA
Lint         ✅ Clean Format
Pedagogy     ❌ 2 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Research     ✅ Content aligned with research
Immersion    🇺🇦 73.7% (target 60-75% (A2.2))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [COMPLEXITY_WORD_COUNT] quiz 'Медична культура в Україні' Q2 prompt length 4 (target: 5-15)
     → FIX: Adjust prompt length to 5-15 words.
  [COMPLEXITY_WORD_COUNT] unjumble 'Складіть речення' item 3 has 3 words (target: 5-10)
     → FIX: Adjust sentence length to 5-10 words to match A2 complexity.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 2 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/health-basics-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/health-basics.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/health-basics-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/health-basics.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/health-basics.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/health-basics.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

