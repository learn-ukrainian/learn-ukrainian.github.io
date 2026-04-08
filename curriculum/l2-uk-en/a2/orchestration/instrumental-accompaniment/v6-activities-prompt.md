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

- `<!-- INJECT_ACTIVITY: match-nom-inst -->`
- `<!-- INJECT_ACTIVITY: fill-in-instrumental-endings -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-cafe-dialogue-sentences-with-correct-instrumental-forms -->`

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

Сьогодні ми починаємо нову граматичну тему. *(Today we are starting a new grammar topic.)* Це **орудний відмінок** *(the instrumental case)*. Його назва походить від дієслова **«орудувати»** *(to handle, to wield a tool)*. Тому його перше і базове значення — це інструмент. *(Therefore, its first and basic meaning is an instrument.)* Ми використовуємо цей відмінок, коли кажемо, яким інструментом ми робимо дію. *(We use this case when we say with which instrument we do an action.)* Наприклад, я пишу **ручкою** *(with a pen)*, або я їм **ложкою** *(with a spoon)*. Але в орудного відмінка є ще одне часте значення. *(But the instrumental case has another frequent meaning.)* Це соціальне значення — **супровід** *(accompaniment)*. Ми використовуємо його, коли робимо щось разом з іншими людьми. *(We use it when we do something together with other people.)* Саме це значення ми будемо вивчати сьогодні. *(This exact meaning we will study today.)*

Кожен відмінок в українській мові має свої питання. *(Every case in the Ukrainian language has its questions.)* Орудний відмінок відповідає на питання **«Ким?»** *(By whom?)* та **«Чим?»** *(With what?)*. Питання «Ким?» ми ставимо до живих істот: людей або тварин. *(We ask the question "Ким?" for living beings: people or animals.)* Питання «Чим?» ми ставимо до неживих предметів. *(We ask the question "Чим?" for inanimate objects.)* Коли ми використовуємо орудний відмінок як інструмент, ми не додаємо прийменники. *(When we use the instrumental case as a tool, we do not add prepositions.)* Ми просто кажемо: я малюю чим? — **олівцем** *(with a pencil)*. Але граматика змінюється, коли ми говоримо про компанію. *(But the grammar changes when we talk about company.)* Тоді ми обов'язково додаємо прийменник **«з»** *(with)*. Тепер наші питання звучать інакше: **«З ким?»** *(With whom?)* та **«З чим?»** *(With what?)*. Цей прийменник повністю змінює фокус нашої розмови. *(This preposition completely changes the focus of our conversation.)*

