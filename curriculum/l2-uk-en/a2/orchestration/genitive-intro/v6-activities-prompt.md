<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/genitive-intro.yaml` file for module **5: У мене немає...** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-possession-vs-absence-drill-vs -->`
- `<!-- INJECT_ACTIVITY: fill-in-genitive-singular-formation -->`
- `<!-- INJECT_ACTIVITY: match-up-genitive-plural -->`
- `<!-- INJECT_ACTIVITY: match-up-translations -->`
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
## Родовий відмінок: Коли чогось немає (The Genitive Case: When Something Isn't There) (~660 words)

Imagine you are moving into a new apartment, and you quickly realize that several essential things are missing. Let us listen to a conversation between a new tenant and her neighbor to see how Ukrainians talk about absence.

> — **Сусідка:** Добрий день! Як ваша нова квартира? *(Good day! How is your new apartment?)*
> — **Нова мешканка:** Добрий день. Квартира гарна, але тут нічого немає. *(Good day. The apartment is nice, but there is nothing here.)*
> — **Сусідка:** Як це нічого? *(What do you mean nothing?)*
> — **Нова мешканка:** У мене немає холодильника! Немає плити! Немає дзеркала! *(I have no fridge! No stove! No mirror!)*
> — **Сусідка:** Ого, це проблема. А що у вас є? *(Wow, that is a problem. And what do you have?)*
> — **Нова мешканка:** Є багато коробок, але дуже мало меблів. *(There are a lot of boxes, but very little furniture.)*

