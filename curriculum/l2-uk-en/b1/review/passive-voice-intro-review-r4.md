ேகthought
CRITICAL INSTRUCTION 1: Use specific MCP tools to check facts, especially vocabulary rules.
CRITICAL INSTRUCTION 2: I am using `mcp_rag_query_grac` or `mcp_rag_search_definitions` or just my general knowledge. Let me check the definition of `аншлаг`.

"повний аншлаг" is a common pleonasm (аншлаг means a notice that all tickets are sold). It's a minor error but a noticeable one in high-quality writing.
Another point:
"в орудному відмінку (instrumental case)" - the text says: "орудний відмінок *(instrumental case)*".
Let's check for any Russian letters or Surzhyk.
"Який же варіант обрати для повсякденної розмови?" (correct)
"Звідки ж беруться ці чудові слова?" (correct)
"Наприклад: «Усі старі речі зібрано (things are packed) у коробки»." (correct)

Let's look closely at the text.
Is there any Surzhyk?
"Щоб ваша українська мова звучала максимально природно та автентично, вам потрібно раз і назавжди запам'ятати просту «ієрархію натуральності»." -> "натуральність" is a bit awkward when "природність" was just used. Wait, the paragraph says "природно" -> "натуральності". This is a bit inconsistent. "Ієрархія природності" is better. Let's fix this just to be safe.

Let's check: "Під час утворення пасиву відбувається повна зміна синтаксичної структури: те, що раніше було прямим додатком, раптом стає підметом." (Correct).
"Щоб створити таку нову пасивну форму, ми беремо звичайне перехідне дієслово (transitive verb). Це таке спеціальне дієслово, яке завжди вимагає після себе прямого додатка у знахідному відмінку." (Correct).
"На цьому відповідальному етапі навчання вам дуже важливо раптом не заплутатися у складній українській граматиці." (Correct).

Let's check the words listed as NOT IN VESUM from the prompt data:
✗ Авраменко — NOT IN VESUM (Proper noun)
✗ Дніпро — NOT IN VESUM (Proper noun)
✗ Марія — NOT IN VESUM (Proper noun)
✗ Олександр — NOT IN VESUM (Proper noun)
✗ пов — NOT IN VESUM -> What is "пов"? Let's search the text.
"повний аншлаг" -> "повний" is a word.
"пов" -> maybe "пов'язаний"? The text has "пов’язаний". Wait, if the tokenizer split on the apostrophe, it would see "пов" and "язаний".
Ah, "пов’язаний". The apostrophe used in the text is `’` (Right Single Quotation Mark, U+2019) or `'` (Apostrophe).
VESUM might expect a specific apostrophe, or the tokenizer separated it. Let's look for "пов’язаний".
Text: `пов’язаний` -> Yes, this is correct Ukrainian.

Let's look for other potential issues:
"Добре слово дім будує. (active) → Поганим словом все руйнується. (passive with -ся)"
Did the text include this example from the plan?
Plan: "Добре слово дім будує. (active) → Поганим словом все руйнується. (passive with -ся)"
Text: I don't see this exact example. Let's search for "руйнується".
Text only has: "«Цей величезний багатоповерховий дім успішно будується вже майже два роки»." It missed the proverb example from the plan. It's a minor deduction for Plan Adherence.

Plan: "Цей товар продається у кожному магазині."
Text: "Цей популярний імпортний товар щодня успішно продається у кожному міському магазині". (Covered).

Plan: "Усі інгредієнти придбано."
Text: Not present exactly, but has "Квитки на потяг успішно куплено", "Усі старі речі зібрано".

Plan: "Учні написали диктант. → Диктант написано."
Text: Has "Уряд ухвалив закон. → Закон ухвалено." and "Архітектори будують...". Not the exact dictation example.

Plan: "Зроблено роботу (not *робота)."
Text: "«Цю цікаву книжку (Знахідний) швидко прочитано». Відчуваєте суттєву різницю? Слово «книжку» не стало підметом." (Covered).

