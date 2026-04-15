## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or banned Russian characters found. The VESUM misses are proper names (`Оля`, `Денис`, `Денисе`) plus the stem fragment `хот`, so they are not errors.

Grammar overstatement: in [i-want-i-can.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/i-want-i-can.md:52), `Never place it before the infinitive verb.` is too absolute. For A1, the module should teach the target pattern `Я не хочу...` without turning it into a universal ban.

## Exercise Check
Four markers are present in the module, in the required order: `fill-in → quiz → fill-in → quiz`. The marker count matches the contract.

The logic issue is in the generated quiz YAML, not the marker placement: both quiz blocks in [i-want-i-can.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/i-want-i-can.yaml:64) and [i-want-i-can.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/i-want-i-can.yaml:160) put every correct answer at `correct: 0`, so learners can game them by always choosing the first option.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Core beats are covered well: `Що ти хочеш робити?... Я не можу, я мушу працювати`, the café preview includes `Я хочу каву` and `Що ви можете порекомендувати?`, and the summary uses `Я хочу гуляти, але не можу — мушу працювати.` The contract miss is the deterministic pipeline count: 1176, below the 1200 target. |
| 2. Linguistic accuracy | 8/10 | Most Ukrainian is solid, but `Never place it before the infinitive verb.` teaches an absolute rule the module cannot safely defend. |
| 3. Pedagogical quality | 8/10 | The module usually gives examples after rules, but the negation explanation is over-absolute and the summary would be stronger with one more concrete `хочу + noun` vs `хочу + infinitive` practice turn. |
| 4. Vocabulary coverage | 9/10 | Required core items appear naturally in prose: `хочеш`, `робити`, `хочу`, `гуляти`, `можу`, `мушу`, `працювати`, `Шкода`, `каву`, `їсти`. |
| 5. Exercise quality | 6/10 | Marker count/order is correct, but both generated quizzes are mechanically guessable because every item has `correct: 0`. |
| 6. Engagement & tone | 9/10 | Teacherly and calm, with no gamified or self-congratulatory nonsense. |
| 7. Structural integrity | 7/10 | All four H2 headings are present and ordered correctly, but the pipeline word count is 1176, below target. |
| 8. Cultural accuracy | 10/10 | No Russian-centered framing, no cultural distortions, no bad comparative framing. |
| 9. Dialogue & conversation quality | 9/10 | Named speakers, multi-turn exchanges, and real situations. The café dialogue is a bit scripted, but still usable. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: [i-want-i-can.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/i-want-i-can.md:52) — `To express that you do not want something, place the negative particle **не** (not) directly before the conjugated modal verb. Never place it before the infinitive verb.`  
Issue: The beginner pattern `Я не хочу...` is correct, but `Never place it before the infinitive verb` is an unsafe absolute rule.  
Fix: Replace the absolute ban with an A1-scoped instruction that teaches the target pattern without using `never`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: [i-want-i-can.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/i-want-i-can.yaml:64) and [i-want-i-can.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/i-want-i-can.yaml:160) — every quiz item uses `correct: 0`  
Issue: Both quizzes are guessable by position rather than knowledge.  
Fix: Shuffle option order and update `correct` indices so the right answer appears in different slots.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Pipeline note — `Word count: 1176 words`  
Issue: The module misses the 1200-word contract target. The cleanest repair is to add a short, useful practice block instead of more English filler.  
Fix: Insert one concrete practice turn in the summary that contrasts `Я хочу каву` with `Я хочу їсти` and reuses the three-modal anchor sentence.

## Verdict: REVISE
REVISE — there is a critical grammar overstatement, the quizzes are mechanically guessable, and the module is still below the 1200-word contract target.

<fixes>
- find: "To express that you do not want something, place the negative particle **не** (not) directly before the conjugated modal verb. Never place it before the infinitive verb."
  replace: "To express the basic A1 idea \"I do not want...\", place the negative particle **не** (not) directly before the conjugated form of **хотіти**: **Я не хочу гуляти.** In this module, keep that pattern as your model."
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
        - мушу
        - можу
        - хочу
        correct: 1
      - question: Добрий день! Що ви ____?
        options:
        - можете
        - мусите
        - хочете
        correct: 2
      - question: Я не можу, я ____ працювати.
        options:
        - мушу
        - можу
        - хочу
        correct: 0
      - question: Що ви ____ порекомендувати?
        options:
        - хочете
        - мусите
        - можете
        correct: 2
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
        - мусимо
        - хочемо
        - можемо
        correct: 2
      title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу**
        (ab'
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
        - я хочю, ти хочеш
        - я хочу, ти хочеш
        - я хоту, ти хотиш
        correct: 1
      - question: 'Choose the correct forms of **могти** (can):'
        options:
        - я можю, ти можиш
        - я могу, ти могиш
        - я можу, ти можеш
        correct: 2
      - question: 'Choose the correct forms of **мусити** (must):'
        options:
        - я мушу, ти мусиш
        - я мушу, ти мушиш
        - я мусу, ти мусиш
        correct: 0
      - question: Which sentence is grammatically correct?
        options:
        - Він хочу їсти.
        - Він хотить їсти.
        - Він хоче їсти.
        correct: 2
      - question: Which sentence is grammatically correct?
        options:
        - Ми могем допомогти.
        - Ми можемо допомогти.
        - Ми можимо допомогти.
        correct: 1
      - question: Which sentence is grammatically correct?
        options:
        - Вони мушать працювати.
        - Вони мусять працювать.
        - Вони мусять працювати.
        correct: 2
      title: Identify the correct conjugation pattern for the verbs.
- insert_after: "* Say what you must do tomorrow. Do you have a strict obligation to work all day, or to help a close friend?"
  text: " Then add one noun pattern too: **Я хочу каву.** Contrast it with **Я хочу їсти.** Say the full chain aloud: **Я хочу гуляти, але не можу — мушу працювати.** Then ask a partner: **Що ти хочеш робити сьогодні? Що ти можеш робити сьогодні? Що ти мусиш робити завтра?**"
</fixes>