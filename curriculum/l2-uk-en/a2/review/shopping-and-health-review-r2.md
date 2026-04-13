## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or Russian-only characters (`ы э ё ъ`) detected in the module prose or activity YAML.

Critical problems found:
- `Another common word is the prefix **пів** (half).`  
  `пів` here is not a prefix; Grade 6 textbook data in the repo treats it as `числівник пів` used with a following noun.
- `У мене дуже сильно болить горло і голова.`  
  This has bad agreement/syntax for coordinated subjects; it should be recast.
- Activity explanation: `Яблука — це однина. Треба використовувати множину: кілограм яблук.`  
  This is factually wrong: `яблука` is plural.

## Exercise Check
All 4 planned marker IDs are present, they match the plan exactly, and they are placed after the relevant teaching sections:
- `fill-in-complete-market-dialogue-lines-with-correct-quantity-genitive-forms`
- `quiz-choose-the-correct-genitive-phrase-for-health-complaints-and-remedies`
- `match-up-match-health-problems-to-their-remedies`
- `true-false-judge-whether-shopping-and-health-phrases-use-the-genitive-correctly`

Marker placement is fine. The problems are in the generated exercise logic:
- The inline fill-in exercise is gameable: all 8 correct options are in first position.
- The match-up exercise drifts away from the planned focus `ліки від... / краплі від...` and uses generic advice pairs instead.
- The true/false block contains a false grammar explanation: `Яблука — це odнина`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The three planned H2 sections are present and required vocabulary is used, but repo search on the module text returned 0 hits for plan-specified exemplars `банка`, `меду`, `алергія на ліки`, `від алергії`, `болить від холоду`. |
| 2. Linguistic accuracy | 5/10 | The prose teaches `пів` as “the prefix **пів**”, the doctor dialogue has `У мене дуже сильно болить горло і голова`, and the activity explanation says `Яблука — це однина`. |
| 3. Pedagogical quality | 6/10 | The market section has good example density, but core explanation accuracy is undermined by the wrong `пів` rule and by exercise items that reward answer-position guessing instead of case knowledge. |
| 4. Vocabulary coverage | 8/10 | All required plan words appear naturally in prose: `ринок`, `кілограм`, `пляшка`, `здоров'я`, `температура`, `рецепт`, `аптека`, `ліки`, `кашель`, `апетит`; recommended words also appear. |
| 5. Exercise quality | 4/10 | Marker count and placement are correct, but the fill-in block has every answer in slot 1, the match-up block includes non-remedy advice pairs like `Мене нудить` → `Вам треба пити воду`, and one true/false explanation teaches wrong grammar. |
| 6. Engagement & tone | 8/10 | The teacher voice is calm and usable, with concrete market details like tasting apples, asking price, paying, and getting change. |
| 7. Structural integrity | 9/10 | All planned sections are present and ordered correctly, markers are clean, and the pipeline word count is 2857, which is above target. |
| 8. Cultural accuracy | 9/10 | Kyiv market / doctor / pharmacy contexts are localized and not Russia-centered; no false cultural framing stood out. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers are used throughout, and the market dialogue is the strongest: it includes greeting, choosing, tasting, pricing, payment, and leave-taking. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `На ринку: скільки вам?` — `Another common word is the prefix **пів** (half).`  
Issue: This teaches the wrong grammar category. In this use, `пів` is not a prefix.  
Fix: Change it to `Another common quantity word is the numeral **пів** (half).`

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `У лікаря: що вас турбує?` — `У мене дуже сильно болить горло і голова.`  
Issue: Bad agreement/syntax with coordinated singular nouns. Learners should not be given this as a model.  
Fix: Replace it with `У мене дуже сильно болить горло, і болить голова.`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: module-wide absence check; searches in the module text returned 0 hits for `банка`, `меду`, `алергія на ліки`, `від алергії`, `болить від холоду`.  
Issue: Several plan-promised genitive exemplars never appear in the prose, so coverage is incomplete.  
Fix: Add those phrases into existing example sentences: `банка меду`, `Чи є алергія на ліки?`, `болить від холоду`, `кашель від алергії`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: inline fill-in block beginning `Дайте мені, будь ласка, один кілограм ____.`  
Issue: All 8 correct answers are in option position 1, so the exercise is trivially gameable.  
Fix: Shuffle option order so the correct answer position varies item by item.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: match-up block — `Мене нудить. → Вам треба пити воду.`, `Я хочу спати. → Вам треба більше відпочивати.`, `Мені погано. → Вам треба йти до лікаря.`  
Issue: The plan says this exercise should match health problems to remedies using `ліки від... / краплі від...`; these pairs drift into generic advice and stop testing the target pattern.  
Fix: Replace those pairs with remedy-based genitive pairs, e.g. `У мене алергія. → Ось ліки від алергії.`

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: true/false explanation — `Яблука — це однина. Треба використовувати множину: кілограм яблук.`  
Issue: This explanation is factually wrong. `Яблука` is plural.  
Fix: Replace it with `Яблука — це множина. Треба використовувати родовий відмінок множини: кілограм яблук.`

## Verdict: REVISE
REVISE. There are critical teach-the-wrong-form errors in both prose and exercise explanations, plus major exercise-design problems and incomplete coverage of several plan-promised exemplars.

<fixes>
- find: "Another common word is the prefix **пів** (half)."
  replace: "Another common quantity word is the numeral **пів** (half)."

- find: "У мене дуже сильно болить горло і голова."
  replace: "У мене дуже сильно болить горло, і болить голова."

