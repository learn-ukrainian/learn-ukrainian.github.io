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

(No injection markers found in prose. All activities will go to workbook.)

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

Що таке **хобі** *(hobby)*? Це ваше **захоплення** *(passion, interest)*. Це ваше улюблене заняття у **вільний час** *(free time)*. Кожна людина повинна мати хобі. Улюблені справи допомагають нам відпочивати. Коли ми багато працюємо або вчимося, нам потрібен гарний відпочинок. Хобі дає нам нову енергію та радість щодня. Хтось любить читати цікаві книжки. Інші люди люблять гуляти на природі. Деякі люди мають дуже оригінальні захоплення. У кожного є своя улюблена справа. Дуже важливо знайти заняття, яке подобається саме вам.

To express what you are passionate about, we use the verb **захоплюватися** *(to be passionate about)*. This verb always requires the noun to be in the Instrumental case. Singular masculine and neuter nouns take the endings **-ом** or **-ем**.

Я захоплююся **малюванням** *(drawing)*.
Мій брат захоплюється **читанням** *(reading)*.
Вона захоплюється **плаванням** *(swimming)*.

Singular feminine nouns take the endings **-ою** or **-ею**.

Я захоплююся **музикою** *(music)*.
Він захоплюється **фотографією** *(photography)*.
Моя мама захоплюється **кулінарією** *(cooking)*.

Ці слова показують сильні емоції. Коли ми захоплюємося чимось, ми робимо це з великою любов'ю. Ми витрачаємо багато часу на наші захоплення. Люди часто шукають друзів, які захоплюються тим самим. Це дуже допомагає у спілкуванні.

Another important verb is **займатися** *(to engage in, to do)*. We use it to talk about active, regular engagement, especially for sports and practical activities. Like the previous verb, it also strictly requires the Instrumental case.

Я постійно займаюся **спортом** *(sport)*.
Вона щоранку займається **йогою** *(yoga)*.
Мій молодший син займається **гімнастикою** *(gymnastics)*.
Ми часто займаємося ранковим **бігом** *(running)*.

For plural hobbies, the Instrumental plural ending is usually **-ами** or **-ями**.

Я займаюся сучасними **танцями** *(dancing)*.
Він професійно займається **шахами** *(chess)*.

У школі діти із задоволенням займаються різними корисними справами. Вони розвивають свої таланти через активні заняття. Займатися спортом дуже корисно для нашого здоров'я та гарного настрою.

When we talk about playing, the Ukrainian language makes a strict distinction between sports and musical instruments. For sports and games, we use the construction **грати в** or **грати у** *(to play)* followed by the Accusative case. This uses the logic of movement into a game.

Я люблю грати у **футбол** *(football)*.
Вони грають у **теніс** *(tennis)* на вихідних.

For musical instruments, we use the construction **грати на** *(to play on)* followed by the Locative case. This uses the logic of interaction on a physical surface.

Він гарно грає на **гітарі** *(guitar)*.
Моя сестра грає на **скрипці** *(violin)*.
Вона вчиться грати на **фортепіано** *(piano)*.

To describe how often you do your hobbies, you can use adverbs of frequency. These adverbs usually stand before the verb in a sentence.

Я **завжди** *(always)* займаюся йогою вранці.
Він **часто** *(often)* грає у футбол з друзями.
Ми **іноді** *(sometimes)* ходимо в кіно на вихідних.
Моя сестра **рідко** *(rarely)* ходить у музей.
Я **ніколи** *(never)* не граю на фортепіано.

In the Ukrainian language, we must use a double negative with the word «ніколи». Такі слова допомагають нам точно розповідати про наш вільний час. Вони роблять нашу розповідь більш цікавою та детальною. Ви можете легко планувати свій розклад з цими словами.

> — **Софія:** Привіт! Мене звати Софія.
> — **Новий знайомий:** Привіт! А я Марко. Дуже приємно познайомитися.
> — **Софія:** Навзаєм. Чим ти зазвичай займаєшся у вільний час?
> — **Новий знайомий:** Я люблю музику й спорт. Я гарно граю на гітарі та бігаю щоранку. А ти чим захоплюєшся?
> — **Софія:** Я захоплююся малюванням. Це мене дуже заспокоює.
> — **Новий знайомий:** Це чудове хобі. Ти малюєш пейзажі чи портрети?
> — **Софія:** Переважно пейзажі. Також я люблю ходити в театр на нові вистави.
> — **Новий знайомий:** Я рідко ходжу в театр, але завжди радий скласти компанію!

<!-- INJECT_ACTIVITY: match-up, Match verbs with their correct case government and examples (захоплюватися, грати в, грати на, займатися) -->


## Куди йдемо? Де ми? (Where Are We Going? Where Are We?)