Plan: "Ukrainian strongly prefers active voice (Заболотний Grade 8 p.95): 'Українська мова уникає пасивних конструкцій. Тому перевагу, де це можливо, слід надавати дієсловам активного стану.'"
Text: "Як зазначає підручник О. Заболотного для 8 класу, «українська мова уникає пасивних конструкцій. Тому перевагу, де це можливо, слід надавати дієсловам активного стану»." (Covered).

Plan: "From Авраменко Grade 11 p.81: 'Синтаксичні конструкції з формами на -но, -то.'"
Text: "Відомий і дуже шанований український мовознавець Олександр Авраменко у своєму підручнику звертає особливу увагу..." but doesn't quote "Синтаксичні конструкції...".

Plan: "Авраменко Grade 11 p.81 observes that Ukrainian speakers often find the agent awkward in -ся passives: 'Речення якої колонки звучать більш природно?' — active versions win. Use active when possible."
Text: "Відомий і дуже шанований український мовознавець Олександр Авраменко у своєму підручнику звертає особливу увагу саме на цю критичну стилістичну проблему." (Covered the concept well).

Let's check the definition of "канцелярит".
Text: "надмірне і бездумне використання пасиву... створює неприємне явище, яке називається канцелярит (bureaucratese)." (Correct).

Let's check "Пасив через зворотні дієслова" -> "По-перше, ми завжди використовуємо пасив, коли виконавець дії нам невідомий..."
"Потім ми просто додаємо до нього афікс -ся у самому кінці слова."
"Але хто ж тоді насправді фізично виконує цю дію, якщо граматичний підмет є пасивним?"
"Для чутливого вуха справжнього носія української мови такі довгі та громіздкі конструкції майже завжди звучать важко, дуже незграбно і відверто штучно."
This is all very good.

Let's look at the dialogue.
"Цей зал був побудований (was built) ще у 1960-х"
"Ці високі стіни були пофарбовані (were painted) минулого місяця"
"його буде відкрито (will be opened) для публіки вже завтра."
This is directly from the plan's dialogue motivation.

Is there any issue with "Ця цікава книга (Називний) була швидко прочитана"?
"Називний" should be "називний відмінок" or simply the text is fine. The text says:
"Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»."
It's acceptable pedagogical shorthand.

Let's check: "Перші квитки продано ще вчора ввечері. Ми з нетерпінням очікуємо на повний аншлаг."
"Аншлаг" is from German Anschlag (notice). In theater, it means all tickets are sold. "Повний аншлаг" is a pleonasm, but it's very commonly used in spoken Ukrainian. Still, for a high-quality B1 module, we can fix it to "справжній аншлаг" or just "аншлаг" to be perfectly stylish. Let's look up if "повний аншлаг" is considered an error by style guides.
I will query `mcp_rag_search_style_guide` for "повний аншлаг", though it yielded no results earlier. Let me just query Wikipedia or a general search. Actually, it's a known pleonasm, like "вільна вакансія" or "прейскурант цін". Let's fix it to "аншлаг".

Wait, let's look closer at the grammatical explanation.
"Знахідний відмінок (Accusative case)" vs "називний відмінок (Nominative case)". Capitalization: "Називний відмінок" shouldn't be capitalized in Ukrainian in the middle of a sentence unless it's a formal title, but often it is.
Text: "в таких українських реченнях принципово відсутній **називний відмінок** *(Nominative case)*." - lower case, correct.
Text: "залишається у **знахідному відмінку** *(Accusative case)*." - lower case, correct.
Text: "Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»." - capitalized here, acting as a label. Acceptable.

Let's review the rule about -но/-то and perfective aspect.
"Зроблено", "прочитано", "закрито" are from perfective verbs. Can we form it from imperfective? Yes, "роблено", "читано", but they are less common. The text focuses on the result (perfective), which is pedagogically correct for B1.

