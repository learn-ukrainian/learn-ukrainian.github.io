<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-direction.yaml` file for module **11: Куди? До якого часу?** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-correct-genitive-noun-form -->`
- `<!-- INJECT_ACTIVITY: quiz-meaning-context -->`
- `<!-- INJECT_ACTIVITY: match-up-functions -->`
- `<!-- INJECT_ACTIVITY: group-sort-categories -->`

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


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

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
## Куди ти йдеш? До + родовий для напрямку (~770 words)

Уявіть ситуацію в таксі. Пасажир сідає в машину і називає свої плани на день.

> *Imagine a situation in a taxi. A passenger gets into the car and names their plans for the day.*

> — **Таксист:** Добрий день! Куди ми їдемо? *(Good afternoon! Where are we going?)*
> — **Пасажир:** Добрий день! Мені потрібно до вокзалу, будь ласка. *(Good afternoon! I need to go to the station, please.)*
> — **Таксист:** Зрозумів. До центрального вокзалу? *(Understood. To the central station?)*
> — **Пасажир:** Так. А потім до аптеки, вона там поруч. *(Yes. And then to the pharmacy, it is nearby there.)*
> — **Таксист:** Добре. Я зачекаю вас там. *(Okay. I will wait for you there.)*
> — **Пасажир:** Чекайте до п'ятої години. А потім поїдемо до готелю. *(Wait until five o'clock. And then we will go to the hotel.)*
> — **Таксист:** Без проблем. Маршрут зрозумілий. *(No problem. The route is clear.)*

In Ukrainian grammar, expressing your destination is a fundamental skill. When you want to specify a direction or a final stop for your movement, you frequently use the preposition **до** (to, toward). This small but mighty word is your key to navigating cities and organizing your schedule. The word **напрямок** (direction) is what we are focusing on here.

Щоб правильно вказати напрямок, ми використовуємо прийменник «до» та родовий відмінок. Ви можете побачити це в нашому діалозі. Кожен іменник змінює своє закінчення після цього прийменника. Наприклад, базова форма «вокзал» змінюється і стає «до вокзалу».

> *To correctly indicate direction, we use the preposition "до" and the Genitive case. You can see this in our dialogue. Every noun changes its ending after this preposition. For example, the basic form "вокзал" changes and becomes "до вокзалу".*

This transformation is predictable and essential. The word **аптека** (pharmacy) drops its final vowel and transforms into **до аптеки**. Similarly, the masculine noun **готель** (hotel) takes a new ending to become **до готелю**. Whenever you hear or read the preposition **до**, your brain should immediately prepare to use the Genitive case for the following noun.

Using this construction is the most natural way to talk about traveling to cities, countries, or specific regions. Whether you are planning a grand vacation or a quick weekend getaway, the Genitive case will be your constant companion on the journey. 

Коли ми говоримо про міста або країни, ми завжди вживаємо цю граматичну конструкцію. Цього літа ми поїхали до України. Ми довго планували цю подорож і купили квитки до Львова. Завтра ти прилетиш до Києва, і ми підемо гуляти містом. Мої друзі часто їздять до Польщі на вихідні.

> *When we talk about cities or countries, we always use this grammatical construction. This summer we went to Ukraine. We planned this trip for a long time and bought tickets to Lviv. Tomorrow you will fly to Kyiv, and we will go walking around the city. My friends often travel to Poland for the weekend.*

Notice how the names of the cities change: Львів becomes **до Львова**, and Київ becomes **до Києва**. The countries follow the same pattern: Україна changes to **до України**, and Польща becomes **до Польщі**. This rule applies universally to geographical names when they are your destination.

Now, let's look at a crucial difference between Ukrainian and English. In English, you go "to the doctor" or "to a friend's house." In Ukrainian, when your destination is a person, you must use **до** plus the Genitive case. It literally translates as going "to the person." 

Кожного разу, коли ви йдете в гості, ви йдете до людини. Сьогодні ввечері я йду до друга на вечерю. У неділю ми поїдемо в село до бабусі. Я хочу записатися на прийом до лікаря, бо я погано себе почуваю. Завтра мій брат іде до стоматолога.

> *Every time you go visiting, you go to a person. Tonight I am going to a friend's for dinner. On Sunday we will go to the village to see grandmother. I want to make an appointment with the doctor because I feel unwell. Tomorrow my brother is going to the dentist.*

:::tip
**Did you know?**
Unlike Russian, which often uses a different preposition and case for people (к + Dative, like "к маме"), Ukrainian strictly and elegantly uses **до** + Genitive for both places and people (**до мами**). Using "до" for people is a hallmark of natural, authentic Ukrainian syntax.
:::

