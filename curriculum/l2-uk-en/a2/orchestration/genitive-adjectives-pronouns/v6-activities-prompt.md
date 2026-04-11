<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-adjectives-pronouns.yaml` file for module **13: Мого друга, цієї книги** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-adj-noun -->`
- `<!-- INJECT_ACTIVITY: quiz-possessive-choice -->`
- `<!-- INJECT_ACTIVITY: match-up-nom-gen -->`
- `<!-- INJECT_ACTIVITY: fill-in-complex-phrases -->`
- `<!-- INJECT_ACTIVITY: error-correction-agreement -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the adjective and noun into the correct Genitive form
  items: 8
  type: fill-in
- focus: Choose the correct possessive pronoun form (мого vs. моєї etc.)
  items: 8
  type: quiz
- focus: Match Nominative noun phrases to their Genitive equivalents
  items: 8
  type: match-up
- focus: Build complete Genitive phrases with demonstrative + adjective + noun
  items: 8
  type: fill-in
- focus: Find and fix adjective-noun agreement errors in Genitive phrases (e.g., *нової
    друга → нового друга, *цієї будинку → цього будинку)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- молодий (young)
- старший (older, elder)
- дівчина (girl, young woman)
- олівець (pencil)
required:
- прикметник (adjective)
- займенник (pronoun)
- присвійний (possessive)
- вказівний (demonstrative)
- узгодження (agreement (grammatical))
- дозвіл (permission)
- підручник (textbook)
- документ (document)
- вчителька (female teacher)
- важливий (important)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Який? Якого? Прикметники в родовому (Which? Whose? Adjectives in the Genitive)

> — **Власник:** Добрий день! Я шукаю сумку мого старшого брата. *(Good day! I am looking for my older brother's bag.)*
> — **Працівник:** Добрий день. У нас є багато сумок. Яка це сумка? *(Good day. We have many bags. Which bag is it?)*
> — **Власник:** Вона велика і чорна. Ви не бачили цієї чорної сумки? *(It is big and black. Have you not seen this black bag?)*
> — **Працівник:** Ні, сьогодні не приносили такої сумки. Тут немає вашої чорної сумки, але є парасолька цієї маленької дівчини. *(No, they did not bring such a bag today. There is no black bag of yours here, but there is an umbrella of this little girl.)*
> — **Власник:** Ні, це не наша. Нам не треба чужої парасольки. А ви не бачили нашого великого чемодана? *(No, that's not ours. We do not need someone else's umbrella. And have you not seen our big suitcase?)*
> — **Працівник:** Ні, тут немає вашого великого чемодана. Але подивіться біля того дерев'яного стола. Може, там? *(No, your big suitcase is not here. But look near that wooden table. Maybe there?)*
> — **Власник:** Добре, я подивлюся. Я не можу повернутися додому без цього великого чемодана. *(Good, I will look. I cannot return home without this big suitcase.)*

In Ukrainian, we use the essential rule of **узгодження** *(agreement)*. Just as nouns change their endings after prepositions like «без» *(without)*, «для» *(for)*, or «біля» *(near)*, the adjectives describing them must also shift to match the exact gender, number, and case of the noun. If the noun is in the Genitive case, the adjective must be in the Genitive case too. This means you cannot just place a Nominative adjective next to a Genitive noun. They must work together as a team.

«Читаємо українською»
Я живу біля великого парку. *(I live near a big park.)*
Він працює без нового комп'ютера. *(He works without a new computer.)*
Це подарунок для молодої мами. *(This is a gift for the young mother.)*
У мене немає червоного олівця. *(I do not have a red pencil.)*
Ми стоїмо біля високого дерева. *(We are standing near a tall tree.)*
Вона не п'є солодкого чаю. *(She does not drink sweet tea.)*

For masculine and neuter adjectives with hard stems, the Genitive ending is **-ого**. This applies to most adjectives you already know. For example, «новий друг» *(new friend)* becomes **«нового друга»**. Similarly, «велике місто» *(big city)* becomes **«великого міста»**, and «старий будинок» *(old building)* changes to **«старого будинку»**. Notice the pronunciation of the **-ого** ending. In Ukrainian, it is pronounced exactly as it is written: with a clear, deep «г» sound, not like a «в» as in some neighboring languages. This is a fundamental feature of authentic Ukrainian phonetics. Say **«нового»**. Never pronounce it like the Russian equivalent.

«Читаємо українською»
Сьогодні немає сильного вітру. *(Today there is no strong wind.)*
Вона чекає біля старого театру. *(She is waiting near the old theater.)*
Я не бачу твого нового друга. *(I do not see your new friend.)*
Тут немає гарячого чаю. *(There is no hot tea here.)*
Ми їдемо з великого міста. *(We are driving from a big city.)*
Я шукаю вікно з відкритого балкона. *(I am looking for a window from an open balcony.)*

If a masculine or neuter adjective belongs to the soft group (usually ending in a soft sign or «й» in the Nominative), it takes the Genitive ending **-ього**. The soft sign ensures that the consonant before the ending remains soft. For example, «синій олівець» *(blue pencil)* becomes **«синього олівця»**. «Вчорашній день» *(yesterday's day)* changes to **«вчорашнього дня»**, and «літнє море» *(summer sea)* becomes **«літнього моря»**. Remember that the soft sign is crucial here.

«Читаємо українською»
Ми живемо недалеко від синього моря. *(We live not far from the blue sea.)*
У нього немає вчорашнього хліба. *(He does not have yesterday's bread.)*
Я не пам'ятаю останнього уроку. *(I do not remember the last lesson.)*
Він не має осіннього пальта. *(He does not have an autumn coat.)*
Вони приїхали після ранкового дощу. *(They arrived after the morning rain.)*

Feminine adjectives take completely different endings in the Genitive case. Hard stem adjectives take the ending **-ої**. For example, «нова книга» *(new book)* becomes **«нової книги»**, and «гарна дівчина» *(pretty girl)* becomes **«гарної дівчини»**. Soft stem adjectives take the ending **-ьої** or **-ньої**. For instance, «синя сукня» *(blue dress)* changes to **«синьої сукні»**, and «вечірня школа» *(evening school)* becomes **«вечірньої школи»**. Pay close attention to these feminine endings. The Ukrainian **-ої** and **-ьої** are unique and distinct. They are pronounced with two clear vowel sounds at the end, unlike the single blended sound found in Russian. Do not confuse them.

«Читаємо українською»
Вона читає сторінку з нової книги. *(She is reading a page from a new book.)*
У мене немає синьої ручки. *(I do not have a blue pen.)*
Вони живуть біля великої річки. *(They live near a large river.)*
Він вийшов з вечірньої школи. *(He came out of the evening school.)*
Це лист від моєї старої бабусі. *(This is a letter from my old grandmother.)*
Ми йдемо від гарної площі. *(We are walking from the beautiful square.)*

We frequently use Genitive adjectives in full phrases after prepositions like «без», «для», «біля», and «від» *(from)*. When you form a sentence, both the adjective and the noun must align in the Genitive case. For example, «Я не можу жити без цієї доброї кави» *(I cannot live without this good coffee)*. Or when giving a present: «Це подарунок для мого старого вчителя» *(This is a gift for my old teacher)*. You can string multiple adjectives together, and they all take the same Genitive ending. For example, «без великого чорного стола» *(without a big black table)*. Practice saying the adjective and the noun together as one flowing unit.

«Читаємо українською»
Я йду додому від старого лікаря. *(I am going home from the old doctor.)*
Ми граємо у футбол біля нового стадіону. *(We are playing football near the new stadium.)*
Вона п'є чай без солодкого цукру. *(She drinks tea without sweet sugar.)*
Це ліки для маленької дитини. *(This is medicine for a small child.)*
У мене є лист від старшого брата. *(I have a letter from an older brother.)*
Я не хочу жити без вільної України. *(I do not want to live without a free Ukraine.)*

<!-- INJECT_ACTIVITY: fill-in-adj-noun -->

## Мого, твого, нашого: присвійні займенники (Possessive Pronouns)

A possessive pronoun (**присвійний займенник**) changes its form to match the noun it describes. When a noun is in the Genitive case, the possessive pronoun must also take a Genitive form. This means that the basic questions for possession must change. The Nominative question **«Чий?»** *(Whose?)* becomes **«Чийого?»** *(Of whose?)* for masculine and neuter nouns. The feminine question **«Чия?»** becomes **«Чиєї?»** *(Of whose?)*. You will use these forms very often when talking about relationships, locations, or things you do not have.

«Читаємо українською»
Чийого зошита тут немає? *(Whose notebook is not here?)*
У нас немає чиєї ручки? *(Whose pen do we not have?)*
Я не знаю, чийого брата ми чекаємо. *(I do not know whose brother we are waiting for.)*
Від чиєї мами цей лист? *(From whose mother is this letter?)*

For masculine and neuter forms, the first-person and second-person pronouns drop their final sounds and add **-ого**. This creates the Genitive forms **мого** *(my)*, **твого** *(your)*, and **свого** *(one's own)*. Notice how the sound shifts to a deep, rounded vowel at the end. These words pair perfectly with Genitive nouns, especially after prepositions that require the Genitive case. For example, the phrase **«мій дім»** *(my house)* becomes **«біля мого дому»** *(near my house)*. The phrase **«твій дозвіл»** *(your permission)* becomes **«без твого дозволу»** *(without your permission)*.

«Читаємо українською»
Я не можу жити без мого телефону. *(I cannot live without my phone.)*
Вона пішла додому без твого дозволу. *(She went home without your permission.)*
Це кабінет мого молодого лікаря. *(This is the office of my young doctor.)*
У мого друга є новий підручник. *(My friend has a new textbook.)*
Ми чекаємо біля твого офісу. *(We are waiting near your office.)*

For feminine nouns, the possessive pronouns take the ending **-єї**. This creates the Genitive forms **моєї** *(my)*, **твоєї** *(your)*, and **своєї** *(one's own)*. This ending has a soft, flowing pronunciation. Pay attention to how it harmonizes with the feminine Genitive noun endings. For instance, the phrase **«моя сестра»** *(my sister)* becomes **«від моєї сестри»** *(from my sister)*. The phrase **«твоя подруга»** *(your friend)* becomes **«для твоєї подруги»** *(for your friend)*.

«Читаємо українською»
Це олівець для твоєї старшої сестри. *(This is a pencil for your older sister.)*
У моєї мами сьогодні день народження. *(My mother has a birthday today.)*
Я йду з роботи до моєї родини. *(I am going from work to my family.)*
Вона не хоче їсти без своєї тарілки. *(She does not want to eat without her plate.)*
Кіт спить біля твоєї нової сумки. *(The cat is sleeping near your new bag.)*

When we speak about things that belong to multiple people, we use plural possessive pronouns. The pronouns **наш** *(our)* and **ваш** *(your)* decline exactly like hard-group adjectives. For masculine and neuter nouns, we use the forms **нашого** and **вашого**. For feminine nouns, we use the forms **нашої** and **вашої**. For example, the phrase **«наша лікарня»** *(our hospital)* becomes **«до нашої лікарні»** *(to our hospital)*. The phrase **«ваше місто»** *(your city)* becomes **«з вашого міста»** *(from your city)*.

> — **Марія:** Звідки ви їдете, дівчата? *(Where are you traveling from, girls?)*
> — **Оксана:** Ми їдемо з нашого міста до Києва. *(We are traveling from our city to Kyiv.)*
> — **Марія:** А де ви будете жити? *(And where will you live?)*
> — **Оксана:** Ми будемо жити біля вашої школи. *(We will live near your school.)*
> — **Марія:** Це дуже близько до нашого дому! *(That is very close to our house!)*

There is a very important rule regarding the pronoun for their possession. In standard Ukrainian, the possessive pronoun is **їхній** *(their)*. Because it is an adjective-like pronoun, it declines fully. It follows the soft-group adjective pattern. For masculine and neuter nouns, we use the form **їхнього**. For feminine nouns, we use the form **їхньої**. You might sometimes hear people use the short personal pronoun to mean possession, but this is a direct borrowing from Russian grammar. Always use the proper, declinable forms to speak natural and correct Ukrainian.

«Читаємо українською»
Я не знаю їхнього старшого брата. *(I do not know their older brother.)*
Ми йдемо до їхньої вчительки. *(We are going to their teacher.)*
У їхнього сина є новий велосипед. *(Their son has a new bicycle.)*
Це ключі від їхньої квартири. *(These are the keys from their apartment.)*
Вони живуть недалеко від їхнього парку. *(They live not far from their park.)*

Third-person singular possessive pronouns are the forms **його** *(his/its)* and **її** *(her)*. Unlike the other possessive pronouns we have studied, these forms are absolutely unchangeable. They remain exactly the same no matter what case, gender, or number the following noun has. Whether the noun is in the Nominative case or the Genitive case, the pronoun does not change. For example, the phrase **«його стіл»** *(his table)* becomes **«біля його столу»** *(near his table)*. The phrase **«її сестра»** *(her sister)* becomes **«від її сестри»** *(from her sister)*.

«Читаємо українською»
У мене немає її важливого документа. *(I do not have her important document.)*
Я чекаю біля його будинку. *(I am waiting near his building.)*
Це подарунок від її бабусі. *(This is a gift from her grandmother.)*
Ми не бачимо його підручника на столі. *(We do not see his textbook on the table.)*
Він не може працювати без її комп'ютера. *(He cannot work without her computer.)*

<!-- INJECT_ACTIVITY: quiz-possessive-choice -->

## Цього, того: вказівні займенники та повні фрази (Demonstratives and Full Phrases)

A demonstrative pronoun (**вказівний займенник**) points out specific objects in our environment or in a conversation. In the Genitive case, the pronoun **цей** *(this)* becomes **цього** for masculine and neuter nouns. Notice that it takes the soft-group adjective ending **-ього**, sounding very similar to «синього». The pronoun **той** *(that)* becomes **того**, taking the hard-group ending **-ого**. We use these forms to contrast proximity: indicating things close to us versus things farther away. For example, if you are walking down the street and choosing a place to live, you might point and say: «Я хочу жити біля цього будинку» *(I want to live near this building)*. Then, pointing across the street, you add: «Але я не хочу жити біля того парку» *(But I do not want to live near that park)*.

«Читаємо українською»
Я не знаю цього чоловіка. *(I do not know this man.)*
У мене немає того важливого документа. *(I do not have that important document.)*
Вона чекає після того уроку. *(She is waiting after that lesson.)*
Ми їдемо від цього нового магазину. *(We are driving from this new store.)*

For feminine nouns, the demonstrative pronouns also change their form to match the Genitive endings. The pronoun **ця** *(this)* becomes **цієї** in the Genitive case. The pronoun **та** *(that)* becomes **тієї**. You will also frequently hear the shorter variant **тої** instead of «тієї». Both forms are absolutely correct, but «тої» is very natural in everyday conversation, poetry, and modern literature. You can use these feminine forms with prepositions of location or to show absence. For example, you might say «без цієї книги» *(without this book)* when you leave something at home, or «навпроти тієї школи» *(opposite that school)* when giving directions.

> — **Анна:** Ти не бачив цієї червоної ручки? *(Have you not seen this red pen?)*
> — **Павло:** Ні, я бачив тільки олівець біля тієї сумки. *(No, I only saw a pencil near that bag.)*
> — **Анна:** Мені треба писати, але я не можу без тої ручки. *(I need to write, but I cannot without that pen.)*
> — **Павло:** Візьми мій синій олівець. *(Take my blue pencil.)*

In Ukrainian, the logical word order for a descriptive phrase is very consistent: first the demonstrative pronoun, then the possessive pronoun or adjective, and finally the noun itself. When you use these full phrases in the Genitive case, every single word in the chain must take the correct Genitive ending. They must all agree in gender, number, and case with the core noun. We start with the Nominative noun: **вчителька** *(female teacher)*. We add a descriptive adjective: **нова вчителька** *(new female teacher)*. Then we add a possessive pronoun: **моя нова вчителька** *(my new female teacher)*. If we want to buy a gift for her, we use the preposition **для** *(for)*, which always requires the Genitive case. Every single word changes: **для моєї нової вчительки** *(for my new female teacher)*.

«Читаємо українською»
Це зошит мого нового друга. *(This is the notebook of my new friend.)*
Я йду до нашої старої школи. *(I am going to our old school.)*
Він читає лист від свого молодого брата. *(He is reading a letter from his young brother.)*
Ми не знаємо тієї високої дівчини. *(We do not know that tall girl.)*

Whether you use a demonstrative and an adjective together, or a possessive and an adjective, all modifiers lock into the Genitive case to match the noun. For example, to say «from this new teacher», you combine the preposition **від** *(from)*, the demonstrative **цього**, the adjective **нового** *(new)*, and the noun **вчителя** *(teacher)*. The complete phrase is **«від цього нового вчителя»**. To say «after that important document», you combine the preposition **після** *(after)*, the demonstrative **того**, the adjective **важливий** *(important)*, and the noun **документ** *(document)*. The complete phrase is **«після того важливого документа»**. Always check the gender of the core noun first. Once you know the gender, simply apply the corresponding Genitive endings to everything that describes it.

:::note Формуємо фрази (Building phrases)
цей великий ринок → біля **цього великого ринку** *(near this big market)*
та цікава книга → без **тієї цікавої книги** *(without that interesting book)*
наш синій олівець → замість **нашого синього олівця** *(instead of our blue pencil)*
:::

«Читаємо українською»
Сьогодні я збираю речі до школи. *(Today I am packing things for school.)* 
В моєму рюкзаку немає цього синього олівця, але є багато моїх нових підручників. *(In my backpack there is no this blue pencil, but there are many of my new textbooks.)* 
Я не можу знайти своєї старої карти України. *(I cannot find my old map of Ukraine.)* 
Вона зазвичай лежить біля того великого словника. *(It usually lies near that big dictionary.)* 
Без цієї важливої карти я не зможу працювати на уроці. *(Without this important map I will not be able to work at the lesson.)* 
Я питаю мого молодшого брата. *(I ask my younger brother.)* 
Він каже, що карта лежить навпроти нашого великого вікна. *(He says that the map lies opposite our big window.)* 
Я дякую брату. *(I thank my brother.)* 
Я беру карту і йду до моєї нової вчительки. *(I take the map and go to my new teacher.)*

<!-- INJECT_ACTIVITY: match-up-nom-gen -->
<!-- INJECT_ACTIVITY: fill-in-complex-phrases -->
<!-- INJECT_ACTIVITY: error-correction-agreement -->

## Підсумок — Summary

1. **Яке закінчення мають прикметники чоловічого роду в родовому відмінку?** *(What ending do masculine adjectives have in the Genitive case?)*
Відповідь: **-ого** (тверда група) або **-ього** (м'яка група). *(Answer: -ogo for the hard group or -jogo for the soft group.)*

2. **Чи змінюються займенники «його» та «її» як присвійні?** *(Do the pronouns "його" and "її" change as possessives?)*
Відповідь: Ні, вони завжди залишаються незмінними. *(Answer: No, they always remain unchanged.)*

3. **Яка форма займенника «цей» для жіночого роду в родовому відмінку?** *(What is the form of the pronoun "цей" for the feminine gender in the Genitive case?)*
Відповідь: **цієї**. *(Answer: цієї.)*

| Тип слова *(Word type)* | Чоловічий / Середній рід *(Masculine / Neuter)* | Жіночий рід *(Feminine)* |
| :--- | :--- | :--- |
| **Прикметники (тверді)** *(Adjectives, hard)* | нов**ого** | нов**ої** |
| **Прикметники (м'які)** *(Adjectives, soft)* | син**ього** | син**ьої** |
| **Присвійні займенники** *(Possessive pronouns)* | м**ого**, тв**ого**, наш**ого**, ваш**ого** | мо**єї**, тво**єї**, наш**ої**, ваш**ої** |
| **Вказівні займенники** *(Demonstrative pronouns)* | ць**ого**, т**ого** | ці**єї**, ті**єї** |

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-adjectives-pronouns
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

**Level: A2 (Module 13/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
