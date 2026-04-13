## Linguistic Scan
No Russianisms, Surzhyk, paronym errors, or forbidden Russian letters found.

Found factual grammar-teaching errors:

1. Scenario 1: `Для опису місця ми завжди використовуємо місцевий відмінок.`
Issue: this is too broad and false. Location in Ukrainian is not always Locative; the same section already uses `біля вікна`, which is Genitive.

2. Scenario 1: `We also use it to express quantity when asking questions or stating exactly how many rooms are in a house.`
Issue: this overstates Genitive usage. Later the module correctly says `два столи`, `три ліжка`, `чотири стільці`, so the explanation contradicts its own examples.

3. Scenario 2: `The question "What time is it?" is «Котра година?». It uses the Nominative case and an ordinal number.`
Issue: `котра` here is not an ordinal numeral; this teaches the wrong grammar.

4. Scenario 2: `Прийменник «з» вимагає Орудного відмінка.`
Issue: false as a general rule. `з` can govern different cases; here only the comitative meaning (`з родиною`) takes Instrumental.

## Exercise Check
Four markers are present, matching the four `activity_hints` in the plan:

- `fill-in-home-description` after Scenario 1
- `quiz-daily-routine-cases` after Scenario 2
- `match-up-routine-times` after Scenario 2
- `error-correction-cases-routine` after Scenario 3

Placement is sensible and spread through the module rather than clustered at the end. Marker IDs match the planned exercise types and focuses closely enough. No inline DSL exercises are present, so distractor logic and answer-key quality cannot be audited from this content alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The section structure and word budgets track the plan, and required/recommended vocabulary is covered. But the plan calls for characteristic-description patterns, and Scenario 1 gives `дерев'яний стіл` rather than explicitly teaching the planned `стіл з дерева / кімната з великими вікнами` style; the speaking-task tip about room counts also clashes with the model answer `У квартирі є три кімнати: велика спальня, вітальня і маленька кухня.` |
| 2. Linguistic accuracy | 6/10 | No Russianisms found, but there are several factual grammar errors: `Для опису місця ми завжди використовуємо місцевий відмінок`, `It uses the Nominative case and an ordinal number`, and `Прийменник «з» вимагає Орудного відмінка.` |
| 3. Pedagogical quality | 6/10 | The module has good example density, but key explanations overgeneralize and misteach: `We also use it to express quantity ... stating exactly how many rooms are in a house`, `Для опису місця ми завжди...`, and the wrong analysis of `Котра година?`. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary appears naturally in prose: `помешкання`, `кімната`, `кухня`, `спальня`, `вітальня`, `меблі`, `розпорядок дня`, `вставати`, `снідати`, `лягати спати`. Recommended items also appear: `балкон`, `коридор`, `килим`, `пригощатися`, `господар`. |
| 5. Exercise quality | 8/10 | Marker coverage matches the plan, and placement follows the teaching sequence. Actual generated exercise content is not present here, so answer logic and distractor quality cannot be verified. |
| 6. Engagement & tone | 8/10 | The tone is mostly teacherly and useful, with concrete situations like a house tour, routine description, and visiting friends. Some prose is padded by generic lines such as `Mastering this case is essential for smooth communication.` |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered correctly. The pipeline word count is 2968, well above the 2000 target, and there are no dangling sections or obvious formatting artifacts. |
| 8. Cultural accuracy | 8/10 | Hospitality details are solid (`гостинці`, `Пригощайтеся!`, dinner visit scenario). The tip about `двокімнатна квартира` is useful, but it is undermined by the model answer counting the kitchen inside `три кімнати`. |
| 9. Dialogue & conversation quality | 8/10 | Dialogues have named speakers and plausible home/daily-life contexts. Scenario 1 is somewhat inventory-driven, but Scenario 3 feels more natural and socially grounded. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Scenario 1, `Для опису місця ми завжди використовуємо місцевий відмінок.`  
Issue: This is factually wrong. Ukrainian location expressions also use other cases, including Genitive (`біля вікна`) and Instrumental (`за столом`).  
Fix: Narrow the rule to `у/в` and `на` constructions instead of presenting Locative as universal.