You will constantly hear phrases like **до лікаря** (to the doctor) and **до бабусі** (to grandmother). Never try to use other prepositions when a person is your destination.

You might be wondering about other ways to say "to." You have probably already learned to use **в** or **на** with the Accusative case to express direction. So, what is the difference between saying "я йду до магазину" and "я йду в магазин"? The good news is that both are completely standard and natural in modern Ukrainian.

Різниця між цими фразами дуже маленька і залежить від контексту. Коли ви кажете «я йду до магазину», ви акцентуєте увагу на самому маршруті та процесі руху. Ви говорите про напрямок. Коли ви кажете «я йду в магазин», ви більше думаєте про кінцеву точку і про те, що ви будете всередині будівлі.

> *The difference between these phrases is very small and depends on the context. When you say "я йду до магазину", you focus attention on the route itself and the process of movement. You are talking about the direction. When you say "я йду в магазин", you are thinking more about the final point and about the fact that you will be inside the building.*

There is no strict hierarchy between these two options. You can choose whichever feels more appropriate for what you want to emphasize: the journey toward the place (**до**) or the physical entry into the destination (**в** / **на**).

Finally, let's briefly review the endings for the Genitive case that you need to use after the preposition **до**. Your choice of ending depends on the gender of the noun and whether its stem is hard or soft. 

Чоловічий рід має різні закінчення. Тверда група отримує закінчення «-у» або «-а», наприклад, «до будинку» або «до парку». М'яка група закінчується на «-ю» або «-я», як у слові «до музею». Жіночий рід також змінюється за правилами. Тверда група має закінчення «-и», як «до школи», а м'яка отримує «-і», як «до станції». Середній рід часто має закінчення «-я», наприклад, «до моря».

> *Masculine gender has different endings. The hard group gets the ending "-у" or "-а", for example, "до будинку" or "до парку". The soft group ends in "-ю" or "-я", as in the word "до музею" (to the museum). Feminine gender also changes according to the rules. The hard group has the ending "-и", like "до школи", and the soft one gets "-і", like "до станції". Neuter gender often has the ending "-я", for example, "до моря".*

Memorizing these patterns will make expressing your destination automatic and effortless.

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-correct-genitive-noun-form -->

## До якого часу? До + родовий для часу (~715 words)

We have seen how the preposition **до** sets the destination for a physical journey. In Ukrainian, we use the exact same logic for time. When you are moving through the day or the calendar, **до** marks the final point, the moment when an action stops. In English, this translates to "until."

Ми вчимося в університеті до літа. Потім у нас будуть великі канікули. Я часто читаю цікаві книги до пізньої ночі. Мій брат любить спати до обіду в неділю. Ми гуляли в парку до самого вечора.

> *We study at the university until summer. Then we will have long holidays. I often read interesting books until late at night. My brother likes to sleep until noon on Sunday. We walked in the park until the very evening.*

When you want to say "until," you simply take the preposition **до** and put the time word in the Genitive case. Some of the most frequent expressions you will use to describe the **вечір** (evening) or the **ранок** (morning) are **до вечора** (until evening) and **до ранку** (until morning). You will also frequently hear days of the week, like **до понеділка** (until Monday).

:::note
**Quick tip** — To ask "until when?", you can say **до якого часу?** or simply **доки?**.
:::

While **до** often means "until," it also functions as "by" when setting a deadline. If you need to finish a task before a certain limit, you again use **до** followed by the Genitive case.

Студенти повинні зробити це складне завдання до п'ятниці. Я планую закінчити мою роботу до вечора. Будь ласка, зателефонуй мені до восьмої. Він має написати статтю до ранку.

> *Students must do this difficult task by Friday. I plan to finish my work by evening. Please, call me by eight o'clock. He has to write the article by morning.*

