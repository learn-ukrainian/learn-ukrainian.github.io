<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/checkpoint-cases.yaml` file for module **64: Контрольна робота 5** (b1).

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

- `<!-- INJECT_ACTIVITY: fill-in-cases-review -->`
- `<!-- INJECT_ACTIVITY: match-up-prepositions-definitions -->`
- `<!-- INJECT_ACTIVITY: error-correction-prepositions -->`
- `<!-- INJECT_ACTIVITY: quiz-numerals-pronouns -->`
- `<!-- INJECT_ACTIVITY: reading-housing-analysis -->`
- `<!-- INJECT_ACTIVITY: essay-response-housing -->`
- `<!-- INJECT_ACTIVITY: quiz-diagnostics-phase6 -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Прочитайте текст про повторення: відмінки і дайте відповіді на запитання.'
  type: reading
- focus: 'Напишіть 5 речень, використовуючи нову лексику з розділу «Повторення: прийменники».'
  type: essay-response
- focus: 'Вставте правильну граматичну форму у реченнях на тему повторення: відмінки.'
  type: fill-in
- focus: 'Знайдіть і виправте помилки у реченнях на тему повторення: прийменники.'
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Повторення:
    відмінки».'
  type: quiz
- focus: 'З''єднайте терміни з розділу «Повторення: прийменники» з їхніми визначеннями.'
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- рубрика (rubric)
- аналіз помилок (error analysis)
- прогалина (gap — in knowledge)
required:
- повторення (review)
- самооцінка (self-assessment)
- комплексний (comprehensive)
- діагностика (diagnostics)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Повторення: відмінки

Welcome to the comprehensive review of Phase 6. In this section, we are moving beyond simple memorization of noun paradigms and focusing on semantic case roles. Understanding why we choose a specific case for a specific meaning is the key to natural fluency. For example, why do we use the Instrumental case to describe both the tool we write with and the path we travel on? It is because cases represent deeper relationships between words. Let us systematically review the advanced nuances of the Genitive, Dative, and Instrumental cases to ensure your foundation is solid before moving forward.

:::info
**Grammar box**
Cases in Ukrainian are not just grammatical requirements; they carry profound semantic meaning. Thinking in terms of "roles" (like the experiencer, the instrument, or the path) makes choosing the correct ending much more intuitive.
:::

Родовий відмінок є одним із найскладніших і найчастотніших в українській мові, оскільки він виконує багато різних семантичних функцій. Перша важлива функція — це частковий родовий відмінок, який вказує на невизначену частину від цілого. Ми використовуємо його, коли говоримо про речовини або матеріали, з яких беремо лише певну порцію. Наприклад, ми просимо налити склянку води, випити трохи чаю або додати цукру в каву. Ця функція тісно пов'язана з дієсловами, які виражають бажання, пошук, досягнення мети або страх. Коли ми чогось прагнемо або шукаємо, об'єкт нашого бажання часто є абстрактним або не повністю визначеним, тому він вимагає родового відмінка. Українці бажають щастя, здоров'я та успіху своїм друзям на великі свята. Студенти активно шукають правди або цікавої інформації під час підготовки до університетських семінарів. Люди часто бояться суцільної темряви, несподіваного іспиту або гучного грому під час грози. У всіх цих ситуаціях дієслова керують родовим відмінком, оскільки дія не охоплює предмет повністю, а лише частково або абстрактно торкається його. Це дуже природний спосіб вираження думки, який значно відрізняється від прямих конструкцій знахідного відмінка. Важливо запам'ятати ці специфічні дієслова, щоб ваше щоденне мовлення звучало максимально автентично та грамотно.

> *The Genitive case is one of the most complex and frequent in the Ukrainian language because it performs many different semantic functions. The first important function is the partitive genitive, which indicates an undefined part of a whole. We use it when talking about substances or materials from which we take only a certain portion. For example, we ask to pour a glass of water, drink some tea, or add sugar to coffee. This function is closely related to verbs expressing desire, search, achievement of a goal, or fear. When we desire or seek something, the object of our desire is often abstract or not fully defined, so it requires the genitive case. Ukrainians wish happiness, health, and success to their friends on big holidays. Students actively seek truth or interesting information while preparing for university seminars. People often fear total darkness, an unexpected exam, or loud thunder during a thunderstorm. In all these situations, verbs govern the genitive case because the action does not cover the object completely, but only partially or abstractly touches it. This is a very natural way of expressing thoughts, which differs significantly from direct accusative constructions. It is important to memorize these specific verbs so that your daily speech sounds as authentic and literate as possible.*

