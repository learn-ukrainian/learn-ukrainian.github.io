## Linguistic Scan
- No Russianisms, surzhyk, calques, paronym errors, or forbidden Russian letters found in the Ukrainian examples.
- Factual grammar issue: the module calls `буду + infinitive` a “specific continuous form of the future tense” and says Ukrainian has “two distinct ways” to talk about the future. Repo textbook data says `складений майбутній час` is the relevant label here, and school grammar distinguishes three future forms, not two.

## Exercise Check
- Marker inventory is correct: `match-pronoun-to-buty`, `fill-in-analytic-future`, and `fill-in-tense-distinction` all appear, and each marker comes after the relevant teaching section.
- The markers are spread sensibly through the module rather than clustered at the end.
- The prose misses part of the planned dialogue coverage: search confirmed `Що буде робити Олена`, `Вона буде читати`, and `ви будете гуляти` occur `0` times in the module, so the planned all-person dialogue pattern is not fully realized in dialogue form.
- Exercise logic is mostly correct, but both inline fill-ins in [what-will-happen.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/what-will-happen.yaml:22) have every correct answer in option slot 1. The computed answer-index patterns are `[0,0,0,0,0,0]` and `[0,0,0,0,0,0]`, which makes the tasks guessable.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections are present, but section pacing is far off the 300-word plan budget: `Dialogues 468`, `Майбутній час 472`, `Практика 389`, `Summary 297`. The planned dialogue lines `Вона буде читати` / `ви будете гуляти` are also absent from the prose dialogue. |
| 2. Linguistic accuracy | 7/10 | The Ukrainian sentence forms are clean, but [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:3) teaches a “specific continuous form of the future tense,” and [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:32) says Ukrainian has “two distinct ways” to express future meaning. The repo textbook corpus gives three future forms. |
| 3. Pedagogical quality | 6/10 | The module has PPP structure, but it repeatedly buries A1 grammar under long English exposition before examples. The opening dialogue section spends a full paragraph of theory before the first Ukrainian line, and the grammar section over-explains a simple pattern instead of moving quickly from model to practice. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary is covered naturally: `завтра`, `буду/будеш/буде/будемо/будете/будуть`, `робити`. Recommended items like `відпочивати`, `план`, `футбол`, `наступного тижня` also appear, but the planned `Звучить добре!` / `звучати` item was swapped out. |
| 5. Exercise quality | 6/10 | The three planned activity types are present and aligned to the teaching, but both fill-in exercises in [what-will-happen.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/what-will-happen.yaml:22) place every correct answer first, creating a strong answer-position pattern. |
| 6. Engagement & tone | 5/10 | Phrases like “This powerful grammatical structure,” “Now let us rigorously apply,” and “You now firmly possess the grammatical tools” read as inflated filler rather than direct teacher talk. |
| 7. Structural integrity | 9/10 | Clean markdown, all planned H2 headings present and ordered correctly, and the pipeline word count is `1571`, which is safely above target. |
| 8. Cultural accuracy | 9/10 | No Russian-centering or cultural inaccuracies found; the `ворожка` setup is plausible and locally grounded. |
| 9. Dialogue & conversation quality | 6/10 | The first “dialogue” is mostly a monologue by the fortune teller, and the second is heavily question-driven. It is serviceable, but not a strong natural conversation with balanced turns. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:3) — “she uses a specific continuous form of the future tense”  
Issue: `буду + infinitive` is mislabeled with English-style “continuous” terminology. That is not the standard Ukrainian grammar label and risks teaching the wrong concept.  
Fix: Replace “continuous form” language with `analytic future tense` / `складений майбутній час`, and describe it as suitable for planned, ongoing, or repeated future actions.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:32) — “Ukrainian actually possesses two distinct ways to talk about the future”  
Issue: This teaches the wrong grammar classification. Repo textbook search returns `Є три форми майбутнього часу`, so “two distinct ways” is factually wrong.  
Fix: Rephrase to say that Ukrainian has other future forms, but this module teaches one practical A1 pattern: the analytic future.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:3), [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:32), [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:106)  
Issue: The prose is too padded with English meta-explanation. That pushes the first three sections far past the plan’s 300-word budgets and slows down A1 learners before they reach the Ukrainian examples.  
Fix: Trim the inflated explanation paragraphs and keep the teaching language short, concrete, and example-first.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:19) — the second dialogue block  
Issue: The planned all-person dialogue coverage is incomplete in dialogue form. Search confirmed `Що буде робити Олена`, `Вона буде читати`, and `ви будете гуляти` are absent, and `Звучить добре!` was replaced by `Чудова думка!`.  
Fix: Rewrite the second dialogue so it includes `Вона буде читати`, `А ви будете гуляти?`, `Так, ми будемо гуляти в парку`, and `Звучить добре!`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: [what-will-happen.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/what-will-happen.yaml:27) and [what-will-happen.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/what-will-happen.yaml:67)  
Issue: Every correct answer is in the first option slot in both fill-in exercises. That creates a mechanical pattern instead of testing understanding.  
Fix: Shuffle the options so the correct answer position varies across items.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: [what-will-happen.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/what-will-happen.md:106) — “You now firmly possess the grammatical tools required…”  
Issue: This is exactly the kind of inflated, self-congratulatory phrasing the rubric warns against.  
Fix: Replace it with direct teacher wording: “You can now talk about future plans with буду + infinitive.”

