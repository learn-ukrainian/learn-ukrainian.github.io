<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-direction.yaml` file for module **11: Куди? До якого часу?** (a2).

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

(No injection markers found in prose. All activities will go to workbook.)

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct meaning of до in context (direction, time, purpose)
  items: 8
  type: quiz
- focus: Complete sentences with до + correct Genitive noun form
  items: 8
  type: fill-in
- focus: Match до-phrases with their functions (direction, time limit, purpose)
  items: 8
  type: match-up
- focus: Sort до-phrases by meaning category (direction vs. time vs. purpose)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- ставлення (attitude)
- інтерес (interest)
- готовий (ready)
- завтра (tomorrow)
required:
- напрямок (direction)
- мета (goal, purpose)
- музей (museum)
- лікар (doctor)
- бабуся (grandmother)
- вечір (evening)
- ранок (morning)
- екзамен (exam)
- побачення (meeting, date; goodbye in 'до побачення')
- список (list)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Куди ти йдеш? До + родовий для напрямку (Where Are You Going? До + Genitive for Direction)

Ми часто подорожуємо. *(We often travel.)* Іноді ми йдемо пішки, іноді їдемо на машині. *(Sometimes we walk, sometimes we go by car.)* Але куди ми прямуємо? *(But where are we heading?)*

In Ukrainian, the preposition **до** *(to, towards)* is your primary tool for expressing movement toward a specific destination. When you want to say that you are going to a place or to see a person, you will frequently use **до**. This preposition always requires the noun that follows it to be in the Genitive case *(родовий відмінок)*. The literal meaning of **до** focuses on the approach, the journey, or the movement right up to the boundary of your target.

«Читаємо українською»:
— Я йду до парку. *(I am walking to the park.)*
— Ми їдемо до річки. *(We are driving to the river.)*
— Вони летять до моря. *(They are flying to the sea.)*
— Вона біжить до лісу. *(She is running to the forest.)*
— Ти йдеш до університету? *(Are you walking to the university?)*

When your destination is a geographic location, such as a city or a country, **до** is the standard preposition. You will use it when traveling from one city to another, or when flying internationally. For masculine proper nouns ending in a consonant, you add **-а** or **-я**. For feminine proper nouns ending in **-а** or **-я**, the ending changes to **-и** or **-і**.

**Місто → до міста** *(City → to the city)*:
— Київ → до Києва *(to Kyiv)*
— Львів → до Львова *(to Lviv)*
— Харків → до Харкова *(to Kharkiv)*
— Одеса → до Одеси *(to Odesa)*
— Полтава → до Полтави *(to Poltava)*

**Країна → до країни** *(Country → to the country)*:
— Україна → до України *(to Ukraine)*
— Польща → до Польщі *(to Poland)*
— Японія → до Японії *(to Japan)*
— Америка → до Америки *(to America)*

«Читаємо українською»:
— Завтра ми їдемо до Києва на екскурсію. *(Tomorrow we are going to Kyiv for an excursion.)*
— Мій брат часто літає до Польщі. *(My brother often flies to Poland.)*
— Улітку вони поїдуть до Одеси. *(In the summer they will go to Odesa.)*
— Туристи приїхали до Львова вранці. *(The tourists arrived in Lviv in the morning.)*
— Коли ти летиш до Японії? *(When are you flying to Japan?)*

In English, you might say "I am going to the doctor" or "I am going to my friend's house." In Ukrainian, this idea is expressed simply and elegantly using **до** plus a person in the Genitive case. When you say you are going "to a person," it automatically implies that you are going to their home, their office, their room, or their professional establishment. There is no need to add words for "house" or "office" unless you want to emphasize the physical building.

**До + людина** *(To + person)*:
— друг *(friend)* → до друга *(to a friend's place)*
— лікар *(doctor)* → до лікаря *(to the doctor)*
— бабуся *(grandmother)* → до бабусі *(to grandma's)*
— сестра *(sister)* → до сестри *(to sister's place)*
— стоматолог *(dentist)* → до стоматолога *(to the dentist)*

«Читаємо українською»:
— Увечері я йду до друга грати в шахи. *(In the evening I am going to a friend's to play chess.)*
— У мене болить зуб, я йду до лікаря. *(My tooth hurts, I am going to the doctor.)*
— На вихідних ми їдемо до бабусі в село. *(On the weekend we are going to grandma's in the village.)*
— Вона часто ходить до сусідки на каву. *(She often goes to the neighbor's for coffee.)*
— Діти побігли до мами. *(The children ran to mom.)*

Let's look closer at the Genitive endings you need for these directional phrases. The ending depends on the gender of the noun and whether its stem is hard or soft.

**Чоловічий рід** *(Masculine)*:
Hard stems take **-а** (for living beings and cities) or **-у** (for many inanimate spaces or buildings). Soft stems take **-я** or **-ю**.
— будинок *(building)* → до будинку
— магазин *(store)* → до магазину
— музей *(museum)* → до музею
— готель *(hotel)* → до готелю
— вокзал *(train station)* → до вокзалу

**Жіночий рід** *(Feminine)*:
Hard stems take **-и**. Soft stems take **-і** (or **-ї** after a vowel).
— школа *(school)* → до школи
— аптека *(pharmacy)* → до аптеки
— станція *(station)* → до станції
— лікарня *(hospital)* → до лікарні
— кімната *(room)* → до кімнати

**Середній рід** *(Neuter)*:
Hard stems take **-а**. Soft stems take **-я**.
— озеро *(lake)* → до озера
— місто *(city)* → до міста
— море *(sea)* → до моря

«Читаємо українською»:
— Студенти йдуть до музею мистецтва. *(The students are going to the art museum.)*
— Ми повільно йшли до озера. *(We walked slowly to the lake.)*
— Автобус їде до станції метро. *(The bus goes to the subway station.)*
— Він щодня ходить до школи пішки. *(He walks to school every day.)*
— Вона повернулася до кімнати. *(She returned to the room.)*

You already know that you can use **в** *(in, to)* or **на** *(on, to)* with the Accusative case for direction. For example, you can say:
— Я йду в магазин. *(I am going to the store.)*

So, what is the difference between this and using **до**? Grammatically, both are correct. Conceptually, **до** often emphasizes the journey, the direction, or approaching the entrance of the place. Meanwhile, **в** or **на** strongly emphasizes the destination itself and the act of entering the interior. However, in modern, everyday Ukrainian, they are frequently interchangeable for general direction. You can use whichever fits the context or feels more natural. There is no strict hierarchy — both are standard. Note that with people, you must always use **до** (you cannot go *into* a person).

Порівнюємо *(Let's compare)*:
— Ми йдемо в театр. *(We are going to the theater — focus on the event or entering.)*
— Ми йдемо до театру. *(We are walking to the theater — focus on the route or building.)*
— Вона їде на роботу. *(She is going to work — standard idiom.)*
— Вона йде до офісу. *(She is walking to the office — focus on the physical place.)*

> — **Олена:** Ти куди зараз ідеш? *(Where are you going now?)*
> — **Марко:** Я йду до супермаркету. Треба купити молоко. *(I am going to the supermarket. I need to buy milk.)*
> — **Олена:** А потім? *(And then?)*
> — **Марко:** А потім — додому! *(And then — home!)*

A practical situation where you use **до** constantly is when giving directions to a taxi driver. You simply name your destinations using **до** plus the Genitive case.

> — **Пасажир:** Добрий день! До вокзалу, будь ласка. *(Good day! To the train station, please.)*
> — **Таксист:** Добрий день. Сідайте. Їдемо до вокзалу. *(Good day. Have a seat. We are going to the train station.)*
> — **Пасажир:** Ой, зачекайте. А тепер спочатку до аптеки. *(Oh, wait. And now to the pharmacy first.)*
> — **Таксист:** Добре, повертаємо до аптеки. *(Okay, we are turning to the pharmacy.)*
> — **Пасажир:** А потім до готелю «Дніпро». *(And then to the "Dnipro" hotel.)*
> — **Таксист:** Зрозумів. Аптека, а потім до готелю. *(Understood. Pharmacy, and then to the hotel.)*

<!-- INJECT_ACTIVITY: fill-in, 12 sentences with до + Genitive for direction -->


## До якого часу? До + родовий для часу (Until When? До + Genitive for Time)

В українській мові ми часто говоримо про час та його межі. *(In the Ukrainian language, we often talk about time and its limits.)* 
When you want to express how long an action continues, you use the preposition **до** *(until)* with the Genitive case. This structure sets a strict limit or boundary for an ongoing state. It means the action persists steadily right up to that specific moment in time, and then it stops. The preposition **до** clearly marks the absolute end point of the duration.

«Читаємо українською» *(Reading in Ukrainian)*:
— Я буду на роботі до вечора. *(I will be at work until evening.)*
— На вечірці ми танцювали до ранку. *(At the party, we danced until morning.)*
— Діти грали в парку до ночі. *(The children played in the park until night.)*
— Я планую жити в Києві до літа. *(I plan to live in Kyiv until summer.)*
— Студенти уважно читали текст до кінця уроку. *(The students read the text attentively until the end of the lesson.)*
— Мій друг спав до обіду. *(My friend slept until noon.)*

In all these examples, the action is continuous. The person is at work the whole time, dancing the whole time, or sleeping the whole time until the boundary is reached. The noun after **до** must always take the Genitive case ending: **вечір** *(evening)* becomes **до вечора**, **ранок** *(morning)* becomes **до ранку**, **літо** *(summer)* becomes **до літа**, and **обід** *(noon/lunch)* becomes **до обіду**.

Час — це також дедлайни та важливі плани. *(Time is also deadlines and important plans.)* 
Besides continuous actions, **до** is heavily used to set deadlines for tasks and appointments. In English, this is usually translated as "by" or "no later than". The grammar remains exactly the same: **до** + Genitive case. However, the meaning shifts slightly. Instead of an action continuing the whole time, the event must happen at some point *before* or exactly *at* the limit.

«Читаємо українською» *(Reading in Ukrainian)*:
— Мені треба зробити цей новий проєкт до п'ятниці. *(I need to do this new project by Friday.)*
— Будь ласка, прийдіть на зустріч до восьмої години. *(Please, come to the meeting by eight o'clock.)*
— Ви повинні написати цей складний тест до завтра. *(You must write this difficult test by tomorrow.)*
— Я обов'язково поверну гроші до понеділка. *(I will definitely return the money by Monday.)*
— Ми маємо купити квитки на потяг до суботи. *(We have to buy the train tickets by Saturday.)*

Notice how verbs like **зробити** *(to finish/do)*, **прийти** *(to come)*, and **купити** *(to buy)* represent single, completed actions. They do not describe a continuous state. The preposition **до** establishes the absolute final moment when this action can occur. Note that words like **завтра** *(tomorrow)* are adverbs and do not change their form after **до**.

> — **Начальник:** Коли звіт буде готовий? *(When will the report be ready?)*
> — **Менеджер:** Я напишу його до середи. *(I will write it by Wednesday.)*
> — **Начальник:** Це запізно. Мені потрібні цифри раніше. Зробіть це до вівторка. *(That's too late. I need the numbers earlier. Do it by Tuesday.)*
> — **Менеджер:** Добре, я надішлю звіт до вечора. *(Okay, I will send the report by evening.)*

Від початку і до самого кінця. *(From the beginning and to the very end.)*
To describe full time ranges, Ukrainian uses paired prepositions. You already know how to set the end point with **до**. To set the starting point, use **від** *(from)* or **з** *(from/since)*. Both of these starting prepositions require the Genitive case. This combination creates a clear, defined block of time. 

«Читаємо українською» *(Reading in Ukrainian)*:
— Я щодня працюю від ранку до вечора. *(I work every day from morning to evening.)*
— Цей великий магазин працює з понеділка до п'ятниці. *(This big store works from Monday to Friday.)*
— Ми чекали на тебе з третьої до п'ятої години. *(We waited for you from three to five o'clock.)*
— Від січня до травня ми вивчали українську історію. *(From January to May we studied Ukrainian history.)*
— Кав'ярня зачинена на перерву з першої до другої. *(The cafe is closed for a break from one to two.)*
— Вона жила в цьому місті від осені до весни. *(She lived in this city from autumn to spring.)*

Both **з** and **від** are standard for time ranges. Often, **з** is used with days of the week or specific hours, while **від** is common with general periods like morning, evening, seasons, or months. The second part of the range always uses **до** + Genitive. 

Розклад роботи та плани. *(Work schedule and plans.)*
One of the most practical everyday applications of **до** is reading and discussing schedules, business hours, and daily routines. When you want to know when a place closes, or when a person finishes their shift, you will use **до** with hours or days of the week. To ask "until what time?", you say **До котрої години?** *(Until which hour?)*.

«Читаємо українською» *(Reading in Ukrainian)*:
— Наша нова аптека відчинена до дев'ятої години. *(Our new pharmacy is open until nine o'clock.)*
— Музей працює щодня, але в неділю тільки до шостої. *(The museum works every day, but on Sunday only until six.)*
— Я зазвичай працюю до сьомої, а потім іду додому відпочивати. *(I usually work until seven, and then I go home to rest.)*
— Супермаркет відчинений з восьмої ранку до десятої вечора. *(The supermarket is open from eight in the morning until ten in the evening.)*
— Мій молодший брат читає цікаву книгу до пізньої ночі. *(My younger brother reads an interesting book until late night.)*

> — **Клієнт:** Вибачте, до котрої години ви сьогодні працюєте? *(Excuse me, until what time do you work today?)*
> — **Касир:** Ми працюємо до десятої години. *(We work until ten o'clock.)*
> — **Клієнт:** А в неділю графік такий самий? *(And on Sunday is the schedule the same?)*
> — **Касир:** Ні, у неділю магазин відчинений тільки до восьмої. *(No, on Sunday the store is open only until eight.)*

<!-- INJECT_ACTIVITY: fill-in, 12 sentences with до + Genitive for time limits and deadlines -->


## До + родовий: решта значень та узагальнення (До + Genitive: Other Meanings and Summary)

Beyond physical movement and time, the preposition **до** with the Genitive case expresses purpose and abstract destinations. Ukrainian has many fixed phrases using this construction that you will hear every day. For example, the standard greeting **до побачення** *(goodbye)* literally means "until seeing" or "until the meeting," where **побачення** *(meeting/date)* is in the Genitive. Another very common conversational phrase is **до речі** *(by the way)*, which translates to "to the point" or "to the thing" (**річ** *(thing)* in Genitive). You will also use **до** to show readiness or preparation for a specific event or goal. When you are ready for something, you use the adjective **готовий** *(ready)* for masculine, **готова** *(ready)* for feminine, or **готові** *(ready)* for plural, followed by **до** and the Genitive.

«Читаємо українською» *(Reading in Ukrainian)*:
— Студенти вже добре готові до екзамену. *(The students are already well ready for the exam.)*
— До речі, я вчора купив квитки в кіно. *(By the way, I bought tickets to the cinema yesterday.)*
— Я ще не готовий до цієї серйозної розмови. *(I am not yet ready for this serious conversation.)*
— Мама зараз готує смачну вечерю до свята. *(Mom is now preparing a tasty dinner for the holiday.)*
— До зустрічі завтра вранці біля університету! *(See you tomorrow morning near the university!)*

> — **Викладач:** Добрий день! Ви готові до тесту? *(Good day! Are you ready for the test?)*
> — **Студент:** Так, я багато читав. До речі, скільки часу ми маємо? *(Yes, I read a lot. By the way, how much time do we have?)*
> — **Викладач:** У вас є одна година. *(You have one hour.)*
> — **Студент:** Дякую. До побачення після уроку! *(Thank you. Goodbye after the lesson!)*

The preposition **до** also shows addition, connection, or relation between things. When you add a new item to an existing group, you use the verb **додати** *(to add)* followed by **до** *(to)*. For example, you can say **додати до списку** *(to add to the list)* when shopping. In academic or learning contexts, when you ask questions about a specific text, Ukrainians say **ставити питання до тексту** *(to ask questions to the text)*. Furthermore, **до** expresses your attitude, feelings, or interest directed toward someone or something. You can have **великий інтерес до мови** *(great interest in the language)*, **любов до музики** *(love for music)*, or a specific **ставлення до роботи** *(attitude toward work)*. This shows that your emotions and actions are moving toward a concept.

«Читаємо українською» *(Reading in Ukrainian)*:
— Продавець додав свіжі яблука до мого замовлення. *(The seller added fresh apples to my order.)*
— Учитель просить поставити п'ять питань до нового тексту. *(The teacher asks to pose five questions to the new text.)*
— Мій молодший брат має великий інтерес до історії. *(My younger brother has a great interest in history.)*
— У нього завжди дуже серйозне ставлення до роботи. *(He always has a very serious attitude toward work.)*
— Будь ласка, додайте холодне молоко до моєї кави. *(Please, add cold milk to my coffee.)*

> — **Менеджер:** Як твоє нове завдання? *(How is your new task?)*
> — **Аналітик:** Нормально. Але я хочу додати нові дані до звіту. *(Fine. But I want to add new data to the report.)*
> — **Менеджер:** Добре. Яке твоє загальне ставлення до цього проєкту? *(Okay. What is your general attitude toward this project?)*
> — **Аналітик:** Я маю великий інтерес до цієї теми. *(I have a great interest in this topic.)*

Let's consolidate the spatial and temporal prepositions you know that always use the Genitive case. You have learned **до** *(toward/until)*, **від** *(away from/since)*, and **після** *(after)*. All three require the Genitive case, but they point in different directions. For physical space, **від** indicates moving away from a starting point, while **до** indicates moving toward an endpoint. For time, **від** sets the starting limit, **до** sets the ending limit, and **після** indicates an action happening later. Understanding these specific vectors helps you navigate both city streets and daily schedules accurately.

«Читаємо українською» *(Reading in Ukrainian)*:
— Ми швидко їхали від Києва до Львова п'ять годин. *(We rode quickly from Kyiv to Lviv for five hours.)*
— Я працюю в офісі від ранку до пізнього вечора. *(I work in the office from morning to late evening.)*
— Після вечора ми будемо спокійно відпочивати вдома. *(After evening we will calmly rest at home.)*
— Від вокзалу до нашого готелю можна швидко йти пішки. *(From the station to our hotel one can quickly walk on foot.)*
— Після смачного обіду я відразу піду до лікаря. *(After a tasty lunch I will immediately go to the doctor.)*

> — **Турист:** Як доїхати від центру міста до старого музею? *(How to get from the city center to the old museum?)*
> — **Гід:** Це дуже близько. Від площі йдіть прямо до парку. *(It is very close. From the square walk straight to the park.)*
> — **Турист:** А що ми будемо робити після цікавої екскурсії? *(And what will we do after the interesting excursion?)*
> — **Гід:** Після музею ми разом підемо до українського ресторану. *(After the museum we will go together to a Ukrainian restaurant.)*

You now have a complete picture of how versatile the preposition **до** is when paired with the Genitive case. It is one of the most frequent words in the Ukrainian language. Let's summarize its main functions so you can confidently use it in any situation.

**Напрямок (Місце) / Direction (Place):**
Moving toward a physical destination.
— Ми їдемо до школи. *(We are riding to school.)*
— Вони йдуть до Львова. *(They are going to Lviv.)*

**Напрямок (Особа) / Direction (Person):**
Going to see someone or to their place.
— Я йду до лікаря. *(I am going to the doctor.)*
— Діти їдуть до бабусі. *(The children are riding to grandma's.)*

**Ліміт часу / Time Limit:**
Expressing "until" a certain period.
— Магазин працює до вечора. *(The store works until evening.)*
— Ми чекали до понеділка. *(We waited until Monday.)*

**Дедлайн / Deadline:**
Expressing "by" a specific time.
— Зроби це до восьмої години. *(Do this by eight o'clock.)*
— Проєкт треба здати до завтра. *(The project must be submitted by tomorrow.)*

**Мета та сталі вирази / Purpose and Fixed Phrases:**
Readiness, greetings, and common idioms.
— Я готовий до екзамену. *(I am ready for the exam.)*
— До побачення! *(Goodbye!)*
— До речі, де мій телефон? *(By the way, where is my phone?)*

**Зв'язок / Relation:**
Adding to a set or expressing an attitude.
— Треба додати це до списку. *(One needs to add this to the list.)*
— У неї гарне ставлення до людей. *(She has a good attitude toward people.)*

<!-- INJECT_ACTIVITY: match-up, Match 12 до-phrases with their specific function (Direction, Time Limit, Purpose, Relation) -->

<!-- INJECT_ACTIVITY: quiz, Choose the correct meaning of до in 12 contextual sentences -->

<!-- INJECT_ACTIVITY: group-sort, Sort 12 phrases into categories: Direction vs. Time vs. Abstract/Purpose -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-direction
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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

---

## Learner Level Context

**Level: A2 (Module 11/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
