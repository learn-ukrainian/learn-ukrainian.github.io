<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/plural-other-cases.yaml` file for module **34: З друзями, для дітей** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-plural-cases -->`
- `<!-- INJECT_ACTIVITY: fill-in-plural-forms-focus-put-the-noun-in-parentheses-into-the-correct-plural-case-dat-or-instr-based-on-context -->`
- `<!-- INJECT_ACTIVITY: quiz-preposition-case-focus-choose-the-correct-preposition-and-plural-case-ending-to-complete-the-sentence -->`
- `<!-- INJECT_ACTIVITY: error-correction-plural-focus-identify-and-fix-incorrect-plural-case-endings-in-a-short-text-about-a-trip -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the noun into the correct plural case (Dat., Instr., or Loc.) based on
    the preposition or verb in the sentence
  items: 8
  type: fill-in
- focus: Match plural noun forms with the correct case label (Dat., Instr., Loc.)
  items: 8
  type: match-up
- focus: Choose the correct preposition + plural case combination to complete a sentence
  items: 8
  type: quiz
- focus: Fix incorrect case endings in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- радити (to advise)
- пояснювати (to explain)
- полиця (shelf)
- прикрашати (to decorate)
required:
- давальний відмінок (dative case)
- орудний відмінок (instrumental case)
- місцевий відмінок (locative case)
- допомагати (to help)
- дякувати (to thank)
- подарунок (gift)
- квіти (flowers)
- діти (children)
- люди (people)
- заняття (class, lesson)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Давальний множини: Кому? (Dative Plural: To Whom?)

Сьогодні ми детально плануємо велику шкільну екскурсію. Це завжди дуже важливий день для всіх нас. Прочитайте цю коротку розмову уважно. Зверніть увагу на спеціальні слова, які відповідають на запитання «кому?».
> — **Вчитель:** Слухайте уважно, **діти** *(children)*! Я зараз розповім **студентам** *(to students)* і **учням** *(to pupils)* новий план нашої цікавої подорожі.
> — **Оксана:** Куди ми їдемо завтра вранці?
> — **Вчитель:** Ми їдемо високо в гори. Спочатку ми напишемо **батькам** *(to parents)* коротке текстове повідомлення. Ми повинні пояснити **дорослим** *(to adults)* наші строгі правила.
> — **Тарас:** А що ми дамо **друзям** *(to friends)* після поїздки додому?
> — **Вчитель:** Ми обов'язково купимо їм гарні сувеніри. Потім ми щиро подякуємо **водіям** *(to drivers)* за велику допомогу в дорозі.

The Dative case in the plural is incredibly regular. You use this specific case to indicate the recipient of an action, answering the question «кому?» (to whom?) or «чому?» (to what?). Unlike the singular forms, plural nouns do not care about grammatical gender here. Masculine, feminine, and neuter nouns all follow the exact same universal pattern.
Якщо слово має твердий приголосний звук в кінці основи, ми завжди додаємо закінчення **-ам** *(-am)*.
Наприклад, це такі відомі слова як «студент», «місто» та «книжка». У множині вони мають прості форми **студентам** *(to students)*, **містам** *(to cities)*, та **книжкам** *(to books)*.
Якщо слово має м'який приголосний звук, ми тоді використовуємо закінчення **-ям** *(-yam)*.
Подивіться на популярні слова «друг», «море» та «пісня». У давальному відмінку множини це будуть форми **друзям** *(to friends)*, **морям** *(to seas)*, та **пісням** *(to songs)*.
Слово «діти» є маленьким винятком. Ми кажемо **дітям** *(to children)*.
Слово «люди» також має м'яке закінчення. Ми завжди кажемо **людям** *(to people)*.

Why is this specific grammar case so pleasant and easy to learn? Let us closely compare the Dative plural with the Genitive plural that you already know. The Genitive case in the plural has many complex and sometimes unpredictable rules. It uses completely different endings like «-ів» or «-ей», and sometimes it drops the ending entirely, creating a tricky zero ending. This immense complexity can be very frustrating for language learners.
Давальний відмінок множини є дуже простим і надзвичайно логічним. Одне коротке універсальне правило чудово працює майже для всіх можливих слів в українській мові. Ви просто уважно дивитеся на останній звук основи іменника. Це робить давальний відмінок найлегшим для швидкого і легкого вивчення у множині. Вам зовсім не потрібно запам'ятовувати довгі і складні таблиці винятків.

We frequently use the Dative plural with specific communicative verbs to express human interaction. Ці важливі дієслова завжди вимагають давального відмінка після себе.
Запам'ятайте такі корисні дієслова: **давати** *(to give)*, **допомагати** *(to help)*, **дякувати** *(to thank)*, **телефонувати** *(to call)*, та **пояснювати** *(to explain)*.
Ось кілька хороших практичних прикладів для вас.
Я даю гарні подарунки моїм друзям.
Вчитель чітко пояснює нові правила студентам.
Хороші батьки часто допомагають малим дітям робити складне домашнє завдання.
Я регулярно телефоную моїм **колегам** *(to colleagues)* кожного робочого ранку.
Ми всі щиро дякуємо **лікарям** *(to doctors)* за їхню важку щоденну роботу.
Також ми досить часто використовуємо дієслово **радити** *(to advise)*.
Я завжди раджу іноземним **туристам** *(to tourists)* відвідати центр міста.

Some nouns in the Ukrainian language exist exclusively in the plural form. Fortunately, these interesting words strictly follow the exact same predictable Dative plural rule.
Ми просто і легко додаємо знайомі закінчення «-ам» або «-ям» до їхньої базової основи.
Подивіться уважно на ці популярні слова в контексті.
Цим гарним **окулярам** *(to glasses)* вже багато років.
Я ніколи в житті не довіряю великим **грошам** *(to money)*.
Цим старим синім **штанам** *(to pants)* потрібен терміновий ремонт сьогодні.
Іноземні туристи зазвичай радіють українським **Карпатам** *(rejoice at the Carpathians)* влітку.

<!-- INJECT_ACTIVITY: match-up-plural-cases -->


## Орудний множини: З ким? Чим? (Instrumental Plural)

Тепер ми вивчаємо орудний відмінок множини. Цей відмінок має дуже важливу функцію в українській мові. The Instrumental plural answers the core questions «з ким?» (with whom?) and «чим?» (with what?). We use it constantly to describe the people we do things with or the exact tools we use for our tasks. Цей відмінок також є надзвичайно регулярним і логічним у множині. Більшість слів мають лише два можливі закінчення: «-ами» або «-ями». Граматичний рід тут зовсім не має значення. Усі слова працюють за одним загальним правилом. Якщо слово має твердий приголосний звук в кінці основи, ми завжди використовуємо закінчення «-ами». Це дуже поширений і простий варіант для багатьох іменників. Наприклад, ми кажемо: **братами** *(with brothers)*, **жінками** *(with women)*, **вікнами** *(with windows)*, **містами** *(with cities)*. Зверніть увагу на ці типові форми. Якщо основа слова закінчується на м'який приголосний звук, тоді ми завжди додаємо закінчення «-ями». Це робить вимову більш плавною і приємною. Подивіться на такі приклади: **вчителями** *(with teachers)*, **вулицями** *(by streets)*, **обличчями** *(with faces)*, **морями** *(with seas)*. Як бачите, правило є дуже стабільним для всіх іменників.

Ukrainian has a special, historically preserved ending for the Instrumental plural. Деякі дуже популярні слова мають коротке закінчення «-ми». Це не якийсь дивний виняток, а давня і красива українська форма. In modern Russian, this specific short ending is mostly archaic, but in standard Ukrainian, it is an everyday, living reality that you must quickly learn. Найважливіші слова з цим закінченням — це **дітьми** *(with children)* та **людьми** *(with people)*. Ми постійно чуємо і говоримо ці слова кожного дня у різних ситуаціях. Також ми часто використовуємо такі цікаві форми як **кіньми** *(with horses)*, **гістьми** *(with guests)* та **чобітьми** *(with boots)*. Для слова «гості» також існує варіант **гостями** *(with guests)*. Він теж є абсолютно правильним у сучасній мові. Слово «гроші» має дві популярні форми в орудному відмінку. Ви можете сказати **грішми** *(with money)* або **грошима** *(with money)*. Обидві ці форми є стандартними і дуже часто звучать у повсякденних розмовах. Запам'ятайте цю невелику групу важливих слів. Вони роблять вашу українську мову дуже автентичною, багатою і природною.

Найчастіше ми використовуємо орудний відмінок множини з прийменником **з** *(with)* або **із** *(with)*. Цей прийменник завжди показує компанію або спільну дію кількох людей. Social interaction is the absolute most common context for this grammatical case. Ми дуже часто кажемо, що ми робимо щось разом з іншими. Наприклад: я люблю **зустрічатися** *(to meet)* з друзями на вихідних у парку. Вона довго розмовляла з **колегами** *(with colleagues)* про новий цікавий проєкт. Наші маленькі діти просто обожнюють гратися з **котами** *(with cats)* у дворі біля дому. The choice between the short preposition «з» and its longer variant «із» depends entirely on vowel harmony and pronunciation rules. The main goal is to make the sentence flow easily without awkward or heavy consonant clusters. Ми завжди використовуємо «із», коли наступне слово починається з важкої групи приголосних звуків. Наприклад, ми кажемо «із студентами» або «із братами», щоб наша мова звучала мелодійно. Правильна вимова є дуже важливою частиною гарної української мови.

Ми також дуже активно використовуємо орудний відмінок без жодних прийменників. У цьому важливому випадку він показує інструмент, конкретний засіб або спосіб дії. The noun itself directly becomes the tool or the means by which a specific action is performed. Це відповідає на дуже просте питання «чим?». Наприклад, маленькі учні у школі часто пишуть **олівцями** *(with pencils)* або малюють яскравими **фарбами** *(with paints)*. В азійському ресторані ми зазвичай їмо смачну їжу **паличками** *(with chopsticks)*. На великі свята ми традиційно прикрашаємо наш дім гарними весняними **квітами** *(with flowers)*. Ми також регулярно використовуємо орудний відмінок для опису різного транспорту у множині. Сьогодні ми всі разом їдемо на довгу екскурсію великими **автобусами** *(by buses)*. Наш молодий вчитель радісно каже: ми їдемо швидко, безпечно і дуже комфортно. Ці сучасні автобуси є нашим надійним засобом пересування сьогодні. Отже, орудний відмінок множини — це ваш головний інструмент для опису засобів і матеріалів.

<!-- INJECT_ACTIVITY: fill-in-plural-forms-focus-put-the-noun-in-parentheses-into-the-correct-plural-case-dat-or-instr-based-on-context -->


## Місцевий множини: Де? На чому? (Locative Plural)

Тепер давайте поговоримо про місця та локації. Де ми часто буваємо разом з іншими людьми? Для цього ми постійно використовуємо місцевий відмінок множини. Цей відмінок завжди показує конкретну локацію, місце роботи або відпочинку. The Locative plural is incredibly regular and easy to learn. There are only two simple endings to remember for all nouns: **-ах** after a hard consonant, and **-ях** after a soft consonant. You will never see a zero-ending here. Головне граматичне правило є дуже суворим, але простим. Місцевий відмінок ніколи не працює без прийменника. Ми обов'язково повинні використовувати короткі слова «в/у» або «на». Just like in the singular form, the Locative plural absolutely requires a preposition to function in a sentence. You cannot use it alone. Наприклад, взимку люди часто відпочивають у сучасних **театрах** *(in theaters)*. Вони також багато гуляють у великих міських **парках** *(in parks)*. Важливі робочі документи завжди лежать на дерев'яних **полицях** *(on shelves)* у кабінеті. Ми часто читаємо цікаві новини у довгих електронних **листах** *(in letters)*. Студенти уважно слухають свого молодого викладача на вечірніх **заняттях** *(at classes)*. Це стабільне правило працює абсолютно для всіх українських слів.

В українській мові є ще один дуже важливий прийменник для опису локації. Це популярний прийменник «по». Ми використовуємо його, коли ми активно рухаємося або довго подорожуємо різними місцями. When you talk about moving across a surface or distributing an action over multiple locations, standard Ukrainian specifically pairs the preposition «по» with the Locative plural. This is a crucial point of precision and decolonization, as Russian heavily uses the Dative case for this exact construction. In authentic Ukrainian, movement across surfaces is always expressed with the Locative. Це означає, що ми завжди і впевнено додаємо закінчення «-ах» або «-ях» після слова «по». Наприклад, ми дуже любимо **гуляти по парках** *(to walk around parks)* восени. Наші іноземні туристи часто люблять **ходити по магазинах** *(to walk around shops)* у старому центрі міста. Вони щиро мріють **подорожувати по країнах** *(to travel around countries)* Європи наступного літа. Маленькі діти дуже люблять весело бігати по глибоких калюжах після сильного дощу. Ця граматична форма завжди звучить дуже природно, традиційно і правильно.

Ми також маємо деякі популярні фрази, які завжди традиційно використовують місцевий відмінок множини. Їх потрібно просто добре запам'ятати як готові блоки. Наприклад, дуже багато українців люблять активно відпочивати в **Карпатах** *(in the Carpathians)*. Це високі і дуже красиві гори на заході нашої країни. Школярі часто їздять туди на зимових **канікулах** *(on holidays)*. Також ми традиційно зустрічаємося з родиною на **вихідних** *(on weekends)*. Ми можемо прочитати про ці давні українські традиції на **сторінках** *(on the pages)* цікавих історичних книжок або у журналах. Зауважте, що всі ці важливі слова завжди мають стабільну форму місцевого відмінка множини у таких стандартних життєвих ситуаціях.

Наприкінці давайте уважно порівняємо два різні відмінки, які мають дуже схожі форми. Це давальний і місцевий відмінки множини. Вони мають абсолютно однакову основу слова, але різну останню літеру. It is extremely important for your fluency to accurately distinguish between the Dative plural ending «-ам» and the Locative plural ending «-ах». They look incredibly similar on paper, but they answer completely different questions and serve entirely different grammatical purposes in a sentence. Давальний відмінок завжди відповідає на запитання «кому?». Наприклад, я часто даю гарні подарунки моїм найкращим **друзям** *(to friends)*. Ми з радістю допомагаємо українським **містам** *(to cities)*. А місцевий відмінок відповідає на запитання «на кому?» або «на чому?». Наприклад, на моїх **друзях** *(on friends)* є дуже гарний новий зимовий одяг. Люди зараз живуть у великих **містах** *(in cities)*. Ми чітко бачимо, що літера «м» показує напрямок дії до людини, а літера «х» показує конкретну локацію. Закінчення «-ах» і «-ях» завжди працюють виключно для місця.

<!-- INJECT_ACTIVITY: quiz-preposition-case-focus-choose-the-correct-preposition-and-plural-case-ending-to-complete-the-sentence -->


## Три відмінки разом: Практика (Synthesis)

Завтра у нашому місті буде чудове свято. Ми активно готуємося до нього вже кілька днів. Зранку ми йдемо в магазин і купуємо різні **подарунки** *(gifts)* **дітям** *(to children)*. Вони дуже люблять сюрпризи. Потім ми разом ідемо до школи. Там ми прикрашаємо простору залу яскравими **квітами** *(with flowers)* та дитячими **малюнками** *(with drawings)*. Це дуже цікава і творча робота. Свято буде у різних **школах** *(in schools)* і дитячих **садках** *(in kindergartens)* нашого регіону. Багато людей прийдуть туди зі своїми найкращими **друзями** *(with friends)*. Ми також щиро радіємо новим **гостям** *(to guests)*. Ввечері ми всі будемо танцювати і співати українські пісні. На цих традиційних **святах** *(at holidays)* завжди дуже весело і тепло. Ми також даємо смачні солодощі всім маленьким **учасникам** *(to participants)*. Наші вчителі завжди допомагають нам з цими важливими **справами** *(with matters)*.

> — **Марія:** Привіт! Ти пам'ятаєш, що завтра день народження Івана? Ми плануємо велике свято.
> — **Олег:** Привіт! Так, звісно. Я пам'ятаю про це. **Кому** *(to whom)* ми ще даруємо подарунки на цьому тижні?
> — **Марія:** Тільки йому і його **батькам** *(to parents)*. А **з ким** *(with whom)* ти йдеш на вечірку завтра?
> — **Олег:** Я йду з моїми старшими **братами** *(with brothers)*. Вони теж хочуть привітати Івана. А ти?
> — **Марія:** Я буду з нашими шкільними **подругами** *(with female friends)*.
> — **Олег:** Супер! А **в яких** *(in which)* кафе ми можемо зручно сісти після свята?
> — **Марія:** Ми можемо посидіти у нових **кав'ярнях** *(in cafes)* у центрі міста.
> — **Олег:** Чудова ідея! Тоді до завтра!

This is a perfect time to summarize these three important cases. You have seen that they are incredibly regular and predictable in the plural form. Unlike the Genitive plural, which has many complex exceptions, the Dative, Instrumental, and Locative plural cases follow very strict and simple patterns. Here is a quick reference table for you to easily remember these essential plural endings:

| Відмінок | Питання | Закінчення | Приклад |
| :--- | :--- | :--- | :--- |
| **Давальний** (Dative) | кому? чому? | -ам, -ям | міст**ам**, друзя**м** |
| **Орудний** (Instrumental) | ким? чим? | -ами, -ями | міст**ами**, друзя**ми** |
| **Місцевий** (Locative) | на/у/по кому? чому? | -ах, -ях | у міст**ах**, на друзя**х** |

Once you know the basic plural form of a Ukrainian noun, you can confidently add these stable endings to it. They are universally the most reliable and consistent plural endings in the entire language. 

<!-- INJECT_ACTIVITY: error-correction-plural-focus-identify-and-fix-incorrect-plural-case-endings-in-a-short-text-about-a-trip -->


## Підсумок

Ми вивчили три важливі відмінки для множини. Вони дуже логічні і мають стабільні закінчення. Це робить їх легкими для запам'ятовування.

First, the Dative plural indicates the recipient of an action. Nouns in this case always end in «-ам» or «-ям». Ми даємо подарунки **дітям** *(to children)* і **друзям** *(to friends)*.

Second, the Instrumental plural is used to express "with whom" or "by what means". The standard endings are «-ами» or «-ями». Ми гуляємо з **братами** *(with brothers)* і пишемо **олівцями** *(with pencils)*. Remember the important exceptions that take the «-ми» ending, like **дітьми** *(with children)* or **людьми** *(with people)*.

Third, the Locative plural is exclusively for location. It always requires a preposition like «у», «в», «на», or «по» and takes the endings «-ах» or «-ях». Ми відпочиваємо в **горах** *(in the mountains)*.

Давайте перевіримо ваші знання. Як сказати "with friends" українською мовою? Правильно, це буде «з друзями». Яке закінчення ми використовуємо у місцевому відмінку множини? Це закінчення «-ах» або «-ях». Коли ми використовуємо слово «дітьми»? Ми використовуємо цю форму в орудному відмінку.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: plural-other-cases
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

**Level: A2 (Module 34/60) — ELEMENTARY**

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
