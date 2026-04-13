<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 45: Розповіді та подорожі (A2, A2.6 [Aspect, Tenses, and Motion])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-045
level: A2
sequence: 45
slug: telling-stories-and-travel
version: '1.0'
title: Розповіді та подорожі
subtitle: Розповідаємо про минуле з видом дієслова та плануємо подорожі з дієсловами руху
focus: communication
pedagogy: TBL
phase: A2.6 [Aspect, Tenses, and Motion]
word_target: 2000
objectives:
- Learner can narrate a past event as a coherent story, correctly alternating between imperfective (background,
  process) and perfective (completed actions, plot events) past tense verbs.
- Learner can describe travel plans using motion verbs (іти/ходити, їхати/їздити, летіти/літати) with
  appropriate prepositions and cases for origin, destination, and route.
- Learner can participate in a dialogue about a past trip — answering questions about where they went,
  how they traveled, what they did, and what happened.
- Learner can write a short narrative (8-10 sentences) about a real or imagined journey, integrating past
  tense aspect, motion verbs, and time expressions.
dialogue_situations:
- setting: 'Scenario 1: A funny thing happened at the вокзал (m, train station) yesterday. Scenario 2:
    Planning a trip to Карпати (pl) — booking хатинка (f, cabin). Scenario 3: Showing vacation photos
    from Одеса — пляж (m), море (n), ресторан (m).'
  speakers:
  - Друзі (sharing stories)
  motivation: 'Past + future + travel: вокзал(m), хатинка(f), пляж(m), море(n)'
content_outline:
- section: 'Сценарій 1: Що вчора трапилось? (Scenario 1: What Happened Yesterday?)'
  words: 550
  points:
  - 'Story-telling structure: setting the scene (imperfective) → events (perfective) → reactions (both
    aspects). Example: Був теплий вечір. Я сидів на балконі і читав книгу (background — impf.). Раптом
    подзвонив друг (event — pf.) і запросив мене на вечерю (event — pf.).'
  - 'Time connectors for narratives: спочатку (at first), потім (then), після цього (after that), нарешті
    (finally), тим часом (meanwhile), раптом (suddenly), у цей момент (at that moment).'
  - 'Practice: learner reads a short story with mixed aspects, identifies which verbs are background (impf.)
    and which are plot events (pf.).'
  - 'Guided storytelling: given a sequence of pictures or prompts, learner tells what happened using correct
    aspect choices.'
- section: 'Сценарій 2: Плануємо подорож (Scenario 2: Planning a Trip)'
  words: 500
  points:
  - 'Dialogue: two friends planning a trip to Lviv. Куди поїдемо? (pf. — specific trip) Як доберемося?
    Поїдемо потягом чи полетимо? Де зупинимося? (pf. — specific result) Що будемо робити? (impf. — general
    activities).'
  - 'Travel vocabulary: подорож (trip), квиток (ticket), потяг (train), літак (airplane), автобус (bus),
    вокзал (station), аеропорт (airport), готель (hotel), зупинитися (to stay/stop).'
  - 'Motion verbs in context: Ми поїдемо потягом до Львова (pf. — specific trip). Зазвичай ми їздимо туди
    влітку (impf. — habitual). Літак летить дві години (unidirectional — in progress).'
  - 'Preposition patterns: поїхати до + Gen. (to a city/person), поїхати на + Acc. (to an event/area —
    на море, на фестиваль), прилетіти з + Gen. (from a place).'
- section: 'Сценарій 3: Розкажи про поїздку! (Scenario 3: Tell Me About Your Trip!)'
  words: 550
  points:
  - 'Dialogue: one friend asks about another''s recent trip. Де ти був? Куди їздив? Як доїхав? Що бачив?
    Що найбільше сподобалось? — All answered using past tense with correct aspect.'
  - 'Sample narrative: Минулого тижня я їздив до Одеси (impf. — round trip). Ми поїхали потягом (pf. —
    departed). Доїхали за десять годин (pf. — completed). Там ми ходили по місту (impf. — walked around),
    відвідали музей (pf. — specific event), купили сувеніри (pf.) і з''їли найсмачніший борщ (pf.).'
  - 'Expressing impressions: Мені дуже сподобалось (I really liked it). Було чудово / цікаво / весело
    (It was wonderful / interesting / fun). Я хочу поїхати ще раз (I want to go again).'
  - 'Contrast: їздив (was there, round-trip completed) vs. поїхав (departed, left). Я їздив до Києва (I
    went to Kyiv and came back) vs. Він поїхав до Києва (He left for Kyiv — may still be there).'
