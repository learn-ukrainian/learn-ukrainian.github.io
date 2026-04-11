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

- `<!-- INJECT_ACTIVITY: quiz-possession-vs-absence -->`
- `<!-- INJECT_ACTIVITY: fill-in-genitive-singular -->`
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

Welcome to a new milestone in your Ukrainian journey! Up to this point, you have been comfortably navigating the world of things that exist, using the Nominative case to name objects and the construction «У мене є...» to express possession. Now, we are stepping into the territory of things that are missing. To talk about absence, lack, or non-existence, you need a brand new grammatical tool: the Genitive case.

Родовий відмінок — це дуже важливий відмінок в українській мові. Він відповідає на питання «кого?» для людей і тварин та «чого?» для неживих предметів. Цей відмінок часто показує походження предмета або належність комусь. Але його найголовніша і найчастіша функція у повсякденному житті — це вираження відсутності.

> *The Genitive case is a very important case in the Ukrainian language. It answers the questions "whom?" for people and animals, and "what?" for inanimate objects. This case often shows the origin of an object or belonging to someone. But its most important and most frequent function in everyday life is expressing absence.*

:::info
**The Magnet of Negation**
The word **немає** acts like a powerful magnet. The moment you use it to say that something is not there, it pulls the following noun out of its basic dictionary form and forces it into the Genitive case.
:::

The contrast between having something and not having something is where the Genitive case truly shines. When you want to say that you have a sister, you use the positive construction «У мене є...» followed by the dictionary form of the noun. However, when you want to state that you do not have a sister, the word «немає» completely changes the grammar of the sentence.

У мене є сестра. Це називний відмінок, базова форма слова. У мене немає сестри. Це родовий відмінок, який показує відсутність людини.

> *I have a sister. This is the nominative case, the basic form of the word. I do not have a sister. This is the genitive case, which shows the absence of a person.*

Let's look at a practical situation to see this in action. Moving into a new apartment is an exciting event, but it is also a time when you acutely notice everything that is missing. Listen to this conversation between a new tenant and her neighbor as they inspect an empty kitchen.

