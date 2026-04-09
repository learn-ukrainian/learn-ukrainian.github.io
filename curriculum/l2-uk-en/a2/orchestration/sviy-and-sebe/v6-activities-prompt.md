<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/sviy-and-sebe.yaml` file for module **56: Своє та себе** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-possessive-choice -->`
- `<!-- INJECT_ACTIVITY: true-false-sviy-grammar -->`
- `<!-- INJECT_ACTIVITY: fill-in-sebe-cases -->`
- `<!-- INJECT_ACTIVITY: match-up-sebe-idioms -->`
- `<!-- INJECT_ACTIVITY: error-correction-sviy-sebe -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose свій or мій/його/її based on sentence context
  items: 8
  type: quiz
- focus: Insert the correct case form of себе (себе, собі, собою)
  items: 8
  type: fill-in
- focus: Identify whether свій is used correctly in each sentence
  items: 8
  type: true-false
- focus: Match expressions with себе to their meanings
  items: 8
  type: match-up
- focus: Find and fix incorrect usage of свій and себе (e.g., *Він читає його книгу
    when meaning his own → свою, *Я почуваю себе when missing adverb)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- власний (own, one's own)
- самостійно (independently)
- звичка (habit)
- щоденний (daily)
required:
- свій (one's own)
- себе (oneself, accusative/genitive)
- собі (oneself, dative)
- собою (oneself, instrumental)
- почувати себе (to feel)
- вести себе (to behave)
- горджуся (I am proud)
- уявити (to imagine)
- дзеркало (mirror)
- парасолька (umbrella)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Свій: чий саме? (Свій: Whose Exactly?)

Уявіть звичайну щоденну ситуацію. Ваш друг читає нову книгу. В англійській мові ми просто кажемо: «He is reading his book». Але давайте подумаємо: чия це книга насправді? Це його власна книга чи, можливо, книга іншого хлопця? Англійська мова тут не дає точної та однозначної відповіді. Ми маємо вгадувати з контексту. В українській мові ми маємо спеціальне слово для таких цікавих ситуацій. Це **присвійний займенник** *(possessive pronoun)* **свій** *(one's own)*. Він завжди допомагає нам бути дуже точними. Головне правило української граматики тут дуже просте та логічне. Ми використовуємо слово «свій», коли власник певного предмета — це також підмет у цьому реченні. Тобто, якщо ваш друг читає свою власну книгу, ми кажемо: «Він читає свою книгу».

Найбільша та найважливіша різниця між англійською та українською мовами існує саме в третій особі. Це слова **він** *(he)*, **вона** *(she)* та **вони** *(they)*. Уважно подивіться на цей класичний приклад: «Він дуже любить свою дружину». Це означає, що він любить свою власну дружину. Все добре і правильно. А тепер подивіться на інше схоже речення: «Він дуже любить його дружину». Це вже справжній скандал! Чому це так звучить? Тому що слова **його** *(his)*, **її** *(her)* та **їхній** *(their)* завжди вказують на іншу людину. Вони чітко показують, що людина належить комусь іншому, а не головному підмету. Тому «його дружина» — це дружина іншого чоловіка. Завжди пам’ятайте це важливе правило, коли говорите про інших людей українською.

А як працює це правило для першої та другої особи? Це такі популярні слова як **я** *(I)*, **ти** *(you)*, **ми** *(we)* та **ви** *(you plural/polite)*. Тут граматичне правило стає трохи іншим і гнучкішим. Для цих осіб ми можемо вільно використовувати обидва варіанти. Ви можете сказати друзям: «Я дуже люблю мою маму» або «Я дуже люблю свою маму». Обидва ці речення абсолютно граматично правильні. Але українці у щоденному житті частіше кажуть «свою». Це просто звучить більш природно та тепло. Це завжди означає «мою власну». Те саме правило стосується інших слів. Ви можете сказати: «Ти знову забув твій телефон вдома» або «Ти знову забув свій телефон». Ми можемо сказати: «Ми щиро любимо наше чудове місто» або «Ми щиро любимо своє місто». Українці дуже люблять слово «свій», тому ви будете чути його постійно.

Як саме працює слово «свій» у структурі речення? Воно працює точно так само, як будь-який звичайний прикметник. Воно завжди граматично узгоджується з предметом, який комусь належить. Це дуже важливо: воно зовсім не залежить від власника. Що це правило означає на практиці? Слово «свій» має різні форми для чоловічого, жіночого та середнього роду. Воно також змінює свою форму в множині. І, звичайно, воно постійно змінюється за всіма відмінками. Наприклад, подивіться на ці два речення. «Він бачить свою малу сестру». Слово **сестра** *(sister)* — це іменник жіночого роду, тут це знахідний відмінок. Тому ми кажемо «свою». Нам абсолютно не важливо, що підмет «він» — це чоловічий рід. А тепер подивимося навпаки: «Вона бачить свого старшого брата». Слово **брат** *(brother)* — це іменник чоловічого роду, знахідний відмінок. Тому ми кажемо «свого». Знову ж таки, нам не важливо, що власник «вона» — це жіночий рід.

Давайте разом подивимося, як це правило працює в реальному житті. Уявіть типову ранкову сімейну сварку про особисті речі.

> — **Брат:** Це мій улюблений **светр** *(sweater)*! Швидко віддай його мені!
> — **Сестра:** Ні, це свій! Я купила його **собі** *(for myself)* вчора в магазині!
> — **Мама:** Діти, будь ласка, припиніть цю сварку! Олено, ти взяла свою чорну сумку, а не його светр. А ти, Максиме, знайди свій старий светр у шафі.

Як ви добре бачите, мудра мама ефективно використовує слово «свій», щоб швидко зупинити цю сварку. Вона чітко показує, хто є справжнім власником кожної речі. Вона каже дочці про її власну сумку («свою сумку»). А синові вона нагадує про його власний светр («свій светр»).

<!-- INJECT_ACTIVITY: quiz-possessive-choice -->


## Свій у відмінках (Свій in All Cases)

Тепер ви добре знаєте головне правило, коли саме ми використовуємо слово «свій». Але це слово також має багато різних форм. Воно **відмінюється** *(declines)* точно так само, як слова «мій» або «твій». Давайте спочатку подивимося на **чоловічий** *(masculine)* та **середній рід** *(neuter)*. У **називному відмінку** *(Nominative case)* ми маємо базові форми «свій» та «своє». Наприклад: «Кожен директор має свій власний **кабінет** *(office)*». У **родовому відмінку** *(Genitive case)* ця форма буде звучати як «свого». Наприклад: «Я довго чекаю свого старого друга» або «Він ніколи не мав свого автомобіля». Також зверніть увагу на **знахідний відмінок** *(Accusative case)*. Для живих істот ми використовуємо форму «свого» («Я щиро люблю свого пса»), а для неживих предметів ми кажемо «свій» («Він знову забув свій пароль»). В **орудному відмінку** *(Instrumental case)* ми завжди кажемо «своїм». Наприклад: «Я дуже горджуся своїм сином». 

А як щодо **жіночого роду** *(feminine)* та **множини** *(plural)*? Тут граматичні правила теж дуже схожі на слово «моя». У називному відмінку ми кажемо «своя» (для жіночого роду) та «свої» (для множини). У родовому відмінку жіночого роду з'являється цікаве закінчення «-єї». Тому ми завжди кажемо «своєї». Наприклад: «Вона швидко вийшла зі своєї кімнати». У множині форма буде «своїх»: «Вони з радістю чекають своїх нових гостей». Орудний відмінок має форми «своєю» та «своїми». Ви можете сказати: «Він приїхав за своєю дружиною» або «Ми дивилися на цю красу своїми **очима** *(eyes)*». І, звичайно, **давальний відмінок** *(Dative case)* має форму «своїй» для жінки та «своїм» для множини. Наприклад: «Вона часто допомагає своїй мамі». 

Давайте подивимося, як ці всі форми працюють на практиці. Українці дуже часто використовують ці присвійні займенники у щоденних розмовах, щоб зробити мову точнішою. Відмінок слова «свій» завжди залежить від дієслова або прийменника, які ви обираєте. Якщо ви використовуєте дієслово «пишатися» або «гордитися», вам потрібен орудний відмінок. Наприклад: «Я щиро **горджуся** *(am proud)* своїм рідним містом». Якщо ви хочете розповісти цікаву історію, ви будете використовувати прийменник «про» та знахідний або місцевий відмінок. Можна сказати так: «Вчора він дуже довго розповідав про свою велику родину». А коли ви робите щось добре для когось, ви використовуєте давальний відмінок. Наприклад: «Щовихідних вона із задоволенням допомагає своїй молодшій сестрі». 

Українська мова має багато цікавих виразів. Слово «свій» настільки популярне, що воно є важливою частиною багатьох сталих фраз та **ідіом** *(idioms)*. Їх варто просто запам'ятати. Коли українці кажуть про щось, що обов'язково має статися в майбутньому, вони часто говорять: «Усе буде у свій час» *(Everything in its own time)*. Також дуже важливо «мати свою думку» *(to have one's own opinion)* про різні життєві події. Іноді люди можуть сказати комусь досить агресивно: «Ти повинен знати своє місце!» *(You must know your place!)*. Але найкраща і найтепліша фраза — це «свої люди». Це означає, що ви з кимось маєте спільні інтереси, ви **однодумці** *(kindred spirits)*.

<!-- INJECT_ACTIVITY: true-false-sviy-grammar -->


## Себе: зворотний займенник (Себе: The Reflexive Pronoun)

Українська мова має ще один дуже важливий займенник. Це слово «себе». Воно називається **зворотним займенником** *(reflexive pronoun)*. Цей займенник є справді унікальним. Він ніколи не має називного відмінка. Чому так відбувається? Тому що слово «себе» ніколи не може бути головним підметом у вашому реченні. Воно завжди показує, що дія повністю повертається до того, хто її робить. Тобто об'єкт і суб'єкт — це одна й та сама особа. Також цей займенник зовсім не має роду та числа. Одна коротка форма чудово працює для всіх: для «я», «ти», «вона», «ми» або «вони». Наприклад, ви кажете: «Я часто бачу себе у великому **дзеркалі** *(mirror)*». І так само ви скажете про інших людей: «Вони часто бачать себе у великому дзеркалі». Форма слова ніколи не змінюється, хто б не виконував цю дію. Це робить правило дуже простим.

Як і слово «свій», займенник «себе» має кілька різних форм. Він завжди змінюється за відмінками. У родовому та знахідному відмінках ми використовуємо базову форму «себе». Наприклад: «Він дуже любить тільки себе і нікого більше». У давальному та місцевому відмінках форма змінюється на коротке слово «собі». Наприклад: «Я завжди бажаю собі великого успіху перед складним іспитом». Або: «Вона несе цей важкий рюкзак на собі». В орудному відмінку ми завжди використовуємо красиву форму «собою». Наприклад: «Він склав дуже складний іспит і тепер справді задоволений собою». Або: «Я завжди ношу цю стару фотографію із собою в гаманці». Як бачите, ці закінчення дуже схожі на відмінювання інших знайомих вам займенників або прикметників. Їх потрібно просто запам'ятати і часто використовувати під час розмов.

Займенник «себе» дуже часто працює разом із певними дієсловами. Найпопулярніші з них — це «почувати себе» та «вести себе». Коли ви хочете сказати, як ви фізично або морально почуваєтеся, ви використовуєте цю конструкцію. Але тут є одна надзвичайно важлива деталь. Англомовні студенти часто роблять одну типову помилку. Вони просто кажуть: «Я почуваю себе...» і відразу ставлять крапку. В українській мові так говорити не можна. Після фрази «почувати себе» ви обов'язково повинні додати конкретний **прислівник** *(adverb)*. Ви повинні чітко відповісти на запитання «як?». Наприклад: «Сьогодні я почуваю себе дуже добре». Або: «Вчора він почував себе трохи погано після довгої роботи». Це правило також працює для дієслова «вести себе». Ви маєте сказати: «Ця маленька дитина веде себе дуже погано в школі».

Форма «собі» також має своє власне спеціальне значення в українських розмовах. Українці дуже часто використовують її, коли вони говорять про **самостійні** *(independent)* дії або якусь особисту вигоду. Вона чітко показує, що людина робить щось саме для себе, а не для когось іншого. Наприклад: «Завтра я хочу купити собі нову **парасольку** *(umbrella)* на ринку». Тут «собі» означає те саме, що «для мене». Інший популярний приклад — це ваші внутрішні процеси. Ми часто кажемо друзям: «Ти взагалі можеш **уявити** *(to imagine)* собі цю ситуацію?». У таких фразах форма «собі» робить речення набагато більш емоційним та особистим. Вона показує ваш внутрішній світ. Або коли людина живе тихо і спокійно, ми часто кажемо про неї: «Він живе сам по собі».

Ви вже точно знаєте багато українських дієслів, які закінчуються на суфікс «-ся». Наприклад: «називатися», «вчитися», «сміятися». Але чи знаєте ви, звідки взагалі з'явився цей суфікс? Насправді суфікс «-ся» — це дуже стара і максимально коротка форма займенника «себе». Колись дуже давно люди говорили довгими фразами: «Я мию себе зранку». Але жива мова завжди шукає простіші і коротші форми. Тому з часом фраза «мити себе» логічно перетворилася на одне коротке слово «митися». Фраза «одягати себе» швидко стала словом «одягатися». Такі зворотні дієслова показують, що дія завжди повертається назад на самого суб'єкта. Розуміння історії слова «себе» дійсно допомагає набагато краще зрозуміти всю українську граматику. Ви починаєте бачити логіку мови.

<!-- INJECT_ACTIVITY: fill-in-sebe-cases -->

<!-- INJECT_ACTIVITY: match-up-sebe-idioms -->


## Свій та себе у мовленні

Давайте подивимося, як ці важливі слова працюють у реальній розмові. Прочитайте цей короткий діалог між двома друзями. Вони зустрілися на вулиці і говорять про свої щоденні **звички** *(habits)* та плани на день. Зверніть увагу, як часто вони використовують форми «свій» та «себе».

> — **Олег:** Привіт, Анно! Ти сьогодні маєш чудовий вигляд. Як твої справи?
> — **Анна:** Привіт! Дякую. Я нарешті дуже добре виспалася у своєму новому ліжку. Тому я почуваю себе чудово. А ти як?
> — **Олег:** Я теж почуваю себе дуже добре. Сьогодні вранці я купив собі новий великий телефон. Тепер я можу зручно читати новини у своєму улюбленому кріслі.
> — **Анна:** Це чудово! Я завжди купую собі щось приємне після важкого тижня. А ти часто робиш собі такі подарунки?
> — **Олег:** Не дуже часто. Зазвичай я просто беру із собою каву і гуляю у своєму районі. Я почуваю себе спокійно, коли багато ходжу пішки.
> — **Анна:** Я теж люблю гуляти. Але сьогодні я забула свою **парасольку** *(umbrella)* вдома, а небо сіре. Тому я зараз швидко йду до своєї машини.
> — **Олег:** Тоді гарного дня! Бережи себе.

Тепер прочитайте невелику розповідь. Цей короткий текст називається «Мій ранок». Він чудово показує, як одне правило працює в кожному реченні. Коли ви виконуєте дію, ви використовуєте «свій» для своїх речей. А коли дія направлена на вас, ви кажете «себе» або «собі».

«Зазвичай я прокидаюся дуже рано у своєму світлому ліжку. Я йду у ванну кімнату і довго дивлюся на себе у велике **дзеркало** *(mirror)*. Потім я йду на свою чисту кухню. Там я готую собі дуже міцну каву. Я ніколи не п'ю чай вранці. Я завжди роблю собі смачний сніданок зі свіжих продуктів. Під час сніданку я читаю цікаву книгу. Я люблю брати свою улюблену книгу із собою за стіл. Після сніданку я одягаю свій теплий **светр** *(sweater)*. Потім я беру свою важку сумку і виходжу на вулицю. Я сідаю у свою стару машину. Я вмикаю свою улюблену музику і їду на свою роботу. Я завжди почуваю себе бадьоро вранці, тому що я люблю свою роботу».

Наприкінці ми маємо поговорити про типові помилки. Студенти часто роблять кілька класичних помилок, коли вчать ці слова.

Перша помилка — це використання слова «його» або «її» замість «свій». Наприклад, студент каже: «Він любить його дружину». Українці зрозуміють це так, що цей чоловік любить дружину іншого чоловіка! Це дуже небезпечна помилка. Ви обов'язково повинні сказати: «Він любить свою дружину». Тоді все буде зрозуміло і правильно.

Друга типова помилка пов'язана з дієсловом «почувати себе». Англомовні люди часто кажуть просто: «Я почуваю себе», і роблять тут паузу. В українській мові це речення не має сенсу. Ви завжди маєте додати слово, яке відповідає на запитання «як?». Скажіть: «Я почуваю себе добре» або «Я почуваю себе погано».

Третя проблема — це прямий переклад фрази «to behave oneself». Студенти часто кажуть: «Вона добре себе поводить». Українці теж так кажуть, і ви можете це почути. Але набагато краще і правильніше сказати: «Вона добре поводиться». Дієслово вже має короткий суфікс «-ся», який означає «себе». Тому вам не потрібно додавати окреме слово «себе».

<!-- INJECT_ACTIVITY: error-correction-sviy-sebe -->


## Підсумок

Сьогодні ми вивчили дві дуже важливі граматичні теми. Давайте коротко повторимо головні правила.

Перше правило стосується слова «свій». Ми завжди використовуємо «свій», коли предмет належить підмету речення. Наприклад, ми кажемо: «Я читаю свою книгу» або «Він любить свою роботу». 

Друге правило стосується зворотного слова «себе». Ми використовуємо «себе», коли дія повертається прямо до підмета. Наприклад: «Я часто бачу себе у дзеркалі». Пам'ятайте, що це слово ніколи не має називного відмінка.

А тепер перевірте свої знання. Спробуйте відповісти на ці прості запитання:

1. Чому речення «Він любить його книгу» є незрозумілим або дивним?
*(Тому що слово «його» тут означає книгу іншого чоловіка, а не підмета).*

2. Чому ми категорично не можемо сказати «Себе бачить мене»?
*(Тому що займенник «себе» ніколи не може бути головним підметом у реченні).*

3. Який це відмінок у формі «собою»?
*(Це орудний відмінок. Наприклад, ми кажемо: «Вона дуже пишається собою»).*

4. Як правильно перекласти англійську фразу "I feel good" українською мовою?
*(Вам обов'язково треба додати слово «добре» або «погано»: «Я почуваю себе добре»).*

Ви чудово попрацювали сьогодні! Ці маленькі слова роблять вашу українську мову дуже природною та красивою.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: sviy-and-sebe
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

**Level: A2 (Module 56/60) — ELEMENTARY**

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
