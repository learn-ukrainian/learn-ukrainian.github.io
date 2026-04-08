<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/services-and-communication.yaml` file for module **22: На пошті** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-complete-post-office-dialogue-lines-with-correct-dative-forms -->`
- `<!-- INJECT_ACTIVITY: match-up-service-requests -->`
- `<!-- INJECT_ACTIVITY: group-sort-dative-functions -->`
- `<!-- INJECT_ACTIVITY: quiz-address-agreement -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete post office dialogue lines with correct dative forms (Надішліть
    цю посилку ___)
  items: 8
  type: fill-in
- focus: Match service requests to appropriate responses (Допоможіть мені → Звичайно,
    що вам потрібно?)
  items: 8
  type: match-up
- focus: Choose the correct dative address form (дорогому/дорогій/дорогим + name)
  items: 8
  type: quiz
- focus: Sort phrases into categories — requesting (прохання), thanking (подяка),
    giving (давання)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- бандероль (small parcel, book post)
- квитанція (receipt)
- одержувач (recipient)
- відправник (sender)
- індекс (postal code)
required:
- пошта (post office, mail)
- лист (letter)
- конверт (envelope)
- марка (stamp)
- посилка (parcel, package)
- адреса (address)
- надіслати (to send)
- отримати (to receive)
- відправити (to send, to dispatch)
- листоноша (mail carrier)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## На пошті: Базова лексика

В Україні головна поштова служба — це **Укрпошта** (Ukrposhta, the national postal service). Кожна локальна філія називається **відділення** (branch, post office). На вулицях ви часто можете побачити жовті металеві коробки. Це **поштові скриньки** (postboxes), куди люди кидають свої листи. У відділенні завжди є клієнти, які хочуть надіслати або отримати щось важливе. Там працюють люди за спеціальними вікнами. The atmosphere is usually busy, especially during the morning hours. Understanding the basic vocabulary will help you navigate this environment confidently. When you enter, you need to find the correct window.

Якщо ви хочете написати комусь текст на папері, вам потрібен **лист** (letter). Щоб відправити лист, ви маєте купити спеціальний паперовий пакет. Це **конверт** (envelope). На конверт обов'язково треба наклеїти маленьку картинку. Це **марка** (postage stamp). Без марки ваш лист не поїде до адресата. Якщо ви хочете надіслати гарне фото з коротким текстом, купіть інший предмет. Це **листівка** (postcard). Листівки часто відправляють без конверта, але марка все одно потрібна. Sometimes, local kiosks or souvenir shops also sell stamps and postcards for your convenience.

Люди часто надсилають не тільки листи, але й великі речі. Якщо ви хочете надіслати одяг або іграшки, це **посилка** (parcel). Ви можете принести свої речі, і на пошті вам дадуть коробку. Якщо річ трохи менша і вже загорнута в папір, ми часто кажемо **пакунок** (package). Для книг, журналів або документів є спеціальне слово. Це **бандероль** (small parcel, book-post). Бандероль легша за посилку і коштує дешевше. It is useful to know these distinctions when you explain what you are sending. The price often depends on whether it is a document or a heavy object.

На пошті працюють різні спеціалісти. Людина, яка сидить за вікном і допомагає вам, — це **оператор** (postal clerk) або **працівник пошти** (postal worker). Людина, яка приносить пошту до вашого дому, — це **листоноша** (mail carrier). Коли ви щось надсилаєте, у цьому процесі є дві головні ролі. Той, хто надсилає річ, — це **відправник** (sender). Той, хто має забрати цю річ, — це **одержувач** (recipient). Ці слова дуже важливі. You will see these terms on every envelope and parcel form. It is crucial not to mix them up to ensure your package arrives correctly.

Які дії ми найчастіше робимо на пошті? Якщо ви віддаєте лист оператору, ви хочете його **надіслати** (to send) або **відправити** (to send, to dispatch). Коли приходить посилка, ви йдете у відділення. Ви хочете її **отримати** (to receive) або **забрати** (to pick up). Щоб надіслати річ, вам часто потрібно написати інформацію на спеціальному папері. Це означає **заповнити бланк** (to fill out a form). Після цього оператор просить вас поставити підпис. Це означає **підписати квитанцію** (to sign a receipt). These action verbs are typically used in their perfective forms because they describe completed actions.


## Надіслати листа: Діалоги на пошті

Ми часто приходимо до відділення, щоб купити прості речі. Іноді нам треба надіслати важливі документи або короткі повідомлення. Давайте подивимося, як правильно почати розмову з оператором на пошті.

> — **Клієнт:** Добрий день! Дайте **мені**, будь ласка, два **конверти** *(envelopes)* і дві **марки** *(stamps)* по Україні.
> — **Оператор:** Добрий день! Звичайно, ось ваші конверти. Вам потрібні стандартні марки?
> — **Клієнт:** Так, стандартні. Я хочу надіслати ці листи сьогодні ввечері. Скільки це коштує?
> — **Оператор:** Це коштує сорок гривень.
> — **Клієнт:** Дякую вам. Ось гроші.
> — **Оператор:** Дякую. Ваша **решта** *(change)* і квитанція. До побачення!

У цьому простому діалозі клієнт просить оператора: «Дайте мені». Це дуже популярна і ввічлива фраза у сфері послуг. Вона допомагає швидко отримати те, що вам потрібно.

In Ukrainian, when we give, sell, send, or explain something to someone, we must use the Dative case (`давальний відмінок`). This grammatical case specifically answers the question **«Кому?»** *(To whom?)*. It functions to show the indirect object of your sentence. We use it frequently with service verbs like **дати** *(to give)*, **продати** *(to sell)*, **показати** *(to show)*, and **допомогти** *(to help)*. For example, when you ask a postal worker to give you an envelope, you say «дайте мені». The pronoun «я» *(I)* changes entirely to «мені» *(to me)* in the Dative case. Other common examples include «дати **листоноші**» *(to give to the mail carrier)* or «продати **клієнту**» *(to sell to the customer)*. The action is always directed toward a specific recipient.

Тепер давайте уявимо іншу ситуацію. Ви хочете надіслати велику і важку річ родичам.

> — **Клієнт:** Добрий день! Я хочу надіслати цю **посилку** *(parcel)* моєму **братові** *(to my brother)*.
> — **Оператор:** Добрий день! Що знаходиться всередині? Це важливо знати.
> — **Клієнт:** Там старі книги, зошити та теплий зимовий одяг.
> — **Оператор:** Добре. Кому саме ви відправляєте посилку? У яке місто?
> — **Клієнт:** Я відправляю її братові у місто Львів.
> — **Оператор:** Будь ласка, заповніть цей **бланк** *(form)*. Напишіть адресу та номер телефону.
> — **Клієнт:** Допоможіть мені, будь ласка. Де треба писати номер телефону одержувача?
> — **Оператор:** Пишіть номер телефону ось тут, унизу спеціального бланка.

У цій ситуації клієнт чітко пояснює, кому він надсилає свої речі.

How do we correctly form the Dative case for nouns? For masculine nouns denoting people, the most common and natural endings are **-ові** and **-еві** (or **-єві**). For example, the word «брат» *(brother)* becomes **братові** *(to the brother)*. The word «друг» *(friend)* becomes **другові**. For feminine nouns, the typical and regular ending is **-і**. The word «сестра» *(sister)* becomes **сестрі** *(to the sister)*. The word «мама» *(mother)* becomes **мамі**. Note that consonant mutation frequently occurs in feminine nouns before this ending. For instance, «подруга» *(female friend)* becomes **подрузі**. These specific endings clearly show who is receiving the physical item or the result of the action. They are essential for clear communication at the post office.

На пошті ми часто говоримо про наші конкретні плани та наміри. Для цього ми найчастіше використовуємо просту конструкцію «Я хочу» плюс дієслово. Наприклад: «Я хочу **надіслати** важливий лист» або «Я хочу **забрати** важку посилку». Якщо ми зовсім не знаємо, де щось зробити, ми запитуємо «Де можна» плюс дієслово. Ви можете підійти до вікна і запитати оператора: «Де можна надіслати гарну **листівку** *(postcard)*?». Або ви можете запитати на вулиці: «Де можна швидко купити марку?». Ці фрази дуже допомагають отримати інформацію. Дієслова у цих фразах завжди стоять у формі інфінітива. Вони показують результат тієї дії, яку ви плануєте зробити.

Коли ми надсилаємо лист або невелику бандероль, ми завжди маємо писати адресу. На кожному конверті обов'язково є два важливі поля для заповнення. Перше поле — це **«Кому»** *(To whom / Recipient)*. Тут ми завжди використовуємо давальний відмінок. Друге поле — це **«Від кого»** *(From whom / Sender)*. Тут ми завжди використовуємо родовий відмінок (`родовий відмінок`). Від того, наскільки правильно написана адреса, залежить швидка доставка. Спочатку ви пишете: «Від кого: від Івана Петренка». Потім ви пишете внизу: «Кому: Оксані Коваленко». Далі ви уважно пишете місто, вулицю, номер будинку, номер квартири та **індекс** *(postal code)*.

<!-- INJECT_ACTIVITY: fill-in-complete-post-office-dialogue-lines-with-correct-dative-forms -->


## Просити, дякувати, допомагати: Давальний у сфері послуг

У поштовому відділенні ми часто просимо про допомогу. Коли ви не знаєте, як заповнити документ, вам потрібне дієслово **допомагати** *(to help)*. When you ask for assistance, the person who receives the help is the indirect object. This means the verb «допомагати» always takes the Dative case. Ви можете сказати оператору: «**Допоможіть мені** *(help me)* заповнити цей бланк». The pronoun «я» changes to the Dative form «мені». Інший корисний приклад — це прохання показати щось. Ви можете запитати: «**Покажіть мені** *(show me)*, де писати адресу». Або ви можете сказати: «Покажіть клієнту, де стоїть скринька». Ці фрази роблять ваше спілкування ввічливим та ефективним. Оператор завжди готовий допомогти вам.

Після того, як ви отримали допомогу, важливо подякувати. У сфері послуг ми використовуємо дієслово **дякувати** *(to thank)*. This is a critical point where many learners make a mistake. In Ukrainian, you do not thank a person; you give thanks to a person. The question is always «дякувати кому?». Тому ми кажемо «**Дякую вам** *(thank you)*», а не «дякую вас». Інші правильні приклади: «Дякую **листоноші** *(to the mail carrier)* за лист». Також ми кажемо: «Дякуємо оператору за швидку роботу». Якщо ви розмовляєте з другом, ви кажете «Дякую **тобі** *(to you)*». Завжди пам'ятайте про давальний відмінок після цього дієслова. Це звучить дуже природно українською мовою.

Працівники пошти також можуть давати корисні рекомендації. Для цього вони використовують дієслово **радити** *(to advise / to suggest)*. This verb also governs the Dative case because you are offering advice to someone. Наприклад, досвідчений оператор може сказати: «**Раджу вам** *(I advise you)* надіслати це **авіапоштою** *(by airmail)*». Так посилка приїде набагато швидше. Якщо посилка дуже важлива, він скаже: «Раджу клієнту обрати надійну доставку». У неформальній ситуації ви можете дати пораду другу. Ви кажете: «**Раджу тобі** *(I advise you)* уважно перевірити **індекс** *(postal code)* перед відправленням». Ці фрази дуже часто звучать у різних сервісних центрах. Вони показують увагу до деталей та турботу про результат.

Коли ми спілкуємося на пошті, ми часто використовуємо ввічливий наказовий спосіб. Polite commands direct an action toward someone, so they naturally pair with the Dative case. Ми вже добре знаємо корисні фрази «допоможіть мені» та «покажіть мені». Є й інші дуже популярні та важливі слова. Ви можете ввічливо запитати: «**Скажіть мені** *(tell me)*, скільки сьогодні коштує марка». Якщо ви прийшли на пошту з родиною, ви скажете щось інше. Ви кажете: «**Поясніть нам** *(explain to us)* ці нові правила відправлення». Працівник пошти може попросити свого колегу: «**Принесіть їй** *(bring her)* ще один великий конверт». Всі ці наказові форми роблять діалог чітким та зрозумілим. Ви прямо вказуєте, кому потрібна конкретна інформація або річ.

Давайте розглянемо життєву ситуацію перед походом на пошту. Ви хочете надіслати подарунок, але не вмієте гарно його **загорнути** *(to wrap)*. Ви йдете до сусідки і просите її про допомогу.
> — **Ви:** Олено, привіт! Це подарунок **моїй бабусі** *(to my grandmother)*.
> — **Олена:** Привіт! Дуже гарна річ. Чим я можу допомогти?
> — **Ви:** Допоможи мені загорнути його, будь ласка.
> — **Олена:** Звичайно, дай мені папір і ножиці.
> — **Ви:** Тримай. Раджу тобі використовувати цю стрічку.
> — **Олена:** Готово. Тепер ти можеш нести посилку на пошту.
> — **Ви:** Дякую тобі за допомогу!

Тут ми яскраво бачимо, як давальний відмінок працює у реальній розмові. 

Як ви вже помітили, короткі особові займенники часто стоять у давальному відмінку. It is essential to memorize their Dative forms for fluent communication in service situations. Use **мені** *(to me)*, **нам** *(to us)*, or the formal **вам** *(to you)* for yourself. When you direct the action at someone else, use the other forms. These are **тобі** *(to you)*, **йому** *(to him/it)*, **їй** *(to her)*, or **їм** *(to them)*. Завжди використовуйте ці займенники разом із дієсловами «давати», «показувати» та «допомагати». Також вони чудово працюють зі словами «радити» та «дякувати». Тоді ваша щоденна українська мова буде граматично правильною та дуже ввічливою. Тепер ви повністю готові до будь-якої розмови на пошті або в іншому місці.

<!-- INJECT_ACTIVITY: match-up-service-requests -->

<!-- INJECT_ACTIVITY: group-sort-dative-functions -->


## Написати адресу: Давальний у листуванні

Від того, наскільки правильно написана **адреса** *(address)*, залежить своєчасна доставка вашого листа. Кожна країна має свої специфічні правила для пошти. В Україні поштову адресу потрібно писати в чіткій послідовності. Спочатку ми завжди пишемо ім'я та прізвище **одержувача** *(recipient)* у правильному відмінку. Далі йде точна назва вулиці, номер будинку та номер квартири, якщо вона є. Наприклад, ми пишемо: вулиця Тараса Шевченка, будинок п'ять, квартира вісім. Після цього ми вказуємо повну назву міста або села. Якщо це маленьке село, ми також пишемо назву області. Останній важливий елемент — це поштовий **індекс** *(postal code)*. Цей короткий номер допомагає пошті швидко знайти правильне відділення. Якщо ви напишете всі дані правильно, ваш лист швидко знайде свого господаря.

Коли ми заповнюємо поле «Кому» на конверті, ми обов'язково використовуємо давальний відмінок. Це граматичне правило стосується всіх слів у цьому рядку. Nouns, adjectives, and possessive pronouns must all agree in the Dative case. Ми рідко просто сухо пишемо ім'я людини. Ми часто додаємо теплі слова або слова поваги. Наприклад, ми пишемо: «**моєму дорогому братові** *(to my dear brother)* Михайлові». Тут займенник «моєму», прикметник «дорогому» та іменник «братові» стоять у давальному відмінку чоловічого роду. Якщо ви пишете близькій жінці, ви скажете: «**любій бабусі** *(to dear grandmother)* Олені». Зверніть увагу на типові закінчення жіночого роду в давальному відмінку. Вони закінчуються на «-ій» або «-і». Правильне узгодження показує вашу високу повагу до людини, яка отримає лист.

The way you address an envelope depends heavily on your relationship with the recipient. Коли ми пишемо офіційний лист у компанію, ми використовуємо формальний стиль. Наприклад, ми солідно пишемо: «**Шановному професорові** *(to the respected professor)* Петренку». Тут ми чітко бачимо типове закінчення «-ові» для чоловічого роду в давальному відмінку. Це закінчення додає вашому тексту необхідної офіційності та поваги. Якщо ми пишемо близькій людині або старому другу, ми обираємо неформальний стиль. На святковому конверті ми тепло напишемо: «**Дорогій подрузі** *(to dear friend)* Марії». Тут ми використовуємо жіночий рід і набагато більш емоційні слова. Вибір правильного стилю адресації дуже важливий для гарного враження. Завжди добре думайте про те, кому саме ви надсилаєте ваш лист чи посилку.

Часто ми не просто надсилаємо різні речі, а й додаємо коротке приємне повідомлення. На звичайній поштовій листівці досить мало вільного місця, тому текст має бути лаконічним. Ви можете почати своє повідомлення так: «**Дорогій подрузі!** *(To dear friend!)* Пишу тобі з Києва». Далі ви можете коротко пояснити мету вашого повідомлення або посилки. Наприклад, ви можете написати: «**Посилаю тобі** *(I am sending you)* цей маленький подарунок на добру згадку». Або ви можете пояснити: «**Надсилаю тобі** *(I am sending you)* нову рідкісну марку для твоєї колекції». Наприкінці повідомлення ми часто тепло вітаємо людину зі святом. Найпопулярніша фраза — це: «**Вітаю тебе** *(I congratulate you)* з великим святом». Такі короткі фрази роблять ваше повідомлення дуже приємним.

Let's practice writing the "Кому" field for different people to reinforce the Dative agreement rules. Уявіть, що ви зараз надсилаєте лист своєму шкільному другу Сергію. Ви повинні уважно написати: «**Моєму найкращому другові** *(to my best friend)* Сергієві». Усі слова в цій фразі стоять у правильному давальному відмінку чоловічого роду. Тепер уявіть, що ваша посилка летить до вашої улюбленої тітки. Ви з любов'ю напишете: «**Моїй улюбленій тітці** *(to my favorite aunt)* Наталі». Тут чудово працюють граматичні правила для жіночого роду. А якщо ви надсилаєте офіційні документи своєму старому вчителю? Тоді ви повинні написати формально: «**Шановному вчителю** *(to the respected teacher)* Іванові Івановичу». Українська мова вимагає точного узгодження кожного слова в іменній групі. Регулярна практика допоможе вам писати ці форми автоматично.

<!-- INJECT_ACTIVITY: quiz-address-agreement -->


## Підсумок

Час перевірити ваші нові знання! Дайте відповіді на ці короткі запитання, щоб добре закріпити матеріал. This is a great way to review the most important rules.

Як перекласти фразу «I want to send a parcel to my friend» українською мовою?
Правильна відповідь: «Я хочу **надіслати** *(to send)* **посилку** *(parcel)* моєму **другові** *(friend)*». Тут ми обов'язково використовуємо давальний відмінок для іменника «друг».

Який відмінок ми використовуємо після дієслова «**дякувати**» *(to thank)*?
Ми завжди використовуємо **давальний відмінок** *(Dative case)*. Ми кажемо: «Дякую вам», а не «дякую вас». This is a very common mistake, so pay close attention to it.

Як правильно підписати **листівку** *(postcard)* для бабусі Олени?
Ми тепло напишемо: «**Любій** *(dear)* бабусі Олені». Обидва слова мають правильні закінчення давального відмінка жіночого роду.

Хто приносить листи додому?
Це робить **листоноша** *(mail carrier)*.

Де ми пишемо **індекс** *(postal code)* і адресу?
Ми уважно пишемо їх на **конверті** *(envelope)* або на офіційному **бланку** *(form)*.

Ви чудово попрацювали сьогодні. You now know how to navigate a Ukrainian post office with confidence and respect. Тепер ви можете вільно надіслати лист або посилку своїм близьким людям!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: services-and-communication
level: a2

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 22/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