- section: 'Мовленнєве завдання: Моя подорож (Speaking Task: My Journey)'
  words: 400
  points:
  - 'Guided writing task: write 8-10 sentences about a real or imagined trip. Include: where you went
    (motion verb + destination), how you traveled (vehicle — Instr.), what you did (perfective events),
    what was happening around you (imperfective background).'
  - 'Checklist: Did you use at least 2 motion verbs? Did you alternate aspects? Did you use time connectors?
    Did you describe impressions?'
  - Model answer for comparison, annotated with aspect labels.
vocabulary_hints:
  required:
  - подорож (trip, journey)
  - розповідати / розповісти (to tell/narrate — impf./pf.)
  - трапитися (to happen)
  - квиток (ticket)
  - потяг (train)
  - вокзал (station)
  - зупинитися (to stay, to stop — pf.)
  - доїхати (to reach by vehicle — pf.)
  - сподобатися (to like — pf.)
  - враження (impression)
  recommended:
  - спочатку (at first)
  - потім (then)
  - нарешті (finally)
  - тим часом (meanwhile)
  - сувенір (souvenir)
activity_hints:
- type: fill-in
  focus: Complete a travel narrative by choosing the correct verb form (aspect and motion verb type) for
    each blank
  items: 8
- type: quiz
  focus: Read a past trip description and answer comprehension questions about what happened, in what
    order, and how the person traveled
  items: 8
- type: match-up
  focus: Match travel situations with the correct motion verb and preposition combination (їхати до +
    Gen., летіти на + Acc.)
  items: 8
- type: error-correction
  focus: Find and correct grammar errors in sentences
  items: 6
references:
- title: Заболотний Grade 6, §42-44, §39-41
  notes: Вид дієслова + дієслова руху — combined in communicative context
- title: 'ULP: Ukrainian Travel Vocabulary'
  url: https://www.ukrainianlessons.com/travel/
  notes: Travel-related vocabulary and dialogues with audio

</plan_content>

## Generated Content

<generated_module_content>
## Сценарій 1: Що вчора трапилось? (~600 words)

Уявіть ситуацію. Два друга, Андрій та Олена, зустрілися в місті. Андрій хоче **розповісти** цікаву історію, яка вчора сталася на вокзалі.

> *Imagine the situation. Two friends, Andriy and Olena, met in the city. Andriy wants to tell an interesting story that happened yesterday at the train station.*

> — **Андрій:** Привіт, Олено! Уявляєш, що вчора **трапилося**? *(Hi, Olena! Can you imagine what happened yesterday?)*
> — **Олена:** Привіт! Що таке? Ти купував **квиток** на **потяг**? *(Hi! What is it? Were you buying a ticket for the train?)*
> — **Андрій:** Так. Був теплий вечір. Я сидів на **вокзалі**, пив каву і просто чекав. *(Yes. It was a warm evening. I was sitting at the station, drinking coffee, and just waiting.)*
> — **Олена:** І що далі? *(And what next?)*
> — **Андрій:** Раптом мені подзвонив старий друг. Він запросив мене на вечерю! *(Suddenly my old friend called me. He invited me to dinner!)*
> — **Олена:** Клас! Він теж планував **подорож**? *(Cool! Was he planning a trip too?)*
> — **Андрій:** Ні, він просто гуляв поруч. Ми зустрілися і чудово провели час. *(No, he was just walking nearby. We met and had a wonderful time.)*

Telling a good story requires a mix of verb aspects. When you set the scene, you describe a process using imperfective verbs. When the main event begins, you take perfective verbs.

Для гарної розповіді нам потрібні різні дієслова. Коли ми описуємо процес, ми використовуємо дієслова недоконаного виду. Коли починається головна подія, ми беремо дієслова доконаного виду.

