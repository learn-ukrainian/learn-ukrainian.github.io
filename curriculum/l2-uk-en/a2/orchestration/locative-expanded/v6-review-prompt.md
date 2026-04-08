<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 20: Місцевий відмінок у нових контекстах (A2, A2.3 [Dative Case])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-020
level: A2
sequence: 20
slug: locative-expanded
version: '1.0'
title: Місцевий відмінок у нових контекстах
subtitle: Абстрактні іменники, часові вирази та тема розмови у місцевому відмінку
focus: grammar
pedagogy: PPP
phase: A2.3 [Dative Case]
word_target: 2000
objectives:
  - Learner can use the locative case with abstract nouns to express contexts
    and domains (у житті, в освіті, на роботі, у політиці).
  - Learner can use temporal locative expressions for months, weeks, and
    periods (у минулому місяці, на цьому тижні, у дитинстві).
  - Learner can use topic-marking locative with по + locative for
    communication topics (по телефону, по радіо) and розмовляти/говорити
    про + accusative vs. по + locative distinctions.
  - Learner can combine locative with prepositions у/в, на, по in varied
    real-life contexts beyond simple physical location.
dialogue_situations:
  - setting: 'Two friends catching up after a long time — talking about life
      changes: Що нового у твоєму житті? — У минулому місяці я змінила роботу.
      Тепер працюю в освіті. А ти? — Я на новому курсі. Розмовляли по
      телефону з мамою — вона хвилюється.'
    speakers:
      - Марія
      - Ігор
    motivation: 'Natural catch-up triggers all three locative extensions:
      abstract (у житті, в освіті), temporal (у минулому місяці), topic
      (по телефону)'
  - setting: 'Student discussing schedule and interests with a tutor: На цьому
      тижні у мене три заняття. У вільний час я читаю про Україну — у
      підручнику з історії. В дитинстві я мало знав про українську культуру.'
    speakers:
      - Студент
      - Викладач
    motivation: 'Temporal locative (на цьому тижні, в дитинстві) + abstract
      domain (в історії, про культуру)'
content_outline:
  - section: 'Місцевий з абстрактними іменниками (Locative with Abstract Nouns)'
    words: 550
    points:
      - 'A1 taught locative for physical location (у місті, на вулиці). Now
        expanding to abstract domains and contexts.'
      - 'Common abstract locative phrases: у житті (in life), в освіті (in
        education), у політиці (in politics), на роботі (at work), в економіці
        (in economics), у мистецтві (in art).'
      - 'Pattern: у/в + abstract noun in locative = "in the domain/field of."
        Note: на роботі (not *у роботі) — на is fixed for робота.'
      - 'Practice forming locative of abstract feminine nouns in -а/-я:
        наука→у науці, політика→у політиці, культура→у культурі.'
  - section: 'Часовий місцевий відмінок (Temporal Locative)'
    words: 600
    points:
      - 'Months: у січні, у лютому, у березні... all months use у/в + locative.
        Masculine months in -ень: -ні (січень→у січні). Neuter місяць compounds:
        у минулому місяці, у наступному місяці.'
      - 'Weeks: на цьому тижні, на минулому тижні, на наступному тижні. Note:
        тиждень uses на (not у).'
      - 'Life periods: у дитинстві (in childhood), у молодості (in youth),
        у старості (in old age), у минулому (in the past), у майбутньому
        (in the future).'
      - 'Contrast with accusative for duration: у понеділок (on Monday, acc.)
        vs. у минулому місяці (last month, loc.). The question test: Коли?
        (temporal loc.) vs. Як довго? (duration, acc.).'
  - section: 'По телефону, по радіо: місцевий із прийменником «по» (Locative
      with "po")'
    words: 500
    points:
      - 'Topic/means with по + locative: по телефону (by phone), по радіо
        (on the radio), по пошті (by mail), по дорозі (on the way).'
      - 'Distinction: говорити по телефону (the medium of communication) vs.
        говорити про телефон (about the phone as a topic). По + locative =
        means/channel. Про + accusative = topic.'
      - 'Common phrases: Я подзвоню по телефону. Ми почули по радіо. Він
        надіслав по пошті. Зустрілися по дорозі додому.'
      - 'Note: по + locative is the traditional Ukrainian pattern. Some modern
        usage shifts to по + dative for distribution (по одному), but for
        communication means, locative is standard.'
  - section: 'Місцевий відмінок: від місця до сенсу (From Place to Meaning)'
    words: 350
    points:
      - 'Summary: locative is not just "where" — it answers де? (location),
        коли? (time), and як? (means/channel).'
      - 'Consolidation table: physical (у місті), abstract (у житті), temporal
        (у січні), means (по телефону) — all locative, four different functions.'
      - 'Practice: building sentences that use 2-3 locative functions together:
        У минулому місяці я розмовляв по телефону з другом у Києві.'