Коли ми говоримо про наше дозвілля, ми часто змінюємо різні локації. Sometimes we talk about where we are going, and other times we describe where we currently are. The Ukrainian language makes a strict distinction between direction and location. To express direction or movement towards a place, we use the question **Куди?** *(Where to?)* and the Accusative case. To express a static location, we use the question **Де?** *(Where?)* and the Locative case. Ця граматична різниця дуже важлива для правильного та точного спілкування. Наприклад, ми говоримо: «Я йду в театр», щоб показати рух. Але ми кажемо: «Я зараз у театрі», щоб показати місце. The ending of the noun always changes based on the verb you choose for your sentence.

Коли ми плануємо наш відпочинок, ми часто використовуємо дієслова руху. Такі дієслова, як **йти** *(to go on foot)*, **піти** *(to go, perfective)* або **їхати** *(to drive/ride)*, завжди вимагають знахідного відмінка. When you answer the question «Куди?», you must use the Accusative case for your destination. For masculine and neuter inanimate nouns, the form remains exactly the same as the Nominative case. Я йду у **басейн** *(pool)*. Ми швидко їдемо в **кіно** *(cinema)*. For feminine nouns ending in -а or -я, the ending changes to -у or -ю. Завтра я піду на цікаву **виставку** *(exhibition)*. Увечері ми з друзями йдемо на **прогулянку** *(walk)*. Цей відмінок чітко показує наш рух до певної мети. Ми завжди використовуємо його, коли тільки прямуємо до нашого місця відпочинку.

Коли ми вже знаходимося в певному місці, наша ситуація змінюється. To describe a static location, we answer the question «Де?» and use the Locative case. We often use the verb **бути** *(to be)*, though in the present tense it is usually omitted in Ukrainian. The Locative case requires specific word endings. Most feminine nouns change their ending to -і. Зараз я на **виставці** *(at the exhibition)*. Вона відпочиває на **прогулянці** *(on a walk)*. Masculine and neuter nouns also typically take the ending -і or sometimes -у. Ми зараз плаваємо у **басейні** *(in the pool)*. Мої друзі вже чекають у **театрі** *(in the theater)*. Маленькі діти граються в **парку** *(in the park)*. Цей відмінок фіксує наше точне місцезнаходження під час відпочинку.

Для позначення місця ми використовуємо короткі прийменники **в** (або **у**) та **на**. The choice between these prepositions usually depends on the type of location. The general rule is to use «в» or «у» for enclosed spaces, rooms, or buildings. Ми з родиною дивимося фільм у **кінотеатрі** *(cinema)*. Вони довго роздивляються старі картини у **музеї** *(museum)*. On the other hand, we use «на» for open spaces, flat surfaces, or public events. Завтра вранці ми будемо на **стадіоні** *(stadium)*. Моя старша сестра зараз співає на **концерті** *(concert)*. There are some exceptions you just need to memorize. For example, we say «на пошті» or «на роботі», even though these are often inside buildings. Правильний прийменник допомагає дуже точно описати ваші плани на вихідні.

> — **Колега 1:** Привіт! Робочий тиждень нарешті закінчується. Що робитимеш на **вихідних** *(weekend)*?
> — **Колега 2:** Привіт! У суботу зранку я піду в басейн, а потім поїду на виставку сучасного мистецтва. А в тебе які плани?
> — **Колега 1:** Я дуже хочу відпочити на свіжому повітрі. Може, підемо разом кудись у суботу ввечері?
> — **Колега 2:** З великим задоволенням! Ми можемо піти в кіно або театр. Але в неділю вранці я буду в парку на **тренуванні** *(training)*.
> — **Колега 1:** О, це чудово. Я теж люблю спорт і часто бігаю. Тоді зустрінемося в неділю в парку на стадіоні!
> — **Колега 2:** Домовилися! Я буду чекати на тебе біля головного входу.

<!-- INJECT_ACTIVITY: quiz, Choose the correct form (Accusative or Locative) based on the verb in the sentence (йти vs. бути) and the venue (музей, стадіон, опера, басейн) -->


## Плани на вихідні (Weekend Plans)

