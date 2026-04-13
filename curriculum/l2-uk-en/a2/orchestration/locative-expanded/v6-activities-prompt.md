<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/locative-expanded.yaml` file for module **20: Місцевий відмінок у нових контекстах** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-identify-the-function-of-locative-in-each-sentence -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->`
- `<!-- INJECT_ACTIVITY: fill-in-locative-forms -->`
- `<!-- INJECT_ACTIVITY: error-correction-prepositions -->`
- `<!-- INJECT_ACTIVITY: quiz-locative-functions -->`
- `<!-- INJECT_ACTIVITY: match-up-expressions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Identify the function of locative in each sentence (physical location, abstract
    domain, temporal, or means)
  items: 8
  type: quiz
- focus: Complete sentences with the correct locative form of the noun (у минулому
    ___, на цьому ___, по ___)
  items: 8
  type: fill-in
- focus: Match locative expressions with their English equivalents across all four
    function types
  items: 8
  type: match-up
- focus: Fix preposition errors (e.g., *у роботі → на роботі, *у телефону → по телефону,
    *на минулому місяці → у минулому місяці)
  items: 8
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- дитинство (childhood)
- молодість (youth)
- майбутнє (future)
- освіта (education)
- мистецтво (art)
required:
- місцевий (locative (case))
- абстрактний (abstract)
- минулий (past, previous)
- місяць (month)
- тиждень (week)
- телефон (phone, telephone)
- подорож (journey, trip)
- зустріч (meeting, encounter)
- думка (thought, opinion)
- проблема (problem)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Місцевий з абстрактними іменниками (Locative with Abstract Nouns) (~600 words total)

Let's listen to a conversation between Mariia and Ihor. They are catching up on life changes after not seeing each other for a long time. Pay attention to how they talk about the past month and their current situations. The word for past or previous is **минулий** (past), and a month is **місяць** (month). The word for a telephone is **телефон** (phone). Notice the different endings they use to describe where they are in life.

> — **Марія:** Привіт, Ігорю! Ми так давно не бачилися. Що нового у твоєму житті? *(Hi, Ihor! We haven't seen each other in so long. What is new in your life?)*
> — **Ігор:** Привіт, Маріє! У минулому місяці я змінив роботу. *(Hi, Mariia! In the past month I changed my job.)*
> — **Марія:** Ого! І де ти зараз працюєш? *(Wow! And where do you work now?)*
> — **Ігор:** Тепер я працюю в освіті. Це дуже цікаво. А ти? *(Now I work in education. It is very interesting. And you?)*
> — **Марія:** Я на новому курсі. Вчора ми розмовляли по телефону з мамою — вона хвилюється. *(I am on a new course. Yesterday we talked on the phone with my mom — she is worried.)*
> — **Ігор:** Не хвилюйся. Це не велика проблема. *(Don't worry. It is not a big problem.)*

In previous lessons, we used the locative case to talk about physical places and locations. The Ukrainian word for this case is **місцевий** (locative). You learned how to say where a person or an object is physically situated in space. Now, we will expand our understanding of this case to talk about abstract ideas, concepts, and contexts. We can use this grammar to talk about the spheres of our lives, our professions, and our general situations without referring to a specific building or street.

Місцевий відмінок допомагає нам говорити про абстрактні речі. Ми використовуємо його, коли говоримо про різні сфери життя.

> *The locative case helps us talk about abstract things. We use it when we talk about different spheres of life.*

When we talk about different professional domains or life situations, we use the prepositions for location with an abstract noun. The word for abstract is **абстрактний** (abstract). This structure translates to "in the domain of" or "in the field of." It shows that someone is immersed in a particular area, not just physically standing inside a room. Let's look at some common examples that you will hear frequently in daily conversations with your friends or colleagues.

Багато людей в Україні працюють в освіті або в сучасній медицині. Мій старший брат має великий досвід у політиці. Що нового у твоєму житті? Моя сестра зараз працює у бізнесі.

> *Many people in Ukraine work in education or in modern medicine. My older brother has great experience in politics. What is new in your life? My sister currently works in business.*

There is one very important exception that you must remember when talking about employment. The word for work is **робота** (work). It always takes the preposition "на". This is a fixed phrase. We always say it this way to mean "at work," and we never use the preposition "у," even when we are talking about the abstract concept of our daily employment. You must contrast this with other abstract nouns that describe fields of study or economy, which usually take "в" or "у".

Зараз мій тато на роботі, тому він не може говорити. В економіці часто бувають серйозні кризи. У європейському мистецтві є багато різних стилів. Моя мама працює в архітектурі.

> *Right now my dad is at work, so he cannot talk. In economics there are often serious crises. In European art there are many different styles. My mom works in architecture.*

:::info
**Preposition rule** — The noun **робота** strictly pairs with the preposition **на** to say "at work." However, most other abstract fields of study or professional domains take the prepositions **у** or **в**.
:::

Many abstract domains are feminine nouns ending in a vowel. To form the locative case for these words, you simply change the final vowel to an "і". However, you must remember the consonant alternation rules that we studied before. If the stem of the word ends in a "к", it changes to a "ц" before the new ending. For example, the word for science is **наука** (science), and it becomes "у науці" in the locative case. The word for politics is **політика** (politics).

Ця нова стаття розповідає про тенденції у сучасній політиці. В українській культурі є багато дуже цікавих традицій. Ми багато читаємо про нові відкриття у науці.

> *This new article talks about trends in modern politics. In Ukrainian culture there are many very interesting traditions. We read a lot about new discoveries in science.*

Let's read some more examples to see how the locative case shifts the meaning from a physical location to an abstract sphere. Notice how these sentences describe situations, thoughts, or professional domains. The word for a thought or opinion is **думка** (thought), and a meeting is a **зустріч** (meeting). The word for a problem is **проблема** (problem). By mastering these grammatical forms, you can have much deeper and more interesting conversations about your career, your interests, and your daily life in Ukrainian.

Він багато років працює в українській політиці. У мене є одна дуже цікава думка. Учора у нас була важлива зустріч. У цій сфері є одна велика проблема.

> *He has been working in Ukrainian politics for many years. I have one very interesting thought. Yesterday we had an important meeting. In this sphere there is one big problem.*

<!-- INJECT_ACTIVITY: quiz-identify-the-function-of-locative-in-each-sentence -->
<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->

## Часовий місцевий відмінок (Temporal Locative) (~650 words total)

We have seen how the locative case is used for an **абстрактний** (abstract) domain. Now we will explore how it expresses time. Listen to this conversation between a student and a teacher. Notice how they use the locative case to talk about weeks, months, and periods of life.

> — **Викладач:** Добрий день! Як ваші справи на цьому тижні? *(Good day! How are your things this week?)*
> — **Студент:** Добрий день! На цьому тижні у мене три заняття. *(Good day! This week I have three classes.)*
> — **Викладач:** Це дуже добре. Що ви читали у вільний час? *(That is very good. What did you read in your free time?)*
> — **Студент:** Я читав цікавий текст у підручнику з історії. *(I read an interesting text in a history textbook.)*
> — **Викладач:** Вам подобається історія України? *(Do you like the history of Ukraine?)*
> — **Студент:** Так, дуже. В дитинстві я мало знав про українську культуру, але зараз це мій улюблений предмет. *(Yes, very much. In childhood I knew little about Ukrainian culture, but now it is my favorite subject.)*
> — **Викладач:** Прекрасно. У минулому місяці ми говорили про традиції. Яка наша нова тема? *(Wonderful. Last month we talked about traditions. What is our new topic?)*

In Ukrainian, we use the prepositions "у" or "в" with the locative case to say that something happens in a specific month. All months are masculine nouns, and most end in the suffix "-ень". When forming the locative case, the vowel "е" drops out before adding the "-і" ending. For example, the word for January is **січень** (January), which becomes "у січні". The word for March is **березень** (March), which becomes "у березні".

Мій брат народився у серпні. Ми плануємо нову подорож у травні. У лютому в Україні часто буває дуже холодно. У жовтні студенти мають багато роботи.

> *My brother was born in August. We are planning a new journey in May. In February it is often very cold in Ukraine. In October students have a lot of work.*

When we do not name the month, we use the word **місяць** (month). To say "last month", both the adjective and the noun take the locative case. The masculine word "місяць" ends in a soft consonant, so it becomes "у місяці". The adjective **минулий** (past, previous) changes to "минулому".

У минулому місяці я прочитав дві цікаві книги. Що ви робили у минулому місяці? Ми хочемо купити нову машину у наступному місяці. У цьому місяці ми маємо багато проєктів.

> *Last month I read two interesting books. What did you do last month? We want to buy a new car next month. This month we have many projects.*

The word for week is **тиждень** (week). Unlike months, the word "тиждень" strictly requires the preposition **на** when expressing time. Just like the months, "тиждень" loses its vowel "е" when it takes the locative ending, becoming "на тижні". You will often see this combined with adjectives.

На цьому тижні ми маємо дуже важливу зустріч. На минулому тижні я був у відрядженні. Що ви плануєте робити на наступному тижні? Вони закінчили роботу на минулому тижні.

> *This week we have a very important meeting. Last week I was on a business trip. What are you planning to do next week? They finished the work last week.*

The locative case also describes major periods of a person's life or general eras. These expressions use "у" or "в" paired with abstract nouns. For instance, the word for childhood is **дитинство** (childhood), which becomes "у дитинстві". The word for youth is **молодість** (youth), which becomes "у молодості". You can also talk about the **майбутнє** (future) or the past.

У дитинстві я дуже любив малювати. Він багато подорожував у молодості. У минулому люди писали довгі листи. Що ми будемо робити у майбутньому?

> *In childhood I really loved to draw. He traveled a lot in his youth. In the past people wrote long letters. What will we do in the future?*

We must contrast the temporal locative with the accusative case. The accusative case is used for specific days of the week or to express duration. The locative case answers the question "Коли?" (When?) for longer periods like weeks, months, or life stages. If you ask "Як довго?" (How long?), you need the accusative.

Коли ви були у Києві? Ми були там у минулому місяці. Як довго ви були у Києві? Ми були там один тиждень. Коли буде зустріч? Вона буде у понеділок.

> *When were you in Kyiv? We were there last month. How long were you in Kyiv? We were there for one week. When will the meeting be? It will be on Monday.*

:::info
**Grammar box** — Days of the week take the accusative case (у понеділок), while weeks, months, and life periods take the locative case (на цьому тижні, у грудні, у молодості).
:::

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->

## По телефону, по радіо: місцевий із прийменником «по» (Locative with "po") (~550 words total)

In Ukrainian, we use the preposition «по» with the **місцевий** (locative) case to talk about the means or channel of communication. This pattern describes how information travels from one person to another. Common examples include «по телефону» (by phone), «по радіо» (on the radio), «по пошті» (by mail), and «по дорозі» (on the way).

Я часто говорю з мамою по телефону. Ми почули гарні новини по радіо. Мій брат надіслав лист по пошті. Ми зустріли друга по дорозі додому.
> *I often speak with my mom by phone. We heard good news on the radio. My brother sent a letter by mail. We met a friend on the way home.*

Notice how these phrases describe the method of connection or the path something takes. The word for mail changes to «пошті», and the word **телефон** (phone, telephone) takes the special locative ending «-у» to form «по телефону».

There is a crucial grammatical distinction between the channel of communication and the topic you are discussing. When you talk "by phone", the phone is the instrument, so you use «по» with the locative case («говорити по телефону»). However, when you talk "about a phone" (for example, if you have a **проблема** (problem) with your device), the phone is the topic of conversation. For topics, Ukrainian uses the preposition «про» with the accusative case («говорити про телефон»).

Вони говорили по телефону про новий проєкт. Ми слухали пісню по радіо, а потім говорили про музику. Студенти розмовляли про нову проблему по дорозі в університет.
> *They talked by phone about a new project. We listened to a song on the radio, and then talked about music. The students talked about a new problem on the way to the university.*

Mixing these up changes the meaning entirely. Always use «по» + locative for how you communicate, and «про» + accusative to share a **думка** (thought, opinion) about a specific subject, whether physical or **абстрактний** (abstract).

Let's look at more examples demonstrating this means of communication in action. It works with various verbs like «дзвонити» (to call), «чути» (to hear), or «надсилати» (to send).

Завтра я подзвоню тобі по телефону. Ми часто чуємо цікаві новини по радіо. Він надіслав важливі документи по пошті.
> *Tomorrow I will call you by phone. We often hear interesting news on the radio. He sent important documents by mail.*

The phrase «по дорозі» is also very common. It means "on the way" and shows the path of your **подорож** (journey, trip). You can use it when describing a **зустріч** (meeting, encounter) or a quick conversation during your commute.

> — **Марія:** Привіт! Ти де зараз? *(Hi! Where are you now?)*
> — **Іван:** Добрий день! Я по дорозі на роботу. *(Good day! I am on the way to work.)*
> — **Марія:** Я надіслала тобі новий план по пошті. *(I sent you a new plan by mail.)*
> — **Іван:** Дякую! Ми поговоримо про це по телефону. *(Thank you! We will talk about it by phone.)*

:::info
**Grammar box** — The preposition «по» followed by the locative case is the traditional, authentic Ukrainian pattern for describing means or paths. In modern grammar, you might sometimes see «по» used with the dative case to express distribution, like giving things out «по одному» (one by one). However, for communication means and paths («по телефону», «по пошті», «по дорозі»), the locative case remains strictly the standard. This preserves the beautiful logic of the locative case showing the "where" or "how" of an action.
:::

In summary, the preposition «по» transforms the locative case from a static location into an active instrument, a channel of communication, or a path of movement. This adds a dynamic layer of meaning to the case. If you look back at the **минулий** (past, previous) **місяць** (month) or **тиждень** (week), you will likely realize how often you communicated «по телефону» or heard news «по радіо»!

<!-- INJECT_ACTIVITY: fill-in-locative-forms -->
<!-- INJECT_ACTIVITY: error-correction-prepositions -->

## Місцевий відмінок: від місця до сенсу (From Place to Meaning)

The **місцевий** (locative (case)) is far more than just a tool for pointing at a map. It expands from answering simple questions about physical locations to framing entire contexts. We can use it to describe an **абстрактний** (abstract) domain, such as an industry, or look back at a **минулий** (past, previous) period to set the stage for a story. 

**Читаємо українською:**
Моя сестра працює в медицині. У минулому році вона жила в Одесі. Зараз вона працює в лікарні. Ми часто розмовляємо по телефону. Вона розповідає про життя в новому місті. Я дуже радий за неї.

> *My sister works in medicine. In the past year, she lived in Odesa. Now she works in a hospital. We often talk by phone. She tells about life in the new city. I am very happy for her.*

Let's consolidate these four functions. Whether pinpointing a specific **місяць** (month) for an event or organizing a busy **тиждень** (week) in your schedule, they all share the same locative endings but serve fundamentally different purposes.

| Функція (Function) | Питання (Question) | Приклад (Example) |
| :--- | :--- | :--- |
| **Фізичне місце** (Physical location) | Де? (Where?) | У місті, на столі |
| **Абстрактна сфера** (Abstract domain) | Де? / У чому? (In what?) | У житті, в освіті |
| **Час** (Temporal) | Коли? (When?) | У січні, на тижні |
| **Засіб / Канал** (Means / Channel) | Як? (How?) | По телефону, по радіо |

**Читаємо українською:**
Я часто слухаю музику по радіо. У лютому я відпочивав у горах. Там я познайомився з цікавими людьми. Моє життя в Києві також дуже цікаве. На цьому тижні я йду на новий ярмарок. В дитинстві я не любив такі події, але зараз люблю.

> *I often listen to music on the radio. In February, I rested in the mountains. There I met interesting people. My life in Kyiv is also very interesting. This week I am going to a new fair. In childhood I did not like such events, but now I do.*

You can build complex sentences by combining multiple functions. Whether you are planning a **подорож** (journey, trip), scheduling a **зустріч** (meeting, encounter), or just talking by **телефон** (phone, telephone), you can merge these details naturally.

> — **Анна:** Привіт! Ми так давно не бачилися. *(Hi! We haven't seen each other for so long.)*
> — **Марко:** Привіт! Так, у минулому місяці я був у відрядженні. *(Hi! Yes, last month I was on a business trip.)*
> — **Анна:** Як пройшла твоя подорож? *(How was your journey?)*
> — **Марко:** Дуже добре. Ми багато говорили про нові проєкти по дорозі в офіс. *(Very well. We talked a lot about new projects on the way to the office.)*
> — **Анна:** А на цьому тижні у тебе є вільний час? *(And this week do you have free time?)*
> — **Марко:** Так, я вільний у суботу. Ми можемо поговорити по телефону. *(Yes, I am free on Saturday. We can talk by phone.)*

By mastering these varied uses, your Ukrainian becomes much more expressive. If you want to share a complex **думка** (thought, opinion) or discuss a serious **проблема** (problem), the locative case helps you specify exactly where, when, and how it occurred. 

> — **Олег:** У тебе є проблема на роботі? *(Do you have a problem at work?)*
> — **Ірина:** Так, в освіті зараз багато нових правил. *(Yes, in education there are many new rules now.)*
> — **Олег:** Це цікава думка. Я читав про це в інтернеті. *(That is an interesting thought. I read about it on the internet.)*
> — **Ірина:** У минулому році все було простіше. *(Last year everything was simpler.)*
> — **Олег:** Не хвилюйся, у житті завжди є зміни. *(Don't worry, in life there are always changes.)*
> — **Ірина:** Дякую! Твоя підтримка дуже допомагає в біді. *(Thank you! Your support helps a lot in trouble.)*

:::tip
**Did you know?** — The preposition «по» is incredibly versatile. While it denotes means of communication («по телефону») or a path («по дорозі») with the locative case, you will also see it used with other cases to express distribution. However, for the methods we discussed here, the locative case is the authentic standard.
:::

<!-- INJECT_ACTIVITY: quiz-locative-functions -->
<!-- INJECT_ACTIVITY: match-up-expressions -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: locative-expanded
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

**Level: A2 (Module 20/60) — ELEMENTARY**

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
