<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/metalanguage-verbs-and-time.yaml` file for module **62: Дія і час** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-verb-terms -->`
- `<!-- INJECT_ACTIVITY: group-sort-verb-tense -->`
- `<!-- INJECT_ACTIVITY: quiz-quiz-dictionary-literacy -->`
- `<!-- INJECT_ACTIVITY: fill-in-fill-in-metalanguage -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match verb category terms to their definitions
  items: 8
  type: match-up
- focus: Read a dictionary entry and answer questions about its grammatical info
  items: 8
  type: quiz
- focus: Sort verb forms by час (минулий, теперішній, майбутній)
  items: 8
  type: group-sort
- focus: Complete sentences about verbs using Ukrainian metalanguage terms
  items: 8
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дійсний спосіб (indicative mood)
- наказовий спосіб (imperative mood)
- умовний спосіб (conditional mood — label only, production is B1)
- скорочення (abbreviation)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
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
| **ч. р.** | чоловічий рід | *masculine gender* |
| **ж. р.** | жіночий рід | *feminine gender* |
| **с. р.** | середній рід | *neuter gender* |
| **одн.** | однина | *singular* |
| **мн.** | множина | *plural* |
| **док.** | доконаний вид | *perfective aspect* |
| **недок.** | недоконаний вид | *imperfective aspect* |

Вивчіть ці скорочення напам'ять. Вони — ваш надійний ключ до успішного самостійного навчання. Коли ви знаєте, що нове слово має позначку «ж. р.», ви точно знаєте, що треба сказати «гарна», а не «гарний». Якщо ви бачите позначку «мн.», це чітко означає, що слово використовується тільки у множині. Хороші приклади таких слів — це «окуляри» *(glasses)*, «гроші» *(money)* або «ножиці» *(scissors)*.

Давайте разом попрактикуємося читати ці коди. Візьмемо два реальні приклади з популярного онлайн-словника.

Перший приклад — це слово «книга». У словнику ми бачимо такий запис: **книга** (ім., ж. р., одн.). Що це означає для нас? Ми відразу розуміємо, що це іменник жіночого роду в однині. Тому ми можемо правильно сказати «моя нова книга» і використовувати її як підмет у реченні. Ми знаємо, які закінчення треба обрати.

Другий приклад — це слово «зробити». Словник каже нам: **зробити** (дієсл., док.). Цей короткий код дає студенту надзвичайно важливу інформацію! Це дієслово доконаного виду. Що це означає на практиці для іноземця? Це означає, що дія має фінальний результат. Але найголовніше правило — ми знаємо, що це дієслово ніколи не має форм теперішнього часу! Ви абсолютно не можете сказати «я зроблю це зараз», якщо ви маєте на увазі процес, який зараз триває. Форма «я зроблю» — це вже проста форма майбутнього часу. Тому цей маленький граматичний блок допомагає вам обрати правильний час для вашого речення і говорити природно.

<!-- INJECT_ACTIVITY: quiz-quiz-dictionary-literacy -->


## Прислівник: види та приклади

Тепер поговоримо про ще одну важливу частину мови в українській граматиці. Це **прислівник** *(adverb)*. Ви вже добре знаєте, що іменники, прикметники та дієслова постійно змінюють закінчення. Вони залежать від контексту. Але прислівник — це унікальне, абсолютно **незмінне слово** *(unchangeable word)*. Що це означає для вас як для студента? Це означає, що прислівник ніколи не має відмінків. Він не має родів, чисел або осіб. Він завжди залишається у своїй початковій словниковій формі. Для вивчення мови це дуже гарна новина! Вам не потрібно думати про складні закінчення. Ви просто берете прислівник і використовуєте його у своєму реченні. Наприклад, слово «добре» *(well)* завжди залишається словом «добре». Це правило діє незалежно від того, хто виконує дію. Але є один невеликий нюанс. Прислівники ніколи не змінюються. Тому іноді студентам важко зрозуміти їхню граматичну роль у тексті. Проте у будь-якому словнику ви завжди знайдете ці слова. Вони будуть мати коротку позначку **«присл.»** *(adv.)*.

В українській мові всі прислівники мають свої специфічні категорії. Вони показують нам різноманітні обставини, за яких відбувається дія. Подивімося детально на три найважливіші види прислівників. Ви вже дуже добре знаєте ці слова. Ви постійно використовуєте їх на практиці. Ми просто дамо їм офіційні граматичні імена. 

Перша базова група — це **прислівник місця** *(adverb of place)*. Цей вид завжди відповідає на питання «де?» *(where?)* або «куди?» *(where to?)*. До цієї групи належать такі слова: «тут» *(here)*, «там» *(there)*, «далеко» *(far)*. Також сюди входять слова «близько» *(near)* та «всюди» *(everywhere)*.

Друга велика і популярна група — це **прислівник часу** *(adverb of time)*. Він дає чітку відповідь на питання «коли?» *(when?)*. Це наші улюблені інструменти для щоденного планування свого життя. Сюди входять слова: «сьогодні» *(today)*, «завтра» *(tomorrow)*, «вчора» *(yesterday)*, «вранці» *(in the morning)*. Слова «завжди» *(always)* та «ніколи» *(never)* також живуть тут.

Третя важлива категорія — це **прислівник способу дії** *(adverb of manner)*. Цей тип пояснює нам, «як» саме ми робимо певну дію. Наприклад: мій друг читає «швидко» *(fast)*, моя мама говорить «повільно» *(slowly)*. Наші нові студенти працюють на уроці дуже «уважно» *(attentively)*. Знання цих трьох термінів допоможе вам розуміти пояснення вчителів.

Як саме утворюється більшість українських прислівників? Вони мають дуже тісний зв'язок із прикметниками. Ви вже знаєте багато різних і корисних прикметників. Тому вам буде дуже легко самостійно створити нові прислівники. Найпростіший спосіб — додати суфікс «-о» або «-е» до основи прикметника. Подивімося на це правило через дуже конкретні приклади.

Візьмемо типовий прикметник «гарний» *(beautiful, good)*. Ми хочемо сказати, як саме людина співає чи малює. Тому ми робимо з нього прислівник: «гарно» *(beautifully)*. Прикметник «швидкий» *(fast, quick)* швидко перетворюється на популярний прислівник «швидко» *(fast, quickly)*. А відомий прикметник «гарячий» *(hot)* за цим правилом стає прислівником «гаряче» *(hotly)*.

Коли ви шукаєте такі слова у великому словнику, ви спочатку бачите прикметник. Потім словник дає вам і форму прислівника. Ці два слова завжди мають граматичний зв'язок. Іноді ви бачите в тексті абсолютно нове слово із закінченням «-о». Можливо, це нове слово має закінчення «-е». Якщо воно відповідає на питання «як?», це точно типовий прислівник. Завжди пам'ятайте про граматичне скорочення **«присл.»**, коли читаєте словникові статті.

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

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: metalanguage-verbs-and-time
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

**Level: A2 (Module 62/60) — ELEMENTARY**

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

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
