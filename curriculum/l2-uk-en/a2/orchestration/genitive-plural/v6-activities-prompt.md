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

(No injection markers found in prose. All activities will go to workbook.)

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


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

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
## Вступ: Чому Родовий множини — це «бос» рівня А2?

Уявіть, що ви хочете купити багато речей. *(Imagine buying many things.)* Ви вже знаєте Родовий відмінок однини. *(You know Genitive singular.)* Але множина — це зовсім інша історія. *(But plural is different.)*

The Genitive plural is the A2 "boss". It has the most ending variety. Nouns might take an **-ів** ending, a completely dropped zero ending, or an inserted vowel. You must master these patterns to count objects and express quantities.

**Читаємо українською** *(Reading in Ukrainian)*
Там стоїть багато **столів**. *(Many tables stand there.)*
Я маю п'ять **книг**. *(I have five books.)*
У кімнаті є кілька **вікон**. *(Several windows are in the room.)*

**Діалог: Ревізія в сільському магазині** *(Inventory check at a village shop)*

> — **Помічник:** Скільки **пляшок** води ми ще маємо? *(How many bottles of water left?)*
> — **Продавець:** Я бачу тільки п'ять **пляшок**. *(Only five bottles.)*
> — **Помічник:** А скільки **банок** меду там стоїть? *(How many jars of honey?)*
> — **Продавець:** Залишилося три або чотири. Треба замовити більше **банок**. *(Three or four. We must order more jars.)*
> — **Помічник:** Добре. А де хліб? Скільки **булок** на полиці? *(Where is the bread? How many buns?)*
> — **Продавець:** У нас зовсім немає **булок**! Усе швидко продали. *(No buns at all! All sold.)*
> — **Помічник:** Це велика проблема. Усі люди хочуть багато свіжих **булок**. *(Big problem. People want fresh buns.)*
> — **Продавець:** Не хвилюйся, завтра буде багато нових **булок**. *(Do not worry, tomorrow there will be many new buns.)*


## Чоловічий рід: -ів та нульове закінчення

Більшість слів чоловічого роду мають закінчення **-ів** у множині. *(Most masculine words have the -ів ending in plural.)*

The most common pattern for masculine nouns in the Genitive plural is adding the ending **-ів**. If a masculine noun ends in a hard consonant, you simply add this suffix. This is the default rule for most objects, places, and people. It is a reliable pattern that you will use constantly when counting items.

**Паттерн: Твердий приголосний + -ів** *(Pattern: Hard consonant + -ів)*
* стіл *(table)* → стол + -ів = **столів** *(tables)*
* брат *(brother)* → брат + -ів = **братів** *(brothers)*
* студент *(student)* → студент + -ів = **студентів** *(students)*
* підручник *(textbook)* → підручник + -ів = **підручників** *(textbooks)*
* автобус *(bus)* → автобус + -ів = **автобусів** *(buses)*

**Читаємо українською**
В університеті вчиться дуже багато **студентів**. *(Very many students study in the university.)*
Я не бачу моїх старших **братів**. *(I do not see my older brothers.)*
У нашій бібліотеці немає нових **підручників**. *(There are no new textbooks in our library.)*
Ми довго чекаємо біля старих **автобусів**. *(We are waiting a long time near the old buses.)*

Soft-stem masculine nouns also take the standard **-ів** ending. When a masculine word ends in the soft sign (**-ь**), you must drop the soft sign and add **-ів**. Often, this transformation includes the dropping of a fleeting vowel, usually **е**, from the stem. This morphological shift is essential to master.

**Паттерн: М'який приголосний (-ь) → -ів** *(Pattern: Soft consonant (-ь) → -ів)*
* учитель *(teacher)* → учител + -ів = **учителів** *(teachers)*
* олівець *(pencil)* → олівц + -ів = **олівців** *(pencils)*
* палець *(finger)* → пальц + -ів = **пальців** *(fingers)*

**Читаємо українською**
У школі працює десять **учителів**. *(Ten teachers work at the school.)*
Мені потрібно п'ять кольорових **олівців**. *(I need five colored pencils.)*
Людина має двадцять **пальців**. *(A person has twenty fingers.)*