Look at Andriy's story.

**Був теплий вечір. Я сидів на вокзалі і пив каву.** — *It was a warm evening. I was sitting at the station and drinking coffee.*

The verbs **був**, **сидів**, and **пив** are imperfective background actions. 

**Раптом подзвонив друг і запросив мене.** — *Suddenly a friend called and invited me.*

Then the verbs **подзвонив** and **запросив** act as perfective interruptions.

To connect these actions chronologically, we use special words. They help our story flow smoothly from the beginning to the end.

Щоб історія була логічною, ми використовуємо слова для часу. Вони поєднують наші речення і роблять розповідь цікавою.

Here are the most important connectors you will need:
*   **спочатку** (at first)
*   **потім** (then)
*   **після цього** (after that)
*   **нарешті** (finally)
*   **тим часом** (meanwhile)
*   **раптом** (suddenly)
*   **у цей момент** (at that moment)

Let's see how these connectors and verbs work together in a short narrative about a trip.

Минулого тижня я вирішив поїхати до Києва і **зупинитися** у друзів. **Спочатку** я купив квиток і зібрав речі. **Потім** я приїхав на вокзал. Я сидів у вагоні і читав книгу. **Тим часом** інші люди шукали місця, а діти сміялися. **Раптом** потяг рушив. Я дивився у вікно і пив чай. **Після цього** я трохи поспав. **Нарешті** ми **доїхали** до міста. Мені все дуже **сподобалося**, і залишилися чудові **враження**!

> *Last week I decided to go to Kyiv and stay with friends. At first, I bought a ticket and packed my things. Then I arrived at the station. I was sitting in the car and reading a book. Meanwhile, other people were looking for seats, and children were laughing. Suddenly the train started moving. I was looking out the window and drinking tea. After that, I slept a little. Finally, we reached the city. I really liked everything, and wonderful impressions remain!*

Let's analyze this story. We start with the main sequence of events using perfective verbs. The words **купив** and **приїхав** are completed actions that move the timeline forward.

:::info
**Grammar box**
Imperfective verbs create a picture, while perfective verbs advance the plot. Imagine imperfective verbs as a long line, and perfective verbs as an "X" on that line.
:::

Then we switch to the background scene. The verbs **сидів**, **читав**, and **сміялися** are imperfective. They describe what was happening while the character was waiting. The connector **тим часом** introduces parallel ongoing actions.

Finally, the word **раптом** brings us back to the main plot. The perfective verb **рушив** shows a sudden action. Later, we get the final completed events: the character slept (**поспав**) and reached the destination (**доїхали**). This alternation makes the story dynamic.

<!-- INJECT_ACTIVITY: quiz-past-trip-comprehension -->

## Сценарій 2: Плануємо подорож (~550 words)

