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

- `<!-- INJECT_ACTIVITY: task-1 -->`
- `<!-- INJECT_ACTIVITY: task-2 -->`
- `<!-- INJECT_ACTIVITY: task-3 -->`
- `<!-- INJECT_ACTIVITY: task-4 -->`
- `<!-- INJECT_ACTIVITY: task-5 -->`

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
## Прикметники у давальному відмінку (Adjectives in the Dative Case)

В університеті закінчилася лекція. Вчителька перевірила тести і зараз роздає їх студентам. *(A lecture has ended at the university. The teacher has checked the tests and is now handing them out to the students.)*

> — **Вчителька:** Олексію, **моєму найкращому студентові** — десятка! *(Oleksiy, to my best student — a ten!)*
> — **Олексій:** Дуже дякую! Я багато читав. *(Thank you very much! I read a lot.)*
> — **Вчителька:** А **нашій новій студентці**, Марії — дев'ятка. Це дуже добрий результат. *(And to our new student, Mariia — a nine. This is a very good result.)*
> — **Марія:** Я дуже рада. *(I am very glad.)*
> — **Вчителька:** Але **цьому хлопцю** треба більше працювати. Іване, це твій тест. *(But this boy needs to work more. Ivan, this is your test.)*
> — **Іван:** Я розумію. Наступного разу буде краще. *(I understand. Next time it will be better.)*

Adjectives must agree with the noun they describe in gender, number, and case. Masculine and neuter adjectives with hard stems take the Dative ending **-ому**.

*   новий будинок → **новому будинку** *(to the new house)*
*   старий друг → **старому другові** *(to the old friend)*
*   велике вікно → **великому вікну** *(to the big window)*

Читаємо українською:
Я завжди допомагаю **новому студенту**. *(I always help the new student.)*
Вона дарує цікаву книгу **старому другові**. *(She is gifting an interesting book to an old friend.)*
Ми йдемо до школи по **новому мосту**. *(We are going to school along the new bridge.)*
Директор тисне руку **відомому письменнику**. *(The director shakes the hand of the famous writer.)*
Я щиро дякую **старому вчителю** за цей урок. *(I sincerely thank the old teacher for this lesson.)*

Masculine and neuter adjectives with soft stems (typically ending in **-ій** or **-є** in the Nominative case) take the Dative ending **-ьому**. The soft sign (ь) is required to preserve the soft sound of the consonant before the vowel «о».

*   синій диван → **синьому дивану** *(to the blue sofa)*
*   літній день → **літньому дню** *(to the summer day)*
*   середній клас → **середньому класу** *(to the middle class)*

Читаємо українською:
Цей новий стілець ідеально пасує **синьому дивану**. *(This new chair perfectly matches the blue sofa.)*
Туристи радіють **літньому дню** та теплому сонцю. *(Tourists rejoice at the summer day and warm sun.)*
Він віддає ключі **наступному клієнту**. *(He gives the keys to the next client.)*
Вчитель довго пояснює складне правило **середньому класу**. *(The teacher explains the complex rule to the middle class for a long time.)*
Мій брат зовсім не вірить **ранньому прогнозу** погоди. *(My brother does not believe the early weather forecast at all.)*

Feminine adjectives take the Dative ending **-ій** for both hard and soft stems. The root consonants (г, к, х) do not change before this ending.

*   нова школа → **новій школі** *(to the new school)*
*   синя сумка → **синій сумці** *(to the blue bag)*
*   тиха вулиця → **тихій вулиці** *(to the quiet street)*
*   дорога сестра → **дорогій сестрі** *(to the dear sister)*
*   легка робота → **легкій роботі** *(to the easy job)*

Читаємо українською:
Я часто телефоную **молодій жінці**. *(I often call the young woman.)*
Він купує гарні квіти **дорогій мамі**. *(He is buying beautiful flowers for the dear mother.)*
Цей жовтий колір дуже пасує **синій сумці**. *(This yellow color matches the blue bag very well.)*
Студенти голосно дякують **новій вчительці**. *(The students loudly thank the new teacher.)*
Вона завжди віддає перевагу **тихій музиці**. *(She always prefers quiet music.)*

In the plural, adjectives of all genders take the Dative ending **-им**.