> — **Анна:** Скільки **учителів** працює у цій школі? *(How many teachers work in this school?)*
> — **Богдан:** Тут є багато дуже добрих **учителів**. *(There are many very good teachers here.)*
> — **Анна:** А де я можу купити десять **олівців**? *(And where can I buy ten pencils?)*
> — **Богдан:** Там є великий магазин. У них багато різних **олівців**. *(There is a large store there. They have many different pencils.)*
> — **Анна:** Дякую! Мені треба багато **олівців** для дітей. *(Thank you! I need many pencils for the children.)*

The ending **-їв** is a variation of **-ів** that appears after vowel stems or an apostrophe. For example, neuter nouns like «подвір’я» *(courtyard)* become **подвір’їв**, and «відкриття» *(discovery)* becomes **відкриттів**. Contrast this with soft-stem masculine nouns ending in **-й**, like «герой» *(hero)*. They drop the **-й** and add **-їв**, creating forms like **героїв** and **музеїв**.

**Паттерн: Голосний / Апостроф + -їв** *(Pattern: Vowel / Apostrophe + -їв)*
* музей *(museum)* → музе + -їв = **музеїв** *(museums)*
* герой *(hero)* → геро + -їв = **героїв** *(heroes)*
* подвір’я *(courtyard)* → подвір’ + -їв = **подвір’їв** *(courtyards)*
* відкриття *(discovery)* → відкритт + -їв = **відкриттів** *(discoveries)*

**Читаємо українською**
У Києві є багато цікавих **музеїв**. *(There are many interesting museums in Kyiv.)*
Ми знаємо імена всіх **героїв**. *(We know the names of all the heroes.)*
Біля нових **подвір’їв** ростуть дерева. *(Trees grow near the new courtyards.)*

A small group of masculine nouns takes a zero ending. This happens primarily with nouns denoting nationality or status that end in the suffix **-ин** or **-їн**. In the plural, they lose this suffix entirely, resulting in a zero ending. A crucial related word is «людина» *(person)*, which transforms into **людей** *(people)*.

**Паттерн: Втрата суфікса -ин → Нульове закінчення** *(Pattern: Loss of suffix -ин → Zero ending)*
* громадянин *(citizen)* → громадян + ∅ = **громадян** *(citizens)*
* селянин *(peasant)* → селян + ∅ = **селян** *(peasants)*
* болгарин *(Bulgarian)* → болгар + ∅ = **болгар** *(Bulgarians)*
* людина *(person)* → **людей** *(people)*

**Читаємо українською**
На площі стоїть тисяча **громадян**. *(A thousand citizens stand on the square.)*
Я бачу багато **людей** на вулиці. *(I see many people on the street.)*
Сьогодні немає **людей** у парку. *(Today there are no people in the park.)*

> — **Студент:** Скільки **людей** живе у цьому місті? *(How many people live in this city?)*
> — **Викладач:** Тут живе мільйон **громадян**. *(A million citizens live here.)*
> — **Студент:** А скільки там **болгар**? *(And how many Bulgarians are there?)*
> — **Викладач:** Там живе багато **болгар** і **селян**. *(Many Bulgarians and peasants live there.)*

Many masculine nouns have fleeting vowels (**о** or **е**) in the Nominative singular that disappear when you add the **-ів** ending. This stem change happens when you move from the Nominative to the Genitive plural. Practice recognizing these vowel drops.

**Паттерн: Зникнення голосного + -ів** *(Pattern: Disappearance of vowel + -ів)*
* день *(day)* → дн + -ів = **днів** *(days)*
* хлопець *(boy)* → хлопц + -ів = **хлопців** *(boys)*
* рівень *(level)* → рівн + -ів = **рівнів** *(levels)*

**Читаємо українською**
У нас є тільки п'ять **днів**. *(We have only five days.)*
Я знаю цих двох **хлопців**. *(I know these two boys.)*
Ця гра має багато складних **рівнів**. *(This game has many difficult levels.)*

The word «чоловік» *(man / husband)* has a special dual identity. When you count people with numbers, it takes a zero ending: «п'ять чоловік» *(five people)*. When you mean "men" generally, it uses the standard ending: «багато чоловіків» *(many men)*. The word «раз» *(time)* also takes a zero ending: «п'ять раз» *(five times)*.

