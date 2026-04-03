## Linguistic Scan
No linguistic errors found. The text uses natural Ukrainian syntax, correctly applies cases (e.g., "зроблено нову роботу" in Accusative), and accurately explains the stylistic preference for the active voice. VESUM verified words exist as expected.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz, Identify voice... -->`: **Misplaced.** Placed right after Section 1, but the -ся and -но/-то forms are not actually taught until Sections 2 and 3. Testing learners on forms they haven't learned yet breaks the PPP sequence.
- `<!-- INJECT_ACTIVITY: fill-in... -->`: Placed correctly after Section 3.
- `<!-- INJECT_ACTIVITY: match-up... -->`: Placed correctly after Section 4.
- `<!-- INJECT_ACTIVITY: error-correction... -->`: Placed correctly after Section 4.
- `<!-- INJECT_ACTIVITY: sentence-builder... -->`: Placed correctly after Section 5.

All markers match the `activity_hints` from the plan exactly in type, focus, and item count.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All sections from the plan are covered beautifully. The Avramenko and Zabolotnyi textbook references are woven directly into the explanations. |
| 2. Linguistic accuracy | 10/10 | No Russianisms or calques. Correctly enforces the accusative object with -но/-то forms ("Зроблено нову роботу"). |
| 3. Pedagogical quality | 9/10 | The prose flows well from concept to examples, with excellent contrastive analysis of the three constructions. |
| 4. Vocabulary coverage | 10/10 | Target vocabulary is integrated smoothly into the prose without feeling like forced lists. |
| 5. Exercise quality | 8/10 | The quiz marker for identifying all three voices is placed prematurely before two of the voices are taught. |
| 6. Engagement & tone | 6/10 | The text suffers from heavy "fluff" and overwrought enthusiasm: "абсолютно унікальну, дуже виразну і стилістично красиву", "фантастичній природності", "магічним чином зупиняє час". This violates the rule against generic meta-commentary. |
| 7. Structural integrity | 8/10 | The module is 4785 words, which is ~20% over the target of 4000 words. |
| 8. Cultural accuracy | 10/10 | Excellent framing of the passive voice as "bureaucratese" (канцелярит) vs the natural Ukrainian active voice. |
| 9. Dialogue & conversation quality | 9/10 | The architect dialogue perfectly demonstrates the formal, official tone where passive voice actually belongs. |

## Findings

[Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: quiz, Identify voice (активний стан, пасивний -ся, or пасивний -но/-то), 10 items -->` after Section 1.
Issue: Pedagogical sequence violation. The quiz asks learners to identify -ся and -но/-то constructions immediately after Section 1, but these forms are not formally taught until Sections 2 and 3.
Fix: Move the quiz marker to the end of Section 4 ("Порівняння трьох конструкцій").

[Engagement & tone] [Major]
Location: Section 3 ("Українська мова має одну абсолютно унікальну, дуже виразну і стилістично красиву граматичну конструкцію, яка найкраще і найточніше передає повністю завершену дію...")
Issue: Overwrought, fluffy language ("corporate-speak" enthusiasm) that pads the word count and violates tone guidelines.
Fix: Remove the excessive adjectives. Replace with: "Українська мова має унікальну граматичну конструкцію, яка точно передає завершену дію та її конкретний результат."

[Engagement & tone] [Minor]
Location: Section 3 ("Цей граматичний процес відбувається абсолютно передбачувано, регулярно і практично без жодних складних винятків...")
Issue: Fluffy padding.
Fix: Condense to: "Цей граматичний процес відбувається передбачувано і практично без винятків. Розгляньмо цю систему на кількох поширених прикладах:"

[Engagement & tone] [Minor]
Location: Section 3 ("а вже потім — на трохи драматичне і сумне **забуто**.")
Issue: Unnecessary emotional projection onto a grammar form.
Fix: Replace with: "а вже потім — на безособове **забуто**."

