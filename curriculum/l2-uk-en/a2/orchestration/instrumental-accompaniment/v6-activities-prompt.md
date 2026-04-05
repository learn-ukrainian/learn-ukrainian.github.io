<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/instrumental-accompaniment.yaml` file for module **24: З другом** (a2).

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

- focus: Form the correct Instrumental ending for nouns after з/із/зі
  items: 8
  type: fill-in
- focus: Match Nominative nouns to their Instrumental forms
  items: 8
  type: match-up
- focus: Choose з/із/зі based on the following word
  items: 8
  type: quiz
- focus: Complete cafe dialogue sentences with correct Instrumental forms
  items: 8
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- супутник (companion)
- разом (together)
- компанія (company, group of friends)
- гриби (mushrooms)
required:
- орудний відмінок (instrumental case)
- з (with)
- із (with — before consonant clusters)
- зі (with — before з-, с-, ш-)
- друг (friend (male))
- подруга (friend (female))
- лимон (lemon)
- молоко (milk)
- масло (butter)
- мед (honey)
- сметана (sour cream)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Орудний відмінок: Знайомство (The Instrumental Case: Introduction)

Українська мова має сім різних відмінків. Ми вже добре знаємо шість із них. Сьогодні ми нарешті вивчаємо сьомий і останній великий відмінок у нашій програмі. Це **орудний відмінок** *(Instrumental case)*. Він відповідає на спеціальні питання **Ким?** *(With whom?)* та **Чим?** *(With what?)*. The Instrumental case is absolutely essential for expressing how an action is performed or exactly who accompanies you during that action. It positions a noun as the practical instrument, the means, or the active companion of an activity. Уявіть, що ви робите щось разом із кимось або за допомогою чогось. Саме для цього нам завжди потрібен цей відмінок. Він показує глибокий зв'язок між дією та предметом, який допомагає цю дію виконати.

Найчастіше ми використовуємо орудний відмінок, коли говоримо про компанію. Для цього ми додаємо короткий прийменник **з** *(with)*. Наприклад, ми дуже часто кажемо у повсякденному житті: **«Я гуляю з другом»** *(I am walking with a friend)*. Тут слово **друг** *(friend)* стоїть саме в орудному відмінку. Цей відмінок чудово показує спільну дію двох або більше людей. Ми також використовуємо його, коли говоримо про стосунки між різними предметами. Наприклад: **«Вона живе з батьками»** *(She lives with her parents)* або **«Я п'ю каву з молоком»** *(I drink coffee with milk)*. The preposition 'з' combined with the Instrumental case perfectly captures this everyday relationship of companionship or physical accompaniment. You will use this pattern constantly when planning activities or describing meals.

Дуже важливо не плутати орудний відмінок з іншими відмінками, які ми вже вивчили раніше. Давайте уважно порівняємо дві різні життєві ситуації. Коли ми кажемо **«Я бачу друга»** *(I see a friend)*, ми використовуємо **знахідний відмінок** *(Accusative case)*. Тут людина є прямим об'єктом вашої дії. Але коли ми кажемо **«Я розмовляю з другом»** *(I am talking with a friend)*, ми обов'язково використовуємо орудний відмінок. In English, the word "with" usually signals this specific relationship of doing things together. In Ukrainian, you must always change the ending of the noun to match the case requirements. Ви не можете просто сказати прийменник і залишити слово у звичайному називному відмінку. Орудний відмінок є суворо обов'язковим для таких ситуацій спілкування.

Орудний відмінок має багато дуже різних функцій у нашій мові. Окрім звичайної компанії, він також показує інструмент, яким ми щось робимо. Наприклад: **«Я пишу олівцем»** *(I am writing with a pencil)*. Ми також регулярно використовуємо його, коли говоримо про професії людей: **«Він працює лікарем»** *(He works as a doctor)*. Крім того, він допомагає описати розташування предметів. Ми використовуємо його після слів **під** *(under)* або **над** *(over)*. The Instrumental case is incredibly versatile and you will see it everywhere in the language as you continue learning. Однак сьогодні ми зосередимося лише на одній, найголовнішій темі для початку. Ми будемо детально вивчати супровід та ознаки з прийменником **з**. Це найкорисніший перший крок для розуміння цього відмінка.


## Закінчення орудного відмінка однини (Instrumental Singular Endings)

Ми починаємо вивчати закінчення з чоловічого роду. Найбільша група слів має твердий приголосний звук у кінці. Для таких іменників ми завжди використовуємо закінчення **-ом**. This is the most common and predictable pattern for masculine nouns that end in a hard consonant. The hard consonant remains unchanged, and you simply attach the suffix to the end of the word. Наприклад, якщо ми маємо слово **брат** *(brother)*, воно перетворюється на форму **з братом** *(with a brother)*. Слово **друг** *(friend)* стає **з другом** *(with a friend)*. Ми часто кажемо: «Я йду в кіно з другом». Також слово **стіл** *(table)* отримує закінчення **-ом**: **за столом** *(behind a table)*. Слово **тато** *(dad)* також належить до цієї великої групи, тому ми кажемо **з татом** *(with dad)*.

Друга важлива група чоловічого роду має м'який приголосний або шиплячий звук у кінці. Для таких слів ми повинні використовувати закінчення **-ем**. Soft consonants and sibilant sounds require a softer vowel to follow them. This is why we switch from the hard ending to the soft one. Наприклад, слово **вчитель** *(teacher)* має м'який знак, тому воно стає **з вчителем** *(with a teacher)*. Слово **ніж** *(knife)* закінчується на шиплячий звук, тому ми маємо форму **з ножем** *(with a knife)*. Слово **хлопець** *(boy)* втрачає голосну і стає **з хлопцем** *(with a boy)*. Окрема мала група слів закінчується на звук [й]. Для них ми використовуємо закінчення **-єм**. Наприклад, слово **чай** *(tea)* стає **з чаєм** *(with tea)*. Ім'я **Сергій** *(Serhiy)* перетворюється на **із Сергієм** *(with Serhiy)*, а **трамвай** *(tram)* стає **трамваєм** *(by tram)*.

Тепер ми переходимо до слів жіночого роду. Більшість таких іменників закінчується на тверду літеру «а». Для цієї великої групи ми завжди використовуємо закінчення **-ою**. The feminine ending is very distinctive and sounds melodic in everyday speech. You drop the final vowel and replace it completely with this new suffix. Наприклад, дуже популярне слово **мама** *(mom)* легко стає **з мамою** *(with mom)*. Ми часто кажемо: «Вона розмовляє з мамою». Слово **подруга** *(female friend)* змінюється на **з подругою** *(with a female friend)*. Слово **сестра** *(sister)* отримує нову форму **із сестрою** *(with a sister)*. Навіть звичайне слово **книжка** *(book)* працює за цим правилом і стає **з книжкою** *(with a book)*. Ця група є найпростішою для запам'ятовування, тому що вона дуже велика і регулярна.

Деякі слова жіночого роду закінчуються на м'який приголосний звук або шиплячий звук. Для цих іменників ми використовуємо закінчення **-ею**. Just like with the masculine nouns, soft stems and sibilant sounds in feminine nouns require a softer ending. We replace the final vowel with the new suffix. Наприклад, слово **земля** *(earth, land)* стає **над землею** *(above the earth)*. Слово **душа** *(soul)* має шиплячий звук і змінюється на **з душею** *(with a soul)*. Слово **каша** *(porridge)* перетворюється на **з кашею** *(with porridge)*. Якщо слово закінчується на звук [й] перед буквою «я», ми повинні використовувати закінчення **-єю**. Наприклад, гарне слово **надія** *(hope)* стає **з надією** *(with hope)*. Або популярне ім'я **Марія** *(Maria)* легко змінюється на форму **з Марією** *(with Maria)*.

Слова середнього роду також мають свої чіткі правила. Вони дуже схожі на правила чоловічого роду. Якщо слово середнього роду закінчується на літеру «о», ми додаємо закінчення **-ом**. This means that neuter words ending in this vowel behave exactly like hard-stem masculine nouns. Наприклад, слово **вікно** *(window)* стає **за вікном** *(behind the window)*. Ми часто використовуємо слово **молоко** *(milk)*, яке змінюється на **з молоком** *(with milk)*: «Я люблю каву з молоком». Слово **масло** *(butter)* також стає **з маслом** *(with butter)*. Якщо слово закінчується на «е» або «я», ми використовуємо м'які закінчення **-ем** або **-ям**. Наприклад, слово **море** *(sea)* перетворюється на форму **за морем** *(beyond the sea)*. Цікаве слово **ім'я** *(name)* отримує закінчення **-ям** і стає **з ім'ям** *(with a name)*.

Давайте підсумуємо ці правила. У підручниках для українських школярів учні завжди спочатку визначають останній звук слова. The crucial step is categorizing the final sound of the stem before applying the case ending. If the sound is hard, you choose the hard suffix. If it is soft, sibilant, or ends in a 'й' sound, you must select the corresponding soft suffix. Це дуже логічна та струнка система.

<!-- INJECT_ACTIVITY: match-up, Match Nominative nouns to their Instrumental forms -->
<!-- INJECT_ACTIVITY: fill-in, Form the correct Instrumental ending for nouns after з/із/зі in short phrases -->


## З/із/зі + орудний відмінок (Z/iz/zi + Instrumental)

Орудний відмінок найчастіше показує супровід. Ми використовуємо прийменник **з** *(with)*, щоб сказати, **з ким** *(with whom)* ми щось робимо. Наприклад, ми дуже рідко буваємо абсолютно самі. Ми часто проводимо час у компанії інших людей. Ви можете **іти з сестрою** *(to go with a sister)* у кіно або в театр. Ви можете **обідати з колегою** *(to have lunch with a colleague)* в затишному кафе. Кожна мати любить **грати з дитиною** *(to play with a child)* у зеленому парку. When expressing accompaniment, the preposition is followed immediately by the noun or pronoun in the Instrumental case. Це дуже популярна конструкція в українській мові. Якщо ви говорите про себе, ви повинні казати **зі мною** *(with me)*. Наприклад: «Мій найкращий друг зараз іде туди зі мною». Завжди пам'ятайте про це просте питання: «Ти робиш це з ким?». Відповідь завжди потребує орудного відмінка.

Друге надзвичайно важливе значення — це ознака предмета або інгредієнт. Ми використовуємо прийменник **з**, щоб відповісти на питання **з чим?** *(with what?)*. Ця конструкція є дуже корисною, коли ми говоримо про їжу та улюблені напої. The Instrumental case here acts as a descriptive attribute, showing what a specific dish or drink contains. Наприклад, багато людей щоранку п'ють гарячу **каву з цукром** *(coffee with sugar)*. На швидкий сніданок українці часто їдять свіжий **бутерброд з сиром** *(sandwich with cheese)*. Коли ми хворіємо восени, ми любимо пити **чай з медом** *(tea with honey)*. А ввечері на вихідних ми можемо замовити велику **піцу з грибами** *(pizza with mushrooms)*. У цих щоденних ситуаціях орудний відмінок показує важливу складову частину нашої страви. Ми часто кажемо: «Я хочу салат з помідорами». Або: «Вона готує смачний суп з м'ясом».

В українській мові ми маємо три різні варіанти цього прийменника: **з**, **із** та **зі**. Це правило існує виключно для милозвучності. Збіг багатьох приголосних звуків може дуже сильно ускладнювати вимову слів. Ukrainian phonetics strongly favors euphony, meaning sentences should flow easily without harsh or awkward consonant clusters. Ми завжди використовуємо варіант **з** перед словами, які починаються на будь-який голосний звук. Ми також використовуємо варіант **з** перед багатьма приголосними звуками. Наприклад: **з другом** *(with a friend)*, **з молоком** *(with milk)*. Але якщо наступне слово починається на кілька приголосних підряд, ми використовуємо варіант **із**. Наприклад, ми правильно кажемо **із сестрою** *(with a sister)* або **із братом** *(with a brother)*. Це допомагає зробити нашу вимову плавною та дуже приємною для слуху. Українці завжди уникають важкого збігу приголосних під час розмови.

Третій цікавий варіант — це коротка форма **зі**. Ми використовуємо цей варіант перед словами, які починаються на букви «з», «с» або «ш». Це особливо важливо, якщо далі йде ще один приголосний звук. This specific phonetic rule is absolutely mandatory because pronouncing two similar sibilant sounds together is physically difficult and interrupts the natural flow. Наприклад, ми правильно кажемо **зі сметаною** *(with sour cream)*. Щодня діти радісно повертаються **зі школи** *(from school)*. Як ми вже добре знаємо, займенник «я» також має форму **зі мною** *(with me)*. Ми також беремо нову книжку **зі столу** *(from the table)*. Милозвучність є базовим і головним правилом української граматики та фонетики. Ви завжди повинні відчувати цей природний мовний ритм. Якщо вам важко вимовити слово з прийменником **з**, спробуйте інший варіант. Можливо, вам потрібна мелодійна форма **із** або **зі**.

<!-- INJECT_ACTIVITY: quiz, Choose the correct variant (з/із/зі) based on the following noun (e.g., ___ сметаною, ___ мамою, ___ другом) -->


## Практика: З ким? З чим? (Practice: With Whom? With What?)

Зараз ми подивимося, як українці використовують орудний відмінок у реальному житті. Уявіть, що ви плануєте відпочинок на природі. Вам потрібно знати, хто прийде і що ці люди будуть їсти. Це ідеальна ситуація для орудного відмінка. Прочитайте цей розгорнутий діалог про вихідні.

> — **Максим:** Привіт усім! Ми їдемо на пікнік у суботу. З ким ти прийдеш, Олено?
> — **Олена:** Я прийду **з Олегом** *(with Oleh)* та **з молодшим братом** *(with a younger brother)*. А ти з ким будеш?
> — **Максим:** Я буду **зі своєю новою подругою** *(with my new girlfriend)*. Що ми будемо їсти на природі?
> — **Олена:** Я вдома зроблю смачні **бутерброди з шинкою та сиром** *(sandwiches with ham and cheese)*.
> — **Максим:** Це просто чудово! А я куплю велику **піцу з грибами** *(pizza with mushrooms)* та м'ясом.
> — **Олена:** Добре. А хто з друзів візьме напої? Нам потрібна вода та різні соки.
> — **Максим:** Наш друг Ігор принесе гарячий **чай з лимоном** *(tea with lemon)* у великому термосі.
> — **Олена:** Супер. Тоді я ще візьму солодку **каву з молоком** *(coffee with milk)*.

У цій розмові друзі постійно використовують прийменники «з» та «зі». Вони говорять про людей та про їжу. Зверніть увагу на закінчення іменників чоловічого та жіночого роду. 

In daily conversations, people often ask about your social circle and daily routines. Найчастіше ми чуємо просте питання: «**З ким ти живеш?**» *(Who do you live with?)*. Або люди цікавляться: «**З ким ти зустрічаєшся?**» *(Who are you dating?)*. Щоб правильно відповісти на ці запитання, ви завжди повинні використовувати орудний відмінок. 

Наприклад, студент може просто сказати: «Я живу **з другом**» *(I live with a friend)*. Українці часто кажуть: «Я живу **з батьком і з мамою**» *(I live with father and with mother)*. Діти зазвичай живуть **з батьками** *(with parents)*. 

The verb **зустрічатися** *(to meet / to date)* strongly requires the Instrumental case. Ви можете зустрічатися **з новим колегою** *(with a new colleague)* біля офісу. Або ви можете зустрічатися **з дівчиною** *(with a girlfriend)* на романтичній вечері. 

Інше популярне дієслово для щоденного спілкування — це **розмовляти** *(to talk)*. Ми часто розмовляємо **з братом** *(with a brother)* по телефону. Суворий учитель серйозно розмовляє **з учнем** *(with a student)* на уроці. 

When you agree with someone, you also use this specific case. Ми кажемо: «Я повністю згоден **з тобою**» *(I completely agree with you)*. Якщо ви підтримуєте ідею колеги, ви погоджуєтеся **з його думкою** *(with his opinion)*. Ці прості фрази роблять вашу українську мову дуже природною. Спробуйте запам'ятати ці базові дієслова: жити, зустрічатися, розмовляти, погоджуватися. Вони завжди працюють у постійній парі з орудним відмінком. 

Ordering food in a restaurant or cafe is another common scenario for the Instrumental case. Коли ми замовляємо страви або напої, ми часто використовуємо прийменник «з». Ви приходите в затишне кафе і читаєте меню. Офіціант може запитати вас: «Що ви будете пити?». Ви можете відповісти: «Мені, будь ласка, чорний **чай з медом** *(black tea with honey)*». Ваш друг може сказати: «А я хочу **каву зі згущеним молоком** *(coffee with condensed milk)*». А на десерт ви кажете: «Дайте мені **млинці з сиром** *(pancakes with cottage cheese)*». Як бачите, орудний відмінок є надзвичайно корисним для щоденного комфортного життя.

<!-- INJECT_ACTIVITY: fill-in, Complete cafe dialogue sentences where friends order drinks and snacks with specific ingredients using correct Instrumental forms, 8 items -->


## Підсумок

Орудний відмінок — це дуже важливий інструмент для щоденного спілкування. Ми використовуємо його, щоб говорити про супровід або ознаки предметів. The Instrumental case answers the questions «з ким?» *(with whom?)* and «з чим?» *(with what?)*.

Давайте згадаємо головні закінчення. Masculine and neuter nouns take the endings **-ом**, **-ем** or **-єм**. Наприклад: **з братом** *(with a brother)*, **з товаришем** *(with a friend)*, **з молоком** *(with milk)*. Feminine nouns use the endings **-ою**, **-ею** or **-єю**. Наприклад: **з сестрою** *(with a sister)*, **з душею** *(with a soul)*.

Також ми вивчили три форми прийменника: **з**, **із** та **зі**. We choose the form based on the first letters of the next word to make pronunciation easy.

Тепер перевірте свої знання. Дайте відповіді на ці запитання:
1. Як сказати українською «with me»? Правильно: **зі мною**.
2. Яке закінчення має слово **друг** *(friend)* у фразі «with a friend»? Відповідь: **-ом** (**з другом**).
3. Коли ми використовуємо прийменник **зі** замість **з**? Відповідь: перед словами, які починаються на звуки з, с, ш (наприклад, **зі сметаною** *(with sour cream)*).

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: instrumental-accompaniment
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

**Level: A2 (Module 24/60) — ELEMENTARY**

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