Is there any problem with "Цей популярний імпортний товар щодня успішно продається у кожному міському магазині"? No.

Let's check the use of "натуральності" vs "природності".
Text: "ієрархію натуральності"
"натуральність" implies being natural (organic vs artificial). "природність" is preferred for language ("природна мова"). I will fix this to "ієрархію природності".

Let's check the rule: "Завжди уважно перевіряйте це правило!". It's a good wrap-up.

Wait, are there any Russianisms?
"багатоповерховий" -> correct.
"співрозмовнику" -> correct.
"новосілля" -> correct.
"громадських просторів" -> correct.
"ретельно налаштовуємо" -> correct.
"розпродано" -> correct.
"гуртують" -> correct.
"відреставрований" -> correct.
"неповоротких" -> correct.

Let's read the section: "Чому автор цієї новини так активно та послідовно використовує форми на -но та -то?"
"Правильна відповідь ховається в меті журналістського тексту. Головне завдання репортера — чітко повідомити суспільству про подію або показати фінальний результат роботи. Читачам не важливо, який саме робітник монтував освітлення, або який депутат голосував за закон. Нам важливо лише те, що «музей відкрито», а «закон ухвалено». Фокус уваги свідомо зміщується з невідомого виконавця на конкретний об'єкт та статус завершеної дії. Якщо журналіст спробує переписати цей текст активним станом і скаже: «Міська рада ухвалила закон, будівельники завершили роботи, а куратори створили експозицію», його текст одразу стане занадто довгим. Він буде перевантажений зайвими деталями та втратить свій офіційний tone. Безособові конструкції допомагають зробити повідомлення лаконічним та професійним."
Wait! "офіційний tone".
**CRITICAL ERROR**: "tone" is an English word!
Let me check the exact text: "втратить свій офіційний tone".
Wow. The AI generated English word "tone" in the middle of a Ukrainian sentence without translation brackets! It should be "офіційний тон".
This is a critical linguistic/structural error.

Let me search for "tone" in the text to be absolutely sure.
"офіційний tone." -> Yes!
"втратить свій офіційний tone."
This must be fixed. "втратить свій офіційний тон."

Let's search for any other stray English words not in brackets or italics.
"The book is read"
"undergoes the action"
"bureaucratese"
"the -sya affix"
"transitive verb"
"instrumental case"
"intransitive verb — no direct object"
"passive voice"
"active voice"
"impersonal forms"
"default standard"
"state of an object"
"semantic nuances"
"housewarming"
"temptation"
"Palace of Culture"
"public spaces"

Is "tone" in brackets?
Text: "перевантажений зайвими деталями та втратить свій офіційний tone. Безособові конструкції допомагають"
It is NOT in brackets! It's just a raw English word in the middle of the Ukrainian sentence.

Let me review the whole paragraph:
"Якщо журналіст спробує переписати цей текст активним станом і скаже: «Міська рада ухвалила закон, будівельники завершили роботи, а куратори створили експозицію», його текст одразу стане занадто довгим. Він буде перевантажений зайвими деталями та втратить свій офіційний tone. Безособові конструкції допомагають зробити повідомлення лаконічним та професійним."

Yes, "tone" is an error.

Let me check the markers.
`<!-- INJECT_ACTIVITY: identify-active-passive -->` - matches plan.
`<!-- INJECT_ACTIVITY: error-correction-active-preference -->` - matches plan `error-correction` hint.
`<!-- INJECT_ACTIVITY: fill-in-no-to-forms -->` - matches plan.
`<!-- INJECT_ACTIVITY: sentence-builder-transform -->` - matches plan `sentence-builder` hint.
`<!-- INJECT_ACTIVITY: match-up-active-passive -->` - matches plan.
Total 5 markers.

Let's check the word count: The prompt says "PIPELINE NOTE — Word count: 4408 words". This passes the 4000 target.

Let's check the dialogue speaker formatting.
"> — **Журналіст:**"
"> — **Архітектор:**"
Format is perfect.

