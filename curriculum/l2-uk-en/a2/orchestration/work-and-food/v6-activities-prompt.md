<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/work-and-food.yaml` file for module **30: Професії та кулінарія** (a2).

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

- `<!-- INJECT_ACTIVITY: match-professions -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-a-recipe-description-for-varenyky-with-correct-instrumental-forms-for-tools-and-ingredients -->`
- `<!-- INJECT_ACTIVITY: quiz-identify-which-instrumental-function-tool-companion-profession-spatial-transport-is-used-in-each-sentence -->`
- `<!-- INJECT_ACTIVITY: true-false-judge-whether-sentences-about-a-workday-use-correct-instrumental-forms-for-transport-and-prepositions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete a recipe description with correct Instrumental forms for tools and
    ingredients
  items: 8
  type: fill-in
- focus: Match profession questions to appropriate Instrumental answers
  items: 8
  type: match-up
- focus: Identify which Instrumental function (tool, companion, profession, spatial)
    is used in each sentence
  items: 8
  type: quiz
- focus: Judge whether sentences about a workday use correct Instrumental forms
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- рецепт (recipe)
- інгредієнт (ingredient)
- нарада (meeting)
- колега (colleague)
- начальник (boss)
required:
- готувати (to cook, to prepare)
- різати (to cut)
- мішати (to stir, to mix)
- посипати (to sprinkle)
- подавати (to serve)
- вареники (varenyky, dumplings)
- картопля (potato)
- помідор (tomato)
- огірок (cucumber)
- сіль (salt)
- олія (oil)
- виделка (fork)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Розмова про професії (Talking About Professions)

Imagine you meet someone new at a party or a networking event. After the basic introductions, the conversation naturally shifts to work and hobbies. In Ukrainian, asking about someone's profession is different from simply asking who they are. While you can ask «Хто ти?» (Who are you?), a more natural way to ask about someone's career is «Хто ти за фахом?» (What is your profession?) or «Ким ти працюєш?» (Who do you work as?). Discussing what you do for a living and what you are passionate about is a great way to find common interests with new friends.

In English, you say "I work as a teacher". In Ukrainian, you do not use the word "as". Instead, the verb **працювати** (to work) always requires the noun to be in the Instrumental case. This answers the question **ким?** (by whom?). For most masculine professions ending in a consonant, you add the ending **-ом** or **-ем**. For feminine professions, which often end in the suffix **-ка**, you use the ending **-кою**.

Мій брат працює програмістом у великій компанії. Моя сестра працює журналісткою, а мама працює лікаркою. Я зараз вчуся в університеті, але потім хочу працювати дизайнером. Мої друзі працюють будівельниками.

> *My brother works as a programmer in a large company. My sister works as a journalist, and my mom works as a doctor. I am currently studying at the university, but later I want to work as a designer. My friends work as builders.*

:::info
**Grammar box**
Remember the endings for the Instrumental case:
- Hard consonants take **-ом** (наприклад: програмістом, дизайнером).
- Soft consonants and «р» take **-ем** (наприклад: лікарем, кухарем, водієм).
- Feminine nouns ending in **-а** take **-ою** (наприклад: вчителькою, лікаркою).
:::

The Instrumental case is also used when discussing your hobbies and passions. The verbs **захоплюватися** (to be passionate about) and **цікавитися** (to be interested in) require the noun to be in the Instrumental case. It answers the question **чим?** (with what?). You also use this case to talk about childhood dreams with the phrase «мріяти стати» (to dream of becoming).

У вільний час я захоплююся фотографією та цікавлюся мистецтвом. Мій друг цікавиться спортом і любить грати в теніс. У дитинстві я мріяв стати пілотом, але зараз працюю інженером.

> *In my free time, I am passionate about photography and interested in art. My friend is interested in sports and likes to play tennis. In childhood, I dreamed of becoming a pilot, but now I work as an engineer.*

:::note
**Quick tip**
The question words for the Instrumental case are **ким?** for people and professions, and **чим?** for objects and interests.
:::

Let's look at a conversation between Олексій, a chef, and Марина, a teacher, who meet at a party and discuss their work and hobbies.