*   нові друзі → **новим друзям** *(to the new friends)*
*   гарні дівчата → **гарним дівчатам** *(to the pretty girls)*
*   сині моря → **синім морям** *(to the blue seas)*
*   великі міста → **великим містам** *(to the big cities)*

Читаємо українською:
Вчитель дає нове завдання **новим студентам**. *(The teacher gives a new task to the new students.)*
Наша держава завжди допомагає **старим людям**. *(Our state always helps old people.)*
Я часто пишу довгі листи **гарним друзям**. *(I often write long letters to good friends.)*
Туристи щиро дивуються **високим горам**. *(Tourists are sincerely surprised by the high mountains.)*
Ці граматичні правила відомі **маленьким дітям**. *(These grammatical rules are known to small children.)*

<!-- INJECT_ACTIVITY: task-1 -->

## Присвійні та вказівні займенники у давальному відмінку (Possessive and Demonstrative Pronouns)

Кожен **присвійний** займенник *(possessive pronoun)* змінює свою форму, щоб узгоджуватися з іменником у давальному відмінку. The pronouns **наш** *(our)* and **ваш** *(your, formal or plural)* take the endings of hard-stem adjectives. The pronouns **мій** *(my)* and **твій** *(your, informal)* take the endings of soft-stem adjectives, using «є» instead of «о» for masculine and neuter forms.

* мій → **моєму** (masc/neut), **моїй** (fem), **моїм** (plural)
* твій → **твоєму** (masc/neut), **твоїй** (fem), **твоїм** (plural)
* наш → **нашому** (masc/neut), **нашій** (fem), **нашим** (plural)
* ваш → **вашому** (masc/neut), **вашій** (fem), **вашим** (plural)

Читаємо українською:
Я завжди телефоную **моєму батькові** ввечері. *(I always call my father in the evening.)*
Він часто допомагає **нашій сестрі** робити домашнє завдання. *(He often helps our sister do homework.)*
Ми зараз купуємо гарний подарунок **твоєму брату**. *(We are currently buying a nice present for your brother.)*
Новий вчитель дає цікаві зошити **вашим дітям**. *(The new teacher gives interesting notebooks to your children.)*
Олена щиро дякує **моїй мамі** за смачну вечерю. *(Olena sincerely thanks my mother for a delicious dinner.)*

> — **Анна:** Ти допомагаєш **твоєму братові**? *(Are you helping your brother?)*
> — **Марко:** Так, я пояснюю математику **моєму братові**. *(Yes, I am explaining math to my brother.)*
> — **Анна:** А що ви даруєте **вашій мамі**? *(And what are you giving to your mother?)*
> — **Марко:** Ми даруємо **нашій мамі** новий телефон. *(We are giving our mother a new phone.)*

The third-person pronouns **його** *(his/its)* and **її** *(her)* are invariable. They never change their form. The pronoun **їхній** *(their)* declines exactly like a soft-stem adjective.

* його друг → **його другові** *(to his friend)*
* її сестра → **її сестрі** *(to her sister)*
* їхній брат → **їхньому братові** *(to their brother)*
* їхня мама → **їхній мамі** *(to their mother)*
* їхні діти → **їхнім дітям** *(to their children)*

Читаємо українською:
Цей студент із радістю показує університет **його мамі**. *(This student happily shows the university to his mother.)*
Молодий лікар дає рецепт на ліки **її дідусеві**. *(The young doctor gives a prescription for medicine to her grandfather.)*
Ми віддаємо ключі від квартири **їхньому синові**. *(We are giving the apartment keys to their son.)*
Я довго розповідаю цю смішну історію **його друзям**. *(I tell this funny story to his friends for a long time.)*
Вона завжди допомагає **їхній бабусі** прибирати кімнату. *(She always helps their grandmother clean the room.)*
Я купую нову іграшку **її собаці**. *(I am buying a new toy for her dog.)*

The demonstrative pronouns **цей** *(this)* and **той** *(that)* decline similarly to adjectives in the Dative case.

* цей → **цьому** (masc/neut), **цій** (fem), **цим** (plural)
* той → **тому** (masc/neut), **тій** (fem), **тим** (plural)