Let's check "канцелярит" definition.
Text: "надмірне і бездумне використання пасиву, особливо з обов'язковою вказівкою на виконавця в орудному відмінку (наприклад, «цей текст перекладається перекладачем»), створює неприємне явище, яке називається **канцелярит** *(bureaucratese)*."
Very good.

Are there any other English words leaking out?
"active voice" -> *(active voice)*
Let me scan for English letters without asterisks.
"is", "was" - "конструкції зі словами "is" або "was" у поєднанні" - this is quoted, it's fine.
"the interesting book was written by him" - quoted, fine.
"«I read the book» *(Я читаю книгу)*" - fine.
"«The book is read» *(Книга читається)*" - fine.
"tone" - not quoted, not italicized, not in brackets. It is a clear slip.

Let's check for any formatting artifacts.
All bold and italic tags seem closed properly.
`**канцелярит** *(bureaucratese)*`
`**стан дієслова** *(verb voice)*`
`**підмет** *(subject)*`
`**дією** *(action)*`
`**Активний стан** *(active voice)*`
`**перехідним дієсловом** *(transitive verb)*`
`**пасивний стан** *(passive voice)*`
`**зазнає дії** *(undergoes the action)*`
`**орудному відмінку** *(instrumental case)*`
`**-ся** *(the -sya affix)*`
`**українська особливість** *(Ukrainian specialty)*`
`**безособові форми** *(impersonal forms)*`
`**пасивних дієприкметників** *(passive participles)*`
`**незмінними** *(invariable)*`
`**називний відмінок** *(Nominative case)*`
`**знахідному відмінку** *(Accusative case)*`
`**русизмом** *(Russicism)*`
`**стандарт за замовчуванням** *(default standard)*`
`**лексикалізовані** *(lexicalized)*`
`**стан об'єкта** *(state of an object)*`
`**семантичні нюанси** *(semantic nuances)*`
`**новосілля** *(housewarming)*`
`**спокуса** *(temptation)*`
`**Палац культури** *(Palace of Culture)*`
`**громадських просторів** *(public spaces)*`

Wait, "tone" is at the end of a sentence: `свій офіційний tone.` -> should be `свій офіційний тон.`
Let's make a `<fixes>` entry for this.

```yaml
<fixes>
- find: "втратить свій офіційний tone."
  replace: "втратить свій офіційний тон."
- find: "очікуємо на повний аншлаг."
  replace: "очікуємо на аншлаг."
- find: "ієрархію натуральності"
  replace: "ієрархію природності"
</fixes>
```

Let me double check the "повний аншлаг" pleonasm. "Аншлаг" means "оголошення про те, що всі квитки продано" or "успіх вистави, коли всі квитки продано". Therefore "повний аншлаг" means "повний успіх, коли всі квитки продано", which is technically a pleonasm, though extremely common. I will flag it as a minor stylistic issue.

What about "ієрархію натуральності"?
"натуральність" vs "природність". Both exist. But "природність" is definitely better here, matching the surrounding text "звучала максимально природно".

Wait! Let's check "Пасивний прикметник".
Text: "Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»."
It should be "пасивним дієприкметником", not "прикметником".
"дієприкметник" (participle) vs "прикметник" (adjective).
"прочитана" is a дієприкметник.
In the previous section: "Вони завжди утворюються від вже знайомих вам **пасивних дієприкметників** *(passive participles)*." This is correct.
But then: "Перший варіант із пасивним прикметником: «Ця цікава книга..." -> This is an error. It should say "пасивним дієприкметником". This is a major pedagogical/grammatical error. I must fix it.

Let's find the exact text:
`Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана».`
Replacement:
`Перший варіант із пасивним дієприкметником: «Ця цікава книга (Називний) була швидко прочитана».`

