## Linguistic Scan
No linguistic errors found. VESUM checks support the disputed forms here, including `дідусю`, `Анно`, `вчителькою`, and `закінчила`; no Russian-only letters (`ы, э, ё, ъ`) appear.

## Exercise Check
Markers in prose: `matching-tense`, `fill-in-signal-words`, `ordering-chronological`, `fill-in-biography`.

Placement is mostly correct:
- `matching-tense` and `fill-in-signal-words` come right after `## Три часи разом`, so they test the tense teaching just introduced.
- `ordering-chronological` and `fill-in-biography` come after `## Моя історія`, so they follow the model biography and scaffold.

Issues found:
- `ordering-chronological` is present in the prose marker, but there is no inline activity with that id in `activities/my-story.yaml`, so one planned injected exercise is missing at publish time.
- Both inline fill-in exercises are mechanically guessable because every correct answer is in option slot 1.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned H2 sections are present, and Taras’s model story follows the plan, but section pacing is far off: `Dialogues` is 537 words and `Три часи разом` is 654 vs planned 300 each. The signal-word prose also omits planned forms `цього року`, `наступного року`, and `коли я був/була маленьким/маленькою` (exact searches in the module returned 0). |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or Russian-only letters found. Verified forms such as `дідусю`, `Анно`, `вчителькою`, and `закінчила` are valid Ukrainian. |
| 3. Pedagogical quality | 6/10 | Long English theory blocks dominate key teaching moments: `The past tense (**минулий час**) is the foundation of your biography...`, `The future tense (**майбутній час**) allows you to share your goals...`, and `Now it is time to transition from individual sentences...`. That weakens PPP by separating rule from practice and inflating the lesson with explanation instead of guided use. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is covered through natural forms like `народився/народилася`, `живу`, `вчилася`, `переїхав/переїхала`, `раніше`, `далі`, `розповідати`. Recommended items such as `подорожувати`, `університет`, `програмістом`, `успіх`, `мрія`, and `батьками` also appear. |
| 5. Exercise quality | 5/10 | Marker placement is good, but one planned exercise will not inject: the prose has `<!-- INJECT_ACTIVITY: ordering-chronological -->`, while inline YAML defines only `matching-tense`, `fill-in-signal-words`, and `fill-in-biography`. In both inline fill-ins, every correct answer is also in position 1. |
| 6. Engagement & tone | 7/10 | The voice is teacherly, but generic framing like `This module teaches a simple life story pattern...` and `Now it is time to transition from individual sentences...` adds words without much new learner value. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly; markdown is clean; pipeline word count is 2058, which is above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module stays Ukrainian-centered, using places like `Київ`, `Львів`, and `Одеса` plus family-history contexts, with no Russia-centric framing. |
| 9. Dialogue & conversation quality | 7/10 | Speakers are named and the situations are plausible, but the Marko-David exchange is mostly interview-style prompting: `А зараз ти живеш тут?`, `Чому ти переїхав?`, `А що ти будеш робити далі?` rather than a reciprocal conversation. |

