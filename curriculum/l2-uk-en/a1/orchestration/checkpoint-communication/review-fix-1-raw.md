✅ Message sent to Gemini (ID: 21280) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #21280...
📨 Message #21280
   From: gemini → To: gemini
   Type: query
   Task: checkpoint-communication-review-fix-1
   Time: 2026-03-06T07:41:18.012720+00:00

============================================================

# Gemini Review Fix: Targeted Repair via FIND/REPLACE

> **You are an expert Ukrainian language editor applying targeted fixes.**
> You have NO tools — output FIND/REPLACE pairs only.
> The build system will apply your fixes programmatically.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original.
- **PRESERVE the author's intent.** Rewrite poorly explained content to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your fixes should read like the original author wrote them on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information).

---

## Fix Plan (from review)

## Critical Issues Found

### Issue 1: Russianism in imperative forms
**Location**: Section "Огляд", "Навичка 3", "Інтеграційне завдання", and multiple activities.
**Problem**: The text teaches the Russian grammatical calque for the 1st person plural imperative: "Дава́й пообі́даємо", "Дава́й зустрі́немось", "Дава́й пої́демо". Standard Ukrainian uses the synthetic form ending in -мо.
**Fix**: Replace with standard Ukrainian imperatives: "Пообі́даймо", "Зустрі́ньмося", and "Пої́дьмо". Update related unjumble and true-false activities to match.

### Issue 2: Fabricated word forms as distractors
**Location**: Activities -> `Complete the Sentences` -> Item 7 ("Нам ___ купити квитки сьогодні.")
**Problem**: The word "треба" is an undeclinable predicative word. The activity options include hallucinated declined forms: `"требу", "требом", "требі"`. This triggered VESUM failures and exposes beginners to false morphology.
**Fix**: Use actual modal verbs or related words as distractors, e.g., `"треба", "можна", "повинен", "хочу"`.

### Issue 3: Grammatically invalid nominative distractors
**Location**: Activities -> `Complete the Sentences` -> Item 1 ("Я хочу поїхати в ___.")
**Problem**: The preposition "в" here requires the accusative case. The correct answer "подорож" works, but the distractors `"школа", "робота", "книга"` are strictly nominative. If a student selects them, it forms ungrammatical phrases ("в школа").
**Fix**: Change distractors to valid accusative targets (e.g., `"школу", "роботу"`) or inanimate masculine nouns (e.g., `"парк", "центр"`).

---

## Ukrainian Language Issues

The primary issue is the structural calque from Russian ("Давай поїдемо" instead of "Поїдьмо"). Ukrainian has a rich synthetic imperative mood that should be modeled from the beginning rather than relying on colloquial Russianisms. Additionally, ensuring that multiple-choice distractors reflect valid morphological possibilities (e.g., not declining the undeclinable "треба") is critical for clean language input.

---

## Fix Plan to Reach 9.5/10

1. Replace all instances of "Давай" + 1st person plural future with standard Ukrainian synthetic imperatives ending in "-мо".
2. Fix the illogical distractors for "треба" in the "Complete the Sentences" activity.
3. Update the distractors in the first "Complete the Sentences" question so they align with the required accusative case.
4. Replace the English translation for "Давай!" in the first dialogue with a natural equivalent like "Згода!" (Agreed!).

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 2005/1200 (raw: 2306) | pedagogy: 1 violations
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-communication-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-communication.md`

```markdown
<!-- SCOPE
Covers: Consolidating A1.5 skills (modal verbs, imperative mood, everyday life routines, and basic travel planning)
Not covered:
  - Future tense conjugation
  - Complex grammatical cases (Dative and Instrumental are treated as fixed lexical chunks)
-->

# Checkpoint: Communication

> **Чому це важливо?**
>
> You have learned how to talk about your abilities, give polite instructions, and describe your everyday life. Now it is time to put all these pieces together. Real communication is about combining these skills naturally.

## Огляд: Checkpoint Communication

Приві́т! Ви чудово працюєте. (Hello! You are working wonderfully.) Ви вже знаєте багато. (You already know a lot.)

We have reached an important milestone in your learning journey. You can now talk about what you want, what you can do, and what you need. It is also possible to give polite instructions to others. Furthermore, you know how to talk about your family, your physical appearance, and your hobbies.