- find: "Я хочу випити велику склянку соку. Дайте мені, будь ласка, шматок свіжого хліба. Ця велика пластикова пляшка мінеральної води коштує сорок гривень. Вчора я купив пів літра молока. Моя сестра випила чашку зеленого чаю без цукру."
  replace: "Я хочу випити велику склянку соку. Дайте мені, будь ласка, шматок свіжого хліба. Мені також потрібна банка меду. Ця велика пластикова пляшка мінеральної води коштує сорок гривень. Вчора я купив пів літра молока. Моя сестра випила чашку зеленого чаю без цукру."

- find: "> — **Лікар:** Чи є у вас температура? *(Do you have a fever?)*"
  replace: "> — **Лікар:** Чи є у вас температура? Чи є алергія на ліки? *(Do you have a fever? Do you have any allergy to medicine?)*"

- find: "У мене зараз сильно болить горло від холодної води. Цей жахливий кашель у мого колеги з'явився від пилу на будівництві. Моя подруга скаржиться, що у неї болить голова від гучної музики. Ввечері ми підемо купувати ефективні краплі від нежиті."
  replace: "У мене зараз сильно болить горло від холоду. У мого колеги кашель від алергії на пил. Моя подруга скаржиться, що у неї болить голова від гучної музики. Ввечері ми підемо купувати ефективні краплі від нежиті."

- find: "Яблука — це однина. Треба використовувати множину: кілограм яблук."
  replace: "Яблука — це множина. Треба використовувати родовий відмінок множини: кілограм яблук."

- find: |
    - id: fill-in-complete-market-dialogue-lines-with-correct-quantity-genitive-forms
      type: fill-in
      instruction: Вставте правильну форму слова
      items:
      - sentence: Дайте мені, будь ласка, один кілограм ____.
        answer: помідорів
        options:
        - помідорів
        - помідора
        - помідору
      - sentence: Я хочу купити пів кіло ____.
        answer: огірків
        options:
        - огірків
        - огірка
        - огірки
      - sentence: Мені потрібен десяток ____.
        answer: яєць
        options:
        - яєць
        - яйця
        - яйців
      - sentence: Дайте шматок свіжого ____.
        answer: хліба
        options:
        - хліба
        - хлібу
        - хліб
      - sentence: Мені потрібна пляшка ____.
        answer: води
        options:
        - води
        - воду
        - водою
      - sentence: Купи, будь ласка, кілограм ____.
        answer: цукру
        options:
        - цукру
        - цукор
        - цукром
      - sentence: З вас п'ять кілограмів ____.
        answer: картоплі
        options:
        - картоплі
        - картопля
        - картопель
      - sentence: Дайте мені велику склянку ____.
        answer: соку
        options:
        - соку
        - сік
        - соком
  replace: |
    - id: fill-in-complete-market-dialogue-lines-with-correct-quantity-genitive-forms
      type: fill-in
      instruction: Вставте правильну форму слова
      items:
      - sentence: Дайте мені, будь ласка, один кілограм ____.
        answer: помідорів
        options:
        - помідора
        - помідорів
        - помідору
      - sentence: Я хочу купити пів кіло ____.
        answer: огірків
        options:
        - огірка
        - огірки
        - огірків
      - sentence: Мені потрібен десяток ____.
        answer: яєць
        options:
        - яйця
        - яєць
        - яйців
      - sentence: Дайте шматок свіжого ____.
        answer: хліба
        options:
        - хліб
        - хлібу
        - хліба
      - sentence: Мені потрібна пляшка ____.
        answer: води
        options:
        - водою
        - води
        - воду
      - sentence: Купи, будь ласка, кілограм ____.
        answer: цукру
        options:
        - цукром
        - цукру
        - цукор
      - sentence: З вас п'ять кілограмів ____.
        answer: картоплі
        options:
        - картопель
        - картоплі
        - картопля
      - sentence: Дайте мені велику склянку ____.
        answer: соку
        options:
        - сік
        - соком
        - соку

- find: |
    - id: match-up-match-health-problems-to-their-remedies
      type: match-up
      instruction: З'єднайте скаргу з рішенням
      pairs:
      - left: У мене кашель.
        right: Ось ліки від кашлю.
      - left: У мене нежить.
        right: Ось краплі від нежиті.
      - left: У мене болить голова.
        right: Ось таблетки від болю.
      - left: Я хочу бути здоровим.
        right: Ось вітаміни для здоров'я.
      - left: Мене нудить.
        right: Вам треба пити воду.
      - left: У мене болить горло.
        right: Пийте багато теплої води.
      - left: Я хочу спати.
        right: Вам треба більше відпочивати.
      - left: Мені погано.
        right: Вам треба йти до лікаря.
  replace: |
    - id: match-up-match-health-problems-to-their-remedies
      type: match-up
      instruction: З'єднайте скаргу з рішенням
      pairs:
      - left: У мене кашель.
        right: Ось ліки від кашлю.
      - left: У мене нежить.
        right: Ось краплі від нежиті.
      - left: У мене болить голова.
        right: Ось таблетки від головного болю.
      - left: Я хочу бути здоровим.
        right: Ось вітаміни для здоров'я.
      - left: У мене алергія.
        right: Ось ліки від алергії.
      - left: У мене болить горло.
        right: Ось спрей від болю в горлі.
      - left: У мене температура.
        right: Ось ліки від температури.
      - left: У мене болить живіт.
        right: Ось таблетки від болю в животі.
</fixes>