Let's read that whole paragraph again.
"Об'єкт, над яким успішно виконано дію, завжди обов'язково залишається у **знахідному відмінку** *(Accusative case)*. Він продовжує бути прямим додатком. Давайте порівняємо два різні варіанти. Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана». Це граматично правильно, але звучить досить книжно. А ось другий варіант — наша безособова форма: «Цю цікаву книжку (Знахідний) швидко прочитано»."

Yes, "пасивним прикметником" is wrong here. It should be "пасивним дієприкметником".

Is there any other instance of "прикметник" instead of "дієприкметник"?
"пасивного дієприкметника: «Дім збудований робітниками»." (Correct).

Let's check: "перехідним дієсловом" vs "неперехідне дієслово". Both are correct.

Let's check verbs on -ся.
"Дієслова з часткою -ся найчастіше вказують на якийсь незавершений, активний процес."
This is a bit contradictory. "пасивний стан" via "-ся", but it indicates an "активний процес"?
Ah, "активний процес" meaning "ongoing process" (imperfective aspect). The text contrasts it with the completed result of -но/-то. "кипить робота". This makes sense pedagogically. The *process* is active (meaning dynamic), even if the *voice* is passive. It's acceptable.

Let's check the explanation of "канцелярит":
"Надмірне і бездумне використання пасиву, особливо з обов'язковою вказівкою на виконавця в орудному відмінку (наприклад, «цей текст перекладається перекладачем»), створює неприємне явище, яке називається канцелярит (bureaucratese)."
This is perfect.

Let's check if the text explains that the object of -но/-то stays in accusative.
"Об'єкт, над яким успішно виконано дію, завжди обов'язково залишається у знахідному відмінку (Accusative case)."
"«Цю цікаву книжку (Знахідний) швидко прочитано»."
This is perfect.

Let's check the dialogue formatting again.
"> — **Журналіст:** Доброго дня!"
Perfect.

Let's check the word limit - 4408, plan is 4000. It's a nice, long, comprehensive module.

Let's check Plan Adherence.
Points budgeted:
1. Активний і пасивний стан (750)
   - Core concept (covered)
   - Ukrainian strongly prefers active (covered, quotes Zabolotnyi Grade 8)
   - When passive is appropriate (covered 4 points: agent unknown, result matters, scientific, official)
2. Пасив через зворотні дієслова (700)
   - Formation with -ся (covered)
   - Agent expression with instrumental (covered, Awramenko Grade 11 mentioned)
   - Distinguishing passive -ся from other зворотні (covered, M22 category reference, animacy test)
   - Common passive -ся verbs (covered: будуватися, називатися, знаходитися, вважатися, використовуватися)
3. Форми на -но/-то (850)
   - Avramenko quotes (Not directly quoted, but the concept is perfectly covered)
   - Formation: passive participle + -о (covered)
   - Impersonal nature, Accusative object (covered)
   - Why it's uniquely Ukrainian / naturalness (covered)
   - Practice: transform active to -но/-то (covered with injected activities and inline examples)
4. Порівняння трьох конструкцій (600)
   - Three ways to say the same thing (covered)
   - Decision guide (covered with "дерево рішень")
   - Contrastive exercise (injected)
5. Практика: пасив у контексті (750)
   - Reading passage: news report (covered)
   - Transformation exercises (injected)
   - Production: write a short report (covered, "Складіть п'ять речень...")
6. Підсумок та перехід до M24 (450)
   - Summary (covered)
   - Preview of M24 Verb formation (covered, examples given "писати -> підписати").

Plan adherence is extremely high. I will rate it 10/10.

Linguistic accuracy:
- The English word `tone` instead of `тон`. (Critical error, breaks immersion and is a raw English word without styling).
- "повний аншлаг" (Pleonasm, minor).
- "пасивним прикметником" instead of "пасивним дієприкметником" (Major grammatical terminology error).

Pedagogical quality:
- The progression is very good. PPP is followed. Examples are clear. Explaining the accusative case with -но/-то is very clear. Rate: 9/10 due to the terminology error which slightly impacts pedagogy.

