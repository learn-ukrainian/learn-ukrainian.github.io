## Linguistic Scan
- Critical text corruption in `На ринку`: `українська граматикаقيقي пропонує вам одразу два рівноцінні варіанти...` contains a stray non-Ukrainian fragment `قيقي`.
- Critical text corruption in `Підсумок`: `обвно об'єктивно` contains a broken extra token `обвно`.
- No definite Russianisms, Surzhyk, calques, or paronym errors found beyond those corruptions.

## Exercise Check
Six markers are present, evenly spread, and each comes after the relevant teaching section:
`fill-in` after `На ринку`, `quiz` after `У магазині`, `sentence-builder` after `На пошті і в банку`, `match-up` after `Послуги`, and `dialogue-completion` plus `free-write` after `Скарга і відгук`.
No inline DSL exercise logic appears in the module text itself, so marker placement is the main thing to review here. Placement is good.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned H2 sections are present, but the comparative-grammar section says `одразу два рівноцінні варіанти`, while the plan/self-check require `за/від/ніж`; the planned full store transaction dialogue is also not actually delivered in one coherent scene. |
| 2. Linguistic accuracy | 7/10 | No clear Russianisms/Surzhyk found, but two critical corruptions remain: `граматикаقيقي` and `обвно`. |
| 3. Pedagogical quality | 6/10 | The module gives rich contexts and examples, but it under-teaches a key planned grammar point by omitting the `від` comparison pattern and never models the full enter-to-exit shop dialogue promised in the plan. |
| 4. Vocabulary coverage | 9/10 | Required plan vocabulary is well represented in prose: `знижка`, `готівка`, `картка`, `чек`, `повернення`, `гарантія`, `розмір`, `примірочна`, `посилка`, `обмін валют`, `курс`, `ремонт`, `бракований`. |
| 5. Exercise quality | 8/10 | Marker inventory is complete and well placed after relevant teaching sections; no marker is prematurely placed. |
| 6. Engagement & tone | 7/10 | The module has concrete Ukrainian detail (`Бессарабський ринок`, `Привоз`, `Нова Пошта`, `Укрпошта`) and teacher warmth without gamified fluff. |
| 7. Structural integrity | 8/10 | All H2 headings from the plan are present and ordered correctly, and the deterministic word count is above target; the main structural blemish is the two visible text-corruption artifacts in running prose. |
| 8. Cultural accuracy | 5/10 | Some claims overreach: `Кожен українець має ... «Дія»`, the supermarket checkout models `Решти не треба` as normal, and the return section states a passport is obligatorily required. |
| 9. Dialogue & conversation quality | 7/10 | Dialogues have named speakers and multiple turns, but `У магазині` still lacks the single full shopping dialogue from greeting to payment that the plan explicitly asked for. |

## Findings
- `[LINGUISTIC ACCURACY] [SEVERITY: critical]` Location: `українська граматикаقيقي пропонує вам одразу два рівноцінні варіанти побудови такого речення.` Issue: the sentence contains a corruption artifact, and it also contradicts the plan by teaching only two comparison patterns instead of three. Fix: remove `قيقي`, change `два` to `три`, and add a third `від` example.
- `[PLAN ADHERENCE] [SEVERITY: major]` Location: `А тепер чітко уявіть, що ви зайшли у великий сучасний магазин одягу...` plus the later cashier-only dialogue. Issue: the plan requires `a full shopping scenario from entering the store to leaving`, but the section gives explanation plus a checkout subscene, not one coherent shop dialogue with consultant, fitting room, comparison, decision, and payment. Fix: insert one compact multi-turn store dialogue covering that whole sequence.
- `[LINGUISTIC ACCURACY] [SEVERITY: critical]` Location: `обвно об'єктивно оцінюючи їх за ціною та загальною якістю`. Issue: `обвно` is a broken token. Fix: delete it.
- `[CULTURAL ACCURACY] [SEVERITY: major]` Location: `> — **Покупець:** Ви знаєте, решти не треба. Залиште це собі...` and `Коротка фраза «Решти не треба» ... ідеально підходить ... на касі.` Issue: this teaches an atypical supermarket interaction; in ordinary retail checkout, the customer usually takes the change, and the module should not normalize tipping a supermarket cashier. Fix: remove `Решти не треба` from the supermarket dialogue and explicitly restrict that phrase to cafe/taxi/informal service contexts.
- `[CULTURAL ACCURACY] [SEVERITY: major]` Location: `Також старший касир обов'язково попросить ваш особистий **паспорт**...` Issue: this is too absolute; a document proving identity may be requested, but `обов'язково паспорт` overstates the rule. Fix: soften to `може попросити документ, що посвідчує особу`.
- `[CULTURAL ACCURACY] [SEVERITY: major]` Location: `Сьогодні українська сфера послуг є однією з найбільш цифровізованих у світі... Кожен українець має державний **додаток** «Дія»...` Issue: both claims are sweeping overgeneralizations. Fix: rewrite as `багато послуг... доступні онлайн` and `багато людей користуються`.

