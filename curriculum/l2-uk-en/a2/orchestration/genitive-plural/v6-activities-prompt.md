<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-plural.yaml` file for module **14: Багато книг, мало студентів** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-match-nominative-singular-nouns-to-their-genitive-plural-forms -->`
- `<!-- INJECT_ACTIVITY: fill-in-genitive-plural -->`
- `<!-- INJECT_ACTIVITY: quiz-ending-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-genitive -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the Genitive plural of given nouns (all three genders)
  items: 8
  type: fill-in
- focus: Choose the correct Genitive plural ending (-ів, -ей, zero, or -їв)
  items: 8
  type: quiz
- focus: Match Nominative singular nouns to their Genitive plural forms
  items: 8
  type: match-up
- focus: Sort Genitive plural forms by ending type (-ів/-їв vs. zero vs. -ей)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- чоловічий рід (masculine gender)
- жіночий рід (feminine gender)
- середній рід (neuter gender)
- виняток (exception)
- вставний голосний (inserted vowel)
required:
- множина (plural)
- нульове закінчення (zero ending)
- кілька (a few, several)
- багато (a lot, many)
- мало (a little, few)
- скільки (how many)
- людина (person) / люди (people)
- стаття (article)
- завдання (task, assignment)
- питання (question)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чоловічий рід: -ів та нульове закінчення (Masculine: -ів and zero ending)

Welcome to the "final boss" of Ukrainian cases: the Genitive Plural (**Родовий відмінок множини**). You already know that changing quantities changes the words we use. When we want to say "how many" of something we have, counting past four requires a completely new set of endings, shifting away from the Nominative Plural you are used to. This case has the most variation, but finding the patterns makes it manageable. Let's see this in action.

> — **Продавець:** Нам треба перевірити наш **товар** *(inventory/goods)* сьогодні. *(We need to check our inventory today.)*
> — **Помічник:** Добре. Скільки у нас **пляшок** *(of bottles)* води? *(Good. How many bottles of water do we have?)*
> — **Продавець:** Тут є **п'ять** *(five)* пляшок. А скільки **банок** *(of jars)* меду? *(Here are five bottles. And how many jars of honey?)*
> — **Помічник:** На полиці стоїть тільки три банки. А що з хлібом? *(There are only three jars on the shelf. And what about bread?)*
> — **Продавець:** У нас зовсім немає **булок** *(of buns)*! *(We have absolutely no buns!)*
> — **Помічник:** Треба **терміново** *(urgently)* замовити **багато** *(many)* булок на завтра. *(We urgently need to order a lot of buns for tomorrow.)*

Notice the words **пляшок**, **банок**, and **булок**. They dramatically change their form when we say "five", "many", or when we have "zero" of them.

The core rule of quantity in Ukrainian is strict, yet logical. When you use numerals from five and up, like **п'ять**, **десять** *(ten)*, **двадцять** *(twenty)* or **сто** *(one hundred)*, the following noun must be in the Genitive Plural. The same rule absolutely applies to words of indefinite quantity: **багато**, **мало** *(few/little)*, **кілька** *(a few, several)*, and the question word **скільки** *(how many)*. This contrasts sharply with the numbers two, three, and four, which only require the Nominative Plural. Think of the Genitive Plural as the "group" form.

:::tip (Правило п'яти)
Always remember: 1 = Nominative Singular, 2/3/4 = Nominative Plural, 5+ = Genitive Plural.
«Два **студенти** *(students)*, але п'ять **студентів** *(of students)*.» *(Two students, but five students.)*
:::

For most masculine nouns ending in a hard consonant, forming the Genitive Plural is incredibly simple: just add **-ів** to the word. This is the most productive and common pattern you will hear every day. If you are unsure about a masculine word, this ending is usually your best guess.
- **стіл** *(table)* → п'ять **столів** *(of tables)*
- **будинок** *(building)* → багато **будинків** *(of buildings)*
- **підручник** *(textbook)* → кілька **підручників** *(of textbooks)*
- **студент** *(student)* → десять **студентів**
- **брат** *(brother)* → шість **братів** *(of brothers)*

**Читаємо українською:**
У місті є багато нових будинків. *(There are many new buildings in the city.)*
Я бачу п'ять великих столів у кімнаті. *(I see five large tables in the room.)*
Скільки студентів сьогодні на лекції? *(How many students are at the lecture today?)*
Ми купили кілька нових підручників. *(We bought a few new textbooks.)*

If a masculine noun ends in a soft consonant (like -ь or -ць), it usually still takes the **-ів** ending. However, you must watch out for fleeting vowels. Often, the vowels **е** or **о** in the final syllable will drop out before you add the ending.
- **учитель** *(teacher)* → п'ять **учителів** *(of teachers)*
- **олівець** *(pencil)* → десять **олівців** *(of pencils)*
- **хлопець** *(boy)* → багато **хлопців** *(of boys)*
- **день** *(day)* → сім **днів** *(of days)*

**Читаємо українською:**
У цій школі працює десять учителів. *(Ten teachers work in this school.)*
Мені треба купити кілька кольорових олівців. *(I need to buy a few colored pencils.)*
На вулиці грає багато хлопців. *(Many boys are playing on the street.)*
Я буду там через п'ять днів. *(I will be there in five days.)*

The ending **-їв** is a variation of -ів, and it appears only when the noun's stem ends in a vowel or an apostrophe. This keeps the pronunciation smooth and natural.
- **герой** *(hero)* → багато **героїв** *(of heroes)*
- **трамвай** *(tram)* → п'ять **трамваїв** *(of trams)*
- **подвір'я** *(courtyard)* → кілька **подвір'їв** *(of courtyards)*
- **відкриття** *(discovery)* → багато **відкриттів** *(of discoveries)*

**Читаємо українською:**
Ми знаємо багато українських героїв. *(We know many Ukrainian heroes.)*
Скільки трамваїв їде в центр? *(How many trams are going to the center?)*
У цьому районі є кілька великих подвір'їв. *(There are a few large courtyards in this area.)*

There is a rare exception for masculine nouns. Words that denote nationalities or social groups and end in the suffix **-ин** or **-їн** lose this suffix entirely in the plural. When this happens, they take a "zero ending" (**нульове закінчення**), meaning you add nothing to the base.
- **громадянин** *(citizen)* → мільйони **громадян** *(of citizens)*
- **селянин** *(villager)* → багато **селян** *(of villagers)*
- **болгарин** *(Bulgarian)* → кілька **болгар** *(of Bulgarians)*
- **татарин** *(Tatar)* → тисячі **татар** *(of Tatars)*

**Читаємо українською:**
Тисячі громадян чекають на новини. *(Thousands of citizens are waiting for news.)*
У нашому місті живе багато болгар. *(Many Bulgarians live in our city.)*
Кілька селян продають овочі на ринку. *(A few villagers are selling vegetables at the market.)*

Finally, pay attention to the word **чоловік** *(man/person)*. It has parallel forms depending on the context. When you count people specifically as a unit of measure with numbers, you use the zero ending form: «п'ять чоловік» *(five people/men)*. However, in more general contexts, «багато **чоловіків**» *(of men)* is also perfectly valid. Most other masculine nouns strictly take the -ів ending.

**Читаємо українською:**
Там стояло десять чоловік. *(Ten people stood there.)*
На конференцію приїхало багато молодих чоловіків. *(Many young men came to the conference.)*

<!-- INJECT_ACTIVITY: match-up-match-nominative-singular-nouns-to-their-genitive-plural-forms -->


## Жіночий рід: нульове закінчення

Уявіть велику бібліотеку. Там є багато книг! *(Imagine a large library. There are many books there!)* The most common pattern for feminine nouns in the Genitive plural (**множина**) is the zero ending (**нульове закінчення**). If a feminine noun ends in **-а** in the Nominative singular, you simply remove that **-а** to form the plural for counting. There is no new letter added to the end. However, if removing the ending leaves an **о** or **е** in the final closed syllable, it often changes to **і**.

- **книга** *(book)* → багато **книг** *(of books)*
- **машина** *(car)* → п'ять **машин** *(of cars)*
- **школа** *(school)* → кілька **шкіл** *(of schools)*
- **країна** *(country)* → багато **країн** *(of countries)*

**Читаємо українською:**
У нашому місті є п'ять нових шкіл. *(There are five new schools in our city.)*
Біля магазину стоїть багато машин. *(Many cars are standing near the store.)*
Ми відвідали кілька європейських країн. *(We visited several European countries.)*
У мене немає цікавих книг для тебе. *(I don't have interesting books for you.)*

Скільки сумок ви маєте? *(How many bags do you have?)* Sometimes, dropping the **-а** leaves a difficult-to-pronounce cluster of two consonants at the end of the word. Ukrainian avoids harsh consonant clusters. When a feminine noun stem ends in two consonants (often before **-к**), we insert the vowel **о** between them. This makes the word flow naturally and is called an inserted vowel (**вставний голосний**).

- **жінка** *(woman)* → багато **жінок** *(of women)*
- **сумка** *(bag)* → п'ять **сумок** *(of bags)*
- **студентка** *(female student)* → кілька **студенток** *(of female students)*
- **донька** *(daughter)* → багато **доньок** *(of daughters)*

**Читаємо українською:**
На зустріч приїхало багато відомих жінок. *(Many famous women came to the meeting.)*
У магазині продають кілька червоних сумок. *(They sell several red bags in the store.)*
У цій групі навчається десять студенток. *(Ten female students study in this group.)*
У мене є багато хороших доньок. *(I have many good daughters.)*

Скільки пісень ви співаєте? *(How many songs do you sing?)* In other cases, particularly when the noun stem is soft (ending in **-я**) or ends in certain consonant combinations, the vowel **е** is inserted instead of **о**. If the noun is soft, the soft sign (**ь**) is usually retained to keep the final consonant soft.

- **сестра** *(sister)* → багато **сестер** *(of sisters)*
- **земля** *(land/earth)* → багато **земель** *(of lands)*
- **вишня** *(cherry)* → кілограм **вишень** *(of cherries)*
- **пісня** *(song)* → десять **пісень** *(of songs)*

**Читаємо українською:**
У моєї мами є кілька сестер. *(My mom has a few sisters.)*
Вони співають багато українських пісень. *(They sing many Ukrainian songs.)*
Дідусь купив кілограм солодких вишень. *(Grandpa bought a kilogram of sweet cherries.)*
Цей фермер має багато вільних земель. *(This farmer has many free lands.)*

Скільки лекцій у вас сьогодні? *(How many lectures do you have today?)* There is a specific group of feminine nouns that end in **-ія** in the Nominative singular. When you apply the zero ending rule to these words, the final **-я** drops, but the **й** sound remains. In Ukrainian spelling, this is written as the letter **й**.

- **станція** *(station)* → кілька **станцій** *(of stations)*
- **лекція** *(lecture)* → п'ять **лекцій** *(of lectures)*
- **мрія** *(dream)* → багато **мрій** *(of dreams)*

**Читаємо українською:**
Сьогодні ми слухали кілька довгих лекцій. *(Today we listened to several long lectures.)*
Наш поїзд проїхав п'ять станцій. *(Our train passed five stations.)*
У неї є багато великих мрій. *(She has many big dreams.)*
Вони закінчили будівництво нових станцій. *(They finished the construction of new stations.)*

Скільки статей ти прочитав? *(How many articles did you read?)* While the zero ending is the absolute rule for most feminine nouns, a small but vital group of feminine words takes the **-ей** ending. This often happens with words ending in double consonants plus **я** or certain nouns from the third declension. You simply need to remember these high-frequency words.

- **стаття** *(article)* → багато **статей** *(of articles)*
- **сім'я** *(family)* → кілька **сімей** *(of families)*
- **миша** *(mouse)* → багато **мишей** *(of mice)*
- **ніч** *(night)* → п'ять **ночей** *(of nights)*

**Читаємо українською:**
Вона написала п'ять наукових статей. *(She wrote five scientific articles.)*
У цьому будинку живе кілька сімей. *(Several families live in this building.)*
Кіт спіймав багато мишей у саду. *(The cat caught many mice in the garden.)*
Ми провели там кілька холодних ночей. *(We spent a few cold nights there.)*

На цій вулиці немає площ. *(There are no squares on this street.)* Finally, there is the mixed group of feminine nouns. These are words whose stems end in the consonants **ж**, **ч**, **ш**, or **щ** (like **площа**). These words take a clean zero ending without any vowel insertion. You simply drop the final **-а**.

- **площа** *(square)* → багато **площ** *(of squares)*
- **задача** *(task/math problem)* → десять **задач** *(of tasks)*
- **тиша** *(silence)* → багато **тиш** *(of silences)*

**Читаємо українською:**
У центрі міста є кілька площ. *(There are several squares in the city center.)*
Студенти вирішили десять складних задач. *(The students solved ten difficult tasks.)*
Тут було багато тиш. *(There were many silences here.)*
Я знаю мало таких площ. *(I know few such squares.)*

Багато людей читають книги. *(Many people read books.)* Let's put all these feminine Genitive plural forms into practice using quantity words. Notice how the ending changes depending on the word's stem, but the core rule of dropping the **-а** remains consistent. Remember that numbers five and above always require the Genitive plural.

> — **Максим:** Скільки пісень ти знаєш? *(How many songs do you know?)*
> — **Олена:** Я знаю дуже багато українських пісень. *(I know very many Ukrainian songs.)*
> — **Максим:** А скільки казок ти пам'ятаєш? *(And how many fairy tales do you remember?)*
> — **Олена:** Я пам'ятаю кілька казок, але багато історій. *(I remember a few fairy tales, but many stories.)*

**Читаємо українською:**
У бібліотеці кілька нових книг. *(There are several new books in the library.)*
На площі багато красивих жінок. *(There are many beautiful women on the square.)*
Мама купила десять червоних сумок. *(Mom bought ten red bags.)*
Нам треба вирішити п'ять задач. *(We need to solve five tasks.)*

<!-- INJECT_ACTIVITY: fill-in-genitive-plural -->
<!-- INJECT_ACTIVITY: quiz-ending-choice -->


## Середній рід та узагальнення *(Neuter Gender and Summary)*

Середній рід часто поводиться як жіночий. *(The neuter gender often behaves like the feminine.)* When we look at standard neuter nouns ending in **-о**, they follow the exact same logic as hard-stem feminine nouns. They simply drop the final vowel to form a clean zero ending. Sometimes the root vowel **о** inside the word changes to **і** in closed syllables, just as we saw earlier with some feminine words. 

- **місто** *(city)* → багато **міст** *(of cities)*
- **слово** *(word)* → п'ять **слів** *(of words)*
- **село** *(village)* → кілька **сіл** *(of villages)*

**Читаємо українською:**
У нашій країні є багато великих міст. *(There are many big cities in our country.)*
Я не знаю значення цих нових слів. *(I do not know the meaning of these new words.)*
Вони швидко проїхали повз кілька маленьких сіл. *(They quickly drove past several small villages.)*
У мене сьогодні дуже багато важливих діл. *(I have a lot of important things to do today.)*

Just like feminine nouns, neuter words often have stems that end in a cluster of two consonants. When we drop the final **-о** to form the zero ending, those two consonants are left together. To make the word easier to pronounce, Ukrainian inserts a fleeting vowel (usually **о** or **е**) between them. This is the exact same vowel insertion rule we learned for feminine words like «сумка → сумок».

- **вікно** *(window)* → п'ять **вікон** *(of windows)*
- **полотно** *(canvas/cloth)* → багато **полотен** *(of canvases)*
- **число** *(number)* → кілька **чисел** *(of numbers)*

**Читаємо українською:**
У цій темній кімнаті немає великих вікон. *(There are no big windows in this dark room.)*
Відомий художник купив п'ять нових полотен. *(The famous artist bought five new canvases.)*
На уроці ми вивчили багато нових чисел. *(At the lesson we learned many new numbers.)*
У великому залі стоїть десять м'яких крісел. *(Ten soft armchairs are standing in the large hall.)*

Now, we meet an interesting exception. Soft-stem neuter nouns that end in **-е** do not usually take a zero ending. Instead, they borrow the productive **-ів** ending directly from the masculine gender. This makes them easy to remember, but you must be aware that they cross over to the masculine pattern in the plural form. While some native speakers might occasionally use a rare zero ending for «поле» (піль), the standard form you should use at the A2 level is **-ів**.

- **море** *(sea)* → багато **морів** *(of seas)*
- **поле** *(field)* → кілька **полів** *(of fields)*

**Читаємо українською:**
На нашій планеті є багато глибоких морів. *(There are many deep seas on our planet.)*
Старий фермер має кілька дуже великих полів. *(The old farmer has several very large fields.)*
Скільки теплих морів ви знаєте? *(How many warm seas do you know?)*
Біля цього села немає широких полів. *(There are no wide fields near this village.)*

A very large group of abstract and collective neuter nouns ends in double consonants followed by **-я** (like «завдання» or «питання»). In the Genitive plural, this double consonant disappears, reducing back to a single consonant. The word then takes either a soft sign (**-ь**) or a plain zero ending, depending on the preceding consonant. This is a common grammatical pattern for professional vocabulary.

- **завдання** *(task/assignment)* → багато **завдань** *(of tasks)*
- **питання** *(question)* → кілька **питань** *(of questions)*
- **обличчя** *(face)* → п'ять **облич** *(of faces)*

**Читаємо українською:**
Наші студенти виконали п'ять складних завдань. *(Our students completed five difficult tasks.)*
У мене є кілька важливих питань до вас. *(I have a few important questions for you.)*
У великому натовпі було багато знайомих облич. *(There were many familiar faces in the large crowd.)*
Для цієї складної роботи треба багато знань. *(For this difficult work, a lot of knowledge is needed.)*

There is a special, small group of neuter nouns that belong to the Fourth Declension. These are mostly specific words for young animals and a few common nouns like «ім'я». When these words become plural, they add a grammatical suffix (**-ат-**, **-ят-**, or **-ен-**). In the Genitive plural, they keep this suffix and simply take a standard zero ending.

- **ім'я** *(name)* → багато **імен** *(of names)*
- **теля** *(calf)* → кілька **телят** *(of calves)*
- **лоша** *(foal)* → п'ять **лошат** *(of foals)*

**Читаємо українською:**
Я ніколи не пам'ятаю всіх їхніх імен. *(I never remember all of their names.)*
На фермі мого дідуся є кілька маленьких телят. *(There are several small calves on my grandfather's farm.)*
У стайні ми бачили п'ять красивих лошат. *(We saw five beautiful foals in the stable.)*
Моя кішка зараз годує багато милих кошенят. *(My cat is currently feeding many cute kittens.)*

Finally, let's look at a few high-frequency neuter nouns denoting paired body parts. Because we often talk about eyes, ears, or shoulders in pairs or groups, their plural forms are extremely common in everyday speech. Some of these take the rare **-ей** ending (just like «людей» or «грошей»), while others follow the regular, expected zero-ending rule.

- **око** *(eye)* → багато **очей** *(of eyes)*
- **плече** *(shoulder)* → кілька **плечей** *(of shoulders)*
- **вухо** *(ear)* → п'ять **вух** *(of ears)*

**Читаємо українською:**
На мене дивилося багато сумних очей. *(Many sad eyes were looking at me.)*
У цього дивного монстра п'ять великих вух. *(This strange monster has five big ears.)*
У кімнаті було багато вух, які все чули. *(There were many ears in the room that heard everything.)*
Скільки сильних плечей можуть нести цей вантаж? *(How many strong shoulders can carry this load?)*

Підсумуємо наші знання. *(Let's summarize our knowledge.)* The Genitive plural is arguably the most complex case form in Ukrainian because it contains the most variation across genders. However, you do not need to memorize every single word at once. If you understand the core patterns, you will guess correctly most of the time.

- **Чоловічий рід** *(Masculine)*: Mostly takes **-ів** (братів, студентів). A rare zero ending appears for specific nationalities and citizens (селян, громадян).
- **Жіночий рід** *(Feminine)*: Mostly takes a zero ending (книг, машин). Watch out for vowel insertion (жінок, сестер).
- **Середній рід** *(Neuter)*: Mostly takes a zero ending (міст, вікон), but uses **-ів** for some soft stems (морів, полів).

The most critical skill is using these forms correctly after key quantity words: **багато** *(a lot/many)*, **мало** *(a little/few)*, **кілька** *(a few/several)*, and **скільки** *(how many)*. Strategic advice: do not stress over rare exceptions. Instead, memorize the highest-frequency irregular forms as set phrases, because you will use them every day: багато **людей** *(many people)*, мало **грошей** *(little money)*, кілька **років** *(a few years)*.

> — **Марко:** Скільки студентів сьогодні в аудиторії? *(How many students are in the lecture hall today?)*
> — **Олена:** Сьогодні дуже мало студентів. *(Very few students today.)*
> — **Марко:** А скільки є вільних місць? *(And how many free seats are there?)*
> — **Олена:** Багато вільних місць, але кілька крісел зламані. *(Many free seats, but a few armchairs are broken.)*
> — **Марко:** Чому сьогодні так мало людей? *(Why are there so few people today?)*
> — **Олена:** У них сьогодні багато складних завдань удома. *(They have many difficult tasks at home today.)*

<!-- INJECT_ACTIVITY: group-sort-genitive -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-plural
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

**Level: A2 (Module 14/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

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
