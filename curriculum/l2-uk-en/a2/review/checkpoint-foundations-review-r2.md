## Linguistic Scan
- Incorrect predicate agreement in a teaching example: `У нашому класі стоїть два великі столи.` should be `У нашому класі стоять два великі столи.`
- Incorrect predicate agreement in a teaching example: `Там на вулиці стоїть п'ять нових студентів.` should be `Там на вулиці стоять п'ять нових студентів.`

## Exercise Check
- Prose markers found: `quiz-mixed-grammar`, `fill-in-transformation`, `error-correction-mixed`, `fill-in-production`.
- Inline activity ids in `activities/checkpoint-foundations.yaml`: `quiz-mixed-grammar`, `fill-in-transformation`, `fill-in-production`.
- Issue: `error-correction-mixed` is referenced in the prose but has no matching inline activity, so Part 3 has a publish-time gap exactly where the learner is told to do error correction.
- Issue: `quiz-mixed-grammar` uses a mechanically guessable key pattern (`correct: 0` throughout the block), which weakens the quiz.
- Issue: the production section talks about answering personal questions and writing `5-7` sentences, but the learner-facing prompts are not stated directly; the prose gives explanation plus dialogue instead of explicit prompts.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | Required/recommended vocabulary is covered, but the plan reference is absent (`Заболотний` search = 0), and the production brief promised direct prompts while the prose only says “You must **написати** (write) your own authentic answers to these questions.” |
| 2. Linguistic accuracy | 6/10 | Two model sentences teach wrong agreement: “**У нашому класі стоїть два великі столи.**” and “**Там на вулиці стоїть п'ять нових студентів.**” |
| 3. Pedagogical quality | 6/10 | The opening spends a long English paragraph on abstract framing (“Mastering these forms moves you away from speaking in broken phrases...”) before learner work starts, and Part 3 announces tasks without stating them directly. |
| 4. Vocabulary coverage | 9/10 | All required items appear in prose (`вправа`, `перевірка`, `контрольна точка`, `завдання`, `текст`, `речення`, `відповідь`), and all recommended items also appear (`правильний`, `варіант`, `обрати`, `написати`). |
| 5. Exercise quality | 4/10 | The prose contains `<!-- INJECT_ACTIVITY: error-correction-mixed -->`, but there is no matching inline block in the activity YAML; the quiz block is also guessable because the correct option stays at index `0`. |
| 6. Engagement & tone | 6/10 | Too much generic English uplift instead of concrete teaching, especially in the opener and summary; the tone is more explanatory boilerplate than sharp checkpoint practice. |
| 7. Structural integrity | 8/10 | H2 structure is complete and the pipeline word count is above target, but the unresolved `<!-- INJECT_ACTIVITY: error-correction-mixed -->` marker leaves a functional hole in Part 3. |
| 8. Cultural accuracy | 9/10 | No Russian-centered framing; examples stay in ordinary Ukrainian classroom/daily-life contexts. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and a plausible study scenario fit the plan well; the dialogue is mostly natural and not interrogation-shaped. |

## Findings
- [DIMENSION 2] [SEVERITY: critical]  
Location: Part 2 numbers section — `**У нашому класі стоїть два великі столи.**` and `**Там на вулиці стоїть п'ять нових студентів.**`  
Issue: Both model sentences use singular `стоїть` with plural quantified subjects, so the module teaches incorrect Ukrainian agreement in examples learners are supposed to trust.  
Fix: Change both predicates to `стоять`.

- [DIMENSION 1] [SEVERITY: major]  
Location: Opening paragraph — `Learning a language requires stopping to review what you know... Mastering these forms moves you away from speaking in broken phrases and allows you to build complete, logical sentences.`  
Issue: The opener is padded with generic English motivation, and it does not integrate the plan reference (`Заболотний Grade 5-6`) or the `повторення вивченого` framing the plan asked for.  
Fix: Replace the paragraph with a shorter checkpoint-oriented intro that names aspect + genitive review and naturally references school-style revision.

- [DIMENSION 5] [SEVERITY: major]  
Location: Part 3 marker — `<!-- INJECT_ACTIVITY: error-correction-mixed -->`  
Issue: The prose promises an error-correction exercise here, but there is no matching inline activity id, so the learner hits a dead spot right after the error-analysis setup.  
Fix: Replace the marker with an inline 6-item error-correction exercise, or add a matching inline block with the same id.

- [DIMENSION 1] [SEVERITY: major]  
Location: Production setup — `You must **написати** (write) your own authentic answers to these questions.` and `The final writing prompt tests your ability to plan ahead and organize your thoughts.`  
Issue: The plan promised explicit open-ended questions and a `5-7` sentence weekend-plans prompt, but the module gives explanation and model dialogue instead of direct learner-facing prompts.  
Fix: Replace those paragraphs with the actual questions and the exact weekend writing prompt.