## Verdict: REVISE
Critical grammar inaccuracies are present, and several dimensions are below 9. The module is structurally usable, but it should not ship until the future-tense explanation is corrected, the dialogue is brought back in line with the plan, and the exercise answer-order bias is fixed.

<fixes>
- find: |-
    Imagine sitting in the cozy, sunlit kitchen of a Ukrainian village **ворожка** (fortune teller). She is intently reading a client’s palm, tracing the intricate lines that predict what lies ahead in life. To describe major life events that will stretch across time—like embarking on long journeys, building relationships, or experiencing a continuous series of happy encounters—she uses a specific continuous form of the future tense. This powerful grammatical structure allows her to talk about ongoing processes and repeated, habitual actions rather than single, sudden, or completed events. It paints a picture of a continuous future reality. Let us listen closely to her predictions and observe how she constructs her sentences.
  replace: |-
    Imagine sitting in the cozy, sunlit kitchen of a Ukrainian village **ворожка** (fortune teller). As she reads a client’s palm, she predicts the future with the analytic future tense: **будеш + infinitive**. This form is useful for planned, ongoing, or repeated actions in the future.

- find: |-
    The fortune teller builds her sweeping predictions using a simple, highly predictable, and repeated grammatical pattern: the conjugated word **будеш** (you will) followed immediately by action words like **подорожувати** (to travel), **зустрічати** (to meet), and **отримувати** (to receive). Notice carefully how the main action verbs stay locked in their dictionary form (the infinitive ending in "-ти"), while only the helper word changes to match the person being spoken to. This specific grammatical construction actively describes an iterative process or repeated actions spread across time, rather than a single, isolated, completed event. It tells the client that the traveling, the meeting, and the receiving will happen continuously and repeatedly in the future.

    :::note
    The word **будеш** is the "you" form of the verb **бути** (to be) in the future tense. When combined with an infinitive, it creates the analytic future tense, which focuses on the process of an action.
    :::
  replace: |-
    The fortune teller builds her predictions with **будеш** + infinitive: **будеш подорожувати**, **будеш зустрічати**, **будеш отримувати**. The main verb stays in the infinitive, while **будеш** changes to match the person being spoken to.

    :::note
    The word **будеш** is the "you" form of the verb **бути** (to be) in the future tense. When combined with an infinitive, it creates the analytic future tense.
    :::

- find: |-
    When discussing your upcoming **план** (plan, m), life predictions, or scheduled events, we need to utilize the **майбутній час** (future tense). Ukrainian actually possesses two distinct ways to talk about the future depending on the nature of the action—whether it is a continuous process or a single completed task. However, at the A1 level, we focus exclusively on learning the most common, accessible, and highly practical form first: the analytic future, known grammatically as **складений майбутній час**. This form is remarkably straightforward for English speakers because it perfectly mirrors the familiar English sentence structure of using the helper word "will" followed by a main action verb.
  replace: |-
    When discussing your upcoming **план** (plan, m), life predictions, or scheduled events, we need to utilize the **майбутній час** (future tense). Ukrainian school grammar distinguishes several future forms, but at the A1 level we focus on one practical pattern: the analytic future, known grammatically as **складений майбутній час**. This is the pattern **буду + infinitive**, as in **я буду читати**.

- find: |-
    Please note that a simple perfective future form exists exclusively for single, completed actions, but that is a complex topic reserved for the A2 level.
  replace: |-
    Please note that Ukrainian also has other future forms, but they are outside the scope of this module.

