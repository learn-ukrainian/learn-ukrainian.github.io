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

- `<!-- INJECT_ACTIVITY: match-up-purpose -->`
- `<!-- INJECT_ACTIVITY: quiz-prep-choice-choose-between-and-to-complete-everyday-sentences -->`
- `<!-- INJECT_ACTIVITY: fill-in-location -->`
- `<!-- INJECT_ACTIVITY: true-false-grammar -->`

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


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

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
## Для кого це? Для + родовий (Who Is It For? Для + Genitive)

In Ukrainian, we use the preposition **для** (for) to express purpose or to show the intended recipient of an object or action. While the English word "for" has many different meanings and can be used in various grammatical structures, the Ukrainian **для** is very specific. It always answers the specific questions **для кого?** (for whom?) or **для чого?** (for what?). Most importantly, the preposition **для** always triggers the Genitive case. This means the noun that follows it must change its ending according to the rules of the Genitive case.

«Читаємо українською» (Reading in Ukrainian):
— Це **подарунок для мами** (This is a gift for mom).
— Мені потрібен **час для відпочинку** (I need time for rest).
— Ця міцна кава **для тебе** (This strong coffee is for you).
— Ми купили квитки **для дітей** (We bought tickets for the children).

When we want to explain what something is strictly intended for, we attach **для** to a noun. This is often an abstract noun or a noun that describes an action or process. This structure helps us talk about the specific function of everyday objects.

Змінюємо закінчення (Changing endings):
«здоров'я» (health) → «для здоров'я»
«робота» (work) → «для роботи»
«навчання» (studying) → «для навчання»

«Читаємо українською»:
— Свіжі фрукти дуже корисні **для здоров'я** (Fresh fruit is very useful for health).
— Я шукаю зручний одяг **для роботи** (I am looking for comfortable clothes for work).
— У нас є нові книги **для навчання** (We have new books for studying).
— Мені потрібен великий стіл **для комп'ютера** (I need a large desk for the computer).
— Це спеціальна кімната **для зустрічей** (This is a special room for meetings).

Now let's look at how we use **для** when giving something to a person or preparing something for them. We will start with regular hard-stem nouns. Remember the standard Genitive case endings we learned earlier: masculine nouns usually take the ending **-а**, and feminine nouns take the ending **-и**.

Змінюємо закінчення (Changing endings):
«брат» (brother) → «для брата»
«сестра» (sister) → «для сестри»
«тато» (dad) → «для тата»

«Читаємо українською»:
— Я маю квиток на концерт **для брата** (I have a concert ticket for my brother).
— Ми готуємо великий сюрприз **для сестри** (We are preparing a big surprise for the sister).
— Сьогодні буде смачна вечеря **для тата** (Today there will be a tasty dinner for dad).
— Я купив цей новий телефон **для друга** (I bought this new phone for a friend).
— Це дуже цікава гра **для сина** (This is a very interesting game for the son).

What about soft-stem nouns and feminine nouns ending in **-ія**? They follow their own specific patterns. For soft masculine nouns, the Genitive ending is usually **-я**. For feminine nouns ending in **-ія**, the ending changes to **-ії**. Soft feminine nouns ending in **-я** take the ending **-і**.

Змінюємо закінчення (Changing endings):
«вчитель» (teacher) → «для вчителя»
«Марія» (Maria) → «для Марії»
«Софія» (Sophia) → «для Софії»

«Читаємо українською»:
— У класі стоїть новий стілець **для вчителя** (A new chair for the teacher stands in the classroom).
— Я несу ці красиві квіти **для Марії** (I am carrying these beautiful flowers for Maria).
— Це м'яка іграшка **для Софії** (This is a soft toy for Sophia).
— Ми купили ефективні ліки **для бабусі** (We bought effective medicine for grandma).
— Це важливий лист **для лікаря** (This is an important letter for the doctor).