Давайте подивимося, де знаходиться орудний відмінок у граматичній системі. *(Let's see where the instrumental case is located in the grammatical system.)* У традиційній українській системі це сьомий відмінок. *(In the traditional Ukrainian system, it is the seventh case.)* Ви вже добре знаєте інші відмінки і розумієте їхні функції. *(You already know the other cases well and understand their functions.)* Наприклад, **знахідний відмінок** *(the accusative case)* показує напрямок руху або об'єкт дії. *(For example, the accusative case shows the direction of movement or an object of action.)* **Родовий відмінок** *(the genitive case)* показує власність або відсутність чогось. *(The genitive case shows possession or the absence of something.)* Орудний відмінок додає абсолютно новий вимір до ваших знань. *(The instrumental case adds an absolutely new dimension to your knowledge.)* Він показує об'єднання, спільну дію та засоби. *(It shows togetherness, joint action, and means.)* Цей відмінок пояснює, як саме або з ким ми виконуємо дію. *(This case explains exactly how or with whom we perform an action.)* Без орудного відмінка наша мова була б дуже самотньою. *(Without the instrumental case, our language would be very lonely.)*

Ми будемо вивчати функції орудного відмінка поступово протягом кількох наступних модулів. *(We will study the functions of the instrumental case gradually over several next modules.)* Сьогодні ми фокусуємося лише на соціальному використанні з прийменником «з». *(Today we focus only on the social use with the preposition "з".)* Наша базова фраза на сьогодні: **«Я іду з другом»** *(I am going with a friend)*. У наступних уроках ми побачимо інші функції цього відмінка. *(In the next lessons, we will see other functions of this case.)* Ми навчимося говорити про професії, коли хтось стає **лікарем** *(a doctor)* або **вчителем** *(a teacher)*. Ми також вивчимо використання інструментів без прийменників. *(We will also study the use of tools without prepositions.)* А пізніше ми додамо просторові прийменники, такі як **«над»** *(above)* або **«під»** *(under)*. Вони також вимагають орудного відмінка для опису місця. *(They also require the instrumental case to describe location.)* Але зараз наша мета — навчитися говорити про людей, які нас супроводжують. *(But right now, our goal is to learn to talk about the people who accompany us.)*


## Закінчення орудного відмінка однини (Instrumental Singular Endings)

In Ukrainian, noun endings in the Instrumental case depend on gender and stem type. The easiest group to learn is masculine nouns with hard stems. Ці іменники мають дуже просте і стабільне закінчення. *(These nouns have a very simple and stable ending.)* Більшість чоловічих іменників в українській мові належать саме до цієї групи. *(Most masculine nouns in the Ukrainian language belong to this exact group.)* Вони завжди отримують закінчення **«-ом»** *(the "-om" ending)*. Наприклад, слово **«друг»** *(friend)* має твердий приголосний в кінці. *(For example, the word "друг" has a hard consonant at the end.)* Тому в орудному відмінку ми кажемо **«другом»** *(with a friend)*. Коли ми говоримо про родину, правило теж працює. *(When we talk about family, the rule also works.)* Інший приклад — це слово **«брат»** *(brother)*, яке стає формою **«братом»** *(with a brother)*. Якщо ми говоримо про неживі предмети, система залишається незмінною. *(If we talk about inanimate objects, the system remains unchanged.)* Слово **«стіл»** *(table)* швидко змінюється на форму **«столом»** *(with/under a table)*. Це абсолютно базова модель, яку дуже легко запам'ятати студентам. *(This is an absolutely basic model that is very easy for students to remember.)* Ви будете використовувати це закінчення найчастіше у щоденних розмовах. *(You will use this ending most often in daily conversations.)*

Now let's look at masculine nouns that end in a soft sign, a sibilant, or the letter "й". Ці слова вимагають більш м'якого звуку в кінці. *(These words require a softer sound at the end.)* Тому вони отримують закінчення **«-ем»** *(the "-em" ending)*. Наприклад, професія **«вчитель»** *(teacher)* має м'який знак. *(For example, the profession "вчитель" has a soft sign.)* В орудному відмінку це слово стає формою **«вчителем»** *(with a teacher)*. Слова з шиплячими приголосними також працюють за цим правилом. *(Words with sibilant consonants also work by this rule.)* Звичайний **«ніж»** *(knife)* перетворюється на форму **«ножем»** *(with a knife)*. Існує також третій варіант для слів, які закінчуються на звук [й]. *(There is also a third variant for words that end in the sound [й].)* Вони отримують закінчення **«-єм»** *(the "-yem" ending)*. Наприклад, ваш улюблений **«чай»** *(tea)* стає словом **«чаєм»** *(with tea)*. Слово **«герой»** *(hero)* перетворюється на форму **«героєм»** *(with a hero)*. The spelling rule is logical: soft and sibilant stems take the letter "e", while stems ending in a vowel sound take "є".

Feminine nouns have their own beautiful and distinct endings in the Instrumental case. Почнемо з іменників жіночого роду, які мають тверду основу. *(Let's start with feminine nouns that have a hard stem.)* Такі слова зазвичай закінчуються на літеру «а» в називному відмінку. *(Such words usually end in the letter "a" in the nominative case.)* В орудному відмінку вони завжди отримують закінчення **«-ою»** *(the "-oyu" ending)*. Наприклад, слово **«мама»** *(mom)* змінюється на теплу форму **«мамою»** *(with mom)*. Слово **«сестра»** *(sister)* стає красивою формою **«сестрою»** *(with a sister)*. Якщо це звичайний предмет, як **«книга»** *(book)*, ми кажемо **«книгою»** *(with a book)*. Це закінчення є дуже важливою фонетичною рисою української мови. *(This ending is a very important phonetic feature of the Ukrainian language.)* It is critical to pronounce the full vowel sound clearly. In Russian, the equivalent ending is often shortened to "-ой" for convenience. Українська мова зберігає повний і глибокий звук в кінці слова. *(The Ukrainian language preserves a full and deep sound at the end of the word.)* Це робить нашу вимову дуже мелодійною та ритмічною. *(This makes our pronunciation very melodic and rhythmic.)* Завжди вимовляйте **«мамою»**, **«сестрою»**, **«водою»** *(with water)*, щоб звучати природно. *(Always pronounce "mamoyu", "sestroyu", "vodoyu" to sound natural.)*

If a feminine noun has a soft stem, a sibilant, or ends in a vowel plus "я", the ending changes slightly. Жіночі іменники з м'якою основою зазвичай закінчуються на літеру «я». *(Feminine nouns with a soft stem usually end in the letter "ya".)* Вони отримують інше закінчення **«-ею»** *(the "-eyu" ending)*. Наприклад, слово **«земля»** *(earth)* стає м'якою формою **«землею»** *(with the earth)*. Слова з шиплячими приголосними теж активно використовують це закінчення. *(Words with sibilant consonants also actively use this ending.)* Слово **«душа»** *(soul)* перетворюється на форму **«душею»** *(with the soul)*. Коли основа слова закінчується на голосний звук, ми додаємо закінчення **«-єю»** *(the "-yeyu" ending)*. Прекрасне слово **«мрія»** *(dream)* стає ще красивішим у формі **«мрією»** *(with a dream)*. Слово **«надія»** *(hope)* легко перетворюється на форму **«надією»** *(with hope)*. The grammatical pattern is remarkably consistent and easy to follow. The soft letter "я" becomes "ею" after a consonant, and it becomes "єю" after another vowel. Ця система допомагає зберегти правильний ритм українських слів. *(This system helps preserve the correct rhythm of Ukrainian words.)*

Finally, let's look at neuter nouns, which conveniently follow the exact same patterns as masculine nouns. Середній рід часто запозичує граматичні закінчення у чоловічого роду. *(The neuter gender often borrows grammatical endings from the masculine gender.)* Слова з твердою основою, які закінчуються на «о», отримують закінчення **«-ом»**. *(Words with a hard stem that end in "o" receive the "-om" ending.)* Наприклад, **«вікно»** *(window)* стає формою **«вікном»** *(with/under a window)*. Слово **«молоко»** *(milk)* змінюється на форму **«молоком»** *(with milk)*. Слова з м'якою основою, які закінчуються на «е», отримують закінчення **«-ем»**. *(Words with a soft stem that end in "e" receive the "-em" ending.)* Слово **«море»** *(sea)* змінюється на поетичну форму **«морем»** *(with the sea)*. Деякі слова середнього роду закінчуються на «я» і отримують закінчення **«-ям»** *(the "-yam" ending)*. Наприклад, важливе слово **«життя»** *(life)* стає формою **«життям»** *(with life)*. Слово **«завдання»** *(task)* перетворюється на форму **«завданням»** *(with a task)*. This table visualizes the Nominative and Instrumental endings side-by-side for quick reference.

| Рід *(Gender)* | Називний *(Nominative)* | Орудний *(Instrumental)* |
| :--- | :--- | :--- |
| **Чоловічий** *(Masculine)* | стіл, друг | столом, другом |
| | вчитель, ніж | вчителем, ножем |
| | чай, герой | чаєм, героєм |
| **Жіночий** *(Feminine)* | мама, сестра | мамою, сестрою |
| | земля, душа | землею, душею |
| | мрія, надія | мрією, надією |
| **Середній** *(Neuter)* | вікно, молоко | вікном, молоком |
| | море, сонце | морем, сонцем |
| | життя, завдання | життям, завданням |

<!-- INJECT_ACTIVITY: match-nom-inst -->
<!-- INJECT_ACTIVITY: fill-in-instrumental-endings -->


## З/із/зі + орудний відмінок (Z/iz/zi + Instrumental)

Найважливіша функція орудного відмінка — це супровід. *(The most important function of the instrumental case is accompaniment.)* Коли ми робимо щось разом з іншою людиною, ми використовуємо прийменник **«з»** *(with)*. Після прийменника «з» завжди йде орудний відмінок. *(After the preposition "z" always comes the instrumental case.)* This is how we express doing an action together with a partner, family member, or companion. Наприклад, на вихідних ви можете **гуляти з другом** *(to walk with a friend)* у міському парку. Або ви можете **жити з батьками** *(to live with parents)* у великому будинку за містом. На роботі ми часто маємо **працювати з колегою** *(to work with a colleague)* над новим складним проєктом. Маленькі діти люблять довго гратися з собакою. *(Small children love to play with a dog for a long time.)* Це дуже корисна граматична конструкція для щоденного спілкування з людьми. *(This is a very useful grammatical construction for daily communication with people.)*

Друга важлива функція орудного відмінка — це опис складу предметів. *(The second important function of the instrumental case is the description of the composition of objects.)* We use the preposition "з" and the instrumental case to describe what an item is made of, or what delicious ingredients it contains. This is absolutely essential for survival Ukrainian, especially when you are ordering food in a cafe, restaurant, or supermarket. Уранці українці часто п'ють гарячу **каву з молоком** *(coffee with milk)*. Якщо ви не любите молоко, ви можете замовити чай **з лимоном** *(with lemon)* та **медом** *(honey)*. На обід ми любимо їсти свіжий **хліб з маслом** *(bread with butter)* або традиційний український борщ **зі сметаною** *(with sour cream)*. Ввечері ви можете замовити велику **піцу з грибами** *(pizza with mushrooms)* для всієї веселої компанії. *(In the evening you can order a large pizza with mushrooms for the whole cheerful company.)*

Українська мова дуже мелодійна. Тому ми маємо три варіанти цього прийменника: **«з»**, **«із»** та **«зі»**. *(The Ukrainian language is very melodic. Therefore, we have three variants of this preposition: "z", "iz", and "zi".)* The rules for choosing between them are based entirely on euphony, or making the spoken phrase easy and pleasant to pronounce. Прийменник «з» — це базовий і найчастіший варіант у мові. *(The preposition "z" is the basic and most frequent variant in the language.)* Ми використовуємо його перед голосними звуками та більшістю одинарних приголосних. *(We use it before vowel sounds and most single consonants.)* Variant "із" is commonly used before words starting with difficult consonant clusters to seamlessly break up the heavy sounds. Наприклад, ми красиво говоримо **«із сестрою»** *(with a sister)*, а не «з сестрою». Variant "зі" is mandatory before words starting with the specific hissing consonants «з», «с», «ш», or heavy clusters like «зв». *(For example, we say "with sour cream" as "зі сметаною" and "with taste" as "зі смаком".)*

Here is a practical phonetic guide to help you quickly choose the correct preposition variant based on the first sound of the following word. Remember that these simple rules help you speak smoothly without stumbling over difficult consonant combinations. Найважливіша фраза, яку ви маєте запам'ятати назавжди — це **«зі мною»** *(with me)*. Це абсолютно фіксована форма. *(This is an absolutely fixed form.)* Кожен студент рівня A2 повинен знати цю коротку фразу напам'ять. *(Every A2 level student must know this short phrase by heart.)*

| Варіант *(Variant)* | Коли використовувати *(When to use)* | Приклад *(Example)* |
| :--- | :--- | :--- |
| **з** | Перед голосними та багатьма одинарними приголосними. *(Before vowels and many single consonants.)* | **з братом** *(with a brother)*, **з другом** *(with a friend)*, **з молоком** *(with milk)* |
| **із** | Між приголосними або перед важкою групою приголосних. *(Between consonants or before a heavy consonant cluster.)* | **із братом** *(with a brother)*, **із сестрою** *(with a sister)* |
| **зі** | Перед словами, що починаються на «з», «с


## Практика: З ким? З чим? (Practice: With Whom? With What?)

Тепер ми готові практикувати орудний відмінок. *(Now we are ready to practice the instrumental case.)* Ми часто використовуємо його, коли відповідаємо на питання «З ким?». *(We often use it when we answer the question "With whom?".)* Ми ставимо це питання про людей. *(We ask this question about people.)*
— Ти йдеш у кіно сама? *(Are you going to the cinema alone?)*
— Ні, я йду **з подругою** *(with a female friend)*.
— **З ким** *(with whom)* ти розмовляєш?
— Я розмовляю **з братом** *(with a brother)*.
— З ким він живе? *(Who does he live with?)*
— Він живе **з батьками** *(with parents)*.
Прийменник «з» і орудний відмінок завжди працюють разом. *(The preposition "z" and the instrumental case always work together.)* Це допомагає нам будувати природні речення. *(This helps us build natural sentences.)*

Друге важливе питання — це «З чим?». *(The second important question is "With what?".)* Ми використовуємо його, коли описуємо їжу та напої. *(We use it when we describe food and drinks.)*
— Я люблю **борщ зі сметаною** *(borsch with sour cream)*.
— Мені подобається **кава з медом** *(coffee with honey)*.
Слово «сметана» має тверду основу. *(The word "smetana" has a hard stem.)* Тому воно отримує закінчення «-ою». *(Therefore it gets the "-ою" ending.)* Слово «вишня» має м'яку основу. *(The word "cherry" has a soft stem.)* Воно отримує закінчення «-ею». *(It gets the "-ею" ending.)* Наприклад, пиріжок **з вишнею** *(a pie with cherry)*. Ці описи дуже корисні в кафе та ресторанах. *(These descriptions are very useful in cafes and restaurants.)*

Давайте прочитаємо діалог двох друзів. *(Let's read a dialogue of two friends.)* Вони зустрілися в кафе. *(They met in a cafe.)*
> — **Олена:** Привіт! Я буду **чай з лимоном** *(tea with lemon)*. А ти?
> — **Марко:** Привіт! А я хочу **каву з холодним молоком** *(coffee with cold milk)*. І ще я буду **бутерброд з шинкою** *(a sandwich with ham)*.
> — **Олена:** Добре. Можна мені також млинець **з яблуком** *(a crepe with apple)*?
> — **Офіціант:** Так, звичайно. Ваш чай з лимоном і кава з молоком будуть готові скоро. *(Yes, of course. Your tea with lemon and coffee with milk will be ready soon.)*

Цей діалог показує різні закінчення в природній розмові. *(This dialogue shows different endings in a natural conversation.)* 

В українській мові є дієслова, які постійно вимагають орудного відмінка з прийменником «з». *(In the Ukrainian language, there are verbs that constantly require the instrumental case with the preposition "z".)* Це дуже важливі слова для спілкування. *(These are very important words for communication.)*
Перше дієслово — **зустрічатися з** *(to meet with)*. Наприклад: Я часто зустрічаюся **з друзями** *(I often meet with friends)*.
Друге дієслово — **розмовляти з** *(to talk with)*. Наприклад: Директор розмовляє **з учителем** *(The director is talking with the teacher)*.
Третє дієслово — **погоджуватися з** *(to agree with)*. Ми використовуємо його для спільної думки. *(We use it for a shared opinion.)* Наприклад: Я повністю погоджуюся **з тобою** *(I completely agree with you)*.

<!-- INJECT_ACTIVITY: fill-in-complete-cafe-dialogue-sentences-with-correct-instrumental-forms -->


## Підсумок

Сьогодні ми вивчили орудний відмінок. *(Today we learned the instrumental case.)* Ми використовуємо його для компанії та їжі. *(We use it for company and food.)* To form this case, masculine and neuter nouns take the endings «-ом», «-ем», or «-єм». Feminine nouns take the endings «-ою», «-ею», or «-єю». 

Ми часто використовуємо цей відмінок після прийменника «з». *(We often use this case after the preposition "z".)* Remember that the preposition «з» changes to «із» or «зі» for the sake of beauty and ease of speech. Це робить українську мову дуже мелодійною і природною. *(This makes the Ukrainian language very melodic and natural.)* Тепер ви знаєте, як розповісти про свою компанію або замовити смачну їжу. *(Now you know how to talk about your company or order delicious food.)*

Давайте перевіримо ваші знання: *(Let's check your knowledge:)*
- Як сказати "with a friend" (male) та "with a friend" (female)?
- Коли ми використовуємо **зі** *(with)* замість **з** *(with)*?
- Яке закінчення мають іменники жіночого роду (hard stem) в орудному відмінку?

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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

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