Читаємо українською:
Я дуже щиро співчуваю **цьому хлопцю**. *(I very sincerely sympathize with this boy.)*
Вона трохи заздрить **тому відомому актору**. *(She slightly envies that famous actor.)*
Ми даруємо великі червоні квіти **цій вчительці**. *(We are giving big red flowers to this teacher.)*
Директор школи пише довгий лист **тим студентам**. *(The school director is writing a long letter to those students.)*
Туристи зовсім не вірять **цьому ранньому прогнозу**. *(The tourists do not believe this early forecast at all.)*

> — **Павло:** Кому ти купуєш цей подарунок? *(Who are you buying this present for?)*
> — **Оксана:** Я купую його **цьому хлопцю**. *(I am buying it for this boy.)*
> — **Павло:** А що ти даруєш **тій дівчині**? *(And what are you giving to that girl?)*
> — **Оксана:** **Тій дівчині** я дарую нову книгу. *(To that girl, I am giving a new book.)*

<!-- INJECT_ACTIVITY: task-2 -->

## Повні іменникові групи у давальному відмінку (Full Dative Noun Phrases)

The possessive pronoun, adjective, and noun must all match in gender, number, and case. In the Dative case, the entire phrase works together as a single unit. The standard word order is: pronoun + adjective + noun.

* мій старший брат → **моєму старшому братові** *(to my older brother)*
* наша нова вчителька → **нашій новій вчительці** *(to our new teacher)*
* ваше маленьке місто → **вашому маленькому місту** *(to your small city)*
* ці добрі люди → **цим добрим людям** *(to these kind people)*
* той високий студент → **тому високому студентові** *(to that tall student)*

Читаємо українською:
Я купую дорогий подарунок **моєму молодшому братові**. *(I am buying an expensive present for my younger brother.)*
Ми показуємо старі фотографії **нашій новій вчительці**. *(We are showing old photographs to our new teacher.)*
Він щовечора розповідає казку **своєму маленькому синові**. *(He tells a fairy tale to his little son every evening.)*
Ви завжди із радістю допомагаєте **цим добрим людям**. *(You always happily help these kind people.)*

Verbs involving communication or giving (**подарувати**, **написати**, **відправити**, **пояснити**) trigger the Dative case for the recipient.

> — **Оксана:** Кому ти хочеш **подарувати** цю цікаву книгу? *(Who do you want to give this interesting book to?)*
> — **Максим:** Я хочу подарувати її **моєму найкращому другу**. *(I want to give it to my best friend.)*
> — **Оксана:** А кому ти зараз пишеш довге повідомлення? *(And who are you writing a long message to now?)*
> — **Максим:** Я пишу **нашій новій вчительці**. *(I am writing to our new teacher.)*

Читаємо українською:
Студент довго намагається пояснити правило **цьому іноземному другу**. *(The student tries for a long time to explain the rule to this foreign friend.)*
Я хочу сьогодні написати лист **моїй старій бабусі**. *(I want to write a letter to my old grandmother today.)*
Вона щороку дарує квіти **своїй улюбленій актрисі**. *(She gives flowers to her favorite actress every year.)*
Ми відправляємо велику посилку **нашому старшому братові**. *(We are sending a large parcel to our older brother.)*
Директор школи дає премію **цьому талановитому вчителю**. *(The school principal gives a bonus to this talented teacher.)*

The Dative ending for masculine modifiers is **-ому** / **-ьому**. The Dative ending for feminine modifiers is **-ій**. Do not mix them.

> — **Ганна:** Що ти даєш **цьому маленькому хлопцю**? *(What are you giving to this little boy?)*
> — **Богдан:** Я даю яблуко **цьому маленькому хлопцю**. *(I am giving an apple to this little boy.)*
> — **Ганна:** А що ти даєш **тій маленькій дівчині**? *(And what are you giving to that little girl?)*
> — **Богдан:** **Тій маленькій дівчині** я даю смачну цукерку. *(To that little girl, I am giving a tasty candy.)*

:::tip Увага! (Attention!)
Завжди перевіряйте рід іменника! *(Always check the gender of the noun!)* If the noun is masculine, use **-ому**: **моєму доброму другу**. If the noun is feminine, use **-ій**: **моїй добрій подрузі**. They must match perfectly!
:::

Читаємо українською:
Я повністю довіряю **цьому розумному чоловікові**. *(I completely trust this smart man.)*
Вона ніколи не вірить **цій хитрій жінці**. *(She never believes this sly woman.)*
Ми радісно купуємо квитки **нашому доброму другу**. *(We joyfully buy tickets for our good friend.)*
Вони дають нові зошити **тій розумній студентці**. *(They give new notebooks to that smart student.)*

