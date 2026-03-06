✅ Message sent to Gemini (ID: 20960) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #20960...
📨 Message #20960
   From: gemini → To: gemini
   Type: query
   Task: tomorrow-future-tense-review-fix-2
   Time: 2026-03-05T23:11:42.685012+00:00

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

### Issue 1: Unnatural "Бути" + "Мати" Construction (Calque)
**Location**: `## Лексика та культурний контекст` and `## Практика та підсумок`
**Problem**: The module uses `будемо мати` and `будеш мати` as a direct translation of "will have" (`Наступного тижня ми будемо мати новий урок.`, `Наступного року ти будеш мати новий дім.`, `ми збираємося мати новий проект.`). While technically understood, native speakers heavily avoid this, preferring `у мене буде` or `матиму`. Teaching `буду мати` reinforces bad habits at A1.
**Fix**: Replace these with natural active verbs (e.g., `починати`, `будувати`, `робити`).

### Issue 2: Tautological Calque
**Location**: `## Практика та підсумок`
**Problem**: The phrase `Ми будемо робити багато роботи.` is an English calque ("do a lot of work") and a tautology in Ukrainian.
**Fix**: Change to the natural `Ми будемо багато працювати.`

### Issue 3: Orphaned Vocabulary Items
**Location**: `## Vocabulary`
**Problem**: The vocabulary list contains several generated words that are never actually used in the module's instructional text, examples, or activities: `сподіватися`, `мріяти`, `планувати`, `пізніше`, `вихідні`. This is a classic LLM generation hallucination.
**Fix**: Delete these 5 unused words from the vocabulary list.

### Issue 4: Unnatural Fill-in Sentence
**Location**: `## Activities` -> `fill-in` -> `Time and Intentions`
**Problem**: The sentence `Я маю плани наступного року.` sounds slightly odd, translating closer to "I possess plans during next year". It is better to match the more natural phrasing used in the reading passage.
**Fix**: Change the item to `___ року ми маємо великі плани.` with the answer `Наступного`.

---

## Ukrainian Language Issues

* `"Наступного року ти будеш мати новий дім."` -> Highly unnatural. Change to `"Наступного року ти будеш будувати новий дім."` (you will build a new house) to keep the compound future practice.
* `"Ми будемо робити багато роботи."` -> Calque/tautology. Change to `"Ми будемо багато працювати."`

---

## Fix Plan to Reach 9/10

1. Replace all instances of `буду мати` / `будемо мати` with active, natural verbs that pair well with the compound future.
2. Fix the "робити багато роботи" tautology.
3. Remove the 5 unused words from the YAML vocabulary list.
4. Update the awkward sentence in the fill-in activity.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
1 Outline Compliance Errors
failing gates:
lesson: 1934/1200 (raw: 2082) | pedagogy: 1 violations | immersion: 34.4% LOW (target 35-55% (M37))
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• 1 Outline Compliance Errors
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/tomorrow-future-tense-audit.log for details)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: 1 Outline Compliance Errors
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md`

```markdown
<!-- SCOPE
Covers: Compound future tense (буду + infinitive), basic future time markers, expressing plans and intentions.
Not covered:
  - Synthetic future tense (працюватиму) → future modules
-->

# Tomorrow - Future Tense

> **Чому це важливо?**
>
> Talking about the past helps us share stories, but talking about the future lets us build our lives together. Knowing how to use the future tense is your key to making arrangements and looking forward to what comes next.

## Вступ

We have already explored how to talk about the things we did in the past. We learned how to say what happened yesterday, last week, or a long time ago. The timeline of our lives moves forward, and it is equally important to discuss where we are going. Today, we shift our focus from the past to the future.

We all have plans. Sometimes our plans are very concrete, like a doctor's appointment or a work meeting. Sometimes they are just dreams or intentions, like wishing to travel or wanting to learn a new skill. Think about your timeline. Right now, you are reading this text. You are studying the Ukrainian language. Yesterday, you perhaps worked or rested. But what happens next? Where will you be tomorrow? What will you do? What will you eat? Who will you see? 

