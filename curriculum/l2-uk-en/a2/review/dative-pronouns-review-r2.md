## Linguistic Scan
- No Russianisms, Surzhyk, calques, paronym errors, forbidden Russian characters, or clear prose-level case/gender mistakes found in the module text.
- One exercise form is wrong: `тебою` in the quiz options is not found in VESUM; the standard instrumental form is `тобою`.

## Exercise Check
- Marker inventory is correct: `match-up-pronouns`, `fill-in-dative-pronouns`, `true-false-impersonal`, and `quiz-choose-dative-or-accusative-pronoun-form-in-context-vs` all appear exactly once.
- Marker placement is correct: each marker comes after the relevant teaching block, and they are spread sensibly through the module.
- The `fill-in-dative-pronouns` exercise is logically broken. Prompts such as `Я дарую ____ нову книгу.` and `Мама купує ____ теплий шарф.` allow multiple dative answers, so the keyed answer is arbitrary.
- The same `fill-in-dative-pronouns` block is guessable because all 8 correct answers are in option slot 0.
- The `match-up-pronouns` block is off-plan: it tests `хто → кому` instead of the planned personal-pronoun item `воно → йому`.
- The quiz block contains the non-word `тебою` twice.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections are present, but none of the plan references is cited in the module text (`Захарійчук: 0`, `Заболотний: 0`, `ukrainianlessons.com/dative-case: 0`), and the match-up tests `хто → кому` instead of the planned paradigm item `воно → йому`. |
| 2. Linguistic accuracy | 8/10 | No Russian contamination found, but the quiz options use `тебою`; VESUM finds `тобою` and does not find `тебою`. |
| 3. Pedagogical quality | 9/10 | The module follows a clear explain -> example -> contrast -> practice sequence: recipient meaning, pronoun paradigm, impersonal dative, then accusative-vs-dative minimal pairs before activities. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary appears naturally in prose, and the recommended `приємно`, `цікаво`, `сумно`, `важко` are all present. |
| 5. Exercise quality | 4/10 | Marker count and placement are right, but `fill-in-dative-pronouns` has ambiguous prompts (`Я дарую ____ нову книгу.`, `Мама купує ____ теплий шарф.`), all answers sit in option 0, the match-up omits explicit `воно → йому`, and the quiz includes non-word `тебою`. |
| 6. Engagement & tone | 9/10 | The teacher voice stays natural and concrete, using gift-distribution and cafe scenes rather than generic hype. |
| 7. Structural integrity | 10/10 | All required H2s are present and ordered correctly; all four markers appear exactly once; pipeline word count is 2901, above target. |
| 8. Cultural accuracy | 10/10 | No Russian-centered framing or cultural distortion appears in the module. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues use named speakers and multi-turn exchange (`Іменинник/Родина`, `Марко/Олена`) rather than anonymous textbook prompts. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: module text, exact search results for plan references: `Захарійчук: 0`, `Заболотний: 0`, `ukrainianlessons.com/dative-case: 0`  
Issue: The plan explicitly includes three references, but the module never cites them.  
Fix: Add one short source note in the pronoun section citing Захарійчук §281, Заболотний §157, and the Ukrainian Lessons overview.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `activities/dative-pronouns.yaml`, `fill-in-dative-pronouns` — `Я дарую ____ нову книгу.`; `Мама купує ____ теплий шарф.`  
Issue: These prompts are ambiguous; multiple dative pronouns fit, so the keyed answer is arbitrary.  
Fix: Rewrite the items so each sentence contains enough context to force exactly one pronoun.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `activities/dative-pronouns.yaml`, `fill-in-dative-pronouns`  
Issue: All 8 correct answers are in option slot 0, making the exercise guessable without grammar knowledge.  
Fix: Shuffle option order so correct answers vary by position while remaining uniquely correct.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `activities/dative-pronouns.yaml`, quiz options for `Я бачу ____ в парку.` and `Я кажу ____ правду.` — `тебою`  
Issue: `тебою` is not found in VESUM; the standard instrumental form is `тобою`.  
Fix: Replace `тебою` with `тобою`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `activities/dative-pronouns.yaml`, `match-up-pronouns` — `він / воно → йому` and `хто → кому`  
Issue: The plan calls for the personal-pronoun paradigm; `воно → йому` should be tested explicitly, and `хто → кому` is off-plan.  
Fix: Split `він` and `воно` into separate pairs and replace `хто → кому` with `воно → йому`.

