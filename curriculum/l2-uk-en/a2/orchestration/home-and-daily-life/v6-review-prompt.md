<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 38: Мій дім, мій день (A2, A2.5 [Case Synthesis and Plurals])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-038
level: A2
sequence: 38
slug: home-and-daily-life
version: '1.0'
title: Мій дім, мій день
subtitle: Описуємо помешкання, меблі та щоденний розпорядок із повною системою відмінків
focus: communication
pedagogy: TBL
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
- Learner can describe their home and its rooms, using Locative for location (у кухні, на балконі), Genitive
  for absence/quantity (немає гаража, багато кімнат), and Nominative for listing (тут є диван, шафа, стіл).
- Learner can describe furniture and household items using Instrumental for characteristics (стіл з дерева,
  кімната з великими вікнами) and Accusative for actions (поставити стілець, повісити картину).
- Learner can narrate a daily routine in sequence, using appropriate tenses and cases (вранці я встаю
  о сьомій годині, снідаю з родиною, їду на роботу).
- Learner can participate in a dialogue about visiting someone's home, asking about rooms and routines
  using the full case system naturally.
dialogue_situations:
- setting: 'Scenario 1: Video tour of your помешкання (n, apartment) — кухня (f, kitchen), вітальня (f,
    living room), спальня (f, bedroom). Scenario 2: Describing your розпорядок дня (m, daily routine).
    Scenario 3: Visiting Ukrainian friends — bringing гостинці (pl, gifts).'
  speakers:
  - Мешканець
  - Онлайн-друг / Господарі
  motivation: 'Home + daily life: кухня(f), вітальня(f), спальня(f), гостинці(pl)'
content_outline:
- section: 'Сценарій 1: Моє помешкання (Scenario 1: My Home)'
  words: 600
  points:
  - 'Dialogue: showing a friend around a new apartment. Host describes rooms and furniture. Cases emerge
    naturally: Ось вітальня (Nom.). У вітальні (Loc.) стоїть великий диван. На стіні (Loc.) висить картина.
    Біля вікна (Gen.) є крісло.'
  - 'Room vocabulary: кухня, спальня, вітальня, ванна кімната, коридор, балкон, кабінет.'
  - 'Furniture vocabulary: диван, крісло, стіл, стілець, шафа, ліжко, полиця, дзеркало, килим.'
  - 'Guest asks questions: А скільки у вас кімнат (Gen.Pl.)? Що на балконі (Loc.)? Де ви поставили книжки
    (Acc.Pl.)?'
- section: 'Сценарій 2: Мій звичайний день (Scenario 2: My Typical Day)'
  words: 600
  points:
  - 'Monologue: describing a typical weekday from morning to evening. Вранці я встаю о сьомій (Loc. for
    time). Іду у ванну (Acc. direction). Снідаю з родиною (Instr.). Їду на роботу (Acc.) автобусом (Instr.).'
  - 'Daily actions: вставати, вмиватися, снідати, обідати, вечеряти, працювати, відпочивати, лягати спати.'
  - 'Time expressions: вранці, вдень, увечері, вночі; о котрій годині; після обіду (Gen.), перед сном
    (Instr.), під час роботи (Gen.).'
  - 'Contrast weekday vs. weekend: У будні я працюю, а у вихідні відпочиваю. По суботах ходжу на ринок
    (Acc.).'
- section: 'Сценарій 3: В гостях (Scenario 3: Visiting Someone)'
  words: 500
  points:
  - 'Dialogue: visiting a Ukrainian friend for dinner. Arrival, tour of the home, sitting down to eat,
    conversation about daily routines.'
  - 'Hospitality expressions: Будь ласка, заходьте! Сідайте за стіл (Acc.). Пригощайтеся! Хочете чаю (Gen.)
    чи кави (Gen.)?'
  - 'Comparing routines: А о котрій ви встаєте? Хто у вас готує вечерю (Acc.)? Ви снідаєте вдома (Loc.
    implied) чи на роботі (Loc.)?'
  - 'Cases in action: за столом (Instr.), на кухні (Loc.), для гостей (Gen.), з цукром (Instr.), дякую
    господарям (Dat.).'