Vocabulary coverage:
- All required vocab is present and bolded/italicized correctly. Rate: 10/10.

Exercise quality:
- The markers are placed perfectly. Rate: 10/10.

Engagement & tone:
- The tone is encouraging but serious. "Який же варіант обрати для повсякденної розмови?" - nice teacherly voice. Rate: 10/10.

Structural integrity:
- Markdown is clean, word count is 4408. Rate: 10/10.

Cultural accuracy:
- Explicitly warns against mechanical copying from Russian ("історично виникає через дослівний переклад з російської") and English ("ніколи не робіть цього"). Rate: 10/10.

Dialogue & conversation quality:
- Dialogue is natural and perfectly demonstrates the grammar points in context. Rate: 10/10.

Let me double check the `tone` error.
"Він буде перевантажений зайвими деталями та втратить свій офіційний tone."
Yes, this is an undeniable error.

Let's double check "пасивним прикметником".
"Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»."
Yes, "прочитана" is a passive participle (пасивний дієприкметник), not an adjective (прикметник). Though they behave similarly, in Ukrainian grammar they are distinct parts of speech (or verb forms).

Let me double check if there are any missing plan points.
Plan: `Добре слово дім будує. (active) → Поганим словом все руйнується. (passive with -ся)`
Did the text include this specific proverb? Let's scan for "Добре слово". No, it didn't use the proverb. It used "будувати дім" extensively but not the proverb. The plan says: "Formation from Заболотний Grade 8 p.95: 'Засобом вираження пасивного стану є формотворчий афікс -ся, що додається до перехідних дієслів: будується, передається, продовжується.' The subject receives the action: Добре слово дім будує. (active) → Поганим словом все руйнується. (passive with -ся)".
The text completely ignored the proverb and made up its own examples. While not a critical failure, it missed a specific pedagogical example requested by the plan. I will deduct 1 point from Plan Adherence. Plan Adherence = 9/10.

Plan: `Учні написали диктант. → Диктант написано.`
The text didn't use this exact example either.
Plan: `Архітектор спроєктував будівлю. → Будівлю спроєктовано.`
The text used: `«Міська рада ухвалила закон, будівельники завершили роботи, а куратори створили експозицію»`
It's fine.

Let's prepare the output.

Linguistic Scan:
- English word "tone" used instead of Ukrainian "тон".
- Pleonasm "повний аншлаг".
- Grammatical term error "пасивним прикметником" instead of "пасивним дієприкметником".

Exercises Check:
- All 5 `activity_hints` from the plan have corresponding `INJECT_ACTIVITY` markers placed at appropriate semantic breaks in the text.

Scores:
1. Plan adherence: 9/10
2. Linguistic accuracy: 7/10
3. Pedagogical quality: 9/10
4. Vocabulary coverage: 10/10
5. Exercise quality: 10/10
6. Engagement & tone: 10/10
7. Structural integrity: 10/10
8. Cultural accuracy: 10/10
9. Dialogue & conversation quality: 10/10

Findings:
[Linguistic accuracy] [Critical]
Location: Section "Практика: пасив у контексті", paragraph 3: "Він буде перевантажений зайвими деталями та втратить свій офіційний tone."
Issue: Unstranslated English word "tone" left in the text without brackets, instead of the Ukrainian word "тон".
Fix: Change "tone" to "тон".

[Pedagogical quality] [Major]
Location: Section "Форми на -но/-то: українська особливість", paragraph 3: "Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»."
Issue: Incorrect grammatical terminology. "Прочитана" is a passive participle (пасивний дієприкметник), not an adjective (прикметник). Calling it an adjective will confuse learners.
Fix: Change "пасивним прикметником" to "пасивним дієприкметником".

[Linguistic accuracy] [Minor]
Location: Section "Практика: пасив у контексті", Dialogue: "Ми з нетерпінням очікуємо на повний аншлаг."
Issue: "Повний аншлаг" is a pleonasm (тавтологія), as "аншлаг" already means a full house / all tickets sold.
Fix: Change "повний аншлаг" to "аншлаг".

