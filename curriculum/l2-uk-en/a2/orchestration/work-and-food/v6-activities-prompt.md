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
- `<!-- INJECT_ACTIVITY: recipe-fill-in -->`
- `<!-- INJECT_ACTIVITY: true-false-workday -->`
- `<!-- INJECT_ACTIVITY: review-instrumental -->`

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

Уявіть ситуацію: ви на веселій вечірці або на діловій зустрічі. Ви знайомитеся з новими цікавими людьми. Як почати приємну розмову? Спочатку ми запитуємо просту загальну інформацію. Ми кажемо: **«Хто ти?»** (Who are you?) або **«Звідки ти?»** (Where are you from?). Але коли ми хочемо знати про кар'єру, питання змінюється. Ми запитуємо: **«Хто ти за фахом?»** (What is your specialty?) або **«Ким ти працюєш?»** (What do you work as?). Розмова про професії та щоденні хобі допомагає знайти спільні інтереси. Це дуже важливий крок для кожного нового знайомства. Коли ми знаємо професію людини, ми можемо знайти багато чудових тем для розмови.

In Ukrainian grammar, the verb **«працювати»** (to work) strictly requires the Instrumental case when you talk about professions. Unlike English, where you say "I work *as a* doctor", in the Ukrainian language, you literally say "I work *by means of a doctor*". This is a core rule you must remember.

Для популярних чоловічих професій ми зазвичай додаємо закінчення **-ом** або **-ем** в орудному відмінку. Наприклад, слово **«програміст»** (programmer) стає **«програмістом»**. Слово **«лікар»** (doctor) змінюється на **«лікарем»**, а **«водій»** (driver) — на **«водієм»**. Для сучасних жіночих професій ми дуже часто використовуємо природний суфікс **-ка**. Наприклад, ми кажемо **«вчителька»** (female teacher), **«журналістка»** (female journalist), **«дизайнерка»** (female designer). Ці нові слова в орудному відмінку завжди мають закінчення **-ою**: працюю **«вчителькою»**, працюю **«журналісткою»**, працюю **«дизайнеркою»**.

The Instrumental case is also absolutely essential when you are talking about your personal hobbies, daily interests, and deep passions. We naturally use it after specific verbs.

Відоме дієслово **«захоплюватися»** (to be passionate about) завжди вимагає орудного відмінка. Наприклад, ви можете **«захоплюватися фотографією»** (to be passionate about photography). Дієслово **«цікавитися»** (to be interested in) також постійно працює з цьому відмінком. Ви можете **«цікавитися спортом»** (to be interested in sport) або активно **«цікавитися мистецтвом»** (to be interested in art). Ми також використовуємо орудний відмінок, коли говоримо про мрії дитинства. Ми запитуємо друзів: **«Ким ти мріяв стати?»** (Who did you dream of becoming?). І відповідаємо: **«Я мріяв стати пілотом»** (I dreamed of becoming a pilot) або **«Я хотіла стати акторкою»** (I wanted to become an actress).

> — **Олексій:** Привіт! Мене звати Олексій. А тебе як звати? *(Hi! My name is Oleksiy. And what is your name?)*
> — **Марина:** Привіт, Олексію! Я Марина. Дуже приємно познайомитися. Ким ти працюєш? *(Hi, Oleksiy! I am Maryna. Nice to meet you. What do you work as?)*
> — **Олексій:** Я працюю кухарем у великому ресторані. А ти хто за фахом? *(I work as a chef in a large restaurant. And what is your specialty?)*
> — **Марина:** Я працюю вчителькою в школі. Мені дуже подобається бути вчителькою. *(I work as a teacher in a school. I really like being a teacher.)*
> — **Олексій:** Це надзвичайно цікава професія! А чим ти захоплюєшся у вільний час? *(That is an extremely interesting profession! And what are you passionate about in your free time?)*
> — **Марина:** Я захоплююся сучасною музикою. А також я багато цікавлюся подорожами. *(I am passionate about modern music. And I am also very interested in traveling.)*
> — **Олексій:** О, ми цікавимося подорожами разом! Я теж дуже люблю мандрувати. *(Oh, we are interested in traveling together! I also really love to journey.)*

It is historically and culturally critical to use authentic Ukrainian terms for professions and actively avoid Russian calques. For example, a professional cook is **«кухар»** (cook), so you must never use the Russian word «повар». A skilled hairdresser is **«перукар»** (hairdresser), not the Russian «парикмахер». Using the correct terminology shows respect for the Ukrainian language.