- section: 'Мовленнєве завдання: Опишіть свій дім (Speaking Task: Describe Your Home)'
  words: 300
  points:
  - 'Guided production task: learner writes 8-10 sentences describing their home and daily routine, using
    a checklist to ensure they include at least 5 different cases.'
  - 'Checklist: use Nom. (what is there), Gen. (what is not there / how many), Dat. (for whom), Acc. (where
    you go / what you do), Instr. (with whom / by what means), Loc. (where things are).'
  - Model answer provided for comparison.
vocabulary_hints:
  required:
  - помешкання (dwelling, apartment)
  - кімната (room)
  - кухня (kitchen)
  - спальня (bedroom)
  - вітальня (living room)
  - меблі (furniture)
  - розпорядок дня (daily routine)
  - вставати (to get up)
  - снідати (to have breakfast)
  - лягати спати (to go to bed)
  recommended:
  - балкон (balcony)
  - коридор (hallway)
  - килим (carpet, rug)
  - пригощатися (to help oneself (to food))
  - господар (host)
activity_hints:
- type: fill-in
  focus: Complete a description of a home with the correct case forms for room and furniture nouns
  items: 8
- type: quiz
  focus: Choose the correct case form in daily routine sentences (time expressions, prepositions, verbs)
  items: 8
- type: match-up
  focus: Match daily activities with the correct time of day and appropriate case construction
  items: 8
- type: error-correction
  focus: Find and correct grammar errors in sentences
  items: 6
references:
- title: Заболотний Grade 5, §§25-28
  notes: Describing places and daily activities — case usage in context
- title: 'ULP: Home and Daily Routine'
  url: https://www.ukrainianlessons.com/season3/
  notes: Vocabulary for home description and daily routines with audio

</plan_content>

## Generated Content

<generated_module_content>
## Сценарій 1: Моє помешкання (~660 words)

> — **Марко:** Привіт, Анно! Ось моє нове помешкання. *(Hi, Anna! Here is my new place.)*
> — **Анна:** Привіт! Яка гарна квартира! А скільки у вас кімнат? *(Hi! What a beautiful apartment! And how many rooms do you have?)*
> — **Марко:** У нас три кімнати: спальня, вітальня і невеликий кабінет. Ось вітальня. *(We have three rooms: a bedroom, a living room, and a small study. Here is the living room.)*
> — **Анна:** Дуже світла! Що це там стоїть? *(Very bright! What is standing over there?)*
> — **Марко:** У вітальні стоїть великий диван. Біля вікна є зручне крісло. На стіні висить картина. *(In the living room stands a large sofa. Near the window there is a comfortable armchair. A picture hangs on the wall.)*
> — **Анна:** А кухня велика? *(And is the kitchen large?)*
> — **Марко:** Так, кухня простора. На кухні є новий стіл і чотири стільці. *(Yes, the kitchen is spacious. In the kitchen there is a new table and four chairs.)*
> — **Анна:** А де балкон? *(And where is the balcony?)*
> — **Марко:** Балкон у спальні. На балконі стоять квіти. *(The balcony is in the bedroom. On the balcony stand flowers.)*
> — **Анна:** Вітаю з новосіллям! *(Congratulations on the housewarming!)*

When describing a home, we need specific vocabulary. The word **помешкання** (dwelling, apartment) is a versatile term for where you live. Inside, you will find different spaces like a **ванна кімната** (bathroom) or a long hallway.

У типовій українській квартирі є кілька кімнат. Зазвичай це простора **вітальня** (living room), світла **спальня** (bedroom) та сучасна **кухня** (kitchen). Деякі люди також мають великий балкон або зручний кабінет для роботи.

> *In a typical Ukrainian apartment, there are several rooms. Usually, this is a spacious living room, a bright bedroom, and a modern kitchen. Some people also have a large balcony or a comfortable study for work.*

:::tip
For "living room", use the standard noun **вітальня**. Do not use **гостинна** here as the room name.
:::

