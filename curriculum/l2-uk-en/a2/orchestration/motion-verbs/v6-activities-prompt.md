<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/motion-verbs.yaml` file for module **43: Іду, їду, лечу** (a2).

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

- focus: Sort motion verb forms into unidirectional vs. multidirectional categories
  items: 8
  type: group-sort
- focus: Complete sentences with the correct motion verb form based on whether the
    action is one-way/now or habitual/round-trip
  items: 8
  type: fill-in
- focus: Conjugate казати, пити, and боротися — choose the correct form for the given
    person and number
  items: 8
  type: quiz
- focus: Match motion verbs with the correct preposition and case for direction (до
    + Gen., на + Acc., з + Gen.)
  items: 8
  type: match-up
- focus: Reorder words to form correct directional sentences with motion verbs and
    prepositions (іду до школи, їду на роботу)
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- чергування (alternation)
- односпрямований (unidirectional)
- різноспрямований (multidirectional)
- звідки (from where)
required:
- іти / ходити (to go on foot — unidirectional/multidirectional)
- їхати / їздити (to go by vehicle — unidirectional/multidirectional)
- летіти / літати (to fly — unidirectional/multidirectional)
- піти (to leave on foot — pf.)
- поїхати (to leave by vehicle — pf.)
- казати / кажу (to say — stem change model)
- пити / п'ю (to drink — irregular model)
- боротися / борюся (to fight/struggle — reflexive model)
- напрямок (direction)
- рух (movement, motion)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Три пари дієслів руху

В українській мові ми використовуємо різні дієслова руху. English has one verb, "to go", for many different situations. You can go to the store right now, go to the store every day, go by car, or go on foot. В українській мові це абсолютно різні слова. Ukrainian distinguishes motion verbs based on two things: how you travel (on foot, by vehicle, by air) and the specific nature of the trip. The most important difference is between unidirectional (one-way) and multidirectional (habitual or round-trip) movement. Це не залежить від швидкості або відстані. *(This does not depend on speed or distance.)* **Односпрямований рух** *(unidirectional motion)* means you are going in one direction right now, or you have a specific, one-way plan. **Багатоспрямований рух** *(multidirectional motion)* means you go there regularly, you travel back and forth, or you just move around aimlessly. We have three main pairs of verbs to express these ideas.

Перша пара — це рух пішки. The first pair is for movement on foot: **іти / ходити** *(to go on foot — unidirectional/multidirectional)*. Дієслово «іти» означає, що ви йдете кудись саме зараз. The verb "іти" shows that you are walking somewhere right now, in one specific direction.
> — **Оксана:** Куди ти йдеш? *(Where are you going?)*
> — **Марко:** Я йду до парку. *(I am walking to the park.)*

Дієслово «ходити» означає регулярну дію або рух туди й назад. The verb "ходити" is for regular habits, repeated actions, or completed round trips.
> — **Оксана:** Ти часто ходиш у цей парк? *(Do you often go to this park?)*
> — **Марко:** Так, я ходжу сюди щодня. *(Yes, I go here every day.)*

In the past tense, a completed trip (going to a place and coming back) is also a round trip, so we use the multidirectional verb "ходити". Вчора я ходив у кіно. *(Yesterday I went to the cinema.)* I went there, watched the movie, and came back. Це закритий цикл. *(This is a closed loop.)*

Друга пара — це рух транспортом. The second pair is for movement by vehicle: **їхати / їздити** *(to go by vehicle — unidirectional/multidirectional)*. Якщо ви використовуєте автобус, поїзд, машину або велосипед, вам потрібні ці дієслова. If you use a bus, train, car, or bicycle, you must use these verbs. You cannot use "іти" or "ходити" if you are in a vehicle.
Дієслово «їхати» описує рух зараз. "Їхати" is one-way motion right now or a planned one-way trip.
> — **Мама:** Ви вже їдете додому? *(Are you driving home already?)*
> — **Син:** Так, ми їдемо. *(Yes, we are driving.)*

Дієслово «їздити» — це регулярні поїздки. "Їздити" describes habitual or regular trips by transport, or going back and forth multiple times.
> — **Анна:** Ви їздите на море щоліта? *(Do you go to the sea every summer?)*
> — **Ігор:** Ні, ми їздимо туди рідко. *(No, we go there rarely.)*

Третя пара — це рух у повітрі. The third pair is for movement through the air: **летіти / літати** *(to fly — unidirectional/multidirectional)*. Дієслово «летіти» описує політ зараз або конкретний запланований рейс. The verb "летіти" describes a flight happening right now, or one specific scheduled flight to a destination.
> — **Тарас:** Де зараз твій брат? *(Where is your brother right now?)*
> — **Олена:** Він летить до Києва. *(He is flying to Kyiv.)*

Дієслово «літати» означає регулярні польоти або загальну здатність істоти літати. The verb "літати" means regular flights, round-trip flights over time, or the general ability to fly.
> — **Тарас:** Твій брат часто літає? *(Does your brother fly often?)*
> — **Олена:** Так, він часто літає у справах. *(Yes, he often flies for business.)*

Птахи літають високо в небі. *(Birds fly high in the sky.)* Це їхня природна здатність. *(This is their natural ability.)* They are not just flying to one destination right now; they fly in general.

<!-- EXERCISE -->


## Дієвідміна та доконаний вид

Тепер ми маємо навчитися правильно змінювати ці дієслова. Now we must learn to conjugate these motion verbs correctly in the present tense. Дієслово **іти** *(to go, walk)* належить до першої дієвідміни. The verb "іти" belongs to the first conjugation. Ось його форми: я **іду**, ти **ідеш**, він **іде**, ми **ідемо**, ви **ідете**, вони **ідуть**. Дієслово **ходити** *(to walk regularly)* належить до другої дієвідміни. The verb "ходити" belongs to the second conjugation, taking endings like -иш, -ить, -ять. Тут є важливе граматичне правило. There is an important consonant alternation here. Коли ми кажемо про себе, звук «д» змінюється на «дж». When forming the "я" (I) form, the stem consonant changes from "д" to "дж". Тому ми кажемо: я **ходжу** *(I walk)*. Але ця зміна працює тільки для форми «я». But this change only applies to the "я" form. Для інших осіб ми використовуємо звичайну літеру «д». For all other persons, we use the regular letter "д". Отже, повна парадигма: я **ходжу**, ти **ходиш**, вона **ходить**, ми **ходимо**, ви **ходите**, вони **ходять**.
> — **Марко:** Куди ти ходиш на вихідних? *(Where do you go on weekends?)*
> — **Олена:** Я ходжу в басейн. *(I go to the pool.)*

Дієслово **їхати** *(to ride, drive)* також належить до першої дієвідміни. The verb "їхати" also belongs to the first conjugation. Воно змінюється так само, як і дієслово «іти». It conjugates just like the verb "іти". Форми такі: я **їду**, ти **їдеш**, воно **їде**, ми **їдемо**, ви **їдете**, вони **їдуть**. Дієслово **їздити** *(to ride regularly)* належить до другої дієвідміни. The verb "їздити" belongs to the second conjugation. Тут ми також маємо складне чергування приголосних у формі «я». Here we also have a complex consonant alternation in the "я" form. Звуки «зд» змінюються на «ждж». The consonant cluster "зд" changes to "ждж". Це дуже специфічний український звук. This is a very specific Ukrainian sound cluster. Ми кажемо: я **їжджу** *(I ride)*. Знову, ця зміна відбувається тільки у першій особі однини. Again, this change only happens in the first person singular form. Повна парадигма виглядає так: я **їжджу**, ти **їздиш**, він **їздить**, ми **їздимо**, ви **їздите**, вони **їздять**.
> — **Ігор:** Чим ви їздите на роботу? *(How do you commute to work?)*
> — **Оксана:** Зазвичай я їжджу трамваєм. *(Usually I take the tram.)*

Третя пара — це дієслова **летіти** *(to fly)* та **літати** *(to fly regularly)*. The third pair is the verbs "летіти" and "літати". Дієслово «летіти» належить до другої дієвідміни. The verb "летіти" belongs to the second conjugation. У формі «я» також є чергування: звук «т» змінюється на «ч». In the "я" form, there is also an alternation: the sound "т" changes to "ч". Ми кажемо: я **лечу** *(I fly)*. Для інших осіб ми повертаємо звук «т» і додаємо стандартні закінчення. For other persons, we return the "т" sound and add the standard endings. Парадигма така: я **лечу**, ти **летиш**, вона **летить**, ми **летимо**, ви **летите**, вони **летять**. Дієслово «літати» є набагато простішим. The verb "літати" is much simpler. Воно належить до першої дієвідміни і не має жодних чергувань. It belongs to the first conjugation and has no consonant alternations. Ми просто додаємо закінчення -ю, -єш до основи. We simply add the endings -ю, -єш to the stem. Парадигма: я **літаю**, ти **літаєш**, він **літає**, ми **літаємо**, ви **літаєте**, вони **літають**.
> — **Анна:** Ти боїшся літати? *(Are you afraid to fly?)*
> — **Павло:** Ні, я часто літаю. *(No, I fly often.)*

Тепер поговоримо про доконаний вид цих дієслів. Now let's talk about the perfective aspect of these verbs. Усі ці дієслова руху є недоконаними. All these motion verbs are imperfective. Вони описують тривалий процес або регулярну звичку. They describe an ongoing process or a regular habit. Щоб показати початок нової подорожі, ми додаємо префікс **по-**. To show the start of a new journey, we add the prefix "по-". Ми додаємо цей префікс до односпрямованих дієслів. We add this prefix to the unidirectional verbs. Так ми отримуємо: **піти** *(to leave on foot)*, **поїхати** *(to leave by vehicle)*, **полетіти** *(to fly off)*. These perfective verbs mean "to set off" or "to leave". Дієслово «піти» має неправильні форми минулого часу. The verb "піти" has irregular past tense forms. Ми кажемо: він **пішов** *(he left)*, вона **пішла** *(she left)*, воно **пішло** *(it left)*, вони **пішли** *(they left)*.
> — **Батько:** Де зараз Тарас? *(Where is Taras right now?)*
> — **Син:** Він уже пішов геть. *(He has already left.)*
Для інших дієслів минулий час є стандартним. For the other verbs, the past tense is standard. Вона поїхала додому. *(She left for home.)* Літак полетів учора. *(The plane took off yesterday.)*

<!-- EXERCISE -->


## Моделі дієвідмінювання: казати, пити, боротися

В українській мові є особливі правила для багатьох дієслів. *(In Ukrainian, there are special rules for many verbs.)* Деякі дієслова змінюють приголосні звуки в корені. *(Some verbs change consonant sounds in the root.)* Ми називаємо це явище **чергуванням** *(alternation)*.

These changes are not random grammatical irregularities. They are predictable and highly systematic consonant alternations. We often see historical shifts like «з» to «ж», «с» to «ш», or «т» to «ч». These shifts naturally make pronunciation much smoother. They also help distinguish different verb forms more clearly in speech. Once you learn a specific phonetic pattern, you can easily apply it to dozens of similar verbs without memorizing each one individually. Let's look at three very common conjugation models that you will use every day.

Перша модель — це постійна зміна приголосного звука. *(The first model is a constant consonant sound change.)* Ця зміна відбувається в усьому теперішньому часі. *(This change happens throughout the entire present tense.)* Візьмемо популярне дієслово **казати / кажу** *(to say — stem change model)*. У цьому слові звук «з» завжди змінюється на шиплячий «ж». *(In this word, the sound "з" always changes to the hissing "ж".)*

This alternation belongs to the standard first conjugation pattern. The new consonant stays securely in place for every person.

Я **кажу** *(I say)*. Ти **кажеш** *(you say)*. Він **каже** *(he says)*. Ми **кажемо** *(we say)*. Ви **кажете** *(you say)*. Вони **кажуть** *(they say)*.

Many common verbs follow this exact same pattern. For example, the verb **писати** *(to write)* changes «с» to «ш» across all active forms.

Я **пишу** *(I write)*. Ти **пишеш** *(you write)*. Вони **пишуть** *(they write)*.

This structural rule also applies directly to perfective verbs in the simple future tense. The perfective partner **сказати** *(to say — pf.)* conjugates exactly the same way to show completed future actions.

Завтра я **скажу** всю правду. *(Tomorrow I will tell the whole truth.)*
> — **Марія:** Що ти зараз кажеш? *(What are you saying right now?)*
> — **Іван:** Я кажу, що я пишу нову статтю. *(I am saying that I am writing a new article.)*

Друга важлива модель — це коротка основа з апострофом. *(The second important model is a short stem with an apostrophe.)* Дієслово **пити / п'ю** *(to drink — irregular model)* має дуже коротку форму в теперішньому часі. *(The verb "пити" has a very short form in the present tense.)* Ми часто використовуємо його щодня. *(We often use it every day.)*

The verbal stem drastically reduces here. Because of this reduction, we must use an apostrophe before adding the standard endings «-ю», «-єш», or «-є». The apostrophe visually and phonetically shows that the consonant and the vowel are pronounced entirely separately.

Я **п'ю** *(I drink)*. Ти **п'єш** *(you drink)*. Вона **п'є** *(she drinks)*. Ми **п'ємо** *(we drink)*. Ви **п'єте** *(you drink)*. Вони **п'ють** *(they drink)*.

Several other short verbs share this specific contraction pattern perfectly. For instance, the verb **бити** *(to hit/beat)* conjugates simply as я **б'ю** *(I hit)*, ти **б'єш** *(you hit)*.

Інше схоже дієслово — це **лити** *(to pour)*. *(Another similar verb is "лити".)* Але тут ми маємо подвійний м'який звук «л». *(But here we have a double soft "л" sound.)*

Я **ллю** *(I pour)*. Ти **ллєш** *(you pour)*. Вони **ллють** *(they pour)*.
> — **Олег:** Що ти п'єш зранку? *(What do you drink in the morning?)*
> — **Анна:** Зазвичай я п'ю чорну каву. *(Usually I drink black coffee.)*

Третя цікава модель — це дієслова на **-отися** *(verbs ending in -отися)*. Дієслово **боротися / борюся** *(to fight/struggle)* має дві головні особливості під час відмінювання. *(The verb "боротися" has two main features during conjugation.)*

First, the structural stem changes from «от» to «ор» in all present tense forms. Second, we must keep the reflexive particle securely attached to the very end of the conjugated word. We use **-ся** after consonants and **-сь** after vowels.

Я **борюся** *(I struggle)*. Ти **борешся** *(you struggle)*. Він **бореться** *(he struggles)*. Ми **боремося** *(we struggle)*. Ви **боретеся** *(you struggle)*. Вони **борються** *(they struggle)*.

Pay extremely close attention to the third person forms ending in «-ться». This cluster is always pronounced together as a soft, prolonged "ts:a" sound, not exactly as it is written.

Ми щодня боремося за нашу свободу. *(We fight for our freedom every day.)* Вони мужньо борються зі складними проблемами. *(They bravely struggle with complex problems.)*
> — **Журналіст:** За що зараз бореться ваша організація? *(What is your organization fighting for now?)*
> — **Активіст:** Ми боремося за рівні права людей. *(We are fighting for equal human rights.)*

<!-- EXERCISE -->


## Рух + прийменники + відмінки

Коли ми рухаємося, ми маємо мету. *(When we move, we have a destination.)* Ми часто запитуємо: «Куди ти йдеш?» або «Куди ви їдете?». *(We often ask: "Where are you going?" or "Where are you driving to?".)* Ukrainian uses three main prepositions to answer this question. First, we use **до** *(to)* with the Genitive case. Я йду **до школи** *(to school)*. Ми їдемо **до друга** *(to a friend)*. Second, we use **на** *(to/onto)* with the Accusative case for events, open spaces, or specific activities. Він іде **на роботу** *(to work)*. Вони йдуть **на пошту** *(to the post office)*. Third, we use **в** або **у** *(to/into)* with the Accusative case for enclosed spaces, cities, and countries. Вона летить **в Україну** *(to Ukraine)*. Ми їдемо **у місто** *(to the city)*. There is a strict rule regarding the name of our country. Ми завжди говоримо «в Україну» або «в Україні». *(We always say "в Україну" or "в Україні".)* Ніколи не кажіть «на Україну» чи «на Україні». *(Never say "на Україну" or "на Україні".)* This is a fundamental grammatical and political rule of the modern language.

Тепер поговоримо про зворотний напрямок. *(Now let's talk about the opposite direction.)* Ми запитуємо: «Звідки ти йдеш?» або «Звідки летить літак?». *(We ask: "Where are you walking from?" or "Where is the plane flying from?".)* Ukrainian perfectly pairs the destination prepositions with specific return prepositions. Усі ці прийменники вимагають родового відмінка. *(All these prepositions require the Genitive case.)* If you went «до» a person or place, you return **від** *(from)* them. Я йду **від друга** *(from a friend)*. Вона їде **від лікаря** *(from the doctor)*. If you went «на» an event or open space, you return **з** or **зі** *(from/off)* it. Ми йдемо **з роботи** *(from work)*. Діти йдуть **зі школи** *(from school)*. If you went «в» or «у» into a country or enclosed space, you also return **з** *(from/out of)* it. Брат їде **з міста** *(from the city)*. Літак летить **з України** *(from Ukraine)*.

Іноді ми не маємо кінцевої мети. *(Sometimes we do not have a final destination.)* Ми просто рухаємося через певний простір. *(We simply move through a certain space.)* To say that you are crossing something, use **через** *(through/across)* with the Accusative case. Ми йдемо **через парк** *(through the park)*. Вони переходять **через дорогу** *(across the road)*. To describe movement along a surface or wandering inside an area, use **по** *(along/around)* with the Locative case. Ми гуляємо **по місту** *(around the city)*. Вона йде **по вулиці** *(along the street)*. Notice the important difference between a specific destination and wandering. Sentence «Я йду в парк» means the park is your destination. Sentence «Я ходжу по парку» means you are already inside and wandering around.

Уявіть типову ситуацію в аеропорту. *(Imagine a typical situation at the airport.)* Там дуже багато людей. *(There are very many people there.)* Усі кудись поспішають. *(Everyone is hurrying somewhere.)*
> — **Олег:** Алло, Маріє! Де ви зараз? *(Hello, Maria! Where are you now?)*
> — **Марія:** Ми вже в аеропорту. Ми йдемо до термінала. *(We are already at the airport. We are walking to the terminal.)*
> — **Олег:** Куди ви летите? *(Where are you flying to?)*
> — **Марія:** Ми летимо до Києва. А де Іван? *(We are flying to Kyiv. And where is Ivan?)*
> — **Олег:** Він щойно прилетів з Польщі. *(He just flew in from Poland.)*
> — **Марія:** А він куди їде? *(And where is he driving to?)*
> — **Олег:** Він їде на таксі в готель. *(He is taking a taxi to the hotel.)*
> — **Марія:** Зрозуміло. Наш літак летить через годину. *(Understood. Our plane flies in an hour.)*
> — **Олег:** Добре, щасливої дороги! Поїхали! *(Good, have a safe trip! Let's go!)*

<!-- EXERCISE -->
<!-- EXERCISE -->


## Підсумок

Ось і все на сьогодні. *(That is all for today.)* Ви зробили велику роботу. *(You did a great job.)* Дієслова руху — це складна, але важлива тема. *(Verbs of motion are a complex but important topic.)* Тепер ви знаєте різницю між рухом пішки та транспортом. *(Now you know the difference between movement on foot and by transport.)* Щоб перевірити свої знання, дайте відповіді на ці запитання. *(To check your knowledge, answer these questions.)*

1. Яка різниця між формами **«я йду»** *(I am walking)* та **«я ходжу»** *(I walk)*? Яке дієслово показує рух зараз, а яке — регулярну звичку? *(Which verb shows movement now, and which — a regular habit?)*
2. Як правильно сказати: «Я їду на автобусі» чи «Я іду на автобусі»? Чому транспорт вимагає іншого дієслова? *(Why does transport require a different verb?)*
3. Яке закінчення має дієслово **їздити** *(to ride)* у формі **я** *(I)*? Згадайте про складне чергування приголосних. *(Remember about the complex consonant alternation.)*
4. Як утворити минулий час чоловічого роду від дієслова **піти** *(to leave on foot)*?
5. Які прийменники ми використовуємо для запитань **«Куди?»** *(Where to?)* та **«Звідки?»** *(Where from?)*? Який відмінок потрібен після прийменників **до** *(to)*, **з** *(from)* та **від** *(from)*? *(Which case is needed after the prepositions to, from, and from?)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: motion-verbs
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

**Level: A2 (Module 43/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