vocabulary_hints:
  required:
    - місцевий (locative (case))
    - абстрактний (abstract)
    - минулий (past, previous)
    - місяць (month)
    - тиждень (week)
    - телефон (phone, telephone)
    - подорож (journey, trip)
    - зустріч (meeting, encounter)
    - думка (thought, opinion)
    - проблема (problem)
  recommended:
    - дитинство (childhood)
    - молодість (youth)
    - майбутнє (future)
    - освіта (education)
    - мистецтво (art)
activity_hints:
  - type: quiz
    focus: 'Identify the function of locative in each sentence (physical
      location, abstract domain, temporal, or means)'
    items: 8
  - type: fill-in
    focus: Complete sentences with the correct locative form of the noun
      (у минулому ___, на цьому ___, по ___)
    items: 8
  - type: match-up
    focus: Match locative expressions with their English equivalents across
      all four function types
    items: 8
  - type: error-correction
    focus: 'Fix preposition errors (e.g., *у роботі → на роботі, *у
      телефону → по телефону, *на минулому місяці → у минулому місяці)'
    items: 8
references:
  - title: Заболотний Grade 5, §28-30
    notes: Місцевий відмінок іменників, прийменники
  - title: Заболотний Grade 6, §34-35
    notes: Часові конструкції з місцевим відмінком
  - title: 'ULP: Ukrainian Cases — Locative'
    url: https://www.ukrainianlessons.com/locative-case/
    notes: Locative case uses including temporal and abstract

</plan_content>

## Generated Content

<generated_module_content>
## Місцевий з абстрактними іменниками (Locative with Abstract Nouns)

На рівні А1 ми вивчали місцевий відмінок як фізичне місце. *(In A1, we studied the locative case as a physical place.)* For example, «у кімнаті» *(in the room)*, «у місті» *(in the city)*, or «на столі» *(on the table)*. Now, we are expanding this concept. The locative case is not just for physical spaces on a map. Це абстрактний простір. *(It is an abstract space.)* We also use it for abstract domains, fields of activity, and general life contexts.

Let's compare two ideas to see the difference clearly. If you say «Я працюю в університеті» *(I work at the university)*, you mean the physical building. It is a concrete place. But if you say «Я працюю в освіті» *(I work in education)*, you mean the abstract field. You could be working from home, but your professional domain is education. This is a very natural and common way to talk about professions and society.