<!-- INJECT_ACTIVITY: task-3 -->
<!-- INJECT_ACTIVITY: task-4 -->

## Порівняння відмінків (Comparing Cases So Far)

| Відмінок *(Case)* | Чоловічий / Середній рід *(Masc / Neut)* | Жіночий рід *(Fem)* | Множина *(Plural)* |
| :--- | :--- | :--- | :--- |
| **Називний** *(Nominative)* | новий, мій / нове, моє | нова, моя | нові, мої |
| **Родовий** *(Genitive)* | нов**ого**, м**ого** | нов**ої**, мо**єї** | нов**их**, мо**їх** |
| **Давальний** *(Dative)* | нов**ому**, мо**єму** | нов**ій**, мо**їй** | нов**им**, мо**їм** |

Читаємо українською:
**Називний відмінок** *(Nominative)*: Це **мій старий друг**. *(This is my old friend.)*
**Родовий відмінок** *(Genitive)*: Сьогодні тут немає **мого старого друга**. *(My old friend is not here today.)*
**Давальний відмінок** *(Dative)*: Я даю гарний подарунок **моєму старому другові**. *(I give a nice gift to my old friend.)*
**Називний відмінок** *(Nominative)*: Ось **наша нова вчителька**. *(Here is our new teacher.)*
**Родовий відмінок** *(Genitive)*: Ми всі дуже чекаємо **нашої нової вчительки**. *(We are all waiting very much for our new teacher.)*
**Давальний відмінок** *(Dative)*: Ми радісно даруємо квіти **нашій новій вчительці**. *(We joyfully give flowers to our new teacher.)*

The Nominative case indicates the subject. The Genitive case indicates absence, possession, or follows specific prepositions. The Dative case indicates the recipient of an action.

> — **Антон:** Хто це такий стоїть біля вікна? *(Who is this standing near the window?)*
> — **Марія:** Це **наш новий студент**. *(This is our new student. - Nominative)*
> — **Антон:** Я раніше не бачив **нашого нового студента**. Звідки він? *(I haven't seen our new student before. Where is he from? - Genitive)*
> — **Марія:** Він з Польщі. Я зараз покажу школу **нашому нового студенту**. *(He is from Poland. I will show the school to our new student now. - Dative)*

Читаємо українською:
Ось **ця красива жінка**. *(Here is this beautiful woman.)*
Біля **цієї красивої жінки** сидить маленький собака. *(A small dog is sitting near this beautiful woman.)*
Я часто допомагаю **цій красивій жінці**. *(I often help this beautiful woman.)*
Це **твій розумний брат**. *(This is your smart brother.)*
У **твого розумного брата** є велика квартира. *(Your smart brother has a large apartment.)*
Ти завжди телефонуєш **твоєму розумному братові**. *(You always call your smart brother.)*

<!-- INJECT_ACTIVITY: task-5 -->

## Підсумок (~150 words)

Дайте відповіді на ці запитання:

* **Яке закінчення мають прикметники чоловічого та середнього роду в давальному відмінку?** *(What ending do masculine and neuter adjectives have in the dative case?)*
  — Вони мають закінчення **-ому** або **-ьому** (наприклад: новому, синьому). *(They have the ending -ому or -ьому (for example: to the new, to the blue).)*

* **Як змінюються займенники «його» та «її» в давальному відмінку?** *(How do the pronouns 'his' and 'her' change in the dative case?)*
  — Вони ніколи не змінюються! *(They never change!)* Ми кажемо: дати його братові, сказати її сестрі. *(We say: to give to his brother, to tell her sister.)*

* **Яке спільне закінчення мають прикметники всіх родів у множині?** *(What common ending do adjectives of all genders have in the plural?)*
  — У множині всі прикметники мають закінчення **-им** (наприклад: новим, моїм). *(In the plural, all adjectives have the ending -им (for example: to the new, to my).)*

* **В якому порядку ми ставимо слова в іменниковій групі?** *(In what order do we put words in a noun phrase?)*
  — Займенник + прикметник + іменник (наприклад: моєму старшому братові). *(Pronoun + adjective + noun (for example: to my older brother).)*

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
