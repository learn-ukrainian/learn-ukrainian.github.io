<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 62: Дія і час (A2, A2.9 [Metalanguage Bridge & Foundation])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-062
level: A2
sequence: 62
slug: metalanguage-verbs-and-time
version: '1.1'
title: Дія і час
subtitle: Дієслівні категорії та словникова грамотність
focus: bridge
pedagogy: Bridge
phase: A2.9 [Metalanguage Bridge & Foundation]
word_target: 2000
objectives:
  - Learner can name Ukrainian verb categories (час, вид, спосіб, дієвідміна, 
    особа) and identify them in verb forms.
  - Learner can distinguish доконаний/недоконаний вид (perfective/imperfective 
    aspect) using Ukrainian terminology.
  - Learner can read and interpret dictionary entries from goroh.pp.ua, 
    understanding abbreviations (ж.р., док., недок., одн., мн., etc.).
  - Learner can use Ukrainian adverb terminology (прислівник місця, часу, 
    способу дії) to classify adverbs they already know.
dialogue_situations:
  - situation: "A student asking the teacher to explain verb aspect terminology —
      Що означає 'доконаний вид'? Як визначити дієвідміну? Teacher uses familiar verbs
      as examples"
    functions: ["asking about grammar concepts", "understanding Ukrainian terminology",
      "connecting terms to known grammar"]
    key_vocabulary: ["доконаний", "недоконаний", "дієвідміна", "особа"]
  - situation: "A student trying to look up a word in an online dictionary — reading
      the entry aloud and asking a classmate what the abbreviations mean"
    functions: ["reading dictionary entries", "interpreting abbreviations", "peer
          help"]
    key_vocabulary: ["словник", "скорочення", "ж.р.", "док.", "недок."]
content_outline:
  - section: 'Дієслово: категорії та терміни (The Verb: Categories and Terms)'
    words: 600
    points:
      - 'Re-labeling what they know: the learner already uses tenses and aspects —
        now they learn the Ukrainian terms. Method: Grade 4-5 textbook excerpts.'
      - 'Час (tense): минулий час (past), теперішній час (present), майбутній час
        (future). Examples with verbs they know: читав (мин.), читаю (теп.), читатиму/буду
        читати (майб.).'
      - 'Вид (aspect): доконаний вид (perfective) — що зробити? прочитати, написати.
        Недоконаний вид (imperfective) — що робити? читати, писати. Connect to what
        they learned in A2.1 aspect modules.'
      - 'Спосіб (mood): дійсний спосіб (indicative — stating facts), наказовий спосіб
        (imperative — giving commands: читай!), умовний спосіб (conditional — label
        only: читав би. Production is B1; here we learn the term so learners can read
        grammar references).'
  - section: 'Дієвідміна та особа (Conjugation and Person)'
    words: 450
    points:
      - 'Дієвідміна (conjugation class): I дієвідміна (-еш, -е pattern: пишеш, пише)
        vs. II дієвідміна (-иш, -ить pattern: говориш, говорить). How to determine:
        look at the 3rd person singular.'
      - 'Особа (person): перша особа (1st — я, ми), друга особа (2nd — ти, ви), третя
        особа (3rd — він/вона/воно, вони).'
      - 'Число (number) in verbs: однина (singular — читаю, читаєш, читає), множина
        (plural — читаємо, читаєте, читають).'
      - 'Practice: identify час, вид, особа, число for given verb forms.'
  - section: 'Словникова грамотність: читаємо словник (Dictionary Literacy: Reading
      a Dictionary)'
    words: 550
    points:
      - 'How to read a goroh.pp.ua entry: headword, stress mark, part of speech abbreviation,
        grammatical information, definitions.'
      - 'Key abbreviations: ім. (іменник), прикм. (прикметник), дієсл. (дієслово),
        займ. (займенник), присл. (прислівник), ч.р. (чоловічий рід), ж.р. (жіночий
        рід), с.р. (середній рід), док. (доконаний), недок. (недоконаний), одн. (однина),
        мн. (множина).'
      - 'Practice: read 5-6 real dictionary entries and extract grammatical information.
        What part of speech? What gender? What aspect?'
      - 'Why this matters: B1 and beyond will use Ukrainian-language references. This
        skill is essential for independent learning.'
  - section: 'Прислівник: види та приклади (The Adverb: Types and Examples)'
    words: 400
    points:
      - 'Adverb classification using Ukrainian terms: прислівник місця (adverb of
        place) — тут, там, далеко, близько; прислівник часу (adverb of time) — сьогодні,
        завтра, вчора, завжди; прислівник способу дії (adverb of manner) — швидко,
        повільно, добре.'
      - 'Practice: sort known adverbs into categories using Ukrainian terms.'
      - 'Connection to прикметник: many adverbs derive from adjectives (швидкий →
        швидко, гарний → гарно). The -о ending pattern.'