In Ukrainian, we ask these questions frequently. Talking about the future is a great way to make friends and build relationships.
— Де ти будеш завтра? (Where will you be tomorrow?)
— Завтра я буду вдома. (Tomorrow I will be at home.)
— Що ти будеш там робити? (What will you do there?)
— Я буду читати книгу. (I will read a book.)
— Це добрий план! Я також буду читати. (That is a good plan! I will also read.)
— Ми будемо читати разом! (We will read together!)

In Ukrainian culture, looking toward the future often carries a sense of hope and resilience. A very common phrase you might hear is «Завтра буде новий день». This translates to "Tomorrow will be a new day." It is a gentle reminder that no matter what challenges we face today, tomorrow brings new opportunities and a fresh start. 

> [!culture]
> When someone has a difficult day, friends often say «Завтра буде новий день» to offer comfort. It shows optimism and a forward-looking mindset.

To express these hopes and plans, we need the right tools. We will learn a simple and highly effective way to build future tense sentences. This method uses a special helper word combined with the basic dictionary form of the verbs you already know. You will soon see that building future actions is actually quite logical and straightforward. Let's prepare to talk about your next steps. 

## Презентація граматики: Буду + Інфінітив

To talk about actions that will happen in the future, we use a compound structure. We take a form of the verb «бути» (to be) and add an infinitive. 

First, we need to know how to change the verb «бути» for the future. 

| Subject | Verb Form | Example | Meaning |
|---------|-----------|---------|---------|
| Я | **буду** | Я буду працювати. | I will work. |
| Ти | **будеш** | Ти будеш читати. | You will read. |
| Він / Вона | **буде** | Він буде спати. | He will sleep. |
| Ми | **будемо** | Ми будемо їсти. | We will eat. |
| Ви | **будете** | Ви будете слухати. | You will listen. |
| Вони | **будуть** | Вони будуть знати. | They will know. |

You choose the correct form of the helper verb and attach the action. The word «буду» means "I will," and «працювати» means "to work." Together, «Я буду працювати» means "I will work."

Let's look at more examples:
* Я буду працювати в офісі. (I will work in the office.)
* Ти будеш читати новий журнал. (You will read a new magazine.)
* Він буде пити гарячу каву. (He will drink hot coffee.)
* Вона буде слухати сучасну музику. (She will listen to modern music.)
* Ми будемо обідати в ресторані. (We will eat lunch in a restaurant.)
* Ви будете писати довгий лист. (You will write a long letter.)
* Вони будуть знати правильну відповідь. (They will know the correct answer.)

> [!warning]
> **Learner Error:** The helper verb «буду» only pairs with imperfective verbs. You must say «Я буду читати» (I will read). You must never use a perfective verb here. Saying «Я буду прочитати» is grammatically incorrect.

We make sentences negative by adding «не».
* Я не буду працювати сьогодні. (I will not work today.)
* Ти не будеш читати цю книгу. (You will not read this book.)
* Ми не будемо обідати там. (We will not eat lunch there.)
* Вони не будуть знати про це. (They will not know about this.)

Asking a question is easy. 
* Що ти будеш робити? (What will you do?)
* Де ви будете жити? (Where will you live?)

> [!tip]
> **FYI: The Synthetic Future**
> You might see words like «працюватиму» or «читатимеш». This merges the verb and the helper into one word. For your own speaking, using «буду працювати» is correct. You only need to recognize these single-word forms. 

## Лексика та культурний контекст: Плани на майбутнє

Now we need time words to say exactly when actions will happen.

The most common future marker is **завтра** (tomorrow). We often combine it with times of the day.
* **завтра вранці** (tomorrow morning)
* **завтра вдень** (tomorrow during the day)
* **завтра ввечері** (tomorrow evening)

* Я буду працювати завтра вранці. (I will work tomorrow morning.)
* Ти будеш читати завтра вдень. (You will read tomorrow during the day.)
* Він буде відпочивати завтра ввечері. (He will rest tomorrow evening.)
* Вона буде пити чай завтра вранці. (She will drink tea tomorrow morning.)
* Вони будуть гуляти завтра ввечері. (They will walk tomorrow evening.)
* Ми будемо їсти борщ завтра вдень. (We will eat borsch tomorrow during the day.)
* Ви будете слухати музику завтра. (You will listen to music tomorrow.)

