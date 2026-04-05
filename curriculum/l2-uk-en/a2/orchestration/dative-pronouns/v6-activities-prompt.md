<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-pronouns.yaml` file for module **17: Мені, тобі, йому...** (a2).

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

- focus: Match nominative pronoun to its dative form (я→мені, ти→тобі, etc.)
  items: 8
  type: match-up
- focus: Complete sentences with the correct dative pronoun based on context
  items: 8
  type: fill-in
- focus: Choose dative or accusative pronoun form in context (тобі vs. тебе)
  items: 8
  type: quiz
- focus: Judge whether impersonal dative sentences (мені холодно, мені бачу) are correct
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- приємно (pleasant)
- цікаво (interesting)
- сумно (sad (impersonal state))
- важко (difficult, hard)
required:
- давальний відмінок (dative case)
- мені (to me)
- тобі (to you (informal))
- йому (to him, to it)
- їй (to her)
- нам (to us)
- вам (to you (formal/plural))
- їм (to them)
- холодно (cold (impersonal state))
- потрібно (necessary, needed)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Давальний відмінок: Кому? (The Dative Case: To Whom?)

Welcome to the **давальний відмінок** (dative case). Think of the dative case as the "recipient" case. In any situation where there is a giver and a receiver, the person receiving the action or object takes the dative case. Imagine you are holding a wrapped gift. You are the giver, the gift is the object, and the friend receiving the gift is the recipient. In Ukrainian, that friend's name or pronoun must change to show they are the destination of your action. The primary questions for the dative case are **Кому?** (To whom?) and **Чому?** (To what?).

> — **Олена:** Кому ти купуєш цей подарунок? *(To whom are you buying this gift?)*
> — **Марко:** Я купую подарунок братові. *(I am buying a gift for my brother.)*
> — **Олена:** А що ти даруєш сестрі? *(And what are you gifting to your sister?)*
> — **Марко:** Сестрі я дарую нову книгу. *(To my sister, I am gifting a new book.)*

**Читаємо українською:**
«Це мій брат. Я даю телефон братові. Це моя сестра. Я даю телефон сестрі. Кому ти даєш свій телефон? Я ніколи не даю телефон собаці!» *(This is my brother. I give the phone to my brother. This is my sister. I give the phone to my sister. To whom do you give your phone? I never give the phone to a dog!)*

To understand the **давальний відмінок**, let's contrast it with the cases you already know. The **називний відмінок** (nominative case) is the doer of the action. The **знахідний відмінок** (accusative case) is the direct target or the "thing" being acted upon. The dative case is the indirect object, the one who benefits from or receives the "thing". Let's look at the verb **давати** (to give). If you give a book to your mom, the mom is the recipient. If you give food to a cat, the cat is the recipient. If you give money to a seller, the seller is the recipient.

**Читаємо українською:**
«Мама читає. Я даю книгу мамі. Кіт хоче їсти. Я даю корм коту. Продавець чекає. Я даю гроші продавцеві. Студент слухає. Вчитель дає завдання студенту.» *(Mom is reading. I give a book to mom. The cat wants to eat. I give food to the cat. The seller is waiting. I give money to the seller. The student is listening. The teacher gives a task to the student.)*

> — **Тарас:** Ти вже дав гроші касиру? *(Did you already give money to the cashier?)*
> — **Анна:** Ні, я дала гроші менеджеру. *(No, I gave money to the manager.)*
> — **Тарас:** А що ти дала брату? *(And what did you give to your brother?)*
> — **Анна:** Брату я дала тільки чек. *(To my brother I gave only the receipt.)*

While the accusative case usually carries the "thing" being acted upon, the dative case carries the "person" who benefits or receives information. When you learn new verbs, notice if they direct an action toward a person. Here are five essential verbs that trigger the dative case: **казати** (to say / to tell), **дарувати** (to gift), **телефонувати** (to call by phone), **допомагати** (to help), and **показувати** (to show). You tell *to* someone, you gift *to* someone, you call *to* someone, you help *to* someone, and you show *to* someone. 

**Читаємо українською:**
«Я хочу сказати правду другові. Ми даруємо квіти мамі. Коли ти телефонуєш бабусі? Вона часто допомагає дідусеві. Вчитель показує карту учню. Вони дарують комп'ютер сину.» *(I want to tell the truth to my friend. We gift flowers to mom. When do you call grandma? She often helps grandpa. The teacher shows the map to the student. They gift a computer to their son.)*

> — **Ігор:** Кому ти зараз телефонуєш? *(Who are you calling right now?)*
> — **Марія:** Я телефоную своєму лікарю. *(I am calling my doctor.)*
> — **Ігор:** Що ти хочеш сказати лікарю? *(What do you want to tell the doctor?)*
> — **Марія:** Я хочу сказати йому, що мені краще. *(I want to tell him that I am better.)*

The dative case isn't just for physical objects; it is crucial for communication and support. These are abstract exchanges. When you say, "I tell you the truth," the truth is the direct object, but "you" are the recipient of the information. When you say, "He helps us," the help is directed toward "us". The question **чому?** (to what?) is used for objects and concepts, but at the A2 level, our primary focus is on **кому?** (to whom?) because we mostly interact with people. Think of the dative as building a bridge between the doer of the action and the person receiving its effects.

**Читаємо українською:**
«Я кажу тобі правду. Він допомагає нам працювати. Вона телефонує подрузі щодня. Ми даруємо радість людям. Ти показуєш дорогу туристу. Ви допомагаєте студентам розуміти граматику.» *(I tell you the truth. He helps us work. She calls her friend every day. We gift joy to people. You show the way to the tourist. You help students understand grammar.)*


## Особові займенники у давальному відмінку (Personal Pronouns in the Dative)

**Читаємо українською:** «Сьогодні свято. Родина дарує подарунки.» *(Today is a holiday. The family is giving gifts.)*

> — **Іменинник:** Дякую всім за свято! Я бачу багато подарунків. Кому вони? *(Thank you all for the holiday! I see many gifts. For whom are they?)*
> — **Мама:** Мені — книгу, тобі — шоколад, йому — теплий шарф, а їй — красиві квіти. *(For me — a book, for you — chocolate, for him — a warm scarf, and for her — beautiful flowers.)*
> — **Батько:** А що ми даруємо бабусі і дідусеві? Що ми даруємо їм? *(And what are we gifting to grandma and grandpa? What are we gifting to them?)*
> — **Мама:** Їм ми даруємо телевізор. Вони люблять новини. *(To them we are gifting a TV. They love news.)*
> — **Іменинник:** А що ви даєте нам? *(And what are you giving to us?)*
> — **Мама:** Нам усім — великий торт! Давайте пити чай! *(To all of us — a big cake! Let's drink tea!)*

In the dialogue above, you can clearly see how personal pronouns change when they become the recipient of an action. The word **я** (I) completely transforms into **мені** (to me), and **ти** (you) becomes **тобі** (to you). Notice that these dative forms look entirely different from their nominative counterparts. Unlike regular noun endings, which often follow predictable phonetic patterns, the personal pronouns in the dative case require rote memorization. They are ancient, irregular forms. You simply have to learn them as a completely new set of vocabulary words. There is no shortcut, but they will quickly become second nature.

**Читаємо українською:** «Я читаю книгу. Дай мені книгу. Ти п'єш каву. Я роблю тобі каву.» *(I am reading a book. Give me the book. You are drinking coffee. I am making you coffee.)*

Here is the full paradigm of personal pronouns in the dative case. Read them aloud to build muscle memory:

*   **я** (I) → **мені** (to me)
*   **ти** (you, sing.) → **тобі** (to you, sing.)
*   **він** (he) / **воно** (it) → **йому** (to him / to it)
*   **вона** (she) → **їй** (to her)
*   **ми** (we) → **нам** (to us)
*   **ви** (you, pl./formal) → **вам** (to you, pl./formal)
*   **вони** (they) → **їм** (to them)

To make memorization easier, notice a few helpful patterns. First, the singular forms **мені** and **тобі** rhyme perfectly. Whenever you think of one, remember that the other sounds identical at the end. Second, the plural forms **нам** and **вам** share the **-ам** ending, typical for plural nouns in the dative case. Finally, the third-person forms **їй** (to her) and **їм** (to them) are very short but distinct from each other: one is singular, and one is plural. The masculine and neuter forms share the exact same word: **йому**.

**Читаємо українською:** «Він любить музику. Ми купуємо йому гітару. Вона любить спорт. Ми даруємо їй м'яч. Мама дає нам борщ. Я допомагаю вам. Викладач пояснює їм правила.» *(He loves music. We buy him a guitar. She loves sport. We gift her a ball. Mom gives us borscht. I help you. The teacher explains rules to them.)*

Let's focus closely on the third-person pronouns: **йому** (to him/it), **їй** (to her), and **їм** (to them). These specific forms have a special behavior. In simple sentences where they act as the recipient without any prepositions, they stay exactly as they are: **йому**, **їй**, **їм**. However, if you add a preposition before them, they gain an initial **н-**. For example, when you use the genitive preposition **до** (to), you say «Я йду до нього» (I go to him). But in the dative case, without a preposition, it is simply «Я дзвоню йому» (I call him).

**Читаємо українською:** «Я пишу листа їй. Я йду в гості до неї. Ми даємо гроші їм. Ми працюємо для них. Вчитель дає зошит йому.» *(I write a letter to her. I go to visit her. We give money to them. We work for them. The teacher gives a notebook to him.)*

<!-- INJECT_ACTIVITY: match-up, Match nominative pronoun to its dative form -->

The dative case is particularly important for verbs of communication. In English, you might say "I call him" or "I tell him," using the standard direct object pronoun. In Ukrainian, these actions are viewed as sending information *to* someone, so they always require the dative case. The verb **телефонувати** (to call by phone) strictly takes the dative. You cannot say «Я телефоную тебе» (using the Accusative case); you absolutely must say «Я телефоную тобі» (using the Dative case). The same rule applies to verbs like **писати** (to write) and **розповідати** (to tell).

**Читаємо українською:** «Я часто телефоную йому вранці. Ти ніколи не дзвониш мені. Вона пише їм довгі листи. Ми розповідаємо вам історію. Ви завжди кажете нам правду. Бабуся розповідає їй казку.» *(I often call him in the morning. You never call me. She writes them long letters. We tell you a story. You always tell us the truth. Grandma tells her a fairy tale.)*

Notice how the action flows toward the pronoun. The person is the receiver of the call, the message, or the story. Mastering these communication verbs with dative pronouns will make your conversational Ukrainian sound much more natural.

<!-- INJECT_ACTIVITY: fill-in, Complete sentences with the correct dative pronoun based on context -->


## Мені холодно: Безособові конструкції (Impersonal Constructions with Dative)

In English, when you describe how you feel, you usually use a subject and an adjective: "I am cold." In Ukrainian, physical and emotional states are frequently expressed using a completely different structure called an impersonal sentence. Instead of saying "I am cold," you say that "it is cold to me." This structure uses a simple, powerful formula: **Dative Pronoun + Adverb/Predicate**. There is no nominative subject doing an action. The person experiencing the state is placed in the dative case. The most common and useful example is **Мені холодно** *(I am cold / It is cold to me)*. 

:::tip Безособові конструкції (Impersonal Constructions)
**Кому?** (To whom?) + **Як?** (How?)
мені + холодно
тобі + тепло
йому + весело
їй + сумно
:::

**Читаємо українською:**
«На вулиці зима, і мені дуже холодно. Тобі холодно без куртки? Йому не холодно, бо він п'є гарячий чай. Їй холодно спати. Нам завжди холодно восени, але влітку добре. Вам тут не холодно? Їм холодно чекати автобус на зупинці.» 
*(It is winter outside, and I am very cold. Are you cold without a jacket? He is not cold, because he is drinking hot tea. She is cold sleeping. We are always cold in autumn, but in summer it is good. Are you not cold here? They are cold waiting for the bus at the stop.)*

Once you understand this formula, you can express a wide variety of states just by changing the adverb. If you want to say you are warm, you use **тепло** *(warm)*. If you are hot, you use **жарко** *(hot)*. Emotional states work exactly the same way. You can use words like **весело** *(cheerful/fun)*, **сумно** *(sad)*, **цікаво** *(interesting)*, **нудно** *(boring)*, **важко** *(hard/difficult)*, and **легко** *(easy)*. All of these words combine seamlessly with the dative pronouns you just learned. You don't need to change the endings of these adverbs based on gender or number, because there is no subject to agree with!

**Читаємо українською:**
«Влітку мені жарко, а навесні тепло. Тобі весело на вечірці? Ні, мені тут дуже нудно. Йому важко читати цей текст, а їй легко. Нам цікаво вивчати українську мову. Чому вам сумно сьогодні? Їм весело грати в парку.»
*(In summer I am hot, and in spring I am warm. Are you having fun at the party? No, I am very bored here. It is hard for him to read this text, but easy for her. It is interesting for us to learn the Ukrainian language. Why are you sad today? It is fun for them to play in the park.)*

> — **Олена:** Привіт, Антоне. Чому тобі так сумно? *(Hi, Anton. Why are you so sad?)*
> — **Антон:** Мені нудно читати цю книгу. *(It is boring for me to read this book.)*
> — **Олена:** А мені дуже цікаво! *(And for me it is very interesting!)*

Beyond physical and emotional states, the dative case is strictly required for three incredibly important functional words: **потрібно** *(necessary/need)*, **можна** *(allowed)*, and **не можна** *(forbidden/not allowed)*. In English, you say "I need to go," treating "need" as a normal verb attached to "I". In Ukrainian, the concept is closer to "It is necessary for me to go." Therefore, you must use the dative pronoun. You cannot say «Я потрібно», you must say **Мені потрібно**. Similarly, asking for permission or stating rules requires the dative person plus **можна** or **не можна**. 

**Читаємо українською:**
«Мені потрібно йти додому, бо вже пізно. Тобі можна пити каву вранці? Йому не можна їсти цукор. Їй потрібно купити квиток на поїзд. Нам можна тут сидіти і читати. Вам потрібно працювати сьогодні? Їм не можна курити в кімнаті. Що мені потрібно робити завтра?»
*(I need to go home, because it is already late. Are you allowed to drink coffee in the morning? He is not allowed to eat sugar. She needs to buy a ticket for the train. We are allowed to sit here and read. Do you need to work today? They are not allowed to smoke in the room. What do I need to do tomorrow?)*

> — **Охоронець:** Вибачте, але вам не можна тут стояти. *(Excuse me, but you are not allowed to stand here.)*
> — **Студент:** Чому? Мені потрібно чекати друга. *(Why? I need to wait for a friend.)*
> — **Охоронець:** Вам можна чекати на вулиці. *(You are allowed to wait outside.)*

It is important to understand the difference between describing a person directly and describing a state using the dative case. You can say **Я втомлена** *(I am tired)* using a nominative subject and an adjective that agrees with your gender. This describes your direct, personal characteristic in that moment. However, if you say **Мені важко** *(It is hard for me)*, the dative construction feels more objective or external. It describes the situation acting upon you, rather than your internal identity. The situation is difficult, and you are the recipient of that difficulty. This external perspective is deeply embedded in the Ukrainian mindset. It highlights that feelings and circumstances often happen *to* us. Let's look at a dialogue at the cinema to see how these states flow naturally in conversation.

> — **Катерина:** Тобі цікаво дивитися цей фільм? *(Is it interesting for you to watch this movie?)*
> — **Тарас:** Так, мені дуже цікаво. А тобі? *(Yes, it is very interesting to me. And to you?)*
> — **Катерина:** А мені нудно. Фільм довгий, і мені важко сидіти. *(And I am bored. The movie is long, and it is hard for me to sit.)*
> — **Тарас:** Тобі холодно? *(Are you cold?)*
> — **Катерина:** Ні, мені тепло, але я дуже втомлена. Мені потрібно спати. *(No, I am warm, but I am very tired. I need to sleep.)*
> — **Тарас:** Добре, нам можна йти додому зараз. *(Okay, we can go home now.)*

<!-- INJECT_ACTIVITY: true-false, Judge whether impersonal dative sentences (мені холодно, мені бачу) are correct -->


## Давальний чи знахідний? (Dative or Accusative?)

It is very common to confuse the accusative case (direct object) and the dative case (indirect object or recipient). In English, both are just "me", "you", "him", or "her". In Ukrainian, you must choose the correct form based on the verb's logic. Let's look at some minimal pairs to see the difference between a direct target and a recipient.

**Читаємо українською:**
«Я бачу тебе.» *(I see you.)* — Accusative. You are the direct target of my vision.
«Я кажу тобі правду.» *(I am telling you the truth.)* — Dative. You are the recipient of the truth.
«Він кохає її.» *(He loves her.)* — Accusative. She is the direct object of his love.
«Він дарує їй квіти.» *(He gives her flowers.)* — Dative. She is the recipient of the flowers.
«Вона чекає його.» *(She is waiting for him.)* — Accusative. He is the direct target of her waiting.
«Вона пише йому повідомлення.» *(She is writing him a message.)* — Dative. He is the recipient of the message.

To decide which case to use, try the "Direct vs. Indirect" test. Ask yourself: is the person the actual thing being moved, seen, grabbed, or known? If yes, use the accusative case. Or is the person just standing there receiving a message, a gift, or an explanation? If they are a recipient or a beneficiary, use the dative case.

Let's test this with the verb **знати** *(to know)*. You know a person directly. You do not give knowledge to them; you just know them. Therefore, it takes the accusative case: **Я знаю його** *(I know him)*. Now compare this to **допомагати** *(to help)*. You give your help to someone. They receive it. Therefore, it takes the dative case: **Я допомагаю йому** *(I am helping him)*. 

> — **Анна:** Ти знаєш його? *(Do you know him?)*
> — **Марко:** Так, я знаю його дуже добре. *(Yes, I know him very well.)*
> — **Анна:** Ти можеш допомогти йому? *(Can you help him?)*
> — **Марко:** Звичайно, я допоможу йому завтра. *(Of course, I will help him tomorrow.)*

Notice the difference between hearing someone (direct target) and calling someone (directing a call to a recipient) in this conversation.

> — **Олег:** Ти чуєш мене? *(Do you hear me?)*
> — **Ірина:** Так, я чую тебе добре. *(Yes, I hear you well.)*
> — **Олег:** Чому ти не дзвониш мені? *(Why don't you call me?)*
> — **Ірина:** Я дзвонила тобі вчора, але ти не відповідав. *(I called you yesterday, but you did not answer.)*

<!-- INJECT_ACTIVITY: quiz, Choose dative or accusative pronoun form in context (тобі vs. тебе, її vs. їй) -->


## Підсумок (Summary)

У цьому модулі ми вивчили давальний відмінок особових займенників. *(In this module, we learned the dative case of personal pronouns.)* The dative case is absolutely essential for expressing who receives an action or who experiences a physical or emotional state. It transforms the direct nominative pronouns into their indirect forms, allowing us to build more complex and natural sentences.

Let's review the complete paradigm one more time to make sure you remember every form:
- **я** *(I)* → **мені** *(to me)*
- **ти** *(you)* → **тобі** *(to you)*
- **він** / **воно** *(he / it)* → **йому** *(to him / to it)*
- **вона** *(she)* → **їй** *(to her)*
- **ми** *(we)* → **нам** *(to us)*
- **ви** *(you)* → **вам** *(to you)*
- **вони** *(they)* → **їм** *(to them)*

**Читаємо українською:**
«Мені дуже подобається ця нова книга.» *(I really like this new book.)*
«Ми даємо вам наші старі ключі.» *(We are giving you our old keys.)*
«Йому дуже сумно сьогодні вранці.» *(He is very sad this morning.)*
«Я телефоную їй щодня після роботи.» *(I call her every day after work.)*
«Вони пишуть нам довгі повідомлення.» *(They write us long messages.)*

Before moving to the next module, ask yourself these three quick self-check questions:

1. **Яке питання ставить давальний відмінок?** *(What question does the dative case ask?)*
   **Відповідь:** Кому? *(To whom?)*
2. **Як сказати "I need" українською?** *(How to say "I need" in Ukrainian?)*
   **Відповідь:** Мені потрібно. *(Literally: To me it is necessary.)*
3. **Яка різниця між "бачу її" та "дзвоню їй"?** *(What is the difference between "I see her" and "I am calling her"?)*
   **Відповідь:** «Бачу її» *(I see her)* uses the accusative case because she is the direct target of your vision. «Дзвоню їй» *(I am calling her)* uses the dative case because she is merely the recipient of your phone call.

Finally, make sure you know the five most important dative verbs from this module:
- **давати** *(to give)*
- **казати** *(to tell, to say)*
- **дарувати** *(to gift, to give a present)*
- **телефонувати** / **дзвонити** *(to call on the phone)*
- **допомагати** *(to help)*

**Читаємо українською:**
«Я хочу допомогти тобі завтра.» *(I want to help you tomorrow.)*
«Що ти можеш подарувати їм на свято?» *(What can you gift them for the holiday?)*
«Будь ласка, скажи нам усю правду.» *(Please, tell us the whole truth.)*
«Мама дає мені смачне яблуко.» *(Mom gives me a tasty apple.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-pronouns
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

**Level: A2 (Module 17/60) — ELEMENTARY**

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