[PEDAGOGICAL QUALITY] [SEVERITY: critical]  
Location: Scenario 1, `We also use it to express quantity when asking questions or stating exactly how many rooms are in a house.`  
Issue: This misstates Genitive usage and contradicts the module’s own later explanation that `2/3/4` take Nominative plural.  
Fix: Limit the claim to `скільки`, `багато`, and similar quantity words.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Scenario 2, `The question "What time is it?" is «Котра година?». It uses the Nominative case and an ordinal number.`  
Issue: `котра` is not an ordinal numeral here; this teaches the wrong grammatical analysis.  
Fix: Explain that the phrase uses the interrogative word `котра` plus the noun `година`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Scenario 2, `Прийменник «з» вимагає Орудного відмінка.`  
Issue: This is false as a general rule. In this sentence the Instrumental is required because `з` means accompaniment, not because `з` always governs Instrumental.  
Fix: Qualify the rule: `У значенні «разом із кимось»...`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Scenario 1 furniture paragraph, `... м'яке **крісло** (armchair) та дерев'яний стіл.`  
Issue: The plan explicitly wants characteristic-description patterns like `стіл з дерева` and `кімната з великими вікнами`, but the prose does not teach that pattern directly.  
Fix: Revise this paragraph to include those constructions in context.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: Speaking task model answer, `У квартирі є три кімнати: велика спальня, вітальня і маленька кухня.`  
Issue: This conflicts with the immediately preceding tip that room counts usually exclude the kitchen in Ukrainian housing talk.  
Fix: Change the model answer so the room count and listed spaces are consistent with the tip.

## Verdict: REVISE
The module is structurally complete and vocabulary-rich, but it contains multiple critical grammar-teaching errors. That alone blocks PASS, and several scored dimensions fall below 9.

<fixes>
- find: "Для опису місця ми завжди використовуємо місцевий відмінок."
  replace: "Для опису місця з прийменниками **у/в** і **на** ми зазвичай використовуємо місцевий відмінок."
- find: "We also use it to express quantity when asking questions or stating exactly how many rooms are in a house."
  replace: "We also use it to express quantity in questions like «Скільки у вас кімнат?» and after quantity words like «багато»."
- find: "The question \"What time is it?\" is «Котра година?». It uses the Nominative case and an ordinal number."
  replace: "The question \"What time is it?\" is «Котра година?». It uses the interrogative word «котра» and the noun «година», not an ordinal numeral."
- find: "Коли я вдома, я йду у ванну кімнату. Тут ми використовуємо Знахідний відмінок для напрямку. Потім я їду на роботу автобусом. Слово «автобус» стоїть в Орудному відмінку, бо це засіб транспорту. Я завжди **снідаю** з родиною або з друзями. Прийменник «з» вимагає Орудного відмінка."
  replace: "Коли я вдома, я йду у ванну кімнату. Тут ми використовуємо Знахідний відмінок для напрямку. Потім я їду на роботу автобусом. Слово «автобус» стоїть в Орудному відмінку, бо це засіб транспорту. Я завжди **снідаю** з родиною або з друзями. У значенні «разом із кимось» прийменник «з» вимагає Орудного відмінка."
- find: "Мої нові меблі дуже зручні та красиві. У кімнаті стоїть великий **диван** (sofa), м'яке **крісло** (armchair) та дерев'яний стіл. Біля стола є зручний стілець, а біля стіни стоїть висока шафа. У спальні ми поставили широке ліжко. На стіні висить полиця, яскравий **килим** (rug) і дзеркало."
  replace: "Мої нові меблі дуже зручні та красиві. У кімнаті з великими вікнами стоїть великий **диван** (sofa), м'яке **крісло** (armchair) та стіл з дерева. Біля стола є зручний стілець, а біля стіни стоїть висока шафа. У спальні ми поставили широке ліжко. На стіні висить полиця, яскравий **килим** (rug) і дзеркало."
- find: "У квартирі є три кімнати: велика спальня, вітальня і маленька кухня."
  replace: "У квартирі є дві кімнати: велика спальня і вітальня. Кухня маленька, але затишна."
</fixes>