Finally, let's look at neuter nouns and plural recipients after our new preposition. Many abstract neuter nouns end in double consonants plus **-я**, like **щастя** (happiness) or **життя** (life). In the Genitive case, their ending remains **-я**. For plural recipients, masculine nouns often take the ending **-ів**, while feminine and neuter nouns usually drop their final vowel entirely.

Змінюємо закінчення (Changing endings):
«щастя» (happiness) → «для щастя»
«діти» (children) → «для дітей»
«друзі» (friends) → «для друзів»

«Читаємо українською»:
— Ми зробимо все можливе **для щастя** (We will do everything possible for happiness).
— Чиста вода дуже потрібна **для життя** (Clean water is very necessary for life).
— У нашому готелі є кімната **для дітей** (Our hotel has a room for children).
— У мене є хороші новини **для друзів** (I have good news for friends).
— Це весела музика **для танців** (This is fun music for dances).

Let's see these Genitive forms in action in a real conversation. Ігор (Igor) and Марта (Marta) are packing their bags for a weekend camping trip in the mountains. Pay attention to how they discuss the purpose of the items and who the specific items are for.

> — **Ігор:** Марто, ми взяли всі речі **для походу**? *(Marta, did we take all the things for the hike?)*
> — **Марта:** Так, майже всі. Але я ще шукаю теплий одяг. *(Yes, almost all. But I am still looking for warm clothes.)*
> — **Ігор:** Ось лежить велика ковдра. **Для кого** ця ковдра? *(Here lies a large blanket. Who is this blanket for?)*
> — **Марта:** Вона **для Олени**. Їй завжди холодно вночі. *(It is for Olena. She is always cold at night.)*
> — **Ігор:** Зрозумів. А навіщо нам цей великий стіл? *(Understood. And what do we need this large table for?)*
> — **Марта:** Це **для комфорту**. Ми будемо там їсти і пити чай. *(It is for comfort. We will eat and drink tea there.)*
> — **Ігор:** Добре, тоді я покладу його в машину. А де ліки **для бабусі**? *(Good, then I will put it in the car. And where is the medicine for grandma?)*
> — **Марта:** Вони вже там. Я все зібрала **для подорожі**. *(They are already there. I packed everything for the trip.)*

<!-- INJECT_ACTIVITY: match-up-purpose -->


## Без чого? Без + родовий (Without What? Без + Genitive)

The preposition **без** (without) is one of the most common and useful words in Ukrainian. It always requires the Genitive case. We use it to express the absence or lack of something, or when we do things without a certain object or person. The best place to start practicing **без** is in a café or restaurant, as it is essential for customizing your food and drinks. 

Змінюємо закінчення (Changing endings):
«цукор» (sugar) → «без цукру»
«молоко» (milk) → «без молока»
«газ» (gas) → «без газу»

«Читаємо українською»:
— Я завжди п'ю каву **без цукру** (I always drink coffee without sugar).
— Дайте, будь ласка, чорний чай **без молока** (Please give me black tea without milk).
— Ми хочемо замовити воду **без газу** (We want to order still water / water without gas).
— Вона їсть свіжий салат **без м'яса** (She is eating a fresh salad without meat).
— Цей гарячий суп зовсім **без солі** (This hot soup is completely without salt).

Beyond food and drinks, **без** is frequently paired with abstract nouns to form common idioms, adverbial phrases, and everyday modifiers. When you combine **без** with a concept, it describes how an action is performed or the state of a situation. These phrases are very natural and are used constantly in spoken Ukrainian.

Змінюємо закінчення (Changing endings):
«сумнів» (doubt) → «без сумніву»
«проблема» (problem) → «без проблем»
«допомога» (help) → «без допомоги»
«успіх» (success) → «без успіху»

«Читаємо українською»:
— Це найкращий варіант, **без сумніву** (This is the best option, without doubt).
— Я зроблю це нове завдання **без проблем** (I will do this new task without problems / no problem).
— Він швидко закінчив роботу **без допомоги** (He quickly finished the work without help).
— Ми довго шукали ключі **без успіху** (We searched for the keys for a long time without success).
— Вони працюють цілий день **без зупинки** (They are working all day without a stop).

