<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-dates-numbers.yaml` file for module **6: Скільки? Котра година? Яке число?** (a2).

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

- focus: What's the Date? (Drill)
  items: 8
  type: quiz
- focus: Counting Objects (1, 2-4, 5+ Rule)
  items: 8
  type: fill-in
- focus: Accusative to Genitive Negation
  items: 8
  type: match-up
- focus: Q&A about quantities and dates
  items: 8
  type: match-up


You MUST create activities that cover all these hints. **Respect the `placement` field:**
- Hints with `placement: inline` go in the `inline:` array. They MUST have an `id` matching one of the injection markers above (e.g., `comprehension-check` or `reading-check`). If the marker id doesn't match exactly, use the closest match.
- Hints with `placement: workbook` go in the `workbook:` array.
- If no `placement` field, use this rule: quiz and reading go inline (2-3 max), everything else goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- числівник (numeral)
- додаток (object (grammatical))
- правило (rule)
required:
- число (дата) (date)
- місяць (month)
- січень (січня) (January)
- лютий (лютого) (February)
- березень (березня) (March)
- квітень (квітня) (April)
- травень (травня) (May)
- червень (червня) (June)
- липень (липня) (July)
- серпень (серпня) (August)
- вересень (вересня) (September)
- жовтень (жовтня) (October)
- листопад (листопада) (November)
- грудень (грудня) (December)
- заперечення (negation)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Яке сьогодні число? Родовий з датами

To plan an event, book a ticket, or simply know what day it is, you need to understand how dates work in Ukrainian. When looking at a calendar, the most common question you will hear or ask is «Яке сьогодні число?» *(What is the date today?)*. The answer requires a specific grammatical structure combining two different forms.

In English, you might say "January first". In Ukrainian, the structure is always "The first of January". The formula is simple: **День** *(The day)* is an ordinal number in the Nominative Neuter form (ending in **-е**, like **перше**, **друге**). **Місяць** *(The month)* is a noun in the Genitive Singular case. Because the word **число** *(date/number)* is neuter, the day always agrees with it, even though we often drop the word **число** in the answer.

All months in Ukrainian are masculine. When answering «Яке число?», the month changes to the Genitive case. Most months drop the vowel **-е-** and take the ending **-я**.

* Січень — **перше січня** *(the first of January)*
* Лютий — **друге лютого** *(the second of February)* (Note: **Лютий** is an adjective, so it takes the adjective ending **-ого**)
* Березень — **третє березня** *(the third of March)*
* Квітень — **четверте квітня** *(the fourth of April)*
* Травень — **п'яте травня** *(the fifth of May)*
* Червень — **шосте червня** *(the sixth of June)*
* Липень — **сьоме липня** *(the seventh of July)*
* Вересень — **восьме вересня** *(the eighth of September)*
* Жовтень — **дев'яте жовтня** *(the ninth of October)*
* Грудень — **десяте грудня** *(the tenth of December)*

Only two months take the ending **-а**.

* Листопад — **одинадцяте листопада** *(the eleventh of November)*
* Серпень — **дванадцяте серпня** *(the twelfth of August)*

Let's practice with the words **сьогодні** *(today)* and **завтра** *(tomorrow)*. Remember, the day is neuter, and the month is in the Genitive.

> — **Олена:** Яке сьогодні число? *(What is the date today?)*
> — **Марко:** Сьогодні двадцять четверте серпня. Це День Незалежності! *(Today is the twenty-fourth of August. It's Independence Day!)*
> — **Олена:** А яке число буде завтра? *(And what date will it be tomorrow?)*
> — **Марко:** Завтра двадцять п'яте серпня. *(Tomorrow is the twenty-fifth of August.)*

### Читаємо українською (Reading Practice)

Сьогодні перше вересня. Це перший день осені. Завтра буде друге вересня. Моя сестра йде до школи. Сьогодні дуже теплий день. 
*(Today is the first of September. It is the first day of autumn. Tomorrow will be the second of September. My sister is going to school. Today is a very warm day.)*

When talking about dates in the past or future, we use the verbs **було** *(was)* and **буде** *(will be)*. Notice that these verbs are also in the neuter form, because they refer to the neuter word **число**. The ordinal number for the day remains in the Nominative Neuter, regardless of the verb tense. You do not need to change the day, only the verb.

> — **Анна:** Яке число було вчора? *(What date was yesterday?)*
> — **Іван:** Вчора було п'ятнадцяте жовтня. *(Yesterday was the fifteenth of October.)*
> — **Анна:** А яке число буде через тиждень? *(And what date will it be in a week?)*
> — **Іван:** Через тиждень буде двадцять друге жовтня. *(In a week it will be the twenty-second of October.)*

So far, we have answered the question "What is the date?". But what if you want to answer the question **Коли?** *(When?)*, for example, «Коли у тебе день народження?» *(When is your birthday?)*. For the "When?" question, both the day and the month take the Genitive case. 

«Мій день народження двадцятого січня» *(My birthday is on the twentieth of January)*. 
«Концерт буде п'ятого травня» *(The concert will be on the fifth of May)*. 

We will practice the "When?" format more later, but for now, focus on simply stating what the current date is.

<!-- INJECT_ACTIVITY: quiz, What's the Date? (Drill) -->


## Рахуємо предмети: правило '1, 2-4, 5+' (~850 words total)

> — **Адміністратор:** Добрий день! На скільки днів ви бронюєте номер? *(Good afternoon! For how many days are you booking the room?)*
> — **Гість:** Добрий день. На три дні, будь ласка. З п'ятого по восьме травня. *(Good afternoon. For three days, please. From the fifth to the eighth of May.)*
> — **Адміністратор:** Добре. Скільки вас? *(Good. How many of you are there?)*
> — **Гість:** П'ять осіб — два чоловіки і три жінки. *(Five people — two men and three women.)*
> — **Адміністратор:** Зрозуміла. Вам потрібні два номери чи один великий? *(Understood. Do you need two rooms or one large one?)*
> — **Гість:** Нам потрібні два номери. Один номер на двох, і один номер на трьох. *(We need two rooms. One room for two, and one room for three.)*
> — **Адміністратор:** Чудово. Це буде коштувати чотири тисячі гривень за ніч. *(Excellent. It will cost four thousand hryvnias per night.)*

In English, counting is simple: one day, two days, five days. The noun just takes a plural "s". In Ukrainian, counting objects is a bit more dynamic. Look closely at the dialogue above. We see «один номер» *(one room)*, «два номери» *(two rooms)*, and «чотири тисячі» *(four thousands)*. We also see «три дні» *(three days)*, «два чоловіки» *(two men)*, but then «п'ять осіб» *(five people)*. The form of the noun changes depending on the number that comes right before it. This is governed by a fundamental pattern in Ukrainian grammar known as the "1, 2-4, 5+" rule. Once you master this rule, you will be able to count anything accurately.

The first part of the rule is the easiest. When a quantity ends in the number **1**, the noun that follows it remains in the Nominative Singular. It does not matter how large the number is. If the last word of the number is **один**, **одна**, or **одне** *(one)*, the object acts as if there is only a single item. Remember that the number "one" must agree with the gender of the noun.

* **Один стіл** *(One table)*
* **Двадцять один стіл** *(Twenty-one tables)*
* **Одна книга** *(One book)*
* **Тридцять одна книга** *(Thirty-one books)*
* **Одне вікно** *(One window)*
* **Сорок одне вікно** *(Forty-one windows)*
* **Сто сорок один кілометр** *(One hundred forty-one kilometers)*

Notice that in English we say "twenty-one books" (plural), but in Ukrainian it is literally "twenty-one book" (singular).

The second part of the rule applies to numbers ending in **2**, **3**, or **4**. When a quantity ends with **два/дві** *(two)*, **три** *(three)*, or **чотири** *(four)*, the noun takes the Nominative Plural form. This feels very natural, as you are talking about multiple items. For masculine and feminine nouns, the Nominative Plural ending is usually **-и** or **-і**. For neuter nouns, it is usually **-а** or **-я**.

* **Два столи** *(Two tables)*
* **Тридцять два столи** *(Thirty-two tables)*
* **Три книги** *(Three books)*
* **Двадцять три книги** *(Twenty-three books)*
* **Чотири вікна** *(Four windows)*
* **Сорок чотири вікна** *(Forty-four windows)*
* **Двісті двадцять два кілометри** *(Two hundred twenty-two kilometers)*

Note that the number **2** has gender forms: **два** for masculine and neuter, and **дві** for feminine (**дві жінки** *(two women)*, **дві машини** *(two cars)*).

The final part of the rule is where Ukrainian differs significantly from English. For the numbers **5 through 20**, all the tens (**30**, **40**, **50**, etc.), hundreds (**100**, **200**, etc.), and any compound numbers ending in **5, 6, 7, 8, 9,** or **0**, the noun shifts into the Genitive Plural. Think of it as saying "a quantity *of* items". Five *of* tables. Ten *of* books. The Genitive Plural has several different endings depending on the gender and the shape of the word. Many feminine and neuter words get a "zero ending" (they lose their final vowel), while many masculine words take the ending **-ів** or **-ей**.

* **П'ять столів** *(Five tables)*
* **Десять книг** *(Ten books)*
* **Вісім вікон** *(Eight windows)*
* **Двадцять п'ять столів** *(Twenty-five tables)*
* **П'ятдесят книг** *(Fifty books)*
* **Сто вісім вікон** *(One hundred eight windows)*

Let's break down how to form the Genitive Plural for each gender, as it is the most complex part of counting.

Most masculine nouns that end in a hard consonant take the ending **-ів** in the Genitive Plural. If the noun ends in a soft consonant, it usually takes **-ів** (sometimes **-їв**) or **-ей**. Let's look at some common masculine words you will need to count frequently, like money and distances.

* **Один долар** *(One dollar)* -> **Два долари** *(Two dollars)* -> **П'ять доларів** *(Five dollars)*
* **Один кілометр** *(One kilometer)* -> **Чотири кілометри** *(Four kilometers)* -> **Десять кілометрів** *(Ten kilometers)*
* **Один місяць** *(One month)* -> **Три місяці** *(Three months)* -> **Шість місяців** *(Six months)*

Some very common masculine words take the ending **-ей** or change slightly.

* **Один день** *(One day)* -> **Два дні** *(Two days)* -> **П'ять днів** *(Five days)*
* **Один гість** *(One guest)* -> **Три гості** *(Three guests)* -> **Десять гостей** *(Ten guests)*
* **Один чоловік** *(One man)* -> **Два чоловіки** *(Two men)* -> **П'ять чоловіків** *(Five men)* 

Feminine nouns ending in **-а** or **-я** usually drop this final vowel in the Genitive Plural. This is called the "zero ending". This can sometimes make them look exactly like the masculine singular!

* **Одна сестра** *(One sister)* -> **Дві сестри** *(Two sisters)* -> **П'ять сестер** *(Five sisters)* (Notice the 'e' appears to make it easier to pronounce).
* **Одна машина** *(One car)* -> **Три машини** *(Three cars)* -> **Шість машин** *(Six cars)*
* **Одна гривня** *(One hryvnia)* -> **Чотири гривні** *(Four hryvnias)* -> **Десять гривень** *(Ten hryvnias)* (The 'я' drops, leaving a soft sign or 'е').

When dropping the final vowel creates a difficult cluster of consonants at the end of the word, Ukrainian often inserts an **-о-** or **-е-** to smooth the pronunciation.

* **Одна книжка** *(One book)* -> **Дві книжки** *(Two books)* -> **П'ять книжок** *(Five books)*
* **Одна ручка** *(One pen)* -> **Три ручки** *(Three pens)* -> **Вісім ручок** *(Eight pens)*
* **Одна дівчина** *(One girl)* -> **Дві дівчини** *(Two girls)* -> **П'ять дівчат** *(Five girls)* (This is a special plural stem).

Like feminine nouns, neuter nouns ending in **-о** or **-е** often drop their final vowel in the Genitive Plural, taking a zero ending.

* **Одне слово** *(One word)* -> **Два слова** *(Two words)* -> **П'ять слів** *(Five words)* (The 'о' changes to 'і' in a closed syllable, a common Ukrainian phonetic rule).
* **Одне місце** *(One place/seat)* -> **Три місця** *(Three places)* -> **Десять місць** *(Ten places)*
* **Одне озеро** *(One lake)* -> **Чотири озера** *(Four lakes)* -> **Шість озер** *(Six lakes)*

Neuter nouns ending in **-я** (often representing concepts or actions) usually take the ending **-нь**.

* **Одне завдання** *(One task)* -> **Два завдання** *(Two tasks)* -> **П'ять завдань** *(Five tasks)*
* **Одне питання** *(One question)* -> **Три питання** *(Three questions)* -> **Багато питань** *(Many questions)*

Here is a quick reference table for the 1-2-5 rule across all genders.

| Number Ending | Grammatical Case | Masculine | Feminine | Neuter |
| :--- | :--- | :--- | :--- | :--- |
| **1** (21, 31...) | Nominative Singular | один стіл | одна книга | одне вікно |
| **2, 3, 4** (22-24...) | Nominative Plural | два столи | дві книги | два вікна |
| **5, 6... 0** (5-20...) | Genitive Plural | п'ять столів | п'ять книг | п'ять вікон |

### Читаємо українською (Reading Practice)

В нашому місті є багато парків. *(In our city there are many parks.)* Ми маємо один великий парк у центрі. *(We have one large park in the center.)* Там є три озера і чотири фонтани. *(There are three lakes and four fountains there.)* Біля парку стоять два високі будинки. *(Near the park stand two tall buildings.)* У цих будинках живуть п'ять тисяч людей. *(Five thousand people live in these buildings.)* Я гуляю там двадцять один день кожного місяця. *(I walk there twenty-one days every month.)* Сьогодні я бачив там десять качок і п'ять лебедів. *(Today I saw ten ducks and five swans there.)*

<!-- INJECT_ACTIVITY: fill-in, Counting Objects (1, 2-4, 5+ Rule) -->


## Заперечення з прямим додатком (Negation with a Direct Object)

Let's review the direct object. When an action directly affects an object, we use the Accusative Case (**Знахідний відмінок**). You already know these basic endings well from our previous modules. Masculine inanimate and neuter nouns usually do not change their form from the dictionary word. Feminine nouns change their ending **-а** to **-у**, and **-я** to **-ю**.
* **Я читаю статтю.** *(I am reading an article.)*
* **Він п'є сік.** *(He is drinking juice.)*
* **Ми бачимо парк.** *(We see a park.)*
* **Вона купила книгу.** *(She bought a book.)*
This is the standard and correct way to express a positive, affirmative action where a subject does something directly to an object.

However, Ukrainian has a special, elegant grammatical tradition for negation. When you negate a verb using the particle **не** *(not)*, the direct object often shifts from the Accusative Case to the Genitive Case (**Родовий відмінок**). This is considered the standard literary form in the Ukrainian language. Instead of just negating the action itself, the language conceptually negates the very presence or involvement of the object. It says "there is an absence of this object regarding this action."
* **Я читаю статтю.** *(Accusative: I am reading the article.)*
* **Я не читаю статті.** *(Genitive: I am not reading the article.)*
* **Ми бачимо парк.** *(Accusative: We see the park.)*
* **Ми не бачимо парку.** *(Genitive: We do not see the park.)*

Why does this grammatical shift happen? The Genitive Case emphasizes the total absence of the object in the context of the action. If you use the Accusative in a negative sentence, it can sometimes weakly imply you didn't interact with a *specific* object, but maybe you interacted with another one. The Genitive makes the negation absolute: there was no interaction with *any* such object.
* **Я не купив машину.** *(Accusative: I didn't buy the specific car we talked about.)*
* **Я не купив машини.** *(Genitive: I didn't buy any car at all.)*
Furthermore, when dealing with abstract concepts, emotions, or ideas, using the Genitive Case in negation is almost mandatory for a natural flow.
* **Він не має рації.** *(He is not right / He has no reason.)*
* **Я не бачу сенсу.** *(I do not see the point.)*

Let's look at some common examples with masculine nouns. Remember that masculine nouns in the Genitive singular take either the **-а** or **-я** ending (usually for concrete physical objects, people, animals, and official documents) or the **-у** or **-ю** ending (usually for abstract concepts, feelings, materials, institutions, and some geographical places). When negating an action involving these nouns, you must apply these standard Genitive endings instead of keeping the word unchanged as you normally would in the Accusative Case. Notice how the direct object changes its form.
* **Він купив хліб.** *(He bought bread.)* -> **Він не купив хліба.** *(He didn't buy bread.)*
* **Я бачив фільм.** *(I saw a film.)* -> **Я не бачив фільму.** *(I didn't see a film.)*
* **Вона п'є чай.** *(She drinks tea.)* -> **Вона не п'є чаю.** *(She doesn't drink tea.)*
* **Ми маємо квиток.** *(We have a ticket.)* -> **Ми не маємо квитка.** *(We don't have a ticket.)*

Now, let's examine feminine nouns in negative constructions. Feminine nouns in the Genitive singular take the **-и** ending (if they end in a hard consonant followed by **-а** in the dictionary form) or the **-і** / **-ї** ending (if they end in a soft consonant followed by **-я**, or if they are a special soft-stem feminine noun ending in a consonant). Pay close attention to how the ending shifts when the negative particle **не** is introduced before the verb.
* **Вона знає відповідь.** *(She knows the answer.)* -> **Вона не знає відповіді.** *(She doesn't know the answer.)*
* **Я маю машину.** *(I have a car.)* -> **Я не маю машини.** *(I don't have a car.)*
* **Ми бачимо проблему.** *(We see a problem.)* -> **Ми не бачимо проблеми.** *(We don't see a problem.)*
* **Він читає книгу.** *(He is reading a book.)* -> **Він не читає книги.** *(He is not reading a book.)*

This rule perfectly connects with a crucial and very common word you already know very well: **немає** *(there is no / does not exist)*. The word **немає** is itself a profound expression of deep negation, and it *always* strictly requires the following noun to be in the Genitive Case. This reinforces the strong, deep-rooted grammatical bond between the overall concept of negation and the Genitive Case in the Ukrainian language. Whenever you need to state that something is missing, lacking, or entirely non-existent in a particular place, the Genitive is your only correct grammatical choice.
* **У мене зараз немає часу.** *(I have no time right now.)*
* **У місті немає метро.** *(There is no subway in the city.)*
* **На столі немає ручки.** *(There is no pen on the table.)*
* **У нас немає проблеми.** *(We have no problem.)*

As a nuance of modern spoken Ukrainian, you might sometimes hear native speakers keep the Accusative Case after **не** in very casual conversation (for example, saying «Я не бачив цю книгу» instead of the Genitive). However, consistently shifting to the Genitive Case («Я не бачив цієї книги») remains the hallmark of high-quality, educated, and truly natural Ukrainian speech. It shows a deep understanding of the language's internal logic.

### Читаємо українською (Reading Practice)
Ось типова розмова про плани та проблеми. *(Here is a typical conversation about plans and problems.)*

> — **Марія:** Привіт, Олександре! Ти вже читав мою статтю? *(Hi, Oleksandr! Have you already read my article?)*
> — **Олександр:** Привіт! Ні, я ще не читав твоєї статті. У мене сьогодні зовсім немає часу. *(Hi! No, I haven't read your article yet. I have absolutely no time today.)*
> — **Марія:** Шкода. А ти купив квитки на концерт? *(It's a pity. And did you buy the tickets for the concert?)*
> — **Олександр:** Ні, я не купив квитків. У касі вже немає вільних місць. *(No, I didn't buy the tickets. There are no free seats left at the box office.)*
> — **Марія:** Зрозуміло. Ти випадково не бачив мого телефону? *(Understood. Have you accidentally not seen my phone?)*
> — **Олександр:** Ні, я не бачив твого телефону. Може, він лежить на столі? *(No, I haven't seen your phone. Maybe it is lying on the table?)*
> — **Марія:** Ні, на столі телефону немає. Я не знаю, де він. *(No, the phone is not on the table. I don't know where it is.)*

<!-- INJECT_ACTIVITY: match-up, Accusative to Genitive Negation -->
<!-- INJECT_ACTIVITY: match-up, Q&A about quantities and dates -->


## Підсумок — Summary

У цьому модулі ми вивчили важливі правила граматики. *(In this module, we learned important grammar rules.)*

* **Дати (Dates):** Use an ordinal number in the neuter gender (Nominative Case) plus the month in the Genitive Case.
  * **Перше травня** *(First of May)*

* **Рахуємо предмети (Counting items):** The number dictates the noun's case.
  * **1 (один):** Nominative Singular. **Один квиток** *(One ticket)*.
  * **2, 3, 4:** Nominative Plural. **Три квитки** *(Three tickets)*.
  * **5+ (п'ять і більше):** Genitive Plural. **Шість квитків** *(Six tickets)*.

* **Заперечення (Negation):** When negating a verb, a direct object in the Accusative Case changes to the Genitive Case.
  * **Я пишу лист.** *(I am writing a letter.)* -> **Я не пишу листа.** *(I am not writing a letter.)*

### Перевірте себе (Self-check)

Спробуйте відповісти на ці запитання: *(Try to answer these questions:)*

1. Як сказати "October 14th" українською? *(How to say "October 14th" in Ukrainian?)*
2. Який відмінок ми вживаємо після чисел 2, 3, 4? *(Which case do we use after numbers 2, 3, 4?)*
3. Що стається з додатком у заперечному реченні? *(What happens to the object in a negative sentence?)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-dates-numbers
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

**Level: A2 (Module 6/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