If something happens the day after tomorrow, we use **післязавтра**. If an event is approaching, we use **скоро** (soon). 
* Ми будемо обідати післязавтра. (We will eat lunch the day after tomorrow.)
* Вони скоро будуть знати результат. (They will soon know the result.)
* Я скоро буду відпочивати. (I will rest soon.)

When we want to say "next week" or "next year", Ukrainian grammar requires the Genitive case. 
* **наступного тижня** (next week)
* **наступного року** (next year)

* Наступного тижня я буду багато працювати. (Next week I will work a lot.)
* Наступного тижня ми будемо починати новий урок. (Next week we will start a new lesson.)
* Наступного року вони будуть жити в Києві. (Next year they will live in Kyiv.)
* Наступного року я збираюся їхати в Україну. (Next year I am going to travel to Ukraine.)
* Наступного тижня вона буде читати цей текст. (Next week she will read this text.)
* Наступного разу ми будемо говорити дуже добре. (Next time we will speak very well.)
* Наступного року ти будеш будувати новий дім. (Next year you will build a new house.)
* Наступного тижня він буде працювати там. (Next week he will work there.)

> [!warning]
> **Learner Error:** Never say «наступний тиждень» when you mean "I will do it next week." Always use the Genitive forms «наступного тижня» and «наступного року».

Sometimes we have a desire or intention. To express a desire, we use **хотіти** (to want). 
* Я хочу знати правду. (I want to know the truth.)
* Вона дуже хоче спати. (She really wants to sleep.)
* Ми хочемо пити каву. (We want to drink coffee.)
* Він хоче працювати там. (He wants to work there.)
* Вони хочуть мати новий дім. (They want to have a new house.)
* Я хочу читати цю книгу. (I want to read this book.)
* Вона хоче гуляти там. (She wants to walk there.)

If we have an intention, we use **збиратися** (to be going to).
* Я збираюся їхати в місто. (I am going to travel to the city.)
* Ми збираємося вчити мову. (We are going to learn the language.)
* Ти збираєшся читати книгу. (You are going to read a book.)

Let's contrast definite plans and intentions. Notice the difference:
* Завтра я буду читати книгу. (Definite plan)
* Завтра я збираюся читати книгу. (Intention)
* Завтра я дуже хочу читати книгу. (Desire)

* Наступного тижня ми будемо працювати. (Definite plan)
* Наступного тижня ми збираємося працювати. (Intention)

> [!culture]
> Ukrainians can be quite cautious when talking about future plans. A famous proverb says: «Не кажи гоп, по́ки не перескочиш». It is a reminder not to celebrate plans before they happen. Because of this, people often prefer to say «Я збираюся...» rather than «Я буду...» for uncertain things.

## Практика та підсумок

Let's look at how people talk about their plans. We use **план** (plan) and **мати плани** (to have plans). We also use **потім** (then, later) to show the sequence of events.

Read these short dialogues:

**Діалог 1:**
— Які ти маєш плани на завтра? (What plans do you have for tomorrow?)
— Завтра вранці я буду працювати. (Tomorrow morning I will work.)
— Що ти будеш робити потім? (What will you do then?)
— Потім я буду читати книгу. (Then I will read a book.)

**Діалог 2:**
— Що ви будете робити післязавтра? (What will you do the day after tomorrow?)
— Ми збираємося їхати в місто. (We are going to travel to the city.)
— Ви будете там гуляти? (Will you walk there?)
— Так, ми дуже хочемо відпочивати. (Yes, we really want to rest.)

**Діалог 3:**
— Де вони будуть жити наступного року? (Where will they live next year?)
— Наступного року вони будуть жити тут. Вони мають великі плани на майбутнє — купити дім. (Next year they will live here. They have big plans for the future — to buy a house.)
— Це добрий план! (That is a good plan!)

Let's read a longer text about personal plans.

