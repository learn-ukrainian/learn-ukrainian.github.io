<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 20: Місцевий відмінок у нових контекстах (A2, A2.3 [Dative Case])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-020
level: A2
sequence: 20
slug: locative-expanded
version: '1.0'
title: Місцевий відмінок у нових контекстах
subtitle: Абстрактні іменники, часові вирази та тема розмови у місцевому відмінку
focus: grammar
pedagogy: PPP
phase: A2.3 [Dative Case]
word_target: 2000
objectives:
  - Learner can use the locative case with abstract nouns to express contexts
    and domains (у житті, в освіті, на роботі, у політиці).
  - Learner can use temporal locative expressions for months, weeks, and
    periods (у минулому місяці, на цьому тижні, у дитинстві).
  - Learner can use topic-marking locative with по + locative for
    communication topics (по телефону, по радіо) and розмовляти/говорити
    про + accusative vs. по + locative distinctions.
  - Learner can combine locative with prepositions у/в, на, по in varied
    real-life contexts beyond simple physical location.
dialogue_situations:
  - setting: 'Two friends catching up after a long time — talking about life
      changes: Що нового у твоєму житті? — У минулому місяці я змінила роботу.
      Тепер працюю в освіті. А ти? — Я на новому курсі. Розмовляли по
      телефону з мамою — вона хвилюється.'
    speakers:
      - Марія
      - Ігор
    motivation: 'Natural catch-up triggers all three locative extensions:
      abstract (у житті, в освіті), temporal (у минулому місяці), topic
      (по телефону)'
  - setting: 'Student discussing schedule and interests with a tutor: На цьому
      тижні у мене три заняття. У вільний час я читаю про Україну — у
      підручнику з історії. В дитинстві я мало знав про українську культуру.'
    speakers:
      - Студент
      - Викладач
    motivation: 'Temporal locative (на цьому тижні, в дитинстві) + abstract
      domain (в історії, про культуру)'
content_outline:
  - section: 'Місцевий з абстрактними іменниками (Locative with Abstract Nouns)'
    words: 550
    points:
      - 'A1 taught locative for physical location (у місті, на вулиці). Now
        expanding to abstract domains and contexts.'
      - 'Common abstract locative phrases: у житті (in life), в освіті (in
        education), у політиці (in politics), на роботі (at work), в економіці
        (in economics), у мистецтві (in art).'
      - 'Pattern: у/в + abstract noun in locative = "in the domain/field of."
        Note: на роботі (not *у роботі) — на is fixed for робота.'
      - 'Practice forming locative of abstract feminine nouns in -а/-я:
        наука→у науці, політика→у політиці, культура→у культурі.'
  - section: 'Часовий місцевий відмінок (Temporal Locative)'
    words: 600
    points:
      - 'Months: у січні, у лютому, у березні... all months use у/в + locative.
        Masculine months in -ень: -ні (січень→у січні). Neuter місяць compounds:
        у минулому місяці, у наступному місяці.'
      - 'Weeks: на цьому тижні, на минулому тижні, на наступному тижні. Note:
        тиждень uses на (not у).'
      - 'Life periods: у дитинстві (in childhood), у молодості (in youth),
        у старості (in old age), у минулому (in the past), у майбутньому
        (in the future).'
      - 'Contrast with accusative for duration: у понеділок (on Monday, acc.)
        vs. у минулому місяці (last month, loc.). The question test: Коли?
        (temporal loc.) vs. Як довго? (duration, acc.).'
  - section: 'По телефону, по радіо: місцевий із прийменником «по» (Locative
      with "po")'
    words: 500
    points:
      - 'Topic/means with по + locative: по телефону (by phone), по радіо
        (on the radio), по пошті (by mail), по дорозі (on the way).'
      - 'Distinction: говорити по телефону (the medium of communication) vs.
        говорити про телефон (about the phone as a topic). По + locative =
        means/channel. Про + accusative = topic.'
      - 'Common phrases: Я подзвоню по телефону. Ми почули по радіо. Він
        надіслав по пошті. Зустрілися по дорозі додому.'
      - 'Note: по + locative is the traditional Ukrainian pattern. Some modern
        usage shifts to по + dative for distribution (по одному), but for
        communication means, locative is standard.'
  - section: 'Місцевий відмінок: від місця до сенсу (From Place to Meaning)'
    words: 350
    points:
      - 'Summary: locative is not just "where" — it answers де? (location),
        коли? (time), and як? (means/channel).'
      - 'Consolidation table: physical (у місті), abstract (у житті), temporal
        (у січні), means (по телефону) — all locative, four different functions.'
      - 'Practice: building sentences that use 2-3 locative functions together:
        У минулому місяці я розмовляв по телефону з другом у Києві.'