**Читаємо українською**
У нашій групі є десять **чоловік**. *(There are ten people in our group.)*
На конференції було багато відомих **чоловіків**. *(There were many famous men at the conference.)*
Я читав цю книгу п'ять **раз**. *(I read this book five times.)*

<!-- INJECT_ACTIVITY: group-sort, Sort Genitive plural forms by ending type (-ів/-їв vs. zero) -->


## Жіночий рід: нульове закінчення та вставні голосні *(Feminine: Zero Ending and Inserted Vowels)*

Most feminine nouns end in **-а** or **-я** in the Nominative singular. To form the Genitive plural, you simply drop this ending. This removes the final vowel entirely, leaving the noun with a "zero ending" (нульове закінчення). This is the foundational rule for the feminine gender. It makes the word shorter and more abrupt compared to its dictionary form. Notice how the word «школа» *(school)* also changes its internal vowel from **о** to **і**.

**Паттерн: Втрата -а/-я → Нульове закінчення** *(Pattern: Loss of -а/-я → Zero ending)*
* книга *(book)* → книг + ∅ = **книг**
* газета *(newspaper)* → газет + ∅ = **газет**
* машина *(car)* → машин + ∅ = **машин**
* країна *(country)* → країн + ∅ = **країн**
* школа *(school)* → шкіл + ∅ = **шкіл**

**Читаємо українською**
У бібліотеці багато **книг**. *(There are many books in the library.)*
Ми купили кілька нових **газет**. *(We bought several new newspapers.)*
На вулиці дуже мало **машин**. *(There are very few cars on the street.)*
У світі є багато цікавих **країн**. *(There are many interesting countries in the world.)*
У нашому місті п'ять нових **шкіл**. *(There are five new schools in our city.)*

> — **Олена:** Скільки **машин** стоїть біля будинку? *(How many cars stand near the house?)*
> — **Тарас:** Там стоїть десять **машин**. *(Ten cars stand there.)*
> — **Олена:** А скільки там **шкіл**? *(And how many schools are there?)*
> — **Тарас:** Там немає **шкіл**. *(There are no schools there.)*

When dropping the final vowel leaves a cluster of consonants at the end of the word, it can be hard to pronounce. Ukrainian prefers a smooth flow of sounds. To fix this awkward cluster, the language inserts a vowel between the last two consonants. If the stem is hard, the inserted vowel is usually **о**. This frequently happens with feminine nouns ending in the suffix **-ка**.

**Паттерн: Вставний голосний «о»** *(Pattern: Inserted vowel "о")*
* жінка *(woman)* → жін + о + к = **жінок**
* сумка *(bag)* → сум + о + к = **сумок**
* зупинка *(stop)* → зупин + о + к = **зупинок**
* казка *(fairy tale)* → каз + о + к = **казок**
* ручка *(pen)* → руч + о + к = **ручок**