**Мої плани на завтра.**
Завтра буде новий день. Завтра вранці я буду працювати. Я маю багато роботи. Я буду писати довгий текст. Потім я буду обідати. Я хочу їсти борщ. Завтра вдень я збираюся читати нову книгу. Я дуже люблю читати. Що я буду робити завтра ввечері? Завтра ввечері я не буду працювати. Я буду відпочивати. Завтра ми збираємося гуляти в парку. Це мій план. Я дуже люблю відпочивати.

Now let's read about a travel intention.

**Плани на наступний рік.**
Наступного року ми маємо великі плани. Ми збираємося їхати в місто Київ. Це велике місто. Там ми будемо жити один місяць. Ми хочемо знати більше про культуру. Завтра ми будемо слухати українську музику. Потім ми будемо говорити українською мовою. Наступного тижня ми будемо складати план. Це буде дуже цікаво. Ми дуже хочемо їхати в Київ.

Let's practice with a role-play dialogue. Imagine an event planner discussing the work week and the upcoming weekend (вихідні).

— Добрий день! Що ми будемо робити наступного тижня? (Good afternoon! What will we do next week?)
— Я складаю план. Наступного тижня ми будемо багато працювати. Завтра вранці ми будемо писати текст, а потім ми будемо обідати. (I am making a plan. Next week we will work a lot. Tomorrow morning we will write text, and then we will eat lunch.)
— А що ми будемо робити на вихідні? (And what will we do on the weekend?)
— На вихідні ми будемо відпочивати. Післязавтра ми будемо слухати презентацію, а потім — вихідні! (On the weekend we will rest. The day after tomorrow we will listen to a presentation, and then — the weekend!)

---

## Підсумок

You now have the tools to talk about the future. You can express solid plans using the helper verb combined with an infinitive. You can specify the exact time using future markers, and you know how to differentiate between a firm commitment and a gentle intention. 

Here are a few questions to help you verify your knowledge:

1. How do you say "we will" and "they will" using the correct forms of the helper verb?
2. Why is the phrase «Я буду прочитати» grammatically incorrect?
3. How do you properly express "next week" and "next year" to indicate when an action will happen?
4. What is the difference in meaning between «Я буду робити» and «Я збираюся робити»?

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/tomorrow-future-tense.yaml`

```yaml
- type: quiz
  title: "Conjugation of 'to be' (future)"
  instruction: "Choose the correct form of the helper verb."
  items:
    - question: "How do you say 'I will' in Ukrainian?"
      options:
        - text: "буду"
          correct: true
        - text: "будеш"
          correct: false
        - text: "буде"
          correct: false
        - text: "будемо"
          correct: false
    - question: "How do you say 'You will' (singular/informal)?"
      options:
        - text: "будеш"
          correct: true
        - text: "буду"
          correct: false
        - text: "буде"
          correct: false
        - text: "будете"
          correct: false
    - question: "How do you say 'He will'?"
      options:
        - text: "буде"
          correct: true
        - text: "буду"
          correct: false
        - text: "будуть"
          correct: false
        - text: "будемо"
          correct: false
    - question: "How do you say 'We will'?"
      options:
        - text: "будемо"
          correct: true
        - text: "буду"
          correct: false
        - text: "будете"
          correct: false
        - text: "будуть"
          correct: false
    - question: "How do you say 'You will' (plural/formal)?"
      options:
        - text: "будете"
          correct: true
        - text: "будемо"
          correct: false
        - text: "будуть"
          correct: false
        - text: "буде"
          correct: false
    - question: "How do you say 'They will'?"
      options:
        - text: "будуть"
          correct: true
        - text: "будемо"
          correct: false
        - text: "будете"
          correct: false
        - text: "буде"
          correct: false
    - question: "Which form of the helper verb goes with 'вона' (she)?"
      options:
        - text: "буде"
          correct: true
        - text: "буду"
          correct: false
        - text: "будеш"
          correct: false
        - text: "будуть"
          correct: false
    - question: "Which form of the helper verb goes with 'я' (I)?"
      options:
        - text: "буду"
          correct: true
        - text: "будеш"
          correct: false
        - text: "буде"
          correct: false
        - text: "будемо"
          correct: false