Notice the phrase **до восьмої** in the example above. This is short for **до восьмої години** (by eight o'clock). In spoken Ukrainian, people frequently drop the word for "hour" when the context is clear. Whether the action takes up the entire time ("until") or must be completed before the limit ("by"), the grammar remains identical.

Often, you need to express a complete time range with a starting point and an ending point. For this, Ukrainian pairs **до** with the prepositions **з** or **від** ("from"). Just as a train travels **з Києва до Варшави**, an action travels from one moment to another.

Я маю працювати в офісі з понеділка до п'ятниці. Ми відпочивали на морі від початку липня до кінця серпня. Цей великий магазин працює щодня з десятої до сьомої.

> *I have to work in the office from Monday to Friday. We rested at the sea from the beginning of July to the end of August. This large store works every day from ten to seven.*

Both **з** and **від** are correct and natural when talking about time. You can say **з ранку до вечора** or **від ранку до вечора**. The most important rule is that both the starting point and the ending point must be in the Genitive case.

Let's look at some common daily phrases and contexts where you will hear **до** used for time. You will encounter these everywhere in Ukraine, from shop signs to everyday conversations.

Цей новий супермаркет відкрито до дев'ятої. Я буду чекати тебе біля метро до завтра. Нам треба прочитати цей довгий текст до початку уроку. Вони жили в цьому гарному місті ще до війни.

> *This new supermarket is open until nine. I will wait for you near the subway until tomorrow. We need to read this long text before the start of the lesson. They lived in this beautiful city even before the war.*

You can see that **до** is incredibly versatile. You can say "чекати до **завтра** (tomorrow)" when making plans with friends. The phrase **до війни** (before the war) is unfortunately very common in modern historical and personal discussions. When referring to events, like **до початку уроку** (until the start of the lesson), the noun "start" takes the Genitive ending.

> — **Олена:** Коли ти будеш вдома сьогодні? *(When will you be at home today?)*
> — **Марко:** Я маю працювати в офісі до шостої. *(I have to work in the office until six.)*
> — **Олена:** Добре. А той магазин відкрито до восьмої? *(Good. And is that store open until eight?)*
> — **Марко:** Ні, він працює тільки до сьомої. Я куплю хліб до вечора. *(No, it only works until seven. I will buy bread by evening.)*

If you step back and look at the big picture, you will notice a beautiful consistency in Ukrainian grammar. The language treats space and time as the same kind of path. The grammatical structure is identical whether you are mapping a physical route or a chronological schedule.

Мій швидкий поїзд їде з Харкова до Одеси. Мій робочий день триває з самого ранку до вечора.

> *My fast train goes from Kharkiv to Odesa. My workday lasts from the very morning to evening.*

In both sentences, you have a starting point introduced by **з** and an ending point introduced by **до**. Both prepositions demand the Genitive case. This means that once you learn how to say you are traveling to the **музей** (museum), you automatically know the grammar needed to say you will be busy until the evening. It is always about movement toward a limit.

## До + родовий: решта значень та узагальнення (~715 words)

We have seen that the preposition **до** indicates movement in space and time. It shows a clear **напрямок** (direction) toward a specific physical destination. But Ukrainian uses this same geometric concept for abstract ideas. When you prepare for something, your effort is moving toward a destination. When you have a feeling about something, your emotion is directed toward an object. In these cases, **до** expresses your **мета** (goal, purpose) or the relationship between two different concepts. The grammatical rule remains exactly the same. You always use the Genitive case after this preposition.

Прийменник до має багато цікавих абстрактних значень. Ми часто використовуємо його, коли говоримо про наші плани, почуття або серйозну підготовку. Це завжди рух до якоїсь конкретної мети або результату. Граматика ніколи не змінюється в таких ситуаціях. Будь-яке слово після цього прийменника завжди стоїть у родовому відмінку.

> *The preposition "до" has many interesting abstract meanings. We often use it when we talk about our plans, feelings, or serious preparation. It is always a movement toward some specific goal or result. The grammar never changes in such situations. Any word after this preposition always stands in the Genitive case.*

One of the most frequent abstract uses of **до** is to express readiness for a future event. If you are a university student, you might say you are ready for an **екзамен** (exam). You use the adjective **готовий** (ready) followed by **до** and the correct Genitive noun.

Сьогодні студенти дуже хвилюються і багато читають. Завтра буде складний тест з історії України. Мій брат довго читав товстий підручник. Зараз він повністю готовий до екзамену. Він добре знає всі важливі дати.

> *Today the students are very worried and are reading a lot. Tomorrow there will be a difficult test on the history of Ukraine. My brother read a thick textbook for a long time. Now he is fully ready for the exam. He knows all the important dates well.*

You will also find **до** in many fixed expressions that imply a future goal or a social interaction. For example, the common phrase for "by the way" or "to the point" is **до речі**. The word **побачення** (meeting, date) means a meeting, so the standard way to say goodbye is literally "until the meeting." 

Коли ми йдемо додому, ми завжди кажемо друзям: «До побачення!». Якщо ми плануємо зустрітися знову дуже скоро, ми говоримо: «До завтра!» або «До зустрічі!». Це дуже ввічливі і природні українські фрази.

> *When we go home, we always say to our friends: "Goodbye!". If we plan to meet again very soon, we say: "Until tomorrow!" or "Until we meet!". These are very polite and natural Ukrainian phrases.*

Another common function of **до** is expressing addition or connection. When you link two things together, you are metaphorically moving one object toward another. If you are organizing your day, you might add a new task to your **список** (list). 

Я пишу новий великий план на наступний тиждень. Мені треба додати кілька важливих справ до списку. Я хочу купити нову книгу і швидко прочитати її.

> *I am writing a new big plan for next week. I need to add a few important tasks to the list. I want to buy a new book and read it quickly.*

Similarly, this preposition is used to describe feelings, attitudes, or interest directed at something or someone. It shows the vector of your emotion. The word **ставлення** means attitude, and **інтерес** means interest.

Мій новий колега має дуже гарне ставлення до роботи. Він завжди виконує всі складні завдання вчасно. Також він має великий інтерес до мови і вивчає нові слова щодня.

> *My new colleague has a very good attitude toward work. He always completes all difficult tasks on time. Also, he has a great interest in the language and learns new words every day.*

> — **Олена:** Ти вже готовий до екзамену з математики? *(Are you already ready for the math exam?)*
> — **Марко:** Так, я додав усі формули до списку. *(Yes, I added all the formulas to the list.)*
> — **Олена:** До речі, ти знаєш, що тест буде завтра? *(By the way, do you know the test is tomorrow?)*
> — **Марко:** Звичайно! У мене серйозне ставлення до навчання. *(Of course! I have a serious attitude toward studying.)*

:::info
**Grammar box**
Notice how the English translations use different prepositions like "for", "to", "toward", or "by". In Ukrainian, all these concepts share the underlying idea of a path reaching a target, which is why they all use **до** + Genitive.
:::

Now that we have explored the various meanings of this preposition, it is helpful to compare it with other prepositions you already know. In earlier modules, you learned about **від** (from) and **після** (after). All three of these prepositions require the Genitive case, but they express entirely different vectors and directions. You will often hear this with times of day, stretching from the **ранок** (morning) to the **вечір** (evening).

Прийменник до показує активний рух до кінцевої точки або мети. Прийменник від показує рух від початкової точки. Прийменник після показує логічну послідовність у часі. Ці три слова допомагають нам орієнтуватися.

> *The preposition "до" shows active movement toward an end point or goal. The preposition "від" shows movement away from a starting point. The preposition "після" shows logical sequence in time. These three words help us orient ourselves.*

If you understand the starting point, the ending point, and what happens later, you can describe almost any situation in your daily life. Let's see how they work together in a realistic context.

Сьогодні ми довго йдемо від старого парку до музею. Після музею ми обов'язково підемо до ресторану. Наша цікава екскурсія триває від самого ранку до вечора.

> *Today we are walking for a long time from the old park to the museum. After the museum, we will definitely go to a restaurant. Our interesting excursion lasts from the very morning to the evening.*

Let us summarize everything we have covered about this essential preposition. We can group its uses into five main categories: physical direction to a place like a **музей** (museum), personal direction to a person like a **лікар** (doctor) or **бабуся** (grandmother), a continuous time limit, a strict deadline, and an abstract purpose or relation. Here is a comprehensive overview of how **до** operates with the Genitive case in everyday communication.

| Категорія (Category) | Приклад (Example) | Переклад (Translation) |
| :--- | :--- | :--- |
| **Напрямок (Місце)** | Ми їдемо до великого музею. | *We are going to a large museum.* |
| **Напрямок (Особа)** | Вона йде до бабусі або до лікаря. | *She is going to grandma's or to the doctor.* |
| **Проміжок часу** | Я працюю тут від ранку до вечора. | *I work here from morning to evening.* |
| **Дедлайн** | Будь ласка, зроби це завдання до п'ятниці! | *Please do this task by Friday!* |
| **Мета або зв'язок** | Додай це слово до списку. До побачення! | *Add this word to the list. Goodbye!* |

Ця маленька частка української мови є надзвичайно потужною. Вона органічно поєднує простір, час та наші абстрактні ідеї в одну логічну систему.

> *This small particle of the Ukrainian language is incredibly powerful. It organically unites space, time, and our abstract ideas into one logical system.*

<!-- INJECT_ACTIVITY: quiz-meaning-context -->
<!-- INJECT_ACTIVITY: match-up-functions -->
<!-- INJECT_ACTIVITY: group-sort-categories -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-direction
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