Друга фундаментальна функція родового відмінка базується на концепції відсутності, нестачі або логічного заперечення. Коли чогось немає в просторі чи часі, українська мова вимагає родового відмінка, оскільки те, що не існує, не може бути прямим об'єктом дії. Якщо у вас зараз немає вільного часу, ви завжди кажете про це саме через родовий відмінок. Так само ми будуємо заперечні речення з перехідними дієсловами, коли заперечення безпосередньо стосується всього об'єкта. Ви не бачили свого старшого брата, не читали цієї довгої статті або не зрозуміли нового складного правила. Присутність заперечної частки «не» автоматично змінює очікуваний знахідний відмінок на родовий, яскраво підкреслюючи повну відсутність результату. Крім того, родовий відмінок відіграє ключову роль у вираженні точного часу, а саме календарних дат. Коли ми називаємо конкретний день місяця, на який припадає певна подія, ми обов'язково використовуємо порядковий числівник у родовому відмінку. Ви народилися п'ятнадцятого березня, важлива зустріч відбудеться двадцять першого лютого, а зимове свято почнеться першого січня. Ця ж сувора логіка поширюється на вказівні займенники з різними часовими проміжками. Ми успішно завершили цей великий проєкт минулого тижня, минулого місяця або минулого року. Глибоке розуміння цієї семантики відсутності та часової приналежності дозволяє уникати дуже поширених помилок під час спілкування.

:::note
**Quick tip**
Always use the Genitive case for the specific day a calendar event happens, like **сьомого серпня** (on the seventh of August).
:::

One of the most persistent challenges for learners is choosing between the **-а/-я** and **-у/-ю** endings for masculine nouns in the Genitive singular. This is not a random linguistic quirk, but a highly logical categorization of the world. The **-а/-я** ending is reserved for concrete objects, living beings, clear geographic locations like cities, and measurable units. If a noun is a solid, distinct entity, it leans heavily towards this ending.

**Я бачу цього лікаря біля старого стола.** — *I see this doctor near the old table.*

In contrast, the **-у/-ю** ending is applied to abstract concepts, continuous processes, bulk materials, natural phenomena, and institutions. You cannot easily count or isolate the strict boundaries of abstract ideas or flowing substances. A useful mnemonic is to imagine whether the noun can be broken into distinct, countable pieces without losing its core identity. If it flows freely, represents an internal feeling, or is a sprawling concept, it generally requires the **-у/-ю** ending. 

**У нас немає вільного часу та дрібного піску.** — *We have no free time and fine sand.*

Mastering this underlying semantic split allows you to instinctively guess the correct ending for new vocabulary without constantly checking a dictionary.

Давальний відмінок найчастіше виступає в ролі суб'єкта стану або того, хто відчуває певні сильні емоції чи фізичні впливи. Також його класична функція — вказувати на адресата дії, наприклад, коли ми допомагаємо другові або телефонуємо лікарю. У поширених безособових конструкціях немає активного діяча в називному відмінку, натомість дія ніби відбувається сама собою і спрямовується безпосередньо на людину. Наприклад, коли взимку несподівано падає сніг, мені стає дуже холодно, а малій дитині завжди весело гратися надворі. Ми також постійно використовуємо давальний відмінок для позначення точного віку, оскільки роки просто непомітно додаються до нашого життя. Зараз мені рівно тридцять років, а моєму найкращому другові зовсім скоро виповниться двадцять п'ять. Крім того, давальний відмінок є невіддільною частиною тих безособових дієслів, які описують життєву необхідність, випадковий успіх або зовнішній примус. Сучасним студентам потрібно дуже багато вчитися, щоб скласти всі складні іспити максимально успішно. Вчора нам неймовірно пощастило знайти вільне затишне місце в кафе, але потім довелося досить довго чекати на офіціанта. У всіх цих життєвих випадках людина не контролює ситуацію безпосередньо, а лише пасивно сприймає її наслідки, відчуває необхідність або отримує результат обставин. Розуміння цієї специфічної ролі «сприймача» або «експериєнцера» допомагає будувати природні українські речення, які часто зовсім не мають прямих аналогів в англійській мові.

:::tip
**Did you know?**
In English, you say "I am cold," putting yourself as the active subject. Ukrainian uses the Dative "Experiencer" role: **мені холодно** (to me it is cold), treating the environment as the force acting upon you.
:::