- type: true-false
  title: "Grammar and Usage: True or False?"
  instruction: "Determine if the statements are true or false."
  items:
    - statement: "The helper verb 'буду' can be used with perfective verbs to talk about the future."
      correct: false
      explanation: "The verb 'буду' is strictly used with imperfective verbs to show ongoing or repeated future actions."
    - statement: "To say 'next week', you use the Genitive case: 'наступного тижня'."
      correct: true
      explanation: "When expressing 'next week' or 'next year', Ukrainian uses the Genitive case to indicate the time of action."
    - statement: "The phrase 'Я буду прочитати' is grammatically correct."
      correct: false
      explanation: "'Прочитати' is perfective, so it cannot follow 'буду'. You must say 'Я буду читати'."
    - statement: "The verb 'збиратися' is used to express an intention, similar to 'to be going to'."
      correct: true
      explanation: "Yes, Ukrainians often use 'збиратися' for plans that are not yet firmly arranged."
    - statement: "'Завтра ввечері' means 'tomorrow morning'."
      correct: false
      explanation: "'Ввечері' means 'in the evening'. Tomorrow morning is 'завтра вранці'."
    - statement: "To say 'I will not work', you put 'не' before the helper verb: 'Я не буду працювати'."
      correct: true
      explanation: "The negative particle 'не' comes directly before the helper verb."
    - statement: "The phrase 'наступного року' means 'next year'."
      correct: true
      explanation: "It uses the Genitive case to show when an action happens."
    - statement: "Ukrainians often say 'Я буду' for everything, even highly uncertain plans."
      correct: false
      explanation: "People often prefer 'Я збираюся' for things that are not yet fixed, following the cautious proverb."

- type: fill-in
  title: "Complete the Sentence"
  instruction: "Choose the correct helper verb."
  items:
    - sentence: "Завтра я ___ працювати."
      answer: "буду"
      options: ["буду", "будеш", "буде", "будемо"]
    - sentence: "Що ти ___ робити завтра?"
      answer: "будеш"
      options: ["будеш", "буду", "буде", "будете"]
    - sentence: "Ми ___ обідати разом."
      answer: "будемо"
      options: ["будемо", "буду", "буде", "будуть"]
    - sentence: "Вони не ___ слухати музику."
      answer: "будуть"
      options: ["будуть", "будемо", "будете", "буде"]
    - sentence: "Він ___ спати вдень."
      answer: "буде"
      options: ["буде", "буду", "будеш", "будуть"]
    - sentence: "Ви ___ читати книгу?"
      answer: "будете"
      options: ["будете", "будемо", "будуть", "буду"]
    - sentence: "Завтра вона ___ відпочивати."
      answer: "буде"
      options: ["буде", "буду", "будеш", "будуть"]
    - sentence: "Я не ___ жити там."
      answer: "буду"
      options: ["буду", "буде", "будемо", "будуть"]

- type: match-up
  title: "Match the Vocabulary"
  instruction: "Match the Ukrainian words with their English translations."
  pairs:
    - left: "завтра"
      right: "tomorrow"
    - left: "післязавтра"
      right: "the day after tomorrow"
    - left: "скоро"
      right: "soon"
    - left: "потім"
      right: "then, later"
    - left: "план"
      right: "plan"
    - left: "наступного тижня"
      right: "next week"
    - left: "хотіти"
      right: "to want"
    - left: "збиратися"
      right: "to be going to"

- type: unjumble
  title: "Build the Sentence"
  instruction: "Put the words in the correct order."
  items:
    - words: ["Я", "буду", "читати", "книгу."]
      answer: "Я буду читати книгу."
    - words: ["Що", "ти", "будеш", "робити?"]
      answer: "Що ти будеш робити?"
    - words: ["Ми", "будемо", "працювати", "завтра."]
      answer: "Ми будемо працювати завтра."
    - words: ["Вони", "не", "будуть", "спати."]
      answer: "Вони не будуть спати."
    - words: ["Я", "збираюся", "їхати", "в", "гори."]
      answer: "Я збираюся їхати в гори."
    - words: ["Завтра", "буде", "новий", "день."]
      answer: "Завтра буде новий день."

