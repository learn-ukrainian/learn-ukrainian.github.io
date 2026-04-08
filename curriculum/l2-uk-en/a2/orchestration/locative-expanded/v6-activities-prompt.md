<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/locative-expanded.yaml` file for module **20: Місцевий відмінок у нових контекстах** (a2).

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

- focus: Identify the function of locative in each sentence (physical location, abstract
    domain, temporal, or means)
  items: 8
  type: quiz
- focus: Complete sentences with the correct locative form of the noun (у минулому
    ___, на цьому ___, по ___)
  items: 8
  type: fill-in
- focus: Match locative expressions with their English equivalents across all four
    function types
  items: 8
  type: match-up
- focus: Fix preposition errors (e.g., *у роботі → на роботі, *у телефону → по телефону,
    *на минулому місяці → у минулому місяці)
  items: 8
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дитинство (childhood)
- молодість (youth)
- майбутнє (future)
- освіта (education)
- мистецтво (art)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Місцевий з абстрактними іменниками (Locative with Abstract Nouns)

На рівні А1 ми вивчали місцевий відмінок як фізичне місце. *(In A1, we studied the locative case as a physical place.)* For example, «у кімнаті» *(in the room)*, «у місті» *(in the city)*, or «на столі» *(on the table)*. Now, we are expanding this concept. The locative case is not just for physical spaces on a map. Це абстрактний простір. *(It is an abstract space.)* We also use it for abstract domains, fields of activity, and general life contexts.

Let's compare two ideas to see the difference clearly. If you say «Я працюю в університеті» *(I work at the university)*, you mean the physical building. It is a concrete place. But if you say «Я працюю в освіті» *(I work in education)*, you mean the abstract field. You could be working from home, but your professional domain is education. This is a very natural and common way to talk about professions and society.

Давайте прочитаємо діалог. *(Let's read the dialogue.)* Марія та Ігор зустрілися на вулиці після довгої перерви. Вони говорять про новини. *(Maria and Ihor met on the street after a long break. They are talking about news.)*

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

<!-- EXERCISE_1 -->

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

<!-- EXERCISE_2 -->

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
- Я прочитав цю цікаву статтю по інтернету. *(I read this interesting article on the internet.)*

> — **Ігор:** Привіт, Маріє! Я дзвонив тобі вчора по телефону. *(Hi, Maria! I called you yesterday by phone.)*
> — **Марія:** Привіт! Вибач, я була на роботі. Я надіслала тобі повідомлення по імейлу. *(Hi! Sorry, I was at work. I sent you a message by email.)*
> — **Ігор:** Так, я бачив. Ти купила каву по дорозі в офіс? *(Yes, I saw it. Did you buy coffee on the way to the office?)*
> — **Марія:** Ні, я пила каву вдома, коли дивилася новини по телевізору. *(No, I drank coffee at home when I was watching the news on TV.)*

<!-- EXERCISE_3 -->

## Місцевий відмінок: від місця до сенсу

The locative case is not just for physical places. It also maps abstract spaces, time periods, and communication channels.

**Читаємо українською (Reading in Ukrainian):**
- Спочатку ми вивчали конкретні місця: у парку, на вулиці, в Україні. *(First we studied concrete places: in the park, on the street, in Ukraine.)*
- Тепер ми знаємо час: у січні, у минулому місяці, на цьому тижні. *(Now we know time: in January, last month, this week.)*
- Ми також говоримо про абстрактні сфери життя: у новій роботі, в освіті, у політиці. *(We also talk about abstract spheres of life: in a new job, in education, in politics.)*
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
- На цьому тижні у мене немає проблем у роботі. *(This week I have no problems at work.)*
- Мій старший брат зараз працює у політиці. *(My older brother works in politics now.)*
- У минулому місяці я був на цікавій зустрічі. *(Last month I was at an interesting meeting.)*
- У дитинстві ми часто читали про подорожі. *(In childhood we often read about journeys.)*

> — **Студент:** На цьому тижні у мене три заняття. *(This week I have three classes.)*
> — **Викладач:** Що ви зараз вивчаєте? *(What are you studying right now?)*
> — **Студент:** У вільний час я читаю про Україну. *(In my free time I read about Ukraine.)*
> — **Викладач:** Де ви це читаєте? *(Where do you read this?)*
> — **Студент:** У підручнику з історії. *(In a history textbook.)*
> — **Викладач:** Це дуже цікаво. В дитинстві я теж багато читав. *(This is very interesting. In childhood I also read a lot.)*

<!-- EXERCISE_4 -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: locative-expanded
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

**Level: A2 (Module 20/60) — ELEMENTARY**

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