[Engagement & tone] [Major]
Location: Section 3 ("Головна відповідь повністю полягає в їхній фантастичній природності, органічності та надзвичайній легкості порівняно з дуже важкими, незграбними і штучними пасивними дієсловами на -ся.")
Issue: Extreme adjective stacking ("фантастичній природності", "надзвичайній легкості").
Fix: Condense to: "Головна причина полягає в їхній природності та легкості порівняно зі штучними пасивними дієсловами на -ся."

[Engagement & tone] [Major]
Location: Section 4 ("На найвищому, першому почесному місці завжди беззаперечно стоїть класичний активний стан... На другому місці впевнено і дуже міцно розташувалися...")
Issue: Overly dramatic framing of a grammar hierarchy.
Fix: Condense to a direct, professional explanation of the hierarchy of naturalness without the sports-announcer framing.

## Verdict: REVISE
The text is grammatically and pedagogically excellent, strictly adhering to the Avramenko and Zabolotnyi rules for Ukrainian passive constructions. However, it requires a revision to fix a critical pedagogical sequence error (testing concepts before teaching them) and to trim down significant descriptive "fluff" that pushes the word count 20% over budget.

<fixes>
- find: "tour!)*\n\n<!-- INJECT_ACTIVITY: quiz, Identify voice (активний стан, пасивний -ся, or пасивний -но/-то), 10 items -->\n\n## Пасив через зворотні дієслова"
  replace: "tour!)*\n\n## Пасив через зворотні дієслова"
- find: "<!-- INJECT_ACTIVITY: error-correction, Fix unnatural passive constructions by rewriting as active voice, 6 items -->\n\n## Практика: пасив у контексті"
  replace: "<!-- INJECT_ACTIVITY: error-correction, Fix unnatural passive constructions by rewriting as active voice, 6 items -->\n\n<!-- INJECT_ACTIVITY: quiz, Identify voice (активний стан, пасивний -ся, or пасивний -но/-то), 10 items -->\n\n## Практика: пасив у контексті"
- find: "Українська мова має одну абсолютно унікальну, дуже виразну і стилістично красиву граматичну конструкцію, яка найкраще і найточніше передає повністю завершену дію та її конкретний результат."
  replace: "Українська мова має унікальну граматичну конструкцію, яка точно передає завершену дію та її конкретний результат."
- find: "Цей граматичний процес відбувається абсолютно передбачувано, регулярно і практично без жодних складних винятків, які б вимагали довгого заучування. Уважно розгляньмо цю струнку і красиву систему на кількох дуже поширених, щоденних життєвих прикладах:"
  replace: "Цей граматичний процес відбувається передбачувано і практично без винятків. Розгляньмо цю систему на кількох поширених прикладах:"
- find: "а вже потім — на трохи драматичне і сумне **забуто**."
  replace: "а вже потім — на безособове **забуто**."
- find: "Головна відповідь повністю полягає в їхній фантастичній природності, органічності та надзвичайній легкості порівняно з дуже важкими, незграбними і штучними пасивними дієсловами на -ся."
  replace: "Головна причина полягає в їхній природності та легкості порівняно зі штучними пасивними дієсловами на -ся."
- find: "На найвищому, першому почесному місці завжди беззаперечно стоїть класичний **активний стан** *(active voice)*. Він найкраще підходить для ясного, зрозумілого, енергійного і динамічного висловлення ваших думок у будь-якій ситуації. На другому місці впевнено і дуже міцно розташувалися специфічні безпідметові безособові форми на -но/-то. Вони є абсолютно ідеальним, бездоганним інструментом, коли вам треба швидко повідомити про **доконаний факт** *(completed fact)* або якийсь важливий об'єктивний результат. Натомість третє, найнижче і найменш бажане місце займає **пасивний стан на -ся** *(passive with -ся)*."
  replace: "Найприроднішим для української мови є **активний стан** *(active voice)*. Він найкраще підходить для ясного висловлення думок у більшості ситуацій. На другому місці розташувалися безособові форми на -но/-то. Вони є чудовим інструментом, коли треба повідомити про **доконаний факт** *(completed fact)* або результат. Натомість третє, найменш бажане місце займає **пасивний стан на -ся** *(passive with -ся)*."
</fixes>
