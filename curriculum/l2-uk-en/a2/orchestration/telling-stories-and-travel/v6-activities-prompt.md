<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/telling-stories-and-travel.yaml` file for module **45: Розповіді та подорожі** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`
- `<!-- INJECT_ACTIVITY: match-up-travel-verbs -->`
- `<!-- INJECT_ACTIVITY: fill-in-travel-narrative -->`
- `<!-- INJECT_ACTIVITY: error-correction-travel -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete a travel narrative by choosing the correct verb form (aspect and
    motion verb type) for each blank
  items: 8
  type: fill-in
- focus: Read a past trip description and answer comprehension questions about what
    happened, in what order, and how the person traveled
  items: 8
  type: quiz
- focus: Match travel situations with the correct motion verb and preposition combination
    (їхати до + Gen., летіти на + Acc.)
  items: 8
  type: match-up
- focus: Find and correct grammar errors in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спочатку (at first)
- потім (then)
- нарешті (finally)
- тим часом (meanwhile)
- сувенір (souvenir)
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


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Сценарій 1: Що вчора трапилось?

**Розповідати / розповісти** (to tell/narrate) цікаві історії — це справжнє мистецтво. Коли ми говоримо про минуле, ми будуємо **розповідь** (narrative). In a Ukrainian story, we use two grammatical tools to build the scene. We use the imperfective and perfective past tenses. Think of it as the "Stage vs. Action" principle. We use the imperfective aspect to set the background scene. Це гарні декорації на вашій сцені. Ось типовий приклад: «Був теплий вечір, яскраво світило сонце, я читав цікаву книгу». The action is ongoing and continuous. Nothing has fundamentally changed yet in the story. Then, we use the perfective aspect for the main events. Ці події швидко рухають сюжет вперед. Це найактивніша дія. Ось приклад: «Раптом хтось гучно постукав, і я швидко відкрив двері». The perfective verbs represent completed, punctual actions. They disrupt the calm background and drive the story forward.

Щоб історія була логічною та зрозумілою, нам потрібні слова-зв’язки. These connector words act as essential glue for your narrative. They help us clearly transition between background states and sudden plot twists. Ось кілька дуже важливих слів для розповіді: **спочатку** (at first), **потім** (then), **після цього** (after that), **тим часом** (meanwhile), **у цей момент** (at that moment), **раптом** (suddenly), та **нарешті** (finally). Слово «спочатку» є ідеальним початком вашої історії. Воно готує слухача до початку подій. Слово «потім» показує чітку хронологічну послідовність дій. Слово «раптом» — це завжди великий сюрприз. Воно миттєво показує швидку зміну ситуації. It usually signals the dramatic arrival of a perfective verb. Слово «нарешті» логічно показує кінець історії або важливий фінальний результат.

Давайте уважно подивимось на один практичний приклад. Уявіть, що ви сьогодні приїхали на **вокзал** (train station). Вокзал — це завжди дуже багато людей і постійного шуму. Ось моя маленька історія для вас. Спочатку все навколо було дуже спокійно. Люди повільно купували **квитки** (tickets), а великі **потяги** (trains) довго стояли на платформі. Я сидів у кафе і спокійно пив гарячу каву. These verbs are all imperfective, perfectly setting our busy background scene. Then, the inevitable plot twist happens. Раптом я з жахом зрозумів, що загубив свій квиток! Я швидко почав шукати його скрізь. Нарешті я знайшов його в кишені своєї куртки. Verbs like the ones for realized, lost, and found are distinct perfective events. Вони показують конкретні завершені дії, які вирішують проблему.

Let's take a moment to review the grammar structure of the past tense. The Ukrainian past tense is formed using specific suffixes attached to the verb stem. They are -в, -ла, -ло, and -ли. The crucial rule here is strict gender agreement for the narrator in the singular form. Якщо розповідає чоловік, він обов'язково каже: «Я ходив, я бачив, я купив». Якщо розповідає жінка, вона має казати: «Я ходила, я бачила, я купила». For all plural subjects, we always use the -ли ending. Ми разом ходили і ми все бачили. Notice that most verbs use the **-в** sound for masculine forms. However, some verbs with consonant stems, like **міг** (could from *могти*), **ніс** (carried from *нести*), or **біг** (ran from *бігти*), do not have this suffix in the masculine form.

Як правильно запитати про цікаві події в минулому? We have two main questions depending on the specific verb aspect. Якщо ви хочете знати загальну інформацію про процес, ви питаєте: «Що відбувалося?». This specific question actively expects an imperfective answer about an ongoing, continuous situation. Але дуже часто ми хочемо знати про конкретну фінальну подію, щоб зрозуміти, що саме мало **трапитися** (to happen). Тоді ми прямо питаємо: «**Що трапилося?**» (What happened?). Ви також можете просто запитати: «Що сталося?». When you hear this direct question, you usually reply with perfective verbs to explain the result. We also frequently use specific verbs to describe our emotional reactions. Наприклад, ми дуже часто кажемо: **я злякався** (I got scared). Або, якщо це жінка: я злякалася. Ви також можете впевнено сказати: **я здивувався** (I was surprised). Усі ці емоційні слова допомагають зробити вашу історію живою та дуже цікавою.

<!-- INJECT_ACTIVITY: quiz-aspect-choice -->

## Сценарій 2: Плануємо подорож

Ось ще одна типова ситуація з нашого життя. Уявіть, що ви плануєте **подорож** (trip) з друзями на вихідні. Це завжди дуже приємний процес. Давайте послухаємо коротку розмову двох друзів.

> — **Оксана:** Привіт, Тарасе! Куди ми поїдемо на наступні вихідні? *(Hi, Taras! Where will we go next weekend?)*
> — **Тарас:** Привіт! Я думаю, що ми поїдемо в **Карпати** (the Carpathians). *(Hi! I think we will go to the Carpathians.)*
> — **Оксана:** Це чудова ідея! Коли ми виїдемо з міста і як доберемося? Поїдемо потягом чи полетимо? *(That's a great idea! When will we depart from the city and how will we get there? Will we go by train or fly?)*
> — **Тарас:** Ми виїдемо в п'ятницю ввечері і поїдемо нічним потягом. *(We will depart on Friday evening and go by night train.)*
> — **Оксана:** Добре. Де ми будемо жити? *(Good. Where will we live?)*
> — **Тарас:** Я сьогодні **забронюю хатинку** (will book a cabin) в горах. *(I will book a cabin in the mountains today.)*
> — **Оксана:** Супер! А що ми будемо там робити? *(Super! And what will we do there?)*
> — **Тарас:** Ми будемо гуляти лісом і насолоджуватися природою. *(We will walk in the forest and enjoy nature.)*
> — **Оксана:** Я впевнена, що наша подорож буде цікавою. *(I am sure our trip will be interesting.)*

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
> — **Олена:** А що тобі найбільше сподобалося? *(And what did you like the most?)*
> — **Марко:** Найбільше мені сподобалася місцева природа. *(I liked the local nature the most.)*

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

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: telling-stories-and-travel
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

**Level: A2 (Module 45/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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

### Pattern: grammar-verb-aspect [A2 §4.2.3.1, B1 §4.2.3.1]
**Вид дієслова** (Verb aspect)
- **group-sort** — Доконаний чи недоконаний?: Розподілити дієслова за видом — розпізнати видові пари / Sort verbs by aspect — recognize aspect pairs
  - Instruction: *Розподіліть дієслова за видами*
- **match-up** — Утвори видові пари: Зіставити недоконане з доконаним дієсловом / Match imperfective ↔ perfective aspect pairs
  - Instruction: *З'єднайте видові пари*
- **fill-in** — Який вид доречний?: Обрати правильний вид для контексту (тривалість vs завершеність) / Choose correct aspect for context (duration vs completion)
  - Instruction: *Оберіть правильну форму*
- **quiz** — Визнач вид дієслова: Визначити вид поданого дієслова / Identify aspect of a given verb
**Anti-patterns (DO NOT generate):**
- ❌ translate: Англійський минулий час НЕ відповідає 1:1 українському виду. «I read» = і «читав», і «прочитав»
- ❌ quiz-only: Вид — це вибір мовця. Учні мають практикувати вибір виду в контексті, а не тільки розпізнавати

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