Прочитаймо діалог. *(Let's read the dialogue.)* Марія та Ігор зустрілися на вулиці після довгої перерви. Вони говорять про новини. *(Maria and Ihor met on the street after a long break. They are talking about news.)*

> — **Марія:** Привіт, Ігоре! Рада тебе бачити. Що нового у твоєму житті? *(Hi, Ihor! Glad to see you. What is new in your life?)*
> — **Ігор:** Привіт, Маріє! У минулому місяці я змінив роботу. *(Hi, Maria! Last month I changed jobs.)*
> — **Марія:** Це чудово! Де ти тепер працюєш? *(That is great! Where do you work now?)*
> — **Ігор:** Тепер працюю в освіті. А ти? *(Now I work in education. And you?)*
> — **Марія:** Я на новому курсі в університеті. Вчора розмовляла по телефону з мамою. Вона дуже хвилюється за моє навчання. *(I am on a new course at the university. Yesterday I talked on the phone with mom. She is very worried about my studies.)*

When we talk about a professional sphere or a broad domain of life, we use the specific pattern **у/в + abstract noun in the locative case**. These are not physical places where you can stand or sit, but conceptual spaces where you spend your time, build a career, or focus your energy. Here are some high-frequency combinations for different professional and cultural fields: **у політиці** *(in politics)*, **в економіці** *(in economics)*, **у науці** *(in science)*, and **у мистецтві** *(in art)*. You can also talk about your broad personal experience using **у житті** *(in life)* or **у думках** *(in thoughts)*.

**Читаємо українською (Reading in Ukrainian):**
- Мій старший брат зараз працює у політиці. *(My older brother now works in politics.)*
- Вона зробила велике відкриття у науці. *(She made a great discovery in science.)*
- У сучасному мистецтві немає строгих правил. *(There are no strict rules in modern art.)*
- У моєму житті було багато цікавих людей. *(In my life there were many interesting people.)*

Let's review the grammatical precision for these abstract nouns. Many of these professional fields are feminine nouns ending in the suffix **-ка**. Remember the fundamental consonant mutation rule for the locative case: **к → ц**. When a feminine noun ends in **-ка**, the locative form changes to **-ці**. Thus, «політика» becomes «у політиці», «наука» becomes «у науці», and «економіка» becomes «в економіці». On the other hand, neuter abstract nouns ending in **-я**, such as **життя** *(life)* and **навчання** *(studies/learning)*, are much simpler to decline. They just take the standard **-і** ending. So, the nominative «життя» becomes «у житті», and «навчання» becomes «у навчанні».

**Читаємо українською (Reading in Ukrainian):**
- Музика → Мій друг нічого не розуміє у музиці. *(Music → My friend understands nothing in music.)*
- Культура → Вони багато читають про нове у культурі. *(Culture → They read a lot about what is new in culture.)*
- Навчання → У навчанні завжди є одна типова проблема. *(Studies → There is always one typical problem in studies.)*

There is one major exception regarding the preposition. When we say "at work" in Ukrainian, we always use the preposition **на**. The phrase is **на роботі**, never «у роботі». Why? Because work is viewed as an activity or an event you attend, rather than an enclosed container or a broad abstract domain. Contrast this with specific physical locations or broad concepts: **в офісі** *(at the office)* means you are physically inside the building, and **у бізнесі** *(in business)* means you operate in that specific professional field.

**Читаємо українською (Reading in Ukrainian):**
- Зараз мій тато на роботі, він буде ввечері. *(Right now my dad is at work, he will be here in the evening.)*
- Сьогодні я був у великому новому офісі. *(Today I was in a large new office.)*
- Моя сестра дуже хоче працювати у бізнесі. *(My sister really wants to work in business.)*
- Ми не можемо говорити, тому що ми на роботі. *(We cannot talk, because we are at work.)*

## Часовий місцевий відмінок (Temporal Locative)

The most common use of the temporal locative is with months of the year to answer the question «коли?» *(when?)*. Кожен місяць має свою назву. *(Each month has its name.)* To say that something happens in a specific month, we use the preposition **у** or **в** followed by the locative case. Most Ukrainian months end in the suffix **-ень**, making them masculine nouns. When these decline into the locative case, the **-ень** mutates to **-ні**. Let's look at this predictable pattern.

- **січень** *(January)* → **у січні** *(in January)*
- **березень** *(March)* → **у березні** *(in March)*
- **травень** *(May)* → **у травні** *(in May)*
- **жовтень** *(October)* → **у жовтні** *(in October)*

**Читаємо українською (Reading in Ukrainian):**
- Мій день народження у січні. *(My birthday is in January.)*
- У березні погода часто буває холодна. *(In March the weather is often cold.)*
- У травні ми завжди відпочиваємо на природі. *(In May we always rest in nature.)*
- У жовтні часто йде холодний дощ. *(In October it often rains coldly.)*

While months use the preposition **у/в**, weeks require a different approach. The word **тиждень** *(week)* also ends in **-ень** and mutates to **тижні** in the locative. However, just like the noun **робота** *(work)* takes the preposition **на** (на роботі), **тиждень** requires **на** when used as a time point. To specify which week, you combine **на** with locative adjectives like **цьому** *(this)*, **минулому** *(last)*, or **наступному** *(next)*.

- **на цьому тижні** *(this week)*
- **на минулому тижні** *(last week)*
- **на наступному тижні** *(next week)*

**Читаємо українською (Reading in Ukrainian):**
- Минулий тиждень був дуже теплим. *(The past week was very warm.)*
- На цьому тижні я маю багато роботи. *(This week I have a lot of work.)*
- Ми були в театрі на минулому тижні. *(We were at the theater last week.)*
- На наступному тижні вона їде у відрядження. *(Next week she is going on a business trip.)*

We also use the locative case to talk about broad periods of life and historical eras. These are treated like abstract conceptual spaces where events happen, taking the preposition **у/в**. When sharing stories, you will frequently use phrases like **у дитинстві** *(in childhood)*, **у молодості** *(in youth)*, and **у старості** *(in old age)*. We extend this logic to general historical time, using **у минулому** *(in the past)* and **у майбутньому** *(in the future)*.

**Читаємо українською (Reading in Ukrainian):**
- У дитинстві я жив у маленькому селі. *(In childhood I lived in a small village.)*
- Мій дідусь багато подорожував у молодості. *(My grandfather traveled a lot in his youth.)*
- У минулому люди не мали інтернету. *(In the past people did not have the internet.)*
- Я сподіваюся, що у майбутньому все буде добре. *(I hope that in the future everything will be fine.)*
- У старості вона хоче жити біля моря. *(In old age she wants to live near the sea.)*

Let's see how these temporal and abstract locative phrases blend naturally in conversation. Here, a student is discussing their schedule and interests with a tutor. 

> — **Студент:** Добрий день! На цьому тижні у мене три заняття. *(Good day! This week I have three classes.)*
> — **Викладач:** Це дуже добре. Ви маєте час на домашнє завдання? *(That is very good. Do you have time for homework?)*
> — **Студент:** Так. У вільний час я читаю про Україну — у підручнику з історії. *(Yes. In my free time I read about Ukraine — in a history textbook.)*
> — **Викладач:** Це цікаво! Що саме ви читаєте зараз? *(That is interesting! What exactly are you reading right now?)*
> — **Студент:** В дитинстві я мало знав про українську культуру, тому зараз читаю все. *(In childhood I knew little about Ukrainian culture, so now I am reading everything.)*

It is crucial to understand the difference between a point in time and a duration. The locative case strictly answers the question **Коли?** *(When?)* to pinpoint an exact moment, such as **у січні** *(in January)*. To answer **Як довго?** *(How long?)*, you must use the accusative case, like **увесь січень** *(all January)*. Mixing these is a common mistake. Remember the strict preposition rules: never use «на» for months, and never use «у» for weeks.

**Читаємо українською (Reading in Ukrainian):**
- Коли? Ми зустрілися у травні. *(When? We met in May.)*
- Як довго? Ми працювали весь травень. *(How long? We worked all May.)*
- Коли? Він купив машину на минулому тижні. *(When? He bought a car last week.)*
- Як довго? Він читав цю книгу цілий тиждень. *(How long? He read this book for a whole week.)*

## По телефону, по радіо: місцевий із прийменником «по»

We have seen that the locative case describes where things are and when things happen. Now we will use it to describe *how* we communicate or send things. When indicating a medium of communication or a channel of transmission, Ukrainian uses the preposition **по** *(by/on)* followed by the locative case. Common examples include **по телефону** *(by phone)*, **по радіо** *(on the radio)*, **по телевізору** *(on TV)*, and **по пошті** *(by mail)*. Notice that for many masculine nouns denoting these channels, like **телефон** and **імейл** *(email)*, the locative ending is **-у**.

**Читаємо українською (Reading in Ukrainian):**
- Я часто говорю з мамою по телефону. *(I often talk with my mom by phone.)*
- Ми почули ці новини по радіо. *(We heard these news on the radio.)*
- Дідусь любить дивитися фільми по телевізору. *(Grandpa likes to watch movies on TV.)*
- Вона надіслала важливі документи по пошті. *(She sent the important documents by mail.)*
- Цей концерт показують по телевізору сьогодні. *(They are showing this concert on TV today.)*

Another very common and useful expression using **по** + locative is **по дорозі** *(on the way/along the path)*. This phrase beautifully combines the idea of a physical path with a sense of time or process. You will use this frequently when talking about things that happen while you are traveling from one place to another. 

**Читаємо українською (Reading in Ukrainian):**
- Я зустрів старого друга по дорозі додому. *(I met an old friend on the way home.)*
- Ми купили смачну каву по дорозі на роботу. *(We bought delicious coffee on the way to work.)*

> — **Оксана:** Де ти зараз? *(Where are you now?)*
> — **Тарас:** Я йду пішки. Я зараз по дорозі додому. *(I am walking. I am on the way home right now.)*
> — **Оксана:** Купи хліб по дорозі, будь ласка. *(Buy bread on the way, please.)*
> — **Тарас:** Добре. Я подзвоню тобі по телефону з магазину. *(Okay. I will call you by phone from the store.)*

It is important to distinguish the *medium* of communication from the *topic* of communication. When the phone is the tool you are using to speak, you use the locative case: **говорити по телефону** *(to talk by phone)*. However, if you are discussing the device itself—for example, if you want to buy a new one—the phone becomes the subject of conversation. For topics, Ukrainian uses the preposition **про** *(about)* followed by the accusative case: **говорити про телефон** *(to talk about a phone)*. This logic applies to all communication subjects.

**Читаємо українською (Reading in Ukrainian):**
- Засіб: Я говорю по телефону. *(Means: I am talking by phone.)*
- Тема: Я думаю про новий телефон. *(Topic: I am thinking about a new phone.)*
- Засіб: Ми почули цю пісню по радіо. *(Means: We heard this song on the radio.)*
- Тема: Ми говорили про українське радіо. *(Topic: We were talking about Ukrainian radio.)*
- Засіб: Вона отримала листа по пошті. *(Means: She received a letter by mail.)*
- Тема: Вона читала про нову пошту. *(Topic: She was reading about the new post office.)*

In modern Ukrainian, you might sometimes hear native speakers use the instrumental case without a preposition to indicate means, such as **дзвонити телефоном** *(to call by phone)* or **надіслати поштою** *(to send by mail)*. While this is grammatically correct and elegant, the construction **по** + locative remains the most natural, frequent, and standard way to express communication channels in everyday speech. As an A2 learner, mastering the **по** + locative pattern will make your Ukrainian sound authentic and help you navigate modern digital life. You can easily adapt it to new technologies and internet platforms.

**Читаємо українською (Reading in Ukrainian):**
- Ми часто спілкуємося по скайпу. *(We often communicate on Skype.)*
- Студенти отримали завдання по імейлу. *(The students received the task by email.)*
- Я прочитав цю цікаву статтю в інтернеті. *(I read this interesting article on the internet.)*

> — **Ігор:** Привіт, Маріє! Я дзвонив тобі вчора по телефону. *(Hi, Maria! I called you yesterday by phone.)*
> — **Марія:** Привіт! Вибач, я була на роботі. Я надіслала тобі повідомлення по імейлу. *(Hi! Sorry, I was at work. I sent you a message by email.)*
> — **Ігор:** Так, я бачив. Ти купила каву по дорозі в офіс? *(Yes, I saw it. Did you buy coffee on the way to the office?)*
> — **Марія:** Ні, я пила каву вдома, коли дивилася новини по телевізору. *(No, I drank coffee at home when I was watching the news on TV.)*

## Місцевий відмінок: від місця до сенсу

The locative case is not just for physical places. It also maps abstract spaces, time periods, and communication channels.

**Читаємо українською (Reading in Ukrainian):**
- Спочатку ми вивчали конкретні місця: у парку, на вулиці, в Україні. *(First we studied concrete places: in the park, on the street, in Ukraine.)*
- Тепер ми знаємо час: у січні, у минулому місяці, на цьому тижні. *(Now we know time: in January, last month, this week.)*
- Ми також говоримо про абстрактні сфери життя: на новій роботі, в освіті, у політиці. *(We also talk about abstract spheres of life: in a new job, in education, in politics.)*
- Ми часто слухаємо новини по радіо і говоримо по телефону. *(We often listen to the news on the radio and talk by phone.)*

The "Locative Matrix" summarizes these four functions. 

| Функція (Function) | Прийменник (Preposition) | Приклад (Example) |
| :--- | :--- | :--- |
| **Місце** *(Place)* | **в/у**, **на** | **в офісі** *(in the office)*, **на столі** *(on the table)* |
| **Час** *(Time)* | **в/у**, **на** | **у січні** *(in January)*, **на цьому тижні** *(this week)* |
| **Сфера** *(Abstract)* | **в/у**, **на** | **у житті** *(in life)*, **на роботі** *(at work)* |
| **Засіб** *(Means)* | **по** | **по радіо** *(on the radio)*, **по телефону** *(by phone)* |

> — **Марія:** Ігоре, що нового у твоєму житті? *(Ihor, what is new in your life?)*
> — **Ігор:** У минулому місяці я змінив роботу. *(Last month I changed jobs.)*
> — **Марія:** Були проблеми на роботі? *(Were there problems at work?)*
> — **Ігор:** Ні, просто тепер працюю в освіті. А ти? *(No, just now I work in education. And you?)*
> — **Марія:** Я навчаюся на новому курсі. Учора була цікава зустріч. *(I am studying in a new course. Yesterday there was an interesting meeting.)*
> — **Ігор:** Ти говорила про це з мамою? *(Did you talk about this with mom?)*
> — **Марія:** Так, ми довго розмовляли по телефону. *(Yes, we talked by phone for a long time.)*

Remember: the locative always needs a preposition (**у/в**, **на**, **по**, **при**). Use **на** for weeks (**на цьому тижні**). Watch for consonant shifts: **політика** *(politics)* becomes **у політиці**. Try combining functions in one sentence!

**Читаємо українською (Reading in Ukrainian):**
- Місцевий відмінок завжди має прийменник. *(The locative case always has a preposition.)*
- На цьому тижні у мене немає проблем на роботі. *(This week I have no problems at work.)*
- Мій старший брат зараз працює у політиці. *(My older brother works in politics now.)*
- У минулому місяці я був на цікавій зустрічі. *(Last month I was at an interesting meeting.)*
- У минулому місяці я розмовляв по телефону з другом у Києві. *(Last month I talked by phone with a friend in Kyiv.)*
- У дитинстві ми часто читали про подорожі. *(In childhood we often read about journeys.)*

> — **Студент:** На цьому тижні у мене три заняття. *(This week I have three classes.)*
> — **Викладач:** Що ви зараз вивчаєте? *(What are you studying right now?)*
> — **Студент:** У вільний час я читаю про Україну. *(In my free time I read about Ukraine.)*
> — **Викладач:** Де ви це читаєте? *(Where do you read this?)*
> — **Студент:** У підручнику з історії. *(In a history textbook.)*
> — **Викладач:** Це дуже цікаво. В дитинстві я теж багато читав. *(This is very interesting. In childhood I also read a lot.)*

<!-- EXERCISE_1 -->

<!-- EXERCISE_2 -->

<!-- EXERCISE_3 -->

<!-- EXERCISE_4 -->
</generated_module_content>

**PIPELINE NOTE — Word count: 2936 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 323 words | Not found: 6 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ігоре — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Маріє — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ ень — NOT IN VESUM

All 323 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
