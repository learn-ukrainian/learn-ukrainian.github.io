## Linguistic Scan
- **Critical case/apposition error:** `Сьогодні чудовий день. Ти в місті Київ.`  
  `Київ` is left in nominative after `в місті`. This should be `Ти в місті Києві.` or simply `Ти в Києві.` VESUM confirms `Києві` as the locative form, and the textbook corpus returns normal usage like `народився в місті Києві`.

## Exercise Check
- Four activity markers are present: `match-up-survival-phrases`, `fill-in-tenses`, `order-chronological`, `quiz-a1-review`.
- Marker count matches the four `activity_hints`, and the markers are spread across the module rather than clustered at the end.
- **Placement problem:** `<!-- INJECT_ACTIVITY: fill-in-tenses -->` appears at the end of `## День`, but the module does not finish teaching/consolidating the three-tense narrative until `## Вечір` with `Що будемо робити ввечері?`, `Завтра я буду подорожувати.`, and the end-of-day reflection. The fill-in activity is early.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | One required dialogue situation is missing: the plan asks for “A learner tells their Ukrainian friend about their plans after finishing the A1 course,” but the closest text is only `Що будемо робити ввечері? ... Ходімо в кіно!`; the summary checklist omits health/emergency handling; searches found no `ULP` or `State Standard` citation in the prose. |
| 2. Linguistic accuracy | 8/10 | `Ти в місті Київ.` is incorrect; `Києві` is the locative form verified in VESUM/textbook corpus. No Russian characters were found. |
| 3. Pedagogical quality | 8/10 | The review flow is coherent, but the all-tenses practice marker is inserted before the module completes its future-tense and mixed-tense consolidation in `## Вечір`. |
| 4. Vocabulary coverage | 9/10 | Required words appear in prose: `готовий`, `вітаю`, `початок`, `сувенір`, `квиток`; recommended items such as `круасан`, `карта`, `лінія`, `фільм`, `подорожувати`, `Лавра`, `готель` also appear. |
| 5. Exercise quality | 7/10 | All four markers are present, but `<!-- INJECT_ACTIVITY: fill-in-tenses -->` comes before `Що будемо робити ввечері?` / `Завтра я буду подорожувати.` and before the reflection it is supposed to test. |
| 6. Engagement & tone | 6/10 | `Welcome to the culmination of your A1 journey.` and `You have built a massive linguistic foundation.` are exactly the kind of self-congratulatory/generic framing the rubric says to avoid. |
| 7. Structural integrity | 9/10 | All four planned H2 sections are present and ordered; 4 activity markers are present; pipeline word count is 1677, above the 1200 target. |
| 8. Cultural accuracy | 9/10 | Kyiv, Khreshchatyk, the metro, vyshyvanka, and the Lavra are presented on Ukrainian terms, with no Russia-centered framing. |
| 9. Dialogue & conversation quality | 7/10 | Speakers are named, but the farewell dialogue is thin (`Давай писати повідомлення. Ось мій номер.`), and the plan’s second dialogue situation about post-course travel plans with a Ukrainian friend is not dramatized. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Сьогодні чудовий день. Ти в місті Київ.`  
Issue: `Київ` is wrongly left in nominative after `в місті`; the construction needs locative apposition.  
Fix: Change it to `Сьогодні чудовий день. Ти в місті Києві.`

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-tenses -->` at the end of `## День`, before `## Вечір` teaches `Що будемо робити ввечері?` and `Завтра я буду подорожувати.`  
Issue: The fill-in exercise is placed before the module completes the three-tense review it is supposed to practice.  
Fix: Move `fill-in-tenses` to the end of `## Вечір`, immediately before `order-chronological`.