## Verdict: REVISE
The module is structurally usable and mostly strong on vocabulary/context, but it has two critical text corruptions and several major plan/cultural issues. That fails the PASS gate.

<fixes>
- find: "Коли ви хочете дуже впевнено сказати, що один обраний вами продукт є значно ліпшим за інший подібний товар, українська граматикаقيقي пропонує вам одразу два рівноцінні варіанти побудови такого речення."
  replace: "Коли ви хочете дуже впевнено сказати, що один обраний вами продукт є значно ліпшим за інший подібний товар, українська граматика пропонує вам одразу три природні варіанти побудови такого речення."
- find: "Другий абсолютно правильний і граматично точний спосіб — це використання популярного сполучника «ніж» та називного відмінка (Nominative). Наприклад, ви можете скласти таке речення: «Цей м'який домашній козячий сир **свіжіший, ніж той** фабричний твердий сир» *(This soft homemade goat cheese is fresher than that factory hard cheese)*. Дуже часто досвідчені покупці на базарі абсолютно впевнено і голосно стверджують:"
  replace: "Другий абсолютно правильний і граматично точний спосіб — це використання популярного сполучника «ніж» та називного відмінка (Nominative). Наприклад, ви можете скласти таке речення: «Цей м'який домашній козячий сир **свіжіший, ніж той** фабричний твердий сир» *(This soft homemade goat cheese is fresher than that factory hard cheese)*. Є і третій природний варіант — конструкція з прийменником «від»: «Цей сир **свіжіший від того** фабричного» *(This cheese is fresher than that factory-made one)*. Дуже часто досвідчені покупці на базарі абсолютно впевнено і голосно стверджують:"
- insert_after: "Постійне практичне використання вищого ступеня порівняння прикметників, таких як «менший», «більший», «довший», «ширший» або «коротший», є абсолютно незамінним і критично важливим під час ретельного вибору вашого ідеального щоденного гардероба."
  content: "Ось короткий повний діалог у магазині одягу, який моделює весь процес покупки. > — **Покупець:** Добрий день! Чи не могли б ви допомогти мені вибрати светр? > — **Продавець-консультант:** Добрий день! Звісно. Який розмір вас цікавить? > — **Покупець:** Мені потрібен менший розмір. І ще підкажіть, будь ласка, де примірочна. > — **Продавець-консультант:** Примірочна праворуч. Ось ще один варіант: цей светр дешевший, але той якісніший. > — **Покупець:** Дякую. Я приміряв обидва й візьму той темно-синій. Він сидить краще. > — **Продавець-консультант:** Чудовий вибір. Проходьте, будь ласка, до каси. > — **Покупець:** Добре. Можна оплатити карткою? І дайте, будь ласка, чек."
- find: "обвно об'єктивно"
  replace: "об'єктивно"
- find: "> — **Покупець:** Ви знаєте, решти не треба. Залиште це собі, гарного і спокійного вам дня! *(You know, keep the change. Keep it for yourself, have a good and peaceful day!)*"
  replace: "> — **Покупець:** Дуже дякую. Гарного і спокійного вам дня! *(Thank you very much. Have a calm and pleasant day!)*"
- find: "Коротка фраза «Решти не треба» є надзвичайно корисною і ввічливою, якщо ви бажаєте залишити дрібні чайові у вашій улюбленій кав'ярні. Також вона ідеально підходить, якщо ви просто не хочете довго чекати і брати зайві дрібні металеві монети на касі."
  replace: "Коротка фраза «Решти не треба» доречніша в кав'ярні, таксі або в інших неформальних сервісних ситуаціях. У звичайному магазині чи супермаркеті покупець зазвичай бере решту."
- find: "Також старший касир обов'язково попросить ваш особистий **паспорт** *(passport)* для правильного офіційного оформлення складної процедури повернення ваших коштів."
  replace: "Для оформлення повернення працівник магазину може також попросити документ, що посвідчує особу."
- find: "Сьогодні українська сфера послуг є однією з найбільш цифровізованих у світі. Більшість рутинних справ можна вирішити через смартфон. Кожен українець має державний **додаток** *(app/application)* «Дія», де зберігаються цифрові документи."
  replace: "Сьогодні багато послуг в Україні вже доступні онлайн. Чимало рутинних справ можна вирішити через смартфон. Багато людей користуються державним **додатком** *(app/application)* «Дія», де можуть зберігатися цифрові документи."
</fixes>