vocabulary_hints:
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
  recommended:
    - дитинство (childhood)
    - молодість (youth)
    - майбутнє (future)
    - освіта (education)
    - мистецтво (art)
activity_hints:
  - type: quiz
    focus: 'Identify the function of locative in each sentence (physical
      location, abstract domain, temporal, or means)'
    items: 8
  - type: fill-in
    focus: Complete sentences with the correct locative form of the noun
      (у минулому ___, на цьому ___, по ___)
    items: 8
  - type: match-up
    focus: Match locative expressions with their English equivalents across
      all four function types
    items: 8
  - type: error-correction
    focus: 'Fix preposition errors (e.g., *у роботі → на роботі, *у
      телефону → по телефону, *на минулому місяці → у минулому місяці)'
    items: 8
references:
  - title: Заболотний Grade 5, §28-30
    notes: Місцевий відмінок іменників, прийменники
  - title: Заболотний Grade 6, §34-35
    notes: Часові конструкції з місцевим відмінком
  - title: 'ULP: Ukrainian Cases — Locative'
    url: https://www.ukrainianlessons.com/locative-case/
    notes: Locative case uses including temporal and abstract

</plan_content>

## Generated Content

<generated_module_content>
## Місцевий з абстрактними іменниками (Locative with Abstract Nouns) (~600 words total)

Let's listen to a conversation between Mariia and Ihor. They are catching up on life changes after not seeing each other for a long time. Pay attention to how they talk about the past month and their current situations. The word for past or previous is **минулий** (past), and a month is **місяць** (month). The word for a telephone is **телефон** (phone). Notice the different endings they use to describe where they are in life.

