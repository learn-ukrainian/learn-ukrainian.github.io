## Linguistic Scan
No linguistic errors found.

## Exercise Check
Four prose markers are present and they follow the relevant teaching sections in a workable order: `fill-in` after `Хотіти`, `quiz` + `fill-in` after `Могти і мусити`, and `quiz` after `Підсумок — Summary`.

The generated exercise YAML has two quality problems:
- Both quiz blocks are gameable because every item uses `correct: 0`.
- The first quiz title is truncated to `title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу** (ab'`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The core beats are covered well: `Що ти хочеш робити сьогодні?`, `Я хочу каву`, `Що ви можете порекомендувати?`, and the anchor `Я хочу гуляти, але не можу — мушу працювати.` The contract miss is required term `іти`: the `Хотіти (To Want)` section teaches `Я хочу читати.`, `Він хоче їсти.`, `Ми хочемо працювати.` but does not introduce exact `іти`. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, bad characters, or wrong Ukrainian forms found in the module prose. |
| 3. Pedagogical quality | 8/10 | The flow is mostly solid and example-rich, but `stating **я хочу** is the direct and common way to express a pressing need` overstates the meaning of `хочу` and blurs desire vs necessity. |
| 4. Vocabulary coverage | 8/10 | Most contract vocabulary appears naturally, including `хочеш`, `робити`, `гуляти`, `можу`, `мушу`, `працювати`, `каву`, and `їсти`. Exact `іти` is still absent from the prose. |
| 5. Exercise quality | 6/10 | Marker count matches the four activity obligations, but both generated quizzes in the YAML use `correct: 0` for every item, and the first quiz title is truncated to `(ab'`, which weakens both logic and presentation. |
| 6. Engagement & tone | 8/10 | The module is clear and teacherly, but the closing line `Consistent daily practice of these specific connections makes navigating everyday conversational plans a very straightforward process.` is generic filler rather than concrete guidance. |
| 7. Structural integrity | 10/10 | All four H2 sections are present in contract order, the marker structure is clean, and the pipeline word count is 1233, above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module stays Ukrainian-first, uses ordinary Ukrainian situations, and avoids Russian-centered framing. |
| 9. Dialogue & conversation quality | 9/10 | Both dialogues are multi-turn, named, and situation-based (`weekend-planning`, café ordering). They read more naturally than a drill sheet. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Хотіти (To Want)` — `* **Я хочу читати.** (I want to read.)`, `* **Він хоче їсти.** (He wants to eat.)`, `* **Ми хочемо працювати.** (We want to work.)`  
Issue: The contract requires exact `іти`, but this teaching section never introduces it; the module only uses `піти` earlier in dialogue. I re-checked the current module text and there is no exact `іти` hit.  
Fix: Replace one infinitive example with an `іти` example, e.g. `Я хочу іти в кіно.`

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Хотіти (To Want)` — `In standard conversational Ukrainian, stating **я хочу** is the direct and common way to express a pressing need.`  
Issue: `хочу` expresses want/desire here, not necessarily a “pressing need”; this explanation muddies the core semantic contrast the module is teaching.  
Fix: Change `pressing need` to `want` or `desire`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: generated quiz YAML — repeated `correct: 0` in both quiz blocks, plus `title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу** (ab'`  
Issue: The quizzes are pattern-gameable because the right answer is always first, and the first quiz title is visibly truncated.  
Fix: Reorder options so correct indices vary, update the `correct` values, and restore the full first quiz title.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `## Підсумок — Summary` — `Consistent daily practice of these specific connections makes navigating everyday conversational plans a very straightforward process.`  
Issue: This is generic filler rather than specific classroom guidance.  
Fix: Replace it with a concrete speaking instruction tied to `хочу/можу/мушу`.

## Verdict: REVISE
REVISE — the prose is linguistically clean, but there is a contract vocabulary miss, one semantic overstatement in the teaching explanation, and a real exercise-logic flaw in the generated quizzes. The module does not meet the PASS gate because multiple dimensions are below 9 and there are fixable findings.

<fixes>
- find: "* **Я хочу читати.** (I want to read.)"
  replace: "* **Я хочу іти в кіно.** (I want to go to the cinema.)"

- find: "In standard conversational Ukrainian, stating **я хочу** is the direct and common way to express a pressing need."
  replace: "In standard conversational Ukrainian, stating **я хочу** is the direct and common way to express a want or desire."

- find: "Consistent daily practice of these specific connections makes navigating everyday conversational plans a very straightforward process."
  replace: "Repeat the pattern aloud until you can switch quickly between **хочу**, **можу**, and **мушу** in your own sentences."

- find: |-
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
  replace: |-
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
        - можете
        - хочете
        - мусите
        correct: 1
      - question: Я не можу, я ____ працювати.
        options:
        - можу
        - хочу
        - мушу
        correct: 2
      - question: Що ви ____ порекомендувати?
        options:
        - хочете
        - можете
        - мусите
        correct: 1
      - question: Вона дуже любить чай. Вона ____ чай.
        options:
        - хоче
        - може
        - мусить
        correct: 0
      - question: Ти знаєш українські слова. Ти ____ читати.
        options:
        - хочеш
        - можеш
        - мусиш
        correct: 1
      - question: Завтра тест. Я ____ вчити слова.
        options:
        - можу
        - мушу
        - хочу
        correct: 1
      - question: Сьогодні ми вільні. Ми ____ гуляти.
        options:
        - хочемо
        - мусимо
        - можемо
        correct: 2
      title: 'Choose the correct modal verb for the situation: **хочу** (desire), **можу** (ability), or **мушу** (obligation).'

- find: |-
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
  replace: |-
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
        - я можу, ти можеш
        - я могу, ти могиш
        correct: 1
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
        - Вони мушать працювати.
        - Вони мусять працювати.
        - Вони мусять працювать.
        correct: 1
      title: Identify the correct conjugation pattern for the verbs.
</fixes>