> — **Сусідка:** Добрий день! Ви нова мешканка? *(Good afternoon! Are you the new tenant?)*
> — **Нова мешканка:** Добрий день! Так, я щойно переїхала. *(Good afternoon! Yes, I just moved in.)*
> — **Сусідка:** Як ваша нова квартира? *(How is your new apartment?)*
> — **Нова мешканка:** Квартира гарна, але тут багато коробок і мало меблів. *(The apartment is nice, but there are many boxes and little furniture here.)*
> — **Сусідка:** Ваша кухня зовсім порожня. *(Your kitchen is completely empty.)*
> — **Нова мешканка:** Так, це проблема. Тут немає холодильника! *(Yes, that is a problem. There is no fridge here!)*
> — **Сусідка:** І я бачу, що тут немає плити. Як ви будете готувати? *(And I see that there is no stove here. How will you cook?)*
> — **Нова мешканка:** Я не знаю. У ванній кімнаті також немає дзеркала. *(I don't know. There is also no mirror in the bathroom.)*

If we analyze this dialogue, we can clearly see the "magnet" effect of the negative word. In the dictionary, the word for a fridge is «холодильник». But because the new tenant is stating its absence, she must say «немає холодильника». The same rule applies to the stove: the dictionary form «плита» transforms into «немає плити». Even the neuter word «дзеркало» changes its ending, becoming «немає дзеркала». You simply cannot use the Nominative case when stating that an object is not present.

:::tip
**Casual Speech Shortcut**
In spoken Ukrainian, you will very often hear the shortened form **нема** instead of the full word **немає**. They mean exactly the same thing and both require the Genitive case, but **нема** sounds much more relaxed and conversational!
:::

Practicing these contrasts is the best way to train your brain to anticipate the case change. Let's look at a few more examples comparing presence and absence. Notice how the ending of the noun changes every single time we introduce the negative element.

Тут є великий стіл. Тут немає стола. У місті є новий театр. У місті немає театру. У нас є проблема. У нас немає проблеми. У мене є час. У мене зовсім нема часу.

> *There is a large table here. There is no table here. The city has a new theater. The city does not have a theater. We have a problem. We do not have a problem. I have time. I have absolutely no time.*

<!-- INJECT_ACTIVITY: quiz-possession-vs-absence -->

To summarize, mastering the Genitive case starts with understanding its deep connection to absence. Whenever you need to express that a person is missing, an object is not there, or a concept is lacking, you must use the word «немає» or «нема». This word acts as a strict grammatical trigger, making the Genitive case absolutely mandatory for the noun that follows.

## Закінчення родового відмінка однини (Genitive Singular Endings)

The biggest challenge with the Genitive case is masculine nouns, which have two possible endings in the singular: **-а/-я** or **-у/-ю**. The choice depends on the meaning of the word. We use the **-а** or **-я** ending for concrete, physical objects that have clear boundaries, living beings, and units of measurement.

Якщо предмет можна намалювати, ми використовуємо закінчення -а або -я. Наприклад, у мене немає брата або стола. У гаражі немає автобуса. Якщо ви купуєте їжу або тканину, ви кажете, що вам не вистачає кілограма або метра. Усі живі істоти також у цій групі.

> *If an object can be drawn, we use the -а or -я ending. For example, I don't have a brother or a table. There is no bus in the garage. If you buy food or fabric, you say that you are missing a kilogram or a meter. All living beings are also in this group.*

We use the **-у** or **-ю** ending for things that are abstract, uncountable, or lack distinct physical boundaries. This includes substances, liquids, emotions, and large geographic regions.

Коли ми говоримо про абстрактні речі, ми додаємо закінчення -у або -ю. Люди часто кажуть, що у них немає часу або досвіду. У каві немає цукру. У пісні немає смутку. Це завжди працює для матеріалів та сильних емоцій.

> *When we talk about abstract things, we add the -у or -ю ending. People often say they have no time or experience. There is no sugar in the coffee. There is no sadness in the song. This always works for materials and strong emotions.*

:::info
**Why Києва but Криму?**
Cities like **Київ** or **Париж** are considered clearly defined points on a map (concrete), taking **-а**. Regions or countries like **Крим** or **Єгипет** are vast spaces, taking **-у**.
:::

Feminine nouns follow a phonetic rule. Words ending in a hard consonant plus **-а** change to **-и**. If the word ends in **-я** or a soft consonant, the ending becomes **-і**. Words belonging to the third declension that end in a consonant also take **-і**.

Більшість жіночих іменників мають закінчення -и. У кімнаті немає мами або роботи. На столі немає книги. Але якщо слово м'яке, закінчення змінюється на -і. У нас немає землі, пісні або вулиці. Є також слова, які закінчуються на приголосний. Ми кажемо, що немає ночі, а в супі немає солі.

> *Most feminine nouns have the -и ending. There is no mom or work in the room. There is no book on the table. But if the word is soft, the ending changes to -і. We have no land, song, or street. There are also words that end in a consonant. We say there is no night, and there is no salt in the soup.*

Neuter nouns are straightforward. If the word ends in **-о**, the Genitive ending is **-а**. If it ends in **-е** or **-я**, the ending becomes **-я**.

Середній рід дуже легкий. У кімнаті немає вікна. Біля будинку немає моря. У тексті немає жодного слова. Іноді здається, що немає спокійного життя. Зверніть увагу на останній звук.

> *The neuter gender is very easy. There is no window in the room. There is no sea near the house. There is not a single word in the text. Sometimes it seems like there is no peaceful life. Pay attention to the final sound.*

### Читаємо українською (Reading Practice)
Let's see how these endings work in a practical situation. Read this dialogue between two colleagues organizing a workspace.

> — **Олена:** У цьому офісі немає стола для менеджера. *(There is no table for the manager in this office.)*
> — **Марко:** Я знаю. Тут також немає комп'ютера і принтера. *(I know. There is also no computer and printer here.)*
> — **Олена:** На кухні немає води і немає цукру. *(There is no water and no sugar in the kitchen.)*
> — **Марко:** У мене зараз зовсім немає часу, щоб піти в магазин. *(I have absolutely no time right now to go to the store.)*

To master these endings, build a simple mental chart. Do not try to memorize lists of rules without context. Practicing anchor pairs will help you intuitively apply the correct ending when you encounter new words.

For masculine nouns, contrast a concrete object with an abstract concept:
**Телефон** — немає телефона
**Час** — немає часу

For feminine nouns, contrast a hard stem with a soft stem:
**Кава** — немає кави
**Вулиця** — немає вулиці

Neuter nouns just shift slightly to their new vowel:
**Слово** — немає слова
**Життя** — немає життя

<!-- INJECT_ACTIVITY: fill-in-genitive-singular -->

There are a couple of important details to remember. English speakers often translate "I don't have money" as a singular concept. However, the Ukrainian word **гроші** (money) is always plural, so you must say **немає грошей**. 

Second, the word **немає** (there is no) is written as one solid word. This is completely different from the phrase **не має**, written as two words, which literally means "he, she, or it does not possess."

Він не має роботи. Тому зараз у нього немає грошей і немає настрою. Він каже, що у місті немає вакансій.

> *He does not have a job. Therefore, right now he has no money and no mood. He says there are no vacancies in the city.*

## Коли є багато або мало (When There Is a Lot or a Little)

Now that you know how to say you don't have one item, let's talk about having a lot of something, or very little. In Ukrainian, when you use words of quantity, the noun that follows must change its form. The most common quantity words are «багато» (a lot, many, much), «мало» (a little, few), and «кілька» or «декілька» (a few, several). These words always require the Genitive plural. You will hear these quantity words constantly in daily conversation, from shopping at the market to discussing your schedule. Think of it like the English phrase "a lot *of* something." In English, you say "many cars" without changing the word "car" besides making it plural. In Ukrainian, the word changes its ending to show that it is part of a larger, quantified group.

У нашому місті є багато парків і мало машин. На столі лежить кілька нових журналів. У мене є декілька запитань до тебе.

> *In our city, there are many parks and few cars. A few new magazines are lying on the table. I have several questions for you.*

Forming the Genitive plural can seem like a puzzle at first, but there are strong patterns. Let's start with masculine nouns. For most masculine words that end in a hard consonant, the dominant Genitive plural ending is **-ів** (or **-їв** after a vowel or soft sign). It is a very reliable pattern that you will use frequently. If you have multiple masculine objects, you simply add this ending to the plural base. This pattern is incredibly consistent for everyday objects, vehicles, and people.

Він має дуже багато братів. У цій великій кімнаті стоїть кілька столів. На вулиці ми бачимо багато нових трамваїв. Мої батьки купили декілька комп'ютерів для офісу.

> *He has very many brothers. In this large room stand several tables. On the street we see many new trams. My parents bought a few computers for the office.*

:::note
**Quick tip** — The word for "friends" in Ukrainian is «друзі». This is an irregular plural, but its Genitive plural form follows the standard masculine rule perfectly: «багато друзів» (a lot of friends). This is an incredibly common phrase, so memorize it as a fixed chunk.
:::

Feminine and neuter nouns share a different pattern. Instead of adding a visible letter, they often take what grammarians call a "zero ending" (нульове закінчення). This means you drop the final vowel of the Nominative singular to form the Genitive plural. However, when you drop that vowel, you sometimes end up with two consonants clustered together at the end of the word, making it hard to pronounce. To fix this "crowded consonant" problem, Ukrainian naturally inserts a "fleeting vowel" (usually **о** or **е**) between the last two consonants.

Студентка читає багато книжок. У моєї мами є кілька сестер. У цьому старому будинку немає вікон. На столі лежить мало яблук.

> *The student reads many books. My mom has several sisters. There are no windows in this old building. There are few apples lying on the table.*

This fleeting vowel makes the language flow smoothly and comfortably. So, the word «книжка» becomes «книжок», «сестра» becomes «сестер», and «вікно» becomes «вікон». You do not need to memorize every single one right away. As you listen and read, your ear will start to expect that helpful vowel whenever the consonants get too crowded.

There is a third, smaller group of nouns across all genders that take the ending **-ей** in the Genitive plural. While this group is smaller, it contains some of the most crucial survival vocabulary in the language. The absolute most important word in this category is «гроші» (money), alongside other common elements of nature and time. 

Зараз у мене зовсім немає грошей. У цієї людини є багато нових ідей. Біля річки гуляє кілька коней. Ми працювали кілька днів і ночей.

> *Right now I have absolutely no money. This person has a lot of new ideas. A few horses are walking near the river. We worked for several days and nights.*

Remember, «гроші» is always a plural concept in Ukrainian. You will constantly use the form «грошей» after «багато», «мало», or «немає».

<!-- INJECT_ACTIVITY: match-up-genitive-plural-quantity -->

Let's put these phrases into everyday context. When you combine quantity words with the Genitive case, you can describe your reality accurately. To ask "How many?" or "How much?", you use the word «скільки». This question word also triggers the Genitive plural for countable items. Whenever you are shopping, asking for directions, or making plans, you will rely heavily on these constructions. They are the building blocks of practical, everyday communication.

> — **Анна:** Скільки у тебе книжок у кімнаті? *(How many books do you have in your room?)*
> — **Марко:** У мене дуже багато книжок, але мало вільного часу. *(I have a lot of books, but little free time.)*
> — **Анна:** У цьому місті є багато парків? *(Are there many parks in this city?)*
> — **Марко:** Так, але там дуже мало дерев. *(Yes, but there are very few trees there.)*

Notice how «скільки» functions just like «багато» and «мало». When you ask someone «Скільки у тебе друзів?», you are structurally asking "How many of friends do you have?". 

<!-- INJECT_ACTIVITY: match-up-translate-genitive -->

<!-- INJECT_ACTIVITY: unjumble-genitive-phrases -->

When English speakers first learn negation, a common mistake is saying «У мене немає машина». Because English says "I don't have a car," it is tempting to leave the noun in its dictionary form. But in Ukrainian, «немає» is a unique grammatical marker of existence. It completely changes the structure of the sentence, demanding the Genitive case: «У мене немає машини». It is not simply a direct translation of the English word "no." 

:::info
**Grammar box** — The endings for masculine nouns in the Genitive singular (**-а** / **-у**) follow a specific, internal Ukrainian logic based on whether an object is concrete or abstract. These endings are distinct from other Slavic languages. Never guess an ending based on Russian; learn the Ukrainian patterns on their own terms.
:::

Він каже, що у нього зараз немає телефона. Вона думає, що в цьому немає сенсу. Ми бачимо, що тут немає швидкого прогресу.

> *He says that he does not have a phone right now. She thinks that there is no sense in this. We see that there is no fast progress here.*

## Підсумок — Summary

Let's review the three golden rules of this module. First, the word «немає» actively demands the Genitive case to show that an object is absent. Second, whenever you talk about quantities using words like «багато», «мало», or «кілька», you must use the Genitive plural. Third, the specific ending you choose depends on the gender of the noun, its stem, and whether it represents a concrete object or an abstract concept.

Коли ви використовуєте ці правила, ваша українська мова звучить природно. Ви знаєте, як сказати, що у вас немає часу або немає грошей. Це справжній фундамент для вільного спілкування.

> *When you use these rules, your Ukrainian sounds natural. You know how to say that you don't have time or don't have money. This is a true foundation for fluent communication.*

:::note
**Quick tip** — Focus on high-frequency words first. If you master everyday forms like «немає часу» and «багато грошей», the underlying patterns will naturally become clear over time.
:::

Before moving on to the next module, use this final checklist to test your understanding:
- Do you use **-а** or **-я** for concrete masculine objects (like «стола»)?
- Do you use **-у** or **-ю** for abstract masculine concepts (like «часу»)?
- Do you remember the fleeing vowel in feminine plurals (like «книжок»)?
- Can you correctly say you don't have money (using «грошей»)?
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