Коли ми хочемо запросити друзів кудись, ми використовуємо спеціальні форми. The best way to make a suggestion is to use hortative and imperative forms. Це робить наше спілкування легким та приємним. Ми часто кажемо: **«Ходімо!»** *(Let's go!)* або **«Давай підемо!»** *(Let's go!)*. Ці слова показують нашу ініціативу. Наприклад: «Ходімо в кіно сьогодні ввечері!». When you want to suggest playing a game, you can say: **«Давай пограємо!»** *(Let's play!)*. Наприклад: «Давай пограємо у футбол на стадіоні!». Також ми можемо запитати: **«Може, підемо...?»** *(Maybe we should go...?)*. Це дуже ввічливий спосіб запропонувати ідею. Якщо ви хочете знати бажання друга, запитайте: **«Хочеш піти...?»** *(Do you want to go...?)*. Такі фрази створюють дружню атмосферу. They set an informal tone and show that you value your friend's preferences. Завжди використовуйте їх, коли плануєте спільний відпочинок зі знайомими.

Якщо вам подобається ідея, треба правильно відповісти. Accepting an invitation politely is important for making quick plans. Українці часто використовують дуже емоційні фрази для згоди. Ви можете сказати: **«З задоволенням!»** *(With pleasure!)*. Це показує вашу радість та ентузіазм. Інший популярний варіант — **«Чудова ідея!»** *(Great idea!)*. Коли ви згодні на пропозицію друга, скажіть: **«Так, давай!»** *(Yes, let's do it!)*. Або просто скажіть: **«Я — за!»** *(I'm in!)*. Ці вирази звучать дуже природно в розмові. If the suggestion is unexpected but good, we say: **«Чому б і ні?»** *(Why not?)*. Наприклад: «Підемо в музей? — Чому б і ні!». Ці короткі відповіді допомагають швидко домовитися про зустріч. Вони показують, що ви готові до нових пригод на вихідних.

Іноді ми не можемо прийняти запрошення. Declining an invitation should always be polite to avoid offending the person. Найкраще почати з фрази: **«На жаль, не можу.»** *(Unfortunately, I can't.)*. Після цього варто пояснити причину вашої відмови. Чоловіки кажуть: **«Я зайнятий»** *(I am busy, masc.)*. Жінки кажуть: **«Я зайнята»** *(I am busy, fem.)*. Часто ми додаємо слово **треба** *(need to)*, щоб пояснити наші поточні обов'язки. Наприклад: «На жаль, я зайнята, мені треба **прибрати** *(to clean)* вдома.» You can always leave the door open for future plans. Suggest an alternative: **«Може, іншим разом?»** *(Maybe next time?)*. Також можна прямо сказати: **«У мене вже є плани.»** *(I already have plans.)*. Це чесний і ввічливий спосіб відмовитися від зустрічі. Головне — завжди залишатися дружнім і відкритим.

Коли ви погодилися на спільну зустріч, треба узгодити важливі деталі. To arrange the exact time and place, we use specific questions in our conversations. Ми завжди питаємо: **«О котрій?»** *(At what time?)* та **«Де зустрінемося?»** *(Where will we meet?)*. To answer about time, use the preposition **о** *(at)*. Use **об** *(at)* before a vowel. It is followed by the Locative case of the number. Наприклад: «Зустрінемося о **п'ятій** *(fifth)* годині.» Або можна сказати: «Зустрінемося об **одинадцятій** *(eleventh)* годині.» Якщо місце має певний вхід, ми кажемо: «Зустрінемося біля **входу** *(entrance)* в метро.» Або можна також сказати: «Зустрінемося біля кінотеатру.» These precise details ensure that no one gets lost or arrives late. Планування точного часу та місця робить ваші вихідні спокійними.

Кожні ідеальні вихідні зазвичай починаються з гарного плану. The logic of weekend planning always follows a simple cycle. It involves suggestion, response, and coordination. Спочатку хтось пропонує цікаву ідею для дозвілля. Потім інша людина погоджується або ввічливо відмовляється від пропозиції. Якщо всі згодні, друзі відразу домовляються про час і місце. Цей процес дуже часто відбувається на роботі у п'ятницю. Колеги активно обговорюють майбутні розваги біля кавоварки. Вони використовують усі ці корисні комунікативні фрази.

> — **Колега:** Робочий тиждень закінчується. Ходімо в кіно! *(The work week is ending. Let's go to the cinema!)*
> — **Ви:** Я — за! Чудова ідея. О котрій зустрінемося? *(I'm in! Great idea. At what time will we meet?)*
> — **Колега:** О сьомій годині, біля входу. *(At seven o'clock, near the entrance.)*

Тепер ви також знаєте, як легко організувати свій вільний час українською мовою. Бажаємо вам цікавих і чудових вихідних у колі друзів!

<!-- INJECT_ACTIVITY: error-correction, find and fix case and preposition errors in invitation sentences (e.g., *ходімо на театр -> у театр, *захоплююся плавання -> плаванням). 6 items. -->


## Що мені подобається найбільше (What I Like Most)

Ми маємо різні інтереси, хобі та захоплення. Деякі заняття ми просто любимо, а інші — щиро обожнюємо. It is important to know how to express different levels of preference in Ukrainian. Коли нам щось приємно робити у вільний час, ми кажемо: **«Мені подобається»** *(I like)*. Наприклад: «Мені подобається читати цікаві книги.» Або: «Мені подобається сучасна фотографія.» When your emotions are stronger, you can intensify the phrase. Коли наші емоції сильніші, ми додаємо слово **дуже** *(very)*. Наприклад: «Мені дуже подобається класична музика.» Або: «Мені дуже подобається грати на гітарі ввечері.» Але майже завжди є одне особливе хобі, яке ми любимо більше за всі інші. Тоді ми кажемо: **«Мені найбільше подобається»** *(I like most)*. Наприклад: «Мені найбільше подобається швидке плавання.» Або: «Мені найбільше подобається дивитися старі фільми.» If you have a true passion for an activity or a thing, use the strong verb **обожнювати** *(to adore)*. Ми кажемо: **«Я обожнюю»** *(I adore)*. Наприклад: «Я обожнюю малювання!» Або: «Я обожнюю ходити в драматичний театр.» You can easily combine these phrases in a long conversation with friends to contrast your interests. Наприклад: «Я люблю спорт, але найбільше мені подобається футбол.» Або: «Мені дуже подобається кулінарія, але я просто обожнюю пекти солодкі торти.» Ці слова допоможуть вам емоційно та щиро розповісти про ваші улюблені щоденні заняття.

Українці надзвичайно люблять активно та цікаво проводити свій вільний час. У нашій багатій культурі є багато традиційних видів відпочинку на природі. На вихідних або у довгій відпустці багато людей люблять **ходити в гори** *(to hike in the mountains)*. Найпопулярніше та найгарніше місце для цього — Карпати. Там українці можуть спокійно насолоджуватися дикою природою та дихати чистим повітрям. Восени дуже популярно **збирати гриби** *(to hunt for mushrooms)* у густому лісі. Це іноді нагадує справжнє спортивне змагання. Кожен хоче знайти найбільше красивих білих грибів. Влітку люди також часто ходять **збирати ягоди** *(to pick berries)*, наприклад, чорницю або малину. У великому місті українці також не сидять сумно удома. Вони дуже люблять **відвідувати фестивалі** *(to attend festivals)*. У різних містах проходить багато музичних, кулінарних та традиційних мистецьких фестивалів. Це завжди чудова можливість послухати живу музику, смачно поїсти та зустрітися з друзями. Для багатьох сучасних сімей головне місце відпочинку влітку — це **дача** *(summer house)*. Дача — це зазвичай маленький затишний будинок за містом. Там люди можуть спокійно відпочивати від швидкого темпу та галасливого міста. На дачі українці дуже часто займаються корисним садівництвом. Вони з великим задоволенням вирощують свіжі овочі, зелень та солодкі фрукти. Working with the soil is considered a perfect way to relax and disconnect from urban stress. Для багатьох старших людей робота на землі — це найкращий відпочинок і улюблене хобі. Увечері на дачі велика родина збирається разом на вулиці. Вони готують смачну вечерю, п'ють чай та довго спілкуються. Такі теплі та спокійні вихідні чудово допомагають відновити сили перед новим складним робочим тижнем.

<!-- INJECT_ACTIVITY: group-sort, categorize vocabulary into groups: Спорт, Мистецтво, На природі, У місті. 8 items. -->
<!-- INJECT_ACTIVITY: fill-in, complete a paragraph about a person's weekend using the correct case forms for hobbies and destinations. 8 items. -->


## Підсумок

Ось і все! Тепер ви знаєте, як розповісти про своє улюблене дозвілля та хобі українською мовою. Ви можете легко планувати вихідні та запрошувати друзів на цікаві події. Давайте перевіримо, що ви запам'ятали з цього уроку. Спробуйте відповісти на ці питання:

* **Як сказати "I am passionate about swimming"?**
  Ми використовуємо дієслово «захоплюватися» та Орудний відмінок: «Я захоплююся плаванням».

* **Який відмінок ми використовуємо після «йти на» або «йти в»?**
  Коли ми говоримо про напрямок або місце призначення, ми використовуємо Знахідний відмінок *(Accusative case)*: «Ми йдемо на виставку» або «Я йду в кіно».

* **Як ввічливо відмовитися від запрошення?**
  Якщо ви не можете піти, скажіть: «На жаль, не можу. У мене вже є плани» або «Може, іншим разом?».

* **Чим відрізняється «грати у футбол» від «грати на гітарі»?**
  Для візних видів спорту ми беремо конструкцію «грати в/у» і Знахідний відмінок *(Accusative)*. Для музичного інструмента треба казати «грати на» і використовувати Місцевий відмінок *(Locative)*.

* **Як запропонувати піти в кіно?**
  Ви можете просто сказати: «Ходімо в кіно!», «Може, підемо в кіно?» або «Хочеш піти на новий фільм?».

Тепер ви повністю готові до активних та цікавих вихідних. Бажаємо вам чудового відпочинку!

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