> — **Марко:** Привіт! Ти вже знаєш, куди поїдемо у відпустку цього літа? *(Hi! Do you already know where we will go on vacation this summer?)*
> — **Олена:** Привіт! Я пропоную поїхати в Карпати. Це буде чудова подорож у гори! *(Hi! I suggest going to the Carpathians. It will be a wonderful trip to the mountains!)*
> — **Марко:** Класна ідея. А як доберемося туди? Поїдемо потягом чи полетимо літаком? *(Great idea. And how will we get there? Will we go by train or fly by airplane?)*
> — **Олена:** Поїдемо потягом. Треба купити квиток на завтрашній рейс. *(We will go by train. We need to buy a ticket for tomorrow's trip.)*
> — **Марко:** Добре. А де зупинимося, коли приїдемо? *(Good. And where will we stay when we arrive?)*
> — **Олена:** Я вже знайшла гарне місце для нас і забронювала маленьку дерев'яну хатинку в лісі. *(I have already found a nice place for us and booked a small wooden cabin in the forest.)*
> — **Марко:** Супер! А що будемо робити там цілий тиждень? *(Super! And what will we do there all week?)*
> — **Олена:** Будемо гуляти, дихати свіжим повітрям, збирати гриби і просто відпочивати. *(We will walk, breathe fresh air, pick mushrooms, and just relax.)*

Для такої поїздки вам потрібні нові слова. Ваша **подорож** (trip) починається тоді, коли ви купуєте **квиток** (ticket). Ви можете обрати різний транспорт: швидкий **потяг** (train), сучасний **літак** (airplane) або зручний **автобус** (bus). Якщо ви подорожуєте потягом, ви їдете на **вокзал** (train station). Коли ви летите літаком, ви їдете в **аеропорт** (airport). На місці вам потрібно знайти комфортний **готель** (hotel) або хатинку. Там ви зможете **зупинитися** (to stay) на кілька днів.

> *For such a trip, you need new words. Your **подорож** (trip) begins when you buy a **квиток** (ticket). You can choose different transport: a fast **потяг** (train), a modern **літак** (airplane), or a comfortable **автобус** (bus). If you travel by train, you go to the **вокзал** (train station). When you fly by airplane, you go to the **аеропорт** (airport). At the location, you need to find a comfortable **готель** (hotel) or a cabin. There you will be able to **зупинитися** (to stay) for a few days.*

When planning a trip, we naturally talk about the future. In Ukrainian, we use different forms of the future tense depending on the aspect of the verb. If we are talking about a specific, one-time action that will be completed, we use the perfective future tense.

Наприклад, якщо ми плануємо конкретну поїздку, ми кажемо: «Ми поїдемо потягом до Львова». Слово «поїдемо» — це дієслово доконаного виду. Але якщо ми описуємо загальні плани під час відпустки, ми беремо складену форму. Ми кажемо: «Там ми будемо багато гуляти».

> *For example, if we plan a specific trip, we say: "We will go by train to Lviv." The word "поїдемо" is a perfective verb. But if we describe general plans during the vacation, we take the compound form. We say: "There we will walk a lot."*

This contrasts with our regular habits. When we describe repeated movement, we use imperfective verbs of motion such as **їздити**, **ходити**, and **літати**. For example: «Зазвичай ми їздимо туди щоліта», «У горах ми щодня ходимо до лісу», «Щоліта ми літаємо на море». For one specific departure, we switch to perfective forms such as **поїхати**, **піти**, or **полетіти**.

:::info
**Grammar box**
When you use verbs of motion, you must choose the correct preposition and case to show your direction or origin. This tells the listener exactly where you are heading.
:::

To express your destination, Ukrainian uses two main prepositions. We use **до** with the Genitive case for cities, countries, and people (e.g., **до Львова**, **до друга**). We use **на** with the Accusative case for events, open areas, or public places (e.g., **на море**, **на фестиваль**, **на вокзал**). To say where you arrived from, use **з** (or **зі**, **із**) with the Genitive case (e.g., **зі Швеції**, **з Києва**).

Ось кілька прикладів, як поєднувати дієслова руху, транспорт і напрямок:

*   Наступного тижня ми поїдемо **автобусом** до Києва.
*   Вони полетять **літаком** на море.
*   Завтра я поїду **потягом** до брата.
*   Моя сестра прилетіла **з** Лондона.
*   Сьогодні ввечері ми поїдемо **на** вокзал.

> *Here are a few examples of how to combine verbs of motion, transport, and direction:*
> *   *Next week we will go by bus to Kyiv.*
> *   *They will fly by airplane to the sea.*
> *   *Tomorrow I will go by train to my brother.*
> *   *My sister flew in from London.*
> *   *Tonight we will go to the station.*

Notice that the vehicle you use for travel is put directly into the Instrumental case (автобусом, літаком, потягом) without any prepositions. This answers the question "by what means?".

<!-- INJECT_ACTIVITY: match-up-match-travel-situations-with-the-correct-motion-verb-and-preposition-combination-gen-acc -->

## Сценарій 3: Розкажи про поїздку! (~600 words)

When we return home, friends always ask us to **розповісти** (to tell) about our **подорож** (trip). Sharing stories and looking at photos together is a great way to practice your language skills. Let's read a short dialogue between Maksym and Olena.

> — **Максим:** Привіт, Олено! Де ти була минулого тижня? *(Hi, Olena! Where were you last week?)*
> — **Олена:** Привіт! Я їздила до Одеси. *(Hi! I went to Odesa.)*
> — **Максим:** Клас! Як ви доїхали? *(Cool! How did you get there?)*
> — **Олена:** Ми поїхали потягом. Це було дуже зручно. *(We went by train. It was very comfortable.)*
> — **Максим:** Що ви там бачили? *(What did you see there?)*
> — **Олена:** Ми ходили на пляж і дивилися на море. А ввечері ми знайшли чудовий ресторан. *(We went to the beach and looked at the sea. And in the evening we found a wonderful restaurant.)*
> — **Максим:** Що тобі найбільше сподобалося? *(What did you like the most?)*
> — **Олена:** Мені дуже сподобалася архітектура міста. Ось фото з пляжу, моря і ресторану. *(I really liked the architecture of the city. Here are photos from the beach, the sea, and the restaurant.)*
> — **Максим:** Клас! Тепер я теж хочу поїхати до Одеси. *(Cool! Now I want to go to Odesa too.)*

When talking about past trips, choosing the right verb of motion is crucial. The difference between **їздив** and **поїхав** is a very common point of confusion for learners. We use the imperfective verb **їздив** (went/travelled) when the trip is entirely completed. It means you went to a place and you have already returned back home. In contrast, the perfective verb **поїхав** (departed/left) focuses specifically on the moment of departure or a one-way trip.

Ось два приклади, які показують цю різницю. Перший: «Я їздив до Києва». Це означає, що я був у Києві, але зараз я вже вдома. Другий: «Мій брат поїхав до Києва». Це означає, що він вирушив у дорогу, і, можливо, він досі там.

> *Here are two examples that show this difference. First: "I went to Kyiv." This means that I was in Kyiv, but now I am already at home. Second: "My brother left for Kyiv." This means that he set off on the journey, and perhaps he is still there.*

:::info
**Grammar box**
Use **їздив** for a round-trip that is over. Use **поїхав** to say someone left for a destination and might not be back yet.
:::

Now let's look at how we combine these verbs to tell a complete story. A good narrative mixes motion verbs with different aspects to show the flow of the journey. When you reach the **вокзал** (station) with your **квиток** (ticket), you usually board a **потяг** (train) or bus. By switching aspects, you can guide your listener through the timeline of events.

Минулого тижня я їздив до Одеси на відпочинок. Спочатку ми поїхали потягом і **доїхали** (to reach) туди за десять годин. В Одесі ми вирішили **зупинитися** (to stay) в маленькому готелі біля моря. Там ми довго ходили по місту і фотографували старі будинки. Наступного дня ми відвідали музей, купили сувеніри для друзів і з'їли найсмачніший український борщ.

> *Last week I went to Odesa for a vacation. First we got on the train. We managed to reach there in ten hours. In Odesa, we decided to stay in a small hotel near the sea. There we walked around the city for a long time and photographed old buildings. The next day we visited a museum, bought souvenirs for friends, and ate the most delicious Ukrainian borscht.*

After telling the events of the story, you usually want to share your feelings and opinions. We use specific phrases to describe the overall **враження** (impression) of the experience. The most common phrase is **мені дуже сподобалось** (I really liked it). Note that **сподобатися** (to like) is a perfective verb here, because it summarizes your final opinion after the completed trip. You use it to reflect on the entire journey as one finished event.

Ти можеш також сказати: «Було чудово», «Було дуже цікаво» або «Було весело». Якщо поїздка була справді гарною, люди часто додають: «Я хочу поїхати туди ще раз».

> *You can also say: "It was wonderful", "It was very interesting", or "It was fun". If the trip was really good, people often add: "I want to go there again."*

Let's analyze the verbs in our Odesa story to see how aspect and motion work together in practice. The story begins with the imperfective verb **їздив**. This immediately tells the listener the context: a round-trip that is already finished. Then, the perfective verbs **поїхали** and **доїхали** describe the specific milestones of the transit — the departure and the successful arrival.

Під час самої поїздки ми використовуємо різні види дієслів. Слово «ходили» — це недоконаний вид, який показує загальний процес або фон. А слова «відвідали», «купили» та «з'їли» — це доконаний вид. Вони показують конкретні результати та завершені дії, які рухають сюжет нашої історії вперед. Таким чином ми можемо точно описати все, що з нами **трапилося** (happened).

> *During the trip itself, we use different aspects of verbs. The word "ходили" (walked) is imperfective, which shows a general process or background. And the words "відвідали" (visited), "купили" (bought), and "з'їли" (ate) are perfective. They show specific results and completed actions that move the plot of our story forward. Thus we can accurately describe everything that happened to us.*

<!-- INJECT_ACTIVITY: fill-in-complete-a-travel-narrative-by-choosing-the-correct-verb-form-aspect-and-motion-verb-type-for-each-blank -->

## Мовленнєве завдання: Моя подорож (~450 words)

Now it is your turn to create a story. Your task is to write a short narrative of eight to ten sentences about a real or imagined **подорож** (trip). You will need to **розповідати** (to tell) us about where you went, how you traveled, and what events occurred along the way. This is a great opportunity to practice combining motion verbs with the past tense. Remember to use different aspects to show the difference between background scenes and completed actions. Think carefully about the sequence of your actions.

Перед тим як писати, перевір свій текст. Ти використав мінімум два дієслова руху? Ти змінював вид дієслова для фону і для подій? Ти використовував слова для часу, такі як «спочатку», «потім» або «раптом»? Наприкінці важливо описати своє загальне **враження** (impression) від міста.

> *Before writing, check your text. Did you use at least two motion verbs? Did you change the verb aspect for background and for events? Did you use words for time, such as "at first", "then", or "suddenly"? At the end, it is important to describe your overall impression of the city.*

A good story goes beyond just listing facts. It sets the scene, introduces a sequence of actions, and explains what unexpected things managed to **трапитися** (to happen) to you during the trip. 

Here is a recommended flow for your text. First, start with an Introduction. Where did you go? You can say that you went to the mountains, to the sea, or to a new city. Second, describe The Journey. How did you get there? Mention buying a **квиток** (ticket) at the local **вокзал** (station) before your departure. You should also specify whether you took a bus, drove a car, or took a fast **потяг** (train). 

Third, list your Activities. Tell us where you decided to **зупинитися** (to stay) and what historical places or museums you visited. Did you manage to **доїхати** (to reach) the hotel quickly, or was the road difficult? Finally, share your Impressions. What was the best part of the trip? End your story by saying what you liked using the perfective verb **сподобатися** (to like).

:::tip
**Did you know?** — When talking about past travels, Ukrainians frequently use the imperfective verb **їздити** to emphasize that they went somewhere and have already returned. It focuses on the round trip as a single, general experience.
:::

Here is an example of a completed narrative about a weekend getaway. Notice how the verbs shift between imperfective and perfective depending on the context. Use this model answer to guide your own writing, paying close attention to how different elements work together in a coherent text.

> [!model-answer]
> Минулого літа я їздив (impf) до Львова. Це була чудова подорож. Спочатку ми купили (pf) квиток і приїхали (pf) на вокзал. Ми сіли (pf) у потяг і змогли доїхати (pf) дуже швидко. У місті ми вирішили зупинитися (pf) в маленькому готелі біля площі Ринок. Ми багато гуляли (impf) старими вулицями і слухали (impf) музику. Потім ми випили (pf) каву, коли раптом пішов (pf) сильний дощ. Ми сховалися (pf) в ресторані і з'їли (pf) смачний борщ. Увечері з нами трапилася (pf) кумедна історія, бо ми загубили (pf) карту. Але ми швидко знайшли (pf) дорогу. Мені дуже сподобалося (pf) це місто. Я хочу розповісти (pf) про нього всім друзям.

<!-- INJECT_ACTIVITY: error-correction-find-and-correct-grammar-errors-in-sentences -->
</generated_module_content>

**PIPELINE NOTE — Word count: 2848 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 420 words | Not found: 10 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрій — NOT IN VESUM
  ✗ Карпати — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Лондона — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ Одеси — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Швеції — NOT IN VESUM

All 420 other words are confirmed to exist in VESUM.

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