vocabulary_hints:
  required:
    - дієслово (verb)
    - час (tense, time)
    - вид (aspect)
    - доконаний (perfective)
    - недоконаний (imperfective)
    - спосіб (mood, manner)
    - дієвідміна (conjugation class)
    - особа (person, grammatical)
    - прислівник (adverb)
    - словник (dictionary)
  recommended:
    - дійсний спосіб (indicative mood)
    - наказовий спосіб (imperative mood)
    - умовний спосіб (conditional mood — label only, production is B1)
    - скорочення (abbreviation)
activity_hints:
  - type: match-up
    focus: Match verb category terms to their definitions
    items: 8
  - type: quiz
    focus: Read a dictionary entry and answer questions about its grammatical 
      info
    items: 8
  - type: group-sort
    focus: Sort verb forms by час (минулий, теперішній, майбутній)
    items: 8
  - type: fill-in
    focus: Complete sentences about verbs using Ukrainian metalanguage terms
    items: 8
references:
  - title: Заболотний Grade 5, Дієслово як частина мови
    notes: Verb categories as introduced in Ukrainian school curriculum
  - title: Вашуленко Grade 4, Дієслово
    notes: Primary school approach to verb tense and aspect terminology

</plan_content>

## Generated Content

<generated_module_content>
## Дієслово: категорії та терміни

Ми довго вчили мову інтуїтивно. Ми просто слухали діалоги і повторювали корисні фрази. Це був дуже хороший і легкий старт. Але тепер нам потрібна чітка система для роботи. 

Welcome to the language of the classroom. 

Щоб вільно читати граматику далі, нам потрібна **термінологія** (terminology). Усі слова у мові мають свої групи. Це **частини мови** (parts of speech). 

Why is this so important for us right now? 

На рівні B1 ми будемо часто використовувати українські словники. Ми будемо читати нові правила українською мовою. 

You will see grammatical terms instead of English explanations. Knowing these terms is the key to independent learning. 

Сьогодні ми уважно подивимося на ті граматичні концепції, які ми вже добре знаємо. Але тепер ми дамо цим правилам правильні українські назви.

Головна частина мови для нас сьогодні — це **дієслово** (the verb). Це справжнє серце кожного українського речення. Дієслово показує активну дію або стан людини. Ми вже добре знаємо, як ці слова працюють у тексті. 

Тепер ми подивимося на три великі категорії дієслова. Ці категорії логічно показують, як саме дієслово змінюється. 

Перша базова категорія — це **час** (tense). Друга важлива категорія — це **вид** (aspect). Третя цікава категорія — це **спосіб** (mood). 

Зараз ми детально розглянемо кожну з цих категорій.

Перша і найпростіша категорія — це час. Він дуже логічно показує, коли саме відбувається наша дія. Українська мова має три часи, які ви вже дуже добре знаєте. 

**Минулий час** (past tense) показує дію, яка вже давно відбулася. Наприклад: «я працював вчора в офісі», «вона довго читала цікаву книгу». 

**Теперішній час** (present tense) показує дію, яка відбувається прямо зараз. Наприклад: «я працюю сьогодні вдома», «вона зараз уважно читає нову книгу». 

**Майбутній час** (future tense) показує дію, яка ще тільки буде завтра. Наприклад: «я буду працювати завтра» або «я попрацюю пізно ввечері». 

Тут є один дуже важливий нюанс для розуміння граматики. 

Only verbs that state real facts have tenses. 

Ця категорія реальності називається **дійсний спосіб** (indicative mood). Якщо дія повністю реальна, вона завжди має минулий, теперішній або майбутній час.