- [DIMENSION 5] [SEVERITY: major]  
Location: `activities/checkpoint-foundations.yaml`, block `quiz-mixed-grammar`  
Issue: The quiz answer key is mechanically guessable because the correct option remains at index `0` across the block.  
Fix: Reorder options so the correct answer position varies.

## Verdict: REVISE
Critical linguistic errors are present in teaching examples, and the exercise layer has a publish-breaking inline-marker mismatch plus weak quiz logic. Several dimensions are below 9, so this cannot pass.

<fixes>
- find: "* **У нашому класі стоїть два великі столи.** (There are two large tables in our classroom. — *Nominative plural*)"
  replace: "* **У нашому класі стоять два великі столи.** (There are two large tables in our classroom. — *Nominative plural*)"

- find: "* **Там на вулиці стоїть п'ять нових студентів.** (Five new students are standing there on the street. — *Genitive plural*)"
  replace: "* **Там на вулиці стоять п'ять нових студентів.** (Five new students are standing there on the street. — *Genitive plural*)"

- find: "Learning a language requires stopping to review what you know. A **контрольна точка** (checkpoint) is precisely that moment in your journey. This module serves as a comprehensive **перевірка** (check) of the foundational grammar topics covered so far at the A2 level. You will deeply review how to navigate verb aspect, known as the **вид дієслова**, and how to master the Genitive case, or the **родовий відмінок**. Both of these grammatical systems are fundamental to speaking clearly and being understood by native speakers. Without them, you cannot accurately describe what happened yesterday, what will happen tomorrow, or what you currently do not have. Mastering these forms moves you away from speaking in broken phrases and allows you to build complete, logical sentences."
  replace: "This **контрольна точка** (checkpoint) is a focused **перевірка** (check) of two A2 foundations: **вид дієслова** and **родовий відмінок**. As in school-style **повторення вивченого** exercises associated with Заболотний, you first notice the pattern in context and then use it yourself. The goal here is practical: choose the right aspect, form the right Genitive ending, and write about past actions or future plans more accurately."

- find: "<!-- INJECT_ACTIVITY: error-correction-mixed -->"
  replace: |
    **Міні-вправа: знайдіть і виправте помилки.**
    
    1. *Я довго прочитав цю книгу.* → **Я довго читав цю книгу.**
    2. *Він прийшов без свій телефон.* → **Він прийшов без свого телефона.**
    3. *Ми часто купили тут каву.* → **Ми часто купували тут каву.**
    4. *У кімнаті є шість великих вікна.* → **У кімнаті є шість великих вікон.**
    5. *Я потребую вашу допомогу.* → **Я потребую вашої допомоги.**
    6. *Я з'їв чотири солодких яблук.* → **Я з'їв чотири солодкі яблука.**

- find: "Open-ended questions simulate real, unpredictable conversations. You will need to answer personal questions which immediately require you to use genitive plural numbers and perfective verbs correctly. You must **написати** (write) your own authentic answers to these questions. Take your time to think deeply about the correct cases and verb forms before you write anything down."
  replace: "Open-ended questions simulate real, unpredictable conversations. **Напишіть** (write) короткі відповіді на ці запитання повними реченнями: **Скільки у вас братів і сестер?** **Що ви зробили вчора?** **Коли у вас день народження?** У відповідях уживайте родовий відмінок після кількості або `немає` і добирайте правильний вид дієслова."

- find: "The final writing prompt tests your ability to plan ahead and organize your thoughts. You will write a short paragraph about your plans for the weekend using both aspects naturally. Combine imperfective verbs for ongoing, continuous processes and perfective verbs for specific, completed goals. Mixing these aspects gives your writing much more depth, realistic pacing, and precision."
  replace: "**Письмова вправа (5-7 речень):** **Напишіть про свої плани на вихідні. Що ви будете робити? Що ви хочете зробити?** Уживайте недоконаний вид для процесів і повторюваних дій, а доконаний вид — для конкретних результатів."

- find: |
    - question: У мене зараз немає ____ часу.
      options:
      - вільного
      - вільний
      - вільному
      - вільна
      correct: 0
    - question: Сьогодні вранці ми ____ яблучний сік.
      options:
      - купили
      - купували
      - купуємо
      - куплять
      correct: 0
    - question: Вона довго ____ довгого листа.
      options:
      - писала
      - написала
      - пише
      - напишу
      correct: 0
    - question: У кабінеті є п'ять старих ____.
      options:
      - столів
      - столи
      - стіл
      - столу
      correct: 0
  replace: |
    - question: У мене зараз немає ____ часу.
      options:
      - вільний
      - вільному
      - вільного
      - вільна
      correct: 2
    - question: Сьогодні вранці ми ____ яблучний сік.
      options:
      - купували
      - купили
      - купуємо
      - куплять
      correct: 1
    - question: Вона довго ____ довгого листа.
      options:
      - написала
      - пише
      - напишу
      - писала
      correct: 3
    - question: У кабінеті є п'ять старих ____.
      options:
      - столи
      - столів
      - стіл
      - столу
      correct: 1
</fixes>