Орудний відмінок також має багатий набір семантичних ролей, серед яких найважливішими є особиста характеристика, інструмент дії та шлях постійного руху. Коли ми говоримо про престижну професію, соціальний статус або тимчасову роль людини, орудний відмінок стає просто незамінним граматичним інструментом. Мій старший брат зараз працює талановитим архітектором, а його молода дружина дуже хоче стати відомою письменницею. Це зовсім не просто базовий опис, а чітка вказівка на певну важливу функцію, яку людина щодня виконує в сучасному суспільстві. Інша фундаментальна роль цього відмінка — це засіб або знаряддя, за допомогою якого людина фізично виконує певну дію. Ви можете легко написати довгий лист синьою кульковою ручкою, обережно різати свіжий хліб гострим ножем або впевнено керувати швидким автомобілем. Але орудний відмінок також чудово описує той відкритий простір, через який пролягає рух, тобто фізичний шлях. Ми дуже любимо довго гуляти тихим вечірнім містом, повільно іти великим тінистим парком або швидко їхати широкою асфальтованою дорогою. Важливо розуміти та чітко розрізняти ці граматичні нюанси. Їхати міським автобусом — це використання конкретного засобу пересування, тоді як їхати новою трасою — це рух певним визначеним шляхом. Крім того, деякі дієслова фіксовано вимагають орудного відмінка (керування). Українці часто кажуть, що вони щиро захоплюються мистецтвом, цікавляться сучасною історією або пишаються своїми талановитими дітьми. Ця унікальна багатогранність робить орудний відмінок одним із найвиразніших елементів української граматики, дозволяючи передавати тонкі деталі дії без використання додаткових прийменників.

<!-- INJECT_ACTIVITY: fill-in-cases-review -->

## Повторення: прийменники

When discussing time and duration, Ukrainian relies heavily on specific prepositions paired with precise grammatical cases. To express that an action will happen after a certain amount of time has passed, use the preposition **через** (in or after) followed by the Accusative case. If you want to emphasize that an action is completed within a specific timeframe, the preposition **за** with the Accusative case is required. For actions spanning an entire period continuously, you need **протягом** followed by the Genitive case. Finally, if something happens at the same time as an event, use **під час** with the Genitive case.

Я зазвичай закінчую працювати через годину, а потім відразу йду додому готувати вечерю. Мій найкращий друг може легко прочитати таку велику книгу лише за один тиждень. Протягом усього дня ми дуже багато спілкувалися з нашими новими клієнтами. Під час цієї важливої зустрічі ніхто не користувався мобільними телефонами.

> *I usually finish working in an hour, and then I immediately go home to cook dinner. My best friend can easily read such a big book in just one week. Throughout the whole day, we communicated a lot with our new clients. During this important meeting, no one used their mobile phones.*

Notice how the preposition **через** points to a future moment from now, while **за** focuses on the duration it takes to finish a specific task. The preposition **протягом** emphasizes the continuous nature of the time period, and **під час** points to a specific event during which something else happens. You will encounter these prepositions daily in both spoken and written Ukrainian. Mastering them will significantly improve your fluency and precision.

:::note
**Quick tip** — Use **через** for a point in the future ("in an hour"), and **за** for the duration it takes to complete a task ("within an hour").
:::

Establishing chronological order is another crucial linguistic skill. To say that something happens before an event, use **перед** combined with the Instrumental case. Its direct counterpart for events happening after a milestone is **після**, which always takes the Genitive case. When setting deadlines or boundaries, use the preposition **до** (until) with the Genitive case. However, when you are planning a duration for an activity or stating how long a state will last, use **на** (for) with the Accusative case.

Перед уроком я завжди купую свіжу гарячу випічку в маленькій місцевій пекарні біля університету. Після важкої роботи мені потрібно просто спокійно відпочити в повній тиші. Ми маємо обов'язково закінчити цей великий архітектурний проєкт до наступного вівторка. Я орендував цю затишну світлу квартиру в центрі міста рівно на місяць.

You must strictly pair these temporal prepositions with their assigned cases. Mixing them up completely changes the meaning or simply sounds incorrect to a native speaker. Pay special attention to the difference between a deadline and a planned duration. It is easy to make a mistake here if you translate directly from your native language.