This checkpoint will help you bring all these pieces together. We will review modal verbs, commands, and everyday situations. We want you to feel comfortable using these tools in real-life conversations.

For our review, the complex grammar explanations and task instructions will be in English. This ensures you understand the rules and nuances clearly without getting lost. However, all our dialogues and practical scenarios will be entirely in Ukrainian. This is how you will experience the language in the real world.

Чи ви готові? (Are you ready?) Let's check your confidence before we begin. Ask yourself these simple questions:
- Can I easily explain the difference between knowing how to do something and being able to do it right now?
- Do I know how to politely ask someone to read a text or give me something?
- Can I describe what my friend looks like and what we want to do on the weekend?

If you answered yes, you are doing great. If you are unsure, do not worry! Ми все повторимо. (We will review everything.)

## Навичка 1: Модальні дієслова (Skill 1: Modal Verbs)

In Ukrainian, we use very different words to express ability, necessity, and desire. Let's start with ability.

English uses the word «can» for almost everything. In Ukrainian, we separate learned skills from situational possibilities. This is a very important distinction to master.

We use **вмі́ти** when we have learned how to do something. It represents a skill or knowledge you have acquired over time.
We use **могти́** when we have the physical ability, the permission, or the time to do something right now. It depends on the circumstances.

### Модель: Вміти чи Могти?

> Я **вмі́ю** гра́ти в ша́хи. Але сього́дні я не **мо́жу** гра́ти. У мене бага́то робо́ти.
> (I **know how** to play chess. But today I **cannot** play. I have a lot of work.)
>
> **Notice:**
> - вмі́ю = **learned skill**
> - не мо́жу = **situational lack of time/ability**

| Ukrainian | English |
|---|---|
| Я вмі́ю чита́ти. | I know how to read. |
| Я не мо́жу чита́ти за́раз. | I cannot read right now. |
| Ти вмі́єш гра́ти в ша́хи? | Do you know how to play chess? |
| Ти мо́жеш гра́ти сього́дні? | Can you play today? |

When we talk about things we cannot do or are not allowed to do, we have three clear options.
Я не вмі́ю. (I do not know how.) Use this for a lack of skill.
Я не мо́жу. (I cannot.) Use this for a lack of time or physical ability.
Тут не мо́жна. (It is not allowed here.) Use this when something is prohibited by rules.

> [!warning]
> The word **мо́жна** is completely impersonal. It never changes its form. You do not say «Я не можна.» You simply say «не мо́жна» to state that a specific action is forbidden in a place.

Now, let's look at obligation and desire. Sometimes you want to do something, and sometimes you absolutely must do it.

| Modal | Intensity | Meaning |
|---|---|---|
| **хоті́ти** | Low | To want (desire) |
| **тре́ба** | Medium | It is necessary (impersonal) |
| **пови́нен** | High | Must (personal duty) |

If you need something, use the impersonal word **тре́ба**. Do not try to change its ending.
Тре́ба йти. (It is necessary to go.)
Я пови́нен працюва́ти. (I must work.)
Я хо́чу спа́ти. (I want to sleep.)

### Пла́ни на вихідні́

Here is a short conversation between two friends planning their time.

