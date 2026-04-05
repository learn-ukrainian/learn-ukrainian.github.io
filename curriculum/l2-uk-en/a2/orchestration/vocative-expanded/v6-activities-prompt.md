<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/vocative-expanded.yaml` file for module **27: Пане лікарю! Друже мій!** (a2).

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

- focus: Form the correct vocative of professional titles and names (пане _____, пані
    _____)
  items: 8
  type: fill-in
- focus: Choose the correct vocative register for a given social situation
  items: 8
  type: quiz
- focus: Match nominative forms to their vocative equivalents (лікар → лікарю, вчитель
    → вчителю, друг → друже)
  items: 8
  type: match-up
- focus: Fix vocative errors (*пан лікар → пане лікарю, *друже моя → подруго моя,
    *Мій друже → Друже мій)
  items: 8
  type: error-correction
- focus: Sort vocative forms by register (formal, professional, emotional)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- добродій (sir (literary/diaspora))
- добродійка (madam (literary/diaspora))
- емоційний (emotional)
- ніжний (tender, affectionate)
- колега (colleague)
required:
- кличний (vocative (case))
- звертання (address, appeal)
- пан (Mr., sir)
- пані (Mrs., Ms., madam)
- лікар (doctor)
- вчитель (teacher)
- друг (friend)
- ввічливий (polite)
- офіційний (official, formal)
- професія (profession)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пане, пані: формальне звертання (Formal Address)

Ми вже знаємо, як кликати друзів. Ми кажемо: **«Оксано!»** *(Oksana!)* або **«Іване!»** *(Ivan!)*. Це **кличний відмінок** *(vocative case)*. Але як звертатися до незнайомих людей? Як говорити з лікарем або директором? У таких ситуаціях ми використовуємо **офіційний** *(official)* стиль. В Україні сьогодні стандартне формальне звертання — це слова **«пан»** *(Mr., sir)* та **«пані»** *(Mrs., Ms., madam)*. Це дуже **ввічливий** *(polite)* спосіб спілкування. In the A1 level, you learned the basic vocative forms for first names. Now, at the A2 level, you will learn how to use the professional and formal registers. Addressing someone by "Pani" or "Pane" is the absolute standard for polite, respectful interaction in modern Ukraine.

Коли ми звертаємося до чоловіка, ми кажемо **«пане»** *(sir)*. Це форма кличного відмінка від слова «пан». Якщо ми називаємо **професію** *(profession)*, це слово також має бути у кличному відмінку. When you use the "Pane + Profession" pattern, both words must be in the vocative case. This is a very common mistake for learners. You cannot use the nominative case for the profession. Наприклад, ми кажемо **«пане директоре»** *(Mr. Director)*, а не «пане директор». Ми кажемо **«пане професоре»** *(Mr. Professor)* і **«пане міністре»** *(Mr. Minister)*. Обидва слова змінюють своє закінчення. Це правило дуже важливе для офіційного спілкування. If you talk to a male doctor, you must say **«пане лікарю»** *(Mr. Doctor)*. The nominative form **«лікар»** *(doctor)* змінюється на «лікарю». Always remember that the vocative case requires both parts of the formal address to change.

Коли ми звертаємося до жінки, ми використовуємо слово «пані». Слово «пані» ніколи не змінюється. Воно завжди залишається у цій формі. Але професія жінки обов'язково стоїть у кличному відмінку. The "Pani + Profession" pattern is slightly different because "пані" is invariable. However, the professional title still changes to its vocative form, which usually ends in -о for feminine nouns. Наприклад, ми кажемо **«пані вчителько»** *(Mrs. Teacher)*. Слово **«вчителька»** *(female teacher)* змінює закінчення. Ми кажемо **«пані лікарко»** *(Mrs. Doctor)* і **«пані директорко»** *(Mrs. Director)*. Сучасна українська мова активно використовує фемінітиви. Це слова, які називають жіночі професії. Це дуже природно і правильно. Therefore, you should always learn the feminine form of a profession. This shows high respect and deep knowledge of the language.

Ми також можемо звертатися до людей на прізвище. Це дуже офіційно. When addressing men by their surname, you use "Пане" followed by the surname in the vocative case. Masculine surnames in Ukrainian decline just like regular nouns. Наприклад, ми кажемо **«пане Ковальчуку»** *(Mr. Kovalchuk)* або **«пане Шевченку»** *(Mr. Shevchenko)*. Прізвище змінює своє закінчення. For women, the rule depends on the ending of the surname. You use "Пані" plus the surname. However, feminine surnames that end in a consonant (like Kovalchuk) or in -о (like Shevchenko) do not decline in the vocative case. Тому ми кажемо **«пані Ковальчук»** *(Ms. Kovalchuk)* та **«пані Шевченко»** *(Ms. Shevchenko)*. Прізвище жінки тут не змінюється. Слово «пані» також не змінюється. Це правило треба запам'ятати.

Чому ми кажемо «пан» і «пані»? Це має велике культурне значення. During the Soviet era, these traditional Ukrainian terms of address were strictly suppressed. The government forced people to use the word **«товариш»** *(comrade)* instead. Returning to "Пан" and "Пані" after independence was a conscious decolonial choice. Сьогодні ці слова показують українську ідентичність. Це європейська традиція поваги до людини. Також існують старі слова **«добродію»** *(sir, literary)* та **«добродійко»** *(madam, literary)*. Їх часто використовує українська діаспора. В Україні ці слова також розуміють, але вони звучать дуже літературно. Using these words correctly demonstrates that you respect Ukrainian culture and history. It is a powerful way to connect with native speakers on a deeper level.

Давайте подивимося, як це працює в житті. Пацієнт прийшов у поліклініку.
> — **Пацієнт:** Добрий день, **пане лікарю**! *(Good day, doctor!)*
> — **Лікар:** Добрий день, **пане Ковальчуку**. *(Good day, Mr. Kovalchuk.)* Проходьте, будь ласка. *(Come in, please.)* Сідайте ось тут. *(Sit right here.)*
> — **Пацієнт:** Дякую. *(Thank you.)* Я маю проблему. *(I have a problem.)*
> — **Лікар:** Слухаю вас уважно. *(I am listening to you carefully.)*


## Професійні звертання (Professional Vocative)

Masculine professions in the vocative case have specific endings. Українська мова розділяє чоловічі професії на дві групи. Це залежить від останнього приголосного звука. The distinction is based on whether the noun stem is hard or soft. If a masculine profession ends in a soft consonant, it takes the ending **-ю** in the vocative case. Наприклад, ми кажемо **«лікарю»** *(doctor)* замість **«лікар»**. Слово **«вчитель»** *(teacher)* змінюється на **«вчителю»**. Слово **«водій»** *(driver)* стає **«водію»**. Слово **«секретар»** *(secretary)* стає **«секретарю»**. Nouns ending in -р that take soft endings follow this rule. If a masculine profession ends in a hard consonant, it takes the ending **-е**. Наприклад, ми кажемо **«професоре»** *(professor)* замість **«професор»**. Слово **«інженер»** *(engineer)* стає **«інженере»**. Слово **«директор»** *(director)* стає **«директоре»**. Слово **«студент»** *(student)* стає **«студенте»**. Ці закінчення дуже важливі для ввічливого спілкування. They show respect to the person's professional role. Коли ви говорите з чоловіком, завжди вибирайте правильне закінчення. 

Feminine professions have a much simpler rule in the vocative case. Більшість жіночих професій в українській мові закінчується на літеру **«-а»**. In the vocative case, this ending almost always changes to **«-о»**. Це правило дуже стабільне і легке. Наприклад, називний відмінок — **«лікарка»** *(female doctor)*. Кличний відмінок — **«лікарко»**. Слово **«вчителька»** *(female teacher)* змінюється на **«вчителько»**. Слово **«журналістка»** *(female journalist)* стає **«журналістко»**. Слово **«директорка»** *(female director)* стає **«директорко»**. Слово **«студентка»** *(female student)* стає **«студентко»**. This consistent pattern makes it easy to address women professionally. Ви завжди знаєте, яке закінчення треба використовувати. Просто замініть літеру «-а» на літеру «-о». Це звучить дуже природно і ввічливо. Українці часто використовують ці форми.

There are a few special cases and common gender nouns to remember. Деякі слова можуть означати і чоловіка, і жінку. Слово **«колега»** *(colleague)* — це одне з таких слів. It ends in -а, so it changes to -о in the vocative case for both men and women. Ми завжди кажемо **«колего»**. Інше цікаве слово — **«суддя»** *(judge)*. It ends in -я, which is a soft vowel. In the vocative case, it takes the ending **-ю**. Ми кажемо **«пане суддю»** *(Mr. Judge)* або **«пані суддю»** *(Madam Judge)*. Також є слово **«майстер»** *(master, craftsman)*. It is a hard stem noun, but it loses the vowel 'е' when it declines. У кличному відмінку це слово стає **«майстре»**. Це дуже популярне професійне звертання в Україні. Ви можете сказати «пане майстре» людині, яка робить ремонт.

<!-- INJECT_ACTIVITY: fill-in, Form the correct vocative of professional titles and names (пане _____, пані _____), 8 items: (директор, вчителька, водій, професор, журналістка, Коваленко (m), Шевченко (f), секретар). -->

<!-- INJECT_ACTIVITY: match-up, Match nominative forms of professions to their vocative equivalents, 8 items: (лікар → лікарю, вчитель → вчителю, інженер → інженере, майстер → майстре, директорка → директорко, колега → колего, професор → професоре, водій → водію). -->

У школі почався перший урок.

> — **Вчителька:** Добрий день, діти! *(Good day, children!)* **Маріє** *(Maria)*, читай текст. **Андрію** *(Andrii)*, не розмовляй на уроці.
> — **Андрій:** Вибачте. *(I am sorry.)* Я більше не буду. *(I will not do it anymore.)*
> — **Марія:** **Пані вчителько** *(Mrs. Teacher)*, можна запитати? *(May I ask?)* Я не зрозуміла слово «звертання». *(I did not understand the word 'address'.)*
> — **Вчителька:** Добре, зараз поясню правило ще раз. *(Good, I will explain the rule again now.)*
> — **Андрій:** **Пані вчителько**, а що означає слово «колега»? *(Mrs. Teacher, and what does the word 'colleague' mean?)*
> — **Вчителька:** Це людина, з якою ти працюєш. *(This is a person with whom you work.)*


## Друже мій, люба моя: емоційний кличний (Emotional Vocative)

Українці дуже емоційні люди. Ми часто використовуємо кличний відмінок для вираження любові. Це робить нашу мову теплою і щирою. Коли ми говоримо з друзями, ми не використовуємо слово **«пан»** *(Mr.)* або **«пані»** *(Ms.)*. Ми використовуємо інші слова. Для чоловіка ми кажемо **«друже»** *(friend)*. Називний відмінок — це **«друг»**. Для жінки ми кажемо **«подруго»** *(friend)*. Називний відмінок — це **«подруга»**. У кличному відмінку жіноче закінчення **«-а»** змінюється на **«-о»**. Для дуже близьких людей ми маємо спеціальні слова. Чоловікові ми кажемо **«любий»** *(dear)*. Жінці ми кажемо **«люба»** *(dear)*. Якщо це ваш чоловік, дружина, хлопець або дівчина, ви використовуєте інші слова. Для чоловіка це слово **«коханий»** *(beloved)*. Для жінки це слово **«кохана»** *(beloved)*. Ці слова мають форму прикметників. In the vocative case, these adjectives retain their nominative forms. Тому ми просто кажемо: «Привіт, кохана!» або «Доброго ранку, любий!».

Українська мова має унікальну рису. Це магія зменшувально-пестливих суфіксів у кличному відмінку. Ukrainian diminutives are not just "baby talk". They are a standard and deeply cultural way to express affection and warmth to adults. Ми додаємо суфікси **«-енько»**, **«-ечко»** або **«-онько»** до звичайних слів. Слово **«серце»** *(heart)* стає словом **«серденько»** *(sweetheart / little heart)*. У кличному відмінку ми так звертаємося до коханої людини. Слово **«сонце»** *(sun)* стає словом **«сонечко»** *(sunshine / little sun)*. Ми часто кажемо «сонечко» дітям або партнерам. Слово **«зоря»** *(star)* стає словом **«зіронько»** *(little star)*. Ми також маємо теплі форми для родичів. Слово **«донька»** *(daughter)* у кличному відмінку стає формою **«донечко»** *(daughter)*. Слово **«син»** *(son)* має дуже ніжну форму **«синку»** *(son)*. Українці постійно використовують ці слова вдома. Коли мама кличе сина, вона не каже офіційне слово. Вона каже: «Синку, іди сюди!». Це показує її любов і турботу.

When expressing strong emotion, the word order in Ukrainian is critical. Якщо ви хочете сказати «my friend», ви використовуєте займенник **«мій»** *(my, masc)* або **«моя»** *(my, fem)*. Але є одне дуже важливе правило. In the vocative case, the possessive pronoun MUST follow the noun to sound natural and emotional. Ми кажемо: «Привіт, **друже мій**!». Ми ніколи не кажемо «Привіт, мій друже!». Це помилка. Слово «мій» завжди стоїть після іменника. Для жінки ми кажемо: «Добрий день, **люба моя**!». Ми не кажемо «моя люба». До мами ми звертаємося так: «**Мамо моя**!». До чоловіка жінка каже: «**Коханий мій**!». Placing the pronoun after the noun creates a very poetic, intimate, and authentic Ukrainian tone. It emphasizes the relationship rather than the ownership. Якщо ви скажете «мій друже», українці вас зрозуміють. Але це звучить як переклад з англійської мови. Щоб говорити як носій мови, завжди ставте займенник на друге місце.

Кличний відмінок — це також відмінок емоцій. Ми використовуємо його, коли ми здивовані, налякані або щасливі. Найпопулярніший вигук — це фраза **«Боже мій!»** *(My God!)*. Називний відмінок — **«Бог»** *(God)*. Ми також часто кажемо **«Господи!»** *(Lord!)*. Коли нам страшно, ми кричимо: **«Мамо!»** *(Mom!)*. Усі ці слова стоять у кличному відмінку. What about addressing multiple people? The rule is very simple. У множині кличний відмінок майже завжди має таку саму форму, як називний відмінок. Називний відмінок множини — **«друзі»** *(friends)*. Кличний відмінок — також **«Друзі!»**. Ви можете сказати: «Друзі, ходімо в кіно!». Слово **«колеги»** *(colleagues)* залишається формою **«Колеги!»**.

<!-- INJECT_ACTIVITY: error-correction, Fix vocative errors related to gender agreement and possessive word order, 8 items: (*Мій друже, *Друже моя, *пані лікар, *пане вчитель, *Моя люба, *Боже моя, *Тарас!, *пані Коваленку (f)). -->

Олег дзвонить своєму другові після візиту до лікаря.
> — **Олег:** Алло! **Друже мій** *(My friend)*, у мене прекрасні новини! *(I have wonderful news!)*
> — **Друг:** Привіт, Олеже! Що сталося? *(Hi, Oleh! What happened?)*
> — **Олег:** Уяви собі — я здоровий! *(Imagine — I am healthy!)* Лікар сказав, що я можу грати у футбол. *(The doctor said that I can play football.)*
> — **Друг:** Це чудово, Олеже! *(This is wonderful, Oleh!)* Я дуже радий за тебе. *(I am very glad for you.)*
> — **Олег:** Дякую, друже. *(Thank you, friend.)* Завтра йдемо на стадіон? *(Are we going to the stadium tomorrow?)*
> — **Друг:** Звісно! *(Of course!)* Бережи себе, **сонечко** *(Take care, sunshine)*.
> — **Олег:** Ха-ха, дуже смішно! *(Haha, very funny!)* До завтра! *(See you tomorrow!)*


## Який кличний обрати? (Choosing the Right Vocative)

Українська мова має дуже багатий вибір звертань *(forms of address)*. Як обрати правильну форму? Усе залежить від соціальної дистанції *(social distance)*. The vocative case acts as a social barometer in Ukrainian society. Якщо ви говорите з незнайомою людиною, використовуйте повну формальну форму. Ми завжди кажемо **«пане професоре»** *(Mr. professor)* або **«пані міністерко»** *(Madam minister)*. Це показує максимальну повагу. For professional interactions with a respectful distance, you can often drop the word "пан" or "пані". Ми часто кажемо просто **«лікарю»** *(doctor)* або **«вчителю»** *(teacher)*. Для колег та друзів ми використовуємо імена у кличному відмінку: **«Тарасе»** *(Taras)*, **«Оксано»** *(Oksana)*. Це дружній і комфортний рівень спілкування. А для найближчих людей ми маємо дуже емоційні слова. Ми кажемо **«друже мій»** *(my friend)* або **«серденько»** *(sweetheart)*. Switching between these registers instantly changes the relationship dynamic. Один чоловік може мати різні звертання. На роботі він — **«пане директоре»** *(Mr. director)*. Для колег він — **«Іване»** *(Ivan)*. А для дружини він — **«коханий мій»** *(my beloved)*. Ви можете бути формальним на роботі, але емоційним вдома. 

Давайте розглянемо кілька типових ситуацій *(typical situations)*. Ви пишете електронного листа професорові в університет. Ви повинні почати цей лист так: **«Вельмишановний пане професоре!»** *(Highly respected Mr. professor!)*. Це стандартна формальна ввічливість *(politeness)*. Ви їдете в таксі і хочете вийти. Ви ввічливо кажете: **«Пане водію, зупиніть тут»** *(Mr. driver, stop here)*. Маленька дитина плаче. Мама обіймає її і лагідно каже: **«Не плач, сонечко моє»** *(Don't cry, my sunshine)*. The vocative case is absolutely crucial for making a good first impression. Якщо ви використовуєте правильну форму, українці відразу бачать вашу повагу. Ввічливість відкриває багато дверей в Україні. Кожна ситуація вимагає свого унікального підходу. Ви не знаєте, яку форму обрати? Завжди починайте з формального звертання. Це найбезпечніший варіант для іноземця.

Які помилки часто роблять студенти? Найголовніша помилка — це використання називного відмінка після слів «пан» або «пані». Ніколи не кажіть «пан лікар» або «пан директор». Це звучить дуже неприродно і грубо. Ви завжди повинні використовувати кличний відмінок: **«пане лікарю»** *(Mr. doctor)*, «пане директоре». Ukrainian speakers find the absence of the vocative case jarring. It sounds overly "Russian-sounding" because modern Russian has entirely lost this grammatical case. The vocative case is a true shibboleth of natural Ukrainian speech. Коли ви використовуєте кличний відмінок, ви говорите як справжній носій мови *(native speaker)*. Це звучить красиво і дуже автентично. Не бійтеся робити помилки в закінченнях. Українці завжди оцінять ваше бажання говорити правильно. Головне — пам'ятайте про кличний відмінок і повагу до співрозмовника!

<!-- INJECT_ACTIVITY: quiz, Choose the correct vocative register for a given social situation, 8 items: (Email to a minister, greeting a neighbor, calling a best friend, addressing a judge in court, talking to a cat, greeting a colleague, asking a doctor for help, calling a waiter) -->
<!-- INJECT_ACTIVITY: group-sort, Sort various vocative forms into categories: Formal, Professional, or Emotional, 8 items: (пане Президенте, лікарю, донечко, пане Ковалю, люба моя, вчителько, пані директорко, серденько) -->


## Підсумок

У цьому модулі ми детально вивчили кличний відмінок *(vocative case)* для різних життєвих ситуацій. Ви тепер знаєте, як правильно показати свою глибоку повагу *(deep respect)* до іншої людини. Пам'ятайте найголовніше правило: після ввічливих слів «пан» або «пані» ми обов'язково використовуємо кличний відмінок. Ми завжди говоримо «пане директоре» та «пані вчителько». Ніколи не використовуйте називний відмінок *(nominative case)* після цих слів, бо це звучить як помилка!

Емоційні звертання *(emotional address)* до близьких людей також мають свої граматичні правила. Якщо ви використовуєте слово «мій» або «моя», воно завжди стоїть тільки після іменника *(noun)*. Правильна українська форма — це «друже мій» або «люба моя».

Перевірте себе *(check yourself)*. Дайте відповіді на ці п'ять запитань:
1. Як правильно звернутися до водія: «пан водій» чи «пане водію»?
2. Де стоїть слово «мій» у звертанні: перед чи після імені?
3. Чи змінюється прізвище *(surname)* жінки після слова «пані»?
4. Яка форма кличного відмінка для слова «колега»?
5. Чому використання кличного відмінка є ознакою ввічливості *(sign of politeness)* в Україні?

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: vocative-expanded
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

**Level: A2 (Module 27/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
