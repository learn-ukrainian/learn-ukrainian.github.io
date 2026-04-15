## Linguistic Scan
No linguistic errors found.

## Exercise Check
- Four markers are present and logically placed: one `<!-- INJECT_ACTIVITY: fill-in -->` after `## Хотіти (To Want)`, two markers after `## Могти і мусити (Can and Must)`, and one `<!-- INJECT_ACTIVITY: quiz -->` after `## Підсумок — Summary`.
- The marker sequence matches the planned exercise flow at a high level: conjugation after `хотіти`, mixed modal practice after `могти/мусити`, then a final review quiz.
- `curriculum/l2-uk-en/a1/activities/i-want-i-can.yaml` has a real exercise-quality problem: both quiz blocks put every correct answer at index `0`, so the answer key is predictable.
- The first quiz title in that same YAML is also broken: it ends as `title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу**\n    (ab'`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Core beats are covered well: `Що ти хочеш робити сьогодні?`, café `Я хочу каву... Що ви можете порекомендувати?`, full paradigms for `хотіти / могти / мусити`, and the anchor `Я хочу гуляти, але не можу — мушу працювати.` The miss is pacing: `## Підсумок — Summary` is 257 words in the live module, below the contract minimum of 270. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym misuse, bad case endings, or false grammar claims surfaced in the Ukrainian text. |
| 3. Pedagogical quality | 9/10 | The module follows a solid teach-then-practice flow: dialogue context, paradigm explanation, then guided production with examples like `Я хочу каву.`, `Я можу говорити українською.`, `Я мушу працювати.` |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is integrated naturally in prose: `хочеш`, `робити`, `гуляти`, `можу`, `мушу`, `працювати`, `Шкода`, `каву`, `їсти`. |
| 5. Exercise quality | 6/10 | Marker placement is fine, but both quiz blocks in `activities/i-want-i-can.yaml` use `correct: 0` for every item, and the first quiz title is truncated to `(ab'`, which makes the exercise set look mechanically generated and easy to game. |
| 6. Engagement & tone | 9/10 | The tone stays teacherly and concrete, especially in the weekend-planning and café scenarios and the contrast `Я хочу каву` vs `Я хочу їсти`. |
| 7. Structural integrity | 8/10 | Headings are correct and ordered, marker syntax is clean, and the pipeline total is 1241 words, but `## Підсумок — Summary` underfills its section budget. |
| 8. Cultural accuracy | 10/10 | No Russia-centering, no fabricated cultural claims, and no misleading “like Russian” framing. |
| 9. Dialogue & conversation quality | 9/10 | The main dialogue is multi-turn and functional rather than interrogative, with named speakers and natural planning turns like `Я не можу, я мушу працювати. — Шкода! А завтра?` |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Підсумок — Summary` — from `Throughout this module, you have seen three core patterns...` to `Repeat the pattern aloud until you can switch quickly...`  
Issue: The summary section is only 257 words in the live module, below the contract minimum of 270 words for this section.  
Fix: Add one short practice paragraph with 2-3 Ukrainian model sentences and one extra guided prompt so the section lands inside the 270-330 word band without changing scope.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `curriculum/l2-uk-en/a1/activities/i-want-i-can.yaml` — first quiz block `correct: 0` on all 8 items and broken title `title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу** ... (ab'`; final quiz block `correct: 0` on all 6 items.  
Issue: The answer key is fully predictable by position, and the first quiz title is truncated. That weakens assessment validity and looks broken in the published exercise set.  
Fix: Shuffle options in both quiz blocks so the correct answer position varies, and replace the broken first quiz title with the full intended string.

## Verdict: REVISE
REVISE — there are fixable but real issues, and dimensions 1, 5, and 7 fall below 9. The prose is linguistically safe, but the summary underfills the contract and the exercise YAML has broken/predictable quiz metadata.

<fixes>
- insert_after: |
    * Say what you must do tomorrow. Do you have a strict obligation to work all day, or to help a close friend? Then add one noun pattern too: **Я хочу каву.** Contrast it with **Я хочу їсти.** Say the full chain aloud: **Я хочу гуляти, але не можу — мушу працювати.** Then ask a partner: **Що ти хочеш робити сьогодні? Що ти можеш робити сьогодні? Що ти мусиш робити завтра?**
  text: |
    * Build two more model sentences aloud: **Я хочу каву, але не можу пити зараз — мушу працювати.** **Ми хочемо гуляти, але не можемо — мусимо вчити слова.** Then switch the subject each time: **я**, **ти**, **ми**. This keeps the three patterns together and reinforces the contrast between **хочу**, **можу**, and **мушу** before you move on.
- find: |
    - id: quiz
      type: quiz
      instruction: 'Choose the correct modal verb for the situation: **хочу** (desire),
        **можу** (ability), or **мушу** (obligation).'
      items:
      - question: Завтра я вільна. Я ____ піти в кіно.
        options:
        - можу
        - мушу
        - хочу
        correct: 0
      - question: Добрий день! Що ви ____?
        options:
        - хочете
        - можете
        - мусите
        correct: 0
      - question: Я не можу, я ____ працювати.
        options:
        - мушу
        - можу
        - хочу
        correct: 0
      - question: Що ви ____ порекомендувати?
        options:
        - можете
        - мусите
        - хочете
        correct: 0
      - question: Вона дуже любить чай. Вона ____ чай.
        options:
        - хоче
        - може
        - мусить
        correct: 0
      - question: Ти знаєш українські слова. Ти ____ читати.
        options:
        - можеш
        - хочеш
        - мусиш
        correct: 0
      - question: Завтра тест. Я ____ вчити слова.
        options:
        - мушу
        - можу
        - хочу
        correct: 0
      - question: Сьогодні ми вільні. Ми ____ гуляти.
        options:
        - можемо
        - мусимо
        - хочемо
        correct: 0
      title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу**
        (ab'
  replace: |
    - id: quiz
      type: quiz
      instruction: 'Choose the correct modal verb for the situation: **хочу** (desire),
        **можу** (ability), or **мушу** (obligation).'
      items:
      - question: Завтра я вільна. Я ____ піти в кіно.
        options:
        - хочу
        - мушу
        - можу
        correct: 2
      - question: Добрий день! Що ви ____?
        options:
        - можете
        - хочете
        - мусите
        correct: 1
      - question: Я не можу, я ____ працювати.
        options:
        - можу
        - мушу
        - хочу
        correct: 1
      - question: Що ви ____ порекомендувати?
        options:
        - хочете
        - можете
        - мусите
        correct: 1
      - question: Вона дуже любить чай. Вона ____ чай.
        options:
        - може
        - хоче
        - мусить
        correct: 1
      - question: Ти знаєш українські слова. Ти ____ читати.
        options:
        - хочеш
        - мусиш
        - можеш
        correct: 2
      - question: Завтра тест. Я ____ вчити слова.
        options:
        - мушу
        - можу
        - хочу
        correct: 0
      - question: Сьогодні ми вільні. Ми ____ гуляти.
        options:
        - хочемо
        - можемо
        - мусимо
        correct: 1
      title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу**
        (ability), or **мушу** (obligation).'
- find: |
    - id: quiz
      type: quiz
      instruction: Identify the correct conjugation pattern for the verbs.
      items:
      - question: 'Choose the correct forms of **хотіти** (to want):'
        options:
        - я хочу, ти хочеш
        - я хочю, ти хочеш
        - я хоту, ти хотиш
        correct: 0
      - question: 'Choose the correct forms of **могти** (can):'
        options:
        - я можу, ти можеш
        - я могу, ти могиш
        - я можю, ти можиш
        correct: 0
      - question: 'Choose the correct forms of **мусити** (must):'
        options:
        - я мушу, ти мусиш
        - я мусу, ти мусиш
        - я мушу, ти мушиш
        correct: 0
      - question: Which sentence is grammatically correct?
        options:
        - Він хоче їсти.
        - Він хотить їсти.
        - Він хочу їсти.
        correct: 0
      - question: Which sentence is grammatically correct?
        options:
        - Ми можемо допомогти.
        - Ми могем допомогти.
        - Ми можимо допомогти.
        correct: 0
      - question: Which sentence is grammatically correct?
        options:
        - Вони мусять працювати.
        - Вони мушать працювати.
        - Вони мусять працювать.
        correct: 0
      title: Identify the correct conjugation pattern for the verbs.
  replace: |
    - id: quiz
      type: quiz
      instruction: Identify the correct conjugation pattern for the verbs.
      items:
      - question: 'Choose the correct forms of **хотіти** (to want):'
        options:
        - я хоту, ти хотиш
        - я хочу, ти хочеш
        - я хочю, ти хочеш
        correct: 1
      - question: 'Choose the correct forms of **могти** (can):'
        options:
        - я могу, ти могиш
        - я можю, ти можиш
        - я можу, ти можеш
        correct: 2
      - question: 'Choose the correct forms of **мусити** (must):'
        options:
        - я мушу, ти мусиш
        - я мусу, ти мусиш
        - я мушу, ти мушиш
        correct: 0
      - question: Which sentence is grammatically correct?
        options:
        - Він хотить їсти.
        - Він хочу їсти.
        - Він хоче їсти.
        correct: 2
      - question: Which sentence is grammatically correct?
        options:
        - Ми можемо допомогти.
        - Ми могем допомогти.
        - Ми можимо допомогти.
        correct: 0
      - question: Which sentence is grammatically correct?
        options:
        - Вони мусять працювать.
        - Вони мушать працювати.
        - Вони мусять працювати.
        correct: 2
      title: Identify the correct conjugation pattern for the verbs.
</fixes>