When using masculine nouns after **без**, you must choose between the **-а** (or **-я**) and **-у** (or **-ю**) endings. As a general rule, concrete objects that you can easily count or touch usually take the **-а** ending. On the other hand, substances, materials, or abstract concepts often take the **-у** ending. 

Змінюємо закінчення (Changing endings):
«хліб» (bread) → «без хліба»
«ніж» (knife) → «без ножа»
«цукор» (sugar) → «без цукру»
«шум» (noise) → «без шуму»

«Читаємо українською»:
— Ми ніколи не їмо борщ **без хліба** (We never eat borscht without bread).
— Я не можу нарізати овочі **без ножа** (I cannot cut vegetables without a knife).
— Мій старший брат п'є чай **без цукру** (My older brother drinks tea without sugar).
— Діти спокійно гралися в кімнаті **без шуму** (The children played calmly in the room without noise).
— Він вийшов на вулицю **без телефона** (He went outside without a phone).

For feminine nouns after **без**, the endings are much simpler and follow the standard rules. Hard-stem feminine nouns take **-и**, while soft-stem nouns (ending in **-я** or a soft consonant) take **-і**. Neuter nouns typically change their final **-о** to **-а**, and their final **-е** to **-я**.

Змінюємо закінчення (Changing endings):
«вода» (water) → «без води»
«сіль» (salt) → «без солі»
«вікно» (window) → «без вікна»
«море» (sea) → «без моря»

«Читаємо українською»:
— Жодна людина не живе довго **без води** (No person lives long without water).
— Ця смачна страва приготовлена **без солі** (This tasty dish is prepared without salt).
— У цьому старому будинку є кімната **без вікна** (In this old building there is a room without a window).
— Я дуже сумую, коли живу **без моря** (I am very sad when I live without the sea).
— Вона пішла на роботу **без куртки** (She went to work without a jacket).

In natural conversation, **без** is frequently used in complete sentences to emphasize dependence or absolute necessity. A very common structure is pairing it with the verb phrase **не можу** (I cannot) to express that something is essential for your routine. You can also use **без** with pronouns, just like you would with regular nouns.

Змінюємо закінчення (Changing endings):
«кава» (coffee) → «без кави»
«парасолька» (umbrella) → «без парасольки»
«він» (he) → «без нього»

«Читаємо українською»:
— Вранці я просто **не можу без кави** (In the morning I simply cannot without coffee).
— На вулиці сильний дощ, а вона прийшла **без парасольки** (There is heavy rain outside, and she arrived without an umbrella).
— Ми поїхали на вечірній концерт **без нього** (We went to the evening concert without him).
— Вони зовсім не можуть жити **без музики** (They absolutely cannot live without music).
— Цей складний проєкт неможливий **без вас** (This complex project is impossible without you).

Let's return to Ігор (Igor) and Марта (Marta). They are continuing to pack their bags for the camping trip. Igor suddenly realizes they forgot an essential item for the dark mountain nights. Pay attention to how they use **без** to discuss what they cannot go without.

> — **Ігор:** Марто, ми забули щось дуже важливе. *(Marta, we forgot something very important.)*
> — **Марта:** Що саме? Я думаю, що ми взяли все. *(What exactly? I think that we took everything.)*
> — **Ігор:** Ми не можемо їхати **без ліхтарика**. У горах дуже темно. *(We cannot go without a flashlight. It is very dark in the mountains.)*
> — **Марта:** Ой, правда. Вночі **без нього** ми нічого не побачимо. *(Oh, right. At night without it we will see nothing.)*
> — **Ігор:** Так. І ще нам треба більше питної води. *(Yes. And we also need more drinking water.)*
> — **Марта:** Згодна. У такий похід не можна йти **без води**. *(Agreed. You cannot go on such a hike without water.)*
> — **Ігор:** Добре, що ми робимо список. Подорожувати **без плану** — це погана ідея. *(Good that we are making a list. Traveling without a plan is a bad idea.)*

<!-- INJECT_ACTIVITY: quiz-prep-choice-choose-between-and-to-complete-everyday-sentences -->