> — **Олексій:** Привіт! Мене звати Олексій. А тебе як звати? *(Hi! My name is Oleksii. And what is your name?)*
> — **Марина:** Привіт! Я Марина. Дуже приємно познайомитися. *(Hi! I am Maryna. Nice to meet you.)*
> — **Олексій:** Мені також. Ким ти працюєш? *(Me too. Who do you work as?)*
> — **Марина:** Я працюю вчителькою в школі. Я викладаю історію. Мені дуже подобається бути вчителькою, бо я люблю працювати з дітьми. А хто ти за фахом? *(I work as a teacher at a school. I teach history. I really like being a teacher because I love working with children. And what is your profession?)*
> — **Олексій:** Я кухар. Я працюю кухарем у ресторані. Це важка робота, але цікава. *(I am a cook. I work as a cook in a restaurant. It is hard work, but interesting.)*
> — **Марина:** О, це чудово! Я люблю смачно поїсти. Ким ти мріяв стати в дитинстві? *(Oh, that's great! I love to eat deliciously. Who did you dream of becoming in childhood?)*
> — **Олексій:** У дитинстві я мріяв стати лікарем, але зараз я цікавлюся кулінарією. А чим ти захоплюєшся у вільний час? *(In childhood I dreamed of becoming a doctor, but now I am interested in cooking. And what are you passionate about in your free time?)*
> — **Марина:** Я захоплююся фотографією і дуже цікавлюся подорожами. *(I am passionate about photography and very interested in travel.)*
> — **Олексій:** Це збіг! Я також цікавлюся подорожами. Ми можемо поговорити про це. *(What a coincidence! I am also interested in travel. We can talk about this.)*

When talking about professions, it is important to use authentic Ukrainian vocabulary. Some learners mistakenly use Russian words that sound familiar, which leads to speaking Surzhyk. For example, the Ukrainian word for a cook is **кухар**, not the Russian *повар*. A hairdresser is **перукар**, not *парикмахер*. Similarly, a cleaner is **прибиральниця**, not *уборщиця*. Using the correct terms shows respect for the language and helps you sound natural.

Here is a quick reference table of common A2 professions and their Instrumental forms:

| Називний (Nominative) | Орудний (Instrumental) |
| :--- | :--- |
| продавець | продавцем |
| будівельник | будівельником |
| кухар | кухарем |
| перукар | перукарем |
| дизайнер | дизайнером |
| журналістка | журналісткою |

<!-- INJECT_ACTIVITY: match-professions -->

## На кухні: Готуємо разом (In the Kitchen: Cooking Together)

Сьогодні ми готуємо традиційну українську вечерю. У нашому святковому меню будуть гарячі вареники з картоплею та свіжий салат з помідорами. Робота на кухні вимагає знання граматики, адже ми постійно використовуємо орудний відмінок. Він потрібен нам для двох важливих речей. По-перше, ми називаємо інструмент, яким ми готуємо їжу. По-друге, ми описуємо інгредієнти нашої страви.

> *Today we are preparing a traditional Ukrainian dinner. In our festive menu there will be hot varenyky with potato and a fresh salad with tomatoes. Work in the kitchen requires knowledge of grammar, because we constantly use the Instrumental case. We need it for two important things. First, we name the tool with which we cook food. Second, we describe the ingredients of our dish.*

When we use an object to perform an action, the Instrumental case acts as the "instrument" or "tool". This function does not require any prepositions. You simply put the noun representing the tool into the Instrumental case to answer the question **чим?** (with what?).

Наприклад, ми можемо обережно різати хліб чи м'ясо гострим ножем. Ми їмо салат виделкою, а мішаємо гарячий суп великою ложкою. Також ми обов'язково посипаємо готову страву сіллю.

> *For example, we can carefully cut bread or meat with a sharp knife. We eat salad with a fork, and we stir hot soup with a large spoon. Also, we necessarily sprinkle the finished dish with salt.*

:::info
**Grammar box: Tool vs. Location**
Tools take the Instrumental without a preposition, but cooking *surfaces* or *locations* take the Locative case with **на** or **в**. We say **смажити на сковорідці** (to fry on a pan), not ~~смажити сковорідкою~~.
:::

The second major use of the Instrumental case in the kitchen is describing ingredients and side dishes. When a dish is made *with* something, we use the preposition **з** (or **зі** before double consonants to make pronunciation easier) followed by the Instrumental case. This answers the question **з чим?** (with what?).

Українці дуже люблять пити гарячий чай з лимоном і медом. На обід ми часто їмо червоний борщ зі сметаною та свіжим хлібом. А на десерт можна приготувати солодкі вареники з вишнями.

> *Ukrainians really love drinking hot tea with lemon and honey. For lunch we often eat red borscht with sour cream and fresh bread. And for dessert one can prepare sweet varenyky with cherries.*

Let's see how these rules come together when Іван and Олена follow a recipe. Notice how they use imperative verb forms like **поріжте**, **додайте**, and **змішайте** alongside Instrumental tools and ingredients.

> — **Іван:** Що ми будемо готувати спочатку? *(What will we cook first?)*
> — **Олена:** Спочатку ми робимо салат. Поріжте помідори, огірки та перець. *(First we are making a salad. Cut the tomatoes, cucumbers, and pepper.)*
> — **Іван:** Чим мені різати цибулю? *(With what should I cut the onion?)*
> — **Олена:** Ріж цибулю цим ножем. Потім додай її в салат і змішай усе ложкою. *(Cut the onion with this knife. Then add it to the salad and mix everything with a spoon.)*
> — **Іван:** Готово. А з чим ми подаємо вареники? *(Done. And with what are we serving the varenyky?)*
> — **Олена:** Подаємо їх зі шкварками та сметаною. *(We are serving them with cracklings and sour cream.)*

When talking about food, it is important to use authentic Ukrainian vocabulary and avoid Russian calques.

Українська мова має чіткі назви для популярних продуктів. Наприклад, соняшникова рідина — це «олія», а твердий продукт із молока — це «масло». Також ми називаємо словом «сир» і твердий сир, і домашній кисломолочний продукт. Пам'ятайте, що м'ясо ми «смажимо», а не «жаримо».

> *The Ukrainian language has clear names for popular products. For example, sunflower liquid is "oil" (олія), and the solid product from milk is "butter" (масло). Also, we call both hard cheese and homemade cottage cheese product with the word "cheese" (сир). Remember that we "fry" (смажимо) meat, not "жаримо" (Russian calque).*

:::note
**Quick tip: Олія vs Масло**
Use **олія** for liquid plant-based oils and **масло** ONLY for dairy butter. The Russian word *творог* does not exist in Ukrainian; use **сир** or **домашній сир** for cottage cheese.
:::

<!-- INJECT_ACTIVITY: fill-in-complete-a-recipe-description-for-varenyky-with-correct-instrumental-forms-for-tools-and-ingredients -->

## Мій робочий день (My Workday)

We have discussed how to talk about our professions and how to use tools in the kitchen. Now, let us connect these ideas to describe a full workday. When we talk about our daily routine, we often describe how we travel, who we spend time with, and where things are located in our workspace. The Instrumental case helps us express all these details smoothly. It allows us to move from simply stating who we are to describing how we navigate through the day, especially when expressing the concept of traveling "by means of" a specific vehicle.

To say how you travel, use the Instrumental case without any prepositions. This expresses the idea of moving by means of a vehicle. For example, you can travel by bus, by car, or by tram. We also use the Instrumental case after specific spatial prepositions to describe locations around the office. These prepositions include words for in front of, behind, between, above, and under.

Я щодня їду на роботу автобусом або машиною. Мій брат їде велосипедом, а сестра завжди їде метро. Я паркуюся перед офісом або за будинком. Мій стіл стоїть між вікном і дверима. Годинник висить над столом, а мій рюкзак лежить під столом.

> *I go to work every day by bus or by car. My brother goes by bicycle, and my sister always goes by subway. I park in front of the office or behind the building. My desk stands between the window and the door. The clock hangs above the desk, and my backpack lies under the desk.*

:::note
**Quick tip: Transport**
Remember that **метро** is a foreign loanword and never changes its ending in Ukrainian. We say **їхати автобусом**, but **їхати метро**.
:::

Let us see how all these Instrumental functions work together in a real-life scenario. In this short vlog monologue, a project manager describes a typical morning and afternoon at the office. Pay attention to how transport, tools, companionship, and spatial locations are all expressed using the same grammatical case.

Вранці я їду на роботу трамваєм. Перед роботою я завжди купую каву з молоком. В офісі я багато працюю за комп'ютером. О першій годині я обідаю з колегами. Після обіду я маю важливу нараду з директором. Мій кабінет розташований над кав'ярнею, тому там завжди гарно пахне.

> *In the morning, I go to work by tram. Before work, I always buy coffee with milk. In the office, I work a lot at the computer. At one o'clock, I have lunch with colleagues. After lunch, I have an important meeting with the director. My office is located above the coffee shop, so it always smells nice there.*

When you add adjectives and possessive pronouns to these descriptions, they must also change to match the noun in the Instrumental case. For masculine and neuter words, adjectives take the ending **-им**. For feminine words, they take the ending **-ою**. Plural adjectives take the ending **-ими**. 

Сьогодні я працюю з моїм новим колегою. Ми сидимо за великим круглим столом. Ввечері я їду додому і відпочиваю з цікавою книжкою. У вихідні ми часто гуляємо з нашими старими друзями.

> *Today I am working with my new colleague. We sit at a large round table. In the evening I go home and relax with an interesting book. On weekends we often walk with our old friends.*

:::info
**Grammar box: Instrumental Adjectives**
Here is a quick reference for adjectives and possessive pronouns in the Instrumental case:
*   **Masculine & Neuter:** ending **-им** (з новим проєктом).
*   **Feminine:** ending **-ою** or **-єю** (з цікавою людиною).
*   **Plural:** ending **-ими** (з хорошими колегами).
:::

<!-- INJECT_ACTIVITY: quiz-identify-which-instrumental-function-tool-companion-profession-spatial-transport-is-used-in-each-sentence -->
<!-- INJECT_ACTIVITY: true-false-judge-whether-sentences-about-a-workday-use-correct-instrumental-forms-for-transport-and-prepositions -->

## Підсумок — Практика: Розкажи про себе

In this final practice, your task is to write a comprehensive profile about yourself. You need to write eight to ten sentences describing your daily life, your job, your hobbies, and your favorite food. Use the Instrumental case to connect these ideas naturally and show your ability to hold a complex conversation.

Тепер твоя черга розповісти про себе. Напиши вісім або десять речень про своє життя. Розкажи, ким ти працюєш. Напиши, чим ти цікавишся. Опиши свій звичайний робочий день. Напиши, чим ти їдеш на роботу. Розкажи також, з ким ти обідаєш. Не забудь розповісти про свою улюблену їжу. Використовуй орудний відмінок для цікавої розповіді.

> *Now it is your turn to tell about yourself. Write eight or ten sentences about your life. Tell what you work as. Write what you are interested in. Describe your usual workday. Write what you travel to work by. Tell also who you have lunch with. Do not forget to tell about your favorite food. Use the Instrumental case for an interesting story.*

When writing your profile, build your sentences around these core phrases: **Я працюю...**, **Я цікавлюся...**, **Я люблю...**, and **Я їду... перед...**. Pay close attention to the gender of the nouns you use. Remember that masculine and neuter nouns usually take the **-ом** or **-ем** endings, while feminine nouns take the **-ою** or **-ею** endings. Check your adjective endings as well to ensure perfect agreement.

Уяви, що ти знайомишся з новою людиною на вечірці. Це чудова нагода попрактикувати нові конструкції в реальній розмові. Використовуй короткі реакції, щоб підтримати бесіду.

> — **Олена:** Привіт! Ми ще не знайомі. Ким ти працюєш? *(Hi! We haven't met yet. What do you work as?)*
> — **Марк:** Привіт! Я працюю архітектором. А ти? *(Hi! I work as an architect. And you?)*
> — **Олена:** Я працюю вчителькою. А чим ти захоплюєшся у вільний час? *(I work as a teacher. And what are you passionate about in your free time?)*
> — **Марк:** Я захоплююся фотографією. Також я люблю готувати. *(I am passionate about photography. Also, I love to cook.)*
> — **Олена:** Справді? Я теж! Яку їжу ти найбільше любиш готувати? *(Really? Me too! What food do you like to cook the most?)*
> — **Марк:** Я часто готую борщ з яловичиною або вареники з картоплею. А ти? *(I often cook borscht with beef or varenyky with potatoes. And you?)*
> — **Олена:** Цікаво! А я обожнюю пекти торти з масляним кремом. *(Interesting! And I adore baking cakes with buttercream.)*

The Instrumental case is one of the most versatile and powerful tools in Ukrainian. You have seen how it connects actions to the tools we use, the people we spend time with, our professions, and even where things are located in space. It is the key to speaking fluently about your daily routines and personal interests.

Ось короткий список для самоперевірки. Прочитай ці питання і перевір свої знання.
* Чи можу я назвати свою професію та ще п'ять інших?
* Чи можу я описати три інгредієнти у страві за допомогою прийменника «з»?
* Чи можу я назвати три інструменти на кухні, наприклад, ножем або ложкою?
* Чи можу я пояснити розташування офісу словами «між» або «за»?
* Чи я пам'ятаю, що не можна казати «повар» і «жарити»?

> *Here is a short checklist for self-assessment. Read these questions and check your knowledge.*
> - *Can I name my profession and five others?*
> - *Can I describe three ingredients in a dish using the preposition "з" (with)?*
> - *Can I name three tools in the kitchen, for example, with a knife or with a spoon?*
> - *Can I explain the location of the office with the words "між" (between) or "за" (behind)?*
> - *Do I remember that one must not say "повар" (cook) and "жарити" (to fry)?*

:::info
**Grammar box: Instrumental Summary**
Use the Instrumental case to answer the questions "By whom?" or "With what?". It is essential for describing professions, tools, accompaniment, spatial locations, and transport. Always verify that you are using authentic Ukrainian vocabulary like **кухар** and **смажити**, avoiding Russian calques.
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: work-and-food
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

**Level: A2 (Module 30/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
