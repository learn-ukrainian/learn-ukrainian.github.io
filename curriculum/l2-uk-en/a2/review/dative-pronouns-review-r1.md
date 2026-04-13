## Linguistic Scan
- Factually wrong grammar claim in the impersonal-construction grammar box: “They always end in the letter «-о».” This is false. Ukrainian impersonal predicates also include forms like `треба` and `можна`.
- No Russianisms, Surzhyk, paronym misuse, or forbidden Russian characters were found in the reviewed module text and activity YAML.

## Exercise Check
- Exact marker inventory is correct: `match-up-pronouns`, `fill-in-dative-pronouns`, `true-false-impersonal`, `quiz-choose-dative-or-accusative-pronoun-form-in-context-vs`. All four markers appear after the relevant teaching sections, match the four `activity_hints`, and are spread sensibly through the module.
- The generated YAML has two real logic problems. The `fill-in-dative-pronouns` block is ambiguous: items like `Я дарую ____ нову книгу.` and `Мама купує ____ теплий шарф.` allow multiple dative answers, so the key is arbitrary. The same block also has every correct option in slot 0 (`[0, 0, 0, 0, 0, 0, 0, 0]`), which makes it guessable.
- The match-up is slightly off-plan: it tests `хто→кому` instead of the planned personal-pronoun paradigm item `воно→йому`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned sections are present and the core dative/accusative contrast is covered, but the planned common predicates are not fully realized in prose: exact search found `можна: 0` and `легко: 0`. The match-up also tests `хто→кому` instead of the planned personal-pronoun item `воно→йому`. |
| 2. Linguistic accuracy | 6/10 | No Russian contamination found, but the module teaches a false rule in the impersonal grammar box: “They always end in the letter «-о».” |
| 3. Pedagogical quality | 7/10 | The overall flow is usable and example-rich, but section 2 opens with a long English metagrammatical paragraph (“In the **давальний відмінок**... Instead, you must memorize...”) before learners get the pattern in compact form. |
| 4. Vocabulary coverage | 8/10 | All required vocabulary appears naturally, and recommended `приємно`, `цікаво`, `сумно`, `важко` are present. Planned common predicates `можна` and `легко` are missing from the prose. |
| 5. Exercise quality | 5/10 | Marker placement and count are correct, but `fill-in-dative-pronouns` is logically broken by ambiguous prompts (`Я дарую ____ нову книгу.`) and uniform answer placement (`[0,0,0,0,0,0,0,0]`). |
| 6. Engagement & tone | 8/10 | The teacher voice is steady and classroom-like, and the cafe dialogue is usable at A2. |
| 7. Structural integrity | 9/10 | All required H2s are present and ordered correctly; the four markers are present; pipeline word count is 2929, above target. |
| 8. Cultural accuracy | 9/10 | No Russian-centered framing; examples stay within ordinary Ukrainian contexts. |
| 9. Dialogue & conversation quality | 8/10 | The dialogues use named speakers and multi-turn exchange, especially in the cafe scene (`Мені трохи сумно... Ходімо в кафе?`). |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Мені холодно: Безособові конструкції`, grammar box — “They always end in the letter «-о».”  
Issue: This teaches a false rule. Ukrainian impersonal predicates do not all end in `-о`; `треба` and `можна` are standard counterexamples.  
Fix: Replace the last sentence with a qualified rule: many common forms end in `-о`, but not all do.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `activities/dative-pronouns.yaml`, `fill-in-dative-pronouns` — e.g. `Я дарую ____ нову книгу.`, `Мама купує ____ теплий шарф.`  
Issue: These prompts do not provide context, so multiple dative pronouns are valid. The answer key is arbitrary.  
Fix: Rewrite the block so each item contains enough context to force one pronoun.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `activities/dative-pronouns.yaml`, `fill-in-dative-pronouns` — correct-answer positions `[0,0,0,0,0,0,0,0]`  
Issue: Every answer is in the first slot, making the exercise guessable even without understanding the grammar.  
Fix: Shuffle options so correct answers vary by position while staying uniquely correct.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Мені холодно: Безособові конструкції` — example paragraph beginning `Мені сьогодні дуже холодно...`  
Issue: The plan’s common predicate set explicitly includes `можна` and `легко`, but exact search found both missing from the prose.  
Fix: Add short examples with both predicates in the impersonal section.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Особові займенники у давальному відмінку`, opening paragraph — “In the **давальний відмінок** (dative case), personal pronouns undergo a complete transformation...”  
Issue: The section starts with a long English explanation instead of giving learners the compact pattern immediately. That slows the lesson and weakens the PPP flow.  
Fix: Replace the paragraph with a shorter, pattern-first introduction using the actual forms (`я→мені`, `ти→тобі`, `ми→нам`, `ви→вам`).

[EXERCISE QUALITY] [SEVERITY: minor]  
Location: `activities/dative-pronouns.yaml`, `match-up-pronouns` — `хто → кому`  
Issue: This is off-plan. The plan calls for the personal-pronoun paradigm, and `воно→йому` should be tested explicitly instead.  
Fix: Replace `хто → кому` with `воно → йому`, and split `він / воно` so both planned forms are tested directly.

## Verdict: REVISE
A critical grammar error is teaching wrong Ukrainian, and the fill-in exercise logic is not shippable. The module structure is otherwise salvageable, so this is a revision pass, not a full rebuild.

<fixes>
- find: |
    Remember that in these structures, words like «холодно» or «цікаво» never change their form. They do not have a gender or plural ending, because there is no subject to agree with. They always end in the letter «-о».
  replace: |
    Remember that in these structures, words like «холодно» or «цікаво» never change their form. They do not have a gender or plural ending, because there is no subject to agree with. Many common state words end in «-о», but not all of them do: compare «холодно», «цікаво», «важко» with «треба» and «можна».

- find: |
    In the **давальний відмінок** (dative case), personal pronouns undergo a complete transformation. For the first and second person, the dative forms are built on an entirely different stem than their standard dictionary forms. You cannot simply attach a new ending to the word "я" or "ти". Instead, you must memorize these forms as a unique set. The word for "I" becomes **мені** (to me), and "you" becomes **тобі** (to you (informal)). In the plural, "we" becomes **нам** (to us), and "you" becomes **вам** (to you (formal/plural)).
  replace: |
    In the **давальний відмінок** (dative case), the first- and second-person pronouns should be learned as a compact set: **я→мені, ти→тобі, ми→нам, ви→вам**. These forms are not made by simply adding a regular ending to the nominative.

- find: |
    Мені сьогодні дуже холодно на вулиці, але вдома тепло. Тобі сумно читати цю стару книгу? Їй завжди весело грати з маленьким собакою, а йому нудно сидіти вдома. Нам цікаво вивчати українські традиції та культуру. Вам потрібно купити квитки на ранковий потяг заздалегідь. Їм дуже важко працювати без нового комп'ютера. Мені приємно бачити вас у нашому новому офісі.

    > *It is very cold for me outside today, but it is warm at home. Is it sad for you to read this old book? It is always fun for her to play with the small dog, and it is boring for him to sit at home. It is interesting for us to study Ukrainian traditions and culture. It is necessary for you to buy tickets for the morning train in advance. It is very hard for them to work without a new computer. It is pleasant for me to see you in our new office.*
  replace: |
    Мені сьогодні дуже холодно на вулиці, але вдома тепло. Тобі сумно читати цю стару книгу? Їй завжди весело грати з маленьким собакою, а йому нудно сидіти вдома. Нам цікаво вивчати українські традиції та культуру. Вам потрібно купити квитки на ранковий потяг заздалегідь. Їм дуже важко працювати без нового комп'ютера. Нам легко зрозуміти це правило. Мені можна сісти тут? Мені приємно бачити вас у нашому новому офісі.

    > *It is very cold for me outside today, but it is warm at home. Is it sad for you to read this old book? It is always fun for her to play with the small dog, and it is boring for him to sit at home. It is interesting for us to study Ukrainian traditions and culture. It is necessary for you to buy tickets for the morning train in advance. It is very hard for them to work without a new computer. It is easy for us to understand this rule. May I sit here? It is pleasant for me to see you in our new office.*

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
      - sentence: У мами день народження. Що ти даруєш ____?
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
        - їй
        - йому
        - їм
      - sentence: Учитель пояснює нове правило всьому класу. Він пояснює його ____.
        answer: нам
        options:
        - вам
        - нам
        - їм
      - sentence: Пані Олено, я показую це фото ____.
        answer: вам
        options:
        - тобі
        - нам
        - вам
</fixes>