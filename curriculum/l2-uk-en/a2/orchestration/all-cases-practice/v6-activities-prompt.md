<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/all-cases-practice.yaml` file for module **37: Все разом** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-identify-which-case-a-highlighted-noun-is-in-and-explain-why-verb-or-preposition-trigger -->`
- `<!-- INJECT_ACTIVITY: match-up-health-cases -->`
- `<!-- INJECT_ACTIVITY: fill-in-travel-dialogue -->`
- `<!-- INJECT_ACTIVITY: error-correction-cases -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete gaps in a dialogue with the correct case form — all 7 cases represented,
    both singular and plural
  items: 8
  type: fill-in
- focus: Identify which case a highlighted noun is in and explain why (verb or preposition
    trigger)
  items: 8
  type: quiz
- focus: Match sentence halves so that the case form in the first half agrees with
    the preposition/verb in the second half
  items: 8
  type: match-up
- focus: Find and fix wrong case endings across all 7 cases (e.g., *допомагаю сестру
    → сестрі, *багато студенти → студентів)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- рецепт (prescription, recipe)
- температура (temperature)
- Карпати (Carpathians)
- милуватися (to admire)
- частувати (to treat (with food))
required:
- вечірка (party)
- подарунок (gift, present)
- лікар (doctor)
- пацієнт (patient)
- здоров'я (health)
- ліки (medicine)
- подорож (trip, journey)
- потяг (train)
- визначне місце (landmark, sight)
- запрошувати (to invite)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалог 1: Організовуємо день народження (Dialogue 1: Organizing a Birthday Party)

Planning a surprise **вечірка** (party) for a friend involves a lot of details and coordination. You have to decide who to invite, what kind of food to prepare, and where the celebration will take place. When native speakers like Оксана and Андрій discuss these plans, they naturally jump between all seven grammatical cases in a single conversation. Seeing all the cases working together is the best way to understand how Ukrainian sentences are built. Let's look at how they organize a celebration for their friend Олена.

This first part of their conversation focuses on the guest list and the food. It is time **запрошувати** (to invite) the guests and prepare the menu.

> — **Оксана:** Привіт, Андрію! У суботу буде вечірка для Олени. *(Hi, Andriy! On Saturday there will be a party for Olena.)*
> — **Андрій:** Клас! А хто прийде? *(Cool! And who will come?)*
> — **Оксана:** Буде багато гостей. Нам час запрошувати друзів. *(There will be many guests. It is time for us to invite friends.)*
> — **Андрій:** Я можу купити великий торт. *(I can buy a large cake.)*
> — **Оксана:** Це чудова ідея. У нас ще немає торта. *(That is a wonderful idea. We don't have a cake yet.)*
> — **Андрій:** А що ми будемо пити? *(And what will we drink?)*
> — **Оксана:** Я куплю сік і воду. *(I will buy juice and water.)*
> — **Андрій:** Добре, я все зрозумів. *(Good, I understood everything.)*

In this first half of the dialogue, we see the Nominative, Genitive, and Accusative cases in action. The Nominative case introduces the main subjects of the sentence, such as when Andriy asks **хто** (who) will come to the celebration. The word **торт** (cake) changes its form depending on its grammatical role. When Andriy offers to buy it, it acts as a direct object and stays **торт** in the Accusative case because it is an inanimate object. However, when Oksana points out that they do not have one, the negative word **немає** (there is no) forces it into the Genitive case, making it **торта**.

Ми також бачимо знахідний відмінок для живих істот. Оксана каже запрошувати друзів на свято. Оскільки друзі — це люди, ця форма збігається з формою родового відмінка.

> *We also see the Accusative case for living beings. Oksana says to invite friends to the holiday. Because friends are people, this form matches the Genitive case form.*

Now let's look at the second part of their conversation, where they discuss the perfect **подарунок** (gift), the location, and the decorations.

> — **Андрій:** Оксано, який подарунок купимо Олені? *(Oksana, what gift will we buy for Olena?)*
> — **Оксана:** Може, книгу? Треба написати друзям і запитати. *(Maybe a book? We need to write to the friends and ask.)*
> — **Андрій:** Добра ідея. А де ми зустрінемося? У кафе? *(Good idea. And where will we meet? In a cafe?)*
> — **Оксана:** Так, ми підемо туди з друзями. *(Yes, we will go there with friends.)*
> — **Андрій:** Ми прикрасимо кімнату яскравими кульками! *(We will decorate the room with bright balloons!)*
> — **Оксана:** Андрію, це буде чудовий сюрприз. *(Andriy, this will be a wonderful surprise.)*
> — **Андрій:** Згоден. На вечірці буде дуже весело. *(I agree. It will be very fun at the party.)*

The second part of the conversation brings in the four remaining cases. The Vocative case is used for direct address, which is why the names change to **Оксано** and **Андрію**. The Dative case shows the recipient of an action, such as buying a gift for Olena (**Олені**) or writing a message to the friends (**друзям**). We use the Instrumental case to show accompaniment, like going with friends (**з друзями**), or to indicate the instrument used to perform an action, like decorating with balloons (**кульками**). Finally, the Locative case is used to indicate the location of an event or meeting.

:::info
**Grammar box**
Remember that the Locative case is the only case that *never* appears without a preposition. You will always see it with words like **у/в** (in) or **на** (on/at), as seen in the phrases **у кафе** (in a cafe) and **на вечірці** (at the party).
:::

:::tip
**Did you know?**
Ukrainian birthday traditions might differ from what you are used to. In some cultures, guests pool their money to pay for the birthday person's meal or drinks when they go out to celebrate. In Ukraine, the custom is the exact opposite. The birthday person, known as the іменинник (birthday boy) or іменинниця (birthday girl), is expected to **частувати** (treat) the guests to food and drinks. The guests bring gifts, but the host covers the cost of the celebration.
:::

<!-- INJECT_ACTIVITY: quiz-identify-which-case-a-highlighted-noun-is-in-and-explain-why-verb-or-preposition-trigger -->

## Діалог 2: У лікарні (Dialogue 2: In the Hospital)

Our next scenario takes us to the hospital, where we will observe a conversation between a doctor and a patient. This dialogue focuses on expressing physical states, describing symptoms, and giving medical advice. We will see how different case constructions are essential for communicating health concerns accurately. You will notice that talking about how you feel in Ukrainian requires a completely different sentence structure than in English.

> — **Лікар:** Добрий день! Заходьте, будь ласка. Що вас турбує сьогодні? *(Good day! Come in, please. What is bothering you today?)*
> — **Пацієнт:** Добрий день! Мені дуже погано ще з учорашнього вечора. У мене висока температура. *(Good day! I have felt very bad since yesterday evening. I have a high temperature.)*
> — **Лікар:** Розумію. Це може бути вірус. У вас болить голова або горло? *(I understand. This might be a virus. Does your head or throat ache?)*
> — **Пацієнт:** Так, у мене сильно болить голова, але немає великого болю в горлі. *(Yes, my head aches badly, but there is no great pain in the throat.)*
> — **Лікар:** Ясно. Що я можу порадити пацієнтові в такій ситуації? Звичайно, багато відпочивати. *(I see. What can I advise a patient in such a situation? Of course, to rest a lot.)*
> — **Пацієнт:** Я згоден. Чи є гарна аптека біля лікарні? *(I agree. Is there a good pharmacy near the hospital?)*
> — **Лікар:** Так, нова аптека знаходиться зовсім поруч, біля лікарні, праворуч від головного входу. *(Yes, the new pharmacy is located very close, near the hospital, to the right of the main entrance.)*
> — **Пацієнт:** Дякую, мені вже трохи краще від вашої уваги та підтримки. *(Thank you, I feel a little better already from your attention and support.)*

У цій частині розмови ми чітко бачимо, як працюють називний, родовий та давальний відмінки. Коли пацієнт говорить про свої симптоми, він використовує конструкцію «у мене» з іменником у називному відмінку. Він каже: «у мене температура», «у мене болить голова». В українській мові ми не кажемо, що ми «маємо» біль або температуру.

> *In this part of the conversation, we clearly see how the Nominative, Genitive, and Dative cases work. When the patient talks about his symptoms, he uses the construction "у мене" with a noun in the Nominative case. He says: "у мене температура" (I have a temperature), "у мене болить голова" (my head aches). In Ukrainian, we do not say that we "have" pain or a temperature.*

To describe a general physical or emotional state, we use the Dative case with an adverb. The patient uses this when saying «мені погано» and later «мені краще». Notice how the Genitive case appears after the preposition «біля» to indicate location, and after the negative word «немає» to show absence. Finally, the word **пацієнт** (patient) is in the Dative case because it acts as the recipient of the doctor's advice.

> — **Пацієнт:** Пане докторе, що мені робити далі? Я хочу швидко одужати. *(Mr. Doctor, what should I do next? I want to recover quickly.)*
> — **Лікар:** Ви прийшли до мене з сильним кашлем і температурою. Вам треба регулярно приймати ці ліки. *(You came to me with a severe cough and a temperature. You need to take this medicine regularly.)*
> — **Пацієнт:** Я можу купити їх просто так в аптеці? *(Can I buy them just like that in the pharmacy?)*
> — **Лікар:** Ні, це серйозні препарати. Купіть їх за рецептом. Я зараз випишу потрібний документ. *(No, these are serious medications. Buy them with a prescription. I will write out the necessary document now.)*
> — **Пацієнт:** Лікарю, а коли мені прийти до вас знову? *(Doctor, and when should I come to you again?)*
> — **Лікар:** Ви зараз у лікарні на першому прийомі. Чекаю вас на огляд через один тиждень. *(You are currently in the hospital at the first appointment. I am waiting for you for a check-up in one week.)*
> — **Пацієнт:** Дякую за допомогу! Я буду дуже уважно берегти своє здоров'я. *(Thank you for the help! I will protect my health very carefully.)*
> — **Лікар:** Це головне правило. Здоров'я — найважливіше для кожної людини. *(That is the main rule. Health is the most important thing for every person.)*

Тут ми зустрічаємо знахідний, орудний, місцевий та кличний відмінки в дії. Лікар каже «приймати ліки» і чекає пацієнта «на огляд» — це прямі об'єкти та напрямок дії у знахідному відмінку. Зверніть увагу, що слово «ліки» завжди вживається у множині, тому воно має відповідну форму.

> *Here we meet the Accusative, Instrumental, Locative, and Vocative cases in action. The doctor says to "take medicine" and waits for the patient "for a check-up" — these are direct objects and the direction of action in the Accusative case. Note that the word "ліки" (medicine) is always used in the plural, so it has the corresponding form.*

The Instrumental case describes accompanying symptoms or conditions, as seen in the phrases «з кашлем» and «за рецептом». The Locative case pins down the exact location of the action, such as «у лікарні» and «на прийомі». Finally, direct address triggers the Vocative case, which is why the patient says «Пане докторе» and «Лікарю».

It is also important to understand how to change singular concepts to plural. For example, the phrase «один пацієнт» in the Nominative case changes completely in the Genitive plural to become «багато пацієнтів». Words that only exist in the plural, known as pluralia tantum, like **ліки** (medicine), stay the same in the Nominative and Accusative cases. However, they change to «ліків» in the Genitive case, such as when you say «багато ліків».

:::info
**Grammar box**
When talking about health, avoid translating directly from English. Never use the direct translation «Я маю головний біль». Always use the natural Ukrainian structure for aches, such as **У мене болить голова** (My head aches). The word **лікар** (doctor) and the piece of paper they give you, the **рецепт** (prescription), are essential vocabulary for a successful hospital visit.
:::

<!-- INJECT_ACTIVITY: match-up-health-cases -->

## Діалог 3: Подорож Україною (Dialogue 3: Traveling Across Ukraine)

Третя ситуація — це велика **подорож** (trip) Україною. Двоє друзів планують свій маршрут, обговорюють транспорт та міста, які хочуть побачити. У цьому діалозі ви побачите, як працюють дієслова руху разом з різними прийменниками та відмінками.

> *The third situation is a big trip across Ukraine. Two friends are planning their route, discussing transport and the cities they want to see. In this dialogue, you will see how verbs of motion work together with different prepositions and cases.*

> — **Марко:** Привіт, Тарасе! Я вже планую нашу літню відпустку. Київ — гарне місто, але я хочу поїхати на захід. *(Hi, Taras! I am already planning our summer vacation. Kyiv is a beautiful city, but I want to go to the west.)*
> — **Тарас:** Привіт! Це чудова ідея. Отже, ми їдемо з Києва. Куди саме ти хочеш поїхати? *(Hi! That is a great idea. So, we are traveling from Kyiv. Where exactly do you want to go?)*
> — **Марко:** Я хочу купити квитки до Львова. Там є багато **визначних місць** (landmarks). *(I want to buy tickets to Lviv. There are many landmarks there.)*
> — **Тарас:** Згоден. Але спочатку нам треба відвідати Одесу. Я давно там не був. *(Agreed. But first we need to visit Odesa. I haven't been there in a long time.)*
> — **Марко:** Добре. Тоді ми поїдемо через Умань. Це дуже цікавий і гарний маршрут. *(Good. Then we will travel through Uman. It is a very interesting and beautiful route.)*
> — **Тарас:** Супер. Я подивлюся, скільки коштують квитки, і ми вирішимо деталі. *(Super. I will check how much the tickets cost, and we will decide the details.)*

When planning a route, the verbs of motion dictate the cases you use. The starting point always uses the preposition **з** to mean "from" with the Genitive case, as in «з Києва». The destination uses **до** to mean "to", which also requires the Genitive case, like «до Львова». However, if you are passing through a place, you use the preposition **через** (through) with the Accusative case, resulting in «через Умань». You also see the Genitive plural in action when Marko says «багато визначних місць», because quantity words always trigger the Genitive case for the following noun.

> — **Тарас:** Друже! Нам треба поспішати. Квитки швидко купують. Краще поїхати **потягом** (train). *(Friend! We need to hurry. Tickets are bought quickly. It is better to travel by train.)*
> — **Марко:** Тарасе, я теж так думаю. Я їду з подругою, тому нам потрібні два місця поруч. *(Taras, I think so too. I am traveling with a girlfriend, so we need two seats next to each other.)*
> — **Тарас:** Чудово. Тоді ми зустрінемося у Львові на вокзалі. Що будемо робити там? *(Great. Then we will meet in Lviv at the station. What will we do there?)*
> — **Марко:** Спочатку купимо сувеніри друзям у Львові. А потім повернемося і гулятимемо по Хрещатику. *(First we will buy souvenirs for friends in Lviv. And then we will return and walk along Khreshchatyk.)*
> — **Тарас:** Ти забув про гори. Після Львова ми будемо **милуватися** (to admire) Карпатами. *(You forgot about the mountains. After Lviv we will admire the Carpathians.)*
> — **Марко:** Точно! У 2024 році це буде наша найкраща подорож. *(Exactly! In 2024, this will be our best trip.)*

Notice how the Locative and Instrumental cases serve very different purposes here. The Locative case marks a static location or time, as seen in «у Львові» and «у 2024 році». It is also used after the preposition **по** to describe movement across a surface, creating the authentic Ukrainian phrase «по Хрещатику». The Instrumental case shows the means of transport without any preposition, like «поїхати потягом». It also follows specific verbs. For example, the verb **милуватися** (to admire) always requires the Instrumental case. The noun **Карпати** (the Carpathians) is a word that only exists in the plural, so it takes the Instrumental plural ending to become «Карпатами».

Українська мова має зручні фрази для планування. Ви можете пропонувати ідеї так: «Давай поїдемо...», «Може, спочатку...» або «А потім можна...». Ці конструкції часто вимагають інфінітива, наприклад, «можна поїхати». Вибрані дієслова руху потім визначають правильний відмінок для вашого напрямку.

> *The Ukrainian language has convenient phrases for planning. You can suggest ideas like this: "Let's go...", "Maybe, first...", or "And then we can...". These constructions often require an infinitive, for example, "one can go". The chosen verbs of motion then determine the correct case for your destination.*

:::info
**Grammar box**
Remember that the preposition **по** in Ukrainian requires the Locative case when describing movement along a surface (e.g., **по вулицях**, **по місту**). Do not use the Dative case here, as that is a common error borrowed from other languages.
:::

<!-- INJECT_ACTIVITY: fill-in-travel-dialogue -->

## Самоперевірка: Знайди помилку (Self-Check: Find the Error)

Пошук помилок у тексті — це останній крок до розуміння граматики. Коли ви можете пояснити проблему, ви дійсно знаєте правило. Це важливо для вашого здоров'я під час навчання, щоб не мати стресу. Прочитайте ці короткі тексти та знайдіть неправильні слова.

> *Finding errors in a text is the final step to understanding grammar. When you can explain the problem, you truly know the rule. This is important for your **здоров'я** (health) during your studies so you do not have stress. Read these short texts and find the incorrect words.*

Учора друзі поїхали у подорож. Вони подорожували швидким потягом. Спочатку вони їхали по *полям. Потім вони пішли дивитися визначне місце з *друзі. У цьому тексті є дві помилки з прийменниками. Фраза «по полям» — неправильна. Прийменник «по» вимагає місцевого відмінка, тому треба казати «по полях». Фраза «з друзі» також неправильна. Прийменник «з» вимагає орудного відмінка, тому правильна форма — «з друзями».

> *Yesterday the friends went on a **подорож** (trip, journey). They traveled by a fast **потяг** (train). First they drove across the fields (incorrect). Then they went to see a **визначне місце** (landmark, sight) with friends (incorrect). There are two mistakes with prepositions in this text. The phrase «по полям» is incorrect. The preposition «по» requires the Locative case, so you must say «по полях». The phrase «з друзі» is also incorrect. The preposition «з» requires the Instrumental case, so the correct form is «з друзями».*

Пацієнт прийшов у лікарню. Він сказав: «Я допомагаю *сестру, але зараз мені потрібні ліки». Там було багато *студенти. Лікар уважно слухав його. Тут є помилки з об'єктами та кількістю. Дієслово «допомагати» завжди вимагає давального відмінка. Правильно говорити «допомагаю сестрі». Слова, які означають кількість, вимагають родового відмінка множини. Тому треба казати «багато студентів».

> *The **пацієнт** (patient) came to the hospital. He said: "I am helping my sister (incorrect), but now I need **ліки** (medicine)." There were many students (incorrect) there. The **лікар** (doctor) listened to him carefully. Here there are mistakes with objects and quantity. The verb "to help" always requires the Dative case. It is correct to say «допомагаю сестрі». Words that mean quantity require the Genitive plural. Therefore, you must say «багато студентів».*

Щоб не робити таких помилок, завжди пам'ятайте про сім відмінків. Ця таблиця допоможе вам правильно вибрати форму слова. Використовуйте її, коли хочете купити подарунок, запрошувати гостей або організувати вечірку.

> *To avoid making such mistakes, always remember the seven cases. This table will help you correctly choose a word form. Use it when you want to buy a **подарунок** (gift, present), **запрошувати** (to invite) guests, or organize a **вечірка** (party).*

:::info
**Підказка з відмінків (Case Cheat Sheet)**

*   **Називний** (Nom): хто? / що? (Subject: Київ, друзі)
*   **Родовий** (Gen): кого? / чого? (Absence, quantity, 'з / до / біля': немає торта, до Львова)
*   **Давальний** (Dat): кому? / чому? (Recipient, age, impersonal states: друзям, мені холодно)
*   **Знахідний** (Acc): кого? / що? (Direct object, 'через': купити ліки, через Умань)
*   **Орудний** (Instr): ким? / чим? (Instrument, 'з' accompaniment: потягом, з кашлем)
*   **Місцевий** (Loc): на / у кому? / чому? (Location 'в / на / по': у лікарні, по Хрещатику)
*   **Кличний** (Voc): (Addressing someone directly: Оксано, лікарю!)
:::

<!-- INJECT_ACTIVITY: error-correction-cases -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: all-cases-practice
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

**Level: A2 (Module 37/60) — ELEMENTARY**

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
