        # Fix Phase — full audit failures

        The following audit errors must be fixed for module `the-dative-ii-nouns`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  HETMAN VERIFY: the-dative-ii-nouns
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  the-dative-ii-nouns
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 3736/3000 (raw: 4068) | pedagogy: 1 violations | immersion: 49.8% LOW (target 50-60% (A2.1))
    activities: 12/10 | density: 1 < 12

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
    [YAML_SCHEMA_VIOLATION] Schema error in the-dative-ii-nouns.yaml: Schema validation error at key '11': {'type': 'select', 'title': 'Культурний контекст', 'instruction': 'Оберіть усі правильні твердження про етикет подарунків в Україні.', 'items': [{'question': 'Скільки квітів можна дарувати живій людині?', 'options': [{'text': 'Одну', 'correct': True}, {'text': 'Дві', 'correct': False}, {'text': 'Три', 'correct': True}, {'text': 'Чотири', 'correct': False}, {'text': "П'ять", 'correct': True}, {'text': 'Шість', 'correct': False}], 'min_correct': 3, 'explanation': 'Живим людям дарують тільки непарну кількість квітів (1, 3, 5...).'}, {'question': "Кому ми зазвичай кажемо 'Ви'?", 'options': [{'text': 'Учителю', 'correct': True}, {'text': 'Директору', 'correct': True}, {'text': 'Мамі', 'correct': False}, {'text': 'Лікарю', 'correct': True}, {'text': 'Собаці', 'correct': False}], 'min_correct': 3, 'explanation': "Ми звертаємося на 'Ви' до людей, яких поважаємо або мало знаємо."}, {'question': 'Які подарунки вважаються табу (погана прикмета)?', 'options': [{'text': 'Годинник', 'correct': True}, {'text': 'Книга', 'correct': False}, {'text': 'Ніж', 'correct': True}, {'text': 'Квіти', 'correct': False}], 'min_correct': 2, 'explanation': 'Годинники та гострі предмети (ножі) краще не дарувати, або брати за них символічну монету.'}, {'question': 'Яке дієслово вимагає Давального відмінка?', 'options': [{'text': 'Допомагати', 'correct': True}, {'text': 'Бачити', 'correct': False}, {'text': 'Телефонувати', 'correct': True}, {'text': 'Любити', 'correct': False}], 'min_correct': 2, 'explanation': 'Допомагати (кому?) і телефонувати (кому?) вимагають Давального відмінка.'}, {'question': "Як змінити слово 'Ольга' у Давальному відмінку?", 'options': [{'text': 'Ользі', 'correct': True}, {'text': 'Ольгі', 'correct': False}, {'text': 'Олзі', 'correct': False}, {'text': 'Бачити Ольгу', 'correct': False}], 'min_correct': 1, 'explanation': 'Правильна форма — Ользі (Г змінюється на З).'}, {'question': 'Кому ми даруємо жовті квіти з обережністю?', 'options': [{'text': 'Коханій дівчині', 'correct': True}, {'text': 'Колезі', 'correct': False}, {'text': 'Артисту', 'correct': False}, {'text': 'Нареченій', 'correct': True}], 'min_correct': 2, 'explanation': 'У романтичних стосунках жовтий колір може символізувати розлуку.'}]} is not valid under any of the given schemas
       → FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
     → 1 violations (minor)
     → Activity density below minimum


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/audit/the-dative-ii-nouns-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/status/the-dative-ii-nouns.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-dative-ii-nouns-audit.log for details)
        ```

        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-ii-nouns.md`
        - Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml`
        - Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/the-dative-ii-nouns.yaml`

        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.