## Де це? Біля, навпроти, коло + родовий (Where Is It? Біля, навпроти, коло + Genitive)

When we want to describe where something is located in relation to another object, we often use the preposition **біля** (near, next to, by). This is the most common preposition for expressing spatial proximity in spoken Ukrainian. The logic is simple: you have a reference point, and something else is situated close to it. Because it defines a relationship of location based on a specific object, it always requires the Genitive case.

Змінюємо закінчення (Changing endings):
«школа» (school) → «біля школи»
«будинок» (building, house) → «біля будинку»
«вікно» (window) → «біля вікна»

«Читаємо українською»:
— Моя нова робота знаходиться **біля школи** (My new job is located near the school).
— Ми живемо в квартирі **біля будинку** моїх батьків (We live in an apartment near my parents' building).
— Вона любить читати книгу **біля вікна** (She likes to read a book by the window).
— Зустрінемося завтра **біля метро** (Let's meet tomorrow near the subway).

Let's practice how different noun genders change their endings after **біля**. Remember that masculine nouns usually take **-а** or **-у**, feminine nouns take **-и** or **-і**, and neuter nouns take **-а** or **-я**. You will hear this preposition constantly when Ukrainians describe their cities, neighborhoods, or favorite places.

Змінюємо закінчення (Changing endings):
«парк» (park) → «біля парку»
«річка» (river) → «біля річки»
«море» (sea) → «біля моря»

«Читаємо українською»:
— Цей чудовий ресторан розташований **біля парку** (This wonderful restaurant is located near the park).
— Влітку ми часто відпочиваємо **біля річки** (In the summer we often relax by the river).
— Вони купили маленьку дачу **біля моря** (They bought a small summer house by the sea).
— Діти радісно грають у футбол **біля лісу** (The children joyfully play football near the forest).

Another very useful spatial preposition is **навпроти** (opposite, across from). We use this word when two objects are facing each other, usually separated by a street, a corridor, or a table. Like our previous prepositions, it strictly demands the Genitive case for the noun that follows it.

Змінюємо закінчення (Changing endings):
«банк» (bank) → «навпроти банку»
«вокзал» (train station) → «навпроти вокзалу»
«церква» (church) → «навпроти церкви»

«Читаємо українською»:
— Нова кав'ярня відкрилася **навпроти банку** (A new coffee shop opened opposite the bank).
— Наш готель знаходиться прямо **навпроти вокзалу** (Our hotel is located right across from the train station).
— Вони зустрілися на площі **навпроти церкви** (They met on the square opposite the church).
— Я мовчки сиджу **навпроти нього** і слухаю (I silently sit opposite him and listen).

You will also encounter the preposition **коло** (near, by). It has exactly the same meaning as **біля** and also takes the Genitive case. While it is slightly less common in everyday urban speech, it is extremely frequent in Ukrainian literature, folk songs, and rural contexts. Knowing it will help you understand traditional stories and poetic descriptions.

Змінюємо закінчення (Changing endings):
«хата» (house, traditional Ukrainian dwelling) → «коло хати»
«дорога» (road) → «коло дороги»

«Читаємо українською»:
— У селі є старий сад **коло хати** (In the village there is an old orchard by the house).
— Вони зупинили машину **коло дороги** (They stopped the car by the road).
— Ця красива пісня розповідає про дівчину **коло річки** (This beautiful song tells about a girl by the river).
— Бабуся завжди сидить **коло вікна** і дивиться на вулицю (Grandmother always sits by the window and looks at the street).

When navigating a Ukrainian city, pay special attention to soft-stem feminine nouns, particularly those ending in **-ія**, **-я**, or a soft consonant like in **площа** (square (city)). These nouns will take the ending **-і** or **-ї** in the Genitive case. 

Змінюємо закінчення (Changing endings):
«станція» (station) → «біля станції»
«площа» → «біля площі»
«лікарня» (hospital) → «навпроти лікарні»

«Читаємо українською»:
— Я зараз стою **біля станції** метро (I am standing near the subway station right now).
— Головний музей міста розташований **біля площі** (The main museum of the city is located near the square).
— Ми припаркували автомобіль **навпроти лікарні** (We parked the car opposite the hospital).
— Ця довга вулиця закінчується **біля академії** (This long street ends near the academy).

Let's build a mental map to see how these prepositions work together to describe a neighborhood. When you ask for directions, locals will often use landmarks and spatial relationships rather than exact street addresses. 

«Читаємо українською»:
— Мій район дуже зручний для життя (My neighborhood is very convenient for living).
— Велика **аптека** (pharmacy) знаходиться **біля ринку** (A large pharmacy is located near the market).
— Якщо ви хочете випити кави, є гарне кафе **навпроти бібліотеки** (If you want to drink coffee, there is a nice cafe opposite the library).
— Також тут є автобусна **зупинка** (stop) прямо **біля станції** метро (Also here is a bus stop right near the subway station).
— Я часто гуляю **навпроти театру** (I often walk opposite the theater).
— Мій дім стоїть **біля парку**, де весело співають птахи (My house stands near the park where birds sing merrily).

Let's rejoin Ігор (Igor) and Марта (Marta). They have finally arrived at their campsite in the mountains. Now they need to decide exactly where to pitch their tent. Notice how they use our new prepositions to discuss the best location.

> — **Ігор:** Нарешті ми приїхали. Де ми поставимо наш намет? *(Finally we arrived. Where will we put our tent?)*
> — **Марта:** Я думаю, що найкраще місце — **біля річки**. *(I think that the best place is near the river.)*
> — **Ігор:** Ні, **біля річки** може бути холодно вночі. *(No, near the river it can be cold at night.)*
> — **Марта:** Тоді, можливо, там, **навпроти дерева**? *(Then maybe there, opposite the tree?)*
> — **Ігор:** Там дуже гарно. І ми зможемо сидіти **коло вогню** ввечері. *(It is very nice there. And we will be able to sit by the fire in the evening.)*
> — **Марта:** Чудова ідея. Я покладу наші речі **біля намету**. *(Great idea. I will put our things near the tent.)*
> — **Ігор:** А я піду шукати сухі дрова для вогню. *(And I will go look for dry firewood for the fire.)*

These location words are part of a larger system of spatial prepositions that use the Genitive case. Later, you will learn prepositions like **до** (to), **з** (from), and **від** (from, away from). The key difference is that **біля**, **навпроти**, and **коло** describe a static position—where something simply exists in space. Prepositions like **до**, on the other hand, will describe active direction or movement toward a destination.

<!-- INJECT_ACTIVITY: fill-in-location -->
<!-- INJECT_ACTIVITY: true-false-grammar -->


## Підсумок — Summary

In this module, we explored three common functions that require the Genitive case. First, we learned how to express purpose or an intended recipient using **для** (for). Next, we discussed how to describe the absence of something using **без** (without). Finally, we looked at how to define a location using the prepositions **біля** (near), **навпроти** (opposite), and **коло** (by). 

Remember that all of these prepositions always demand the Genitive case. The noun that follows them must change its ending according to its gender and stem.

«Читаємо українською»:
— Цей подарунок **для** мами. *(This gift is for mom.)*
— Я п'ю чай **без** цукру. *(I drink tea without sugar.)*
— Моя машина стоїть **навпроти** школи. *(My car stands opposite the school.)*
— Ми зустрінемося **біля** театру. *(We will meet near the theater.)*
— Кіт спить **коло** вікна. *(The cat sleeps by the window.)*

Before we finish, try this quick self-check:
1. Чи пам'ятаєте ви закінчення для чоловічого роду після «біля»? *(Do you remember the endings for masculine gender after "біля"?)*
2. Як сказати "coffee without sugar"? *(How to say "coffee without sugar"?)*
3. Який прийменник краще для "opposite"? *(Which preposition is better for "opposite"?)*

Keep practicing these small but important words, and soon the Genitive case will feel natural.

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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

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