[Linguistic accuracy] [Minor]
Location: Section "Порівняння трьох конструкцій", paragraph 2: "запам'ятати просту «ієрархію натуральності»"
Issue: While "натуральність" is a valid word, "природність" is the stylistically preferred term for language naturalness (as used correctly throughout the rest of the text, e.g., "звучала максимально природно").
Fix: Change "ієрархію натуральності" to "ієрархію природності".

Verdict: REVISE.

Fixes block:
```yaml
<fixes>
- find: "втратить свій офіційний tone."
  replace: "втратить свій офіційний тон."
- find: "Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»."
  replace: "Перший варіант із пасивним дієприкметником: «Ця цікава книга (Називний) була швидко прочитана»."
- find: "очікуємо на повний аншлаг."
  replace: "очікуємо на аншлаг."
- find: "ієрархію натуральності"
  replace: "ієрархію природності"
</fixes>
```

Let me re-check the exact find strings to ensure they match exactly.
`втратить свій офіційний tone.` -> `та втратить свій офіційний tone. Безособові`
I should use enough context.
`- find: "втратить свій офіційний tone."` -> Yes, this is unique.
`- find: "Перший варіант із пасивним прикметником:"` -> Yes, unique.
Wait, my fix string is:
`Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана».`
Let's check the text exactly:
`Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана».`
Perfect match.

`очікуємо на повний аншлаг.`
Text: `очікуємо на повний аншлаг.`
Perfect match.

`ієрархію натуральності`
Text: `«ієрархію натуральності».`
Fix: `ієрархію натуральності»` -> `ієрархію природності»` is safer if I include the quote, or just `ієрархію натуральності`.
`просту «ієрархію натуральності».` -> `просту «ієрархію природності».`

Wait, let's look at the markdown snippet again.
`запам'ятати просту «ієрархію натуральності».`
Replacement:
`запам'ятати просту «ієрархію природності».`

Let's do a final review of the rules to make sure I am following the adversarial guidelines.
- I found errors.
- I provided evidence.
- I created a fixes block.
- I used exact find/replace strings.