> — **Марія:** Привіт, Ігорю! Ми так давно не бачилися. Що нового у твоєму житті? *(Hi, Ihor! We haven't seen each other in so long. What is new in your life?)*
> — **Ігор:** Привіт, Маріє! У минулому місяці я змінив роботу. *(Hi, Mariia! In the past month I changed my job.)*
> — **Марія:** Ого! І де ти зараз працюєш? *(Wow! And where do you work now?)*
> — **Ігор:** Тепер я працюю в освіті. Це дуже цікаво. А ти? *(Now I work in education. It is very interesting. And you?)*
> — **Марія:** Я на новому курсі. Вчора ми розмовляли по телефону з мамою — вона хвилюється. *(I am on a new course. Yesterday we talked on the phone with my mom — she is worried.)*
> — **Ігор:** Не хвилюйся. Це невелика проблема. *(Don't worry. It is not a big problem.)*

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

Let's read some more examples to see how the locative case shifts the meaning from a physical location to an abstract sphere. Notice how these sentences describe situations, thoughts, or professional domains. The word for a thought or opinion is **думка** (thought), and a meeting is a **зустріч** (meeting). The word for a problem is **проблема** (problem). 

Він багато років працює в українській політиці. У мене є одна дуже цікава думка. Учора у нас була важлива зустріч. У цій сфері є одна велика проблема.

> *He has been working in Ukrainian politics for many years. I have one very interesting thought. Yesterday we had an important meeting. In this sphere there is one big problem.*

## Часовий місцевий відмінок (Temporal Locative) (~650 words total)

We have seen how the locative case is used for an **абстрактний** (abstract) domain. Now we will explore how it expresses time. Listen to this conversation between a student and a teacher. Notice how they use the locative case to talk about weeks, months, and periods of life.

> — **Викладач:** Добрий день! Що у вас заплановано на цьому тижні? *(Good day! What do you have planned for this week?)*
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

## По телефону, по радіо: місцевий із прийменником «по» (Locative with "po") (~550 words total)

In Ukrainian, we use several common expressions with «по» to talk about a channel or path, such as «по телефону» (by phone), «по радіо» (on the radio), and «по дорозі» (on the way). For sending something by mail, standard Ukrainian often prefers «поштою», so learners should memorize the whole expression rather than generalize «по» to every noun.

Я часто говорю з мамою по телефону. Ми почули гарні новини по радіо. Мій брат надіслав лист поштою. Ми зустріли друга по дорозі додому.
> *I often speak with my mom by phone. We heard good news on the radio. My brother sent a letter by mail. We met a friend on the way home.*

Notice how these phrases describe the method of connection or the path something takes. Because some Ukrainian forms are syncretic, it is safer to learn the full expressions: «по телефону», «по радіо», «по дорозі», but «надіслати лист поштою».

There is a crucial grammatical distinction between the channel of communication and the topic you are discussing. When you talk "by phone", the phone is the instrument, so you use «по» with the locative case («говорити по телефону»). However, when you talk "about a phone" (for example, if you have a **проблема** (problem) with your device), the phone is the topic of conversation. For topics, Ukrainian uses the preposition «про» with the accusative case («говорити про телефон»).

Вони говорили по телефону про новий проєкт. Ми слухали пісню по радіо, а потім говорили про музику. Студенти розмовляли про нову проблему по дорозі в університет.
> *They talked by phone about a new project. We listened to a song on the radio, and then talked about music. The students talked about a new problem on the way to the university.*

Mixing these up changes the meaning entirely. Use «по телефону» and «по радіо» for the channel of communication, «поштою» for sending something by mail, and «про» + accusative to share a **думка** (thought, opinion) about a specific subject, whether physical or **абстрактний** (abstract).

Let's look at more examples demonstrating this means of communication in action. It works with various verbs like «дзвонити» (to call), «чути» (to hear), or «надсилати» (to send).

Завтра я подзвоню тобі по телефону. Ми часто чуємо цікаві новини по радіо. Він надіслав важливі документи поштою.
> *Tomorrow I will call you by phone. We often hear interesting news on the radio. He sent important documents by mail.*

The phrase «по дорозі» is also very common. It means "on the way" and shows the path of your **подорож** (journey, trip). You can use it when describing a **зустріч** (meeting, encounter) or a quick conversation during your commute.

> — **Марія:** Привіт! Ти де зараз? *(Hi! Where are you now?)*
> — **Іван:** Добрий день! Я по дорозі на роботу. *(Good day! I am on the way to work.)*
> — **Марія:** Я надіслала тобі новий план поштою. *(I sent you a new plan by mail.)*
> — **Іван:** Дякую! Ми поговоримо про це по телефону. *(Thank you! We will talk about it by phone.)*

:::info
**Grammar box** — Fixed expressions like «по телефону», «по радіо», and «по дорозі» can mark a channel or path. But when you mean "by mail", standard Ukrainian often prefers the instrumental form «поштою». Do not confuse these expressions with «про» + accusative, which names the topic of conversation.
:::

In summary, the preposition «по» transforms the locative case from a static location into an active instrument, a channel of communication, or a path of movement. This adds a dynamic layer of meaning to the case. If you look back at the **минулий** (past, previous) **місяць** (month) or **тиждень** (week), you will likely realize how often you communicated «по телефону» or heard news «по радіо»!

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-with-the-correct-locative-form -->
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

 If you want to share a complex **думка** (thought, opinion) or discuss a serious **проблема** (problem), the locative case helps you specify exactly where, when, and how it occurred. 

> — **Олег:** У тебе є проблема на роботі? *(Do you have a problem at work?)*
> — **Ірина:** Так, в освіті зараз багато нових правил. *(Yes, in education there are many new rules now.)*
> — **Олег:** Це цікава думка. Я читав про це в інтернеті. *(That is an interesting thought. I read about it on the internet.)*
> — **Ірина:** У минулому році все було простіше. *(Last year everything was simpler.)*
> — **Олег:** Не хвилюйся, у житті завжди є зміни. *(Don't worry, in life there are always changes.)*
> — **Ірина:** Дякую! Твоя підтримка дуже допомагає в біді. *(Thank you! Your support helps a lot in trouble.)*

:::tip
**Did you know?** — The preposition «по» is incredibly versatile. While it denotes means of communication («по телефону») or a path («по дорозі») with the locative case, you will also see it used with other cases to express distribution. However, for the methods we discussed here, the locative case is the authentic standard.
:::

<!-- INJECT_ACTIVITY: quiz-identify-the-function-of-locative-in-each-sentence -->
<!-- INJECT_ACTIVITY: match-up-expressions -->
</generated_module_content>

**PIPELINE NOTE — Word count: 2926 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 313 words | Not found: 9 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Ігорю — NOT IN VESUM
  ✗ Ірина — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Маріє — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ ень — NOT IN VESUM

All 313 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