Expressing causality requires sensitivity to the context and an understanding of the "Golden Rule" of Ukrainian decolonization. For negative or neutral causes, the most common preposition is **через** followed by the Accusative case. You can also use **від** for physical/emotional reactions (**від холоду**), **з** for motivation (**з поваги**), or formal terms like **внаслідок** and **у зв'язку з**. For positive outcomes where gratitude, success, or appreciation is implied, you must use **завдяки** with the Dative case. The preposition **із-за** used for causality is a direct Russianism and must be completely avoided in modern Ukrainian. You only use it for its true spatial meaning, like pulling something out from behind a physical object.

Ми не змогли поїхати високо в гори через дуже сильну снігову бурю на вихідних. Наш ранковий рейс несподівано скасували через погану погоду та густий туман. Але ми знайшли чудовий просторий готель завдяки своєчасній допомозі місцевих жителів. Завдяки вашим неймовірним зусиллям ми змогли швидко вирішити цю складну фінансову проблему.

Always ask yourself if the cause resulted in something beneficial or detrimental. If the outcome is good, give thanks by using the Dative-triggering preposition for gratitude. If the outcome is bad, use the neutral or negative Accusative-triggering preposition. This simple distinction makes your Ukrainian sound much more authentic and culturally aware.

:::tip
**Did you know?** — Using **із-за** to mean "because of" is a direct Russianism. In authentic Ukrainian, **із-за** is strictly a spatial preposition (e.g., coming out from behind a tree). Always use **через** or **завдяки** for causality.
:::

When you need to express the purpose of an object or an action, you have several distinct grammatical tools at your disposal. The preposition **для** (for) requires the Genitive case and usually indicates the intended user or the function of an object. The preposition **за** with the Instrumental case is heavily used in spoken language to mean fetching or going after something. However, the most authentic Ukrainian way to express fetching is using **по** with the Accusative case. Finally, to link an action with a specific goal, use the conjunction **щоб** followed by an infinitive verb.

Я купив цей новий товстий зошит спеціально для своїх щоденних робочих записів. Вранці мій старший брат швидко сходив за свіжою гарячою кавою до кав'ярні. Згодом я теж вирішив піти по чисту воду до найближчого джерела. Ми приїхали сюди лише для того, щоб нарешті підписати цей важливий контракт.

Using the correct purpose construction shows a high level of grammatical maturity. You should try to adopt the native fetching construction with the Accusative case whenever possible. It immediately signals that you are learning authentic Ukrainian rather than a mixed dialect. These small adjustments build a strong foundation for your future conversational skills.

:::info
**Grammar box** — While **сходити за кавою** (fetching coffee) is extremely common in modern speech, the prescriptive, traditional Ukrainian form uses **по** with the Accusative case: **піти по воду** or **піти по каву**.
:::

To elevate your speech from simple noun phrases to complex sentences, you can transform these prepositions into compound conjunctions. By adding the words **те що** to a preposition like **через**, or **тому що** to **завдяки**, you create a bridge that allows you to introduce an entire explanatory clause. This grammatical structure is absolutely essential for professional or academic communication where detailed explanations are regularly required. It gives you the freedom to explain complex situations with a subject and a conjugated verb.

Ми залишилися вдома ввечері через те, що раптово почалася дуже сильна злива. Наш новий проєкт став неймовірно успішним завдяки тому, що вся команда працювала дуже злагоджено. Вони змінили свої плани через те, що обставини несподівано погіршилися. Нам вдалося виграти цей престижний конкурс завдяки тому, що ми наполегливо готувалися.

You can think of these compound conjunctions as upgraded versions of their simple preposition counterparts. They carry the exact same positive or negative connotations as the base words. This means you still need to apply the "Golden Rule" when choosing between them. Practice building longer sentences this way to prepare for advanced discussions.

<!-- INJECT_ACTIVITY: match-up-prepositions-definitions -->
<!-- INJECT_ACTIVITY: error-correction-prepositions -->

## Повторення: кличний, числівники, займенники (~780 words total)

The Vocative case is crucial in Ukrainian for establishing professional respect. Unlike in some other languages, formal address frequently requires you to decline both the first name and the patronymic. For example, a male colleague named **Олександр Петрович** becomes **Олександре Петровичу**. A female colleague named **Ірина Іванівна** is addressed as **Ірино Іванівно**. Both parts take their respective Vocative endings.

Кличний відмінок є обов’язковим елементом офіційного спілкування. Якщо ви звертаєтеся до свого керівника, ви повинні завжди використовувати правильні закінчення. Використання називного відмінка у звертаннях звучить неприродно і грубо. Коли ви пишете лист, ви починаєте його словами «Шановний пане директоре». Ці граматичні деталі роблять вашу мову справжньою.

