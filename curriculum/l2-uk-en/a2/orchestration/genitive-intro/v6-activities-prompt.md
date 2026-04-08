<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-intro.yaml` file for module **5: У мене немає...** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-possession-vs-absence-drill-vs -->`
- `<!-- INJECT_ACTIVITY: fill-in-genitive-singular-formation -->`
- `<!-- INJECT_ACTIVITY: match-up-genitive-plural-quantity -->`
- `<!-- INJECT_ACTIVITY: match-up-translate-genitive -->`
- `<!-- INJECT_ACTIVITY: unjumble-genitive-phrases -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Possession vs. Absence Drill (`Є` vs. `Немає`)
  items: 8
  type: quiz
- focus: Genitive Singular Formation
  items: 8
  type: fill-in
- focus: Genitive Plural Formation with Quantity Words
  items: 8
  type: match-up
- focus: Translate sentences with 'a lot of...' / 'I don't have...'
  items: 8
  type: match-up
- focus: Reorder words to form correct genitive phrases with немає and quantity expressions
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- кількість (quantity)
- відсутність (absence)
- гроші (money)
- час (time)
required:
- родовий відмінок (genitive case)
- немає ((there) is not, (I) don't have)
- багато (a lot, many, much)
- мало (a little, few)
- кілька (a few, several)
- скільки (how many, how much)
- закінчення (ending (grammar))
- однина (singular)
- множина (plural)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Родовий відмінок: Коли чогось немає (The Genitive Case: When Something Isn't There)

Welcome to a new grammatical concept. So far, you have learned how to talk about things that exist and things that you have. But how do you talk about the things that are missing? In Ukrainian, when something is not there, we use a special form of the noun. This form is called the **родовий відмінок** (Genitive case). It is one of the most frequently used cases in the Ukrainian language. The Genitive case answers the questions **Кого?** (Whom?) and **Чого?** (What?). Historically, this case was used to show origin, like where a person is from, or to show possession, like who owns a specific item. While those functions are still very important today, the first and most practical way you will use the Genitive case is to express absence.

Let's look at the core construction for possession. You already know how to say «У мене є...» (I have...). When you use this positive phrase, the object you own remains in the **називний відмінок** (Nominative case), which is the basic dictionary form. For example, «У мене є брат» (I have a brother) or «У мене є сестра» (I have a sister). However, when you want to say that you do not have something, you must use the negative word **немає** ((there) is not / (I) don't have). This is where the rule applies: the word **немає** always forces the following noun to change into the Genitive case. So, the sentence becomes «У мене немає брата» (I don't have a brother) and «У мене немає сестри» (I don't have a sister).

Let's see this in action. Imagine a situation where someone is moving into a new apartment. A neighbor comes to visit and sees an empty kitchen.

> — **Сусідка:** Добрий день! Ви нова мешканка? *(Good day! Are you the new tenant?)*
> — **Нова мешканка:** Привіт! Так, це моя квартира. Але тут ще нічого немає. *(Hi! Yes, this is my apartment. But there is nothing here yet.)*
> — **Сусідка:** Ого. Тут немає холодильника! *(Wow. There is no fridge here!)*
> — **Нова мешканка:** Так, немає холодильника. І немає плити. *(Yes, there is no fridge. And there is no stove.)*
> — **Сусідка:** А де ваші речі? Тут немає дзеркала, немає стола... *(And where are your things? There is no mirror here, no table...)*
> — **Нова мешканка:** У мене є багато коробок. Але меблів ще немає. *(I have a lot of boxes. But there is no furniture yet.)*
> — **Сусідка:** Розумію. Бажаю удачі! *(I understand. I wish you luck!)*

If we look closely at this dialogue, we can see the Genitive case in action. The dictionary form for a fridge is **холодильник** (fridge, masculine). But because the neighbor says it is missing, she uses the word **немає**, and the noun changes to **холодильника**. The same thing happens with the feminine noun **плита** (stove), which changes to **плити**. The neuter noun **дзеркало** (mirror) changes to **дзеркала**. You can think of the word **немає** as a powerful grammatical magnet. Whenever it appears in a sentence, it pulls the object that is missing out of its basic dictionary form and forces it to take a new Genitive ending. Notice that the new tenant says she has **багато коробок** (a lot of boxes). The word **багато** (a lot, many, much) also requires the Genitive case.

To build a strong habit, it is helpful to practice contrasting positive and negative statements. Look at how the nouns change when we switch from existence to absence.

* **Тут є стіл.** *(There is a table here.)*
* **Тут немає стола.** *(There is no table here.)*
* **У мене є проблема.** *(I have a problem.)*
* **У мене немає проблеми.** *(I don't have a problem.)*
* **У нас є вікно.** *(We have a window.)*
* **У нас немає вікна.** *(We don't have a window.)*
* **В офісі є директор.** *(There is a director in the office.)*
* **В офісі немає директора.** *(There is no director in the office.)*
* **У тебе є вода?** *(Do you have water?)*
* **Ні, у мене немає води.** *(No, I don't have water.)*

In everyday casual speech, Ukrainians often shorten the word **немає** to simply **нема** (there is no). This short form means exactly the same thing and follows the exact same grammatical rule. It still acts as a magnet for the Genitive case. A very common example you will hear every day is «Часу нема» (There is no time), where **час** (time) becomes **часу**.

### Читаємо українською (Reading Practice)

**Моя нова кімната дуже велика.** *(My new room is very big.)*
**Але зараз вона порожня.** *(But right now it is empty.)*
**Тут є тільки одне ліжко.** *(There is only one bed here.)*
**У мене немає шафи.** *(I don't have a wardrobe.)*
**У мене немає телевізора.** *(I don't have a television.)*
**На вікні немає штори.** *(There is no curtain on the window.)*
**Я хочу працювати, але в кімнаті немає стола.** *(I want to work, but there is no table in the room.)*
**У мене є тільки багато планів.** *(I only have a lot of plans.)*
**Завтра я куплю меблі.** *(Tomorrow I will buy furniture.)*

<!-- INJECT_ACTIVITY: quiz-possession-vs-absence-drill-vs -->

To summarize this section, remember the golden rule of absence in Ukrainian. Whenever something is missing, whether it is a person, a physical object in a room, or an abstract concept like time, you must use the word **немає** (or **нема**). And whenever you use that word, the missing noun must take the Genitive case. In the next section, we will learn exactly how to form these endings for all noun genders.


## Закінчення родового відмінка однини (Genitive Singular Endings)

For masculine nouns, the Genitive singular presents an interesting challenge. Unlike feminine and neuter nouns, masculine nouns can take one of two different endings: **-а** (or the soft version **-я**) and **-у** (or the soft version **-ю**). The choice between these two endings depends entirely on the meaning of the word. The ending **-а** or **-я** is used for concrete, specific, and well-defined objects, as well as for living beings. If you can easily draw a picture of it, or if it is a specific person or animal, it takes this ending. This also includes specific units of measurement.
* **Тут немає мого брата.** *(My brother is not here.)*
* **У кімнаті немає стола.** *(There is no table in the room.)*
* **Сьогодні немає автобуса.** *(There is no bus today.)*
* **У мене немає одного метра.** *(I am missing one meter.)*
* **У нас немає кілограма яблук.** *(We don't have a kilogram of apples.)*

Notice how **брат** (brother), **стіл** (table), and **автобус** (bus) are all specific, physical things. They clearly take the **-а** ending.

The second ending for masculine nouns is **-у** or **-ю**. This ending is reserved for abstract concepts, substances, liquids, powders, and large geographic areas. These are things that are difficult to define with a clear physical boundary. This ending is very common in everyday speech, especially when talking about things you lack.
* **Вибачте, у мене немає часу.** *(Sorry, I don't have time.)*
* **У каві немає цукру.** *(There is no sugar in the coffee.)*
* **У нього немає досвіду.** *(He doesn't have experience.)*
* **У її голосі немає смутку.** *(There is no sadness in her voice.)*

Words like **час** (time), **цукор** (sugar), **досвід** (experience), and **смуток** (sadness) take the **-у** ending. An interesting contrast happens with places. A specific city like **Київ** (Kyiv) takes **-а**, becoming **Києва**. But a large, general region like **Крим** (Crimea) takes **-у**, becoming **Криму**.
* **Я зараз не біля Києва.** *(I am not near Kyiv right now.)*
* **Він ще не бачив Криму.** *(He hasn't seen Crimea yet.)*

Feminine nouns follow a much simpler rule. They split into two main endings: **-и** and **-і**. If the basic dictionary form ends in a hard consonant followed by **-а**, the Genitive ending is **-и**.
* **У мене немає книги.** *(I don't have a book.)*
* **Зараз немає мами.** *(Mom is not here right now.)*
* **Сьогодні немає роботи.** *(There is no work today.)*

If the word ends in **-я** or a soft consonant, it takes the **-і** ending.
* **Тут немає сухої землі.** *(There is no dry land here.)*
* **У плейлисті немає пісні.** *(There is no song in the playlist.)*
* **У селі немає вулиці.** *(There is no street in the village.)*

There is also a small group of feminine nouns that end in a consonant in their basic form, such as **ніч** (night) or **сіль** (salt). These also take the **-і** ending, becoming **ночі** and **солі**.
* **У мене немає солі.** *(I don't have salt.)*

Neuter nouns are the easiest of all. They simply replace their final vowel. If the basic form ends in **-о**, it changes to **-а**. If it ends in **-е** or **-я**, it changes to **-я**. Listen closely when you speak, as the change from **-о** to **-а** can be a subtle but important shift in sound.
* **Тут немає вікна.** *(There is no window here. — from **вікно**, window)*
* **У місті немає моря.** *(There is no sea in the city. — from **море**, sea)*
* **Без води немає життя.** *(Without water there is no life. — from **життя**, life)*
* **У мене немає слова.** *(I don't have a word. — from **слово**, word)*

To quickly remember these rules, it helps to build a simple mental chart and anchor it with common words. For masculine nouns, remember the concrete **телефон** (phone) which becomes **телефона**, and the abstract **час** (time) which becomes **часу**. For feminine nouns, remember the hard stem **кава** (coffee) which becomes **кави**, and the soft stem **вулиця** (street) which becomes **вулиці**. For neuter nouns, remember **слово** (word) which becomes **слова**.

Let's look at a short dialogue to see these endings in action.
> — **Анна:** Привіт! У тебе є кава? *(Hi! Do you have coffee?)*
> — **Марк:** Привіт! Ні, у мене немає кави. *(Hi! No, I don't have coffee.)*
> — **Анна:** А чай є? *(And is there tea?)*
> — **Марк:** Чаю теж немає. Немає води. *(There is no tea either. There is no water.)*
> — **Анна:** Це проблема. А магазину тут немає? *(That is a problem. And is there no store here?)*
> — **Марк:** Магазин є, але у мене немає часу. *(There is a store, but I have no time.)*

<!-- INJECT_ACTIVITY: fill-in-genitive-singular-formation -->

As you practice these endings, watch out for a few common pitfalls. First, be careful with the word **гроші** (money). In Ukrainian, this word is always plural. Even if you are talking about a small amount in a singular context in English, you cannot use singular Genitive endings for it; it will take a special plural form we will learn later. Second, remember that the word **немає** (there is no) is written as one single word. Do not confuse it with **не має** (he/she/it does not have), which is written as two separate words.
* **Тут немає стола.** *(There is no table here. — indicating absence)*
* **Він не має стола.** *(He does not have a table. — indicating lack of possession)*

Both require the Genitive case, but **немає** is the universal magnet for absence.

### Читаємо українською (Reading Practice)
**Сьогодні дуже поганий день.** *(Today is a very bad day.)*
**Я хочу працювати, але немає інтернету.** *(I want to work, but there is no internet.)*
**У мене немає комп'ютера, тільки телефон.** *(I don't have a computer, only a phone.)*
**На столі немає кави.** *(There is no coffee on the table.)*
**У кухні немає цукру.** *(There is no sugar in the kitchen.)*
**Я дивлюся у вікно, але там немає сонця.** *(I look out the window, but there is no sun there.)*
**На вулиці немає автобуса.** *(There is no bus on the street.)*
**У мене немає настрою працювати.** *(I have no mood to work.)*


## Коли є багато або мало (When There Is a Lot or a Little)

Now that you know how to say that one specific thing is missing, let's talk about quantities. When you want to express that you have "a lot of" or "a little of" something, Ukrainian uses the Genitive case, but in the plural form. Think of it as saying "a lot OF items." The most common quantity words are **багато** (a lot / many / much), **мало** (a little / few), and **кілька** or **декілька** (a few / several). Unlike English, which just uses the regular plural form ("many cars"), Ukrainian changes the ending of the noun to reflect this quantity. 

* **Тут багато людей.** *(There are a lot of people here.)*
* **У місті мало парків.** *(There are few parks in the city.)*
* **Він має декілька питань.** *(He has several questions.)*
* **На столі лежить кілька яблук.** *(There are a few apples lying on the table.)*

Forming the Genitive plural can seem tricky at first, so we will focus on the most important and common patterns. For most masculine nouns ending in a consonant, the dominant ending is **-ів** (or **-їв** after a vowel or soft sign). This is the easiest group to spot and use in daily conversation.

* **брат** (brother) -> **багато братів** *(many brothers)*
* **стіл** (table) -> **кілька столів** *(several tables)*
* **трамвай** (tram) -> **мало трамваїв** *(few trams)*
* **студент** (student) -> **багато студентів** *(many students)*
* **комп'ютер** (computer) -> **кілька комп'ютерів** *(several computers)*

One extremely high-frequency word has an irregular, but very important form. The word **друг** (friend) becomes **друзі** in the plural, and its Genitive plural form is **друзів**.

* **У мене дуже багато друзів.** *(I have very many friends.)*

Feminine and neuter nouns usually take a different approach. Instead of adding a new ending, they often lose their final vowel, resulting in what we call a "zero ending" (**нульове закінчення**). 

* **машина** (car) -> **багато машин** *(many cars)*
* **справа** (matter / business) -> **багато справ** *(many matters)*
* **місце** (place) -> **мало місць** *(few places)*

However, Ukrainian language does not like having too many consonants crowded together at the end of a word. When dropping the vowel leaves a difficult cluster of letters, a "fleeting vowel" (**о** or **е**) magically appears between the consonants to make pronunciation smooth and melodic.

* **книжка** (book) -> **кілька книжок** *(a few books)*
* **сестра** (sister) -> **багато сестер** *(many sisters)*
* **вікно** (window) -> **мало вікон** *(few windows)*
* **пісня** (song) -> **багато пісень** *(many songs)*

Finally, there is a small but essential group of nouns across all genders that take the ending **-ей** in the Genitive plural. You simply need to memorize the most common ones, as they are everyday survival words. The most critical word in this group is **гроші** (money). In Ukrainian, money is always grammatically plural, and after words like **багато** or **мало**, you must always use the form **грошей**.

* **гроші** (money) -> **багато грошей** *(a lot of money)*
* **очі** (eyes) -> **кілька очей** *(a few eyes)*
* **речі** (things) -> **багато речей** *(many things)*
* **ночі** (nights) -> **кілька ночей** *(several nights)*
* **гості** (guests) -> **багато гостей** *(many guests)*

<!-- INJECT_ACTIVITY: match-up-genitive-plural-quantity -->

To ask "How many?" or "How much?", use the question word **Скільки**. Naturally, the noun following **Скільки** must also be in the Genitive case. When you ask about countable objects, use the Genitive plural.

* **Скільки у тебе книжок?** *(How many books do you have?)*
* **Скільки коштує квиток? У мене мало грошей.** *(How much does a ticket cost? I have little money.)*
* **Скільки студентів тут живе?** *(How many students live here?)*

Let's see these quantity phrases in a short conversation.

> — **Марко:** Привіт! Скільки у тебе вільного часу сьогодні? *(Hi! How much free time do you have today?)*
> — **Олена:** Привіт! У мене зовсім немає часу. Є багато справ. *(Hi! I have absolutely no time. There are many matters.)*
> — **Марко:** Шкода. А завтра? У мене є кілька квитків у кіно. *(A pity. And tomorrow? I have a few tickets to the cinema.)*
> — **Олена:** Завтра я вільна. Скільки друзів іде з нами? *(Tomorrow I am free. How many friends are going with us?)*
> — **Марко:** Тільки ми. У інших багато роботи. *(Only us. The others have a lot of work.)*

<!-- INJECT_ACTIVITY: match-up-translate-genitive -->

<!-- INJECT_ACTIVITY: unjumble-genitive-phrases -->

When learning the Genitive case, English speakers often make the mistake of using the Nominative case after **немає** or quantity words, saying «У мене немає машина» instead of the correct «У мене немає машини». Remember that the Ukrainian **немає** is a unique grammatical marker of non-existence, not just a direct translation of the English word "no". It acts as a magnet that demands the Genitive case for the object that is missing. 

Furthermore, do not try to guess Ukrainian endings based on patterns from other languages. The masculine Genitive singular endings **-а** and **-у** have their own specific rules in Ukrainian. For example, abstract nouns often take **-у** (like **часу** for time or **настрою** for mood), while concrete objects usually take **-а** (like **стола** for table). Embrace the Ukrainian logic independently to build a strong foundation and sound truly natural.

### Читаємо українською (Reading Practice)

**У нашому місті є багато проблем.** *(In our city there are many problems.)*
**Тут мало дерев і зовсім немає великих парків.** *(There are few trees here and absolutely no large parks.)*
**На вулицях завжди багато машин і багато людей.** *(There are always many cars and many people on the streets.)*
**Але у нас є кілька хороших музеїв і театрів.** *(But we have a few good museums and theaters.)*
**Скільки грошей треба на квиток?** *(How much money is needed for a ticket?)*
**Квиток коштує мало, але у студентів часто немає грошей.** *(The ticket costs little, but students often have no money.)*
**У мене є кілька друзів у цьому місті.** *(I have a few friends in this city.)*
**Ми маємо мало часу, але багато нових ідей.** *(We have little time, but many new ideas.)*


## Підсумок — Summary

Let's review the three golden rules we have learned in this module:

1. **Negation requires the Genitive:** The word **немає** *(there is not / have not)* always acts as a magnet for the Genitive case.
   * **У мене немає машини.** *(I don't have a car.)*
2. **Quantity requires the Genitive plural:** Words like **багато** *(many/much)*, **мало** *(few/little)*, and **кілька** *(several)* must be followed by the Genitive plural when counting objects.
   * **Тут є багато людей і мало дерев.** *(There are many people and few trees here.)*
3. **Endings depend on gender and stems:** The correct ending relies on whether the noun is masculine, feminine, or neuter, and if its stem is hard or soft.

**Самоперевірка** *(Self-check)*:
* Do you use **-а** / **-я** for concrete masculine objects? (**немає стола** *(there is no table)*, **немає брата** *(there is no brother)*)
* Do you use **-у** / **-ю** for abstract masculine concepts? (**немає часу** *(there is no time)*, **немає цукру** *(there is no sugar)*)
* Do you remember the fleeing vowel in feminine plurals? (**книжка** *(book)* → **кілька книжок** *(several books)*)
* Can you correctly say you don't have money? (**У мене немає грошей.** *(I have no money.)*)

### Читаємо українською (Reading Practice)
**Сьогодні у мене немає вільного часу.** *(Today I have no free time.)*
**Я маю багато роботи і кілька нових завдань.** *(I have a lot of work and several new tasks.)*
**На вулиці немає дощу, але також немає сонця.** *(There is no rain outside, but there is also no sun.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-intro
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

**Level: A2 (Module 5/60) — ELEMENTARY**

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
