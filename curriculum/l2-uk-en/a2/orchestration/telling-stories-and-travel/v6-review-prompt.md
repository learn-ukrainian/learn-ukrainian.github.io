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
## Сценарій 1: Що вчора трапилось?

**Розповідати / розповісти** (to tell/narrate) цікаві історії — це справжнє мистецтво. Коли ми говоримо про минуле, ми будуємо **розповідь** (narrative). In a Ukrainian story, we use two grammatical tools to build the scene. We use the imperfective and perfective past tenses. Think of it as the "Stage vs. Action" principle. We use the imperfective aspect to set the background scene. Це гарні декорації на вашій сцені. Ось типовий приклад: «Був теплий вечір, яскраво світило сонце, я читав цікаву книгу». The action is ongoing and continuous. Nothing has fundamentally changed yet in the story. Then, we use the perfective aspect for the main events. Ці події швидко рухають сюжет вперед. Це сама активна дія. Ось приклад: «Раптом хтось гучно постукав, і я швидко відкрив двері». The perfective verbs represent completed, punctual actions. They disrupt the calm background and drive the story forward.

Щоб історія була логічною та зрозумілою, нам потрібні слова-зв’язки. These connector words act as essential glue for your narrative. They help us clearly transition between background states and sudden plot twists. Ось кілька дуже важливих слів для розповіді: **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **у цей момент** (at that moment), **раптом** (suddenly), та **нарешті** (finally). Слово «спочатку» дає ідеальний старт вашій історії. Воно готує слухача до початку подій. Слово «потім» показує чітку хронологічну послідовність дій. Слово «раптом» — це завжди великий сюрприз. Воно миттєво показує швидку зміну ситуації. It usually signals the dramatic arrival of a perfective verb. Слово «нарешті» логічно показує кінець історії або важливий фінальний результат.

Давайте уважно подивимось на один практичний приклад. Уявіть, що ви сьогодні приїхали на **вокзал** (train station). Вокзал — це завжди дуже багато людей і постійного шуму. Ось моя маленька історія для вас. Спочатку все навколо було дуже спокійно. Люди повільно купували **квитки** (tickets), а великі **потяги** (trains) довго стояли на платформі. Я сидів у кафе і спокійно пив гарячу каву. These verbs are all imperfective, perfectly setting our busy background scene. Then, the inevitable plot twist happens. Раптом я з жахом зрозумів, що загубив свій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені своєї куртки. Verbs like the ones for realized, lost, and found are distinct perfective events. Вони показують конкретні завершені дії, які вирішують проблему.

Let's take a moment to review the grammar structure of the past tense. The Ukrainian past tense is formed using specific suffixes attached to the verb stem. They are -в, -ла, -ло, and -ли. The crucial rule here is strict gender agreement for the narrator in the singular form. Якщо розповідає чоловік, він обов'язково каже: «Я ходив, я бачив, я купив». Якщо розповідає жінка, вона має казати: «Я ходила, я бачила, я купила». For all plural subjects, we always use the -ли ending. Ми разом ходили і ми все бачили. Notice that most verbs use the **-в** sound for masculine forms. However, some verbs with consonant stems, like **міг** (could from *могти*), **ніс** (carried from *нести*), or **біг** (ran from *бігти*), do not have this suffix in the masculine form.

Як правильно запитати про цікаві події в минулому? We have two main questions depending on the specific verb aspect. Якщо ви хочете знати загальну інформацію про процес, ви питаєте: «Що відбувалося?». This specific question actively expects an imperfective answer about an ongoing, continuous situation. Але дуже часто ми хочемо знати про конкретну фінальну подію, щоб зрозуміти, що саме мало **трапитися** (to happen). Тоді ми прямо питаємо: «**Що трапилося?**» (What happened?). Ви також можете просто запитати: «Що сталося?». When you hear this direct question, you usually reply with perfective verbs to explain the result. We also frequently use specific verbs to describe our emotional reactions. Наприклад, ми дуже часто кажемо: **я злякався** (I got scared). Або, якщо це жінка: я злякалася. Ви також можете впевнено сказати: **я здивувався** (I was surprised). Усі ці емоційні слова допомагають зробити вашу історію живою та дуже цікавою.

<!-- INJECT_ACTIVITY: quiz-aspect-choice -->

## Сценарій 2: Плануємо подорож

Ось ще одна типова ситуація з нашого життя. Уявіть, що ви плануєте **подорож** (trip) з друзями на вихідні. Це завжди дуже приємний процес. Давайте послухаємо коротку розмову двох друзів.