**Читаємо українською**
У залі було багато молодих **жінок**. *(There were many young women in the hall.)*
Ми купили кілька нових **сумок**. *(We bought several new bags.)*
Автобус проїхав п'ять **зупинок**. *(The bus passed five stops.)*
Діти знають багато цікавих **казок**. *(Children know many interesting fairy tales.)*
У мене немає червоних **ручок**. *(I don't have red pens.)*

> — **Продавець:** Скільки **сумок** ви хочете купити? *(How many bags do you want to buy?)*
> — **Клієнт:** Мені потрібно п'ять **сумок**. *(I need five bags.)*
> — **Продавець:** А скільки **ручок**? *(And how many pens?)*
> — **Клієнт:** Дайте, будь ласка, десять **ручок**. *(Please give me ten pens.)*

If the consonant cluster contains a soft consonant, or if it involves sonorant letters like **р** or **л**, the inserted vowel is typically **е**. This makes the phonetic transition between sounds smoother and more natural. While the insertion of **е** is less common than **о**, it is still very important for pronouncing everyday words correctly. The word «гривня» *(hryvnia)* is a classic example of this pattern.

**Паттерн: Вставний голосний «е»** *(Pattern: Inserted vowel "е")*
* сестра *(sister)* → сест + е + р = **сестер**
* земля *(earth/land)* → зем + е + ль = **земель**
* гривня *(hryvnia)* → грив + е + нь = **гривень**
* крапля *(drop)* → крап + е + ль = **крапель**

**Читаємо українською**
У нього є п'ять **сестер**. *(He has five sisters.)*
Король хоче захопити багато нових **земель**. *(The king wants to capture many new lands.)*
Ця книга коштує триста **гривень**. *(This book costs three hundred hryvnias.)*
Після дощу на склі багато **крапель**. *(After the rain there are many drops on the glass.)*

> — **Максим:** Скільки у тебе **сестер**? *(How many sisters do you have?)*
> — **Андрій:** У мене немає **сестер**, тільки брати. *(I have no sisters, only brothers.)*
> — **Максим:** Скільки **гривень** коштує квиток? *(How many hryvnias does the ticket cost?)*
> — **Андрій:** Він коштує п'ятдесят **гривень**. *(It costs fifty hryvnias.)*

Feminine nouns ending in **-я** (soft stems) also take a zero ending in the plural. However, because the consonant right before the ending was soft, this linguistic softness must be preserved even when the vowel is gone. We do this by adding a soft sign (**ь**) at the very end of the word. Sometimes, this rule also combines with the inserted **е** rule to break up consonant clusters.

**Паттерн: Нульове закінчення та м'який знак** *(Pattern: Zero ending and soft sign)*
* вулиця *(street)* → вулиц + ь = **вулиць**
* крамниця *(shop)* → крамниц + ь = **крамниць**
* пісня *(song)* → піс + е + нь = **пісень**
* вишня *(cherry)* → виш + е + нь = **вишень**

**Читаємо українською**
У центрі міста багато широких **вулиць**. *(There are many wide streets in the city center.)*
Тут мало **крамниць**, але багато кафе. *(There are few shops here, but many cafes.)*
Ми заспівали кілька українських **пісень**. *(We sang several Ukrainian songs.)*
У саду немає **вишень**. *(There are no cherries in the garden.)*

Feminine nouns that end in the combination **-ія** form a special, highly predictable subset. When you remove the final **-я** to form the zero ending, the letter **і** remains. The hidden "y" sound from the dropped "я" transforms into the visible consonant **й**. Thus, all words in this group will reliably end in **-ій** in the Genitive plural form.

**Паттерн: Група на -ія → -ій** *(Pattern: Group ending in -ія → -ій)*
* станція *(station)* → станці + й = **станцій**
* лекція *(lecture)* → лекці + й = **лекцій**
* аудиторія *(auditorium/classroom)* → аудиторі + й = **аудиторій**
* історія *(history/story)* → історі + й = **історій**

**Читаємо українською**
У нашому метро п'ятдесят **станцій**. *(There are fifty stations in our metro.)*
Сьогодні у нас немає **лекцій**. *(Today we have no lectures.)*
На цьому поверсі багато світлих **аудиторій**. *(There are many bright classrooms on this floor.)*
Дідусь знає багато цікавих **історій**. *(Grandfather knows many interesting stories.)*

While almost all feminine nouns follow the zero-ending pattern, a very small, closed group of words completely breaks this rule. These specific nouns take the ending **-ей** instead of a zero ending. There is no logical reason for this; it is a historical linguistic anomaly. You simply need to memorize these exceptions, as they include some of the most common words used in everyday Ukrainian speech.

**Паттерн: Винятки з закінченням -ей** *(Pattern: Exceptions with -ей ending)*
* стаття *(article)* → стат + -ей = **статей**
* сім'я *(family)* → сім + -ей = **сімей**
* миша *(mouse)* → миш + -ей = **мишей**
* свиня *(pig)* → свин + -ей = **свиней**

**Читаємо українською**
Журналіст написав кілька нових **статей**. *(The journalist wrote several new articles.)*
У цьому будинку живе п'ять **сімей**. *(Five families live in this house.)*
Кіт зловив багато **мишей**. *(The cat caught many mice.)*
Фермер має багато **свиней**. *(The farmer has many pigs.)*

> — **Студент:** Скільки **статей** треба прочитати? *(How many articles is it necessary to read?)*
> — **Викладач:** Прочитайте п'ять **статей**. *(Read five articles.)*
> — **Студент:** А скільки **сімей** брали участь у дослідженні? *(And how many families took part in the research?)*
> — **Викладач:** Близько ста **сімей**. *(About a hundred families.)*

<!-- INJECT_ACTIVITY: match-up, Match Nominative singular nouns to their Genitive plural forms -->


## Середній рід та узагальнення

The basic rule for neuter nouns is very similar to the rule for feminine nouns. Most neuter nouns end in **-о** in the Nominative singular. To form the Genitive plural, you simply drop this final vowel, resulting in a zero ending. This pattern is highly predictable and covers the majority of hard-stem neuter words you will encounter. Notice how the vowels inside the root often change from **о** or **е** to **і** when the ending disappears.

**Паттерн: Середній рід — нульове закінчення** *(Pattern: Neuter gender — zero ending)*
* слово *(word)* → слов - о = **слів**
* місто *(city)* → міст - о = **міст**
* село *(village)* → сел - о = **сіл**
* озеро *(lake)* → озер - о = **озер**

**Читаємо українською**
Він знає багато нових **слів**. *(He knows many new words.)*
Ми відвідали кілька великих **міст**. *(We visited several large cities.)*
Біля лісу немає старих **сіл**. *(There are no old villages near the forest.)*
На півночі країни багато глибоких **озер**. *(There are many deep lakes in the north of the country.)*

Just as with feminine nouns, removing the final vowel from a neuter word can sometimes leave an unpronounceable cluster of consonants at the end of the stem. When this happens, Ukrainian inserts an **о** or an **е** between the final consonants for phonetic ease. However, if the consonants are easy to pronounce together, no vowel is inserted.

**Паттерн: Вставні голосні в середньому роді** *(Pattern: Inserted vowels in neuter gender)*
* вікно *(window)* → вікн + о = **вікон**
* полотно *(canvas)* → полотн + е = **полотен**
* дзеркало *(mirror)* → дзеркал = **дзеркал** (no insertion)
* яблуко *(apple)* → яблук = **яблук** (no insertion)

**Читаємо українською**
У цьому класі немає широких **вікон**. *(There are no wide windows in this classroom.)*
Художник купив багато нових **полотен**. *(The artist bought many new canvases.)*
У ванній кімнаті мало **дзеркал**. *(There are few mirrors in the bathroom.)*
У саду лежить багато стиглих **яблук**. *(Many ripe apples lie in the garden.)*

> — **Дизайнер:** Скільки **дзеркал** треба для кімнати? *(How many mirrors are needed for the room?)*
> — **Клієнт:** Я думаю, два або три. *(I think two or three.)*
> — **Дизайнер:** А скільки **вікон** тут є? *(And how many windows are there here?)*
> — **Клієнт:** Тут є п'ять великих **вікон**. *(There are five large windows here.)*

Neuter nouns that end in **-е** in the Nominative singular often behave differently. Instead of taking a zero ending, they typically borrow the **-ів** ending from the masculine pattern. This is a very common feature of the Genitive plural, blurring the lines between genders. You must learn to distinguish these words from verbal nouns ending in **-ння**, which have a completely different rule.

**Паттерн: Середній рід із закінченням -ів** *(Pattern: Neuter gender with -ів ending)*
* море *(sea)* → мор + ів = **морів**
* поле *(field)* → пол + ів = **полів**

**Читаємо українською**
Моряк бачив багато глибоких **морів**. *(The sailor saw many deep seas.)*
Там немає зелених **полів**. *(There are no green fields there.)*
Туристи зробили багато фотографій теплих **морів**. *(The tourists took many photos of warm seas.)*
Навесні там багато квітучих **полів**. *(In the spring, there are many blooming fields there.)*

A massive category of neuter nouns ends in **-ння**, representing abstract concepts or the result of an action (verbal nouns). These words always take a zero ending. Because the stem ends in a soft consonant, they require a soft sign (**-ь**) at the end. Be careful not to confuse them with the **-е** nouns that take **-ів**.

**Паттерн: Віддієслівні іменники на -ння** *(Pattern: Verbal nouns in -ння)*
* завдання *(task)* → завдан + ь = **завдань**
* питання *(question)* → питан + ь = **питань**
* знання *(knowledge)* → знан + ь = **знань**
* читання *(reading)* → читан + ь = **читань**

**Читаємо українською**
Сьогодні у нас немає домашніх **завдань**. *(Today we have no homework tasks.)*
У студентів було кілька важливих **питань**. *(The students had a few important questions.)*
Для цієї роботи треба багато **знань**. *(For this job, a lot of knowledge is needed.)*
Він організував кілька публічних **читань**. *(He organized several public readings.)*

> — **Студент:** Чи є багато **питань** у тесті? *(Are there many questions in the test?)*
> — **Професор:** Ні, тільки десять **питань**. *(No, only ten questions.)*
> — **Студент:** А скільки практичних **завдань**? *(And how many practical tasks?)*
> — **Професор:** П'ять практичних **завдань**. *(Five practical tasks.)*

Some neuter words undergo a significant stem transformation in the plural. Words that belong to this special group add the syllable **-ен-** to the stem before forming the Genitive plural. For words like **ім'я** or **плем'я**, the ending changes drastically to **-ен**. You simply need to memorize these forms, as they are essential everyday vocabulary.

**Паттерн: Спеціальні основи середнього роду** *(Pattern: Special neuter stems)*
* ім'я *(name)* → ім + ен = **імен**
* плем'я *(tribe)* → плем + ен = **племен**

**Читаємо українською**
Я не пам'ятаю їхніх **імен**. *(I don't remember their names.)*
Історик знає культуру давніх **племен**. *(The historian knows the culture of ancient tribes.)*
У цьому списку немає ваших **імен**. *(Your names are not on this list.)*
Вони вивчають історію африканських **племен**. *(They are studying the history of African tribes.)*