When you want to say that something does not exist or that you do not have something, Ukrainian uses a special grammatical form called the **родовий відмінок** (genitive case). This case answers the questions «кого?» (whom?) or «чого?» (what?). Its first and most important key function for beginners is expressing absence or non-existence using the construction with the word **немає** ((there) is not, (I) don't have). If you look closely at the dialogue above, you will notice that the new tenant did not use the basic dictionary forms of the words. Instead, she changed them to fit the grammatical rules of absence: «холодильник» became «холодильника», «плита» became «плити», and «дзеркало» became «дзеркала».

Родовий відмінок — це дуже важлива тема в українській граматиці. Коли ми кажемо слово «немає», іменник після нього завжди змінює своє закінчення. Це правило працює для всіх слів.

> *The Genitive case is a very important topic in Ukrainian grammar. When we say the word "немає", the noun after it always changes its ending. This rule works for all words.*

In English, negation does not change the form of the noun itself. You say "I have a brother" and "I do not have a brother." The word "brother" stays exactly the same. In Ukrainian, possession and absence are treated as structural opposites. When you possess something, you use the Nominative case, which is the standard dictionary form. When that thing is absent, you must shift to the Genitive case. The word «немає» is absolute and commands this grammatical change every single time.

У мене є старший брат. Це називний відмінок. Але мій друг каже, що у нього немає брата. Тут ми використовуємо родовий відмінок, бо говоримо про відсутність.

> *I have an older brother. This is the nominative case. But my friend says that he does not have a brother. Here we use the genitive case, because we are talking about absence.*

:::info
**Grammar box**
You will often hear Ukrainians use the short form **нема** instead of **немає** in everyday conversations. Both words mean exactly the same thing and both require the Genitive case.
:::

Let us practice this transformation with some simple sentences. You need to build the habit of automatically changing the noun whenever you use «немає» or «нема». Historically, this word comes from the Old East Slavic phrase meaning "not to have," making this case requirement a core structural feature of the language rather than just a random modern rule. It is so fundamental that you will even see it in famous Ukrainian proverbs.

У кімнаті є великий стіл. А в коридорі немає стола. На вулиці є зупинка автобуса. Біля парку немає зупинки. У природи нема поганої погоди. У нашому місті є театр, але немає метро.

> *There is a large table in the room. And in the hallway there is no table. There is a bus stop on the street. Near the park there is no stop. Nature has no bad weather. In our city there is a theater, but there is no subway.*

Notice how the words change their form: «стіл» (table) takes an «-а» ending, while «зупинка» (bus stop) changes its «-а» to an «-и». We will study the exact rules for every **закінчення** (ending (grammar)) in the next section, whether the noun is **однина** (singular) or **множина** (plural).

Before we dive into the full grammatical paradigm, there are several high-frequency abstract phrases that you should memorize immediately as fixed chunks. These are extremely useful in daily conversations. You will notice that some abstract masculine nouns take a «-у» or «-ю» ending instead of «-а».

Вибачте, але у мене зараз немає часу. Сьогодні у нас немає настрою працювати. Я думаю, що в цьому немає сенсу.

> *Sorry, but I do not have time right now. Today we are not in the mood to work. I think there is no point in this.*

By memorizing chunks like «немає часу» (no time), «немає настрою» (no mood), and «немає сенсу» (no sense/point), you can start speaking naturally right away. You will also need the Genitive case when talking about quantities with words like **багато** (a lot, many, much), **мало** (a little, few), **кілька** (a few, several), and when asking **скільки** (how many, how much). We will explore quantities later, but first, let us practice the difference between having something and not having it.

<!-- INJECT_ACTIVITY: quiz-possession-vs-absence-drill-vs -->

## Закінчення родового відмінка однини (Genitive Singular Endings) (~770 words)

Now that you understand when to use the Genitive case, we need to learn how to form it. We will look at the **закінчення** (ending (grammar)) for each gender in the **однина** (singular). The most straightforward group is the neuter gender. For neuter nouns, the rule is simple: words ending in «-о» change to «-а», and words ending in «-е» change to «-я». Words that already end in «-я» keep their «-я» ending.

У моїй кімнаті є велике вікно. Але в коридорі немає вікна. Це Чорне море. У нашому місті немає моря. Я люблю спокійне життя. Без тебе немає спокійного життя.

> *In my room there is a large window. But in the hallway there is no window. This is the Black Sea. In our city there is no sea. I love a peaceful life. Without you there is no peaceful life.*

Notice how «вікно» becomes «вікна», and «море» becomes «моря». This predictable pattern makes neuter nouns very easy to manage.

Next, let us look at feminine nouns, which typically end in «-а» or «-я». The Genitive ending depends on whether the final consonant before the ending is hard or soft. For hard stems ending in «-а», the ending changes to «-и». For soft stems ending in «-я», the ending changes to «-і» or «-ї». 

:::note
**Quick tip**
Feminine words ending in a hissing consonant plus «-а» (like груш**а**, меж**а**) belong to a mixed group. They always take the soft ending **-і** in the Genitive case.
:::

Моя нова машина дуже швидка. У мого брата немає машини. Моя сестра живе в Києві. Сьогодні вдома немає сестри. Ця книга дуже цікава. У бібліотеці немає цієї книги. Це наша рідна земля. На карті немає цієї землі. Гарна пісня лунає по радіо. У моєму плейлисті немає цієї пісні. Велика сім'я збирається за столом. У нього немає сім'ї. На столі лежить солодка груша. У мене немає груші.

> *My new car is very fast. My brother does not have a car. My sister lives in Kyiv. Today my sister is not at home. This book is very interesting. The library does not have this book. This is our native land. This land is not on the map. A beautiful song sounds from the radio. My playlist does not have this song. A large family gathers at the table. He does not have a family. A sweet pear lies on the table. I do not have a pear.*

Remember: hard «-а» becomes «-и» (машина → машини), while soft «-я» becomes «-і» or «-ї» (земля → землі, сім'я → сім'ї).

Now we arrive at the masculine nouns. This is often considered the biggest challenge in Ukrainian grammar. Unlike feminine and neuter nouns, masculine nouns that end in a consonant can take either an «-а»/«-я» ending or an «-у»/«-ю» ending. The choice depends entirely on the meaning of the word.

Це мій старший брат. У мене немає брата. Там стоїть великий стіл. У кімнаті немає стола. Це мій новий комп'ютер. У мене немає комп'ютера. Київ — велике місто. На цій карті немає Києва.

> *This is my older brother. I do not have a brother. There stands a large table. There is no table in the room. This is my new computer. I do not have a computer. Kyiv is a large city. There is no Kyiv on this map.*

Notice that words like «брат» (brother), «стіл» (table), and «Київ» (Kyiv) all take the «-а» ending. We use «-а» or «-я» for concrete, specific, and animate items. This includes people, animals, distinct objects you can touch, and names of cities.

Мені потрібен час. На жаль, у мене немає часу. Я люблю солодкий чай. У моїй каві немає цукру. Надворі сильний вітер. Сьогодні немає вітру. Це великий прогрес. У нашій роботі немає прогресу.

> *I need time. Unfortunately, I do not have time. I like sweet tea. There is no sugar in my coffee. There is a strong wind outside. Today there is no wind. This is a great progress. There is no progress in our work.*

Here, words like «час» (time), «цукор» (sugar), and «вітер» (wind) take the «-у» ending. We use «-у» or «-ю» for abstract concepts, substances, materials, natural phenomena, and institutions. Do not worry about memorizing every exception right now. Your goal at the A2 level is to focus on high-frequency words. Perfect mastery of masculine endings is a long-term goal for the B1 and B2 levels.

:::info
**Grammar box**
When in doubt about a masculine noun, think about whether you can physically pick up the object and count it. If yes (like a phone or a table), it usually takes **-а**. If it is an abstract concept, a liquid, or a powder (like love, juice, or sand), it usually takes **-у**.
:::

Finally, we have a smaller group of feminine nouns that end in a consonant instead of a vowel. These are words like «ніч» (night), «сіль» (salt), and «любов» (love). For this group, the Genitive singular ending is always «-і».

Сьогодні дуже тепла ніч. Влітку немає холодної ночі. Це морська сіль. У цьому супі немає солі. Материнська любов дуже сильна. Без довіри немає любові. Моя мати працює в школі. На фотографії немає матері.

> *Today is a very warm night. In summer there is no cold night. This is sea salt. There is no salt in this soup. A mother's love is very strong. Without trust there is no love. My mother works at school. The mother is not in the photograph.*

Notice that «мати» (mother) is an important exception. It takes the suffix «-ер-» before the ending, becoming «матері». For all other nouns in this category, simply add «-і» to the end of the word.

Let us consolidate the rules with a concise summary chart. Recognizing these patterns is much more important than perfect memorization at this stage.

| Рід (Gender) | Базове закінчення (Basic Ending) | Родовий відмінок (Genitive) | Приклад (Example) |
| :--- | :--- | :--- | :--- |
| **Середній** (Neuter) | -о, -е, -я | **-а, -я** | вікн**о** → вікн**а**, мор**е** → мор**я** |
| **Жіночий** (Feminine) | -а, -я | **-и, -і, -ї** | машин**а** → машин**и**, сім'**я** → сім'**ї** |
| **Жіночий** (Fem. Consonant) | приголосний (consonant) | **-і** | сіл**ь** → сол**і**, ніч → ноч**і** |
| **Чоловічий** (Masculine) | приголосний, -о | **-а/-я** АБО **-у/-ю** | брат → брат**а**, час → час**у** |

<!-- INJECT_ACTIVITY: fill-in-genitive-singular-formation -->

## Коли є багато або мало (When There Is a Lot or a Little) (~770 words)

We have already seen how to use the **родовий відмінок** (genitive case) when something is entirely absent. However, this case is also essential when we want to talk about quantity. Whenever you want to express that there is a large or small amount of something, you must use a new form. This happens after specific words like **багато** (a lot, many, much) and **мало** (a little, few).

В українській мові ми завжди змінюємо слово після таких слів. Коли ви говорите про велику кількість предметів або людей, форма слова стає іншою. У мене є багато друзів, але зараз у мене мало часу.

> *In the Ukrainian language, we always change the word after such words. When you talk about a large quantity of objects or people, the form of the word becomes different. I have many friends, but right now I have little time.*

You will also use this exact same grammatical structure when asking questions about quantity, or when indicating an imprecise number. Words such as **кілька** (a few, several) and **скільки** (how many, how much) trigger this change. When we talk about multiple countable objects, we use the form called **множина** (plural).

Скільки студентів сьогодні в аудиторії? На столі лежить кілька зошитів. Ми бачимо багато великих будинків.

> *How many students are in the classroom today? There are a few notebooks lying on the table. We see many large buildings.*

Forming the plural in the Genitive case can seem challenging at first, as there are different patterns depending on the gender of the noun. The form for **однина** (singular) is no longer enough to express these ideas. Let us start with masculine nouns, which generally follow a very predictable and consistent pattern. For most masculine nouns ending in a consonant, the **закінчення** (ending (grammar)) in the Genitive plural is «-ів» або «-їв».

Більшість іменників чоловічого роду отримують закінчення «-ів». Один брат — це називний відмінок, а кілька братів — це родовий відмінок. Якщо слово закінчується на голосний або м'який знак, ми додаємо «-їв». Наприклад, один трамвай стає багато трамваїв.

> *Most masculine nouns receive the "-ів" ending. One brother is the Nominative case, and a few brothers is the Genitive case. If the word ends in a vowel or a soft sign, we add "-їв". For example, one tram becomes many trams.*

:::info
**Grammar box**
This rule applies not only to quantity words, but also to numbers. In Ukrainian, numbers from five upwards act like quantity words and require the Genitive plural. So, we say «один брат» (one brother), but «п'ять братів» (five brothers). This is an ancient feature of Slavic languages where numbers were originally treated as nouns meaning "a group of."
:::

While masculine nouns usually add a visible suffix, feminine and neuter nouns often do the exact opposite. To form the Genitive plural for these words, we typically remove the final vowel, leaving what linguists call a zero ending.

Для іменників жіночого та середнього роду ми часто просто забираємо останню букву. Слово «машина» стає «машин». Слово «озеро» перетворюється на «озер». У місті є багато великих площ і широких вулиць.

> *For feminine and neuter nouns, we often simply remove the last letter. The word "машина" (car) becomes "машин". The word "озеро" (lake) turns into "озер". In the city, there are many large squares and wide streets.*

Sometimes, removing the final vowel leaves two consonants together at the end of the word, which can be difficult to pronounce. When this happens, the Ukrainian language naturally inserts a fleeting vowel—usually «о» or «е»—between those consonants to make the word sound melodic and smooth.

Якщо в кінці слова залишаються два приголосні звуки, між ними з'являється голосний. Наприклад, слово «сестра» змінюється на «сестер». Слово «вікно» має форму «вікон». Слово «книга» може бути «книг», але слово «книжка» завжди перетворюється на «книжок».

> *If two consonant sounds remain at the end of the word, a vowel appears between them. For example, the word "сестра" (sister) changes to "сестер". The word "вікно" (window) has the form "вікон". The word "книга" (book) can be "книг", but the word "книжка" (book) always turns into "книжок".*

Instead of trying to memorize complex mathematical rules for when to insert vowels, it is much more effective to treat these common plural forms as individual vocabulary items. With practice, your ear will naturally expect the extra vowel. There is also a smaller, yet highly frequent, group of nouns that take the ending «-ей» in the Genitive plural. This group includes certain masculine and neuter nouns, plural-only nouns, and feminine nouns ending in a consonant.

Деякі дуже важливі слова завжди мають закінчення «-ей». Слово «гість» стає «гостей», а «кінь» перетворюється на «коней». Слово «око» має форму «очей». Це треба просто запам'ятати.

> *Some very important words always have the "-ей" ending. The word "гість" (guest) becomes "гостей", and "кінь" (horse) turns into "коней". The word "око" (eye) has the form "очей". This simply needs to be memorized.*

The most common plural-only word you will use every day—money—also uses this exact ending. Let's look at a practical dialogue to see how the negative structure **немає** ((there) is not, (I) don't have) works with these plural forms in real life.