Друга і мабуть найважливіша категорія — це вид. Це фундаментальна різниця у всіх слов'янських мовах. Вид показує, як саме протікає наша дія. 

**Недоконаний вид** (imperfective aspect) означає довгий процес або регулярну дію. Він завжди відповідає на питання «що робити?». Наприклад: «що робити кожного дня? — читати, писати, купувати, працювати». 

**Доконаний вид** (perfective aspect) означає фінальний результат або одноразову завершену дію. Він завжди відповідає на питання «що зробити?». Наприклад: «що зробити сьогодні? — прочитати, написати, купити, попрацювати». 

Let's closely compare two past tense verbs you already know well. 

Слово «купував» — це минулий час, недоконаний вид. Це означає, що ви просто ходили по магазину і дуже довго вибирали речі. 

Слово «купив» — це минулий час, доконаний вид. Це означає конкретний результат: ви вже дали гроші касиру і взяли свій товар. 

Правильний вид дуже важливий для точного спілкування з людьми.

Третя граматична категорія — це спосіб. Він емоційно показує відношення дії до нашої реальності. Ми вже чудово знаємо дійсний спосіб, який описує реальні факти. Наприклад: «Сонце яскраво світить на небі». 

Але є ще **наказовий спосіб** (imperative mood). Ми використовуємо його кожного дня для наказів, прохань або корисних порад. Наприклад: «Слухай мене уважно!» або «Читай цей текст швидко!». 

Третій тип — це **умовний спосіб** (conditional mood). Він показує наші мрії або цікаві гіпотетичні ситуації. Наприклад: «Я б пішов у кіно сьогодні ввечері». 

Here is a critical decolonization rule for authentic Ukrainian phrasing. Never use the Russian calque "давайте" to form group commands. 

Українська мова має свої власні красиві та синтетичні форми для цього. Замість «давайте підемо», ми завжди кажемо коротко «ходімо». Замість «давайте працювати», ми чудово кажемо «працюймо». Це звучить дуже природно і правильно для носіїв мови.

<!-- INJECT_ACTIVITY: match-up-verb-terms -->

## Дієвідміна та особа

Ми добре знаємо, що дієслово змінює свою форму. Чому воно це робить? Тому що воно показує, хто саме виконує дію. Ця граматична категорія називається **особа** *(person)*. Також дієслово завжди показує, скільки людей або предметів виконують дію. Ця категорія називається **число** *(number)*. В українській мові є **однина** *(singular)* та **множина** *(plural)*.

Коли ми говоримо про себе, ми використовуємо **першу особу** *(first person)*. Це займенники «я» *(I)* та «ми» *(we)*. Коли ми говоримо з кимось прямо, це **друга особа** *(second person)*. Ми кажемо «ти» *(you, singular)* або «ви» *(you, plural/formal)*. Коли ми говоримо про інших людей або предмети, це **третя особа** *(third person)*. Це займенники «він» *(he)*, «вона» *(she)*, «воно» *(it)* та «вони» *(they)*.

Ось зручна таблиця для цих граматичних термінів.

| Число | 1-ша особа | 2-га особа | 3-тя особа |
| :--- | :--- | :--- | :--- |
| **Однина** | я | ти | він, вона, воно |
| **Множина** | ми | ви | вони |

Ці слова є фундаментальними для спілкування. Вони допомагають нам правильно змінювати дієслова.

Тепер ми вивчимо ще один корисний термін. Ви, мабуть, помітили, що дієслова мають різні закінчення в теперішньому часі. Чому ми кажемо «ти пишеш», але при цьому кажемо «ти говориш»? Це залежить від граматичної групи дієслова. Ця група називається **дієвідміна** *(conjugation class)*.

В українській мові є лише дві такі групи. **Перша дієвідміна** *(first conjugation)* має голосні літери «е» або «є» у закінченнях. Наприклад: «ти пиш-е-ш», «він чита-є», «ми зна-є-мо». **Друга дієвідміна** *(second conjugation)* має голосні літери «и» або «ї» у закінченнях. Наприклад: «ти говор-и-ш», «вона сто-ї-ть», «ми мовч-и-мо».