Once you know the rooms, you can talk about what is inside them. Remember that the word **меблі** (furniture) is always plural in Ukrainian.

Мої нові меблі дуже зручні та красиві. У кімнаті стоїть великий **диван** (sofa), м'яке **крісло** (armchair) та дерев'яний стіл. Біля стола є зручний стілець, а біля стіни стоїть висока шафа. У спальні ми поставили широке ліжко. На стіні висить полиця, яскравий **килим** (rug) і дзеркало.

> *My new furniture is very comfortable and beautiful. In the room stands a large sofa, a soft armchair, and a wooden table. Near the table there is a comfortable chair, and near the wall stands a tall wardrobe. In the bedroom we put a wide bed. On the wall hangs a shelf, a bright rug, and a mirror.*

To say *where* something is located, use the Locative case. It answers the question «Де?» (Where?) and always follows prepositions like **у/в** (in) or **на** (on/at).

Для опису місця ми завжди використовуємо місцевий відмінок. Наприклад, ми кажемо, що стіл стоїть у квартирі або на кухні. Квіти стоять на балконі або на вікні. Наш кіт любить спати у коридорі або у вітальні.

Notice how the noun endings change when we show location. Most feminine nouns ending in **-а** take **-і**. This is a very consistent rule that you will use every day.
**квартира → у квартирі** — *apartment → in the apartment*

Masculine nouns ending in a consonant usually take **-і** or **-у**. If you are ever unsure, the **-і** ending is extremely common for rooms.
**коридор → у коридорі** — *hallway → in the hallway*
**балкон → на балконі** — *balcony → on the balcony*

Neuter nouns often change to **-і** or **-у** as well.
**вікно → на вікні** — *window → on the window*
**ліжко → на ліжку** — *bed → on the bed*

:::note
Pay attention to consonant shifts in the Locative case. The word **кухня** ends in a soft consonant, so it becomes **на кухні**. In English, this translates naturally as "in the kitchen".
:::

The Genitive case is equally important for describing your home. We rely on it to talk about things we lack, using the negative word **немає** (there is no). We also use it to express quantity when asking questions or stating exactly how many rooms are in a house. Mastering this case is essential for smooth communication.

У моїй новій квартирі немає великого кабінету. У нас також немає старого килима на стіні. Коли друзі запитують, вони кажуть: «Скільки у вас кімнат?». Ми відповідаємо, що маємо дві просторі кімнати.

> *In my new apartment, there is no large study. We also do not have an old rug on the wall. When friends ask, they say: "How many rooms do you have?". We answer that we have two spacious rooms.*

When counting items, pay close attention to the plural forms. For the numbers two, three, and four, we use the Nominative plural. This feels quite natural because it is similar to just making the noun plural.
**два столи** — *two tables*
**три ліжка** — *three beds*
**чотири стільці** — *four chairs*

For five and above, or with quantity words like "багато" (many), we switch to the Genitive plural.
**п'ять кімнат** — *five rooms*
**багато меблів** — *a lot of furniture*

A frequent mistake for beginners is forgetting to change the noun case after a preposition of location. Since English nouns do not change form, direct translation often leads to structural errors. You must always change the ending in Ukrainian, rather than just dropping the dictionary form into the sentence. Think of the preposition and the new ending as two parts of the same tool.

Ніколи не кажи, що ти живеш в квартира або спиш на ліжко. Українська мова вимагає зміни закінчення після прийменника. Правильно казати: я живу у квартирі, а мій кіт спить на ліжку.

<!-- INJECT_ACTIVITY: fill-in-home-description -->

## Сценарій 2: Мій звичайний день (~660 words)

Let's look at how to describe a typical day from morning to evening. Notice how actions follow a logical sequence.

Мій **розпорядок дня** дуже простий, але насичений. З понеділка по п'ятницю я маю багато справ. Вранці я **встаю** о сьомій годині. Спочатку я йду у ванну кімнату. Там я вмиваюся і чищу зуби. Потім я йду на кухню. Я **снідаю** з родиною за великим столом. Ми п'ємо гарячу каву або чай. Після сніданку я швидко одягаюся. Потім я їду на роботу автобусом. Моя дорога займає близько тридцяти хвилин. Я починаю працювати о дев'ятій годині.