> — **Оксана:** Привіт, Тарасе! Куди ми поїдемо на наступні вихідні? *(Hi, Taras! Where will we go next weekend?)*
> — **Тарас:** Привіт! Я думаю, що ми поїдемо в **Карпати** (the Carpathians). *(Hi! I think we will go to the Carpathians.)*
> — **Оксана:** Це чудова ідея! Коли ми виїдемо з міста? *(That's a great idea! When will we depart from the city?)*
> — **Тарас:** Ми виїдемо в п'ятницю ввечері. *(We will depart on Friday evening.)*
> — **Оксана:** Добре. Де ми будемо жити? *(Good. Where will we live?)*
> — **Тарас:** Я сьогодні **забронюю хатинку** (will book a cabin) в горах. *(I will book a cabin in the mountains today.)*
> — **Оксана:** Супер! Я впевнена, що наша подорож буде цікавою. *(Super! I am sure our trip will be interesting.)*

Зверніть увагу на слова, які використовують друзі. Вони активно планують своє майбутнє. In Ukrainian, we have two primary ways to form the future tense depending on our focus. The first method is the compound form, which we use to describe ongoing processes or habits in the future. It consists of the conjugated auxiliary verb «бути» (to be) and the infinitive of an imperfective verb. This structure is very straightforward. You simply conjugate «бути» — я буду, ти будеш, він буде, ми будемо, ви будете, вони будуть — and add the main action. Ось гарний приклад: «У Карпатах ми **будемо гуляти** (will walk)». Ми **будемо дихати** (will breathe) свіжим повітрям і **будемо багато відпочивати** (will rest a lot). These verbs show continuous, pleasant processes without a specific final result.

The second method is the simple form of the future tense. We use this specifically when we want to emphasize a completed action or a one-time result in the future. This form is built using perfective verbs. Interestingly, we conjugate these perfective verbs using the exact same endings as the present tense. For instance, when Taras talks about accommodation, he says: «Я забронюю хатинку». He focuses on the successful completion of the task. Let's look at a clear contrast. Якщо ви кажете: «Я **буду купувати** (will be buying) квитки», ви описуєте довгий процес вибору. Але якщо ви кажете: «Я **куплю** (will buy) квитки сьогодні», ви гарантуєте фінальний результат. The tickets will be purchased and ready.

When we plan a trip, verbs of motion are absolutely essential. For the actual journey to your destination, we use unidirectional perfective verbs. Ви кажете: «Я **поїду** (will go by vehicle) до міста» або «Я **полечу** (will fly) за кордон». Ці слова показують конкретний рух в одному напрямку. However, for general movement around the destination once you arrive, we use the compound future with multidirectional verbs. Наприклад: «Там я **буду їздити** (will ride around) на екскурсії». We also must pay close attention to prepositions. Ми використовуємо прийменник «до» з родовим відмінком для міст та країн: до Києва, до Львова. Але ми використовуємо прийменник «на» зі знахідним відмінком для відкритих просторів чи подій. Наприклад: на море, на фестиваль, на концерт. Щоб сказати, звідки ви приїхали, використовуйте прийменник «з» або «зі» з родовим відмінком: прилетіти з Києва, повернутися зі Львова.

Для успішної подорожі нам потрібні правильні слова. Щоб сісти в транспорт, ви повинні мати **квиток** (ticket). Please note that the authentic Ukrainian word is «квиток», which helps us avoid the common Russianism «білет». Якщо ви любите подорожувати по землі, ви обираєте **потяг** (train). Потяги їздять там, де є **залізниця** (railway). Якщо ви цінуєте свій час, ваш вибір — це **літак** (airplane). Ваш політ завжди починається там, де розташований **аеропорт** (airport). Коли ви подорожуєте Україною, вкрай важливо використовувати правильні українські назви міст. You must always say Київ, Львів, Харків, Рівне, Одеса. Using Russian versions of these names is incorrect and represents a legacy of russification. Справжня українська мова поважає власні історичні назви.

<!-- INJECT_ACTIVITY: match-up-travel-verbs -->

## Сценарій 3: Розкажи про поїздку!

Давайте послухаємо розмову двох друзів. Марко щойно повернувся з відпустки, і Олена розпитує його про подорож.
> — **Олена:** Марку, привіт! Я тебе давно не бачила. **Де ти був** (where were you) минулого тижня? *(Marko, hi! I haven't seen you in a long time. Where were you last week?)*
> — **Марко:** Привіт, Олено! Я був на півдні України. *(Hi, Olena! I was in the south of Ukraine.)*
> — **Олена:** Дуже цікаво! А **куди ти їздив** (where did you go)? *(Very interesting! And where did you go?)*
> — **Марко:** Я їздив до Одеси! Я хотів побачити Чорне море. *(I went to Odesa! I wanted to see the Black Sea.)*
> — **Олена:** Клас! Як ви змогли туди **доїхати** (to reach by vehicle)? Це ж далеко. *(Cool! How did you reach there? It's far, after all.)*
> — **Марко:** Ми поїхали нічним потягом. Вранці ми вже пили каву біля моря. *(We went by night train. In the morning we were already drinking coffee by the sea.)*
> — **Олена:** Що ви робили там щодня? *(What did you do there every day?)*
> — **Марко:** Ми багато ходили на **пляж** (beach) і просто дивилися на **море** (sea). Це був чудовий відпочинок! *(We went to the beach a lot and just looked at the sea. It was a wonderful vacation!)*

In this dialogue, Olena asks two different questions to understand the situation. First, she asks «Де ти був?» to find out Marko's general location in the past. Then, she specifically asks «Куди ти їздив?» to ask about his complete round-trip journey. The verb «їхати» is imperfective and means "to be going in one direction," but its partner «їздити» (imperfective, multidirectional) is uniquely used in the past tense to describe a fully completed round trip. Марко каже: «Я **їздив** (went and came back) до Одеси». Ми чітко розуміємо, що він уже повернувся додому. This is a very crucial distinction in Ukrainian. Ви можете сказати інакше: «Мій брат **поїхав** (left) до Києва». Це означає, що ваш брат покинув дім. Він усе ще перебуває в Києві. Або ви просто фокусуєтесь на факті його від'їзду. The perfective verb «поїхати» focuses entirely on the departure, not the return.

When we tell a story about a past trip, we must build a clear and logical narrative sequence. We use perfective verbs for the main, sequential events of the plot, and imperfective verbs for continuous background processes. Ось гарний приклад правильної розповіді: «**Спочатку** (at first) ми **приїхали** (arrived) до нового міста. **Потім** (then) ми вирішили швидко **зупинитися** (to stay, to stop) в затишному готелі. Вдень ми дуже багато **ходили** (walked) по місту, а ввечері ми **відвідали** (visited) оперу». Pay close attention to the verb choices here. «Ходити по місту» is a long process — you walk around and explore without a specific, immediate final destination. Therefore, we use the multidirectional imperfective verb. However, «відвідати оперу» is a specific, completed event with a clear result in the past, so we use a perfective verb. Alternating these aspects makes your story dynamic and natural.

Після детальної розповіді про події ми часто хочемо поділитися своїми позитивними емоціями. Якщо подорож змогла вам **сподобатися** (to like), як правильно сказати про це українською? Найпопулярніша та найприродніша фраза — це «Мені сподобалося» (I liked it). You use this specific construction with the dative case pronoun («мені») and the past tense verb. Якщо ви додаєте інфінітив, дієслово завжди має середній рід: «Мені сподобалося гуляти по місту». Якщо ви додаєте іменник, дієслово узгоджується з його родом: «Мені сподобалося місто» (neuter), «Мені сподобався музей» (masculine), або «Мені сподобалася вулиця» (feminine). Також Марко може емоційно сказати: «Я **отримав багато вражень**» (I got many impressions). Використовуйте такі короткі слова для загальної атмосфери: **було чудово** (it was wonderful), **було дуже весело** (it was very fun), або **було цікаво** (it was incredibly interesting).

Завжди важливо свідомо обирати питомо українські слова для ваших мандрівок. Ніколи не використовуйте російське слово «путешествіє». Правильне і красиве українське слово — це **подорож** (journey). Ви довго подорожуєте потягом і прибуваєте на великий вокзал. Слово «вокзал» є в багатьох мовах, але українська мова має своє унікальне історичне слово — **двірець** (station). Це слово особливо популярне в західних регіонах України. Наприклад, у Львові ви приїдете саме на Головний двірець. Також обов'язково пам'ятайте різницю між місцями зупинок транспорту. Для міських автобусів або трамваїв ми завжди використовуємо слово **зупинка** (bus stop). Але для потягів та метро ми кажемо **станція** (train station). Використовуйте ці правильні слова, і ваша українська мова звучатиме природно.

<!-- INJECT_ACTIVITY: fill-in-travel-narrative -->

## Мовленнєве завдання: Моя подорож

Ваше головне завдання — написати коротку розповідь про свою недавню подорож. Write a cohesive text consisting of 8 to 10 sentences about a trip you recently took. Це може бути реальна історія або ваша фантазія. Your narrative must clearly demonstrate your ability to sequence past events and describe travel. Обов'язково використайте принаймні три **слова-зв'язки** (time connectors) для логіки тексту. For example, you can use «спочатку», «потім», або «нарешті». Також вам потрібно використати мінімум два **дієслова руху** (verbs of motion) у минулому часі. Most importantly, your story must show a clear contrast between background actions using the imperfective aspect and main events using the perfective aspect. Розкажіть детально, куди саме ви їздили та як ви туди дісталися. Напишіть, що ви там робили та які позитивні враження отримали.

Коли ви закінчите писати текст, уважно перевірте його за допомогою цього списку. This checklist will help you identify and fix common mistakes before you finalize your story. Перше: чи правильно ви узгодили дієслова минулого часу зі своїм родом? If you are female, did you remember to use the «-ла» endings for all your past tense verbs? Друге: чи правильно ви використали прийменники напрямку? Did you use the preposition «до» plus the genitive case when naming destination cities? Третє: чи логічно розвивається ваша історія? Did you successfully use words like «потім» (then) or «після цього» (after that) to show the chronological sequence of your actions? Четверте: чи описали ви свої фінальні емоції від поїздки?

Ось приклад гарної розповіді, яку ви можете використати як орієнтир для вашого власного тексту. Here is a model answer annotated with grammatical explanations for the key verbs and structures. Read it carefully to see how the background states contrast with the sudden actions.

> [!model-answer]
> **Минулого літа** (Last summer) я **їздив** [Imperfective, completed round-trip] до Карпат зі своїми друзями. **Спочатку** (At first) ми дуже довго **їхали** [Imperfective, process of traveling] потягом до міста Яремче. **Потім** (Then) ми швидко **знайшли** [Perfective, completed event] наш маленький готель. Там ми **залишили** [Perfective, completed event] усі свої важкі речі. Наступного дня ми **пішли** [Perfective, one-time departure on foot] високо в гори. Погода була просто чудова, і сонце яскраво **світило** [Imperfective, background state]. Ми повільно **йшли** [Imperfective, continuous process] темним лісом. Раптом ми **побачили** [Perfective, sudden event] великого оленя біля дерева. Це було справді неймовірно! Увечері ми **повернулися** [Perfective, completed result] до нашого готелю дуже втомлені, але абсолютно щасливі. Мені дуже **сподобалася** [Perfective, final impression] ця коротка, але надзвичайно цікава подорож. Я обов'язково хочу поїхати туди ще раз наступного року.

Перед тим як почати свою розповідь, давайте ще раз згадаємо найчастіші помилки. Before you write, let's review the most typical pitfalls English speakers face with travel narratives. Найперша проблема стосується роду в минулому часі. If a woman says "I went to the cinema," she must say «я ходила в кіно», never «я ходив». Українські дієслова завжди показують рід того, хто говорить. The second major pitfall relates to transportation methods. When you say "I will fly by airplane," you must use the instrumental case directly. Правильно казати «летіти літаком» або «їхати потягом». You must never use the preposition «з» (with) for vehicles, so «летіти з літаком» is completely wrong. Завжди пам'ятайте про ці важливі граматичні правила.

<!-- INJECT_ACTIVITY: error-correction-travel -->

## Підсумок

У цьому модулі ми навчилися розповідати цікаві історії та планувати **подорожі** (trips). Тепер ви знаєте, як правильно будувати **розповідь** (narrative).

Ми використовуємо **недоконаний вид** (imperfective aspect) для опису фону або процесу. Наприклад: «Сонце яскраво світило». Ми використовуємо **доконаний вид** (perfective aspect) для швидких подій або результату. Наприклад: «Раптом ми побачили оленя».

Також ми вивчили важливі **слова-зв'язки** (time connectors). Вони роблять історію логічною. Це слова **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **раптом** (suddenly), **нарешті** (finally).

Ви навчилися правильно використовувати дієслова руху. Слово **поїхав** (left/departed) означає рух в один бік. Слово **їздив** (went and returned) означає завершену поїздку. Ми кажемо **буду їздити** (will travel regularly) для звички. Слово **поїду** (will go) означає один конкретний план.

Пам'ятайте про правильні прийменники. Ми використовуємо **до** (to) плюс **родовий відмінок** (Genitive case) для напрямку. Наприклад: «до Києва». Ми використовуємо **з** (from) або **зі** плюс родовий відмінок для старту. Наприклад: «зі Львова». Ми кажемо **на** (to/on) плюс **знахідний відмінок** (Accusative case) для подій або поверхонь. Наприклад: «на море».

Ви вивчили нові слова: **квиток** (ticket), **потяг** (train), **вокзал** (station) та **враження** (impression). Тепер ви готові подорожувати!
</generated_module_content>

**PIPELINE NOTE — Word count: 2794 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 667 words | Not found: 18 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Карпат — NOT IN VESUM
  ✗ Карпатах — NOT IN VESUM
  ✗ Карпати — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Одеси — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ Харків — NOT IN VESUM
  ✗ Яремче — NOT IN VESUM
  ✗ путешествіє — NOT IN VESUM
  ✗ язки — NOT IN VESUM

All 667 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
