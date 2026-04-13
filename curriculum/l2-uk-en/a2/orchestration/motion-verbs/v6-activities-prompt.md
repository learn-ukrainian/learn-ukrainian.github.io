<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/motion-verbs.yaml` file for module **43: Іду, їду, лечу** (a2).

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

- `<!-- INJECT_ACTIVITY: group-sort-sort-motion-verb-forms-into-unidirectional-vs-multidirectional-categories -->`
- `<!-- INJECT_ACTIVITY: fill-in-motion-context -->`
- `<!-- INJECT_ACTIVITY: quiz-conjugate-and-choose-the-correct-form-for-the-given-person-and-number -->`
- `<!-- INJECT_ACTIVITY: match-up-prepositions-cases -->`
- `<!-- INJECT_ACTIVITY: unjumble-directional-sentences -->`

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
## Три пари дієслів руху (~550 words)

> — **Друг:** Привіт! Де ти зараз? Я тебе не бачу. *(Hi! Where are you now? I don't see you.)*
> — **Пасажир:** Я вже в аеропорту. Тут хаос! Я швидко іду до виходу номер п'ять. *(I'm already at the airport. It's chaos here! I am walking quickly to gate number five.)*
> — **Друг:** А де твій брат? Він теж тут? *(And where is your brother? Is he here too?)*
> — **Пасажир:** Ні, він зараз їде в місто на таксі. У нього інший рейс. *(No, he is currently riding to the city by taxi. He has a different flight.)*
> — **Друг:** Зрозуміло. А куди летить твій літак? *(Understood. And where is your plane flying to?)*
> — **Пасажир:** Мій літак летить до Парижа. *(My plane is flying to Paris.)*
> — **Друг:** Класно! А батьки вже вдома? *(Cool! And are the parents already at home?)*
> — **Пасажир:** Так, ми пішли з квартири о третій годині, а вони залишилися. *(Yes, we left the apartment at three o'clock, and they stayed.)*

In English, you can simply say "I go" whether you are walking to the kitchen, driving to another city, or flying to another country. Ukrainian requires much more precision. We categorize the **рух** (motion) based on two main factors: the method of transport and the **напрямок** (direction) of the action. 

Українська мова розрізняє рух пішки, рух транспортом та рух у повітрі. Також дуже важливо знати, чи це дія в один бік у даний момент, чи це регулярна звичка.

> *The Ukrainian language distinguishes motion on foot, motion by transport, and motion in the air. It is also very important to know whether this is an action in one direction at a given moment, or a regular habit.*

This distinction is fundamental. A one-way trip happening right now uses a completely different verb than a regular commute that happens every day. For each transport method, we have one verb for a unidirectional, in-progress action, and another for a multidirectional or habitual action.

The first pair is used for moving on foot. Use **іти** (to go on foot) when you are walking right now in one specific direction. Use **ходити** (to walk regularly) when you walk often, back and forth, or aimlessly.

Я зараз іду до магазину, бо мені потрібен хліб. Це моя мета на цей момент. Але я ходжу до цього магазину щодня, тому що він дуже близько.

> *I am walking to the store right now because I need bread. This is my goal for this moment. But I walk to this store every day because it is very close.*

Notice how the context changes the verb. If someone asks what you are doing right now, you use the first verb. If you describe your daily routine, you use the second one. The perfective verb **піти** (to leave on foot — pf.) is formed directly from the first verb.

The second pair is used whenever a vehicle is involved, whether you are the driver or a passenger. This applies to cars, buses, trains, and bicycles. Use **їхати** (to go by vehicle) for a trip happening right now. Use **їздити** (to ride regularly) for routine trips or commuting.

Ми зараз їдемо до Львова на машині. Дорога дуже довга, але ми любимо подорожувати. Ми їздимо до Львова щоліта, щоб побачити друзів.

> *We are driving to Lviv by car right now. The road is very long, but we love to travel. We drive to Lviv every summer to see friends.*

:::info
**Grammar box**

Remember that Ukrainian strictly separates walking from using transport. If you use a walking verb for a long trip, people will think you are literally traveling on foot!

**Я іду до Києва.** — *I am walking to Kyiv (on foot).*

Always use the vehicle verbs for long distances. The perfective verb **поїхати** (to leave by vehicle — pf.) is formed by adding a prefix to the one-way verb.
:::

The third pair is specifically for motion through the air. Use **летіти** (to fly) when a plane, bird, or person is flying in one direction right now. Use **літати** (to fly regularly) for habitual flights, round trips, or the general ability to fly.

У небі летить великий літак. Він летить до Києва. Мій колега дуже часто літає у відрядження. Він літає літаком, тому що це найшвидший спосіб.

> *A big plane is flying in the sky. It is flying to Kyiv. My colleague very often flies on business trips. He flies by plane because it is the fastest method.*

<!-- INJECT_ACTIVITY: group-sort-sort-motion-verb-forms-into-unidirectional-vs-multidirectional-categories -->

## Дієвідміна та доконаний вид (~550 words)

Now that we know when to use each verb, we need to learn how to conjugate them. The first pair of verbs, **іти** (to go on foot — unidirectional) and **ходити** (to go on foot — multidirectional), belong to different conjugation groups. The verb **іти** follows the first conjugation pattern. Its stem is **ід-**, and we add the standard vowels for this group: -у, -еш, -е, -емо, -ете, -уть. The verb **ходити** belongs to the second conjugation pattern. It also introduces a common feature of Ukrainian grammar: consonant alternation.

Я іду, ти ідеш, він іде, ми ідемо, ви ідете, вони ідуть. Це дуже правильне дієслово. Але дієслово «ходити» має одну особливість. У першій особі однини ми бачимо чергування приголосних. Приголосний звук «д» змінюється на «дж». Тому ми кажемо: я ходжу, ти ходиш, вона ходить, ми ходимо, ви ходите, вони ходять.

> *I go, you go, he goes, we go, you go, they go. This is a very regular verb. But the verb "ходити" has one special feature. In the first person singular, we see an alternation of consonants. The consonant sound "д" changes to "дж". Therefore, we say: I go, you go, she goes, we go, you go, they go.*

The second pair involves transport. The verb **їхати** (to go by vehicle — unidirectional) belongs to the first conjugation. Its stem changes to **їд-** in the present tense, giving it standard first conjugation endings. The multidirectional partner, **їздити** (to go by vehicle — multidirectional), belongs to the second conjugation and has a consonant alternation.

Дієслово «їхати» має такі форми: я їду, ти їдеш, він їде, ми їдемо, ви їдете, вони їдуть. Коли ми відмінюємо дієслово «їздити», група приголосних «зд» змінюється на «ждж». Я їжджу на роботу щодня. Далі чергування зникає. Ти їздиш, він їздить, ми їздимо, ви їздите, вони їздять.

> *The verb "їхати" has the following forms: I drive, you drive, he drives, we drive, you drive, they drive. When we conjugate the verb "їздити", the consonant group "зд" changes to "ждж". I drive to work every day. After that, the alternation disappears. You drive, he drives, we drive, you drive, they drive.*

:::info
**Grammar box**
The consonant alternations (д → дж, зд → ждж) only happen in the **я** (I) form of the present tense for these specific verbs. All other forms keep the regular consonant from the infinitive.
:::

The final pair is for motion through the air. The unidirectional verb **летіти** (to fly — unidirectional) belongs to the second conjugation and experiences a consonant alternation where the letter «т» changes to «ч». The multidirectional verb **літати** (to fly — multidirectional) is a completely regular first conjugation verb.

Дієслово «летіти» має такі форми: я лечу, ти летиш, літак летить, ми летимо, ви летите, птахи летять. Дієслово «літати» відмінюється дуже просто: я літаю, ти літаєш, вона літає, ми літаємо, ви літаєте, вони літають.

> *The verb "летіти" has the following forms: I fly, you fly, the plane flies, we fly, you fly, the birds fly. The verb "літати" is conjugated very simply: I fly, you fly, she flies, we fly, you fly, they fly.*

Up to this point, we have only looked at imperfective verbs. To form the perfective partners for our unidirectional motion verbs, we add the prefix **по-**. This creates the verbs **піти** (to leave on foot — pf.), **поїхати** (to leave by vehicle — pf.), and **полетіти** (to fly off — pf.). Because they are perfective, we frequently use them in the past tense to indicate that someone has set off or departed.

Від дієслова «іти» ми утворюємо доконаний вид «піти». Минулий час має інший корінь: він пішов, вона пішла, ми пішли. Від дієслова «їхати» ми утворюємо слово «поїхати». Її сестра поїхала на роботу. Від дієслова «летіти» ми утворюємо форму «полетіти». Наш літак полетів.

> *From the verb "іти", we form the perfective aspect "піти". The past tense has a different root: he left, she left, we left. From the verb "їхати", we form the word "поїхати". Her sister left for work. From the verb "летіти", we form the form "полетіти". Our plane took off.*

To summarize, if a **рух** (movement, motion) in a specific **напрямок** (direction) is happening right now, you use the unidirectional present tense verbs like **іду** or **їду**. If the action of leaving is already complete and the person is gone, you use the perfective past tense forms like **пішов** or **поїхав**.

<!-- INJECT_ACTIVITY: fill-in-motion-context -->

## Моделі дієвідмінювання: казати, пити, боротися (~600 words)

We have seen how verbs of motion use consonant alternations, like the «д» changing to «дж» in the word for "I drive regularly." This is not a random exception or a mistake. Ukrainian has a very predictable and historical system of consonant alternations that appear across many different verbs. The most common sound changes are «з» to «ж», «с» to «ш», «т» to «ч», and «д» to «дж». When you learn these patterns, you stop memorizing individual exceptions and start seeing the underlying logic of the language. Mastering a few key conjugation models, like **казати / кажу** (to say — stem change model), will unlock dozens of new vocabulary words for you. Let's look at three essential models that every learner needs to know in order to speak naturally.

Перша важлива модель — це дієслово «казати». У цій групі приголосний звук в основі слова змінюється для всіх осіб теперішнього часу. Літера «з» змінюється на «ж», і ми отримуємо нову основу «каж-». Це дієслово першої дієвідміни, тому ми додаємо до нього стандартні закінчення: я кажу, ти кажеш, він каже, ми кажемо, ви кажете, вони кажуть. За цією ж моделлю відмінюється дуже популярне дієслово «писати», де літера «с» змінюється на «ш»: я пишу, ти пишеш, вона пише, вони пишуть. Якщо ми додамо префікс, граматичне правило зовсім не зміниться. Наприклад, дієслово доконаного виду «сказати» матиме такі ж форми: я скажу, ти скажеш, вони скажуть.

> *The first important model is the verb "казати". In this group, the consonant sound in the word stem changes for all persons in the present tense. The letter "з" changes to "ж", and we get the new stem "каж-". This is a first conjugation verb, so we add standard endings to it: I say, you say, he says, we say, you say, they say. The very popular verb "писати" is conjugated according to this same model, where the letter "с" changes to "ш": I write, you write, she writes, they write. If we add a prefix, the grammatical rule will not change at all. For example, the perfective verb "сказати" will have the same forms: I will say, you will say, they will say.*

:::info
**Grammar box**
Remember that for second conjugation verbs (like *їздити* or *летіти*), the consonant alternation usually only happens in the **я** (I) form. But for first conjugation verbs like *казати* or *писати*, the changed consonant stays for the ENTIRE present tense paradigm. This makes them much easier to remember once you know the first form!
:::

The second model involves verbs with very short infinitives, where the stem drastically reduces and takes contracted endings. A perfect example is the irregular model **пити / п'ю** (to drink). These verbs often consist of just a single consonant and a vowel in their dictionary form, which makes their conjugation look quite different from standard verbs.

Дієслово «пити» має коротку основу, яка складається лише з одного приголосного звука «п». Оскільки після губного приголосного йде літера «ю» або «є», ми обов'язково ставимо апостроф. Форми теперішнього часу виглядають так: я п'ю, ти п'єш, вона п'є, ми п'ємо, ви п'єте, вони п'ють. Інші короткі дієслова працюють дуже схоже і зберігають цю логіку. Наприклад, дієслово «бити» має такі форми: я б'ю, ти б'єш, він б'є, вони б'ють. Дієслово «лити» теж втрачає свій голосний звук, але літера «л» подовжується: я ллю, ти ллєш, вона ллє, вони ллють.

> *The verb "пити" has a short stem consisting of only one consonant sound, "п". Since a labial consonant is followed by the letter "ю" or "є", we must use an apostrophe. The present tense forms look like this: I drink, you drink, she drinks, we drink, you drink, they drink. Other short verbs work very similarly and keep this logic. For example, the verb "бити" has these forms: I hit, you hit, he hits, they hit. The verb "лити" also loses its vowel sound, but the letter "л" is lengthened: I pour, you pour, she pours, they pour.*

The third model focuses on reflexive verbs. These are verbs that end in the particle **-ся** or **-сь**, which originally meant "oneself." The verb **боротися / борюся** (to fight/struggle — reflexive model) is an excellent example of a complex reflexive verb because it also features a stem change from «от» to «ор». Reflexive verbs are incredibly common in daily speech, so getting their endings right is essential.

Коли ми відмінюємо зворотне дієслово, ми спочатку змінюємо основну частину слова, а потім додаємо частку «-ся» або «-сь». Дієслово «боротися» має такі форми: я борюся, ти борешся, він бореться, ми боремося, ви боретеся, вони борються. Зверніть особливу увагу на вимову цих слів! Комбінація літер «-ться» завжди звучить як довгий м'який звук. Комбінація літер «-шся» теж має свою особливу вимову і звучить як довгий м'який звук «сся». Це дуже важливе фонетичне правило української мови, яке робить ваше мовлення більш природним.

> *When we conjugate a reflexive verb, we first change the main part of the word, and then we add the particle "-ся" or "-сь". The verb "боротися" has the following forms: I struggle, you struggle, he struggles, we struggle, you struggle, they struggle. Pay special attention to the pronunciation of these words! The letter combination "-ться" always sounds like a long soft sound. The letter combination "-шся" also has its own special pronunciation and sounds like a long soft sound "сся". This is a very important phonetic rule of the Ukrainian language that makes your speech more natural.*

Mastering these three specific irregularities might feel challenging at first, but it is a crucial stepping stone for reaching the B1 level. Once you are comfortable with the persistent consonant changes in first conjugation verbs, the contracted endings of short verbs, and the phonetic rules of reflexive structures, you will be well prepared. You will soon be able to conjugate hundreds of new verbs intuitively without looking them up.

<!-- INJECT_ACTIVITY: quiz-conjugate-and-choose-the-correct-form-for-the-given-person-and-number -->

## Рух + прийменники + відмінки (~500 words)

When describing **рух** (movement, motion), choosing the right **напрямок** (direction) is essential. To express direction *to* a destination, Ukrainian uses three main prepositions. The preposition «до» (to/towards) always takes the Genitive case. The prepositions «на» (onto) and «в/у» (into) require the Accusative case when indicating motion towards a target.

Коли ви хочете **піти** (to leave on foot — pf.) до друга, ви використовуєте родовий відмінок. Якщо вам потрібно **поїхати** (to leave by vehicle — pf.) на пошту або в місто, ви обираєте знахідний відмінок. Завжди звертайте увагу на ці маленькі слова, коли будуєте речення.

> *When you want to leave on foot to a friend's place, you use the Genitive case. If you need to leave by vehicle to the post office or into the city, you choose the Accusative case. Always pay attention to these small words when building sentences.*

To express direction *from* an origin, the logic simply reverses, and we use the Genitive case across the board. If you went *into* («в/у») a place, you return *from* («з/із») it. If you went *onto* («на») a surface, you also return *from* («з/із») it. However, if you went *to* a person («до»), you must return *from* («від») that person.

Кожного вечора учні можуть **іти / ходити** (to go on foot — unidirectional/multidirectional) зі школи через старий центр міста. Дорослі часто змушені **їхати / їздити** (to go by vehicle — unidirectional/multidirectional) з роботи дуже довго через великі затори. Коли ми повертаємося від лікаря або від друга, ми також завжди використовуємо родовий відмінок.

> *Every evening students can go on foot from school through the old city center. Adults are often forced to go by vehicle from work for a very long time because of huge traffic jams. When we return from a doctor or from a friend, we also always use the Genitive case.*

Sometimes your journey is not about the destination, but the path itself. To describe motion *through* a space, use «через» with the Accusative case. To describe motion *along* a surface or route, use «по» with the Locative case. People who like to **летіти / літати** (to fly — unidirectional/multidirectional) often look down at the paths we take.

Ми часто гуляємо по вулиці і просто насолоджуємося красивою архітектурою. Іноді набагато швидше пройти через парк, ніж довго обходити його навколо. Важливо постійно **боротися / борюся** (to fight/struggle — reflexive model) зі звичкою перекладати англійські прийменники дослівно.

> *We often walk along the street and simply enjoy the beautiful architecture. Sometimes it is much faster to go through the park than to walk around it for a long time. It is important to constantly fight the habit of translating English prepositions literally.*

During a trip, you will inevitably talk to other people about your route. You might **казати / кажу** (to say — stem change model) where you are heading, or **пити / п'ю** (to drink — irregular model) coffee while waiting for your transport. When explaining *how* you are traveling, use the Instrumental case without any prepositions.

> — **Олег:** Привіт! Куди ти їдеш? *(Hi! Where are you driving to?)*
> — **Анна:** Їду на роботу. А ти звідки йдеш? *(I am driving to work. And where are you walking from?)*
> — **Олег:** Іду з магазину. Як ти їдеш туди? *(I am walking from the store. How are you traveling there?)*
> — **Анна:** Автобусом, бо моя машина зламалася. *(By bus, because my car broke down.)*

:::note
**Quick tip**
Always ask yourself the right question to choose the correct preposition and case combination. If the motion is "to" a place, ask «Куди?» (Where to?). If the motion is "from" an origin, ask «Звідки?» (From where?). If there is no motion and you are just describing location, ask «Де?» (Where at?).
:::

<!-- INJECT_ACTIVITY: match-up-prepositions-cases -->
<!-- INJECT_ACTIVITY: unjumble-directional-sentences -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: motion-verbs
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