Як перевірити дієвідміну нового слова? Є дуже простий тест. Подивіться на форму другої особи однини. Якщо там є «е» або «є» — це перша дієвідміна. Якщо там є «и» або «ї» — це друга дієвідміна.

Також можна дивитися на форму третьої особи множини. Перша дієвідміна завжди закінчується на «-уть» або «-ють» (вони пишуть, вони читають). Друга дієвідміна закінчується на «-ать» або «-ять» (вони кричать, вони говорять). Цей тест працює ідеально.

Тепер ми можемо зробити повний граматичний аналіз слова. В українській школі цей процес називається **морфологічний розбір** *(morphological analysis)*. Це означає, що ми беремо одне слово і знаходимо всі його граматичні категорії.

Для практичного прикладу візьмемо дієслово «читаємо» з простого речення «ми зараз читаємо нову книгу». Спробуймо знайти шість ключових категорій.

Крок перший: яка це **частина мови** *(part of speech)*? Це дієслово, бо воно показує дію.
Крок другий: який це час? Це теперішній час, бо дія відбувається зараз.
Крок третій: який це вид? Це недоконаний вид, бо це довгий процес і він відповідає на питання «що робимо?».
Крок четвертий: яка це особа? Це перша особа, бо ми використовуємо займенник «ми».
Крок п'ятий: яке це число? Це множина, бо людей багато.
Крок шостий: яка це дієвідміна? Це перша дієвідміна, бо ми бачимо літеру «є» у слові «читаємо» і закінчення «-ють» у формі «читають».

Цей аналіз показує, як логічно працює мова. Тепер ви знаєте базову граматичну термінологію. Ви можете самостійно аналізувати нові слова.

<!-- INJECT_ACTIVITY: group-sort-verb-tense -->

## Словникова грамотність: читаємо словник (~550 words)

> — **Марк:** Вибачте, я зараз дивлюся у **словник** *(dictionary)* Goroh.pp.ua. Тут є нове слово «бачити». Але що означають ці маленькі букви поруч: «недок.» і «дієсл.»? *(Excuse me, I am looking in the dictionary Goroh.pp.ua right now. Here is the new word "бачити". But what do these small letters nearby mean: "недок." and "дієсл."?)*
> — **Вчителька:** Це дуже гарне і важливе питання! *(This is a very good and important question!)* Це спеціальні граматичні **скорочення** *(abbreviations)*. Словники завжди використовують такий короткий код, щоб зекономити місце. *(Dictionaries always use such a short code to save space.)*
> — **Марк:** Тобто це граматика? *(So this is grammar?)*
> — **Вчителька:** Так, це ключова граматична інформація. *(Yes, this is key grammatical information.)* Слово «дієсл.» означає дієслово. А «недок.» означає недоконаний вид. Коли ви самостійно читаєте словник, ви повинні розуміти цей код. *(The word "дієсл." means verb. And "недок." means imperfective aspect. When you independently read a dictionary, you must understand this code.)*

Анатомія словникової статті має свої чіткі правила. Коли ви відкриваєте словник, перше велике слово — це **заголовне слово** *(headword)*. Воно завжди стоїть у початковій формі. Для дієслова це інфінітив, а для іменника — це називний відмінок однини. Друга дуже важлива річ у словнику — це **наголос** *(stress mark)*. Наголос показує нам, як правильно вимовляти нове слово. Це перше, що ви повинні уважно перевірити. Український наголос часто може змінювати значення слова. Наприклад, порівняйте слова «замок» *(castle)* і «замок» *(lock)*. Одразу після наголосу йде граматичний блок. Саме там живуть наші короткі граматичні скорочення. Вони дають вам точну інструкцію, як правильно використовувати це слово в реченні. Якщо ви розумієте цей граматичний блок, ви автоматично уникнете багатьох серйозних помилок у майбутньому.

Ось велика таблиця базових скорочень, які ви дуже часто будете бачити. Цей список допоможе вам читати майже будь-який український словник без проблем.