Ось коротка таблиця популярних професій та їхніх правильних форм в орудному відмінку:
*   **«продавець»** (seller) → я працюю **«продавцем»**
*   **«будівельник»** (builder) → він працює **«будівельником»**
*   «кухар» → мій брат працює **«кухарем»**
*   «перукар» → вона працює **«перукарем»**
*   **«менеджер»** (manager) → я працюю **«менеджером»**
*   **«інженер»** (engineer) → мій тато працює **«інженером»**

Завжди звертайте пильну увагу на ці автентичні українські слова.

<!-- INJECT_ACTIVITY: match-professions -->


## На кухні: Готуємо разом (In the Kitchen: Cooking Together)

Уявіть, що ви чекаєте гостей на святкову вечерю. *(Imagine that you are expecting guests for a festive dinner.)* Ви уважно плануєте смачне меню для друзів. *(You are carefully planning a delicious menu for friends.)* Ви хочете приготувати традиційні українські **страви** (dishes). Наприклад, ви будете готувати гарячі **вареники з картоплею** (dumplings with potatoes). Для них потрібна свіжа **картопля** (potato). Також ви робите свіжий **салат з помідорами** (salad with tomatoes), для якого ідеально підійде зелений **огірок** (cucumber). The Instrumental case is absolutely essential in the kitchen. We use it for two main reasons when we talk about the cooking process. First, we use it to talk about the physical tools we hold in our hands. Second, we use it to describe the tasty ingredients that go into a dish. Сьогодні ми будемо **готувати** (to cook) разом і вивчати ці корисні правила. *(Today we will cook together and learn these useful rules.)*

When you use a physical object to perform an action, you must use the Instrumental case without any preposition. Це дуже важливе правило української граматики. *(This is a very important rule of Ukrainian grammar.)* Наприклад, ми кажемо **«різати ножем»** (to cut with a knife). Слово **«ніж»** (knife) — це іменник чоловічого роду. Тому воно має закінчення **-ем**. А ось слово **«виделка»** (fork) — це жіночий рід. Жіночий рід зазвичай має стандартне закінчення **-ою**. Тому ми кажемо **«їсти виделкою»** (to eat with a fork) або **«мішати ложкою»** (to stir with a spoon). Особливу увагу зверніть на слово **«сіль»** (salt). Це жіночий рід, який закінчується на м'який приголосний. В орудному відмінку ми кажемо **«посипати сіллю»** (to sprinkle with salt). But be careful not to confuse cooking tools with physical locations. If you cook something on a hot surface, you need the Locative case. Ми правильно кажемо **«смажити на сковорідці»** (to fry on a pan), а не використовуємо орудну форму.

When we describe what a dish is made of or what it is served with, we use the preposition **«з»** (with) plus the Instrumental case. Ми часто запитуємо один одного: **«З чим це?»** (With what is this?). Відповідь детально описує інгредієнти. Наприклад, ми щоранку п'ємо гарячий **«чай з медом»** (tea with honey). Ми із задоволенням їмо смачний **«борщ зі сметаною»** (borscht with sour cream). Notice that we use the specific form **«зі»** instead of «з» before a word that starts with two consonants, like «сметана». Це робить швидку вимову значно легшою. *(This makes fast pronunciation significantly easier.)* Українці також дуже люблять літні солодкі **«вареники з вишнями»** (dumplings with cherries). У цьому смачному випадку ми використовуємо орудний відмінок множини.

