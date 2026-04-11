<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-adjectives-pronouns.yaml` file for module **19: Моєму другові, нашій вчительці** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-sort-dative-adjective-forms-by-gender-masculine-feminine-plural -->`
- `<!-- INJECT_ACTIVITY: quiz-pronoun-forms-choose-the-correct-dative-form-of-the-possessive-pronoun-vs-vs -->`
- `<!-- INJECT_ACTIVITY: match-up-nom-dat-match-nominative-noun-phrases-to-their-dative-equivalents -->`
- `<!-- INJECT_ACTIVITY: fill-in-dative-phrases -->`
- `<!-- INJECT_ACTIVITY: error-correction-agreement -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete dative noun phrases with the correct adjective/pronoun ending (мо___
    друг___)
  items: 8
  type: fill-in
- focus: Choose the correct dative form of the possessive pronoun (моєму vs. моїй
    vs. моїм)
  items: 8
  type: quiz
- focus: Match nominative noun phrases to their dative equivalents (мій друг → моєму
    другові)
  items: 8
  type: match-up
- focus: Sort dative adjective forms by gender (masculine -ому, feminine -ій, plural
    -им)
  items: 8
  type: group-sort
- focus: Find and fix adjective-pronoun agreement errors in dative phrases (e.g.,
    *моїй другові → моєму другові, *нашому вчительці → нашій вчительці)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- вказівний (demonstrative)
- узгодження (agreement (grammar))
- іменникова група (noun phrase)
- їхньому (to their (masc./neut. dat.))
required:
- моєму (to my (masc./neut. dat.))
- моїй (to my (fem. dat.))
- твоєму (to your (masc./neut. dat.))
- нашій (to our (fem. dat.))
- цьому (to this (masc./neut. dat.))
- тому (to that (masc./neut. dat.))
- новому (to the new (masc./neut. dat.))
- старшому (to the older (masc./neut. dat.))
- прикметник (adjective)
- присвійний (possessive)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Вступ та діалог (Introduction and Dialogue)

In previous lessons, we learned how to use the Dative case for nouns and personal pronouns. This case answers the question of who receives an action. Але що, якщо ми хочемо сказати більше? *(But what if we want to say more?)* 

Instead of just giving a gift to a friend, we often want to give it to our best friend or our new teacher. Whenever we add descriptive words to a noun in the Dative case, those words must also change their endings. To do this, we need our adjectives and possessive pronouns to match the noun perfectly. Let us see how this agreement works in a real classroom situation.

У класі вчитель віддає тести. *(In the classroom, the teacher is handing back tests.)* Студенти уважно слухають. *(The students listen carefully.)*

> — **Вчитель:** **Моєму найкращому студентові** — десятка! *(To my best student — a ten!)*
> — **Студенти:** Ого, вітаємо! *(Wow, congratulations!)*
> — **Вчитель:** **Нашій новій студентці** — дев'ятка. *(To our new student — a nine.)* Дуже добре! *(Very good!)*
> — **Нова студентка:** Дякую! *(Thank you!)* Мені дуже приємно. *(I am very pleased.)*
> — **Вчитель:** А **цьому хлопцю** треба більше працювати. *(And this boy needs to work more.)*
> — **Студент:** Я розумію. *(I understand.)* Дякую **нашому доброму вчителеві** за допомогу. *(Thank you to our kind teacher for the help.)*
> — **Вчитель:** Будь ласка. *(You are welcome.)* Завтра ми пишемо новий тест. *(Tomorrow we are writing a new test.)*

## Прикметники у давальному відмінку (Adjectives in the Dative Case)

When we add an adjective to a noun, they must work as a team. This grammatical teamwork is called agreement. This means the adjective must match the noun's gender, number, and case perfectly. If the noun is in the Dative case, the adjective must also take a Dative case ending. To find the right adjective form, we ask the question **«Якому?»** *(To which? / To what kind?)* for masculine and neuter nouns, **«Якій?»** *(To which?)* for feminine nouns, and **«Яким?»** *(To which?)* for plural nouns.

> — **Студент:** **Якому** студентові вчитель дає тест? *(To which student does the teacher give the test?)*
> — **Подруга:** Він дає тест розумному студентові. *(He gives the test to the smart student.)*
> — **Студент:** А **якій** вчительці ви даруєте квіти? *(And to which teacher are you giving flowers?)*
> — **Подруга:** Ми даруємо квіти нашій першій вчительці. *(We are giving flowers to our first teacher.)*

For masculine and neuter adjectives that have a hard stem (like **новий** - *new*, **старий** - *old*, **гарний** - *beautiful/good*), the adjective takes the ending **-ому**. Notice how the Nominative ending changes to match the Dative form. This is the most common adjective ending you will see for these genders.

*   новий друг → **новому** другу *(to a new friend)*
*   старе місто → **старому** місту *(to an old city)*
*   гарний будинок → **гарному** будинку *(to a beautiful house)*

«Читаємо українською»
Я часто допомагаю **моєму старому другові**. *(I often help my old friend.)*
Діти дуже радіють **старому місту**. *(The children are very happy about the old city.)*
Вони радіють **цьому гарному будинку**. *(They are happy about this beautiful house.)*

If the adjective has a soft stem (these usually end in **-ій** in the dictionary form, like **синій** - *blue*, **останній** - *last*, **вечірній** - *evening*), the masculine and neuter ending becomes **-ьому**. We use the soft sign **ь** to keep the pronunciation soft before the vowel **о**. The pattern is exactly the same as the hard group, just with an added soft sign.

*   синій колір → **синьому** кольору *(to the blue color)*
*   останній день → **останньому** дню *(to the last day)*
*   вечірній поїзд → **вечірньому** поїзду *(to the evening train)*

«Читаємо українською»
Студенти радіють **останньому дню** семестру. *(The students are happy about the last day of the semester.)*
Ми дуже радіємо **вечірньому поїзду** додому. *(We are very happy about the evening train home.)*
Художник додає темні тіні **синьому морю**. *(The artist adds dark shadows to the blue sea.)*

For feminine nouns, the rules are much simpler. Both hard and soft stem adjectives take the exact same ending: **-ій**. This makes it very easy to remember! Also, remember that after the letters **г**, **к**, and **х**, adjectives do not change their stem consonant in the Dative case, even though nouns often do.

*   нова подруга → **новій** подрузі *(to a new friend)*
*   синя сукня → **синій** сукні *(to a blue dress)*
*   довга дорога → **довгій** дорозі *(to a long road)*
*   тиха вулиця → **тихій** вулиці *(to a quiet street)*

«Читаємо українською»
Я купив гарний подарунок **новій подрузі**. *(I bought a beautiful present for a new friend.)*
Цей яскравий колір дуже пасує **синій сукні**. *(This bright color really suits the blue dress.)*
Ми завжди радіємо **тихій вулиці** біля нашого дому. *(We are always happy about the quiet street near our house.)*

In the plural, the adjective system becomes even simpler. All genders (masculine, feminine, and neuter) use the exact same ending pattern: **-им** for hard stems and **-ім** for soft stems.

*   нові друзі → **новим** друзям *(to new friends)*
*   сині моря → **синім** морям *(to blue seas)*
*   гарні дівчата → **гарним** дівчатам *(to beautiful girls)*

«Читаємо українською»
Новий вчитель пояснює граматичне правило **новим студентам**. *(The new teacher explains the grammar rule to the new students.)*
Літнє сонце дарує тепло **синім морям**. *(The summer sun gives heat to the blue seas.)*
Ми завжди допомагаємо **нашим гарним дівчатам**. *(We always help our beautiful girls.)*

When we compare the hard and soft groups in the Dative case, we see a beautiful consistency in the Ukrainian language. While Russian differentiates masculine hard and soft endings (ому/ему), Ukrainian unifies masculine and neuter endings with the rich "o" sound: **-ому** and **-ьому**. The only difference is the soft sign, which tells us how to pronounce the consonant before it. This makes the Ukrainian system logical, consistent, and uniquely melodic.

> — **Ганна:** **Якому** братові ти телефонуєш, старшому чи молодшому? *(Which brother are you calling, the older or the younger?)*
> — **Марко:** Я зараз телефоную **моєму молодшому братові**. *(I am calling my younger brother now.)*
> — **Ганна:** А що ти даруєш мамі на свято? *(And what are you giving to mom for the holiday?)*
> — **Марко:** Я дарую квіти **моїй рідній мамі**. *(I am giving flowers to my dear mom.)*

<!-- INJECT_ACTIVITY: group-sort-sort-dative-adjective-forms-by-gender-masculine-feminine-plural -->

## Присвійні та вказівні займенники у давальному відмінку (Possessive and Demonstrative Pronouns in the Dative)

Now that you know how to decline adjectives, possessive pronouns will be much easier to learn. The possessive pronouns for the first and second person singular (**мій** — *my*, **твій** — *your*, and the reflexive **свій** — *one's own*) change their stem slightly in the Dative case. The masculine and neuter forms take the ending **-єму** (мо**єму**, тво**єму**, сво**єму**), while the feminine forms take **-їй** (мо**їй**, тво**їй**, сво**їй**). The plural form for all genders is **-їм** (мо**їм**, тво**їм**, сво**їм**). Notice the appearance of the letters **є** and **ї** — they make the pronunciation smooth and melodic.

* мій батько → **моєму** батькові *(to my father)*
* твоя сестра → **твоїй** сестрі *(to your sister)*
* свої діти → **своїм** дітям *(to one's own children)*

«Читаємо українською»
Я зараз телефоную **моєму батькові**. *(I am calling my father now.)*
Допоможи **твоїй сестрі** зробити домашнє завдання. *(Help your sister do her homework.)*
Кожна людина бажає щастя **своїй родині**. *(Every person wishes happiness to their own family.)*
Ми завжди радіємо **моїм новим ідеям**. *(We are always happy about my new ideas.)*

The plural possessives **наш** *(our)* and **ваш** *(your, formal/plural)* are very straightforward. They decline exactly like hard group adjectives. For masculine and neuter nouns, use the ending **-ому** (наш**ому**, ваш**ому**). For feminine nouns, use **-ій** (наш**ій**, ваш**ій**). And for the plural, it is simply **-им** (наш**им**, ваш**им**).

* наш вчитель → **нашому** вчителю *(to our teacher)*
* ваша перемога → **вашій** перемозі *(to your victory)*
* наші друзі → **нашим** друзям *(to our friends)*

«Читаємо українською»
Студенти щиро дякують **нашому вчителю**. *(The students sincerely thank our teacher.)*
Ми дуже раді **вашій перемозі** на конкурсі. *(We are very glad about your victory in the competition.)*
Директор дає премію **нашим найкращим працівникам**. *(The director gives a bonus to our best workers.)*
Я довіряю **вашому досвіду**. *(I trust your experience.)*

The Ukrainian word for "their" is **їхній**. This is a fully declinable pronoun that behaves exactly like a soft group adjective. In the Dative case, it takes the ending **-ьому** for masculine/neuter (їхнь**ому**), **-ій** for feminine (їхн**ій**), and **-ім** for plural (їхн**ім**). You might sometimes hear people use the short, invariable form «їх» (the Genitive form of «вони») as a possessive, but in standard, natural Ukrainian, you should always decline **їхній**. This is a beautiful feature of our language!

* їхній сусід → **їхньому** сусідові *(to their neighbor)*
* їхня донька → **їхній** доньці *(to their daughter)*
* їхні проблеми → **їхнім** проблемам *(to their problems)*

«Читаємо українською»
Люди часто заздрять **їхньому багатому сусідові**. *(People often envy their rich neighbor.)*
Батьки купили нову іграшку **їхній маленькій доньці**. *(The parents bought a new toy for their little daughter.)*
Ми не можемо зарадити **їхнім проблемам**. *(We cannot help their problems.)*
Ця музика дуже подобається **їхнім дітям**. *(Their children really like this music.)*

Here is a very important rule: the possessive pronouns **його** *(his / its)* and **її** *(her)* **never change their form**. They are invariable, regardless of the case, gender, or number of the noun they describe. This is a common trap for English speakers! Do not try to add Dative endings to them. Just leave them as they are and decline the noun.

* його друг → **його** другу *(to his friend)*
* її сестра → **її** сестрі *(to her sister)*

«Читаємо українською»
Я повністю вірю **його другу**. *(I completely believe his friend.)*
Лікар дав ліки **її хворій сестрі**. *(The doctor gave medicine to her sick sister.)*
Ця машина належить **його братові**. *(This car belongs to his brother.)*
Ми щиро радіємо **її успіхам**. *(We are sincerely happy about her successes.)*

Finally, let's look at demonstrative pronouns: **цей** *(this)* and **той** *(that)*. They are crucial for pointing things out. **Цей** follows a soft-like pattern, while **той** has its own unique forms. For masculine/neuter, we use **цьому** *(to this)* and **тому** *(to that)*. For feminine, we use **цій** *(to this)* and **тій** *(to that)*. The plural forms are very short: **цим** *(to these)* and **тим** *(to those)*.

* цей будинок → **цьому** будинку *(to this house)*
* та дівчина → **тій** дівчині *(to that girl)*
* ці студенти → **цим** студентам *(to these students)*

«Читаємо українською»
Дай цю цікаву книгу **тому хлопцеві**. *(Give this interesting book to that boy.)*
**Цьому старому будинку** потрібен капітальний ремонт. *(This old house needs a major renovation.)*
Поясни нове правило **тій новій студентці**. *(Explain the new rule to that new student.)*
Я зовсім не вірю **цим новинам**. *(I do not believe these news at all.)*

> — **Олена:** Кому ти телефонуєш? *(Who are you calling?)*
> — **Тарас:** Я телефоную **моєму новому колезі**. *(I am calling my new colleague.)*
> — **Олена:** А що ти хочеш пояснити **цьому чоловікові**? *(And what do you want to explain to this man?)*
> — **Тарас:** Я маю надіслати важливі документи **його відділу**. *(I have to send important documents to his department.)*
> — **Олена:** Зрозуміло. Передай вітання **вашій команді**! *(Understood. Send greetings to your team!)*

<!-- INJECT_ACTIVITY: quiz-pronoun-forms-choose-the-correct-dative-form-of-the-possessive-pronoun-vs-vs -->
<!-- INJECT_ACTIVITY: match-up-nom-dat-match-nominative-noun-phrases-to-their-dative-equivalents -->

## Повні іменникові групи у давальному відмінку (Full Dative Noun Phrases)

Now that we know how to change both adjectives and pronouns, it is time to put everything together. In Ukrainian, a full noun phrase often consists of a possessive pronoun, an adjective, and a noun. When this entire phrase acts as the indirect object — the receiver of an action — every single word in the chain must change into the Dative case. This concept is called agreement. For example, if you want to say "to my older brother", you cannot just change the noun. You must change the pronoun **мій** *(my)* to **моєму**, the adjective **старший** *(older)* to **старшому**, and the noun **брат** *(brother)* to **братові**. The result is the beautiful, harmonious phrase: **моєму старшому братові** *(to my older brother)*.

«Читаємо українською»
Я допомагаю **моєму старшому братові**. *(I am helping my older brother.)*
Вони вірять **цьому новому лікарю**. *(They believe this new doctor.)*
Ми купили квіти **нашій улюбленій вчительці**. *(We bought flowers for our favorite teacher.)*
Передай привіт **твоїй молодшій сестрі**! *(Say hello to your younger sister!)*

The good news is that the word order remains completely stable. The sequence you learned in the Nominative case — Possessive Pronoun, then Adjective, then Noun — stays exactly the same in the Dative case. You do not need to learn a new sentence structure. You only need to apply the correct endings. This makes the transition from the basic dictionary form to the Dative case much easier. 

«Читаємо українською»
Номінатив: **мій найкращий друг** *(my best friend)*
Давальний: **моєму найкращому другові** *(to my best friend)*
Номінатив: **наша нова сусідка** *(our new neighbor)*
Давальний: **нашій новій сусідці** *(to our new neighbor)*

One of the most common situations for using these full phrases is when giving gifts or dedicating something to someone. Verbs like **дарувати** *(to gift)*, **купувати** *(to buy)*, and **присвятити** *(to dedicate)* naturally require the Dative case. When you buy a present for someone, you are directing your action toward them. 

«Читаємо українською»
Я хочу подарувати цю книгу **моєму найкращому другові**. *(I want to gift this book to my best friend.)*
Батько купив телефон **своєму молодшому синові**. *(The father bought a phone for his younger son.)*
Вона присвятила пісню **її коханому чоловікові**. *(She dedicated a song to her beloved husband.)*
Що ви купили **вашим маленьким дітям**? *(What did you buy for your little children?)*

Another frequent use case involves verbs of communication and assistance. When you call, write, or help someone, that person is the receiver of your action. Verbs like **телефонувати** *(to call)*, **писати** *(to write)*, and **допомагати** *(to help)* are your cues to use the Dative case for the entire noun phrase describing the person.

> — **Остап:** Кому ти пишеш повідомлення? *(Who are you writing a message to?)*
> — **Марта:** Я пишу **нашій новій вчительці**. *(I am writing to our new teacher.)*
> — **Остап:** А я телефоную **цьому старому майстру**. *(And I am calling this old repairman.)*
> — **Марта:** Він може допомогти **вашій великій родині**? *(Can he help your big family?)*
> — **Остап:** Так, він завжди допомагає **своїм постійним клієнтам**. *(Yes, he always helps his regular clients.)*

A very common trap for learners is to change the noun and the pronoun, but forget to change the adjective in the middle. For example, saying "моєму старий другу" is incorrect. In Ukrainian, every single word in the phrase must "signal" the Dative case. You cannot leave the adjective in its dictionary form. The endings **-ому** or **-ій** act like grammatical echoes, repeating the Dative signal across the whole phrase. Always check that your pronoun, adjective, and noun are wearing their matching Dative "uniforms."

«Читаємо українською»
❌ Я телефоную моєму старий друг.
✅ Я телефоную **моєму старому другові**. *(I am calling my old friend.)*
❌ Ми допомагаємо нашій нова сусідка.
✅ Ми допомагаємо **нашій новій сусідці**. *(We are helping our new neighbor.)*

<!-- INJECT_ACTIVITY: fill-in-dative-phrases -->
<!-- INJECT_ACTIVITY: error-correction-agreement -->

## Порівняння відмінків (Comparing Cases So Far)

It is very common to confuse the Genitive and Dative cases, especially for masculine and neuter words. The Genitive ending is **-ого**, while the Dative ending is **-ому**. The letter "м" in **-ому** is your unique marker for the Dative case. When you hear or write "м", you are usually directing an action to someone.

«Читаємо українською»
У мене немає **нового друга**. *(I do not have a new friend.)* [Родовий / Genitive]
Я телефоную **новому другові**. *(I am calling a new friend.)* [Давальний / Dative]
Вона не бачить **мого старшого брата**. *(She does not see my older brother.)* [Родовий / Genitive]
Вона купує каву **моєму старшому братові**. *(She is buying coffee for my older brother.)* [Давальний / Dative]

For feminine words, you must contrast the Genitive ending **-ої** with the Dative ending **-ій**. Notice that the Dative **-ій** is exactly identical to the Locative form you use with the prepositions **на** *(on)* or **в** *(in)*.

«Читаємо українською»
Тут немає **нашої нової вчительки**. *(Our new teacher is not here.)* [Родовий / Genitive]
Ми даруємо квіти **нашій новій вчительці**. *(We are gifting flowers to our new teacher.)* [Давальний / Dative]
Я не знаю **твоєї молодшої сестри**. *(I do not know your younger sister.)* [Родовий / Genitive]
Я допомагаю **твоїй молодшій сестрі**. *(I am helping your younger sister.)* [Давальний / Dative]

How do you know which case to choose? The verb or the preposition in your sentence is always the "driver." Prepositions like **для** *(for)* or **без** *(without)* always require the Genitive case. Verbs of giving, telling, and helping always require the Dative case. 

> — **Анна:** Це подарунок для **твого найкращого друга**? *(Is this a gift for your best friend?)*
> — **Марк:** Так, я завжди купую подарунки **моєму найкращому другові**. *(Yes, I always buy gifts for my best friend.)*
> — **Анна:** А що ти подаруєш **твоїй дівчині**? *(And what will you gift to your girlfriend?)*
> — **Марк:** Я ще не знаю. Я запитаю **її старшу сестру**. *(I do not know yet. I will ask her older sister.)*
> — **Анна:** Ти часто телефонуєш **її старшій сестрі**? *(Do you often call her older sister?)*
> — **Марк:** Так, ми дуже добре спілкуємося. *(Yes, we communicate very well.)*

Here is a quick reference for common verbs that require the Dative case for your noun phrases.

«Читаємо українською»
**Дієслова для давального відмінка** *(Verbs for the dative case)*
**давати / дати** *(to give)* → даю **цьому чоловікові** *(giving to this man)*
**дарувати / подарувати** *(to gift)* → дарую **моїй мамі** *(gifting to my mom)*
**телефонувати / зателефонувати** *(to call)* → телефоную **нашому лікарю** *(calling our doctor)*
**допомагати / допомогти** *(to help)* → допомагаю **старому сусідові** *(helping the old neighbor)*
**дякувати / подякувати** *(to thank)* → дякую **вашому синові** *(thanking your son)*

## Підсумок (Summary)

Let's review the key rules for adjectives and possessive pronouns in the Dative case. When you direct an action to someone, every word in the noun phrase must agree. 

For masculine and neuter words, your main ending is **-ому**. 
For feminine words, the ending is always **-ій**. 
For plural words, use the ending **-им** (or **-ім** for soft stems).

«Читаємо українською»
Я даю зошит **новому студенту**. *(I give a notebook to the new student.)*
Вона допомагає **старій сусідці**. *(She helps the old neighbor.)*

Possessive and demonstrative pronouns follow this exact pattern. **Мій** *(my)* becomes **моєму** or **моїй**. **Цей** *(this)* becomes **цьому** or **цій**. Remember that **його** *(his)* and **її** *(her)* are your best friends in Ukrainian grammar because they never change their form! 

> — **Анна:** Що ти подаруєш **твоєму новому колезі**? *(What will you gift to your new colleague?)*
> — **Марк:** Я куплю каву **цьому хлопцю**. *(I will buy coffee for this guy.)*
> — **Анна:** А я подарую квіти **нашій вчительці**. *(And I will gift flowers to our teacher.)*

Self-check time:
*   Can you say "to my sister"? (**моїй сестрі**)
*   Can you say "to this new student"? (**цьому новому студентові**)
*   Do you remember the ending for plural? (**-им**)

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-adjectives-pronouns
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

**Level: A2 (Module 19/60) — ELEMENTARY**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
