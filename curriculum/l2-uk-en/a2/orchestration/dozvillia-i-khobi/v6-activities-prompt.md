<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dozvillia-i-khobi.yaml` file for module **35: Чим ти захоплюєшся? Дозвілля та хобі** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-categories -->`
- `<!-- INJECT_ACTIVITY: fill-in-hobbies-cases -->`
- `<!-- INJECT_ACTIVITY: quiz-acc-loc -->`
- `<!-- INJECT_ACTIVITY: match-up-verb-govt -->`
- `<!-- INJECT_ACTIVITY: error-correction-cases -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete sentences about hobbies with the correct case form (Я захоплююся
    ___ (плавання). Ми йдемо в/на ___)
  items: 8
  type: fill-in
- focus: Choose accusative (going to) vs. locative (being at) for leisure venues
  items: 8
  type: quiz
- focus: Match hobby verbs with their correct case government (захоплюватися + inst.,
    грати в + acc., ходити на + acc.)
  items: 8
  type: match-up
- focus: Sort leisure activities into categories (спорт, мистецтво, на природі, у
    місті)
  items: 8
  type: group-sort
- focus: Fix case errors in leisure sentences (e.g., *захоплююся плавання → плаванням,
    *ходжу в кіно → locative needed? No — accusative is correct for direction)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- вподобання (preferences, interests)
- прогулянка (walk, stroll)
- змагання (competition)
- малювання (drawing, painting)
- кіно (cinema, movies)
required:
- дозвілля (leisure, free time)
- хобі (hobby)
- захоплюватися (to be passionate about)
- займатися (to engage in, to do)
- спорт (sport)
- розвага (entertainment)
- вільний (free)
- плавання (swimming)
- музика (music)
- виставка (exhibition)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Хобі та вподобання

У кожної людини є **вільний час** (free time) або **дозвілля** (leisure). Після довгої роботи чи навчання ми всі хочемо приємно відпочивати. Хтось любить активний спорт, а хтось любить спокійне мистецтво чи відпочинок на природі. Коли ми знайомимося з новими людьми, ми часто запитуємо: «**Що ти любиш робити у вільний час?**» (What do you like to do in your free time?). Це дуже важливе та корисне питання. Воно допомагає краще зрозуміти людину, її характер та її світ. Ваші інтереси та **хобі** (hobbies) — це велика частина вашого життя. Сьогодні ми детально навчимося розповідати про свої улюблені заняття. Ми поговоримо про те, що ми любимо робити вдома чи на вулиці.

The simplest way to talk about your hobbies is to use the verb **любити** (to love / to like) followed by an infinitive verb. You already know this structure from previous lessons. It is very versatile and easy to use. You can describe almost any activity this way without changing endings. Ось кілька дуже корисних прикладів:

* Я **люблю читати книги** (I love to read books) пізно ввечері.
* Мій старший брат **любить плавати в басейні** (loves to swim in the pool) на вихідних.
* Ми з друзями **любимо подорожувати** (love to travel) влітку.
* Після важкої роботи я **люблю дивитися серіали** (love to watch TV series).
* У неділю моя мама **любить готувати** (loves to cook) нові смачні страви.

Такі речення дуже прості, але вони чудово описують ваше щоденне дозвілля.

If you want to sound more advanced and natural, use specific verbs that require the Instrumental case. The two most common verbs for hobbies are **займатися** (to engage in / to do) and **захоплюватися** (to be passionate about). These verbs cannot take an infinitive action. They must be followed by a noun in the Instrumental case. Давайте уважно подивимося на закінчення іменників в орудному відмінку:

* Чоловічий рід (Masculine) зазвичай отримує закінчення **-ом**: Я активно займаюся **спортом** (sport), мій друг дуже захоплюється **футболом** (football).
* Жіночий рід (Feminine) отримує закінчення **-ою**: Моя сестра займається класичною **музикою** (music), я захоплююся **йогою** (yoga).
* Середній рід (Neuter verbal nouns) часто закінчується на **-ям**: Ми займаємося **плаванням** (swimming), діти в школі захоплюються **малюванням** (drawing).

Ці слова допомагають гарно розказати про ваші глибокі та серйозні інтереси.

To give more detail about your daily routine, you can use adverbs of frequency and time expressions. These words clearly tell others how often you do your favorite leisure activities. Ви можете використовувати такі корисні слова:

* **завжди** (always): Я завжди читаю цікаві книги перед сном.
* **часто** (often): Ми часто гуляємо в зеленому парку біля дому.
* **іноді** (sometimes): Іноді я дивлюся старі європейські фільми.
* **рідко** (rarely): Взимку я дуже рідко граю в настільний теніс.
* **ніколи** (never): Я ніколи не займаюся професійним боксом.

Також вам буде корисно знати фрази про регулярність:

* **щодня** (every day): Вона плаває щодня вранці.
* **раз на тиждень** (once a week): Я ходжу в спортзал раз на тиждень.

Ці маленькі слова роблять вашу розповідь набагато точнішою та живою.

Давайте подивимося, як люди говорять про своє дозвілля в реальному житті. Двоє колег обідають разом у кафе і говорять про плани на вихідні.

> — **Колега 1:** Що ти робитимеш на вихідних? Маєш уже якісь плани?
> — **Колега 2:** Я дуже захоплююся **плаванням** (swimming), тож у суботу піду **у басейн** (to the pool). А ти?
> — **Колега 1:** А я люблю сучасне мистецтво. У неділю я йду **на виставку** (to an exhibition) з подругою.
> — **Колега 2:** Це чудово! Я також іноді люблю ходити в різні музеї.
> — **Колега 1:** Може, наступного тижня ми підемо кудись разом?
> — **Колега 2:** З задоволенням! Але спочатку я хочу пограти у футбол з моїми друзями.

<!-- INJECT_ACTIVITY: group-sort-categories -->
<!-- INJECT_ACTIVITY: fill-in-hobbies-cases -->


## Куди йдемо? Де ми?

Коли ми плануємо вільний час, важливо розуміти різницю між напрямком руху та місцем. 
To express direction (going TO a place), Ukrainian uses the Accusative case. 
To express location (being AT a place), we use the Locative case. 
Давайте порівняємо ці дві ситуації на дуже популярних прикладах. 
Коли ви йдете дивитися виставу, ви кажете: «Я **йду в театр**» (am going to the theater). 
Але коли ви вже дивитеся виставу, ви кажете: «Я **в театрі**» (am in the theater). 
Якщо ви любите картини, ви кажете: «Ми **йдемо на виставку**» (are going to an exhibition). 
Коли ви вже там, ви кажете: «Ми **на виставці**» (are at the exhibition). 
Для спорту ми говоримо: «Він **йде на стадіон**» (is going to the stadium). 
А коли матч уже йде, він каже: «Він **на стадіоні**» (is at the stadium). 
This pattern is essential for talking about your weekend plans accurately.

Для регулярних занять і хобі ми часто використовуємо дієслова руху. 
The most common verb for regular visits to a place is **ходити** (to go regularly). 
Наприклад, ви можете сказати: «Я **ходжу в басейн** (go to the pool) щовівторка». 
Це означає, що плавання — це ваше постійне хобі. 
When you want to talk about a one-time event or a specific future plan, you use the perfective verb **піти** (to go once). 
Наприклад, ви кажете: «Завтра я **піду в басейн**» (will go to the pool). 
Ось інший приклад: «Ми часто **ходимо в кіно** (go to the movies), але сьогодні ми **підемо в театр** (will go to the theater)». 
Ці два дієслова допомагають дуже точно описувати ваші звички та плани.

Дуже популярне хобі — це ігри та музика. 
Для цього ми використовуємо дієслово **грати** (to play), але воно має дві різні конструкції. 
When you talk about sports or games, you must use "грати в" or "грати у" followed by the Accusative case. 
Наприклад: мій брат любить **грати у футбол** (to play football), а я люблю **грати в теніс** (to play tennis). 
Увечері ми можемо **грати в шахи** (to play chess) з батьком. 
When you talk about playing musical instruments, you must use "грати на" followed by the Locative case. 
Наприклад: моя подруга чудово вміє **грати на гітарі** (to play the guitar). 
Її сестра любить **грати на піаніно** (to play the piano), а їхній брат вчиться **грати на скрипці** (to play the violin). 
Ця різниця дуже важлива для правильного українського спілкування.

Ще один активний вид дозвілля — це катання. 
For activities that involve riding something, Ukrainian uses the construction **кататися на** (to ride / to roll on) followed by the Locative case. 
Цей вид відпочинку дуже залежить від сезону. 
Влітку або навесні люди люблять **кататися на велосипеді** (to ride a bicycle) у парку. 
Також влітку можна поїхати на озеро і **кататися на човні** (to ride a boat). 
Взимку українці обирають інші активні розваги. 
Коли падає сніг, діти і дорослі йдуть **кататися на лижах** (to ski) у гори. 
А у місті дуже популярно **кататися на ковзанах** (to ice skate) на великих ковзанках. 
Запам'ятайте цю конструкцію, вона дуже часто звучить у розмовах про зимовий чи літній відпочинок.

Давайте послухаємо розмову двох людей, які щойно познайомилися. Вони розповідають про свої хобі. 
> — **Софія:** Привіт! Мене звати Софія. Я дуже **захоплююся малюванням** (am passionate about drawing).
> — **Новий знайомий:** Привіт, Софійо! Дуже приємно. А я більше люблю спорт. Я часто граю у футбол.
> — **Софія:** Це цікаво! А ти любиш музику?
> — **Новий знайомий:** Так, звичайно. У вільний час я люблю грати на гітарі. А ти граєш на чомусь?
> — **Софія:** Ні, але я іноді **ходжу на концерти** (go to concerts).

Цей короткий діалог — чудовий приклад того, як можна легко розповісти про себе.

<!-- INJECT_ACTIVITY: quiz-acc-loc -->
<!-- INJECT_ACTIVITY: match-up-verb-govt -->


## Плани на вихідні

Коли ми маємо вільний час, ми часто хочемо провести його з друзями. When you want to suggest an activity, Ukrainian has several natural phrases. Найпростіший спосіб — це сказати **«Ходімо!»** (Let's go!). Наприклад, ви можете запропонувати другу: «Ходімо в кіно!» або «Ходімо на стадіон!». Якщо ви не дуже впевнені і хочете запропонувати варіант, використовуйте фразу **«Може, підемо...?»** (Maybe we'll go...?). Наприклад: «Може, підемо на прогулянку?». Для спорту та ігор ми часто кажемо **«Давай пограємо!»** (Let's play!). Наприклад: «Давай пограємо в теніс!». Якщо ви хочете запитати про бажання іншої людини, використовуйте конструкцію **«Хочеш піти на...?»** (Do you want to go to...?). Наприклад: «Хочеш піти на виставку?». Ці фрази допомагають легко планувати спільний відпочинок. Їх дуже корисно знати для щоденного спілкування.

Коли друзі пропонують вам щось цікаве, важливо вміти радісно погодитися. Accepting an invitation with enthusiasm makes communication much warmer. Якщо вам дуже подобається пропозиція, скажіть **«З задоволенням!»** (With pleasure!). Це звучить дуже ввічливо і позитивно. Інша популярна фраза — це **«Чудова ідея!»** (Great idea!). Наприклад, якщо друг каже: «Ходімо в парк!», ви можете відповісти: «Чудова ідея!». Коли хтось використовує слово «Давай...», ви можете просто відповісти **«Так, давай!»** (Yes, let's!). А в неформальній розмові серед друзів дуже часто звучить коротка фраза **«Я — за!»** (I'm in!). Вона означає, що ви повністю підтримуєте план. Використовуйте ці емоційні відповіді, щоб показати, що ви раді провести час разом. Вони роблять вашу українську мову більш живою та природною.

Але іноді ми не маємо часу або просто не хочемо кудись іти. Declining an invitation politely is just as important as accepting one. Найкращий спосіб відмовити — це почати з фрази **«На жаль, не можу»** (Unfortunately, I can't). Це показує, що ви б хотіли піти, але обставини не дозволяють. Потім варто пояснити причину. Чоловік скаже **«Я сьогодні зайнятий»** (I'm busy today), а жінка — **«Я сьогодні зайнята»**. Ви також можете сказати **«У мене вже є плани»** (I already have plans). Це універсальна відмова, коли ви не хочете розповідати деталі. Щоб зберегти хороші стосунки і показати, що ви хочете зустрітися пізніше, запитайте: **«Може, іншим разом?»** (Maybe another time?). Така відповідь є дуже дружньою. Навіть коли ви відмовляєте, важливо залишатися ввічливим.

Коли ви вже домовилися про зустріч, треба обговорити важливі деталі. Discussing logistics like time and place involves specific question words and cases. Щоб запитати про час, ми використовуємо фразу **«О котрій?»** (At what time?). Відповідь завжди буде з прийменником «о» або «об» та порядковим числівником. Наприклад: **«О п'ятій»** (At five) або «О сьомій» (At seven). Щоб домовитися про місце, запитайте **«Де зустрінемося?»** (Where will we meet?). Часто ми зустрічаємося біля якихось об'єктів. Для цього ми використовуємо прийменник **«біля»** (near) та іменник у родовому відмінку (Genitive case). Наприклад, ви можете сказати: **«Біля входу»** (Near the entrance), «Біля метро» (Near the subway), або «Біля парку» (Near the park). Ці короткі запитання і відповіді роблять планування дуже швидким та ефективним.

Давайте прочитаємо коротку історію про те, як двоє друзів планують свої вихідні. Вони обирають між концертом, музеєм та прогулянкою.

> — **Марко:** Привіт, Тарасе! Які маєш плани на неділю? Хочеш піти на концерт? *(Hi, Taras! What plans do you have for Sunday? Do you want to go to a concert?)*
> — **Тарас:** Привіт! На жаль, не можу. У мене вже є плани на ранок. А що ти робиш після обіду? *(Hi! Unfortunately, I can't. I already have plans for the morning. And what are you doing in the afternoon?)*
> — **Марко:** Після обіду я вільний. Може, підемо в музей? *(In the afternoon I am free. Maybe we'll go to the museum?)*
> — **Тарас:** Музей — це цікаво, але погода дуже гарна. Ходімо краще в парк! *(A museum is interesting, but the weather is very nice. Let's go to the park instead!)*
> — **Марко:** Чудова ідея! Я — за! Де зустрінемося? *(Great idea! I'm in! Where will we meet?)*
> — **Тарас:** Давай зустрінемося біля входу в парк. О котрій? *(Let's meet near the entrance to the park. At what time?)*
> — **Марко:** О п'ятій годині. *(At five o'clock.)*
> — **Тарас:** Домовилися! До неділі! *(Agreed! Until Sunday!)*

Цей діалог показує, як легко комбінувати пропозиції, відмови та деталі логістики.

<!-- INJECT_ACTIVITY: error-correction-cases -->


## Що мені подобається найбільше

Коли ми плануємо вихідні, ми обираємо те, що любимо. Іноді нам подобається багато різних речей, але одна є улюбленою. To express strong preferences and rank your interests, Ukrainian has several useful phrases that go beyond basic likes. Базова фраза — це **«мені подобається»** (I like). Наприклад: «Мені подобається сучасна музика». Але якщо ви дуже любите певне заняття, скажіть **«мені найбільше подобається»** (I like most). Це показує ваш головний пріоритет серед інших справ. А для максимальної емоції ми маємо дієслово **«обожнювати»** (to adore). The phrase "я обожнюю" is a fantastic way to show true passion for an activity. Ми часто комбінуємо різні хобі в одному реченні, щоб показати контраст. Ви можете сказати: **«Я люблю читати, але найбільше обожнюю малювати»** (I love to read, but most of all I adore drawing). Або інший приклад: «Мені подобається спорт, але я обожнюю ходити в гори».

А як українці проводять свій вільний час? Звичайно, ми любимо ходити в кіно, театри та займатися спортом. Але відпочинок на природі має особливе місце в нашій культурі. Nature holds a very special place in Ukrainian leisure activities. Дуже популярно їздити в **Карпати** (the Carpathians). Там люди гуляють у лісі, дихають свіжим повітрям і просто відпочивають. Exploring ancient castles in Western Ukraine is another favorite weekend trip for many families. Там можна побачити багато цікавої історії. Також українці мають традиційні сезонні хобі. Восени багато людей їдуть у ліс **збирати гриби** (to hunt mushrooms). Це заняття часто називають тихим полюванням. А влітку дуже популярно **збирати ягоди** (to pick berries). Ці традиції допомагають забути про стрес і швидкий міський шум. Якщо ви скажете українцям: «Я обожнюю збирати гриби», ви одразу знайдете нових друзів!

Наш вільний час показує, які ми насправді люди. Our leisure time often defines our personality and helps us connect with others. Тепер ви знаєте достатньо слів, щоб цікаво розповісти про себе. You have the vocabulary and grammar tools to describe your unique lifestyle to new Ukrainian friends. Не забувайте активно використовувати чотири головні дієслова з цього уроку. Ви можете **«займатися»** (to engage in) спортом, танцями або йогою. Ви можете сильно **«захоплюватися»** (to be passionate about) музикою чи фотографією. Ви можете **«грати в»** (to play) теніс або **«грати на»** (to play an instrument) гітарі. І, звичайно, ви можете **«ходити в»** (to go to) кіно, музей або на стадіон. Практикуйте ці конструкції, комбінуйте їх і розповідайте про свої хобі впевнено. Розкажіть світу, чим ви захоплюєтеся!


## Підсумок

Сьогодні ми вивчили, як говорити про **дозвілля** *(leisure)* та хобі. Ви вже знаєте, які дієслова використовувати для різних занять. Головне правило — це пам'ятати про правильний відмінок. The main rule is to remember the correct case after the verb.

Коли ви говорите про ігри, використовуйте конструкцію «грати в» плюс знахідний відмінок. Наприклад: я граю в теніс. For musical instruments, use the structure "грати на" plus the locative case. Наприклад: вона грає на гітарі.

Якщо ви маєте серйозне хобі, використовуйте дієслово «захоплюватися». Після нього завжди йде орудний відмінок. Наприклад: він захоплюється малюванням. For leisure destinations, use "ходити на" or "ходити в" with the accusative case. Наприклад: ми ходимо на концерт.

Тепер перевірте себе. Now test yourself. Спробуйте відповісти на три запитання:

1. Яка різниця між «граю в...» та «граю на...»?
2. Як сказати "I am interested in photography"?
3. Як запросити друга в кіно?

Якщо ви знаєте ці відповіді, ви чудово засвоїли нову тему! If you know the answers, you have mastered this topic perfectly!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dozvillia-i-khobi
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

**Level: A2 (Module 35/60) — ELEMENTARY**

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