Давайте уважно прочитаємо діалог двох хороших друзів. *(Let's carefully read a dialogue of two good friends.)* Іван та Олена готують святкову вечерю разом. *(Ivan and Olena are cooking a festive dinner together.)* Вони читають новий **рецепт** (recipe). *(They are reading a new recipe.)*
> — **Іван:** Олено, я дуже хочу зробити салат. *(Olena, I really want to make a salad.)*
> — **Олена:** Добре! Спочатку помий всі овочі теплою водою. *(Good! First, wash all the vegetables with warm water.)*
> — **Іван:** Чим мені швидко різати цю цибулю? *(What should I quickly cut this onion with?)*
> — **Олена:** Ріж цибулю цим великим гострим ножем. Потім додай свіжі помідори. *(Cut the onion with this big sharp knife. Then add fresh tomatoes.)*
> — **Іван:** А що ми зараз робимо з варениками? *(And what are we doing with the dumplings now?)*
> — **Олена:** Наші вареники вже повністю готові. Тепер ми будемо їх **подавати** (to serve). *(Our dumplings are already completely ready. Now we will serve them.)*
> — **Іван:** З чим ми зазвичай подаємо вареники? *(What do we usually serve the dumplings with?)*
> — **Олена:** Ми завжди подаємо їх зі шкварками та смаженою цибулею. *(We always serve them with cracklings and fried onion.)*

There are a few common vocabulary traps to avoid in the Ukrainian kitchen. Many language learners confuse the everyday words for oil and butter. В українській мові **«олія»** (oil) — це завжди рідкий продукт, наприклад, соняшникова або оливкова олія. А **«масло»** (butter) — це завжди твердий продукт з коров'ячого молока. Також пам'ятайте про популярне слово **«сир»** (cheese). В Україні це коротке слово означає і твердий сир, і м'який кисломолочний сир. Finally, remember to use authentic Ukrainian cooking verbs. Коли ми готуємо м'ясо на сковорідці, ми повинні **«смажити»** (to fry). Ніколи не використовуйте російське слово «жарити». Ми завжди смажимо картоплю або рибу на обід. *(We always fry potatoes or fish for lunch.)*

<!-- INJECT_ACTIVITY: recipe-fill-in -->


## Мій робочий день (My Workday)

Ми вже знаємо, як говорити про наші професії та смачну їжу. *(We already know how to talk about our professions and delicious food.)* Тепер давайте детально поговоримо про наш типовий **робочий день** (workday). Коли ми описуємо свою щоденну професійну рутину, ми постійно рухаємося в просторі та часі. Ми швидко їдемо на роботу, сидимо за робочим столом, смачно обідаємо з колегами. У всіх цих ситуаціях нам дуже допомагає орудний відмінок. Він показує не тільки зручний інструмент або приємну компанію. Орудний відмінок чудово описує, як саме ми подорожуємо містом і де точно ми працюємо. *(The Instrumental case perfectly describes exactly how we travel through the city and where exactly we work.)* When we talk about daily movement and schedules, the Instrumental case clearly expresses the core idea of "by means of".

In Ukrainian, we don't need an extra preposition to say we travel "by" a certain type of transport. Ми просто використовуємо слово у правильній формі орудного відмінка. *(We simply use the word in the correct Instrumental case form.)* Наприклад, ми часто кажемо **«їхати автобусом»** (to go by bus), **«їхати машиною»** (to go by car), або **«їхати велосипедом»** (to go by bicycle). Пам'ятайте, що популярне слово **«метро»** (subway) ніколи не змінює свою форму. The Instrumental case is also absolutely essential for describing physical locations and time using specific prepositions. These important spatial and temporal prepositions are **«перед»** (before / in front of), **«за»** (behind / at), **«між»** (between), **«над»** (above), and **«під»** (under). Ми кажемо: **«Я завжди паркуюся за офісом»** (I always park behind the office). Або ми детально описуємо кімнату: **«Мій стіл стоїть між великим вікном і дверима»** (My desk stands between the big window and the door). Ми часто ховаємо сумку **під столом** (under the table).

Давайте разом подивимося короткий відеоблог про типовий день менеджера. *(Let's watch a short vlog about a manager's typical day together.)* Ця цікава розповідь чудово поєднує різні корисні функції орудного відмінка. *(This interesting story perfectly combines various useful functions of the Instrumental case.)*
> — **Менеджер:** Вранці я завжди їду на роботу **трамваєм** (by tram). *(In the morning I always go to work by tram.)*
> — **Менеджер:** **Перед роботою** (Before work) я купую гарячу каву з молоком.
> — **Менеджер:** Мій новий офіс — **над кав'ярнею** (above the coffee shop).
> — **Менеджер:** Я майже весь день працюю **за комп'ютером** (at the computer).
> — **Менеджер:** О першій годині я обідаю **з колегами** (with colleagues).
> — **Менеджер:** Після смачного обіду я маю важливу **нараду** (meeting) з директором.
> — **Менеджер:** Ввечері я повертаюся додому машиною. *(In the evening I return home by car.)*

To make our sentences more natural and descriptive, we very often add adjectives and possessive pronouns. When the main noun changes to the Instrumental case, its connected adjectives and pronouns must change too. Для чоловічого та середнього роду ми завжди використовуємо закінчення **-им**. *(For masculine and neuter genders, we always use the ending -ym.)* Наприклад, ми із задоволенням говоримо **«з моїм новим менеджером»** (with my new manager) або вішаємо лампу **«над великим столом»** (above the big table). Для жіночого роду ми використовуємо м'яке закінчення **-ою** або **-єю**. *(For the feminine gender, we use the soft ending -oyu or -yeyu.)* Наприклад, ми пишемо **«новою ручкою»** (with a new pen) або щодня працюємо **«з моєю новою директоркою»** (with my new director).

| Рід (Gender) | Займенник (Pronoun) | Прикметник (Adjective) | Приклад (Example) |
| :--- | :--- | :--- | :--- |
| **Чоловічий / Середній** | мо**їм** | нов**им**, велик**им** | з мо**їм** нов**им** менеджером |
| **Жіночий** | мо**єю** | нов**ою**, цікав**ою** | з мо**єю** нов**ою** директоркою |

Ці граматичні закінчення роблять нашу українську мову красивою та дуже точною. *(These grammatical endings make our Ukrainian language beautiful and very precise.)* Тепер ви можете детально описати свій щоденний маршрут та звичайний робочий день. *(Now you can describe your daily route and regular workday in detail.)*

<!-- INJECT_ACTIVITY: true-false-workday -->


## Практика: Розкажи про себе (Practice: Tell About Yourself)

Зараз ми об'єднаємо всі наші знання про орудний відмінок. *(Now we will combine all our knowledge about the Instrumental case.)* Спробуйте написати коротку розповідь про себе, свою професію та інтереси. *(Try to write a short story about yourself, your profession, and interests.)* Your profile should be about eight to ten sentences long. Почніть з опису вашої роботи: **«Я працюю...»** (I work as...). *(Start with a description of your work: "I work as...".)* Далі розкажіть про ваше хобі: **«У вільний час я цікавлюся...»** (In my free time I am interested in...). *(Next, tell about your hobby: "In my free time I am interested in...".)* Не забудьте описати вашу улюблену страву: **«Я люблю салат з...»** (I love salad with...). *(Don't forget to describe your favorite dish: "I love salad with...".)* Наприкінці опишіть ваш типовий маршрут: **«Вранці я їду на роботу...»** (In the morning I go to work by...). *(At the end, describe your typical route: "In the morning I go to work by...".)* When writing, always check the gender of the noun. Remember that masculine and neuter nouns take the ending **-ом** or **-ем**, while feminine nouns take **-ою** or **-ею**. Уважно перевіряйте закінчення прикметників: **«з моїм новим колегою»** (with my new colleague) або **«з моєю новою колегою»** (with my new [female] colleague). *(Carefully check the endings of adjectives: "with my new colleague" or "with my new [female] colleague".)*

