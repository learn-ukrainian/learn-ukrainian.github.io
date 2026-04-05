<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/instrumental-means.yaml` file for module **25: Ручкою, автобусом** (a2).

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

- focus: Put the noun in Instrumental singular to express the tool of an action
  items: 8
  type: fill-in
- focus: Choose between з + Instrumental (companion) and bare Instrumental (tool)
  items: 8
  type: quiz
- focus: Match transport nouns to their Instrumental forms
  items: 8
  type: match-up
- focus: Sort sentences into Tool/Means vs. Accompaniment categories
  items: 8
  type: group-sort
- focus: Reorder words to form correct instrumental phrases expressing tool or means
    of transport
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- знаряддя (instrument, tool)
- транспорт (transport)
- пішки (on foot)
- корабель (ship)
required:
- ручка (pen)
- олівець (pencil)
- фарба (paint)
- лінійка (ruler)
- ніж (knife)
- ложка (spoon)
- автобус (bus)
- потяг (train)
- літак (airplane)
- трамвай (tram)
- засіб (means, tool)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чим? Знаряддя дії (With What? The Tool of an Action)

Орудний відмінок має кілька важливих функцій. *(The Instrumental case has several important functions.)* One of its primary uses is to express the specific tool or instrument you use to perform an action. Коли ми робимо щось за допомогою предмета, ми використовуємо орудний відмінок. *(When we do something with the help of an object, we use the Instrumental case.)* Щоб знайти цей предмет у реченні, ми ставимо питання «Чим?». *(To find this object in a sentence, we ask the question "With what?".)* In English, you use the preposition "with" to show the tool, for example, "with a pen". However, Ukrainian structure is different here. В українській мові ми не використовуємо прийменник для знаряддя дії. *(In the Ukrainian language, we do not use a preposition for the tool of an action.)* Саме закінчення слова передає значення прийменника. *(The word ending itself conveys the meaning of the preposition.)* Тому ми кажемо «писати ручкою», а не «писати з ручкою». *(Therefore we say "to write with a pen", and not "to write with a pen".)* Додавання прийменника «з» перед знаряддям — це помилка. *(Adding the preposition "with" before a tool is a mistake.)*

Let's look at how feminine nouns change their endings when they become the tool of an action. Жіночий рід має три основні закінчення в орудному відмінку однини. *(The feminine gender has three main endings in the singular Instrumental case.)* Більшість іменників із твердим складом отримують закінчення **-ою**. *(Most nouns with a hard stem receive the ending -ою.)* For example, the word **ручка** *(pen)* becomes **ручкою**, and the word **ложка** *(spoon)* becomes **ложкою**. Якщо іменник жіночого роду має м'який склад, закінчення змінюється на **-ею**. *(If the feminine noun has a soft stem, the ending changes to -ею.)* An example is the word **земля** *(earth, soil)*, which becomes **землею**. Нарешті, якщо слово закінчується на **-ія**, воно отримує закінчення **-єю**. *(Finally, if the word ends in -ія, it receives the ending -єю.)* The word **лінія** *(line)* becomes **лінією**. Ось кілька прикладів. *(Here are a few examples.)* «Я щодня пишу синьою ручкою в школі.» *(I write with a blue pen every day at school.)* «Вона обережно креслить лінійкою.» *(She carefully draws with a ruler.)* «Ми їмо суп великою ложкою.» *(We eat soup with a big spoon.)*

Now we will learn the spelling rules for masculine and neuter nouns in the singular form. Чоловічий та середній рід мають абсолютно однакові закінчення в цьому відмінку. *(The masculine and neuter genders have absolutely identical endings in this case.)* Якщо слово закінчується на твердий приголосний, ми використовуємо закінчення **-ом**. *(If the word ends in a hard consonant, we use the ending -ом.)* This means that **автобус** *(bus)* changes to **автобусом**, and **вікно** *(window)* changes to **вікном**. Для іменників із м'яким складом ми додаємо закінчення **-ем**. *(For nouns with a soft stem, we add the ending -ем.)* Thus, **олівець** *(pencil)* becomes **олівцем**, and **ніж** *(knife)* becomes **ножем**. Якщо слово закінчується на **-й**, ми завжди пишемо закінчення **-єм**. *(If the word ends in -й, we always write the ending -єм.)* For example, **трамвай** *(tram)* becomes **трамваєм**. Діти часто малюють олівцем на уроках мистецтва. *(Children often draw with a pencil in art classes.)* Я люблю мити вікно чистою ганчіркою. *(I like to wash the window with a clean rag.)*

The Instrumental case is extremely useful when we talk about daily chores and regular household actions. Удома ми постійно використовуємо різні знаряддя для прибирання. *(At home, we constantly use various tools for cleaning.)* Коли підлога брудна, треба підмітати віником. *(When the floor is dirty, one must sweep with a broom.)* Якщо ваше взуття не чисте, час чистити щіткою. *(If your shoes are not clean, it is time to clean with a brush.)* Коли на столі багато пилу, варто витирати ганчіркою. *(When there is a lot of dust on the table, it is worth wiping with a rag.)* А після прання одягу необхідно прасувати праскою. *(And after washing clothes, it is necessary to iron with an iron.)* Ці прості та знайомі дії чудово показують функцію цього відмінка. *(These simple and familiar actions perfectly show the function of this case.)*

<!-- INJECT_ACTIVITY: fill-in, Put the noun in Instrumental singular to express the tool of an action (ніж, ручка, олівець, ложка, щітка, лінійка, віник, фарба) -->


## Їхати автобусом: Засіб пересування (Travel by Bus: Means of Transport)

Орудний відмінок також показує засіб пересування. *(The Instrumental case also shows the means of transport.)* In Ukrainian, when we talk about how we travel, we can use the Instrumental case without any preposition. У цьому випадку слово відповідає на питання «чим?». *(In this case, the word answers the question "with what?".)* This means we are focusing on the vehicle as a tool or instrument for our journey. Звісно, ви можете сказати «їхати на **автобусі**». *(Of course, you can say "to travel on a bus".)* When you use the preposition **на** *(on)* with the Locative case, you focus on the physical location inside the vehicle. Але українці дуже часто кажуть просто «їхати автобусом». *(But Ukrainians very often simply say "to travel by bus".)* This bare Instrumental form is elegant and natural. Воно підкреслює сам **засіб** *(means)*, який ми обрали для поїздки. *(It emphasizes the very means we chose for the trip.)* For example, «летіти **літаком**» *(to fly by airplane)* highlights the method of flying. «Пливти **кораблем**» *(to sail by ship)* shows the instrument of sailing. Ця форма робить речення коротшим і точнішим. *(This form makes the sentence shorter and more precise.)*

Колеги часто обговорюють свій шлях до офісу. *(Colleagues often discuss their route to the office.)* Сьогодні вранці Андрій та Марія зустрілися біля роботи. *(This morning Andriy and Mariia met near work.)* Вони запитують одне одного про ранковий маршрут. *(They ask each other about the morning route.)*
> — **Андрій:** Привіт, Маріє! Чим ти зазвичай їдеш на роботу? *(Hi, Mariia! How do you usually travel to work?)*
> — **Марія:** Добрий ранок, Андрію! Я їду автобусом, а потім **метро** *(by metro)*. А ти? *(Good morning, Andriy! I travel by bus, and then by metro. And you?)*
> — **Андрій:** А я їду власним **автомобілем** *(by car)* або **трамваєм** *(by tram)*. *(And I travel by my own car or by tram.)*
> — **Марія:** Це зручно. Ти часто стоїш у заторах? *(That is convenient. Do you often stand in traffic jams?)*
> — **Андрій:** Так, іноді мій шлях машиною займає багато часу. *(Yes, sometimes my trip by car takes a lot of time.)*
> — **Марія:** Тоді трамваєм набагато швидше. *(Then by tram is much faster.)*

Тепер давайте вивчимо словник для різних видів транспорту. *(Now let's learn the vocabulary for various types of transport.)* Для далеких подорожей ми обираємо великий **транспорт** *(transport)*. *(For long journeys, we choose large transport.)* Слово **потяг** *(train)* у цьому відмінку змінюється на **потягом**. *(The word train in this case changes to by train.)* Слово літак має форму літаком. *(The word airplane has the form by airplane.)* Якщо ви подорожуєте морем, слово корабель стає кораблем. *(If you travel by sea, the word ship becomes by ship.)* Для міста ми маємо інший міський транспорт. *(For the city, we have different urban transport.)* Слово **тролейбус** *(trolleybus)* змінюється на **тролейбусом**. *(The word trolleybus changes to by trolleybus.)* Популярна українська **маршрутка** *(minibus)* отримує закінчення жіночого роду і стає **маршруткою**. *(The popular Ukrainian minibus receives the feminine ending and becomes by minibus.)* Пам'ятайте, що слово метро ніколи не змінює закінчення. *(Remember that the word metro never changes its ending.)* Ми завжди кажемо «їхати метро». *(We always say "to travel by metro".)* Також слово **таксі** *(taxi)* є незмінним. *(Also, the word taxi is indeclinable.)* Ви можете зручно «їхати таксі» додому. *(You can comfortably travel by taxi home.)*

У цьому правилі є один дуже важливий виняток. *(There is one very important exception in this rule.)* English speakers often say "to go on foot". В українській мові ми не використовуємо орудний відмінок для ніг у цій ситуації. *(In the Ukrainian language, we do not use the Instrumental case for feet in this situation.)* Замість цього ми маємо спеціальний прислівник **пішки** *(on foot)*. *(Instead, we have a special adverb on foot.)* We say «іти пішки» rather than using a noun for "foot" in the Instrumental. Порівняйте ці два речення. *(Compare these two sentences.)* «Він не їде потягом, він іде пішки.» *(He is not traveling by train, he is walking on foot.)* «Ми не поїхали маршруткою, ми пішли пішки.» *(We did not go by minibus, we went on foot.)* Як ми вже згадували, слово таксі також залишається без змін. *(As we already mentioned, the word taxi also remains without changes.)* Слово таксі — це запозичене слово, тому воно не має відмінків. *(The word taxi is a borrowed word, so it has no cases.)* Ви можете їхати таксі, або йти пішки. *(You can travel by taxi, or go on foot.)*

<!-- INJECT_ACTIVITY: match-up, Match transport nouns to their Instrumental forms (потяг, літак, корабель, тролейбус, маршрутка, таксі, метро, автобус) -->


## Орудний відмінок множини (Instrumental Plural)

У множині орудний відмінок має дуже прості правила. *(In the plural, the Instrumental case has very simple rules.)* Усі іменники мають майже однакові закінчення, незалежно від їхнього роду. *(All nouns have almost identical endings, regardless of their gender.)* In the plural, we do not need to worry about masculine, feminine, or neuter genders. The endings depend entirely on whether the final consonant of the stem is hard or soft. Для слів із твердим коренем ми використовуємо закінчення **-ами** *(-amy)*. *(For words with a hard stem, we use the ending -amy.)* Наприклад, слово **рука** *(hand)* стає **руками** *(with hands)*. Слово **стіл** *(table)* змінюється на **столами** *(with tables)*. Слово **книга** *(book)* отримує форму **книгами** *(with books)*. Для слів із м'яким коренем ми додаємо закінчення **-ями** *(-yamy)*. *(For words with a soft stem, we add the ending -yamy.)* Наприклад, слово **олівець** *(pencil)* стає **олівцями** *(with pencils)*. Слово **тиждень** *(week)* стає **тижнями** *(by weeks)*. Також є цікаві винятки, які треба просто запам'ятати. *(Also there are interesting exceptions that you just need to remember.)* Слово **діти** *(children)* має неправильну форму **дітьми** *(with children)*. *(The word children has the irregular form with children.)* Слово **двері** *(door)* може бути **дверима** *(with doors)* або **дверями** *(with doors)*. *(The word door can be with doors or with doors.)*

Тепер давайте подивимося, як ці слова працюють у реченнях. *(Now let's see how these words work in sentences.)* Ми часто використовуємо орудний відмінок множини для інструментів. *(We often use the Instrumental plural for tools.)* Коли ми малюємо, ми використовуємо різні кольори. *(When we draw, we use different colors.)* Діти на уроці кажуть: «Ми малюємо кольоровими **олівцями** *(with colored pencils)*». *(The children at the lesson say: "We draw with colored pencils".)* Справжній художник зазвичай працює **фарбами** *(with paints)*. *(A real artist usually works with paints.)* Ви можете різати папір великими **ножицями** *(with scissors)*. *(You can cut paper with large scissors.)* When we talk about eating utensils in the plural, we also use these endings. В Японії люди традиційно їдять **паличками** *(with chopsticks)*. *(In Japan, people traditionally eat with chopsticks.)* В Україні люди їдять суп **ложками** *(with spoons)*, а салат — **виделками** *(with forks)*. *(In Ukraine, people eat soup with spoons, and salad with forks.)* Це дуже зручно і просто. *(This is very convenient and simple.)*

Наші частини тіла — це також наші інструменти. *(Our body parts are also our tools.)* Ми виконуємо багато різних дій за допомогою нашого тіла. *(We perform many different actions with the help of our body.)* Тому ми часто вживаємо ці слова в орудному відмінку множини. *(Therefore, we often use these words in the Instrumental plural.)* Коли ми бачимо друзів, ми можемо **махати руками** *(to wave hands)*. *(When we see friends, we can wave hands.)* Коли діти сердяться, вони іноді можуть **тупати ногами** *(to stomp feet)*. *(When children are angry, they sometimes can stomp feet.)* Ми завжди маємо **дивитися очима** *(to look with eyes)* і слухати **вухами** *(with ears)*. *(We always must look with eyes and listen with ears.)* Згадайте вірш про те, як я допомагаю родині. *(Remember the poem about how I help the family.)* Я можу **мити руками** *(to wash with hands)* брудний посуд. *(I can wash dirty dishes with hands.)* Я також можу прибирати кімнату і **замітати віником** *(to sweep with a broom)*. *(I also can clean the room and sweep with a broom.)*

Також є особлива група слів жіночого роду. *(Also there is a special group of feminine words.)* Nouns of the feminine third declension end in a consonant in the dictionary form. У множині вони часто отримують закінчення **-ами** або **-ями**. *(In the plural, they often receive the ending -amy or -yamy.)* Наприклад, слово **ніч** *(night)* стає **ночами** *(by nights)*. Слово **подорож** *(journey)* стає **подорожами** *(with journeys)*. We write the ending with the letter "a" here because of the hushing consonants at the end of the stems. Слово **річ** *(thing)* стає **речами** *(with things)*. *(The word thing becomes with things.)* Моя сестра любить захоплюватися новими подорожами. *(My sister likes to be fascinated by new journeys.)* Я дуже люблю подорожувати різними **країнами** *(through different countries)*. *(I really love traveling through different countries.)*

<!-- INJECT_ACTIVITY: unjumble, Reorder words to form correct instrumental phrases expressing tool or means of transport -->


## Практика: Знаряддя чи супутник?

Тепер час перевірити, як добре ми розуміємо різницю між знаряддям та супутником. Уявіть просту ситуацію: ви маєте нову ручку. *(Imagine a simple situation: you have a new pen.)* Ви можете робити з нею різні дії. In English, you use the word "with" for both the tool you use and the person or thing accompanying you. Ukrainian makes a strict grammatical distinction here. Ми кажемо: «Я пишу текст **ручкою** *(with a pen)*». Ручка допомагає вам писати. Це ваш інструмент, тому прийменник тут зовсім не потрібен. Але ми також можемо сказати: «Я йду до школи **з ручкою** *(with a pen)*». Тут ручка — це вже ваш супутник, звичайна річ, яку ви несете в руці. When you act together with someone or something, you must use the preposition **з** *(with)*. Наприклад, ми часто кажемо: «Я гуляю в парку **з собакою** *(with a dog)*». Ви та собака гуляєте разом, тому ми обов'язково додаємо цей прийменник. Це дуже важливе правило.

Давайте подивимося на інші приклади, щоб краще побачити цю різницю. Це дуже добре видно, коли ми порівнюємо живих людей та неживі речі. Ми кажемо: «Я їду на роботу **з братом** *(with a brother)*». Брат сидить і їде поруч із вами. Він — ваш супутник у цій подорожі. Але ми кажемо: «Я їду на роботу **автобусом** *(by bus)*». Автобус — це ваш засіб пересування, а не жива людина. *(The bus is your means of transport, not a living person.)* Якщо ви помилково скажете «Я їду з автобусом», це означатиме щось дуже дивне. Це звучатиме так, ніби великий автобус іде поруч із вами як ваш друг. Adding the preposition to a tool makes it sound like a person accompanying you. Порівняйте ще раз ці дві ситуації. «Він малює картину **з учителем** *(with a teacher)*» означає, що вони малюють її разом. «Він малює картину **олівцем** *(with a pencil)*» означає, що він просто використовує дерев'яний олівець для роботи.

Є також особливі українські дієслова, які завжди вимагають орудного відмінка без прийменника. They might not seem like they involve a physical "tool," but they use the Instrumental to show the means or the object of an action. Наприклад, ми кажемо: «Я люблю **займатися спортом** *(to do sports)*». Спорт тут діє як засіб вашої активності. Інше дуже важливе і популярне словосполучення — **цікавитися музикою** *(to be interested in music)*. Мій брат дуже цікавиться історією, а сестра цікавиться літературою. Music or history is the "instrument" that captures your interest. Ми не кажемо «цікавитися з історією», це неправильно. Також ми використовуємо цей відмінок, коли говоримо про різні запахи навколо нас. Навесні старий сад починає солодко **пахнути квітами** *(to smell of flowers)*. Вранці наша кухня завжди пахне свіжим хлібом або гарячою кавою. Квіти та кава — це джерела запаху, тому ми вживаємо орудний відмінок.

<!-- INJECT_ACTIVITY: quiz, Choose between з + Instrumental (companion) and bare Instrumental (tool) -->
<!-- INJECT_ACTIVITY: group-sort, Sort sentences into Tool/Means vs. Accompaniment categories -->


## Підсумок

У цьому модулі ми вивчили важливу функцію орудного відмінка. *(In this module, we learned an important function of the Instrumental case.)* Тепер ви знаєте, як називати знаряддя дії та засіб пересування. You know that Ukrainian uses the bare Instrumental case without a preposition to express the tool you use or the transport you take.

Згадаємо закінчення для однини. *(Let's recall the endings for the singular.)* Жіночий рід має закінчення **-ою** (ручка — ручкою). Чоловічий та середній рід мають **-ом** або **-ем** (олівець — олівцем). У множині всі слова мають **-ами** або **-ями** (ручки — ручками, олівці — олівцями).

Короткий список для самоперевірки: *(A short checklist for a self-test:)*

1. Do I use the preposition "з" for a pen? Ні, ми кажемо просто «ручкою».
2. How do I say "by bus"? Ми кажемо «автобусом».
3. What is the plural ending for "олівець"? Це буде «олівцями».

Типові запитання та відповіді: *(Typical questions and answers:)*

> — **Запитання:** Чим ти пишеш?
> — **Відповідь:** Я пишу ручкою.
> — **Запитання:** Чим ти їдеш додому?
> — **Відповідь:** Я їду трамваєм.
> — **Запитання:** Чим ви їсте суп?
> — **Відповідь:** Ми їмо ложками.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: instrumental-means
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

**Level: A2 (Module 25/60) — ELEMENTARY**

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
