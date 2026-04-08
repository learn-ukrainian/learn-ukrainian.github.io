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

- `<!-- INJECT_ACTIVITY: quiz-what-s-the-date-drill -->`
- `<!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->`
- `<!-- INJECT_ACTIVITY: match-up-q-a-about-quantities-and-dates -->`
- `<!-- INJECT_ACTIVITY: match-up-accusative-to-genitive-negation -->`

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


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

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
## Яке сьогодні число? Котра година?

When you want to know the current date in Ukrainian, you ask: «Яке сьогодні число?» (What is today's date?). The word «число» literally means "number," but in this context, it translates to "date." If you want to know *when* a specific event happens, you ask: «Коли?» (When?) or «Якого числа?» (On what date?).

Here are a few quick examples of asking and answering about today's date:
* «Яке сьогодні число?» — «Сьогодні десяте березня.» (What is the date today? — Today is the tenth of March.)
* «Яке завтра число?» — «Завтра одинадцяте березня.» (What is the date tomorrow? — Tomorrow is the eleventh of March.)
* «Яке вчора було число?» — «Вчора було дев'яте березня.» (What was the date yesterday? — Yesterday was the ninth of March.)

Let's look closer at the formula for stating the date. In English, you might simply say "January first." In Ukrainian, you use a specific grammatical structure. The day is expressed as an ordinal numeral (first, second, third) in the neuter nominative case, because it agrees with the implied neuter word «число». The month that follows must be in the Genitive singular case, acting like the English "of January."

So, the formula is: **Ordinal Numeral (Neuter) + Month (Genitive)**.

Look at these examples:
* «перше січня» (the first of January)
* «друге лютого» (the second of February)
* «двадцять четверте серпня» (the twenty-fourth of August)
* «Сьогодні п'яте травня.» (Today is the fifth of May.)
* «Завтра шосте листопада.» (Tomorrow is the sixth of November.)

To master dates, you need to know the twelve months and their Genitive forms. All Ukrainian month names are masculine. Most of them take the standard Genitive ending «-я» or «-а». A very important spelling rule to remember is that many months have a mobile vowel «-е-» that disappears when you add the Genitive ending. For example, «січень» (January) becomes «січня» (of January).

Here is the complete list of months and their Genitive forms used for dates:
* «січень» (January) — «січня» (Mobile «-е-» drops out)
* «лютий» (February) — «лютого» (This month is an adjective, so it takes an adjectival ending)
* «березень» (March) — «березня» (Mobile «-е-» drops out)
* «квітень» (April) — «квітня» (Mobile «-е-» drops out)
* «травень» (May) — «травня» (Mobile «-е-» drops out)
* «червень» (June) — «червня» (Mobile «-е-» drops out)
* «липень» (July) — «липня» (Mobile «-е-» drops out)
* «серпень» (August) — «серпня» (Mobile «-е-» drops out)
* «вересень» (September) — «вересня» (Mobile «-е-» drops out)
* «жовтень» (October) — «жовтня» (Mobile «-е-» drops out)
* «листопад» (November) — «листопада» (Takes the «-а» ending)
* «грудень» (December) — «грудня» (Mobile «-е-» drops out)

Now, let's talk about time. To ask "What time is it?", use the phrase: «Котра година?». To ask "At what time?" an event happens, use: «О котрій годині?».

In Ukrainian, we use ordinal numerals (first, second, third) to name the hour. Because the word «година» (hour) is feminine, the numeral must also be feminine.
* «Зараз друга година.» (It is two o'clock now. — *Literally: It is the second hour.*)
* «Зараз п'ята година.» (It is five o'clock now.)

To say "half past," we use the construction «пів на» (half to) followed by the *next* hour in the accusative case.
* «пів на другу» (half past one — *Literally: half to the second*)
* «пів на шосту» (half past five)

To answer «О котрій годині?» (At what time?), use the preposition «о» (or «об» before a vowel) and the locative case.
* «Зустріч о дев'ятій.» (The meeting is at nine.)
* «Кіно об одинадцятій.» (The movie is at eleven.)

Let's see how these phrases work in a real-life situation. In this dialogue, a client is calling a beauty salon to book an appointment. Notice the contrast between stating today's date and booking for a specific time.

> — **Клієнтка:** Добрий день! Підкажіть, будь ласка, яке сьогодні число? *(Good day! Could you tell me, please, what is the date today?)*
> — **Адміністраторка:** Добрий день! Сьогодні п'яте травня. *(Good day! Today is the fifth of May.)*
> — **Клієнтка:** Дякую. Я хочу записатися на манікюр на шосте травня. *(Thank you. I want to book an appointment for a manicure for the sixth of May.)*
> — **Адміністраторка:** Добре, о котрій годині вам зручно? *(Good, at what time is it convenient for you?)*
> — **Клієнтка:** Об одинадцятій годині, якщо можна. *(At eleven o'clock, if possible.)*
> — **Адміністраторка:** Так, одинадцята година вільна. Чекаємо на вас! *(Yes, eleven o'clock is free. We are waiting for you!)*

<!-- INJECT_ACTIVITY: quiz-what-s-the-date-drill -->


## Рахуємо предмети: правило «1, 2-4, 5+» (Counting Items: The "1, 2-4, 5+" Rule)

When you want to count objects in Ukrainian, the number you use dictates the grammatical form of the noun that follows it. Unlike English, where you simply use the singular form for "one" and the plural form for everything else, Ukrainian counting is divided into three distinct grammatical tiers. The numeral is the absolute boss in these phrases; it tells the noun whether it should be singular or plural, and exactly which case it must take. We call this the "1, 2-4, 5+" rule. To understand this hierarchy clearly, we will use the masculine word «стіл» (table) as our core example. Depending on how many tables you actually have, the word will change its form to perfectly match the specific tier of the number.

### Рівень 1: Правило одиниці (Tier 1: The "1" Rule)

The first tier is the simplest and applies to the number 1, as well as any compound number that ends in 1, such as 21, 31, or 101 (but excluding 11, which falls into a different category). For this tier, the noun remains in the Nominative singular case, just as you would find it in a dictionary. However, the number "one" in Ukrainian behaves exactly like an adjective, meaning it must agree with the gender of the noun it describes. You must choose between «один» for masculine nouns, «одна» for feminine nouns, and «одне» for neuter nouns. Even when you are counting a very large quantity like 101, if the number ends in the digit 1, the noun stays strictly singular.

* «У кімнаті стоїть один стіл.» (One table stands in the room.)
* «На столі лежить одна книга.» (One book lies on the table.)
* «Тут є тільки одне вікно.» (There is only one window here.)
* «Це мій двадцять один рік.» (This is my twenty-one year. / *Meaning: I am 21 years old.*)
* «У цьому будинку сто один номер.» (There is one hundred and one room in this building.)

### Рівень 2: Правило двох, трьох і чотирьох (Tier 2: The "2, 3, 4" Rule)

The second tier applies to the numbers 2, 3, and 4. When you use these numbers, the noun must be placed in the Nominative plural case. This is where Ukrainian starts to differ significantly from English logic. In English, saying "two tables" just uses the standard plural form without any special rules. In Ukrainian, the specific numbers "two," "three," and "four" trigger the Nominative plural form. For masculine and feminine nouns, this usually means adding an «-и» or «-і» ending to the root word. Remember that the number 2 also has gender agreement: «два» is used for masculine and neuter nouns, while the special form «дві» is used exclusively for feminine nouns.

* «У кабінеті стоять два столи.» (Two tables stand in the office.)
* «Я купив три книги.» (I bought three books.)
* «У цій кімнаті є чотири вікна.» (There are four windows in this room.)
* «На столі лежать два телефони.» (Two phones lie on the table.)
* «Ми маємо дві машини.» (We have two cars.)

### Рівень 3: Правило п'яти і більше (Tier 3: The "5-20" Rule)

The third tier is often the most challenging for language learners. It applies to numbers 5 through 20. When counting from 5 upwards, the noun drops into the Genitive plural case. This is the biggest mental shift you need to make when speaking Ukrainian. Historically, numbers from five and above functioned as nouns themselves, meaning "a five of tables," which is why they require the Genitive case to show relation. For masculine nouns, the Genitive plural often ends in «-ів». For feminine nouns, it usually has a zero ending, meaning the final vowel simply disappears. For neuter nouns, it can have a zero ending or «-ів». Notice the stark contrast between counting just one item and counting five.

* «У нас є п'ять столів.» (We have five tables.)
* «Я прочитав шість книг.» (I read six books.)
* «У будинку сім вікон.» (There are seven windows in the building.)
* «Там працює десять людей.» (Ten people work there.)
* «Це коштує двадцять гривень.» (This costs twenty hryvnias.)

### Складені числівники (Compound Numbers)

When you are dealing with compound numbers like 22, 35, or 144, the grammar rule always follows the *last* word in the numeral. You ignore the tens, hundreds, or thousands and only look at the final digit. If the number ends in 2, 3, or 4, you use the Nominative plural. If it ends in 5, 6, 7, 8, 9, or 0, you use the Genitive plural. If it ends in 1 (except 11), you use the Nominative singular. Let's look at how this works in practice when counting hotel rooms (the word «номер» is masculine).

* «Наш готель має двадцять один номер.» (Our hotel has twenty-one rooms.)
* «На поверсі є двадцять два номери.» (There are twenty-two rooms on the floor.)
* «Ми забронювали двадцять п'ять номерів.» (We booked twenty-five rooms.)
* «Там працюють тридцять три людини.» (Thirty-three people work there.)
* «Вони мають сорок вісім машин.» (They have forty-eight cars.)

### Фокус на іменниках жіночого роду (Focus on Feminine Nouns)

Feminine nouns require some special attention because their Nominative plural form (which is used with the numbers 2, 3, and 4) can look completely identical to their Genitive singular form. For example, the word «сестра» (sister) becomes «сестри» in both of these cases. However, their underlying grammatical function in the sentence is different. When you say «дві сестри», you are using the Nominative plural specifically for counting. Sometimes, the stress shifts to distinguish the two forms, but the spelling remains exactly the same. The key is to remember the consistent pattern: «дві» plus the Nominative plural ending «-и» or «-і».

* «Одна сестра живе тут, а дві сестри живуть там.» (One sister lives here, and two sisters live there.)
* «Я маю одну книгу, а він має три книги.» (I have one book, and he has three books.)
* «Одна машина червона, а чотири машини чорні.» (One car is red, and four cars are black.)
* «На столі лежить одна ручка і дві лінійки.» (One pen and two rulers lie on the table.)
* «У мене є дві проблеми.» (I have two problems.)

### Діалог: На рецепції готелю (Dialogue: At the Hotel Reception)

Let's see how these rules work in a practical situation. Pay close attention to how the receptionist and the guest use different forms of the words «номер» (room) and «гість» (guest) depending on the numbers they use.

> — **Адміністратор:** Добрий день! Чим я можу вам допомогти? *(Good day! How can I help you?)*
> — **Гість:** Добрий день! Мені потрібно три номери. *(Good day! I need three rooms.)*
> — **Адміністратор:** Добре. На скільки людей? *(Good. For how many people?)*
> — **Гість:** На п'ять гостей. *(For five guests.)*
> — **Адміністратор:** У нас є два великих номери і один малий номер. *(We have two large rooms and one small room.)*
> — **Гість:** Чудово. Скільки це коштує? *(Great. How much does this cost?)*
> — **Адміністратор:** Це коштує дві тисячі гривень за добу. *(This costs two thousand hryvnias per day.)*
> — **Гість:** Дякую, я беру ці три номери. *(Thank you, I will take these three rooms.)*

### Читаємо українською (Reading Practice)

«У нашому офісі є один великий кабінет. Там працюють три менеджери. Вони мають три столи і шість стільців. На столі лежить один комп'ютер. У шафі стоять десять папок. Ми купили двадцять один новий маркер. Також ми маємо два принтери. Це дуже зручно для роботи.»
*(In our office there is one large office. Three managers work there. They have three tables and six chairs. One computer lies on the table. Ten folders stand in the cabinet. We bought twenty-one new markers. Also we have two printers. This is very convenient for work.)*

<!-- INJECT_ACTIVITY: fill-in-counting-objects-1-2-4-5-rule -->
<!-- INJECT_ACTIVITY: match-up-q-a-about-quantities-and-dates -->


## Заперечення з прямим додатком (Negation with a Direct Object)

When you build a positive sentence in Ukrainian, the object that receives the action usually takes the Accusative case (Знахідний відмінок). For example, if you have a ticket, you use the Accusative form for the word "ticket". However, when you turn that exact same sentence into a negative one by adding the word «не» (not), a fascinating shift happens in Slavic languages. The direct object often drops the Accusative case and takes the Genitive case (Родовий відмінок) instead. This grammatical transformation is a hallmark of Ukrainian syntax. It signals that the action did not happen, and therefore, the object itself is completely uninvolved or absent from the situation.
* «Я маю квиток.» (I have a ticket. — Accusative)
* «Я не маю квитка.» (I do not have a ticket. — Genitive)
* «Він знає цю пісню.» (He knows this song. — Accusative)
* «Він не знає цієї пісні.» (He does not know this song. — Genitive)

You might hear Ukrainians using the Accusative case after negation in modern, casual speech. It is not strictly forbidden, but using the Genitive case is the grammatical standard and carries a specific nuance of emphasis. Using the Genitive creates a sense of total negation. It changes the meaning from "I didn't read *the* specific book" to "I didn't read *a single* book" or "I haven't been reading at all". When you want to sound natural and emphasize that an action absolutely did not occur regarding an object, the Genitive is your best choice. Let's compare the feeling of these two sentences:
* «Я не читав книгу.» (I didn't read the book. — Accusative. Perhaps I read a magazine instead, or I will read the book later.)
* «Я не читав книги.» (I didn't read any book. — Genitive. I was not engaged in the action of reading books at all.)
* «Вона не п'є каву.» (She is not drinking the coffee. — Accusative)
* «Вона не п'є кави.» (She doesn't drink coffee at all. — Genitive)

Let's look at how this transformation works in practice with common masculine and feminine nouns. For masculine nouns ending in a consonant, the Genitive singular ending is usually «-а» or «-у». For feminine nouns ending in «-а» or «-я», the Genitive singular ending is «-и» or «-і». Pay attention to how the ending changes the moment the word «не» appears before the verb.
* «Я купую свіжий хліб.» (I am buying fresh bread.)
* «Я не купую свіжого хліба.» (I am not buying fresh bread.)
* «Він бачить нову машину.» (He sees a new car.)
* «Він не бачить нової машини.» (He does not see a new car.)
* «Ми розуміємо це правило.» (We understand this rule.)
* «Ми не розуміємо цього правила.» (We do not understand this rule.)
* «Вона пише довгий лист.» (She is writing a long letter.)
* «Вона не пише довгого листа.» (She is not writing a long letter.)
* «Я їм смачну піцу.» (I am eating a tasty pizza.)
* «Я не їм смачної піци.» (I am not eating a tasty pizza.)

There is a special word in Ukrainian that absolutely always triggers the Genitive case: **немає** (there is no / is not present). Do not confuse «немає» with the verb phrase «не маю» (I do not have). «Не маю» is a regular negated verb (я маю -> я не маю) where you are the subject. «Немає» is an impersonal word denoting total absence, and the thing that is absent must be in the Genitive.
* «Тут немає кави.» (There is no coffee here. — Absence)
* «Я не маю кави.» (I do not have coffee. — Possession negated)
* «У кімнаті немає стола.» (There is no table in the room.)
* «Сьогодні немає дощу.» (There is no rain today.)
* «У нас немає проблем.» (We have no problems.)

The rule of Genitive negation is especially strong when we talk about abstract concepts. Words like **час** (time), **гроші** (money), or **допомога** (help) almost always take the Genitive case in negative sentences. With abstract nouns, the idea of "total negation" makes the most sense. You either have time, or you have no time at all.
* «Я не маю часу.» (I do not have time.)
* «У мене немає грошей.» (I have no money.)
* «Він не потребує допомоги.» (He does not need help.)
* «Вона не каже правди.» (She is not telling the truth.)
* «Ми не бачимо різниці.» (We do not see a difference.)

### Діалог: У магазині (Dialogue: In the Store)
Let's see how these negative forms are used in a typical conversation at a grocery store. Notice how the Genitive case naturally follows verbs with «не» and the word «немає».

> — **Покупець:** Добрий день! Чи є у вас свіжий хліб? *(Good day! Do you have fresh bread?)*
> — **Продавець:** Добрий день! Ні, на жаль, сьогодні немає хліба. *(Good day! No, unfortunately, there is no bread today.)*
> — **Покупець:** Зрозуміло. А молоко є? *(I understand. And milk?)*
> — **Продавець:** Я не бачу молока на полиці. Напевно, вже продали. *(I do not see milk on the shelf. Probably, they already sold it.)*
> — **Покупець:** Шкода. Тоді дайте, будь ласка, сік. *(It's a pity. Then give me juice, please.)*
> — **Продавець:** Вибачте, але я не маю соку. Є тільки вода. *(Sorry, but I do not have juice. There is only water.)*
> — **Покупець:** Добре, я беру воду. Я не маю часу шукати інший магазин. *(Good, I will take water. I do not have time to look for another store.)*

### Читаємо українською (Reading Practice)
«Мій друг Максим сьогодні дуже сумний. Він каже: "Я не маю настрою. Я не маю енергії працювати". Я питаю його: "Ти не хочеш кави?". Він відповідає: "Ні, я не п'ю кави вранці. І я не маю часу на відпочинок. У мене багато роботи, але я не бачу результату". Я хочу допомогти йому. Я кажу: "Максиме, у тебе немає проблем. Тобі просто треба поспати. Коли людина не має сну, вона не бачить позитиву". Максим слухає мене, але не каже ні слова. Він тільки зітхає. Я розумію, що зараз він не потребує моїх порад.»
*(My friend Maksym is very sad today. He says: "I have no mood. I have no energy to work." I ask him: "Do you not want coffee?". He answers: "No, I do not drink coffee in the morning. And I do not have time for rest. I have a lot of work, but I do not see a result." I want to help him. I say: "Maksym, you have no problems. You just need to sleep. When a person has no sleep, they do not see positivity." Maksym listens to me, but does not say a word. He only sighs. I understand that right now he does not need my advice.)*

<!-- INJECT_ACTIVITY: match-up-accusative-to-genitive-negation -->


## Підсумок — Summary

You have learned three essential ways to use the Genitive case in daily life. Let's review the main rules. Can you answer these self-check questions?

*   **Яке сьогодні число?** *(What is today's date?)* Remember that the day is an ordinal number, but the month must be in the Genitive singular.
    *   «Сьогодні десяте травня.» *(Today is the tenth of May.)*
*   **How do you count to five?** The numbers 2, 3, and 4 take the Nominative plural, but numbers from 5 and above require the Genitive plural.
    *   «Один стіл, два столи, п'ять столів.» *(One table, two tables, five tables.)*
*   **How do you negate «Я бачу фільм»?** When you negate a verb that takes a direct object, the object often changes from the Accusative to the Genitive case to emphasize the total absence of the action or object.
    *   «Я не бачу фільму.» *(I do not see a film.)*

The Genitive case is fundamental to Ukrainian grammar. It brings precision when we talk about exact quantities, specific dates, and total absences. Whether you are checking your calendar, counting items on your desk, or explaining that you do not have time, you are relying on this case. As you continue to practice, using the Genitive with words like «немає» and numbers from five upwards will become a natural habit.

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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

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