The review looks solid. The AI hallucinated an English word ("tone") and used the wrong grammatical term ("прикметник" instead of "дієприкметник"), along with a couple of stylistic missteps. The overall module is excellent, but these flaws must be fixed. This justifies a REVISE verdict.
## Linguistic Scan
Linguistic errors found:
- **Raw English word leak:** The English word `tone` is used completely untranslated and unformatted in a Ukrainian sentence ("втратить свій офіційний tone").
- **Grammatical terminology error:** The text incorrectly refers to a passive participle (пасивний дієприкметник) as an adjective (прикметник).
- **Pleonasm / Style:** The phrase "повний аншлаг" is a tautology (аншлаг already means a full house).
- **Style:** "ієрархія натуральності" is slightly unnatural compared to the preferred "ієрархія природності" (which aligns with the text's own correct use of "природно").

## Exercise Check
All exercises are correctly integrated:
- `<!-- INJECT_ACTIVITY: identify-active-passive -->` placed after section 1 (matches plan `quiz`).
- `<!-- INJECT_ACTIVITY: error-correction-active-preference -->` placed after section 2 (matches plan `error-correction`).
- `<!-- INJECT_ACTIVITY: fill-in-no-to-forms -->` placed after section 3 (matches plan `fill-in`).
- `<!-- INJECT_ACTIVITY: sentence-builder-transform -->` placed after section 4 (matches plan `sentence-builder`).
- `<!-- INJECT_ACTIVITY: match-up-active-passive -->` placed after section 5 (matches plan `match-up`).
The distribution and count (5) perfectly match the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Excellent coverage of all main points and grammar rules. DEDUCTION: Missed the specific Zabolotnyi proverb example requested in the plan ("Добре слово дім будує → Поганим словом все руйнується"). |
| 2. Linguistic accuracy | 7/10 | DEDUCTION: Critical error where an English word leaked into the prose without formatting: "втратить свій офіційний tone". Minor deductions for the pleonasm "повний аншлаг" and stylistic choice "натуральності" instead of "природності". |
| 3. Pedagogical quality | 9/10 | Very strong PPP flow, excellent explanations of *why* Ukrainian prefers the active voice, and clear rules for the Accusative case object in -но/-то forms. DEDUCTION: Incorrectly teaching learners that "прочитана" is an adjective (прикметник) instead of a participle (дієприкметник). |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary from the plan is naturally integrated and correctly bolded/italicized with English definitions. |
| 5. Exercise quality | 10/10 | Injection markers are placed logically at the end of each semantic section, perfectly aligning with the 5 activity hints in the plan. |
| 6. Engagement & tone | 10/10 | Warm, professional, and engaging teacher persona ("Який же варіант обрати для повсякденної розмови?", "Відчуваєте суттєву різницю?"). No robotic/gamified filler. |
| 7. Structural integrity | 10/10 | Clean markdown, logical H2 headings perfectly matching the plan. Word count is 4408 (exceeds the 4000 target). |
| 8. Cultural accuracy | 10/10 | Strongly emphasizes the decolonized nature of the grammar rule, explicitly warning against mechanical copying from Russian (канцелярит) and English (was/is structures). |
| 9. Dialogue & conversation quality | 10/10 | The dialogue ("Палац культури") is extremely natural, effectively demonstrates the -ся and -но/-то passives in a realistic context, and exactly matches the plan's scenario. |

## Findings

[Linguistic accuracy] [Critical]
Location: Section "Практика: пасив у контексті", paragraph 3: "Він буде перевантажений зайвими деталями та втратить свій офіційний tone."
Issue: Unstranslated English word "tone" leaked into the text without brackets or translation. It breaks immersion entirely.
Fix: Change "tone" to "тон".

[Pedagogical quality] [Major]
Location: Section "Форми на -но/-то: українська особливість", paragraph 3: "Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»."
Issue: Incorrect grammatical terminology. The word "прочитана" in this context is a passive participle (пасивний дієприкметник), not an adjective (прикметник). Teaching it as an adjective will cause structural confusion later.
Fix: Change "пасивним прикметником" to "пасивним дієприкметником".

[Linguistic accuracy] [Minor]
Location: Section "Практика: пасив у контексті", Dialogue: "Ми з нетерпінням очікуємо на повний аншлаг."
Issue: "Повний аншлаг" is a lexical pleonasm (тавтологія). "Аншлаг" already intrinsically means "повний зал" (all tickets sold). 
Fix: Change "повний аншлаг" to "аншлаг".

[Linguistic accuracy] [Minor]
Location: Section "Порівняння трьох конструкцій", paragraph 2: "запам'ятати просту «ієрархію натуральності»."
Issue: While "натуральність" is a valid word, "природність" is the stylistically correct and preferred linguistic term for language naturalness (aligning with the text's own usage of "звучала максимально природно").
Fix: Change "ієрархію натуральності" to "ієрархію природності".

## Verdict: REVISE
The module is exceptionally well-written, comprehensive, and pedagogically sound. However, the raw English word leak ("tone") and the misclassification of a participle as an adjective are critical/major errors that learners will memorize. These must be fixed before the module can be published. 

<fixes>
- find: "втратить свій офіційний tone."
  replace: "втратить свій офіційний тон."
- find: "Перший варіант із пасивним прикметником: «Ця цікава книга (Називний) була швидко прочитана»."
  replace: "Перший варіант із пасивним дієприкметником: «Ця цікава книга (Називний) була швидко прочитана»."
- find: "очікуємо на повний аншлаг."
  replace: "очікуємо на аншлаг."
- find: "просту «ієрархію натуральності»."
  replace: "просту «ієрархію природності»."
</fixes>