> — **Анна:** Ти хочеш піти в кіно сьогодні? *(Do you want to go to the cinema today?)*
> — **Марк:** Вибач, я не можу. У мене зараз немає грошей. *(Sorry, I cannot. I don't have any money right now.)*
> — **Анна:** Нічого, я можу купити квитки. *(It's okay, I can buy the tickets.)*
> — **Марк:** Дякую! Але після таких довгих ночей я хочу просто спати. *(Thank you! But after such long nights I just want to sleep.)*

Now that you have seen the different endings, it is time to integrate these concepts. The true test of your grammar skills is combining negation with quantity expressions and plural nouns in the same sentence. A very common mistake among English speakers is keeping the noun in the singular form after numbers or quantity words, saying something like "п'ять книга" instead of using the correct plural case.

Завжди звертайте увагу на слова, які означають кількість. Якщо ви кажете «багато», іменник повинен змінитися. У мене є кілька нових книжок, але зовсім немає вільного часу їх читати.

> *Always pay attention to words that mean quantity. If you say "багато" (a lot), the noun must change. I have a few new books, but I have absolutely no free time to read them.*

:::tip
**Quick tip**
Do not stress about getting every single fleeting vowel or abstract ending perfectly right in conversation. Native speakers will always understand you if you use the wrong ending. Focus on recognizing the high-frequency forms like «грошей» (money), «людей» (people), «років» (years), and «друзів» (friends). Perfecting the entire system is a long-term goal!
:::

Mastering the Genitive plural will unlock your ability to talk freely about shopping, groups of people, distances, and absence. Practice combining these elements deliberately, and soon the patterns will feel like second nature. Let's review a few more examples.

Він має багато ідей, але в нього немає хороших працівників. Скільки кілометрів до наступного міста? На вулиці мало машин, тому що сьогодні неділя.

> *He has many ideas, but he has no good workers. How many kilometers to the next city? There are few cars on the street because today is Sunday.*

<!-- INJECT_ACTIVITY: match-up-genitive-plural -->
<!-- INJECT_ACTIVITY: match-up-translations -->
<!-- INJECT_ACTIVITY: unjumble-genitive-phrases -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: genitive-intro
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