| Скорочення | Повне слово | Переклад |
| :--- | :--- | :--- |
| **ім.** | іменник | *noun* |
| **прикм.** | прикметник | *adjective* |
| **дієсл.** | дієслово | *verb* |
| **займ.** | займенник | *pronoun* |
| **присл.** | прислівник | *adverb* |
| **ч. Р.** | чоловічий рід | *masculine gender* |
| **ж. Р.** | жіночий рід | *feminine gender* |
| **с. Р.** | середній рід | *neuter gender* |
| **одн.** | однина | *singular* |
| **мн.** | множина | *plural* |
| **док.** | доконаний вид | *perfective aspect* |
| **недок.** | недоконаний вид | *imperfective aspect* |

Вивчіть ці скорочення напам'ять. Вони — ваш надійний ключ до успішного самостійного навчання. Коли ви знаєте, що нове слово має позначку «ж. Р.», ви точно знаєте, що треба сказати «гарна», а не «гарний». Якщо ви бачите позначку «мн.», це чітко означає, що слово використовується тільки у множині. Хороші приклади таких слів — це «окуляри» *(glasses)*, «гроші» *(money)* або «ножиці» *(scissors)*.

Давайте разом попрактикуємося читати ці коди. Візьмемо два реальні приклади з популярного онлайн-словника.

Перший приклад — це слово «книга». У словнику ми бачимо такий запис: **книга** (ім., ж. Р., одн.). Що це означає для нас? Ми відразу розуміємо, що це іменник жіночого роду в однині. Тому ми можемо правильно сказати «моя нова книга» і використовувати її як підмет у реченні. Ми знаємо, які закінчення треба обрати.

Другий приклад — це слово «зробити». Словник каже нам: **зробити** (дієсл., док.). Цей короткий код дає студенту надзвичайно важливу інформацію! Це дієслово доконаного виду. Що це означає на практиці для іноземця? Це означає, що дія має фінальний результат. Але найголовніше правило — ми знаємо, що це дієслово ніколи не має форм теперішнього часу! Ви не можете сказати «я зроблю це зараз», якщо ви маєте на увазі процес, який зараз триває. Форма «я зроблю» — це вже проста форма майбутнього часу. Тому цей маленький граматичний блок допомагає вам обрати правильний час для вашого речення і говорити природно.

<!-- INJECT_ACTIVITY: quiz-quiz-dictionary-literacy -->

## Прислівник: види та приклади

Тепер поговоримо про ще одну важливу частину мови в українській граматиці. Це **прислівник** *(adverb)*. Ви вже добре знаєте, що іменники, прикметники та дієслова постійно змінюють закінчення. Вони залежать від контексту. Але прислівник — це унікальне, **незмінне слово** *(unchangeable word)*. Що це означає для вас як для студента? Це означає, що прислівник ніколи не має відмінків. Він не має родів, чисел або осіб. Він завжди залишається у своїй початковій словниковій формі. Для вивчення мови це дуже гарна новина! Вам не потрібно думати про складні закінчення. Ви просто берете прислівник і використовуєте його у своєму реченні. Наприклад, слово «добре» *(well)* завжди залишається словом «добре». Це правило діє незалежно від того, хто виконує дію. Але є один невеликий нюанс. Прислівники ніколи не змінюються. Тому іноді студентам важко зрозуміти їхню граматичну роль у тексті. Проте у будь-якому словнику ви завжди знайдете ці слова. Вони будуть мати коротку позначку **«присл.»** *(adv.)*.

В українській мові всі прислівники мають свої специфічні категорії. Вони показують нам різноманітні обставини, за яких відбувається дія. Подивімося детально на три найважливіші види прислівників. Ви вже дуже добре знаєте ці слова. Ви постійно використовуєте їх на практиці. Ми просто дамо їм офіційні граматичні імена. 

Перша базова група — це **прислівник місця** *(adverb of place)*. Цей вид завжди відповідає на питання «де?» *(where?)* або «куди?» *(where to?)*. До цієї групи належать такі слова: «тут» *(here)*, «там» *(there)*, «далеко» *(far)*. Також сюди входять слова «близько» *(near)* та «всюди» *(everywhere)*.

Друга велика і популярна група — це **прислівник часу** *(adverb of time)*. Він дає чітку відповідь на питання «коли?» *(when?)*. Це наші улюблені інструменти для щоденного планування свого життя. Сюди входять слова: «сьогодні» *(today)*, «завтра» *(tomorrow)*, «вчора» *(yesterday)*, «вранці» *(in the morning)*. Слова «завжди» *(always)* та «ніколи» *(never)* також живуть тут.