## Findings
[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Dialogues`, `## Три часи разом`, `## Моя історія` — `"This module teaches a simple life story pattern..."`, `"The past tense (**минулий час**) is the foundation of your biography..."`, `"The future tense (**майбутній час**) allows you to share your goals..."`, `"Now it is time to transition from individual sentences..."`  
Issue: English meta-commentary is too long for A1, inflates the section budgets, and weakens PPP by delaying practice.  
Fix: Replace the long explanatory paragraphs with short cues tied directly to the Ukrainian examples and model text.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Три часи разом` — `"To help your listener clearly follow your story..."`  
Issue: The plan’s signal-word coverage is incomplete in prose. Exact searches in the module return 0 for `цього року`, `наступного року`, `коли я був`, `коли я була`, `маленьким`, and `маленькою`.  
Fix: Expand the signal-word paragraph and examples to include those planned forms.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: Prose marker `<!-- INJECT_ACTIVITY: ordering-chronological -->` vs inline activity ids in `activities/my-story.yaml`  
Issue: The module includes an `ordering-chronological` injection marker, but there is no inline activity with that id, so one planned exercise cannot render.  
Fix: Add an inline `ordering-chronological` activity matching the plan’s chronological life-events task.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `fill-in-signal-words` and `fill-in-biography` in `activities/my-story.yaml`  
Issue: Every correct answer is in option position 1, so learners can game the task by pattern instead of recognizing tense.  
Fix: Shuffle the options so correct answers appear in varied positions.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: Marko-David dialogue — `"А зараз ти живеш тут?"`, `"Чому ти переїхав?"`, `"А що ти будеш робити далі?"`  
Issue: The exchange reads like an interview, with one speaker asking stock questions and the other only responding.  
Fix: Let David volunteer one present/future detail and make Marko react to it, so the conversation feels reciprocal.

## Verdict: REVISE
No Ukrainian-language errors surfaced, but the module still has major plan, pedagogy, exercise, and dialogue issues. Several dimensions are below 9, and the missing inline activity plus guessable option ordering require concrete fixes before ship.

<fixes>
- find: |-
    This module teaches a simple life story pattern: where you were born, where you live now, and what you plan to do next.
  replace: |-
    Listen for three parts of the story: past, present, and future.

- find: |-
    The past tense (**минулий час**) is the foundation of your biography. When talking about yourself, the past tense strictly requires gender agreement for the pronoun **я** (I). A male speaker must use the masculine ending **-в**, while a female speaker must use the feminine ending **-ла**. This gender distinction is a core feature of the Ukrainian past tense. It is crucial to remember that the past tense does not change based on who you are talking to, but rather the gender of who is speaking or who you are talking about.
  replace: |-
    The past tense (**минулий час**) shows what happened before. Match the verb to the speaker: **я народився / я народилася**, **я жив / я жила**, **я вчився / я вчилася**.

- find: |-
    The future tense (**майбутній час**) allows you to share your goals. The most common and simple way to express the future is by using the compound form. You create this by combining the conjugated helper verb **бути** (to be) with the infinitive form of the main action verb. This compound future is incredibly flexible because you only need to conjugate the helper verb. The main verb always stays in its dictionary infinitive form.
  replace: |-
    The future tense (**майбутній час**) shows plans. In this module, use **бути** + infinitive: **буду працювати**, **будеш працювати**, **буде працювати**, **будемо працювати**.

- find: |-
    Now it is time to transition from individual sentences to a complete, structured monologue. Telling a personal narrative requires organization. A clear story always has three main parts: an introduction, a main body, and a conclusion. By combining your past, present, and future into this structure, you can confidently **розповідати** (to tell/narrate) your unique biography.
  replace: |-
    Now turn the pattern into a short monologue: past background, present life, future plans. Use the model and then build your own story.

- find: |-
    To help your listener clearly follow your story, you should use time signal words. These words act as anchors, marking tense shifts on your timeline. For the past tense, use words like **раніше** (before/earlier) or **у дитинстві**. For the present tense, use **зараз** (now) or **сьогодні** (today). For the future tense, use **потім** (then) or **далі** (further/next). These signal words prepare the listener for the grammar that follows.

    *   **Раніше я жив у Лондоні.** *(Before I lived in London.)*
    *   **Зараз я живу в Києві.** *(Now I live in Kyiv.)*
    *   **Далі я буду жити в Одесі.** *(Next I will live in Odesa.)*
  replace: |-
    To help your listener clearly follow your story, use time signal words. For the past, try **раніше**, **у дитинстві**, or **коли я був маленьким / коли я була маленькою**. For the present, use **зараз**, **сьогодні**, or **цього року**. For the future, use **потім**, **далі**, or **наступного року**.

    *   **Раніше я жив у Лондоні.** *(Before I lived in London.)*
    *   **Цього року я живу в Києві.** *(This year I live in Kyiv.)*
    *   **Наступного року я буду жити в Одесі.** *(Next year I will live in Odesa.)*

- find: |-
    > **Марко:** **А що ти будеш робити далі?** *(And what will you do next?)*
    > **Девід:** **Я буду працювати тут і вчити мову.** *(I will work here and study the language.)*
    > **Марко:** **Цікаво. Тобі подобається Київ?** *(Interesting. Do you like Kyiv?)*
    > **Девід:** **Так, мені тут добре.** *(Yes, I feel good here.)*
    > **Марко:** **Чудово! Успіхів тобі!** *(Wonderful! Success to you!)*
  replace: |-
    > **Марко:** **А що ти будеш робити далі?** *(And what will you do next?)*
    > **Девід:** **Я буду працювати тут і вчити мову. Мені подобається Київ.** *(I will work here and study the language. I like Kyiv.)*
    > **Марко:** **Це чудово.** *(That is wonderful.)*
    > **Девід:** **Так, мені тут добре.** *(Yes, I feel good here.)*
    > **Марко:** **Чудово! Успіхів тобі!** *(Wonderful! Success to you!)*

- find: |-
    - id: fill-in-signal-words
      type: fill-in
      instruction: Вставте правильне дієслово (Fill in the correct verb)
      items:
      - sentence: Раніше я ____ в Канаді.
        answer: жив
        options:
        - жив
        - живу
        - буду жити
      - sentence: Зараз я ____ в університеті.
        answer: працюю
        options:
        - працюю
        - працював
        - буду працювати
      - sentence: Далі я ____ українську мову.
        answer: буду вивчати
        options:
        - буду вивчати
        - вивчав
        - вивчаю
      - sentence: У дитинстві вона ____ читати.
        answer: любила
        options:
        - любила
        - любить
        - буде любити
      - sentence: Сьогодні ми ____ в Україні.
        answer: живемо
        options:
        - живемо
        - жили
        - будемо жити
      - sentence: Далі ми ____ говорити про це.
        answer: будемо
        options:
        - будемо
        - були
        - є
  replace: |-
    - id: fill-in-signal-words
      type: fill-in
      instruction: Вставте правильне дієслово (Fill in the correct verb)
      items:
      - sentence: Раніше я ____ в Канаді.
        answer: жив
        options:
        - живу
        - жив
        - буду жити
      - sentence: Зараз я ____ в університеті.
        answer: працюю
        options:
        - буду працювати
        - працюю
        - працював
      - sentence: Далі я ____ українську мову.
        answer: буду вивчати
        options:
        - вивчаю
        - буду вивчати
        - вивчав
      - sentence: У дитинстві вона ____ читати.
        answer: любила
        options:
        - буде любити
        - любила
        - любить
      - sentence: Сьогодні ми ____ в Україні.
        answer: живемо
        options:
        - жили
        - будемо жити
        - живемо
      - sentence: Далі ми ____ говорити про це.
        answer: будемо
        options:
        - є
        - будемо
        - були

- find: |-
    - id: fill-in-biography
      type: fill-in
      instruction: Доповніть історію (Complete the story)
      items:
      - sentence: Я ____ у Львові.
        answer: народилася
        options:
        - народилася
        - народився
        - народилися
      - sentence: Там я ____ в школі.
        answer: вчилася
        options:
        - вчилася
        - вчився
        - вчилися
      - sentence: Потім я ____ в Київ.
        answer: переїхала
        options:
        - переїхала
        - переїхав
        - переїде
      - sentence: Тут я ____ університет.
        answer: закінчила
        options:
        - закінчила
        - закінчив
        - буду закінчувати
      - sentence: Зараз я ____ вчителькою.
        answer: працюю
        options:
        - працюю
        - працювала
        - буду працювати
      - sentence: Наступного року я ____.
        answer: буду подорожувати
        options:
        - буду подорожувати
        - подорожувала
        - подорожую
  replace: |-
    - id: fill-in-biography
      type: fill-in
      instruction: Доповніть історію (Complete the story)
      items:
      - sentence: Я ____ у Львові.
        answer: народилася
        options:
        - народився
        - народилися
        - народилася
      - sentence: Там я ____ в школі.
        answer: вчилася
        options:
        - вчилися
        - вчилася
        - вчився
      - sentence: Потім я ____ в Київ.
        answer: переїхала
        options:
        - переїде
        - переїхала
        - переїхав
      - sentence: Тут я ____ університет.
        answer: закінчила
        options:
        - закінчив
        - буду закінчувати
        - закінчила
      - sentence: Зараз я ____ вчителькою.
        answer: працюю
        options:
        - працювала
        - буду працювати
        - працюю
      - sentence: Наступного року я ____.
        answer: буду подорожувати
        options:
        - подорожувала
        - буду подорожувати
        - подорожую

- find: |-
    workbook:
  replace: |-
    - id: ordering-chronological
      type: ordering
      instruction: Розташуйте події в правильному порядку (Put the life events in logical chronological order)
      items:
      - Я народився в Торонто.
      - У дитинстві я жив з батьками.
      - Потім я вчився в університеті.
      - Зараз я живу в Києві і працюю програмістом.
      - Далі я буду подорожувати.
    workbook:
</fixes>