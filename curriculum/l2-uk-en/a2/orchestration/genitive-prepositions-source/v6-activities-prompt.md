<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-source.yaml` file for module **9: Звідки ти? З чого це зроблено?** (a2).

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

- focus: Choose the correct variant з/із/зі based on the following word
  items: 8
  type: quiz
- focus: Complete sentences with від or з + correct Genitive noun form
  items: 8
  type: fill-in
- focus: Match preposition phrases to their English meanings (origin, material, time)
  items: 8
  type: match-up
- focus: Sort phrases into з (place/material) vs. від (person/protection) vs. після
    (time)
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
- дитинство (childhood)
- шовк (silk)
- парасолька (umbrella)
- сусід (neighbor)
required:
- прийменник (preposition)
- джерело (source)
- походження (origin)
- матеріал (material)
- далеко (far)
- недалеко (not far, nearby)
- подарунок (gift)
- сніданок (breakfast)
- вечеря (dinner, supper)
- канікули (vacation, holidays)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Звідки? З/із/зі + родовий (Where From? З/із/зі + Genitive)

> — **Марко:** Привіт усім! *(Hello everyone!)* Ласкаво просимо на нашу інтернаціональну **вечерю** *(dinner)*!
> — **Анна:** Дякую! *(Thank you!)* Я дуже голодна. *(I am very hungry.)* Що ми маємо сьогодні на вечерю?
> — **Марко:** Подивися на цей великий стіл. *(Look at this big table.)* Це **сир** *(cheese)* із Франції. *(This is cheese from France.)*
> — **Олена:** А це червоне вино з Італії. *(And this is red wine from Italy.)* Мій **сусід** *(neighbor)* працює там. *(My neighbor works there.)*
> — **Джон:** Я маю смачний **шоколад** *(chocolate)* зі Швейцарії. *(I have delicious chocolate from Switzerland.)* Це **подарунок** *(gift)* від моєї мами. *(This is a gift from my mom.)*
> — **Анна:** А це свіжі **оливки** *(olives)* з Греції? *(And are these fresh olives from Greece?)*
> — **Марко:** Так, саме так. *(Yes, exactly.)* Ми маємо смачну їжу з усього світу! *(We have delicious food from all over the world!)*

We use the **прийменник** *(preposition)* **з** (from) to talk about origin. When we bring food to a party, we want to know its **походження** *(origin)*. To say where something or someone is from, we use **з** + the Genitive case. This tells us the starting point of a person or an object.

The primary meaning of **з** is "from" a place, a surface, or a container. We use it with cities, countries, universities, and other locations. When you move away from a place, the noun changes to the Genitive case. This shows the direction of your movement.

«Читаємо українською»
Мій новий студент приїхав з Києва.
Вона повернулася з університету дуже пізно.
Мій брат зараз їде з вокзалу додому.
Туристи з України дуже люблять цю країну.

Notice how the ending of the noun changes to show the Genitive case. The word Київ becomes Києва, and університет becomes університету. We always use this case after the прийменник **з** when we talk about movement from a location.

«Читаємо українською»
Я щойно прийшла з роботи додому.
Вони повернулися з великого театру.
Діти радісно вийшли зі школи.
Я взяла нову книгу зі стола.

If you are inside a building or a place and you leave it, you are moving "from" it. This is a very common way to describe your daily movements in Ukrainian.

The Ukrainian language loves euphony, which we call **милозвучність** *(euphony, pleasantness of sound)*. To make speaking easier and more melodic, the прийменник **з** has three forms: **з**, **із**, and **зі**. You choose the variant based on the letters that surround it. There is no difference in meaning.

We use **з** before vowels and before single consonants. This is the most common form you will see and hear.

«Читаємо українською»
Моя найкраща подруга приїхала з Одеси.
Ми щойно повернулися з університету.
Я взяла цей зошит з полиці.
Вони приїхали з Києва вчора ввечері.

We use **із** between two consonants (if the previous word ends in a consonant) or before words that start with sibilants like с, з, ц, ш, ж, ч. This helps avoid a heavy block of consonant sounds.

«Читаємо українською»
Я отримав цей довгий лист із Бразилії.
Цей новий автобус їде із Запоріжжя.
Моя бабуся приїхала із села сьогодні.
Ми принесли ці смачні яблука із саду.

We use **зі** before consonant clusters that start with letters like з, с, ш, щ, and sometimes others. This adds a vowel to make pronunciation smooth.

«Читаємо українською»
Минулого тижня ми повернулися зі Львова.
Діти дуже швидко вийшли зі школи.
Кіт несподівано стрибнув зі стола на підлогу.
Він повернувся зі столиці тільки вчора.

Beyond locations, we use **з** + Genitive to describe **матеріал** *(material)*. If you want to say what an object is made of, you use this construction instead of an adjective. It is a very natural way to describe everyday objects.

«Читаємо українською»
Ця красива **сукня** *(dress)* з **шовку** *(silk)*.
Моя мама носить **обручку** *(ring)* із **золота** *(gold)*.
Ми купили великий стіл з дерева.
Цей теплий светр з вовни.

We also use this structure to talk about the contents of a container or what a product is made from. It tells us what is inside a glass or what fruit is in a drink.

«Читаємо українською»
Я п'ю свіжий **сік** *(juice)* з **яблук** *(apples)*.
На столі стоїть **склянка** *(glass)* з молока.
Він приніс велику коробку з цукерок.
Діти люблять пити сік з апельсинів.

Finally, the preposition **з** is used to indicate a starting point in time. It translates to "since" or "from" a specific moment. This is essential for talking about when an action began.

«Читаємо українською»
Я працюю тут з **понеділка** *(Monday)*.
Він читає цю цікаву книгу з **ранку** *(morning)*.
Ми знаємо один одного з **дитинства** *(childhood)*.
Вона чекає на тебе з п'ятої години.

Notice that the time words also take the Genitive case. For instance, ранок becomes ранку, понеділок becomes понеділка, and дитинство becomes дитинства. You will use this often to describe your daily schedule or long-term habits.

«Читаємо українською»
Я вчу українську мову з жовтня.
Він не спить з шостої години ранку.
Ми живемо в цьому великому місті з весни.
Моя сестра грає на піаніно з дитинства.

Using **з** + Genitive for time gives your stories more detail. It shows exactly when a situation started.

<!-- INJECT_ACTIVITY: quiz, choose з/із/зі based on the following word -->


## Від кого? Від + родовий (From Whom? Від + Genitive)

Коли ми отримуємо щось від іншої людини, ми використовуємо прийменник **від**. *(When we receive something from another person, we use the preposition 'від'.)* 

The preposition **від** *(from)* is essential when talking about the source of an object, a message, or information, specifically when that source is a person or an entity (like a company or an organization). Just like **з**, the preposition **від** always requires the following noun to be in the Genitive case. It answers the question **від кого?** *(from whom?)* or **від чого?** *(from what?)*. You will use this to talk about receiving gifts, messages, or news. When writing emails or formal letters, you will also see **від** used to indicate the sender. The entire concept revolves around transfer: something is moving from a person to you.

«Читаємо українською»
Я отримав довгий **лист** *(letter)* від **мами** *(mom)*.
Цей красивий **подарунок** *(gift)* від мого найкращого **друга** *(friend)*.
Ми щойно почули цікаві **новини** *(news)* від нашого **сусіда** *(neighbor)*.
Цей важливий документ від директора компанії.
Я маю нове повідомлення від сестри на телефоні.
Чи ти маєш якісь новини від старшого брата?
Сьогодні вранці прийшла посилка від дідуся.

> — **Олена:** Від кого ці красиві квіти? *(From whom are these beautiful flowers?)*
> — **Марк:** Це подарунок від мого колеги. *(This is a gift from my colleague.)*
> — **Олена:** А ця нова книга також від нього? *(And is this new book also from him?)*
> — **Марк:** Ні, ця книга від моєї сестри. *(No, this book is from my sister.)*

It is very important to understand the difference between **з** and **від**. Both translate to "from" in English, but they have completely different functions in Ukrainian. We use **з** (or із/зі) when we talk about geographical origin, a physical place you left, or the material an object is made of. We use **від** when a person or a specific sender gives us something. Do not confuse **від** *(from)* with the preposition **з** *(with)* when followed by the Instrumental case. If you say «з братом» (Instrumental), you are doing something together. If you say «від брата» (Genitive), you are receiving something.

:::tip Як запам'ятати (How to remember)
- Звідки? З Києва, з роботи, зі школи. *(Where from? From Kyiv, from work, from school. — Origin/Location)*
- Від кого? Від Олега, від лікаря, від мами. *(From whom? From Oleh, from the doctor, from mom. — Person/Sender)*
- З ким? З Олегом, з лікарем, з мамою. *(With whom? With Oleh, with the doctor, with mom. — Instrumental case!)*
:::

«Читаємо українською»
Мій друг приїхав з Лондона вчора ввечері. *(My friend arrived from London yesterday evening.)*
Я отримав цей цікавий сувенір від друга. *(I received this interesting souvenir from a friend.)*
Вона повернулася з магазину дуже пізно. *(She returned from the store very late.)*
Ці гроші від моїх батьків на новий комп'ютер. *(This money is from my parents for a new computer.)*
Ми чекаємо на офіційну відповідь від менеджера. *(We are waiting for an official answer from the manager.)*
Він іде в кіно з дівчиною, а квитки він отримав від брата. *(He is going to the cinema with his girlfriend, and he received the tickets from his brother.)*

Де це знаходиться? *(Where is this located?)* Another very common use of **від** + Genitive is to express distance or proximity. When you want to say that something is far from or not far from a specific point, you use the adverbs **далеко** *(far)* or **недалеко** *(not far, nearby)* followed by **від**. This is extremely useful for asking for directions, describing where you live, or explaining how long a trip will take. You can also use this structure to give instructions to a taxi driver or explain where you parked your car. The reference point is always in the Genitive case.

«Читаємо українською»
Наш новий будинок знаходиться далеко від **центру** *(center)* міста.
Мій університет розташований недалеко від головного **вокзалу** *(train station)*.
Я живу дуже далеко від **дому** *(home)* моїх батьків.
Цей великий супермаркет знаходиться недалеко від нашої школи.
Чи твоя нова робота далеко від станції метро?
Наш готель знаходиться недалеко від міжнародного аеропорту.
Цей гарний парк розташований недалеко від річки.

> — **Анна:** Твій офіс знаходиться далеко від центру міста? *(Is your office located far from the city center?)*
> — **Павло:** Ні, він недалеко від станції метро. *(No, it is not far from the subway station.)*
> — **Анна:** А далеко від твого дому до офісу? *(And is it far from your home to the office?)*
> — **Павло:** Так, дуже далеко. Я їду туди цілу годину. *(Yes, very far. I travel there for a whole hour.)*

Для чого це? *(What is this for?)* Finally, the preposition **від** + Genitive is used to express protection or remedy. When we use something to stop, cure, or protect against a negative thing (like an illness, bad weather, or pests), we use **від**. In English, you might say "medicine *for* a headache" or "protection *against* mosquitoes", but in Ukrainian, you use **від** *(from)*. You are literally saying "medicine *from* a headache". You will see this construction often in a pharmacy or a supermarket. If you need to buy something to solve a physical problem, you will ask the pharmacist for something **від** that problem.

:::note Корисні фрази (Useful phrases)
- **ліки від...** *(medicine for...)*
- **захист від...** *(protection from...)*
- **засіб від...** *(remedy/repellent against...)*
- **крем від...** *(cream against/for...)*
:::

«Читаємо українською»
Я маю хороші ліки від сильного **головного болю** *(headache)*.
Не забудь взяти велику **парасольку** *(umbrella)* від осіннього дощу.
У мене є новий ефективний засіб від **комарів** *(mosquitoes)*.
Ми купили теплий зимовий одяг від сильного холоду.
Цей новий крем дуже добре захищає від сонця на пляжі.
Які таблетки ти зазвичай приймаєш від болю в горлі?
Ми купили спеціальний засіб від плям на одязі.

<!-- INJECT_ACTIVITY: fill-in, complete sentences with від or з + correct Genitive noun form, 8 items -->


## Що було потім? Після + родовий (What Happened Next? Після + Genitive)

In Ukrainian, when we want to talk about what happens after a specific event, a certain time, or a defined period, we use the preposition **після** *(after)*. This preposition is incredibly common and is always followed by the Genitive case. Whether you are talking about what you do after work, after a class, after a morning meal, or after a long vacation, **після** is the exact word you need to sequence your actions chronologically. It establishes a clear timeline, indicating that one action follows the completion of another.

«Читаємо українською»
Я маю вільний час тільки після **уроку** *(lesson)*.
Ми йдемо в новий ресторан після **обіду** *(lunch)*.
Вони завжди відпочивають у парку після **роботи** *(work)*.
Що ти будеш робити сьогодні після **зустрічі** *(meeting)*?
Після ранкового **сніданку** *(breakfast)* я п'ю чорну каву.
Мій старший брат читає новини після пізньої **вечері** *(dinner)*.
Молоді батьки мають час для себе тільки після сну дітей.

> — **Олег:** Що ти робиш сьогодні після роботи? *(What are you doing today after work?)*
> — **Марія:** Після роботи я йду в басейн. А ти? *(After work I am going to the pool. And you?)*
> — **Олег:** А я після роботи їду додому. *(And after work I am going home.)*
> — **Марія:** Що ти зазвичай робиш удома після роботи? *(What do you usually do at home after work?)*
> — **Олег:** Після роботи я готую вечерю і читаю книгу. *(After work I cook dinner and read a book.)*

Let's review how to form the Genitive case after **після** for different types of nouns. The rules are the same as you learned previously. For masculine nouns ending in a hard consonant, we typically add **-у** or **-а**, such as **екзамен** *(exam)* becoming після **екзамену**. Soft masculine nouns often take the ending **-я**, like the word **день** *(day)* changing to після **дня**. Neuter nouns change their final **-о** to **-а**, as in **свято** *(holiday)* becoming після **свята**. For feminine nouns ending in **-ія**, the ending changes to **-ії**, for example, **лекція** *(lecture)* becomes після **лекції**. Remember that some words are always plural, like **канікули** *(vacation)*, which drops the vowel and becomes **канікул** in the Genitive plural.

:::note Зміни закінчень (Ending changes)
- **екзамен** *(exam)* → після **екзамену**
- **день** *(day)* → після **дня**
- **свято** *(holiday)* → після **свята**
- **лекція** *(lecture)* → після **лекції**
- **канікули** *(vacation)* → після **канікул**
:::

«Читаємо українською»
Студенти йдуть додому після складного екзамену.
Після довгого робочого дня я дуже хочу спати.
Ми довго прибираємо в кімнаті після веселого свята.
Молодий викладач п'є холодну воду після довгої лекції.
Діти не хочуть іти до школи після літніх канікул.
Що ваші студенти зазвичай роблять після екзамену?

Using the preposition **після** is the most natural way to describe your daily routine in Ukrainian. By chaining actions together with this preposition, you can create a smooth, connected narrative of your entire day. You can easily link your daily meals, your work or study schedule, and your evening free time activities. This structure makes your conversational speech sound much more fluent and native-like than simply listing independent actions one after another.

«Читаємо українською»
Я прокидаюся дуже рано, коли сонце тільки встає.
Після швидкого сніданку я йду в великий **спортзал** *(gym)*.
Після **залу** *(gym)* я приймаю душ і їду в офіс.
Я багато працюю, але після обіду я завжди маю перерву.
Після роботи я йду в супермаркет і купую свіжі продукти.
Вдома після роботи я готую дуже смачну вечерю для сім'ї.
Після вечері я дивлюся новий фільм або читаю книгу.

> — **Анна:** Який твій звичайний розклад на день? *(What is your usual schedule for the day?)*
> — **Віктор:** Після сніданку я п'ю каву і читаю новини. *(After breakfast I drink coffee and read news.)*
> — **Анна:** А що ти робиш після обіду? *(And what do you do after lunch?)*
> — **Віктор:** Після обіду я маю важливі зустрічі з клієнтами. *(After lunch I have important meetings with clients.)*
> — **Анна:** Ти втомився після цих довгих зустрічей? *(Are you tired after these long meetings?)*
> — **Віктор:** Так, тому після роботи я тільки відпочиваю. *(Yes, that is why after work I only rest.)*

To fully master the concept of time sequence in Ukrainian, it is incredibly helpful to contrast **після** *(after)* with its direct opposite, the preposition **до** *(before, until)*. Fortunately, both of these prepositions require the exact same grammatical case: the Genitive case. Using them together in your sentences allows you to be very precise about when something happens. **До** clearly indicates the time leading up to an event, while **після** indicates the time following the successful completion of that same event.

:::tip Антоніми часу (Time antonyms)
- **до** уроку *(before the lesson)* ↔ **після** уроку *(after the lesson)*
- **до** роботи *(before work)* ↔ **після** роботи *(after work)*
- **до** обіду *(before lunch)* ↔ **після** обіду *(after lunch)*
:::

«Читаємо українською»
Я п'ю воду до сніданку, а каву — після сніданку.
Студенти читають текст до уроку, а пишуть тест після уроку.
Ми гуляємо в парку до роботи, а відпочиваємо вдома після роботи.
До теплого обіду я інтенсивно працюю за комп'ютером.
Після смачного обіду я маю зустріч з клієнтом.
До довгих канікул діти дуже багато вчаться в школі.
Після веселих канікул вони мають енергію для навчання.
Я завжди мию руки до обіду і після обіду.

<!-- INJECT_ACTIVITY: match-up, match preposition phrases to their English meanings (origin, material, time) -->
<!-- INJECT_ACTIVITY: group-sort, sort phrases into з (place/material) vs. від (person/protection) vs. після (time) -->


## Підсумок — Summary

You have learned how to use the prepositions **з** *(from/made of/since)*, **від** *(from a person)*, and **після** *(after)*. All of these prepositions require the Genitive case to function correctly. You also know how to choose the correct phonetic variant (**з**, **із**, or **зі**) to make your spoken Ukrainian sound natural and melodic. 

Давайте перевіримо ваші знання! *(Let's check your knowledge!)* Answer these self-check questions to review what we have covered in this module:

- Коли ми використовуємо **зі** замість **з**? *(When do we use 'зі' instead of 'з'?)* 
  — Перед збігом приголосних, як у слові «зі школи». *(Before a cluster of consonants, like in the phrase "from school".)*
  
- Який прийменник ми вживаємо, щоб сказати, від кого отримали подарунок? *(Which preposition do we use to say who we received a gift from?)*
  — Прийменник **від**. Наприклад: подарунок від друга. *(The preposition 'від'. For example: a gift from a friend.)*
  
- Який відмінок ми використовуємо після прийменників **після**, **від** та **з**? *(Which case do we use after the prepositions 'після', 'від', and 'з'?)*
  — Родовий відмінок. *(The Genitive case.)*
  
- Як сказати "after dinner" українською? *(How to say "after dinner" in Ukrainian?)*
  — Після вечері. *(After dinner.)*

If you can confidently answer these questions, you are ready to move forward. Practice using these prepositions when talking about your daily routine, your friends, and the origin of things around you!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-source
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

**Level: A2 (Module 9/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


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