> *The Vocative case is a mandatory element of formal communication. If you are addressing your manager, you must always use the correct endings. Using the Nominative case in addresses sounds unnatural and rude. When you write a letter, you start it with the words "Respected Mr. Director". These grammatical details make your speech authentic.*

When using professional titles alongside a surname, the title takes the Vocative case. A male surname like **Петренко** also declines (**лікарю Петренку**), but for female professionals, the surname remains unchanged: **лікарю Петренко**. However, if you combine a polite word and a profession, both take the Vocative form: **пане професоре**. Mastering these nuances shows deep respect for cultural norms.

Matching nouns with numbers is a complex but essential skill. You must instinctively apply the one-two-five rule. The number **один** acts like an adjective, agreeing in gender, number, and case, requiring the Nominative Singular: **один стіл**. Numbers two through four require the noun to be in the Nominative Plural: **два столи**. However, numbers from five onwards demand that the following noun be in the Genitive Plural: **п'ять столів**.

Узгодження числівників з іменниками є фундаментом української граматики. Коли ви говорите про кількість предметів, ви завжди повинні думати про правильний відмінок. Ви маєте один великий будинок, два нові автомобілі та п'ять розумних студентів. Зверніть увагу на те, що слово «людина» в множині змінює свою основу. Ми кажемо «дві людини», але після п'яти ми використовуємо форму «людей».

:::info
**Grammar box** — The words **людина** (person) and **дитина** (child) have unique behaviors. For 2-4, use the standard forms **дві людини** and **три дитини**. For 5+, switch entirely to the plural stems: **п'ять людей** and **десять дітей**.
:::

Ordinal numerals indicate position in a sequence, such as first or second, and behave exactly like standard adjectives. They change their endings based on the gender, number, and case of the noun they describe. You decline them using the standard adjective tables: **до другого поверху** or **на третьому поверсі**.