- type: group-sort
  title: "Sort the Words"
  instruction: "Categorize the words into the correct groups."
  groups:
    - name: "Helper Verb Forms"
      items: ["буду", "будеш", "буде", "будемо", "будуть"]
    - name: "Time Markers"
      items: ["завтра", "скоро", "потім", "післязавтра"]
    - name: "Intention Verbs"
      items: ["хотіти", "збиратися"]

- type: quiz
  title: "Usage of Time and Intentions"
  instruction: "Choose the best answer for each question."
  items:
    - question: "How do you say 'next week' in Ukrainian?"
      options:
        - text: "наступного тижня"
          correct: true
        - text: "наступний тиждень"
          correct: false
        - text: "наступного року"
          correct: false
        - text: "завтра"
          correct: false
      explanation: "Time expressions like 'next week' require the Genitive case."
    - question: "Which phrase means 'next year'?"
      options:
        - text: "наступного року"
          correct: true
        - text: "наступний рік"
          correct: false
        - text: "наступного тижня"
          correct: false
        - text: "наступного разу"
          correct: false
    - question: "If you are making a firm commitment to read, what do you say?"
      options:
        - text: "Я буду читати."
          correct: true
        - text: "Я хочу читати."
          correct: false
        - text: "Я збираюся читати."
          correct: false
        - text: "Я буду прочитати."
          correct: false
      explanation: "Using 'буду' shows a solid commitment."
    - question: "Which verb expresses an intention for the future?"
      options:
        - text: "збиратися"
          correct: true
        - text: "бути"
          correct: false
        - text: "мати"
          correct: false
        - text: "робити"
          correct: false
      explanation: "Ukrainians use 'збиратися' for intentions."
    - question: "How do you express 'I really want to sleep'?"
      options:
        - text: "Я дуже хочу спати."
          correct: true
        - text: "Я буду спати."
          correct: false
        - text: "Я збираюся спати."
          correct: false
        - text: "Я не хочу спати."
          correct: false
    - question: "What does the word 'скоро' mean in English?"
      options:
        - text: "soon"
          correct: true
        - text: "tomorrow"
          correct: false
        - text: "then"
          correct: false
        - text: "later"
          correct: false
    - question: "How do you ask 'What plans do you have?'"
      options:
        - text: "Які ти маєш плани?"
          correct: true
        - text: "Який план?"
          correct: false
        - text: "Що ти робиш?"
          correct: false
        - text: "Які ти маєш роки?"
          correct: false
    - question: "How do you say 'tomorrow evening'?"
      options:
        - text: "завтра ввечері"
          correct: true
        - text: "завтра вранці"
          correct: false
        - text: "завтра вдень"
          correct: false
        - text: "післязавтра"
          correct: false

