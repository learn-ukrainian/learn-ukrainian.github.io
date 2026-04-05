<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-prepositions-purpose.yaml` file for module **10: Для кого? Без чого? Біля чого?** (a2).

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

- focus: Complete location descriptions with біля/навпроти/коло + correct Genitive
    form
  items: 8
  type: fill-in
- focus: Choose для, без, or біля to complete everyday sentences
  items: 8
  type: quiz
- focus: Match Ukrainian prepositional phrases to their English equivalents
  items: 8
  type: match-up
- focus: Judge whether preposition + noun form combinations are grammatically correct
  items: 8
  type: true-false


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- навчання (studying, education)
- церква (church)
- вокзал (train station)
- річка (river)
required:
- призначення (purpose, destination)
- відпочинок (rest, relaxation)
- допомога (help, assistance)
- сумнів (doubt)
- будинок (building, house)
- зупинка (stop (bus/tram))
- бібліотека (library)
- лікарня (hospital)
- площа (square (city))
- станція (station)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ — Ковдра, ліхтарик і річка

Уявіть, що ви збираєтеся в похід *(Imagine that you are going on a camping trip)*. Що вам потрібно взяти зі собою? When organizing your belongings or setting up camp, you need specific prepositions. In Ukrainian, some of the most useful prepositions require the Genitive case.

Today, we will focus on three essential concepts. When you want to say who an item is for, you use **для** *(for)*. When you lack something crucial, you use **без** *(without)*. And when you describe where things are located, you use **біля** *(near)*, **навпроти** *(opposite)*, or **коло** *(by)*.

Ці слова дуже важливі для спілкування *(These words are very important for communication)*. Без них важко пояснити свої плани *(Without them, it is hard to explain your plans)*. Let's see how Ihor and Marta pack for their trip.

> — **Ігор:** Марто, ми взяли всі речі? *(Marta, did we take all the things?)*
> — **Марта:** Так. Ця велика **ковдра** *(blanket)* — **для Олени** *(for Olena)*. Вона завжди мерзне. *(Yes. This big blanket is for Olena. She is always cold.)*
> — **Ігор:** Добре. А де мій ліхтарик? *(Good. And where is my flashlight?)*
> — **Марта:** Він на столі. Ми не можемо їхати без ліхтарика! *(It is on the table. We cannot go without a flashlight!)*
> — **Ігор:** Згоден, **без ліхтарика — ніяк** *(without a flashlight — no way)*. Де ми поставимо **намет** *(tent)*? *(Agreed, without a flashlight — no way. Where will we put the tent?)*
> — **Марта:** Найкраще місце — **біля річки** *(near the river)*. Там дуже гарно. *(The best place is near the river. It is very beautiful there.)*
> — **Ігор:** Чудова ідея. Намет біля річки, ковдра для Олени, і ліхтарик для нас. Ми готові! *(Great idea. A tent near the river, a blanket for Olena, and a flashlight for us. We are ready!)*


## Для кого це? Для + родовий (Who Is It For? Для + Genitive)

The preposition **для** *(for)* is one of the most common ways to express the intended recipient of an object or action. You must always use the Genitive case after **для**. For regular hard-stem nouns, masculine words take the ending **-а**, while feminine words take **-и**. Plural nouns often take the ending **-ів** or drop their ending entirely.

Читаємо українською:
— Цей великий торт — **для мами** *(This big cake is for mom)*.
— Я купив новий телефон **для брата** *(I bought a new phone for my brother)*.
— Ми готуємо сюрприз **для друга** *(We are preparing a surprise for a friend)*.
— Ця світла кімната — **для дітей** *(This bright room is for the children)*.
— Вона має гарний подарунок **для тата** *(She has a nice present for dad)*.

> — **Оксана:** Для кого ця цікава книга? *(Who is this interesting book for?)*
> — **Степан:** Це для брата. Він дуже любить читати. *(It is for my brother. He loves to read a lot.)*
> — **Оксана:** А ці червоні квіти? Вони для мами? *(And these red flowers? Are they for mom?)*
> — **Степан:** Так, квіти для мами, а торт для дітей. *(Yes, the flowers are for mom, and the cake is for the children.)*

Beyond people, we use **для** to describe the purpose or function of an object. This answers the question: what is this used for? In Ukrainian, it is very common to combine a noun with **для** and another noun in the Genitive case to create a descriptive phrase.

Читаємо українською:
— Це дуже корисна **книга для навчання** *(This is a very useful book for learning)*.
— Ми робимо **вправу для спостереження** *(We are doing an exercise for observation)*.
— Вечір — це **час для відпочинку** *(Evening is a time for rest)*.
— Ось нова **програма для роботи** *(Here is a new program for work)*.
— Це спеціальна **вода для дітей** *(This is special water for children)*.

> — **Ігор:** Що це за синій зошит? *(What kind of blue notebook is this?)*
> — **Марта:** Це мій зошит для навчання. Я пишу там нові слова. *(It is my notebook for learning. I write new words there.)*
> — **Ігор:** А цей великий стіл? *(And this big table?)*
> — **Марта:** Це стіл для роботи. Мій старий стіл був занадто малий. *(This is a table for work. My old table was too small.)*

While hard stems are predictable, you must also remember how soft-stem and mixed-group nouns change in the Genitive case after **для**. Soft masculine nouns (like those ending in **-тель**) take **-я**. Soft feminine nouns (ending in **-ія**) take **-ії**. Soft neuter nouns (ending in **-тя** or **-дя**) take **-тя** or **-дя** (often looking identical to the Nominative form, but with different stress or origins).

Читаємо українською:
— Цей новий комп'ютер — **для вчителя** *(This new computer is for the teacher)*.
— Ми купили квитки в театр **для Марії** *(We bought tickets to the theater for Mariia)*.
— Це дуже необхідно **для життя** *(This is very necessary for life)*.
— Вона шукає подарунок **для Андрія** *(She is looking for a present for Andrii)*.
— У нас є сюрприз **для бабусі** *(We have a surprise for grandma)*.

:::note (Граматика)
**студент** *(student)* → для студент**а** *(hard masculine)*
**вчитель** *(teacher)* → для вчител**я** *(soft masculine)*
**сестра** *(sister)* → для сестр**и** *(hard feminine)*
**Марія** *(Mariia)* → для Марі**ї** *(soft feminine)*
**щастя** *(happiness)* → для щаст**я** *(soft neuter)*
:::

> — **Оксана:** Ти купив квитки для Андрія? *(Did you buy tickets for Andrii?)*
> — **Степан:** Ні, я купив квитки для Марії. Андрій не хоче йти. *(No, I bought tickets for Mariia. Andrii does not want to go.)*
> — **Оксана:** Це добре. Концерт для молоді буде дуже цікавим. *(That is good. The concert for the youth will be very interesting.)*

You will frequently use **для** with personal pronouns to express how something affects someone, or who a gift is meant for. Remember that third-person pronouns add the letter **н-** after prepositions (нього, неї, них).

Читаємо українською:
— Цей новий проект дуже **важливий для мене** *(This new project is very important for me)*.
— У мене є великий **подарунок для тебе** *(I have a big gift for you)*.
— Вона зробила це **для нас** *(She did this for us)*.
— Цей сюрприз тільки **для нього** *(This surprise is only for him)*.
— Ми купили квитки на поїзд **для неї** *(We bought train tickets for her)*.
— Це дуже гарна новина **для вас** *(This is very good news for you)*.
— Ці зручні місця — **для них** *(These comfortable seats are for them)*.

> — **Марта:** Ігорю, у мене є подарунок для тебе. *(Ihor, I have a gift for you.)*
> — **Ігор:** Для мене? Дуже дякую! Що це? *(For me? Thank you very much! What is it?)*
> — **Марта:** Це нова книга. Я знаю, що це важливо для тебе. *(It is a new book. I know that this is important for you.)*
> — **Ігор:** Ти завжди робиш приємні речі для нас. *(You always do nice things for us.)*

Finally, **для** is used with abstract concepts to show the ultimate goal or benefit of an action. This is very common when talking about health, assistance, or general well-being. 

Читаємо українською:
— Ранковий спорт корисний **для здоров'я** *(Morning sport is useful for health)*.
— Мені потрібен час **для роздумів** *(I need time for reflection)*.
— Ми збираємо гроші **для допомоги** *(We are collecting money for help)*.
— Цей інструмент ідеально підходить **для роботи** *(This tool is perfectly suited for work)*.
— Вона робить все можливе **для успіху** *(She does everything possible for success)*.

> — **Степан:** Чому ти так багато бігаєш? *(Why do you run so much?)*
> — **Оксана:** Це корисно для здоров'я. І це дає мені час для роздумів. *(It is good for health. And it gives me time for reflection.)*
> — **Степан:** А я читаю цікаві книги для відпочинку. *(And I read interesting books for relaxation.)*

<!-- INJECT_ACTIVITY: match-up, Match Ukrainian prepositional phrases with 'для' to their English equivalents -->


## Без чого? Без + родовий (Without What? Без + Genitive)

The preposition **без** *(without)* is the exact opposite of the word «з» *(with)*. In Ukrainian, **без** is a strict preposition: it always requires the noun or pronoun that follows it to take the Genitive case. You will hear this word most often in cafes, restaurants, or kitchens when people order food or prepare drinks. For hard-stem masculine nouns, the ending is usually **-а** or **-у**. For hard-stem feminine nouns, the ending is **-и**.

Читаємо українською:
— Я хочу каву **без цукру** *(I want coffee without sugar)*.
— Він п'є чай **без молока** *(He drinks tea without milk)*.
— Дайте, будь ласка, борщ **без сметани** *(Give me, please, borscht without sour cream)*.
— Цей новий салат **без сиру** *(This new salad is without cheese)*.
— Ми замовили велику піцу **без м'яса** *(We ordered a big pizza without meat)*.

We also use **без** to talk about essential items or people we cannot do without. If you forget something important, or if someone is missing from a group, **без** is the preposition you need. Remember that personal pronouns also change their form in the Genitive case after prepositions.

Читаємо українською:
— Я не можу працювати **без комп'ютера** *(I cannot work without a computer)*.
— Вона прийшла **без парасольки**, а на вулиці дощ *(She arrived without an umbrella, and it is raining outside)*.
— Ми поїхали на вокзал **без нього** *(We went to the train station without him)*.
— Вони не можуть зробити це **без допомоги** *(They cannot do this without help)*.
— Діти гуляють у дворі **без шапки** *(The children are walking in the yard without a hat)*.

> — **Оксана:** Чому ти тут без куртки? *(Why are you here without a jacket?)*
> — **Степан:** Я забув її вдома. Але мені тепло без неї. *(I forgot it at home. But I am warm without it.)*
> — **Оксана:** На вулиці холодно. Ти не можеш гуляти без теплого одягу. *(It is cold outside. You cannot walk without warm clothes.)*

When a noun has a soft stem, the Genitive endings look different. Soft feminine nouns change their ending to **-і** (and sometimes the vowel changes inside the word, like **сіль** → **солі**). Soft neuter nouns take **-я**, while hard neuter nouns take **-а**. Soft masculine nouns take **-я** or **-ю**.

:::note (Граматика)
**сіль** *(salt, f)* → без сол**і**
**цибуля** *(onion, f)* → без цибул**і**
**олівець** *(pencil, m)* → без олівц**я**
**вікно** *(window, n)* → без вікн**а**
**море** *(sea, n)* → без мор**я**
:::

Читаємо українською:
— Цей суп зовсім **без солі** *(This soup is completely without salt)*.
— Я люблю салат **без цибулі** *(I like salad without onion)*.
— Студент прийшов на урок **без олівця** *(The student came to the lesson without a pencil)*.
— Наша нова кімната **без вікна** *(Our new room is without a window)*.
— Вони не уявляють літо **без моря** *(They do not imagine summer without the sea)*.

Ukrainians frequently use **без** to form common abstract phrases. These set phrases describe how an action is performed: easily, constantly, or with certainty. You will hear these expressions every day in both casual and professional conversations.

Читаємо українською:
— Ми зробимо це **без проблем** *(We will do this without problems)*.
— Він, **без сумніву**, найкращий лікар у місті *(He is, without doubt, the best doctor in the city)*.
— Автобус їхав дві години **без зупинки** *(The bus drove for two hours without stopping)*.
— Вона працює у магазині **без вихідних** *(She works in the store without days off)*.
— Це важливе рішення прийняли **без вашої згоди** *(This important decision was made without your consent)*.

> — **Марта:** Ти зможеш перекласти цей текст до вечора? *(Will you be able to translate this text by evening?)*
> — **Ігор:** Так, без сумніву. Це дуже легкий текст. *(Yes, without doubt. It is a very easy text.)*
> — **Марта:** Чудово. Я знала, що ти зробиш це без проблем. *(Great. I knew that you would do this without problems.)*

Using **без** is essential for describing weather, daily routines, and contrasting situations. While the preposition «з» *(with)* usually requires the Instrumental case (which you will learn later), **без** always strictly dictates the Genitive. Practicing these scenarios will make the grammatical rule a natural habit.

Читаємо українською:
— Сьогодні похмурий день **без дощу** *(Today is a gloomy day without rain)*.
— Ми любимо каву з цукром, але сьогодні п'ємо **без цукру** *(We like coffee with sugar, but today we are drinking without sugar)*.
— Чай з лимоном смачний, але чай **без лимона** теж непоганий *(Tea with lemon is tasty, but tea without lemon is also not bad)*.
— Вони живуть у маленькому селі **без інтернету** *(They live in a small village without internet)*.
— Я люблю читати старі книги **без картинок** *(I like reading old books without pictures)*.

> — **Степан:** Який сьогодні гарний день без вітру! *(What a beautiful day without wind today!)*
> — **Оксана:** Так, але завтра буде день без сонця. *(Yes, but tomorrow will be a day without sun.)*
> — **Степан:** Нічого страшного. Головне, щоб вихідні були без дощу. *(No problem. The main thing is that the weekend is without rain.)*

<!-- INJECT_ACTIVITY: true-false, Judge whether 'без' + noun form combinations are grammatically correct (e.g., без цукору vs без цукру), 8 items -->


## Де це? Біля, навпроти, коло + родовий (Where Is It? Біля, навпроти, коло + Genitive)

When we need to say that something is located near or next to a reference point, we use the preposition **біля** *(near/next to)*. It is the most common preposition for expressing physical proximity, especially when talking about buildings, locations, or nature. Just like the previous prepositions you learned in this module, it always requires the Genitive case. 

:::note (Граматика)
**школа** *(school, f)* → **біля школи** *(near the school)*
**будинок** *(building, m)* → **біля будинку** *(near the building)*
**річка** *(river, f)* → **біля річки** *(near the river)*
:::

Читаємо українською:
— Моя нова квартира знаходиться **біля парку** *(My new apartment is located near the park)*.
— Ми домовилися зустрітися **біля школи** *(We agreed to meet near the school)*.
— Діти грають у м'яч **біля будинку** *(The children are playing ball near the building)*.
— Наш намет стоїть **біля річки** *(Our tent stands near the river)*.
— Твоя машина припаркована **біля магазину** *(Your car is parked near the store)*.

> — **Ігор:** Де ти зараз? Я чекаю тебе біля входу. *(Where are you now? I am waiting for you near the entrance.)*
> — **Марта:** Я ще біля метро. Буду через п'ять хвилин. *(I am still near the metro. I will be there in five minutes.)*
> — **Ігор:** Добре, я стою біля каси. *(Good, I am standing near the cash register.)*

To describe orientation, specifically when objects are facing each other across a space (like a street or a room), we use **навпроти** *(opposite/across from)*. While **біля** merely indicates proximity, **навпроти** specifically communicates that two objects are positioned face-to-face. This is extremely useful for navigating cities or describing your neighborhood.

:::note (Граматика)
**парк** *(park, m)* → **навпроти парку** *(opposite the park)*
**вокзал** *(train station, m)* → **навпроти вокзалу** *(opposite the train station)*
**церква** *(church, f)* → **навпроти церкви** *(opposite the church)*
:::

Читаємо українською:
— Мій офіс розташований **навпроти парку** *(My office is located opposite the park)*.
— Новий готель збудували **навпроти вокзалу** *(A new hotel was built opposite the train station)*.
— Стара площа знаходиться **навпроти церкви** *(The old square is located opposite the church)*.
— Я сиджу за столом прямо **навпроти тебе** *(I am sitting at the table right opposite you)*.
— Їхній балкон **навпроти нашого вікна** *(Their balcony is opposite our window)*.

> — **Олена:** Ви живете біля вокзалу? *(Do you live near the train station?)*
> — **Тарас:** Ні, ми живемо навпроти вокзалу. Наш дім через дорогу. *(No, we live opposite the train station. Our house is across the road.)*
> — **Олена:** Там, мабуть, дуже шумно. *(It must be very noisy there.)*

You will also encounter the preposition **коло** *(near/by)*. It means exactly the same thing as **біля**, but it is more poetic and slightly literary. While **біля** dominates modern everyday spoken Ukrainian, **коло** frequently appears in classic literature, folk songs, and traditional expressions. Understanding it will help you connect with Ukrainian culture.

:::note (Граматика)
**хата** *(house, f)* → **коло хати** *(near the house)*
**дорога** *(road, f)* → **коло дороги** *(by the road)*
**вікно** *(window, n)* → **коло вікна** *(by the window)*
:::

Читаємо українською:
— Садок вишневий **коло хати** *(A cherry orchard near the house)*.
— Цей старий дуб росте **коло дороги** *(This old oak grows by the road)*.
— Бабуся часто сидить **коло вікна** і читає *(Grandmother often sits by the window and reads)*.
— Маленькі діти граються **коло двору** *(Little children are playing near the yard)*.
— Ми посадили красиві квіти **коло паркану** *(We planted beautiful flowers by the fence)*.

> — **Марія:** Де посадити це дерево? Біля будинку? *(Where to plant this tree? Near the building?)*
> — **Іван:** Краще посадити його коло дороги. *(It is better to plant it by the road.)*
> — **Марія:** Згодна, там більше сонця. *(I agree, there is more sun there.)*

When describing locations in a city, you will often use nouns that belong to the soft or mixed groups. Pay special attention to feminine nouns ending in **-ія**, **-я**, or a husher consonant (like **-щ** or **-ч**). In the Genitive case, they require the **-і** or **-ї** endings rather than **-и**. This is essential for talking about city infrastructure accurately.

:::note (Граматика)
**станція** *(station, f)* → **біля станції** *(near the station)*
**площа** *(square, f)* → **біля площі** *(near the square)*
**лікарня** *(hospital, f)* → **навпроти лікарні** *(opposite the hospital)*
**бібліотека** *(library, f)* → **біля бібліотеки** *(near the library)*
:::

Читаємо українською:
— Нова сучасна кав'ярня відкрилася **біля станції** метро *(A new modern coffee shop opened near the subway station)*.
— Ми зустрілися з друзями **навпроти лікарні** *(We met with friends opposite the hospital)*.
— Студенти завжди збираються ввечері **біля площі** *(Students always gather in the evening near the square)*.
— Моя улюблена пекарня знаходиться **біля бібліотеки** *(My favorite bakery is located near the library)*.
— Туристи зупинилися **навпроти станції** *(The tourists stopped opposite the station)*.

Combining these prepositions with everyday urban vocabulary allows you to give precise directions. Notice how the endings change depending on the gender and stem of the reference point. Feminine nouns typically take **-и** (hard) or **-і** (soft), while masculine nouns will take either **-а/-я** or **-у/-ю** depending on their specific word class.

:::tip (Словник)
**ринок** *(market, m)* → **біля ринку** *(near the market)*
**банк** *(bank, m)* → **навпроти банку** *(opposite the bank)*
**зупинка** *(bus stop, f)* → **навпроти зупинки** *(opposite the bus stop)*
**аптека** *(pharmacy, f)* → **біля аптеки** *(near the pharmacy)*
:::

Читаємо українською:
— Ця **аптека біля ринку** працює цілодобово *(This pharmacy near the market works around the clock)*.
— Твоя **зупинка навпроти банку** *(Your bus stop is opposite the bank)*.
— Вони живуть **навпроти зупинки** автобуса *(They live opposite the bus stop)*.
— Нам треба знайти банкомат **біля аптеки** *(We need to find an ATM near the pharmacy)*.
— Найкращий ресторан міста знаходиться **навпроти ринку** *(The best restaurant of the city is located opposite the market)*.

> — **Дмитро:** Вибачте, де тут найближча аптека? *(Excuse me, where is the nearest pharmacy here?)*
> — **Перехожий:** Вона зовсім поруч, навпроти банку. *(It is very close, opposite the bank.)*
> — **Дмитро:** А банк знаходиться біля ринку? *(And the bank is located near the market?)*
> — **Перехожий:** Так, ідіть прямо. *(Yes, go straight.)*

Let's expand your city map vocabulary. For masculine inanimate objects like buildings or abstract places, remember the rule for Genitive endings. Words denoting institutions or locations like **супермаркет** *(supermarket)* and **театр** *(theater)* take the **-у** ending, while words denoting specific objects or monuments, like **пам'ятник** *(monument)*, often take the **-а** ending.

:::note (Граматика)
**супермаркет** *(supermarket, m)* → **навпроти супермаркету** *(opposite the supermarket)*
**театр** *(theater, m)* → **біля театру** *(near the theater)*
**пам'ятник** *(monument, m)* → **коло пам'ятника** *(near the monument)*
:::

Читаємо українською:
— Наша родина вже десять років живе **біля театру** *(Our family has been living near the theater for ten years)*.
— Вони запаркували машину **навпроти супермаркету** *(They parked the car opposite the supermarket)*.
— Туристи фотографуються **коло пам'ятника** Тарасу Шевченку *(Tourists are taking pictures near the Taras Shevchenko monument)*.
— Я чекаю на тебе на вулиці **біля супермаркету** *(I am waiting for you on the street near the supermarket)*.
— Цей історичний музей знаходиться прямо **навпроти театру** *(This historical museum is located right opposite the theater)*.

<!-- INJECT_ACTIVITY: fill-in, Complete location descriptions with біля/навпроти/коло + correct Genitive form, 8 items -->
<!-- INJECT_ACTIVITY: quiz, Choose для, без, or біля to complete everyday sentences, 8 items -->


## Підсумок — Summary

In this module, we explored three essential functions of the Genitive case using specific prepositions. You learned how to express purpose or designate a recipient using **для** *(for)*, how to indicate the absence of something with **без** *(without)*, and how to describe exact locations using **біля**, **навпроти**, and **коло** *(near, opposite, by)*.

Let's do a quick self-check to review what we covered:
- Чи ви знаєте різницю між «біля» та «навпроти»? *(Do you know the difference between "near" and "opposite"?)*
- Чи можете ви сказати «без» із м'якими іменниками (сіль, олівець)? *(Can you say "without" with soft nouns (salt, pencil)?)*
- Як сказати «для кого» про себе та друзів? *(How to say "for whom" about yourself and friends?)*

Remember the core rule for Genitive endings after these prepositions. Hard-stem nouns typically take **-а** or **-у** for masculine, and **-и** for feminine. Soft-stem nouns and mixed-group nouns often take **-я** or **-ю** for masculine, and **-і** for feminine. Mastering these prepositions allows you to give precise directions, order food exactly how you like it, and easily explain who a gift is intended for.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-prepositions-purpose
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

**Level: A2 (Module 10/60) — ELEMENTARY**

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
