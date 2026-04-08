<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 5: У мене немає... (A2, A2.1 [Foundation and Aspect Introduction])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-005
level: A2
sequence: 5
slug: genitive-intro
version: '1.1'
title: У мене немає...
subtitle: Родовий відмінок для вираження відсутності та кількості
focus: grammar
pedagogy: PPP
phase: A2.1 [Foundation and Aspect Introduction]
word_target: 2000
objectives:
  - Learner can correctly use the Genitive singular after `немає` to express the
    absence of an object.
  - Learner can form the Genitive singular endings for all three noun genders 
    (-а/-я, -у/-ю, -и/-і).
  - Learner can use quantity words `багато`, `мало`, `кілька`, `декілька` with 
    the Genitive plural.
  - Learner can form the Genitive plural endings for all three noun genders 
    (-ів, -ей, нульове закінчення).
dialogue_situations:
  - setting: 'Moving into a new apartment — discovering what''s missing: Немає холодильника
      (m, fridge)! Немає плити (f, stove)! Немає дзеркала (n, mirror)! Є багато коробок
      (pl, boxes) але мало меблів (pl, furniture).'
    speakers:
      - Сусідка (neighbor)
      - Нова мешканка (new tenant)
    motivation: 'Genitive with немає: холодильник→холодильника, плита→плити, дзеркало→дзеркала'
content_outline:
  - section: 'Родовий відмінок: Коли чогось немає (The Genitive Case: When Something
      Isn''t There)'
    words: 600
    points:
      - Introducing the Genitive case (Родовий відмінок), answering 'Кого? 
        Чого?'.
      - 'Its first key function: expressing absence or non-existence with the construction
        `(У мене) немає + Genitive`.'
      - 'Contrast: ''У мене є брат'' (Nominative) vs. ''У мене немає брата'' (Genitive).'
      - 'Practice with simple sentences: ''Тут є стіл.'' -> ''Тут немає стола.'''
  - section: Закінчення родового відмінка однини (Genitive Singular Endings)
    words: 700
    points:
      - 'Masculine nouns: the -а/-я vs. -у/-ю puzzle. -а/-я for concrete, animate,
        specific items (стола, брата, комп''ютера). -у/-ю for abstract concepts, substances,
        locations (часу, цукру, Києву).'
      - 'Feminine nouns: -и for hard stems (книги, мами), -і for soft stems and stems
        in -я (землі, пісні).'
      - 'Neuter nouns: -а for stems in -о (вікна), -я for stems in -е (моря, сонця).'
      - Provide clear charts and practice drills for forming the Genitive 
        singular.
  - section: Коли є багато або мало (When There Is a Lot or a Little)
    words: 700
    points:
      - 'Introducing quantity words that require the Genitive plural: багато (a lot),
        мало (a little, few), кілька/декілька (a few, some), скільки (how many).'
      - 'Genitive Plural Endings: a tricky topic. Masculine: often -ів (столів, братів).
        Feminine/Neuter: often a zero ending, sometimes with a fleeting vowel (книг → книжок,
        сестер, вікон). A small group of masculine/neuter nouns takes -ей (гостей, коней, очей).'
      - 'Lots of examples: багато друзів, мало грошей, кілька книжок, скільки студентів?'
      - Focus on recognizing and using the most common forms, not memorizing 
        every exception.
vocabulary_hints:
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
  recommended:
    - кількість (quantity)
    - відсутність (absence)
    - гроші (money)
    - час (time)
activity_hints:
  - type: quiz
    focus: Possession vs. Absence Drill (`Є` vs. `Немає`)
    items: 8
  - type: fill-in
    focus: Genitive Singular Formation
    items: 8
  - type: match-up
    focus: Genitive Plural Formation with Quantity Words
    items: 8
  - type: match-up
    focus: Translate sentences with 'a lot of...' / 'I don't have...'
    items: 8
  - type: unjumble
    focus: Reorder words to form correct genitive phrases with немає and 
      quantity expressions
    items: 6
references:
  - title: "ULP: 10 Uses of Genitive Case"
    url: "https://www.ukrainianlessons.com/genitive-case/"
    notes: "All genitive functions explained"
  - title: "Заболотний Grade 6, §81"
    notes: "немає vs не має — key distinction with examples"

</plan_content>

## Generated Content

<generated_module_content>
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
</generated_module_content>

**PIPELINE NOTE — Word count: 3245 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 233 words | Not found: 6 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Крим — NOT IN VESUM
  ✗ Криму — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Олена — NOT IN VESUM

All 233 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