> *My daily routine is very simple but busy. From Monday to Friday, I have many things to do. In the morning, I get up at seven o'clock. First, I go to the bathroom. There, I wash my face and brush my teeth. Then I go to the kitchen. I have breakfast with my family at a large table. We drink hot coffee or tea. After breakfast, I quickly get dressed. Then I go to work by bus. My commute takes about thirty minutes. I start working at nine o'clock.*

To describe a typical day, we use specific verbs for repeated actions. Because we are talking about a routine, we rely on imperfective verbs. These focus on the process or repetition of the action, rather than its completion.

Основні дієслова для опису дня: **вставати**, вмиватися, **снідати**, обідати і вечеряти. Коли ми на роботі, ми працюємо. Після роботи ми повертаємося додому і відпочиваємо. Увечері ми можемо читати книгу або дивитися телевізор. Нарешті, ми йдемо в **спальню** і готуємося **лягати спати**. Усі ці дії ми повторюємо щодня.

> *The main verbs for describing a day: to get up, to wash one's face, to have breakfast, to have lunch, and to have dinner. When we are at work, we work. After work, we return home and rest. In the evening, we can read a book or watch TV. Finally, we go to the bedroom and prepare to go to bed. We repeat all these actions every day.*

You also need to state when things happen. Asking for the time and stating the time require different grammar forms. The question "What time is it?" is «Котра година?». It uses the Nominative case and an ordinal number. However, when you say that you do something *at* a certain time, you must change the case.

Коли ми питаємо про розклад, ми кажемо: «О котрій годині?». Для відповіді ми використовуємо прийменник «о» та Місцевий відмінок. Наприклад, ми кажемо: «о сьомій годині» або «о дев'ятій годині». Ми також використовуємо загальні слова для частин дня. Ми працюємо вдень, а спимо вночі. Вранці ми п'ємо каву, а увечері вечеряємо.

> *When we ask about a schedule, we say: "At what time?". To answer, we use the preposition "о" and the Locative case. For example, we say: "at seven o'clock" or "at nine o'clock". We also use general words for parts of the day. We work during the day, and we sleep at night. In the morning we drink coffee, and in the evening we have dinner.*

:::info
**Telling time** — Remember that «о» becomes «об» before vowels for better flow. So, "at eleven" is «об одинадцятій годині».
:::

Sometimes, you link activities to other events rather than specific hours. Each preposition demands a specific case. The phrase «після обіду» (after lunch) requires the Genitive case. The word «перед» (before) requires the Instrumental case, so we say «перед сном» (before sleep).

Під час роботи я часто п'ю воду або чай. Прийменник «під час» завжди вимагає Родового відмінка. Після обіду я маю трохи часу для відпочинку. Увечері, перед сном, я люблю читати цікаву книгу. Ці фрази роблять нашу мову більш природною.

Describing a routine means explaining where you go and how you get there. Use the Locative case to say where you are («на роботі» - at work). But when you talk about *going* somewhere, use the Accusative case for direction. Use the Instrumental case to explain your means of transport or your company.

Коли я вдома, я йду у ванну кімнату. Тут ми використовуємо Знахідний відмінок для напрямку. Потім я їду на роботу автобусом. Слово «автобус» стоїть в Орудному відмінку, бо це засіб транспорту. Я завжди **снідаю** з родиною або з друзями. Прийменник «з» вимагає Орудного відмінка.

Finally, routines change depending on the day. We often use the time expressions «у будні» and «у вихідні» to contrast weekdays and weekends. To say that you do something every Saturday, use a special repetitive structure.

Мій розклад у будні і у вихідні дуже різний. У будні я багато працюю і мало відпочиваю. Але у вихідні я маю вільний час для себе. По суботах я часто ходжу на місцевий ринок. Там я купую свіжі фрукти та овочі. По неділях ми з друзями гуляємо в парку.