Finally, let us review when to actually use all these complex Genitive plural forms. You must use the Genitive plural after numbers from five onwards (**п'ять**, **шість**, **десять**, etc.), and after words expressing quantity such as **багато** (many), **мало** (few), **кілька** (several), and **скільки** (how many). This is the most common reason you will need the Genitive plural in everyday conversations.

**Паттерн: Кількість та числа** *(Pattern: Quantity and numbers)*
* 5+ / багато / мало / кілька / скільки + Родовий відмінок множини *(Genitive plural)*

**Читаємо українською**
На вулиці багато **людей**. *(There are many people on the street.)*
Він чекав кілька **днів**. *(He waited for several days.)*
Я живу тут уже десять **років**. *(I have lived here for ten years already.)*
Ми отримали мало нових **завдань**. *(We received few new tasks.)*

> — **Марія:** Скільки **студентів** у вашій групі? *(How many students are in your group?)*
> — **Викладач:** У нас двадцять **студентів**. *(We have twenty students.)*
> — **Марія:** А скільки **питань** на екзамені? *(And how many questions on the exam?)*
> — **Викладач:** Тридцять **питань**. *(Thirty questions.)*

<!-- INJECT_ACTIVITY: fill-in, Form the Genitive plural of given nouns (all three genders) -->
<!-- INJECT_ACTIVITY: quiz, Choose the correct Genitive plural ending (-ів, -ей, zero, or -їв) -->


## Підсумок — Summary

Вивчення родового відмінка множини — це великий крок! *(Learning the Genitive plural is a big step!)* It is the most complex form, but you can master it. Use this checklist to review:

* **Do I use -ів for most masculine nouns?** 
  Так, тут багато **братів**. *(Yes, there are many brothers here.)*
* **Do I remove the -а from feminine nouns?**
  Так, у нас мало **книг**. *(Yes, we have few books.)*
* **Do I insert «о» or «е» for clusters?**
  Так, я бачу багато **жінок** і **сестер**. *(Yes, I see many women and sisters.)*
* **Do I use a zero ending for -ння neuter nouns?**
  Так, немає нових **завдань**. *(Yes, there are no new tasks.)*
* **Can I count from 5 to 10 correctly?**
  Так, це **п'ять студентів**. *(Yes, these are five students.)*

Родовий відмінок множини вимагає практики. *(The Genitive plural requires practice.)* Do not worry if you make mistakes with exceptions. Read texts, listen to native speakers, and the patterns will become natural. Успіхів! *(Good luck!)*

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
