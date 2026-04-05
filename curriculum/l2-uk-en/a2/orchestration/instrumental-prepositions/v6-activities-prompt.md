<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/instrumental-prepositions.yaml` file for module **28: Над, під, між** (a2).

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

- focus: Complete location sentences with correct preposition + Instrumental noun
    form
  items: 8
  type: fill-in
- focus: Match prepositions (над, під, перед, за, між) to pictures showing spatial
    relationships
  items: 8
  type: match-up
- focus: Distinguish spatial vs. temporal meaning of перед and за
  items: 8
  type: quiz
- focus: Judge whether location descriptions match a room diagram
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- стеля (ceiling)
- підлога (floor)
- кут (corner)
- розклад (schedule)
- сон (sleep, dream)
required:
- над (above, over)
- під (under, below)
- перед (in front of; before (temporal))
- за (behind; according to)
- між (between)
- стіл (table)
- будинок (building, house)
- ліжко (bed)
- стіна (wall)
- обід (lunch)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Просторові прийменники: Де це? (Spatial Prepositions: Where Is It?)

Ми часто використовуємо просторові прийменники. Вони показують точне місце предмета або людини. *(We often use spatial prepositions. They show the exact location of an object or a person.)* Сьогодні ми вивчимо п'ять дуже важливих прийменників: **над** *(above/over)*, **під** *(under/below)*, **перед** *(in front of)*, **за** *(behind)*, та **між** *(between)*. These five prepositions are absolutely essential for describing the physical space around you. Усі ці прийменники вимагають орудного відмінка, коли ми відповідаємо на питання «Де?». *(All these prepositions require the Instrumental case when we answer the question "Where?".)* Let's quickly recap the Instrumental endings for nouns to set the grammatical stage. Чоловічий та середній рід зазвичай мають закінчення **-ом** або **-ем** / **-єм**. Наприклад, **стіл** *(table)* стає столом, а **вікно** *(window)* стає вікном. Жіночий рід завжди отримує закінчення **-ою** або **-ею** / **-єю**. Наприклад, **стіна** *(wall)* стає стіною. У множині ми завжди використовуємо закінчення **-ами** або **-ями**. Наприклад, **двері** *(doors)* стають дверима.

Прийменник **над** означає, що один предмет знаходиться вище за інший предмет у просторі. *(The preposition над means that one object is located higher than another object in space.)* The preposition "над" describes a vertical relationship where objects do not touch each other. Дуже важливо не плутати його з прийменником «на». *(It is very important not to confuse it with the preposition "on".)* Якщо предмет лежить прямо на поверхні, ми кажемо «на столі». *(If an object lies right on a surface, we say "on the table".)* Але якщо предмет висить високо у повітрі, ми кажемо «над столом». *(But if an object hangs high in the air, we say "above the table".)* **Лампа** *(lamp)* яскраво світить над столом у вітальні. **Птахи** *(birds)* швидко летять над глибоким **морем** *(sea)*. Великі **хмари** *(clouds)* повільно пливуть над високими **горами** *(mountains)*. Моя нова квартира знаходиться над великим магазином. Гарна картина висить на стіні над моїм ліжком.

Прийменник **під** є повною протилежністю до прийменника «над». *(The preposition під is the exact opposite of the preposition "над".)* Він означає, що предмет знаходиться значно нижче або він повністю схований. *(It means that an object is located significantly lower or it is completely hidden.)* The preposition "під" is used for objects that are underneath something else, often resting on the floor or covered. Мій пухнастий **кіт** *(cat)* солодко спить під **стільцем** *(chair)*. Старий **килим** *(carpet)* лежить під великим **ліжком** *(bed)*. Ми випадково знайшли мій м'яч під диваном. Маленький собака ховає свою кістку під столом. Під цим високим **будинком** *(house/building)* є дуже темний **підвал** *(basement)*. Веселі діти граються в хованки під старим деревом. Я завжди тримаю свої теплі капці під ліжком.

Прийменники **перед** та **за** допомагають нам описати перспективу людини. *(The prepositions перед and за help us describe a person's perspective.)* The use of "перед" and "за" often depends on where the speaker is standing or the natural front of an object. Прийменник «перед» означає, що об'єкт знаходиться спереду. *(The preposition "перед" means that an object is located in the front.)* Велике зелене дерево росте прямо перед моїм вікном. Нова синя машина стоїть перед нашим будинком. Прийменник «за» означає, що об'єкт знаходиться позаду іншого об'єкта. *(The preposition "за" means that an object is located behind another object.)* Гарний зелений **сад** *(garden)* знаходиться відразу за будинком. Темний ліс починається далеко за широкою річкою. Уявіть, що ви довго стоїте в **черзі** *(queue)*. *(Imagine that you are standing in a queue for a long time.)* Ви стоїте перед жінкою, а високий чоловік стоїть за вами. Хтось довго стоїть за зачиненими дверима.

Прийменник **між** має свою власну особливу логіку використання у реченнях. *(The preposition між has its own special logic of use in sentences.)* This preposition usually links two distinct objects to show that something is directly in the middle. Коли ми використовуємо слово «між», ми зазвичай з'єднуємо два предмети сполучником «і». *(When we use the word "між", we usually connect two objects with the conjunction "and".)* Both of these linked objects must be in the Instrumental case. Новий міський парк знаходиться між школою і **бібліотекою** *(library)*. Мій улюблений стілець стоїть між столом і великою **шафою** *(wardrobe)*. Маленький дерев'яний столик стоїть між ліжком і білою стіною. Ми також можемо легко використовувати цей прийменник з іменниками у множині. *(We can also easily use this preposition with nouns in the plural.)* Старе історичне місто лежить між високими горами. Швидка машина їде між великими сірими будинками.

<!-- INJECT_ACTIVITY: match-up, Match prepositions (над, під, перед, за, між) to 8 illustrations showing spatial relationships -->


## Описуємо кімнату

Зараз ми вивчимо нові слова, щоб детально описувати кімнату. *(Now we will learn new words to describe a room in detail.)* У кожній кімнаті є різні предмети інтер'єру. Почнемо зі слів чоловічого роду: **кут** *(corner)*, **стіл** *(table)*, **камін** *(fireplace)*, **килим** *(carpet)*. В орудному відмінку ці іменники мають типове закінчення -ом: кутом, столом, каміном, килимом. Тепер розглянемо важливі слова жіночого роду: **стіна** *(wall)*, **шафа** *(wardrobe)*, **полиця** *(shelf)*, **картина** *(painting)*. В орудному відмінку вони отримують закінчення -ою або -ею: стіною, шафою, полицею, картиною. Зверніть увагу також на слова середнього роду: **вікно** *(window)*, **ліжко** *(bed)*, **дзеркало** *(mirror)*. Їхні форми в орудному відмінку також завжди мають закінчення -ом: вікном, ліжком, дзеркалом. Ми часто використовуємо всі ці слова з просторовими прийменниками. Це прийменники «над», «під», «між», «перед» та «за». Ці прийменники з орудним відмінком допомагають нам дуже точно сказати локацію. Де саме знаходиться конкретний предмет у просторі? Ми зараз це побачимо.

Коли ми шукаємо певний предмет у будинку, ми зазвичай запитуємо: «Де?». *(When we look for a specific object in a house, we usually ask: "Where?".)* Для побудови правильної відповіді ми використовуємо іменник у називному відмінку. Потім ми додаємо відповідний прийменник і друге слово в орудному відмінку. Наприклад, хтось запитує вас: «Де висить велике дзеркало?». Повна і правильна відповідь буде звучати так: «Дзеркало висить над **умивальником** *(sink)*». Або ви довго шукаєте свій новий телефон і тривожно питаєте: «Де мій телефон?». Відповідь може бути такою: «Твій телефон лежить на підлозі під зеленим килимом». Це дуже природний та логічний спосіб описувати простір навколо нас. Коли ми кажемо «Мій кіт спокійно спить за великою шафою», ми даємо точну інформацію. Ми допомагаємо іншій людині швидко знайти потрібне місце. Використання таких повних речень робить ваше мовлення багатим і зрозумілим.

> — **Макс:** Олено, де ми поставимо цей великий новий стіл? *(Olena, where will we put this big new table?)*
> — **Олена:** Давай поставимо наш стіл прямо перед великим вікном. Там ми будемо працювати, і тут буде світло. *(Let's put our table right in front of the big window. We will work there, and it will be light here.)*
> — **Макс:** Це справді дуже добра ідея. А куди нам повісити цю нову яскраву лампу? *(That is really a very good idea. And where should we hang this new bright lamp?)*
> — **Олена:** Будь ласка, повісь лампу високо на стелі прямо над столом. Вона буде добре світити. *(Please, hang the lamp high on the ceiling right above the table. It will shine well.)*
> — **Макс:** Добре, я зроблю це. А де буде лежати наш старий пухнастий килим? *(Okay, I will do this. And where will our old fluffy carpet lie?)*
> — **Олена:** Нехай цей килим лежить на підлозі під столом. Там дуже затишно і тепло ногам. *(Let this carpet lie on the floor under the table. It is very cozy and warm for the feet there.)*
> — **Макс:** Супер! У нас залишилася тільки одна річ. Де стоятиме ця полиця для книг? *(Super! We have only one thing left. Where will this bookshelf stand?)*
> — **Олена:** Постав її в кут між вікном і широкими дверима. Це ідеальне місце. *(Put it in the corner between the window and the wide door. It is the perfect place.)*

Тепер давайте уявимо собі ідеальну кімнату для роботи та відпочинку. *(Now let's imagine a perfect room for work and rest.)* У моїй кімнаті великий дубовий стіл стоїть прямо перед яскравим вікном. Над цим столом висить дуже гарна і сучасна картина. Під столом на підлозі завжди солодко спить мій маленький собака. Між високою шафою і широкими дверима стоїть велике дзеркало. За зручним ліжком у кутку є теплий камін. Перед цим каміном завжди лежить м'який червоний килим. На світлій стіні над каміном висить довга полиця з книгами. Між цією полицею і моїм ліжком стоїть маленька дерев'яна тумбочка. Цей детальний опис допомагає швидко створити чітку картинку в голові. Ви бачите, що кожен важливий предмет має своє власне логічне місце. Ви можете легко описати свою власну кімнату друзям. Для цього просто використовуйте ці нові граматичні правила. Спробуйте розказати про свою вітальню або спальню.

<!-- INJECT_ACTIVITY: true-false, Judge whether 8 location descriptions match a provided room diagram -->


## Перед обідом, за розкладом: Часове значення (Before Lunch, On Schedule: Temporal Meaning)

Ми вже знаємо, як описувати простір. Але прийменники також можуть описувати час. Ми часто використовуємо прийменник **перед** *(before)* для опису часу. The preposition «перед» means "before" and is used with the Instrumental case to describe an action that happens immediately prior to an event. You might already know the preposition «до» *(until/before)*, which takes the Genitive case. However, «перед» is much more specific. It emphasizes that one action happens right on the threshold of another. Наприклад, ми кажемо **перед обідом** *(before lunch)* або **перед сном** *(before sleep)*. Це означає дію прямо перед подією. Я завжди читаю цікаву книгу перед сном. Максим часто п'є воду перед виходом з дому. Це дуже корисне правило для щоденного розкладу. You will hear native speakers use «перед» with the Instrumental case constantly when talking about their daily routines.

Давайте розглянемо нашу щоденну рутину. У нашому житті є багато регулярних дій. Ми постійно повторюємо їх кожного дня. Ми використовуємо прийменник «перед» разом з орудним відмінком дуже часто. Ось найпопулярніші короткі фрази, які вам треба запам'ятати:
*   Мити брудні руки **перед їдою** *(before a meal)*.
*   Читати цікаву нову книгу перед сном.
*   Пити міцну гарячу каву **перед роботою** *(before work)*.
*   Робити легку ранкову зарядку **перед сніданком** *(before breakfast)*.
*   Уважно повторювати нові слова **перед уроком** *(before class)*.
*   Купувати дешеві квитки **перед відпусткою** *(before vacation)*.

Ці готові вирази надзвичайно зручні. Ви можете сміливо використовувати їх щодня у різних ситуаціях. Наприклад: «Я завжди ретельно мию руки перед їдою». Або: «Моя молодша сестра дуже любить гуляти перед сном». Використання таких конструкцій робить ваше мовлення швидким і природним. Спробуйте запам'ятати ці короткі вирази як цілі блоки слів.

Ще один дуже важливий прийменник — це **за** *(according to, on)*. Another spatial preposition that shifts to a conceptual or temporal meaning is «за». When used with the Instrumental case in this context, it describes the manner or timing of an action relative to a formal structure or rule. Це означає, що подія відбувається за правилом. Найкращі приклади — це корисні фрази **за розкладом** *(on schedule)* та **за планом** *(according to plan)*. Наш швидкий поїзд завжди прибуває на головний вокзал чітко за розкладом. Усе йде за планом, ми зовсім не маємо ніяких проблем. Ми також часто кажемо **за правилами** *(according to the rules)*. Всі розумні студенти повинні грати в гру тільки за правилами. In English, you might translate this specific usage as "by," "according to," or "on." The grammar rules remain exactly the same as the spatial «за» *(behind)*. Ми просто змінюємо контекст і його значення. Університет працює за розкладом, а наш старий автобус завжди запізнюється.

Тепер давайте уважно порівняємо два різних значення цих слів. Прийменники можуть легко показувати простір або час і спосіб. Граматика завжди залишається однаковою для обох варіантів. Ми завжди використовуємо форму орудного відмінка. Але загальний сенс речення повністю змінюється. «Перед високим будинком» *(in front of the tall building)* — це місце і фізичний простір. Нова машина спокійно стоїть перед будинком. «Перед цікавим уроком» *(before the interesting lesson)* — це час. Студенти весело розмовляють перед уроком. Те саме правило стосується короткого прийменника «за». «За будинком» *(behind the building)* — це знову місце. А «за планом» *(according to plan)* — це спосіб або час дії. Ця граматична система працює дуже логічно і стабільно. Ви обов'язково швидко звикнете до неї.

<!-- INJECT_ACTIVITY: quiz, Distinguish spatial vs. temporal meaning of перед and за -->


## Практика: Де? Коли? (Practice: Where? When?)

Уявіть собі звичайну щоденну ситуацію: ви бачите пухнастого кота у кімнаті. Де він зараз знаходиться? Він спокійно сидить **під столом** *(under the table)*. Ми ставимо просте питання: «Де?» *(Where?)*. Відповідь на це питання завжди вимагає орудного відмінка. Але ми знаємо, що кіт не завжди сидить на одному місці. Він також любить активно рухатися кімнатою. Що він робить зараз? Він швидко лізе під стіл. Тепер ми ставимо зовсім інше питання: «Куди?» *(Where to?)*. Відповідь на питання напрямку вже вимагає знахідного відмінка. This is a very important and beautiful distinction in Ukrainian grammar. When there is no movement and we describe a static, unmoving location, we use the Instrumental case with spatial prepositions like «під», «над», and «за». These prepositions perfectly capture the physical relationships between objects in space. Наприклад: кіт лежить під ліжком. Стара картина висить над столом. Великий собака спить за будинком. Це все статичні позиції. However, when there is active motion toward a specific destination, these exact same prepositions suddenly shift their behavior and take the Accusative case instead. The case change signals the movement. Кіт біжить під ліжко. Ми вішаємо картину над стіл. Собака біжить за будинок. In this specific module, we focus exclusively on the static location aspect. You do not need to master the motion rules yet. Пам'ятайте одне дуже просте правило: питання «Де?» завжди надійно працює з орудним відмінком.

Тепер давайте значно детальніше розглянемо дуже популярний короткий прийменник «за». Цей маленький прийменник насправді має два абсолютно різні значення в українській мові. Перше значення — це конкретний фізичний простір. Наприклад, щось знаходиться **за школою** *(behind the school)*, **за парком** *(behind the park)* або **за високим деревом** *(behind the tall tree)*. Це знову наше знайоме просторове питання «Де?», тому ми впевнено використовуємо форму орудного відмінка. Друге значення — це мета, причина або абстрактна подяка. Наприклад, ми кожного дня часто кажемо друзям: **«Дякую за каву»** *(Thank you for the coffee)* або **«Дякую за допомогу»** *(Thank you for the help)*. Learners often make the logical but incorrect assumption that they should use the Instrumental case here as well, since they just learned that «за» requires it. However, when «за» means "for" or indicates a reason, purpose, or exchange, it strictly always takes the Accusative case. This semantic contrast is a core feature of the language that prevents confusion between location and reason. Ніколи не кажіть «Дякую за кавою» або «Дякую за допомогою»! Це досить серйозна граматична помилка. Граматика української мови завжди дуже чітко розділяє ці дві різні ситуації. Простір і місцезнаходження — це орудний відмінок. Причина, мета і подяка — це тільки знахідний відмінок. Запам'ятайте цю різницю назавжди.

Давайте уважно подивимося, як ці важливі просторові правила працюють у реальному щоденному житті. Уявіть, що ви зараз гуляєте новим містом. Ви дуже шукаєте аптеку і хочете запитати дорогу на вулиці.

> — **Турист:** Перепрошую, ви не підкажете, де тут знаходиться найближча **аптека** *(pharmacy)*?
> — **Місцевий:** Так, звісно, я можу допомогти. Вона зовсім поруч звідси. Ви бачите той великий червоний театр?
> — **Турист:** Так, бачу. Він стоїть прямо **перед нами** *(in front of us)*.
> — **Місцевий:** Чудово. Нова аптека знаходиться відразу **за театром** *(behind the theater)*.
> — **Турист:** Зрозуміло, дякую! Це далеко йти пішки?
> — **Місцевий:** Ні, це дуже близько, одна хвилина. Вона стоїть точно **між банком** *(between the bank)* і **поштою** *(and the post office)*. Ви її легко побачите.
> — **Турист:** Тепер я знаю дорогу. Дуже дякую за допомогу!
> — **Місцевий:** Прошу, нехай щастить! Гарного вам дня!

Як ви бачите, українська мова має надзвичайно точну і логічну систему для орієнтації в просторі. Ці короткі прийменники працюють разом з орудним відмінком як одна ідеальна граматична команда. Спочатку ця система здається трохи складною, але ви обов'язково дуже швидко звикнете до неї. Українська просторова точність показує справжню красу і математичну логіку нашої мови. Практикуйте ці корисні слова кожного дня у своєму місті. Ваше мовлення швидко стане дуже природним, впевненим та красивим.

<!-- INJECT_ACTIVITY: fill-in, Complete 8 sentences with the correct preposition and Instrumental noun form -->


## Підсумок

Давайте швидко повторимо головні правила цього уроку. Ці питання допоможуть вам перевірити свої знання. Прочитайте їх дуже уважно.

- **Питання:** Який відмінок ми використовуємо з прийменниками **над** *(above)*, **під** *(under)*, **перед** *(in front of)*, **за** *(behind)*, **між** *(between)*?
- **Відповідь:** Ми завжди використовуємо **орудний відмінок** *(Instrumental case)*. Питання «Де?» вимагає саме цієї граматичної форми.

- **Питання:** Як правильно сказати українською мовою фразу "between the table and the wall"?
- **Відповідь:** Правильний переклад — **між столом і стіною**. Обидва іменники мають спеціальні закінчення орудного відмінка.

- **Питання:** Яке нове **часове значення** *(temporal meaning)* має український прийменник **перед**?
- **Відповідь:** Цей прийменник означає "before" в часі. Наприклад: **перед сном** *(before sleep)*, **перед роботою** *(before work)*, **перед обідом** *(before lunch)*.

- **Питання:** Чим відрізняється фраза **за будинком** *(behind the building)* від фрази **дякую за допомогу** *(thank you for the help)*?
- **Відповідь:** Фраза «за будинком» означає конкретне місце *(location)*. Тут ми впевнено використовуємо форму орудного відмінка. Фраза «за допомогу» показує причину або подяку *(reason or gratitude)*. Тут ми повинні використовувати тільки **знахідний відмінок** *(Accusative case)*.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: instrumental-prepositions
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

**Level: A2 (Module 28/60) — ELEMENTARY**

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