— Приві́т! Ти мо́жеш пої́хати в по́дорож? (Hi! Can you go on a journey?)
— Приві́т! Я хо́чу пої́хати. (Hi! I want to go.) Але́ я не мо́жу. (But I cannot.) Тре́ба працюва́ти. (It is necessary to work.)
— Шкода́. (It's a pity.) Ти пови́нен працюва́ти в субо́ту? (Must you work on Saturday?)
— Так. Я мо́жу зустрі́тися в неді́лю. (Yes. I can meet on Sunday.)
— Чудо́во! (Great!) Я вмі́ю готува́ти пі́цу. (I know how to cook pizza.) Пообі́даймо ра́зом. (Let's have lunch together.)
— Зго́да! (Agreed! / Let's do it!)

### Практика: Оберіть правильне слово

**Your Turn:** Choose the correct modal verb for each sentence.

1. Я (вмі́ю / мо́жу) говори́ти українською мовою. (skill)
2. Ти (вмі́єш / мо́жеш) грати за́раз? (situational)
3. Тут (не тре́ба / не мо́жна) палити. (prohibited)
4. Я хочу їсти. (Тре́ба / Пови́нен) купити хліб. (impersonal necessity)

> [!solution] Перевірити (Check)
> 1. вмі́ю (it is a learned skill)
> 2. мо́жеш (asking about current physical ability/time)
> 3. не мо́жна (it is prohibited)
> 4. тре́ба (impersonal necessity)

### Самоперевірка

- ☐ Did you use **вміти** for skills and **могти** for possibilities?
- ☐ Did you remember that **можна** and **треба** do not change their form?

## Навичка 2: Накази та прохання (Skill 2: Commands & Requests)

When we want someone to do something, we use the imperative form. We have two main forms to remember: informal (ти) for our friends and family, and formal or plural (ви) for respect or for addressing multiple people at once.

### Модель: Неформально чи Формально?

> **Неформально (ти):** Дай квито́к, бу́дь ла́ска.
> **Формально (ви):** Да́йте квито́к, бу́дь ла́ска.
>
> **Notice:**
> - дай = **informal (friend, family)**
> - да́йте = **formal (stranger, authority) OR plural**

Here are eight essential verbs you will need to use every day in Ukrainian.

| Verb | Informal (ти) | Formal / Plural (ви) |
|---|---|---|
| чита́ти (to read) | чита́й | чита́йте |
| писа́ти (to write) | пиши́ | пиші́ть |
| сказа́ти (to say) | скажи́ | скажі́ть |
| да́ти (to give) | дай | да́йте |
| іти́ (to go) | іди́ | іді́ть |
| слу́хати (to listen) | слу́хай | слу́хайте |
| диви́тися (to look) | диви́сь | диві́ться |
| стоя́ти (to stand) | стій | сті́йте |

> [!culture]
> Ukrainian politeness is beautifully simple. We do not often use long, indirect phrases like «Would you mind giving me the book?». We simply use the imperative form and add **бу́дь ла́ска** (please). Your tone of voice is very important to sound friendly!

Let's look at how to make requests, starting from very direct to very polite.
Дай квито́к. (Give the ticket.) This is direct, only used for close friends.
Да́йте, бу́дь ла́ска, квито́к. (Please give the ticket.) This is the standard polite form for everyday life.
Прошу́ вас да́ти квито́к. (I ask you to give the ticket.) This is very formal.
Чи не могли́ б ви да́ти квито́к? (Could you please give the ticket?) This is extremely polite and deferential.

We also use negative commands to tell people what not to do. This is very common in public spaces or on transportation.
Стій тут. (Stand here.)
Не стій тут. (Do not stand here.)
Слу́хай ува́жно. (Listen carefully.)
Не слу́хай це. (Do not listen to this.)
Чита́йте текст. (Read the text.)
Не чита́йте за́раз. (Do not read right now.)

### Практика: Утворіть прохання

**Your Turn:** Choose the correct imperative form based on the context.

1. Мамо, (диви́сь / диві́ться) на мене!
2. Пане, (скажи́ / скажі́ть), будь ласка, де банк?
3. Друзі, (слу́хай / слу́хайте) уважно.
4. Олено, не (чита́й / чита́йте) це зараз.

> [!solution] Перевірити (Check)
> 1. диви́сь (informal, addressing mother)
> 2. скажі́ть (formal, addressing "Пане" / "Sir")
> 3. слу́хайте (plural, addressing friends)
> 4. чита́й (informal, addressing Olena)

### Самоперевірка

- ☐ Did you use **-й/-и/-сь** for singular, informal requests?
- ☐ Did you use **-йте/-іть/-ться** for formal or plural requests?

## Навичка 3: Повсякдення (Skill 3: Everyday Life)

Now let's practice talking about the people in our lives and what we enjoy doing with them. Read this short text describing a friend.

### Модель: Опис Друга і Плани

> Це мій друг. (This is my friend.) Його́ зва́ти Іва́н. (His name is Ivan.) Йому́ два́дцять ро́ків. (He is twenty years old.) Він молоди́й. (He is young.) Він висо́кий і струнки́й. (He is tall and slim.) У ньо́го є вели́ка роди́на. (He has a big family.) У ньо́го є брат і сестра́. (He has a brother and a sister.)
> 
> Я люблю́ гра́ти в те́ніс, а він гра́є на гіта́рі. (I love playing tennis, and he plays the guitar.)
> Зустрі́ньмося в па́рку. (Let's meet in the park.)
> Ми бу́демо ї́хати авто́бусом. (We will go by bus.)
>
> **Notice:**
> - У нього є = **He has (At him is)**
> - грати в = **play a game**
> - грати на = **play an instrument**
> - автобусом = **by bus (fixed form)**

We often invite our friends to do things together during our free time. We can use the friendly phrases **Ході́мо!** (Let's go!) or **Зустрі́ньмося!** (Let's meet!).
Зустрі́ньмося в па́рку. (Let's meet in the park.)
Яке́ у те́бе хо́бі? (What is your hobby?)
Я люблю́ гра́ти в те́ніс. (I love playing tennis.) Ході́мо на стадіо́н! (Let's go to the stadium!)

> [!tip]
> Remember the important difference in hobbies. We use **гра́ти в** for sports and games, but we use **гра́ти на** for musical instruments. Я гра́ю у футбо́л. Я гра́ю на гіта́рі.

When we travel to meet friends, we use transportation vocabulary. In Ukrainian, we use a specific fixed form to say «by bus» or «by train». We just say **авто́бусом** or **по́їздом** as a single idea.
Ми хо́чемо пої́хати в по́дорож. (We want to go on a journey.) Ми бу́демо ї́хати авто́бусом. (We will go by bus.) Я хо́чу запроси́ти те́бе. (I want to invite you.) Це ду́же ці́каво. (This is very interesting.) Поверні́ть налі́во бі́ля стадіо́ну. (Turn left near the stadium.) Там є зупи́нка. (There is a stop there.)

### Практика: Опишіть повсякдення

**Your Turn:** Fill in the correct word.

1. У (мене / я) є брат.
2. Я люблю грати (в / на) піаніно.
3. Мій друг грає (в / на) футбол.
4. Ми їдемо (автобус / автобусом).

> [!solution] Перевірити (Check)
> 1. мене (У мене є = I have)
> 2. на (playing an instrument)
> 3. в (playing a sport/game)
> 4. автобусом (fixed transportation form)

### Самоперевірка

- ☐ Did you use **У мене/нього є** to say someone has something?
- ☐ Did you use **в + sport** and **на + instrument** correctly?
- ☐ Did you use the fixed **-ом** ending for transportation?

## Інтеграційне завдання (Integration Task)

### Сцена́рій: По́дорож на вихідні́

Now it is your turn to combine everything you know. Real language happens when we mix different rules together. Here is a model dialogue showing how two friends plan a weekend trip. Notice carefully how they use modal verbs, polite commands, and travel words naturally.

— Приві́т, Окса́но! (Hi, Oksana!) Ти хо́чеш пої́хати в по́дорож на вихідні́? (Do you want to go on a journey for the weekend?)
— Приві́т! Так, я ду́же хо́чу. (Hi! Yes, I really want to.) Але́ куди́ ми мо́жемо пої́хати? (But where can we go?)
— Пої́дьмо в го́ри! (Let's go to the mountains!) Нам тре́ба купи́ти квитки́ сього́дні. (We need to buy tickets today.)
— До́бре. (Good.) Ті́льки я не мо́жу ї́хати авто́бусом. (Only I cannot go by bus.) Це до́вго. (It is long.) Я хо́чу ї́хати по́їздом. (I want to go by train.)
— Без пробле́м. (No problem.) Я не вмі́ю купува́ти квитки́ в інтерне́ті. (I do not know how to buy tickets on the internet.) Подиви́сь розкла́д, бу́дь ла́ска. (Look at the schedule, please.)
— Диви́сь, є по́їзд у субо́ту вра́нці. (Look, there is a train on Saturday morning.)
— Чудо́во, купу́й! (Great, buy them!) І скажи́ час. (And tell the time.)

Your integration task is to write your own dialogue. Imagine you are planning a short trip with your friend.
Follow these specific steps to practice your skills:
1. Ask your friend if they want to go somewhere using the word **хо́чеш**.
2. State something that is necessary using the impersonal **тре́ба**.
3. Suggest a mode of transport (for example, use the fixed phrase **авто́бусом**).
4. Give at least two polite commands using the imperative forms (like **скажи́**, **чита́й**, or **диви́сь**).

---

## Підсумок

You have done an excellent job reviewing these essential communication skills. You now know how to clearly distinguish between a learned skill and circumstantial ability. You understand the different levels of obligation. You can confidently form polite requests using imperative verbs without overcomplicating your sentences. And you have successfully integrated family, hobby, and transportation vocabulary into your everyday conversations.

Here are a few quick questions to check your progress:
1. What is the fundamental difference between saying «я не вмію» and «я не можу»?
2. How do you express «I need» without trying to conjugate the word «треба»?
3. What is the polite formal imperative form of the verb «читати»?
4. How do you say «by bus» as a fixed phrase in Ukrainian travel contexts?

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/checkpoint-communication.yaml`

```yaml
- type: quiz
  title: "Modal Verbs Check"
  instruction: "Choose the correct modal verb for each situation."
  items:
    - question: "What word do you use to say you learned how to cook?"
      options:
        - text: "вмію"
          correct: true
        - text: "можу"
          correct: false
        - text: "треба"
          correct: false
        - text: "хочу"
          correct: false
    - question: "Which word means you cannot meet right now?"
      options:
        - text: "не можу"
          correct: true
        - text: "не вмію"
          correct: false
        - text: "не можна"
          correct: false
        - text: "не треба"
          correct: false
    - question: "How do you express necessity, like 'it is necessary'?"
      options:
        - text: "треба"
          correct: true
        - text: "я треба"
          correct: false
        - text: "я хочу"
          correct: false
        - text: "я можу"
          correct: false
    - question: "What word is used for a strict personal obligation, like 'I must work'?"
      options:
        - text: "повинен"
          correct: true
        - text: "можу"
          correct: false
        - text: "вмію"
          correct: false
        - text: "хочу"
          correct: false
    - question: "Which word means 'to want'?"
      options:
        - text: "хотіти"
          correct: true
        - text: "могти"
          correct: false
        - text: "вміти"
          correct: false
        - text: "стояти"
          correct: false
    - question: "How do you express that something is forbidden or not allowed?"
      options:
        - text: "не можна"
          correct: true
        - text: "не треба"
          correct: false
        - text: "не вмію"
          correct: false
        - text: "не можу"
          correct: false
    - question: "What is the correct way to say 'I do not know how to swim'?"
      options:
        - text: "я не вмію"
          correct: true
        - text: "я не можу"
          correct: false
        - text: "я не можна"
          correct: false
        - text: "я не хочу"
          correct: false
    - question: "What is the correct way to say 'I cannot play today'?"
      options:
        - text: "я не можу"
          correct: true
        - text: "я не вмію"
          correct: false
        - text: "я не можна"
          correct: false
        - text: "я не повинен"
          correct: false

- type: true-false
  title: "True or False: Modals"
  instruction: "Read the statements and decide if they are true or false."
  items:
    - statement: "We use the word 'могти' to express a learned skill."
      correct: false
      explanation: "We use 'вміти' for learned skills, and 'могти' for situational ability."
    - statement: "The word 'треба' does not change its ending for I, you, or he."
      correct: true
      explanation: "Треба is impersonal and does not change its form."
    - statement: "'Треба' means 'I want'."
      correct: false
      explanation: "'Треба' means 'it is necessary'."
    - statement: "'Тут не можна' means 'It is not allowed here'."
      correct: true
      explanation: "'Не можна' is used to state that something is forbidden."
    - statement: "'Я не можу' and 'я не вмію' mean exactly the same thing."
      correct: false
      explanation: "'Не можу' means you cannot right now, 'не вмію' means you do not know how."
    - statement: "To say 'I must work', we use 'Я повинен працювати'."
      correct: true
      explanation: "'Повинен' expresses a strong personal obligation."
    - statement: "'Могти' is used when you have the time and physical ability to do something right now."
      correct: true
      explanation: "It depends on the circumstances."
    - statement: "'Я вмію читати' means 'I am reading right now'."
      correct: false
      explanation: "'Я вмію читати' means 'I know how to read'."

- type: match-up
  title: "Match the Imperatives"
  instruction: "Match the infinitive verb to its informal command form."
  pairs:
    - left: "читати"
      right: "читай"
    - left: "писати"
      right: "пиши"
    - left: "сказати"
      right: "скажи"
    - left: "дати"
      right: "дай"
    - left: "іти"
      right: "іди"
    - left: "слухати"
      right: "слухай"
    - left: "дивитися"
      right: "дивись"
    - left: "стояти"
      right: "стій"

- type: group-sort
  title: "Sort the Commands"
  instruction: "Sort the verbs into informal and formal commands."
  groups:
    - name: "Informal Commands"
      items:
        - "читай"
        - "пиши"
        - "скажи"
        - "іди"
        - "слухай"
    - name: "Formal/Plural Commands"
      items:
        - "читайте"
        - "пишіть"
        - "скажіть"
        - "ідіть"
        - "слухайте"

- type: fill-in
  title: "Complete the Sentences"
  instruction: "Choose the correct word to complete the sentence."
  items:
    - sentence: "Я хочу поїхати в ___."
      answer: "подорож"
      options:
        - "подорож"
        - "школа"
        - "робота"
        - "книга"
    - sentence: "Ми будемо їхати ___."
      answer: "автобусом"
      options:
        - "автобусом"
        - "автобус"
        - "автобуса"
        - "автобусу"
    - sentence: "Я люблю грати в ___."
      answer: "теніс"
      options:
        - "теніс"
        - "гітара"
        - "піаніно"
        - "скрипка"
    - sentence: "Поверніть ___ біля стадіону."
      answer: "наліво"
      options:
        - "наліво"
        - "вліво"
        - "лівий"
        - "ліва"
    - sentence: "Я ___ зустрітися в неділю."
      answer: "можу"
      options:
        - "можу"
        - "можеш"
        - "може"
        - "можуть"
    - sentence: "___ розклад, будь ласка."
      answer: "подивись"
      options:
        - "подивись"
        - "дивитися"
        - "дивиться"
        - "дивлюся"
    - sentence: "Нам ___ купити квитки сьогодні."
      answer: "треба"
      options:
        - "треба"
        - "требу"
        - "требом"
        - "требі"
    - sentence: "Я не ___ грати на гітарі."
      answer: "вмію"
      options:
        - "вмію"
        - "вмієш"
        - "вміє"
        - "вміють"

- type: unjumble
  title: "Build the Sentences"
  instruction: "Put the words in the correct order."
  items:
    - words:
        - "Я"
        - "хочу"
        - "поїхати"
        - "в"
        - "подорож"
      answer: "Я хочу поїхати в подорож"
    - words:
        - "Треба"
        - "купити"
        - "квиток"
      answer: "Треба купити квиток"
    - words:
        - "Я"
        - "не"
        - "вмію"
        - "читати"
      answer: "Я не вмію читати"
    - words:
        - "Я"
        - "люблю"
        - "грати"
        - "в"
        - "теніс"
      answer: "Я люблю грати в теніс"
    - words:
        - "Давай"
        - "зустрінемось"
        - "у"
        - "парку"
      answer: "Давай зустрінемось у парку"
    - words:
        - "Ми"
        - "будемо"
        - "їхати"
        - "автобусом"
      answer: "Ми будемо їхати автобусом"

- type: quiz
  title: "Everyday Scenarios"
  instruction: "Choose the best response for each situation."
  items:
    - question: "How do you ask a friend for a ticket?"
      options:
        - text: "Дай квиток"
          correct: true
        - text: "Дайте квиток"
          correct: false
        - text: "Прошу дати"
          correct: false
        - text: "Давати квиток"
          correct: false
    - question: "How do you politely ask for the time?"
      options:
        - text: "Скажіть, будь ласка"
          correct: true
        - text: "Скажи, будь ласка"
          correct: false
        - text: "Сказати, будь ласка"
          correct: false
        - text: "Кажи, будь ласка"
          correct: false
    - question: "You are telling your friend not to listen to something. What do you say?"
      options:
        - text: "Не слухай це"
          correct: true
        - text: "Не слухайте це"
          correct: false
        - text: "Не слухати це"
          correct: false
        - text: "Не слухає це"
          correct: false
    - question: "You want to suggest going to the stadium. What do you say?"
      options:
        - text: "Ходімо на стадіон"
          correct: true
        - text: "Іди на стадіон"
          correct: false
        - text: "Ідіть на стадіон"
          correct: false
        - text: "Стояти на стадіоні"
          correct: false
    - question: "You want to say that you must work on Saturday. What do you say?"
      options:
        - text: "Я повинен працювати"
          correct: true
        - text: "Я можу працювати"
          correct: false
        - text: "Я вмію працювати"
          correct: false
        - text: "Я хочу працювати"
          correct: false
    - question: "You want to tell a friend to stand here. What do you say?"
      options:
        - text: "Стій тут"
          correct: true
        - text: "Стояти тут"
          correct: false
        - text: "Стійте тут"
          correct: false
        - text: "Стою тут"
          correct: false
    - question: "How do you say 'He is young'?"
      options:
        - text: "Він молодий"
          correct: true
        - text: "Він двадцять років"
          correct: false
        - text: "Його молодий"
          correct: false
        - text: "Він є молодий"
          correct: false
    - question: "How do you say 'We will go by bus'?"
      options:
        - text: "Ми будемо їхати автобусом"
          correct: true
        - text: "Ми будемо їхати автобус"
          correct: false
        - text: "Ми будемо їхати в автобусі"
          correct: false
        - text: "Ми будемо їхати на автобус"
          correct: false

- type: true-false
  title: "True or False: Everyday Vocabulary"
  instruction: "Read the statements and decide if they are true or false."
  items:
    - statement: "'Автобусом' is a fixed phrase meaning 'by bus'."
      correct: true
      explanation: "In Ukrainian, we use this form to express traveling by bus."
    - statement: "'Грати в' is used for musical instruments, and 'грати на' is for sports."
      correct: false
      explanation: "It is the opposite: 'грати в' is for sports, 'грати на' is for instruments."
    - statement: "'Давай зустрінемось' means 'Let's meet'."
      correct: true
      explanation: "It is a friendly way to invite someone to meet."
    - statement: "You should say 'Я граю на теніс'."
      correct: false
      explanation: "You should say 'Я граю в теніс' because tennis is a sport."
    - statement: "'Стій тут' is a polite formal command."
      correct: false
      explanation: "It is informal. The formal version is 'Стійте'."
    - statement: "'Високий і стрункий' means 'tall and slim'."
      correct: true
      explanation: "These words are used to describe physical appearance."
    - statement: "'Будь ласка' is used to make a request polite."
      correct: true
      explanation: "It means 'please'."
    - statement: "'Я хочу запросити тебе' means 'I want to invite you'."
      correct: true
      explanation: "This is a common way to invite a friend."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/checkpoint-communication.yaml`

```yaml
items:
  - lemma: "могти"
    translation: "can, to be able (circumstantial)"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "вміти"
    translation: "to know how, to be able (learned skill)"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "треба"
    translation: "it is necessary, need"
    pos: "predicative"
  - lemma: "хотіти"
    translation: "to want"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "повинен"
    translation: "must, obliged"
    pos: "adjective"
  - lemma: "читай"
    translation: "read! (informal)"
    pos: "verb"
    aspect: "imperfective"
    notes: "imperative form of читати"
  - lemma: "скажи"
    translation: "say! tell! (informal)"
    pos: "verb"
    aspect: "perfective"
    notes: "imperative form of сказати"
  - lemma: "дай"
    translation: "give! (informal)"
    pos: "verb"
    aspect: "perfective"
    notes: "imperative form of дати"
  - lemma: "подорож"
    translation: "journey, trip"
    pos: "noun"
    gender: "f"
  - lemma: "автобус"
    translation: "bus"
    pos: "noun"
    gender: "m"
  - lemma: "хобі"
    translation: "hobby"
    pos: "noun"
    gender: "n"
  - lemma: "стадіон"
    translation: "stadium"
    pos: "noun"
    gender: "m"
  - lemma: "запрошувати"
    translation: "to invite"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "наліво"
    translation: "to the left"
    pos: "adverb"
  - lemma: "пиши"
    translation: "write! (informal)"
    pos: "verb"
    aspect: "imperfective"
    notes: "imperative form of писати"
  - lemma: "іди"
    translation: "go! (informal)"
    pos: "verb"
    aspect: "imperfective"
    notes: "imperative form of іти"
  - lemma: "слухай"
    translation: "listen! (informal)"
    pos: "verb"
    aspect: "imperfective"
    notes: "imperative form of слухати"
  - lemma: "дивись"
    translation: "look! (informal)"
    pos: "verb"
    aspect: "imperfective"
    notes: "imperative form of дивитися"
  - lemma: "стій"
    translation: "stand! (informal)"
    pos: "verb"
    aspect: "imperfective"
    notes: "imperative form of стояти"
  - lemma: "поїзд"
    translation: "train"
    pos: "noun"
    gender: "m"
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, locate the exact text in the file contents above
2. Output a FIND/REPLACE pair with the exact text and the corrected version
3. Prioritize: **audit gate failures first**, then review issues
4. Only fix issues documented above — no silent extra changes
5. Maximum **15 FIND/REPLACE pairs** total

---

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections unless the Fix Plan explicitly requests it
- If nothing needs fixing, output an empty fix block
- FIND text must match the file contents EXACTLY (copy-paste from above)

---

## Output Format

You MUST use these exact delimiters:

```
===SECTION_FIX_START===
FILE: [filename]
FIND:
[exact text from the file — must match character-for-character]
REPLACE:
[corrected text]
---
FILE: [filename]
FIND:
[exact text]
REPLACE:
[corrected text]
---
[... more pairs, max 15 ...]
===SECTION_FIX_END===
```

If no fixes are needed:

```
===SECTION_FIX_START===
(No fixes needed — all issues resolved)
===SECTION_FIX_END===
```

After the fix block, output a friction report:

```
===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: {what you were doing}
**Friction Type**: NONE | TEXT_NOT_FOUND | ...
**Raw Error**: {actual issue or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done
- Do NOT output ===REVIEW_START=== or ===FACTUAL_REVIEW_START=== blocks
- Do NOT use Edit tool or any other tool — you have NO tool access
- Output ONLY FIND/REPLACE pairs within the delimiters above
- Maximum 15 FIND/REPLACE pairs


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 15 min timeout]...
===SECTION_FIX_START===
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-communication.yaml
FIND:
    - sentence: "Я хочу поїхати в ___."
      answer: "подорож"
      options:
        - "подорож"
        - "школа"
        - "робота"
        - "книга"
REPLACE:
    - sentence: "Я хочу поїхати в ___."
      answer: "подорож"
      options:
        - "подорож"
        - "парк"
        - "центр"
        - "офіс"
---
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-communication.yaml
FIND:
    - sentence: "Нам ___ купити квитки сьогодні."
      answer: "треба"
      options:
        - "треба"
        - "требу"
        - "требом"
        - "требі"
REPLACE:
    - sentence: "Нам ___ купити квитки сьогодні."
      answer: "треба"
      options:
        - "треба"
        - "можна"
        - "повинен"
        - "хочу"
---
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-communication.yaml
FIND:
    - words:
        - "Давай"
        - "зустрінемось"
        - "у"
        - "парку"
      answer: "Давай зустрінемось у парку"
REPLACE:
    - words:
        - "Зустріньмося"
        - "в"
        - "парку"
        - "сьогодні"
      answer: "Зустріньмося в парку сьогодні"
---
FILE: curriculum/l2-uk-en/a1/activities/checkpoint-communication.yaml
FIND:
    - statement: "'Давай зустрінемось' means 'Let's meet'."
      correct: true
      explanation: "It is a friendly way to invite someone to meet."
REPLACE:
    - statement: "'Зустріньмося' means 'Let's meet'."
      correct: true
      explanation: "It is a friendly way to invite someone to meet."
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Applying FIND/REPLACE fixes to YAML activities.
**Friction Type**: NONE
**Raw Error**: None
**Self-Correction**: Markdown file already contained the fixed imperative forms ("Зустріньмося", "Пообідаймо"), so fixes were only applied to the YAML activities where the outdated forms ("Давай зустрінемось") and fabricated morphology ("требу") still resided.
**Proposed Tooling Fix**: N/A
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (2045 chars)
✅ Message sent to Claude (ID: 21285)
✓ Message 21285 acknowledged
   Auto-acknowledged reply #21285 (stdout delivery — no inbox accumulation)
⚠️  GitHub issue creation failed: could not add label: 'review-result' not found

✓ Message 21280 acknowledged
