<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/home-and-daily-life.yaml` file for module **38: Мій дім, мій день** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-home-description -->`
- `<!-- INJECT_ACTIVITY: quiz-daily-routine-cases -->`
- `<!-- INJECT_ACTIVITY: match-up-routine-times -->`
- `<!-- INJECT_ACTIVITY: error-correction-cases-routine -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete a description of a home with the correct case forms for room and
    furniture nouns
  items: 8
  type: fill-in
- focus: Choose the correct case form in daily routine sentences (time expressions,
    prepositions, verbs)
  items: 8
  type: quiz
- focus: Match daily activities with the correct time of day and appropriate case
    construction
  items: 8
  type: match-up
- focus: Find and correct grammar errors in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- балкон (balcony)
- коридор (hallway)
- килим (carpet, rug)
- пригощатися (to help oneself (to food))
- господар (host)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
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
Always use the beautiful Ukrainian word **вітальня** for your living room. Avoid Russian-sounding words like "гостинна", which are incorrect in standard Ukrainian.
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
Pay attention to consonant shifts in the Locative case. The word **кухня** ends in a soft consonant, so it becomes **на кухні** (in the kitchen). Yes, in Ukrainian we say "on the kitchen" rather than "in the kitchen"!
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

Finally, routines change depending on the day. We contrast weekdays and weekends using the Locative case. "On weekdays" is «у будні», and "on weekends" is «у вихідні». To say that you do something every Saturday, use a special repetitive structure.

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

За столом друзі часто говорять про свій розпорядок дня. Марк запитує: «А о котрій годині ви встаєте?». Олена відповідає, що вона завжди встає рано. Вона йде у ванну, а потім готує сніданок. Тарас запитує Марка: «А хто у вас готує вечерю?». Марк розповідає, що він зазвичай вечеряє на роботі. У цій простій розмові ми бачимо багато відмінків разом.

> *At the table, friends often talk about their daily routine. Mark asks: "And at what time do you get up?". Olena answers that she always gets up early. She goes to the bathroom, and then prepares breakfast. Taras asks Mark: "And who cooks dinner at your place?". Mark says that he usually has dinner at work. In this simple conversation, we see many cases together.*

<!-- INJECT_ACTIVITY: error-correction-cases-routine -->

## Мовленнєве завдання: Опишіть свій дім (~330 words)

It is time to put everything together and describe your own **помешкання** (dwelling, apartment). Imagine you are sending a short voice message to a Ukrainian friend to tell them about your life. You need to write an eight to ten sentence description of your home and your typical **розпорядок дня** (daily routine). Think about what your mornings look like. Mention what time you usually have **вставати** (to get up) and what you do immediately after that.

Розкажіть детально про свою квартиру чи будинок. Напишіть, яка у вас є улюблена **кімната** (room) і які там стоять **меблі** (furniture). Поясніть, де ви зазвичай любите **снідати** (to have breakfast) перед роботою.

> *Tell in detail about your apartment or house. Write what your favorite room is and what furniture stands there. Explain where you usually like to have breakfast before work.*

When describing your evening routine, do not forget to mention when you prefer to **лягати спати** (to go to bed). Before you write your text, review this grammar checklist to ensure you use the different cases correctly. This is a great way to practice everything you have learned.

Use the Nominative case to list what exists in your home. Use the Genitive case to state what is missing or to specify quantities. Use the Accusative case to show where you go during the day. Use the Instrumental case to explain how you travel or who you spend your time with. Finally, use the Locative case to pinpoint exactly where things are, like in the **кухня** (kitchen), the **спальня** (bedroom), or the **вітальня** (living room).

:::tip
**Did you know?** — When Ukrainians describe their homes, they often count the number of living spaces, excluding the kitchen, bathroom, and hallways. A "two-room apartment" (двокімнатна квартира) typically means it has a living room and one bedroom, plus a separate kitchen! Keep this in mind when talking to native speakers.
:::

> [!model-answer]
> Привіт! Я хочу розповісти про своє помешкання. Я живу у великій світлій квартирі. У квартирі є три кімнати: велика спальня, вітальня і маленька кухня. У вітальні стоять нові зручні меблі, але там зовсім немає телевізора. Мій розпорядок дня дуже простий. У будні я завжди встаю рано, о сьомій годині. Я йду у ванну кімнату, а потім снідаю з родиною за столом. Після сніданку я їду на роботу міським автобусом. Удень я багато працюю за комп'ютером. Увечері я повертаюся додому, вечеряю і читаю цікаву книгу на дивані. Я зазвичай лягаю спати об одинадцятій годині.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: home-and-daily-life
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**Level: A2 (Module 38/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