- find: |-
    > **Олена:** Що ти будеш робити завтра? *(What will you do tomorrow?)*
    > **Антон:** Завтра я буду працювати. *(Tomorrow I will work.)*
    > **Олена:** А ввечері? *(And in the evening?)*
    > **Антон:** Ввечері я буду готувати вечерю. *(In the evening I will prepare dinner.)*
    > **Олена:** Що ви будете робити на вихідних? *(What will you guys do on the weekend?)*
    > **Антон:** У суботу ми будемо відпочивати. *(On Saturday we will rest.)*
    > **Олена:** А в неділю? *(And on Sunday?)*
    > **Антон:** У неділю я буду готувати, а чоловік буде гуляти з дітьми. *(On Sunday I will cook, and my husband will walk with the children.)*
    > **Олена:** Чудова думка! А я буду дивитися футбол. *(Great idea! And I will watch football.)*
    > **Антон:** Ти завжди будеш дивитися футбол! *(You will always watch football!)*
  replace: |-
    > **Олена:** Що ти будеш робити завтра? *(What will you do tomorrow?)*
    > **Антон:** Завтра я буду працювати. *(Tomorrow I will work.)*
    > **Олена:** А ввечері? *(And in the evening?)*
    > **Антон:** Ввечері я буду готувати вечерю. *(In the evening I will prepare dinner.)*
    > **Олена:** А що буде робити твоя сестра? *(And what will your sister do?)*
    > **Антон:** Вона буде читати. *(She will read.)*
    > **Олена:** А ви будете гуляти? *(And will you go for a walk?)*
    > **Антон:** Так, ми будемо гуляти в парку. *(Yes, we will walk in the park.)*
    > **Олена:** Звучить добре! А я буду дивитися футбол. *(That sounds good! And I will watch football.)*
    > **Антон:** Ти завжди будеш дивитися футбол! *(You will always watch football!)*

- find: |-
    You now firmly possess the grammatical tools required to talk about the future and make extensive plans. The single core communicative question you must memorize is: **Що ти будеш робити?** (What will you do?). When someone asks you this common question, you simply reply with **Я буду** plus the infinitive of your planned action. To actively test your understanding of this module, look at the bulleted question-and-answer self-check list below and try to answer each question mentally using a full, complete Ukrainian sentence.
  replace: |-
    You can now talk about future plans with **буду + infinitive**. The key question is: **Що ти будеш робити?** (What will you do?). Answer with **Я буду** plus an infinitive, then use the questions below to practice.

- find: |-
      - sentence: Завтра я ____ працювати.
        answer: буду
        options:
        - буду
        - буде
        - будемо
      - sentence: Що ти ____ робити ввечері?
        answer: будеш
        options:
        - будеш
        - буду
        - будете
      - sentence: Вона ____ читати книжку.
        answer: буде
        options:
        - буде
        - будуть
        - будемо
      - sentence: Ми ____ дивитися футбол.
        answer: будемо
        options:
        - будемо
        - буде
        - буду
      - sentence: Ви ____ гуляти в парку?
        answer: будете
        options:
        - будете
        - будеш
        - будуть
      - sentence: Вони ____ відпочивати.
        answer: будуть
        options:
        - будуть
        - будемо
        - буде
  replace: |-
      - sentence: Завтра я ____ працювати.
        answer: буду
        options:
        - буде
        - буду
        - будемо
      - sentence: Що ти ____ робити ввечері?
        answer: будеш
        options:
        - буду
        - будете
        - будеш
      - sentence: Вона ____ читати книжку.
        answer: буде
        options:
        - буде
        - будемо
        - будуть
      - sentence: Ми ____ дивитися футбол.
        answer: будемо
        options:
        - буду
        - будемо
        - буде
      - sentence: Ви ____ гуляти в парку?
        answer: будете
        options:
        - будуть
        - будете
        - будеш
      - sentence: Вони ____ відпочивати.
        answer: будуть
        options:
        - буде
        - будемо
        - будуть

- find: |-
      - sentence: Зараз я ____.
        answer: читаю
        options:
        - читаю
        - читав
        - буду читати
      - sentence: Учора він ____ у парку.
        answer: гуляв
        options:
        - гуляв
        - гуляє
        - буде гуляти
      - sentence: Завтра ми ____ фільм.
        answer: будемо дивитися
        options:
        - будемо дивитися
        - дивилися
        - дивимося
      - sentence: Минулого тижня вона ____.
        answer: працювала
        options:
        - працювала
        - працює
        - буде працювати
      - sentence: Сьогодні я ____ вечерю.
        answer: готую
        options:
        - готую
        - готував
        - буду готувати
      - sentence: У суботу вони ____.
        answer: будуть відпочивати
        options:
        - будуть відпочивати
        - відпочивали
        - відпочивають
  replace: |-
      - sentence: Зараз я ____.
        answer: читаю
        options:
        - читав
        - читаю
        - буду читати
      - sentence: Учора він ____ у парку.
        answer: гуляв
        options:
        - гуляє
        - буде гуляти
        - гуляв
      - sentence: Завтра ми ____ фільм.
        answer: будемо дивитися
        options:
        - дивилися
        - будемо дивитися
        - дивимося
      - sentence: Минулого тижня вона ____.
        answer: працювала
        options:
        - працює
        - буде працювати
        - працювала
      - sentence: Сьогодні я ____ вечерю.
        answer: готую
        options:
        - буду готувати
        - готую
        - готував
      - sentence: У суботу вони ____.
        answer: будуть відпочивати
        options:
        - будуть відпочивати
        - відпочивають
        - відпочивали
</fixes>