Третя важлива категорія — це **прислівник способу дії** *(adverb of manner)*. Цей тип пояснює нам, «як» саме ми робимо певну дію. Наприклад: мій друг читає «швидко» *(fast)*, моя мама говорить «повільно» *(slowly)*. Наші нові студенти працюють на уроці дуже «уважно» *(attentively)*. Знання цих трьох термінів допоможе вам розуміти пояснення вчителів.

Як саме утворюється більшість українських прислівників? Вони мають дуже тісний зв'язок із прикметниками. Ви вже знаєте багато різних і корисних прикметників. Тому вам буде дуже легко самостійно створити нові прислівники. Найпростіший спосіб — додати суфікс «-о» або «-е» до основи прикметника. Подивімося на це правило через дуже конкретні приклади.

Візьмемо типовий прикметник «гарний» *(beautiful, good)*. Ми хочемо сказати, як саме людина співає чи малює. Тому ми робимо з нього прислівник: «гарно» *(beautifully)*. Прикметник «швидкий» *(fast, quick)* швидко перетворюється на популярний прислівник «швидко» *(fast, quickly)*. А відомий прикметник «гарячий» *(hot)* за цим правилом стає прислівником «гаряче» *(hotly)*.

Коли ви шукаєте такі слова у великому словнику, ви спочатку бачите прикметник. Потім словник дає вам і форму прислівника. Ці два слова завжди мають граматичний зв'язок. Іноді ви бачите в тексті нове слово із закінченням «-о». Можливо, це нове слово має закінчення «-е». Якщо воно відповідає на питання «як?», це точно типовий прислівник. Завжди пам'ятайте про граматичне скорочення **«присл.»**, коли читаєте словникові статті.

<!-- INJECT_ACTIVITY: fill-in-fill-in-metalanguage -->

## Підсумок

Ось і все! Цей урок був дуже важливим для вашого майбутнього. Тепер ви добре знаєте справжню українську граматичну термінологію. Зробімо невелику перевірку ваших нових знань.

*   Чи можете ви назвати три часи дієслова в українській мові? (Так, це минулий, теперішній і майбутній час).
*   Чи можете ви швидко пояснити різницю між скороченнями «док.» та «недок.»? (Це доконаний і недоконаний вид дієслова).
*   Чи точно ви знаєте, який саме рід означає коротке скорочення «ж.р.»? (Звісно, це жіночий рід).

Якщо ви легко відповіли «так» на ці запитання, ви повністю готові працювати з українськими словниками! 

Для успішного переходу на наступний рівень B1 вам обов'язково потрібно пам'ятати ці десять критичних скорочень:
1. **ім.** — іменник *(noun)*
2. **прикм.** — прикметник *(adjective)*
3. **дієсл.** — дієслово *(verb)*
4. **займ.** — займенник *(pronoun)*
5. **присл.** — прислівник *(adverb)*
6. **ч.р.** — чоловічий рід *(masculine gender)*
7. **ж.р.** — жіночий рід *(feminine gender)*
8. **с.р.** — середній рід *(neuter gender)*
9. **док.** — доконаний вид *(perfective aspect)*
10. **недок.** — недоконаний вид *(imperfective aspect)*

З цими новими знаннями ви зможете самостійно читати будь-які граматичні правила.
</generated_module_content>

**PIPELINE NOTE — Word count: 2434 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 762 words | Not found: 13 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Марк — NOT IN VESUM
  ✗ ать — NOT IN VESUM
  ✗ говор — NOT IN VESUM
  ✗ дієсл — NOT IN VESUM
  ✗ займ — NOT IN VESUM
  ✗ мовч — NOT IN VESUM
  ✗ недок — NOT IN VESUM
  ✗ одн — NOT IN VESUM
  ✗ пиш — NOT IN VESUM
  ✗ прикм — NOT IN VESUM
  ✗ присл — NOT IN VESUM
  ✗ уть — NOT IN VESUM
  ✗ ють — NOT IN VESUM

All 762 other words are confirmed to exist in VESUM.

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