## Verdict: REVISE
The prose is mostly sound, but the activity YAML is not shippable as written: it contains one wrong Ukrainian form and multiple exercise-logic failures. This needs revision, not a full rebuild.

<fixes>
- find: |
    Notice that "він" and "воно" share the exact same form in the dative case. You will use these tiny words continuously when explaining who received a specific item or who is being addressed.
  replace: |
    Notice that "він" and "воно" share the exact same form in the dative case. You will use these tiny words continuously when explaining who received a specific item or who is being addressed. For a school-style declension table, compare Захарійчук Grade 4, §281; for a broader learner overview, see Ukrainian Lessons, “Dative Case in Ukrainian”; and when you later move from pronouns to noun endings such as -ові/-у, compare Заболотний Grade 10, §157.

- find: |
      - left: він / воно
        right: йому
  replace: |
      - left: він
        right: йому

- find: |
      - left: хто
        right: кому
  replace: |
      - left: воно
        right: йому

- find: |
    - id: fill-in-dative-pronouns
      type: fill-in
      instruction: Вставте правильний займенник у давальному відмінку.
      items:
      - sentence: Я дарую ____ нову книгу.
        answer: йому
        options:
        - йому
        - їй
        - їм
      - sentence: Вчитель каже ____ правило.
        answer: нам
        options:
        - нам
        - вам
        - їм
      - sentence: Що вони дарують ____ на свято?
        answer: тобі
        options:
        - тобі
        - мені
        - вам
      - sentence: Ми даємо ____ квитки в театр.
        answer: їм
        options:
        - їм
        - йому
        - їй
      - sentence: Будь ласка, скажи ____ усю правду.
        answer: мені
        options:
        - мені
        - тобі
        - нам
      - sentence: Брат показує ____ нове фото.
        answer: їй
        options:
        - їй
        - йому
        - їм
      - sentence: Мама купує ____ теплий шарф.
        answer: вам
        options:
        - вам
        - нам
        - тобі
      - sentence: Вони пишуть ____ довгого листа.
        answer: нам
        options:
        - нам
        - вам
        - їм
  replace: |
    - id: fill-in-dative-pronouns
      type: fill-in
      instruction: Вставте правильний займенник у давальному відмінку.
      items:
      - sentence: Це мій брат. Я дарую ____ нову книгу.
        answer: йому
        options:
        - їй
        - йому
        - їм
      - sentence: Це моя сестра. Мама купує ____ теплий шарф.
        answer: їй
        options:
        - йому
        - їй
        - їм
      - sentence: Це твій подарунок. Що вони дарують ____ на свято?
        answer: тобі
        options:
        - мені
        - вам
        - тобі
      - sentence: Ми купили квитки для друзів. Ми даємо їх ____.
        answer: їм
        options:
        - їм
        - йому
        - їй
      - sentence: Це мій секрет. Будь ласка, скажи ____ усю правду.
        answer: мені
        options:
        - тобі
        - нам
        - мені
      - sentence: Брат показує сестрі нове фото. Він показує ____ його зараз.
        answer: їй
        options:
        - їм
        - їй
        - йому
      - sentence: Пані Олено, я пишу ____ листа сьогодні.
        answer: вам
        options:
        - вам
        - нам
        - тобі
      - sentence: Учитель пояснює нове правило всьому класу. Він пояснює його ____.
        answer: нам
        options:
        - їм
        - нам
        - вам

- find: |
      - question: Я бачу ____ в парку.
        options:
        - тебе
        - тобі
        - ти
        - тебою
        correct: 0
      - question: Я кажу ____ правду.
        options:
        - тебе
        - тобі
        - ти
        - тебою
        correct: 1
  replace: |
      - question: Я бачу ____ в парку.
        options:
        - тебе
        - тобі
        - ти
        - тобою
        correct: 0
      - question: Я кажу ____ правду.
        options:
        - тебе
        - тобі
        - ти
        - тобою
        correct: 1
</fixes>