А тепер давайте попрактикуємо ці конструкції в реальній розмові. *(And now let's practice these constructions in a real conversation.)* Уявіть, що ви знайомитеся з новою людиною на вечірці. *(Imagine that you are meeting a new person at a party.)*

> — **Анна:** Привіт! Ми ще не знайомі. **Ким ти працюєш?** *(Hi! We haven't met yet. What do you do for a living?)*
> — **Максим:** Привіт! Я працюю **програмістом** (programmer). А ти?
> — **Анна:** А я працюю **вчителькою** (teacher). **Чим ти захоплюєшся** (What are you passionate about) після роботи?
> — **Максим:** Я цікавлюся **фотографією** (photography). А також дуже люблю готувати!
> — **Анна:** **Справді?** (Really?) Яку їжу ти любиш готувати?
> — **Максим:** Найбільше я люблю робити великий бутерброд **з сиром** (with cheese) і **помідорами** (tomatoes).
> — **Анна:** **Я теж!** (Me too!) Це дуже смачно. **Цікаво** (Interesting), де ти працюєш?
> — **Максим:** Мій офіс знаходиться **між** (between) банком і парком.

**Підсумок** (Summary). You have successfully learned how to use the Instrumental case in many different daily situations. Цей відмінок є надзвичайно важливим для природного спілкування українською мовою. *(This case is extremely important for natural communication in Ukrainian.)* Before we finish this module, use this simple self-check list to review your new skills. Подумайте, чи можете ви відповісти «так» на всі ці запитання. *(Think if you can answer "yes" to all these questions.)*

* Can I confidently name my own profession and five others using the correct **-ом**, **-ем**, **-ою**, or **-ею** endings?
* Can I accurately describe three ingredients in my favorite dish using the preposition **«з»** (with)?
* Can I name three tools I regularly use in the kitchen, like **ножем** (with a knife) or **ложкою** (with a spoon)?
* Can I explain exactly where my office or home is located using spatial prepositions like **«між»** (between), **«за»** (behind), or **«над»** (above)?
* Do I remember NOT to use the Russian calques «повар» and «жарити», and instead use the correct Ukrainian words **кухар** (cook) and **смажити** (to fry)?

Якщо ви відповіли «так», ви чудово засвоїли цей матеріал! *(If you answered "yes", you have mastered this material perfectly!)*

<!-- INJECT_ACTIVITY: review-instrumental -->

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