> *My schedule on weekdays and on weekends is very different. On weekdays I work a lot and rest a little. But on weekends I have free time for myself. On Saturdays, I often go to the local market. There I buy fresh fruits and vegetables. On Sundays, my friends and I walk in the park.*

:::tip
**Repetitive actions** — To express doing something every week on a certain day, use «по» + Locative plural: «по суботах» (on Saturdays), «по неділях» (on Sundays).
:::

<!-- INJECT_ACTIVITY: quiz-daily-routine-cases -->
<!-- INJECT_ACTIVITY: match-up-routine-times -->

## Сценарій 3: В гостях (~550 words)

> — **Олена:** Привіт, Марку! Будь ласка, заходьте! *(Hi Mark! Please, come in!)*
> — **Марк:** Добрий вечір! Дякую за запрошення. Це вам маленькі гостинці. *(Good evening! Thank you for the invitation. These are small gifts for you.)*
> — **Тарас:** Дуже дякуємо! Яке гарне вино. Проходьте у вітальню. *(Thank you very much! What a nice wine. Come through to the living room.)*
> — **Олена:** Сідайте за стіл. Пригощайтеся, будь ласка! Я приготувала борщ. *(Sit down at the table. Help yourself, please! I cooked borsch.)*
> — **Марк:** Пахне дуже смачно. У вас чудове помешкання. *(It smells very delicious. You have a wonderful home.)*
> — **Тарас:** Дякую. Хочете чаю чи кави після вечері? *(Thank you. Do you want tea or coffee after dinner?)*
> — **Марк:** Кави з цукром, будь ласка. *(Coffee with sugar, please.)*

In Ukrainian culture, the **господар** (host) or **господиня** (hostess) takes great pride in welcoming visitors. It is customary and polite to bring **гостинці** (small gifts) when you visit someone's home. When the food is ready, the hosts will use the reflexive verb **пригощатися** (to help oneself) to warmly invite you to eat.

Українці дуже люблять запрошувати гостей додому. Коли ви йдете в гості, важливо принести гостинці. Це може бути торт, цукерки або пляшка вина. Господар і господиня завжди готують багато смачної їжі. Вони ставлять страви на стіл і кажуть: «Пригощайтеся!». Це означає, що ви можете брати все, що хочете. Українська гостинність дуже щедра і тепла.

> *Ukrainians really love inviting guests to their home. When you go visiting, it is important to bring gifts. This can be a cake, candies, or a bottle of wine. The host and hostess always prepare a lot of delicious food. They put the dishes on the table and say: "Help yourself!". This means that you can take whatever you want. Ukrainian hospitality is very generous and warm.*

Notice how the cases change depending on whether there is movement or static location with **меблі** (furniture). When the host invites you to sit down, there is a direction of action. We use the Accusative case for the destination.

Олена каже: «Сідайте за стіл». Тут ми використовуємо Знахідний відмінок, бо це напрямок. Коли ми вже сидимо і їмо, ми використовуємо Орудний відмінок. Наприклад, ми говоримо: «Ми сидимо за столом і вечеряємо». Так само ми використовуємо Знахідний відмінок, коли ставимо нові меблі в кімнату. Але коли меблі вже там стоять, ми використовуємо Місцевий або Орудний відмінки.

> *Olena says: "Sit down at the table". Here we use the Accusative case because it is a direction. When we are already sitting and eating, we use the Instrumental case. For example, we say: "We are sitting at the table and having dinner". Similarly, we use the Accusative case when we put new furniture into a room. But when the furniture is already standing there, we use the Locative or Instrumental cases.*

:::info
**Direction vs. Location** — Prepositions like **за** (behind/at) and **під** (under) take the Accusative case when answering the question "where to?" (direction). They take the Instrumental case when answering the question "where?" (location).
:::

During the meal, you will also hear the Genitive case used in a special way. When offering a portion or an undefined quantity of food or drink, Ukrainians use the partitive Genitive. This means you are offering "some of" the item.

