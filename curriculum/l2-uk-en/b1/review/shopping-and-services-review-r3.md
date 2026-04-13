## Linguistic Scan
- No Russianisms, Surzhyk, paronyms, or Russian letters (`ы/э/ё/ъ`) found on manual scan.
- `філянку` is a bad form here. Local dictionary/RAG checks confirm `філіжанка / філіжанку`, while `філянка` was not attested in the provided verification tools.
- The receipt explanation is factually outdated: it teaches that the seller must issue a printed paper fiscal receipt, but official DPS guidance says the fiscal check may be paper or electronic: [DPS, 2026-01-13](https://wvp.tax.gov.ua/media-ark/news-ark/971765.html), [DPS, 2024-02-26](https://vin.tax.gov.ua/media-ark/news-ark/print-758679.html).

## Exercise Check
All 6 planned activity types have corresponding markers:
`fill-in`, `quiz`, `sentence-builder`, `match-up`, `dialogue-completion`, `free-write`.

Placement is generally correct:
- `fill-in-shopping-dialogues` follows the market teaching.
- `quiz-transaction-phrases` follows the store/payment teaching.
- `sentence-builder-comparison` follows the delivery/bank comparison section.
- `match-up-agent-workplace` follows the services/word-formation section.
- `dialogue-completion-complaint` and `free-write-service-review` both follow the complaint/review section.

No exercise-marker mismatches found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers the planned domains and required vocab well, but the store section never delivers the planned full scenario “from entering the store to leaving”; it moves from explanation to a cashier dialogue instead. |
| 2. Linguistic accuracy | 6/10 | `філянку` is non-standard/typo-level bad here, and the receipt paragraph incorrectly teaches that the buyer always gets a printed paper check. |
| 3. Pedagogical quality | 7/10 | There is plenty of contextualized language, but the store section explains shopping language at length without giving the integrated try-on/compare/pay dialogue promised by the plan. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is broadly present in prose: `знижка`, `готівка`, `картка`, `чек`, `повернення`, `гарантія`, `розмір`, `примірочна`, `посилка`, `обмін валют`, `курс`, `ремонт`, `бракований`. |
| 5. Exercise quality | 9/10 | All planned activity types are present as markers and are placed after the relevant teaching sections. |
| 6. Engagement & tone | 6/10 | The module has real cultural detail, but some prose is inflated with low-value filler such as “На гарне завершення нашої сьогоднішньої важливої теми...”. |
| 7. Structural integrity | 9/10 | All H2 sections are present and ordered correctly; the pipeline word count is 5487, which is safely above the 4000 target. |
| 8. Cultural accuracy | 8/10 | The module is strongly Ukrainian-centered overall, but the supermarket cashier dialogue models “Решти не треба. Залиште це собі,” which is not a normal retail script. |
| 9. Dialogue & conversation quality | 7/10 | The market and service dialogues are usable, but the shop section lacks the promised end-to-end shopping conversation, and the cashier exchange becomes unrealistic at the tip line. |

## Findings
1. [Linguistic accuracy] [SEVERITY: critical]  
Location: “Це традиційне місце, де ви можете спокійно випити філянку ароматної кави.”  
Issue: `філянку` is not the standard word here; the expected form is `філіжанку`.  
Fix: Replace `філянку` with `філіжанку`.

2. [Linguistic accuracy] [SEVERITY: critical]  
Location: “Після кожної успішної транзакції та повної оплати продавець завжди суворо зобов'язаний видати вам офіційний друкований фіскальний чек... Цей маленький паперовий документ...”  
Issue: This teaches an outdated factual rule. Official DPS guidance dated January 13, 2026 and February 26, 2024 says a fiscal check may be paper or electronic, not only printed on paper: [1](https://wvp.tax.gov.ua/media-ark/news-ark/971765.html), [2](https://vin.tax.gov.ua/media-ark/news-ark/print-758679.html).  
Fix: Change the explanation to “фіскальний чек у паперовій або електронній формі”.

3. [Plan adherence] [SEVERITY: major]  
Location: Store section paragraph beginning “А тепер чітко уявіть, що ви зайшли у великий сучасний магазин одягу...”  
Issue: The plan explicitly calls for an extended store dialogue from greeting to asking for help, trying on, comparing options, deciding, and paying. This paragraph explains the language but does not actually model that full sequence.  
Fix: Replace the explanatory paragraph with a compact integrated shopping scenario that includes greeting, size request, fitting room, comparison, decision, and payment.

4. [Engagement & tone] [SEVERITY: major]  
Location: “На гарне завершення нашої сьогоднішньої важливої теми, давайте дуже уважно прочитаємо невелику, але надзвичайно цікаву розповідь...”  
Issue: This is padding rather than teaching; it spends words on generic emphasis instead of new language value.  
Fix: Replace it with a short instruction that names the task and the target language clearly.

5. [Dialogue & conversation quality] [SEVERITY: major]  
Location: “— **Покупець:** Ви знаєте, решти не треба. Залиште це собі...” and the follow-up paragraph explaining that phrase after a supermarket cashier dialogue.  
Issue: This is not a normal supermarket script; a cashier does not normally keep a customer’s change as a personal tip. It misleads the learner about real retail interaction.  
Fix: Remove the tip line from the supermarket dialogue and restrict “Решти не треба” to café/taxi-type contexts.

## Verdict: REVISE
Critical factual/linguistic errors are present, and several major plan/pedagogy/dialogue issues need correction. This is not a reject-level rebuild, but it is not shippable as-is.

<fixes>
- find: |
    Це традиційне місце, де ви можете спокійно випити філянку ароматної кави.
  replace: |
    Це традиційне місце, де ви можете спокійно випити філіжанку ароматної кави.

- find: |
    Після кожної успішної транзакції та повної оплати продавець завжди суворо зобов'язаний видати вам офіційний друкований фіскальний **чек** *(receipt)*. Цей маленький паперовий документ є надзвичайно важливим для споживача, адже він легально підтверджує факт вашої законної покупки.
  replace: |
    Після кожної успішної транзакції та повної оплати продавець має видати вам фіскальний **чек** *(receipt)* у паперовій або електронній формі. Цей документ є надзвичайно важливим для споживача, адже він підтверджує факт покупки.

- find: |
    А тепер чітко уявіть, що ви зайшли у великий сучасний магазин одягу. Ви вибрали гарний теплий светр, але вам обов'язково потрібно його **приміряти** *(to try on)* перед покупкою. Для цього вам завжди потрібна спеціальна зручна кабінка, яка називається **примірочна** *(fitting room)*. Часто в житті буває так, що обрана річ вам зовсім не підходить. Тоді вам терміново необхідний інший правильний **розмір** *(size)*. Ви можете впевнено звернутися до продавця-консультанта і прямо запитати: «Вибачте, підкажіть, де у вас знаходиться примірочна?». Після швидкої примірки ви можете виявити, що цей новий светр **завеликий** *(too big)* або ж навпаки — трохи замалий. Тоді ви дуже ввічливо кажете: «Мені потрібен інший розмір. Цей светр завеликий, чи є у вас менший варіант?». Також ви можете детально розпитати про матеріал, з якого професійно зшитий одяг. Наприклад: «Яка це **тканина** *(fabric)*? Це стовідсоткова натуральна бавовна чи звичайна синтетика?». Постійне практичне використання вищого ступеня порівняння прикметників, таких як «менший», «більший», «довший», «ширший» або «коротший», є абсолютно незамінним і критично важливим під час ретельного вибору вашого ідеального щоденного гардероба.
  replace: |
    А тепер уявіть повну сцену в магазині одягу: ви заходите, просите про допомогу, знаходите **примірочну** *(fitting room)*, порівнюєте моделі й доходите до каси. Наприклад: «Добрий день, чи є цей светр у більшому розмірі?», «Примірочна праворуч», «Цей светр якісніший, але дорожчий за той. Чи є дешевший варіант?», «Я візьму перший. Можна оплатити карткою?». Так ви відпрацьовуєте слова **розмір** *(size)*, **примірочна** *(fitting room)* і **тканина** *(fabric)* разом із формами «більший», «менший», «дешевший» та «якісніший».

- find: |
    На гарне завершення нашої сьогоднішньої важливої теми, давайте дуже уважно прочитаємо невелику, але надзвичайно цікаву розповідь про типову метушливу суботу на гамірному українському базарі. Цей живий і багатий текст чудово допоможе вам дуже чітко побачити всю пройдену сьогодні граматику в її реальній повсякденній практичній дії.
  replace: |
    На завершення прочитаймо коротку розповідь про типову суботу на українському базарі. У ній ви побачите в дії лексику теми та ступені порівняння.

- find: |
    > — **Покупець:** Ви знаєте, решти не треба. Залиште це собі, гарного і спокійного вам дня! *(You know, keep the change. Keep it for yourself, have a good and peaceful day!)*
  replace: |
    > — **Покупець:** Дуже дякую. Гарного і спокійного вам дня! *(Thank you very much. Have a good and peaceful day!)*

- find: |
    Коротка фраза «Решти не треба» є надзвичайно корисною і ввічливою, якщо ви бажаєте залишити дрібні чайові у вашій улюбленій кав'ярні. Також вона ідеально підходить, якщо ви просто не хочете довго чекати і брати зайві дрібні металеві монети на касі.
  replace: |
    Коротка фраза «Решти не треба» доречніша в кав'ярні, таксі або в інших неформальних сервісних ситуаціях, де люди іноді залишають дрібну суму. У звичайному магазині чи супермаркеті покупець зазвичай бере решту.
</fixes>