Порядкові числівники допомагають нам орієнтуватися в часі та просторі. Ми використовуємо їх, коли називаємо дати, поверхи в будинку або сторінки в книзі. Для позначення точного часу ми використовуємо прийменник «о» з місцевим відмінком (о п'ятій годині) або «за» для позначення часу до події (за десять хвилин до початку). Якщо ви хочете сказати про частину чогось, ви використовуєте дроби. Українці дуже часто вживають слова «половина» і «чверть» у повсякденному житті.

Fractions present a different grammatical structure. Words like **половина** and **третина** are standard nouns followed by another noun in the Genitive case. A unique word you must master is **півтора** for masculine or neuter nouns, and its feminine equivalent **півтори**. This word uniquely forces the following noun into the Genitive Singular: **півтора року** or **півтори години**.

Pronouns hold complex sentences together. Your review must cover interrogative pronouns like **хто** and **чий**, as well as relative pronouns like **який** and **котрий**. Indefinite pronouns are formed by adding suffixes or prefixes. Words like **хтось** or **будь-хто** decline exactly like their base word **хто**.

Займенники роблять наше мовлення більш плавним і природним. Вони дозволяють нам уникати постійного повторення тих самих іменників. Заперечні займенники мають одну цікаву особливість. Коли ви використовуєте прийменник, він завжди стає між часткою «ні» та самим займенником. Це правило розщеплення є унікальним і дуже важливим.

The most critical rule involves negative pronouns like **ніхто**. When used with a preposition, the preposition physically splits the pronoun into three separate words. Instead of saying that you went with nobody as "з ніким", you must say **ні з ким**. Similarly, the word for "to no one" becomes **ні до кого**.

The reflexive pronoun **себе** is highly versatile, referring to the subject regardless of person or number. It has no Nominative form because it can never be the subject. It declines like the pronoun **ти**: Genitive and Accusative are **себе**, Dative is **собі**, and Instrumental is **собою**.

Зворотний займенник «себе» показує, що дія спрямована на саму людину, яка її виконує. Ми часто використовуємо форму давального відмінка «собі» в розмовному стилі, щоб підкреслити особистий інтерес. Наприклад, ви можете сказати, що просто гуляєте собі по парку. Це робить ваше мовлення дуже природним та розслабленим.

:::tip
**Did you know?** — Definitive pronouns like **сам** (oneself, alone) and **увесь** (all, whole) help emphasize the completeness of an action. They decline like hard or soft adjectives, adding strong emphasis to the noun they modify.
:::

<!-- INJECT_ACTIVITY: quiz-numerals-pronouns -->

## Комплексні завдання

Житловий ринок сучасної України переживає значні зміни, особливо у великих містах, як Київ та Львів. Історично склалося так, що квартири у цих містах мали великий попит. Протягом останніх років ця ситуація стала ще динамічнішою. Завдяки інвестиціям у міське будівництво з'явилося багато сучасних житлових комплексів. Однак через економічні коливання вартість оренди значно зросла. Сьогодні бути власником квартири в центрі міста — це розкіш. Більшість людей віддають перевагу довгостроковій оренді, підписуючи контракти на рік.

Для сучасних орендарів найважливішим фактором є не лише ціна, але й інфраструктура. Вони шукають квартири заради особистого комфорту та безпеки. Наявність паркінгу, укриття та автономного опалення стала критичною вимогою. Через те що багато людей працюють дистанційно, їм потрібен стабільний інтернет. Вартість оренди однокімнатної квартири у Львові може досягати вісімнадцяти тисяч гривень на місяць. У Києві ціни бувають ще вищими.

Після підписання договору оренди нові мешканці отримують ключі та заселяються. Перед переїздом дуже важливо перевірити технічний стан меблів. Багато власників вимагають депозит у розмірі вартості двох місяців оренди. Згідно з законодавством такий договір захищає права обох сторін. Орендарі зобов'язані вчасно платити за комунальні послуги. Завдяки цим правилам процес оренди стає прозорим і безпечним.

> *The housing market of modern Ukraine is experiencing significant changes, especially in large cities like Kyiv and Lviv. Historically, apartments in these cities have been in high demand. Over the past few years, this situation has become even more dynamic. Thanks to investments in urban construction, many modern residential complexes have appeared. However, due to economic fluctuations, the cost of rent has increased significantly. Today, being the owner of an apartment in the city center is a luxury. The majority of people prefer long-term renting, signing contracts for a year.*
>
> *For modern tenants, the most important factor is not only the price, but also the infrastructure. They look for apartments for the sake of personal comfort and security. The presence of parking, a shelter, and autonomous heating has become a critical requirement. Because many people work remotely, they need stable internet. The cost of renting a one-room apartment in Lviv can reach eighteen thousand hryvnias per month. In Kyiv, prices are often even higher.*
>
> *After signing the lease agreement, the new residents receive the keys and move in. Before moving, it is very important to check the technical condition of the furniture. Many owners require a deposit in the amount of the cost of two months of rent. According to the legislation, such a contract protects the rights of both parties. Tenants are obliged to pay for utility services on time. Thanks to these rules, the rental process is becoming transparent and safe.*

<!-- INJECT_ACTIVITY: reading-housing-analysis -->

> — **Професор:** Добрий день, шановні студенти! Пане Олександре, ви готові почати вашу презентацію про сучасну урбаністику? *(Good day, dear students! Mr. Oleksandr, are you ready to start your presentation on modern urban studies?)*
> — **Олександр:** Так, пане професоре! Сьогодні я розповім про міський простір. Нам важливо зрозуміти, як інфраструктура впливає на людей. *(Yes, Professor! Today I will talk about urban space. It is important for us to understand how infrastructure affects people.)*
> — **Професор:** Які дані ви використовували для дослідження? *(What data did you use for the research?)*
> — **Олександр:** Двоє дослідників зібрали статистику щодо нових районів Києва. Завдяки їхній роботі, ми маємо точні цифри. *(Two researchers collected statistics regarding the new districts of Kyiv. Thanks to their work, we have exact numbers.)*
> — **Професор:** Які головні проблеми ви виявили? *(What main problems did you discover?)*
> — **Олександр:** Найбільша проблема — це постійні затори. Через велику кількість автомобілів мешканцям важко дістатися до центру. *(The biggest problem is constant traffic jams. Due to the high number of cars, it is difficult for residents to reach the center.)*

One of the most important steps in mastering B1 Ukrainian is clearing your speech of linguistic ghosts—grammatical structures from Russian that haunt the language of many learners. These calques, or loan translations, often slip into speech because they use familiar Ukrainian vocabulary but apply a completely foreign grammatical logic. To speak naturally, you must learn the unique case government of Ukrainian verbs and prepositions.

Let us examine the verb **сміятися** (to laugh). A very common mistake is saying **сміятися над другом** using the Instrumental case. This is a direct copy of the Russian structure. The authentic Ukrainian phrase requires the preposition **з** followed by the Genitive case: **сміятися з друга**. This subtle shift in prepositions changes your speech from sounding translated to sounding completely native.

Another frequent trap is the verb **дякувати** (to thank). In English, you thank someone as a direct object, and in Russian, you use the Accusative case for the person you are thanking. However, in Ukrainian, **дякувати** always demands the Dative case, indicating the recipient of your gratitude. You must say **дякую вам**, never **дякую вас**. Using the Accusative case here is a grammatical error that immediately flags your speech as unnatural.

Similarly, the verb **навчатися** (to study) specifically requires the Genitive case. While a learner might be tempted to say **навчатися музиці** (Dative) due to Russian interference, the correct form is **навчатися музики** (Genitive). Remembering these specific combinations is essential for passing the B1 checkpoint.

:::info
**Grammar box** — Always double-check verb government when learning new words. Make a firm habit of memorizing the required preposition and case alongside the infinitive form, such as **дякувати (кому?)**, **навчатися (чого?)**, and **сміятися (з кого?)**.
:::

Now it is time to put all your theoretical knowledge of cases, prepositions, and numerals into practical use. Imagine you are relocating to Lviv for a new job and need to find an apartment. You have found a suitable option online and must write a formal email to the landlord, Pan Sydorenko. Your message needs to be polite, grammatically precise, and clear about your housing expectations.

In your email, you must use the Vocative case for the greeting, demonstrating your cultural respect. You also need to employ cause and purpose prepositions like **для** (for), **протягом** (during), and **через те що** (because of the fact that) to accurately explain your situation. Additionally, you will have to correctly decline numerals to state your budget and specify the exact address you are interested in.

When drafting your response, consider the following structure. First, address the landlord using the formal Vocative case: **Шановний пане Сидоренку!**. Next, introduce yourself and explain why you are writing: **Я пишу вам через те що...**. Then, state how long you plan to rent the apartment: **протягом року** or **на півтора року**. Mention what is important to you in the apartment, using the Genitive case for purpose: **для комфортної роботи**. Finally, confirm the price you saw in the advertisement, ensuring the numeral agrees with the noun **гривень**.

This exercise tests your ability to synthesize everything you have learned in this phase. Precise case usage is not just an academic exercise; it is the foundation of effective, professional communication in Ukrainian.

<!-- INJECT_ACTIVITY: essay-response-housing -->

## Самооцінка та підготовка до Фази 7

Welcome to the final stage of Phase 6. Before moving forward, it is crucial to honestly evaluate your grasp of the concepts we have covered. This self-assessment matrix is designed to help you pinpoint exactly where your strengths lie and which areas require a little more attention. Ask yourself a few diagnostic questions. Can I confidently use the Genitive case for partitive meanings, negation, and dates? For example, if you want a glass of water, do you automatically think of the partitive Genitive and say «склянка води», or do you accidentally use the Nominative? Can I accurately apply the Dative case for experiencers and age? If you need to say that you feel cold, the correct form is «мені холодно», using the Dative pronoun. Can I correctly deploy the Instrumental case for characterization and means? When talking about your profession, you should say «я працюю лікарем». Furthermore, can I seamlessly integrate temporal and cause prepositions into my sentences? If you want to say "because of the rain," do you correctly choose «через дощ», avoiding Russian-influenced structures? Finally, can I decline numerals to express exact dates and quantities?

Регулярна самооцінка та діагностика власних знань є дуже важливими. Коли ви аналізуєте свої навички, звертайте увагу на дрібні деталі. Якщо у вас є певна прогалина в знаннях, наприклад, ви відчуваєте невпевненість під час вибору між закінченнями «-а» та «-у» в родовому відмінку чоловічого роду, це нормально. Ця тема є однією з найскладніших в українській граматиці. Головне правило полягає в тому, щоб не намагатися завчити всі слова напам'ять з таблиць. Натомість запам'ятовуйте нову лексику в контексті або у складі сталих словосполучень. Якщо ви робите помилки у виборі прийменників причини чи мети, перегляньте ваші власні тексти та виправте їх. Такий аналіз помилок і комплексна практика з реальними реченнями набагато ефективніші за просте читання граматичних довідників.

> *When you analyze your skills, pay attention to small details. If you feel unsure when choosing between the "-а" and "-у" endings in the masculine Genitive case, this is absolutely normal. This topic is one of the most difficult in Ukrainian grammar. The main rule is not to try to memorize all the words by heart from tables. Instead, memorize new vocabulary in context or as part of fixed phrases. If you make mistakes in choosing prepositions of cause or purpose, review your own texts and correct them. Practice with real sentences is much more effective than simply reading grammar reference books.*

Identifying a gap in your knowledge is the first step toward true fluency. If you realize that masculine Genitive endings still confuse you, or if prepositional cases feel like guesswork, change your study strategy. Instead of staring at declension charts, start drilling with context. Create personalized sentences about your daily life. For instance, instead of trying to remember that the word for sugar takes an «-у» ending, write down «я п'ю каву без цукру» and practice saying it aloud. Contextual drilling anchors the grammar to real-world situations, making the correct forms sound natural to your ear over time. Whenever you learn a new verb, always write down the preposition and case it requires.

:::tip
**Quick tip** — Create a dedicated notebook section exclusively for your "frequent flyers." Write down the top ten words or phrases you consistently decline incorrectly and review them for just one minute every morning.
:::

Looking ahead, we are preparing to cross the bridge into Phase 7, where your mastery of cases will be put to the ultimate test. In the next modules, we will introduce participles, known as «дієприкметники». These fascinating words act as adjective-verb hybrids. They describe a noun while simultaneously conveying an action. Because they function like adjectives, they must agree with the noun they modify in gender, number, and case. This is why a solid foundation from Phase 6 is non-negotiable. If your underlying case knowledge is shaky, building these complex modifiers will be incredibly frustrating.

Орудний відмінок відіграватиме важливу роль під час вивчення пасивних дієприкметників. Коли ви захочете сказати, що лист був написаний директором, вам доведеться використати орудний відмінок для позначення виконавця дії. Без чіткого розуміння того, як формується цей відмінок, ви не зможете правильно будувати такі конструкції. Крім того, усі ті нюанси прийменників, які ви щойно повторили, стануть органічною частиною довгих речень. Ваша здатність швидко обирати правильний відмінок дозволить вам говорити плавно та впевнено.

> *The Instrumental case will play an extremely important role when studying passive participles. When you want to say that the letter was written by the director, you will have to use the Instrumental case to indicate the performer of the action. Without a clear understanding of how this case is formed, you will not be able to build such constructions correctly. Furthermore, all those nuances of prepositions that you have just reviewed will become an organic part of long sentences. Your ability to quickly choose the correct case will allow you to speak fluently and confidently.*

Take your time with the final diagnostic quiz below. Treat it as a comprehensive check of your readiness for the advanced syntax that awaits you. If you pass this comfortably, 

<!-- INJECT_ACTIVITY: quiz-diagnostics-phase6 -->

## Підсумок

You have reached the end of Phase 6, a significant milestone in your Ukrainian journey. You have moved far beyond basic object identification. Now, you are capable of expressing complex relationships with confidence. You can articulate nuances of cause and purpose, describe the means and path of an action, and control the precise temporal flow of your narratives. Furthermore, you have mastered the formal vocative case, allowing you to show deep respect in professional settings. You have also tackled the intricate agreement rules of Ukrainian numerals. This level of precision—this comprehensive "Case Mastery"—is exactly what distinguishes a solid B1 learner from a casual speaker. It proves that you are actively thinking within the structural logic of the Ukrainian language.

Цей етап вимагав від вас значних зусиль, адже українська система відмінків не пробачає неуважності. Тепер ви чітко розумієте, що правильний вибір прийменника може кардинально змінити зміст сказаного. Ви навчилися відчувати мову глибше та будувати граматично правильні речення.

> *This stage required significant effort from you, because the Ukrainian case system does not forgive inattention. Now you clearly understand that the correct choice of a preposition can radically change the meaning of what is said. You have learned to feel the language more deeply and to build grammatically correct sentences.*

Before we officially close this chapter, take a moment to do a final check of your grammatical instincts:

* Can you confidently distinguish when a masculine noun takes the «-а»/«-я» ending versus the «-у»/«-ю» ending in the Genitive case?
* Do you instinctively use «завдяки» for positive causes, leaving «через» for negative ones?
* Can you flawlessly address a university professor as «Пане професоре, Іване Петровичу»?
* Do you correctly split your negative pronouns with prepositions, saying «ні з ким»?

:::info
**Self-Correction** — True mastery is not about being flawless. It is about recognizing your own errors the moment they happen and knowing exactly how to fix them.
:::

If you can confidently answer "yes" to these questions, you are ready for Phase 7. The upcoming modules will introduce participles and gerunds. In these new structures, your rock-solid understanding of cases will serve as the essential foundation for building sophisticated modifiers.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: checkpoint-cases
level: b1

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

**Level: B1 (Module 64)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