Тарас запитує: «Хочете чаю чи кави?». Слова «чай» і «кава» стоять у Родовому відмінку. Це означає, що він пропонує трохи напою, а не весь чай у домі. Якщо ви хочете додати щось до напою, використовуйте Орудний відмінок. Марк просить каву з цукром і з молоком. Це дуже корисні фрази для спілкування за столом.

> *Taras asks: "Do you want tea or coffee?". The words "tea" and "coffee" are in the Genitive case. This means that he is offering some of the drink, not all the tea in the house. If you want to add something to the drink, use the Instrumental case. Mark asks for coffee with sugar and with milk. These are very useful phrases for communicating at the table.*

After dinner, the conversation often shifts to daily life and the **розпорядок дня** (daily routine). This is a great opportunity to synthesize everything you have learned about cases, times, and actions in a natural setting.

За столом друзі часто говорять про свій розпорядок дня. Марк запитує: «А о котрій годині ви встаєте?». Олена відповідає, що вона завжди встає рано. Вона йде у ванну, а потім готує сніданок. Тарас запитує Марка: «А хто у вас готує вечерю?». Марк розповідає, що він зазвичай вечеряє на роботі. Наприкінці він дякує господарям за вечерю. У цій простій розмові ми бачимо багато відмінків разом.

> *At the table, friends often talk about their daily routine. Mark asks: "And at what time do you get up?". Olena answers that she always gets up early. She goes to the bathroom, and then prepares breakfast. Taras asks Mark: "And who cooks dinner at your place?". Mark says that he usually has dinner at work. In this simple conversation, we see many cases together.*

<!-- INJECT_ACTIVITY: error-correction-cases-routine -->

## Мовленнєве завдання: Опишіть свій дім (~330 words)

It is time to put everything together and describe your own **помешкання** (dwelling, apartment). Imagine you are sending a short voice message to a Ukrainian friend to tell them about your life. You need to write an eight to ten sentence description of your home and your typical **розпорядок дня** (daily routine). Think about what your mornings look like. Mention what time you usually have **вставати** (to get up) and what you do immediately after that.

Розкажіть детально про свою квартиру чи будинок. Напишіть, яка у вас є улюблена **кімната** (room) і які там стоять **меблі** (furniture). Поясніть, де ви зазвичай любите **снідати** (to have breakfast) перед роботою.

> *Tell in detail about your apartment or house. Write what your favorite room is and what furniture stands there. Explain where you usually like to have breakfast before work.*

When describing your evening routine, do not forget to mention when you prefer to **лягати спати** (to go to bed). Before you write your text, review this grammar checklist to ensure you use the different cases correctly. This is a great way to practice everything you have learned.

Use the Nominative case to list what exists in your home. Use the Genitive case to state what is missing or to specify quantities. Use the Dative case to show for whom you do something. Use the Accusative case to show where you go during the day. Use the Instrumental case to explain how you travel or who you spend your time with. Finally, use the Locative case to pinpoint exactly where things are, like in the **кухня** (kitchen), the **спальня** (bedroom), or the **вітальня** (living room).

:::tip
**Did you know?** — When Ukrainians describe their homes, they often count the number of living spaces, excluding the kitchen, bathroom, and hallways. A "two-room apartment" (двокімнатна квартира) typically means it has a living room and one bedroom, plus a separate kitchen! Keep this in mind when talking to native speakers.
:::

> [!model-answer]
> Привіт! Я хочу розповісти про своє помешкання. Я живу у великій світлій квартирі. У квартирі є три кімнати: велика спальня, вітальня і маленька кухня. У вітальні стоять нові зручні меблі, але там зовсім немає телевізора. Мій розпорядок дня дуже простий. У будні я завжди встаю рано, о сьомій годині. Я йду у ванну кімнату, а потім снідаю з родиною за столом. Після сніданку я їду на роботу міським автобусом. Удень я багато працюю за комп'ютером. Увечері я повертаюся додому, вечеряю і читаю цікаву книгу на дивані. Я зазвичай лягаю спати об одинадцятій годині.
</generated_module_content>

**PIPELINE NOTE — Word count: 2968 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 450 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Анно — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM

All 450 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
