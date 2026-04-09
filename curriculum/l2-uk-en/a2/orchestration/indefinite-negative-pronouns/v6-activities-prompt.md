<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/indefinite-negative-pronouns.yaml` file for module **57: Хтось, ніхто** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-sort-pronouns-by-series -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-appropriate-or-form -->`
- `<!-- INJECT_ACTIVITY: true-false-identify-correct-double-negation-usage-in-sentences -->`
- `<!-- INJECT_ACTIVITY: quiz-pronoun-context -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct indefinite or negative pronoun for the context
  items: 8
  type: quiz
- focus: Complete sentences with the appropriate -сь, -небудь, де-, будь-, or ні-
    form
  items: 8
  type: fill-in
- focus: Sort pronouns by series (-сь, -небудь, де-, будь-, ні-)
  items: 8
  type: group-sort
- focus: Identify correct double negation usage in sentences
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- абияк (carelessly, anyhow)
- деякий (some, certain)
- нічий (nobody's)
- хто-небудь (anyone at all)
required:
- хтось (someone)
- щось (something)
- ніхто (nobody)
- ніщо (nothing)
- ніколи (never)
- ніде (nowhere)
- дехто (some people)
- будь-хто (anyone)
- десь (somewhere)
- колись (once, sometime)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Хтось, щось: невідоме, але конкретне

Уявіть звичайну щоденну ситуацію: ви чуєте тихі кроки, але не бачите саму людину. Це справжня маленька загадка у вашому житті! В українській мові ми використовуємо спеціальні неозначені займенники. These are indefinite pronouns. Вони чітко показують, що предмет або особа реально існує, але ми їх не знаємо. Створити такі надзвичайно корисні слова дуже і дуже просто. Ми беремо знайоме питальне слово. This is a question word. Наприклад, це слова **«хто»**, **«що»** або **«де»**. These mean who, what, or where. Потім ми просто додаємо до нього короткий український суфікс «-сь». Порівняйте ці два короткі речення. Пряме питання звучить так: «Хто це?». This means "Who is this?". Але коли ми кажемо «Хтось іде», ми вже стверджуємо реальний факт. This means "Someone is walking". Ми точно знаємо, що людина там є, але її ім'я залишається невідомим. Цей короткий суфікс «-сь» завжди працює як справжній маркер таємниці.

Найчастіше в щоденних розмовах ми використовуємо популярні слова **«хтось»** та **«щось»**. They mean someone and something. Вони ідеально підходять для звичайних стверджувальних речень. These are affirmative sentences. Дія абсолютно реальна, вона точно відбувається прямо зараз, але головний герой залишається без імені. Подивіться дуже уважно на ці три конкретні життєві приклади. Ми кажемо: «Хтось стукає у двері». Someone is knocking at the door. Ви чуєте гучний звук, ви знаєте, що там стоїть людина, але не знаєте її імені. Ми кажемо: «Я бачу щось цікаве». I see something interesting. Ваш погляд випадково впав на новий предмет, але ви ще не знаєте, що це. Ми кажемо: «Хтось забув парасольку». Someone forgot an umbrella. Мокра парасолька лежить на столі, подія відбулася зовсім недавно, але власник речі нам абсолютно невідомий. У цих звичайних ситуаціях ми маємо конкретний факт, але ми не маємо конкретного імені.

Цей корисний суфікс «-сь» працює не тільки з людьми та різними цікавими предметами. Ми також можемо дуже легко додавати його до багатьох знайомих прислівників. These are adverbs. Так ми швидко створюємо нові слова: **«десь»**, **«колись»** та **«якось»**. They mean somewhere, sometime or once, and somehow. Слово «десь» завжди вказує на конкретне, але абсолютно невідоме для нас місце. Наприклад, ми дуже часто кажемо: «Він десь тут». He is somewhere here. Ви впевнені, що ця людина зовсім близько, але не бачите її точної локації. Слово «колись» — це дуже зручний і універсальний маркер нашого часу. Цікаво, що воно може вказувати як на далеке минуле, так і на наше майбутнє. Для далекого минулого ми кажемо: «Колись я жив у Львові». Once I lived in Lviv. Для нашого майбутнього ми скажемо: «Колись ми зустрінемося знову». Sometime we will meet again. Слово «якось» дуже сильно допомагає нам, коли ми не знаємо точного способу дії. Ми просто кажемо: «Я якось це зроблю». I will do this somehow.

Тепер давайте дуже детально поговоримо про нашу граматику. Як правильно і швидко відмінювати ці нові слова? Правило тут напрочуд просте і надзвичайно логічне для вивчення. Базовий займенник просто змінює свою форму за відмінками. The base pronoun changes its form by cases. А наш суфікс «-сь» просто спокійно чекає в самому кінці цього слова. Він абсолютно ніколи не змінюється. Ось як це чітко виглядає на практиці у трьох різних відмінках. Родовий відмінок дає нам популярні форми **«когось»** та **«чогось»**. Genitive case gives us forms meaning of someone and of something. Давальний відмінок дає нам часті форми **«комусь»** та **«чомусь»**. Dative case gives us forms meaning to someone and to something. Орудний відмінок дає нам відомі слова **«кимось»** та **«чимось»**. Instrumental case gives us forms meaning by or with someone and something. Зверніть особливу увагу на одну дуже важливу маленьку деталь. Короткі прийменники абсолютно ніколи не розривають ці нові слова. Prepositions never split these words. Ми завжди пишемо їх разом і ставимо прийменник прямо перед словом. Ми кажемо тільки так: «з кимось». With someone.

Наприкінці нашого уроку запам'ятайте одне дуже важливе правило для чистої української мови. Ніколи не використовуйте старі російські частки «-то» або «-либо». Never use Russian suffixes. В сучасній українській мові їх просто не існує. Наш рідний суфікс «-сь» — це єдиний правильний і природний маркер для невідомих об'єктів чи осіб.

<!-- INJECT_ACTIVITY: group-sort-sort-pronouns-by-series -->


## Будь-хто, дехто, абихто: різні відтінки

Іноді ми не знаємо точного об'єкта чи людини. Sometimes we do not know the exact object or person. Іноді нам підходить будь-який варіант. Sometimes any option works for us. Для таких випадків ми маємо частку **«-небудь»**. It means any or at all. Вона допомагає створити нове слово **«хто-небудь»**. This means anyone. Також ми маємо слово **«що-небудь»**. This means anything. Третє корисне слово — це **«де-небудь»**. This means anywhere. Ми дуже часто використовуємо цю групу слів у запитаннях. We use this group of words very often in questions. Наприклад, ви шукаєте свої ключі вдома. Ми питаємо: «Ти бачив кого-небудь у кімнаті?». Have you seen anyone in the room? Або ви хочете читати нову книгу ввечері. Ви кажете: «Дай мені що-небудь почитати». Give me anything to read. Також ці слова чудово працюють у різних гіпотетичних ситуаціях. Ці ситуації ще не сталися. These situations haven't happened yet. Наприклад, ми кажемо: «Якщо хто-небудь запитає, я на роботі». If anyone asks, I am at work. Ця частка завжди пишеться через дефіс. This particle is always written with a hyphen.

Тепер давайте подивимося на дуже популярний префікс **«будь-»**. It means any whatsoever. Цей короткий префікс також завжди пишеться через дефіс. З ним ми створюємо слово **«будь-хто»**. This means anyone at all. Також ми маємо слово **«будь-що»**. This means anything at all. Ще одне важливе слово — це **«будь-який»**. This means any kind. Ця група слів має дуже сильну енергію. Вони означають, що у нас абсолютно немає жодних обмежень. They mean we have absolutely no restrictions. Нам абсолютно неважливо, яка це людина чи який це предмет. It does not matter to us what person or object it is. Слово «будь-хто» звучить значно сильніше, ніж просте слово «хто-небудь». Наприклад, ми кажемо: «Будь-хто може це зробити». Anyone can do this. Це означає, що завдання дуже просте для всіх. Або ми кажемо в книжковому магазині: «Вибирай будь-яку книгу». Choose any book. Ви маєте повну свободу вибору. You have complete freedom of choice. Цей префікс робить ваше мовлення дуже природним.

Наступна важлива група слів починається з префікса **«де-»**. It means some. Цей короткий префікс завжди пишеться разом зі словом. This prefix is always written together with the word. Він допомагає нам створити дуже корисне слово **«дехто»**. This means some people. Також ми часто використовуємо слово **«дещо»**. This means some things. Інше популярне слово — це **«деякий»**. This means some or certain. Ця група має зовсім інший, дуже спокійний характер. Вони завжди вказують лише на певну частину великої групи. They always point only to a certain part of a large group. Ми використовуємо їх, коли говоримо про кількох людей чи кілька предметів. Наприклад, ми кажемо: «Дехто з нас уже бачив цей новий фільм». Some of us have already seen this new movie. Це означає, що фільм бачили не всі люди в кімнаті. Або ми хочемо почати серйозну розмову з другом. Ми кажемо: «Я маю дещо сказати тобі зараз». I have something to say to you now.

Остання група має дуже цікавий і специфічний характер. Це слова з префіксом **«аби-»**. It means just any or low quality. Цей префікс також завжди пишеться разом зі своїм словом. Він допомагає створити слово **«абихто»**. This means just anyone. Також ми маємо слово **«абищо»**. This means just anything. Інше важливе слово — це **«абияк»**. This means carelessly or anyhow. Вони часто мають дуже негативний відтінок у нашій щоденній розмові. They often have a very negative nuance in our daily conversation. Слово «абихто» означає просто випадкову людину абсолютно без досвіду. Слово «абияк» означає, що людина робить дію дуже погано та без уваги. Наприклад, ми дуже гостро критикуємо поганого працівника в офісі. Ми кажемо: «Він робить свою роботу абияк». He does his job carelessly. Ми не хочемо працювати з абиким. We do not want to work with just anyone.

Наприкінці цієї секції давайте запам'ятаємо одне критично важливе правило орфографії. At the end of this section, let us remember one critically important orthography rule. Це правило стосується коротких прийменників і наших нових займенників. This rule concerns short prepositions and our new pronouns. Якщо між префіксом і словом стає прийменник, слово повністю розривається. If a preposition stands between the prefix and the word, the word breaks apart completely. Усі три частини пишуться абсолютно окремо. All three parts are written completely separately. Ми кажемо: «будь з ким». With anyone. Ми кажемо: «аби до кого». To just anyone. Ми кажемо: «де в чому». In some things. Завжди пам'ятайте про дефіс для частки «будь-» і частки «-небудь». Також завжди пам'ятайте про написання разом для префіксів «де-» і «аби-» без прийменників.

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-appropriate-or-form -->


## Ніхто, ніщо, ніколи: заперечення

Тепер ми переходимо до дуже важливої теми. Це заперечні займенники та прислівники. They are negative pronouns and adverbs. Ми використовуємо їх, коли хочемо показати повну відсутність. We use them when we want to show a complete absence. Це може бути відсутність людини, предмета або якості. Всі ці слова починаються з префікса **«ні-»**. Наприклад, ми маємо слово **«ніхто»** (nobody) та слово **«ніщо»** (nothing). Також є слова **«ніякий»** (no kind of) та **«нічий»** (nobody's). Крім займенників, ми маємо корисні заперечні прислівники. Це слова **«ніде»** (nowhere), **«ніколи»** (never) та **«ніяк»** (no way). Цей префікс завжди пишеться разом зі словом, якщо немає прийменника. Ці слова роблять наше мовлення дуже точним і категоричним.

В українській мові є одне критично важливе правило синтаксису. Це правило обов'язкового подвійного заперечення. This is the rule of mandatory double negation. В англійській мові ми використовуємо лише одне заперечення. Ви кажете: «I see nothing». Але українська логіка працює зовсім інакше. Якщо ви використовуєте заперечний займенник, дієслово також обов'язково має частку **«не»** (not). Ми кажемо: «Я нічого не бачу». Ми маємо два заперечення: «нічого» та «не». Це не помилка, це обов'язкова граматика. This is not a mistake, this is mandatory grammar. Давайте подивимося на інші приклади. Ми кажемо: «Ніхто не прийшов» (Nobody came). Ми кажемо: «Ми ніколи не здаємося» (We never give up). Або ми кажемо: «Вона нічого не знає» (She knows nothing). Ви завжди повинні ставити частку «не» перед дієсловом. If you forget "не", the sentence will be completely incorrect.

Слова «ніхто» та «ніщо» постійно змінюють свою форму. Вони відмінюються так само, як слова «хто» та «що». They decline exactly like the words "who" and "what". Найважливіший відмінок тут — це родовий відмінок. The most important case here is the Genitive case. Ми використовуємо його зі словом **«немає»** (there is no) для вираження відсутності. Наприклад, ми кажемо: «Тут нікого немає» (There is nobody here). Також ми дуже часто використовуємо слово **«нічого»** (nothing - Genitive). Наприклад, ми кажемо: «Мені нічого не треба» (I don't need anything). У розмовній мові є цікава фонетична деталь. In spoken language, there is an interesting phonetic detail. Значення слова залежить від того, який склад ми виділяємо голосом. The meaning depends on which syllable we emphasize with our voice. Якщо ми робимо акцент на першому складі, це означає неможливість дії. If we emphasize the first syllable, it means the impossibility of an action. Наприклад, «нікого спитати» (there is no one to ask). Якщо акцент на другому складі, це означає відсутність. Наприклад, «нікого немає» (there is nobody).

Тепер давайте детально поговоримо про прийменники. Now let's talk about prepositions in detail. Заперечні займенники мають таку ж поведінку, як і слова з часткою «будь-». Negative pronouns behave the same way as words with the "будь-" particle. Якщо ми маємо короткий прийменник, він стає всередину слова. If we have a short preposition, it stands inside the word. Прийменник повністю розриває префікс і займенник. Усі три частини пишуться абсолютно окремо. All three parts are written completely separately. Наприклад, ми кажемо **«ні з ким»** (with nobody). Ми кажемо **«ні про що»** (about nothing). Або ми кажемо **«ні в кого»** (from/at nobody). Ви ніколи не можете сказати «з ніким». Це дуже груба помилка. This is a very serious mistake. Завжди ставте прийменник між префіксом «ні» та словом. Always put the preposition between the "ні" prefix and the word. Наприклад: «Я ні з ким не говорив» (I didn't speak with anybody). «Вона ні про що не думає» (She doesn't think about anything).

Давайте порівняємо ці слова для кращого розуміння. Let's compare these words for better understanding. Префікс змінює весь світ речення від існування до повної відсутності. The prefix changes the entire world of the sentence from existence to total absence. Порівняйте слово **«колись»** (once, sometime) та слово «ніколи» (never). Порівняйте слово **«десь»** (somewhere) та слово «ніде» (nowhere). Порівняйте слово **«хтось»** (someone) та слово «ніхто» (nobody). Це дуже логічна і красива система.

<!-- INJECT_ACTIVITY: true-false-identify-correct-double-negation-usage-in-sentences -->


## Практика: хтось чи ніхто?

Давайте прочитаємо діалог. Уявіть ситуацію: Олена та Максим на вечірці у великому будинку. Вони грають у настільну гру, але раптом чують дивний звук. Зверніть увагу на те, як вони використовують неозначені та заперечні займенники.

> — **Олена:** Ти чув цей звук? **Щось** (something) важке впало на кухні!
> — **Максим:** Це дуже дивно. **Ніхто** (nobody) не міг туди зайти зараз.
> — **Олена:** Але я точно чула гучний звук. Може, **хтось** (someone) пішов туди і шукає воду або їжу?
> — **Максим:** Ні, я впевнений. **Будь-хто** (anyone) з наших гостей зараз сидить у залі. Ми всі тут.
> — **Олена:** Але **десь** (somewhere) у цьому будинку має бути кіт. Може, це він стрибнув на стіл?
> — **Максим:** Я **нікого** (nobody) не бачив сьогодні. Кота тут немає.
> — **Олена:** Все одно треба **кому-небудь** (to anyone) піти на кухню і подивитися, що там сталося.
> — **Максим:** Добре, я піду і перевірю. Я **нічого** (nothing) не боюся у цьому будинку.

А тепер прочитайте коротку історію про дивний вечір. Спробуйте знайти всі неозначені та заперечні слова.

Був пізній і темний вечір. Один чоловік повільно йшов додому через старий міський парк. Раптом він чітко почув тихі кроки позаду себе. Він подумав, що **хтось** (someone) іде за ним. Він швидко зупинився і уважно подивився назад. Але там **нікого** (nobody) не було. На вулиці була абсолютна тиша. **Ніхто** (nobody) не гуляв у цей пізній час.

Чоловік пішов далі, але трохи швидше. Раптом він відчув, що він **щось** (something) загубив. Він зупинився знову і швидко перевірив усі свої кишені. Але там **нічого** (nothing) не було, крім старих ключів. Він хотів запитати **кого-небудь** (anyone) про час, щоб заспокоїтися. Але вулиця була абсолютно порожня. Він **ніде** (nowhere) не бачив інших людей чи машин.

Раптом він різко прокинувся. Він лежав у своєму теплому ліжку вдома. Чоловік згадав, що **колись** (once) у дитинстві він уже бачив цей дивний сон. Це був просто поганий сон. Насправді **нічого** (nothing) страшного не сталося.

Давайте коротко повторимо типові помилки. Студенти часто роблять їх, коли вивчають ці займенники.

По-перше, ніколи не забувайте про заперечну частку «не». В українській мові завжди є подвійне заперечення. Ви не можете просто сказати «Ніхто знає». Це велика помилка. Ви завжди повинні сказати «Ніхто **не** знає». Або ви можете сказати «Я **нічого** не бачу».

По-друге, ніколи не використовуйте російську частку «-то». В українській мові немає слів «хто-то» або «що-то». Це суржик. Ми завжди використовуємо питому українську частку «-сь». Правильно казати **хтось** (someone) та **щось** (something).

По-третє, будьте дуже уважні з прийменниками. Якщо ви маєте прийменник, він стає всередину слова. Це стосується слів із часткою «будь-» або префіксом «ні-». Наприклад, ми не кажемо «з будь-ким». Правильно казати **будь з ким** (with anyone). Також ми ніколи не кажемо «з ніким». Правильно казати **ні з ким** (with nobody). Усі три слова пишуться окремо.

Ці маленькі слова дуже важливі для щоденного спілкування. Коли ви використовуєте їх правильно, ваша українська мова звучить набагато природніше. Ви можете легко говорити про невідомі речі. Також ви можете правильно будувати заперечення. Практикуйтеся щодня, і ви будете говорити впевнено і красиво. Ви будете говорити як справжній носій мови!

<!-- INJECT_ACTIVITY: quiz-pronoun-context -->


## Підсумок

Давайте коротко перевіримо ваші нові знання. Це допоможе вам краще запам'ятати сьогоднішню тему. Спробуйте дати правильні відповіді на ці п'ять запитань:

*   **Як утворити займенник someone від слова «хто»?**
    Для цього треба просто додати суфікс «-сь». У вас вийде нове слово **хтось** (someone).

*   **Чи можна сказати «Я нічого бачу»?**
    Ні, це велика граматична помилка. Українська мова завжди вимагає обов'язкового подвійного заперечення. Тому правильно казати: «Я **нічого** (nothing) не бачу».

*   **Де ставиться прийменник «з» у слові «будь-хто»?**
    Прийменник завжди ставиться прямо між двома частинами цього слова. Усі три слова пишуться абсолютно окремо. Правильно писати: **будь з ким** (with anyone).

*   **Яка головна різниця між словами «хтось» та «будь-хто»?**
    Слово **хтось** (someone) — це одна конкретна, але невідома особа. Слово **будь-хто** (anyone) — це абсолютно будь-яка особа без жодних обмежень.

*   **Як правильно написати anyone at all — через дефіс чи разом?**
    Пам'ятайте, що це слово завжди пишеться через дефіс. Правильно писати: **хто-небудь** (anyone at all).

Тепер ви чудово знаєте всі ці важливі займенники! Ви зможете легко використовувати їх у щоденних розмовах з друзями. Вони зроблять вашу українську мову набагато багатшою та природнішою.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: indefinite-negative-pronouns
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

**Level: A2 (Module 57/60) — ELEMENTARY**

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