- type: fill-in
  title: "Time and Intentions"
  instruction: "Choose the correct word to complete the sentence."
  items:
    - sentence: "___ буде новий день."
      answer: "Завтра"
      options: ["Завтра", "Скоро", "Потім", "Сьогодні"]
    - sentence: "Я ___ їхати в гори."
      answer: "збираюся"
      options: ["збираюся", "буду", "хочу", "план"]
    - sentence: "Ми будемо працювати ___ тижня."
      answer: "наступного"
      options: ["наступного", "наступний", "завтра", "скоро"]
    - sentence: "Вони дуже ___ знати правду."
      answer: "хочуть"
      options: ["хочуть", "будуть", "збираються", "планують"]
    - sentence: "Ми складаємо ___ на майбутнє."
      answer: "план"
      options: ["план", "року", "тижня", "день"]
    - sentence: "___ року ми маємо великі плани."
      answer: "Наступного"
      options: ["Наступного", "Наступний", "Цього", "Минулого"]
    - sentence: "Завтра вранці ми будемо працювати, а ___ відпочивати."
      answer: "потім"
      options: ["потім", "завтра", "скоро", "дуже"]
    - sentence: "___ ми будемо слухати презентацію."
      answer: "Післязавтра"
      options: ["Післязавтра", "Завтра", "Сьогодні", "Потім"]
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/tomorrow-future-tense.yaml`

```yaml
items:
  - lemma: "завтра"
    translation: "tomorrow"
    pos: "adverb"
  - lemma: "буду"
    translation: "I will"
    pos: "verb"
    aspect: "imperfective"
    notes: "Helper verb. Pairs only with imperfective verbs."
  - lemma: "наступний"
    translation: "next"
    pos: "adjective"
    notes: "Requires Genitive case in time expressions like наступного тижня."
  - lemma: "план"
    translation: "plan"
    pos: "noun"
    gender: "m"
  - lemma: "хотіти"
    translation: "to want"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "збиратися"
    translation: "to be going to"
    pos: "verb"
    aspect: "imperfective"
  - lemma: "скоро"
    translation: "soon"
    pos: "adverb"
  - lemma: "потім"
    translation: "then, later"
    pos: "adverb"
  - lemma: "тиждень"
    translation: "week"
    pos: "noun"
    gender: "m"
  - lemma: "рік"
    translation: "year"
    pos: "noun"
    gender: "m"
  - lemma: "післязавтра"
    translation: "the day after tomorrow"
    pos: "adverb"
  - lemma: "вранці"
    translation: "in the morning"
    pos: "adverb"
  - lemma: "вдень"
    translation: "in the day"
    pos: "adverb"
  - lemma: "ввечері"
    translation: "in the evening"
    pos: "adverb"
  - lemma: "майбутнє"
    translation: "future"
    pos: "noun"
    gender: "n"
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md
FIND:
## Практика та підсумок
REPLACE:
## Практика
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md
FIND:
Що я буду робити завтра ввечері? Завтра ввечері я не буду працювати. Я буду відпочивати. Завтра ми збираємося гуляти в парку. Це мій план. Я дуже люблю відпочивати.
REPLACE:
Що я буду робити завтра ввечері? Завтра ввечері я не буду працювати. Я буду відпочивати. Я буду слухати українську музику. Мої друзі будуть пити чай зі мною. Ми будемо говорити про життя. Завтра ми збираємося гуляти в парку. Це мій план. Я дуже люблю відпочивати.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md
FIND:
**Плани на наступний рік.**
Наступного року ми маємо великі плани. Ми збираємося їхати в місто Київ. Це велике місто. Там ми будемо жити один місяць. Ми хочемо знати більше про культуру. Завтра ми будемо слухати українську музику. Потім ми будемо говорити українською мовою. Наступного тижня ми будемо складати план. Це буде дуже цікаво. Ми дуже хочемо їхати в Київ.
REPLACE:
**Плани на наступний рік.**
Наступного року ми маємо великі плани. Ми збираємося їхати в місто Київ. Це велике красиве місто. Там ми будемо жити один місяць. Ми хочемо знати більше про культуру та історію. Завтра ми будемо слухати українську музику. Потім ми будемо говорити українською мовою з нашими друзями. Наступного тижня ми будемо складати план на кожен день. Це буде дуже цікаво. Ми дуже хочемо їхати в Київ і бачити нові місця.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/tomorrow-future-tense.md
FIND:
* Ви будете писати довгий лист. (You will write a long letter.)
* Вони будуть знати правильну відповідь. (They will know the correct answer.)

> [!warning]
REPLACE:
* Ви будете писати довгий лист. (You will write a long letter.)
* Вони будуть знати правильну відповідь. (They will know the correct answer.)
* Ми будемо вивчати українську мову кожного дня. (We will study the Ukrainian language every day.)
* Я буду думати про наші плани. (I will think about our plans.)

> [!warning]
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Applying Review and Audit fixes
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: Issues 1, 2, 3, and 4 from the Fix Plan were already corrected in the provided file contents.
**Self-Correction**: Skipped applying the Review fixes since the source text and YAML already contained the updated, corrected versions (`будувати`, `багато працювати`, correct vocab list, correct fill-in sentence). Focused entirely on resolving the Audit Gate Failures (Outline Compliance and Low Immersion).
**Proposed Tooling Fix**: Ensure the reviewer model uses the most recent file state or skips reporting issues that have already been resolved in a previous phase.
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (2989 chars)
✅ Message sent to Claude (ID: 20961)
✓ Message 20961 acknowledged
   Auto-acknowledged reply #20961 (stdout delivery — no inbox accumulation)
⚠️  GitHub issue creation failed: could not add label: 'review-result' not found

✓ Message 20960 acknowledged