[PLAN ADHERENCE, DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location:  
`> **Ти:** Що будемо робити ввечері?`  
`> **Олена:** Ходімо в кіно!`  
`> **Ти:** Добре! О котрій?`  
`> **Олена:** О сьомій.`  
Issue: This covers same-evening scheduling, but not the plan’s required dialogue where the learner tells a Ukrainian friend what they will do after finishing A1.  
Fix: Expand this exchange so Olena asks about post-course plans and the learner answers in the future tense, e.g. travel in Ukraine, see the Carpathians, see the Lavra.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `You can even narrate a story about the past and make plans for the future. You have built a massive linguistic foundation.`  
Issue: The final A1 skills checklist omits the plan’s promised `handle health and emergencies` coverage.  
Fix: Add a sentence that explicitly mentions describing pain, asking for medicine, and calling for help.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `What is next? The A2 level awaits. ... But right now, you must celebrate your hard work.`  
Issue: The plan references (`ULP Season 1, Episodes 36-40` and `State Standard 2024`) are not cited anywhere in the module.  
Fix: Add one natural sentence in this paragraph pointing learners back to those references for review.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `Welcome to the culmination of your A1 journey.` and `You have built a massive linguistic foundation.`  
Issue: The framing is generic and self-congratulatory rather than concrete, teacherly, and specific to the lesson.  
Fix: Replace the opener with direct task framing and tone down the generic praise line.

## Verdict: REVISE
A PASS is not possible here because there is a **critical linguistic error** (`Ти в місті Київ`) and several **major** plan/exercise issues: one required dialogue situation is missing, the three-tense exercise is misplaced, the final checklist omits health/emergency handling, and the plan references are not cited.

<fixes>
- find: "Welcome to the culmination of your A1 journey. To test your skills, we will simulate a full day in Ukraine. You will use the past, present, and future tenses. You will navigate the city, order food, and meet people. This is where all the separate pieces you learned come together into natural communication. You are ready for this challenge."
  replace: "In this module, you will spend one full day in Ukraine. You will use the past, present, and future tenses as you travel across the city, order food, shop, and meet people. This is a full A1 review in context."

- find: "Сьогодні чудовий день. Ти в місті Київ. Зранку ти прокинувся в готелі."
  replace: "Сьогодні чудовий день. Ти в місті Києві. Зранку ти прокинувся в готелі."

- find: |
    > **Ти:** Що будемо робити ввечері? *(What will we do in the evening?)*
    > **Олена:** Ходімо в кіно! *(Let's go to the cinema!)*
    > **Ти:** Добре! О котрій? *(Good! At what time?)*
    > **Олена:** О сьомій. *(At seven.)*
  replace: |
    > **Ти:** Що будемо робити ввечері? *(What will we do in the evening?)*
    > **Олена:** Ходімо в кіно! *(Let's go to the cinema!)*
    > **Ти:** Добре! О котрій? *(Good! At what time?)*
    > **Олена:** О сьомій. *(At seven.)*
    > **Олена:** А що ти будеш робити після курсу? *(And what will you do after the course?)*
    > **Ти:** Я буду подорожувати Україною. Я хочу побачити Карпати і Лавру! *(I will travel around Ukraine. I want to see the Carpathians and the Lavra!)*

- find: "The phrase **що будемо робити** uses the future tense. You are asking about plans. Asking **о котрій** (at what time) is essential for scheduling."
  replace: "The phrase **що будемо робити** uses the future tense. The question **що ти будеш робити після курсу?** also keeps the focus on future plans after A1. Asking **о котрій** (at what time) is essential for scheduling."

- find: "<!-- INJECT_ACTIVITY: fill-in-tenses -->"
  replace: ""

- find: "<!-- INJECT_ACTIVITY: order-chronological -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-tenses -->\n\n<!-- INJECT_ACTIVITY: order-chronological -->"

- find: "You can even narrate a story about the past and make plans for the future. You have built a massive linguistic foundation."
  replace: "You can even narrate a story about the past and make plans for the future. You can also describe pain, ask for medicine, and call for help in an emergency. You now have a solid A1 foundation for everyday Ukrainian."

- find: "What is next? The A2 level awaits. In A2, you will learn the grammatical cases (**відмінки**). You will learn verb aspect, specifically the difference between imperfective and perfective verbs (**доконаний/недоконаний вид**), which changes how you talk about completed actions. You will learn the synthetic future tense, like the word **прочитаю** (I will read). These tools will make your sentences richer and more complex. But right now, you must celebrate your hard work."
  replace: "What is next? The A2 level awaits. In A2, you will learn the grammatical cases (**відмінки**). You will learn verb aspect, specifically the difference between imperfective and perfective verbs (**доконаний/недоконаний вид**), which changes how you talk about completed actions. You will learn the synthetic future tense, like the word **прочитаю** (I will read). These tools will make your sentences richer and more complex. For extra review, go back to ULP Season 1, Episodes 36-40, and compare your skills with the A1 completion areas in the State Standard 2024. But right now, you must celebrate your hard work."
</fixes>