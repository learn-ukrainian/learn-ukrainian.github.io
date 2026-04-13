## Linguistic Scan
One factual grammar problem found:

- **Overgeneralized rule:** `Numbers 5 and above always require the Genitive plural... The numbers 2, 3, and 4... requiring the Nominative plural instead.`  
  This is too absolute as written. It needs to be scoped to the simple counting patterns practiced in this module.

## Exercise Check
- The prose has 4 markers, and they are placed after the relevant teaching sections: `quiz-mixed-grammar`, `fill-in-transformation`, `error-correction-mixed`, `fill-in-production`.
- The marker set broadly matches the 4 `activity_hints` in the plan.
- One publish-breaking mismatch exists: the prose contains `<!-- INJECT_ACTIVITY: error-correction-mixed -->`, but `activities/checkpoint-foundations.yaml` defines only 3 inline ids: `quiz-mixed-grammar`, `fill-in-transformation`, `fill-in-production`.
- Exercise logic is also weak in the generated YAML: `quiz-mixed-grammar` has all 10 correct answers at index `0`, and `fill-in-production` has all 10 answers in first position. That makes guessing by pattern trivial.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The required/recommended vocabulary is present, but the plan reference `Заболотний Grade 5-6` is never cited (`Заболотний` appears 0 times), and Part 3 gives only an English paraphrase instead of the plan’s learner-facing prompt `Напишіть про свої плани на вихідні. Що ви будете робити? Що ви хочете зробити?`. |
| 2. Linguistic accuracy | 7/10 | No Russianisms, Surzhyk, paronym misuse, or forbidden Russian characters were found, but the rule `Numbers 5 and above always require the Genitive plural... The numbers 2, 3, and 4... requiring the Nominative plural instead` is factually overbroad. |
| 3. Pedagogical quality | 7/10 | The module has many examples, but it opens with a long English preamble: `Learning a language requires stopping to review what you know... Mastering these forms moves you away from speaking in broken phrases...` before getting to learner tasks. For a checkpoint, that is too much abstract framing. |
| 4. Vocabulary coverage | 10/10 | All required plan words appear in prose: `вправа`, `перевірка`, `контрольна точка`, `завдання`, `текст`, `речення`, `відповідь`; recommended `правильний`, `варіант`, `обрати`, `написати` also appear. |
| 5. Exercise quality | 4/10 | The prose promises `<!-- INJECT_ACTIVITY: error-correction-mixed -->`, but the inline YAML has no such id; only `quiz-mixed-grammar`, `fill-in-transformation`, and `fill-in-production` exist. In addition, `quiz-mixed-grammar` has 10/10 correct answers at index 0. |
| 6. Engagement & tone | 7/10 | The teacher voice is not gamified, but lines like `Mastering these forms moves you away from speaking in broken phrases` and `This checkpoint confirms your solid understanding...` read as generic filler rather than specific instruction. |
| 7. Structural integrity | 9/10 | All planned H2 sections are present and ordered cleanly; formatting is intact; pipeline word count is 2493, so the module is safely above target. |
| 8. Cultural accuracy | 9/10 | No Russia-centering or cultural inaccuracies found. The module treats Ukrainian grammar on its own terms. |
| 9. Dialogue & conversation quality | 9/10 | The peer-study setup from the plan is preserved, the speakers are named, and both dialogues are multi-turn rather than transactional. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Numbers 5 and above always require the Genitive plural, or **родовий відмінок множини** (Genitive plural). The numbers 2, 3, and 4 act completely differently, requiring the Nominative plural instead.`  
Issue: This teaches an unqualified absolute rule. It needs to be limited to the simple counting patterns practiced in this module.  
Fix: Rewrite the paragraph so it explicitly says this is the pattern for the basic counting sentences in the module.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Learning a language requires stopping to review what you know... Mastering these forms moves you away from speaking in broken phrases and allows you to build complete, logical sentences.`  
Issue: The opening spends too much space on generic English framing and does not integrate the plan reference (`Заболотний Grade 5-6`) at all.  
Fix: Replace the paragraph with a shorter, task-specific checkpoint intro that cites the school-style source.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Learning a language requires stopping to review what you know...`  
Issue: The checkpoint begins with abstract motivational exposition instead of quickly moving into recognition and production tasks.  
Fix: Replace the paragraph with a concise description of the actual review sequence: recognize aspect, choose Genitive forms, then write short answers and a paragraph.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `The final writing prompt tests your ability to plan ahead and organize your thoughts. You will write a short paragraph about your plans for the weekend using both aspects naturally.`  
Issue: The plan’s exact learner-facing Ukrainian prompt is missing. Search confirms 0 occurrences of `Що ви будете робити?` and `Що ви хочете зробити?`.  
Fix: Replace this paragraph with the explicit Ukrainian writing prompt from the plan.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: prose marker `<!-- INJECT_ACTIVITY: error-correction-mixed -->`; `activities/checkpoint-foundations.yaml` inline ids are only `quiz-mixed-grammar`, `fill-in-transformation`, `fill-in-production`.  
Issue: One prose marker has no corresponding inline activity definition, so the promised error-correction activity will not inject.  
Fix: Add an inline `error-correction-mixed` block to `activities/checkpoint-foundations.yaml` with 6 items, matching the plan.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `activities/checkpoint-foundations.yaml`, blocks `quiz-mixed-grammar` and `fill-in-production`.  
Issue: Correct answers are patternable: `quiz-mixed-grammar` has all 10 correct answers at index `0`, and `fill-in-production` has all 10 answers first.  
Fix: Reorder options so correct answers do not sit in the same position throughout the block.

## Verdict: REVISE
REVISE. The module is structurally complete and mostly strong on vocabulary/dialogue, but it has one critical grammar overgeneralization, one missing inline activity mapping, and several plan/pedagogy mismatches. Multiple dimensions are below 9 with concrete fixes required.

<fixes>
- find: |-
    Learning a language requires stopping to review what you know. A **контрольна точка** (checkpoint) is precisely that moment in your journey. This module serves as a comprehensive **перевірка** (check) of the foundational grammar topics covered so far at the A2 level. You will deeply review how to navigate verb aspect, known as the **вид дієслова**, and how to master the Genitive case, or the **родовий відмінок**. Both of these grammatical systems are fundamental to speaking clearly and being understood by native speakers. Without them, you cannot accurately describe what happened yesterday, what will happen tomorrow, or what you currently do not have. Mastering these forms moves you away from speaking in broken phrases and allows you to build complete, logical sentences.
  replace: |-
    This checkpoint reviews two A2 foundations: verb aspect and the Genitive case. You will first recognize aspect pairs in context, then choose correct Genitive forms after `немає` and quantity words, and finally write short answers and a short paragraph that combine both topics. The review follows the same school-style practice used in sources such as Заболотний Grade 5-6.

- find: |-
    The Genitive case intersects heavily and predictably with numbers. Numbers 5 and above always require the Genitive plural, or **родовий відмінок множини** (Genitive plural). The numbers 2, 3, and 4 act completely differently, requiring the Nominative plural instead. This specific split in the number system is an ancient grammatical feature that you will use every single day when shopping or counting objects.
  replace: |-
    In the simple counting patterns practiced in this module, numbers 5 and above take the Genitive plural, or **родовий відмінок множини** (Genitive plural). The numbers 2, 3, and 4 usually take the plural counting forms you see in examples like «два брати», «три сестри», and «чотири яблука». This split is one of the core patterns you need for everyday counting and shopping language.

- find: |-
    The final writing prompt tests your ability to plan ahead and organize your thoughts. You will write a short paragraph about your plans for the weekend using both aspects naturally. Combine imperfective verbs for ongoing, continuous processes and perfective verbs for specific, completed goals. Mixing these aspects gives your writing much more depth, realistic pacing, and precision.
  replace: |-
    The final writing prompt is: **Напишіть про свої плани на вихідні. Що ви будете робити? Що ви хочете зробити?** Write 5-7 sentences and use both aspects naturally: imperfective verbs for ongoing or repeated actions, and perfective verbs for specific results you want to achieve.

- find: |-
      - sentence: Я купив п'ять червоних ____.
        answer: яблук
        options:
        - яблук
        - яблука
    workbook:
  replace: |-
      - sentence: Я купив п'ять червоних ____.
        answer: яблук
        options:
        - яблук
        - яблука
    - id: error-correction-mixed
      type: error-correction
      instruction: Знайдіть і виправте помилку
      items:
      - sentence: Я довго прочитав цю книгу.
        error: прочитав
        correction: читав
        error_type: word
        explanation: Слово «довго» вказує на процес (недоконаний вид).
        options:
        - читав
        - читає
        - почитав
      - sentence: Він прийшов без свій телефон.
        error: свій телефон
        correction: свого телефона
        error_type: phrase
        explanation: Після «без» потрібен родовий відмінок.
        options:
        - свого телефона
        - своєму телефону
        - своїм телефоном
      - sentence: Ми часто купили тут каву.
        error: купили
        correction: купували
        error_type: word
        explanation: «Часто» вказує на регулярну дію (недоконаний вид).
        options:
        - купували
        - купуємо
        - купимо
      - sentence: У кімнаті є шість великих вікна.
        error: вікна
        correction: вікон
        error_type: word
        explanation: Після «шість» потрібен родовий відмінок множини.
        options:
        - вікон
        - вікно
        - вікнам
      - sentence: Він швидко робив домашнє завдання за п'ять хвилин.
        error: робив
        correction: зробив
        error_type: word
        explanation: Результат дії за короткий час вимагає доконаного виду.
        options:
        - зробив
        - робив
        - зробить
      - sentence: Я потребую вашу допомогу.
        error: вашу допомогу
        correction: вашої допомоги
        error_type: phrase
        explanation: Дієслово «потребувати» вимагає родового відмінка.
        options:
        - вашої допомоги
        - вашій допомозі
        - вашою допомогою
    workbook:

- find: |-
      - question: У мене зараз немає ____ часу.
        options:
        - вільного
        - вільний
        - вільному
        - вільна
        correct: 0
  replace: |-
      - question: У мене зараз немає ____ часу.
        options:
        - вільний
        - вільному
        - вільного
        - вільна
        correct: 2

- find: |-
      - sentence: Вона шукала довго, але не знайшла ____.
        answer: ключів
        options:
        - ключів
        - ключі
  replace: |-
      - sentence: Вона шукала довго, але не знайшла ____.
        answer: ключів
        options:
        - ключі
        - ключів
</fixes>