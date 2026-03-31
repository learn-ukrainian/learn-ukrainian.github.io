<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/emergencies.yaml` file for module **54: Emergencies** (a1).

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

- `<!-- INJECT_ACTIVITY: quiz-emergency-phrases -->`
- `<!-- INJECT_ACTIVITY: fill-in-emergency-call -->`
- `<!-- INJECT_ACTIVITY: order-112-dialogue -->`
- `<!-- INJECT_ACTIVITY: fill-in-police-hospital -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct emergency phrase for the situation.
  items:
  - options:
    - Тут аварія! Викличте швидку!
    - Тут пожежа! Допоможіть!
    - Я загубив паспорт.
    question: You see a car crash.
  - options:
    - Тут пожежа! Допоможіть!
    - Тут аварія!
    - Мені потрібен лікар.
    question: You see a building on fire.
  - options:
    - Людині погано! Викличте швидку!
    - Викличте поліцію!
    - Я загубив паспорт.
    question: Someone is feeling very ill on the street.
  - options:
    - Я загубив паспорт.
    - Тут аварія!
    - Мені потрібна швидка.
    question: You cannot find your passport at the airport.
  - options:
    - Викличте поліцію! Допоможіть!
    - Тут пожежа!
    - Мені потрібен лікар.
    question: Someone stole your wallet.
  type: quiz
- focus: Complete the emergency phone call.
  items:
  - Алло! {Допоможіть|Дякую|Вибачте}! Тут аварія!
  - '{Викличте|Загубив|Потрібен} швидку допомогу!'
  - Я на {вулиці|лікарні|поліції} Хрещатик, біля метро.
  - Мене {звати|прізвище|адреса} Адам.
  - Мій номер {телефону|паспорта|будинку} — нуль дев'яносто три...
  - Мені потрібна {допомога|пожежа|аварія}!
  type: fill-in
- focus: Put the dialogue with the 112 operator in the correct order.
  items:
  - — Служба порятунку, слухаю вас.
  - — Допоможіть! Тут пожежа!
  - — Де ви?
  - — На вулиці Шевченка, будинок п'ять.
  - — Зрозуміло. Швидка і пожежники вже їдуть. Як вас звати?
  - — Мене звати Анна. Дякую!
  type: order
- focus: Reporting an issue at the police station or hospital.
  items:
  - Добрий день. Я {загубив|викличте|допоможіть} паспорт.
  - Моє {прізвище|ім'я|номер} — Сміт.
  - Мені {потрібен|погана|хворий} лікар.
  - У мене {алергія|пожежа|аварія} на ці таблетки.
  - Я не розумію. {Повторіть|Допоможіть|Викличте}, будь ласка.
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- пожежа (fire, f)
- порятунок (rescue, m)
- паспорт (passport, m)
- адреса (address, f)
- номер (number, m)
- алергія (allergy, f)
- форма (form/document, f)
- будинок (building, m)
required:
- допомога (help, f)
- допоможіть (help! — imperative)
- швидка (ambulance, f — short for швидка допомога)
- поліція (police, f)
- лікарня (hospital, f)
- аварія (accident, f)
- загубити (to lose)
- викликати (to call/summon)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
<!-- TAB:Урок -->

## Dialogues

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Опера́тор:</span> Слу́жба поряту́нку, слу́хаю вас. *(Emergency service, I'm listening.)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Допоможі́ть! Тут ава́рія! *(Help! There's an accident here!)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Люди́на не ру́хається! *(A person isn't moving!)*</div>


<div class="dialogue-line"><span class="speaker">Оператор:</span> Де ви? *(Where are you?)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> На ву́лиці Хреща́тик, бі́ля метро́ Майда́н Незале́жності. *(On Khreshchatyk street, near Maidan Nezalezhnosti metro.)*</div>


<div class="dialogue-line"><span class="speaker">Оператор:</span> Зрозумі́ло. Швидка́ вже ї́де. *(Understood. The ambulance is already on its way.)*</div>


<div class="dialogue-line"><span class="speaker">Оператор:</span> Як вас зва́ти? *(What's your name?)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Ме́не звати Адам. *(My name is Adam.)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Мій но́мер — нуль дев'яно́сто три... *(My number is zero ninety-three...)*</div>


<div class="dialogue-line"><span class="speaker">Оператор:</span> Дякую. Залиша́йтеся на мі́сці. *(Thank you. Stay where you are.)*</div>


</div>

Адам is walking near Maidan when he sees a car crash. He dials **112** (оди́н один два) — Ukraine's universal emergency number. The operator at **служба порятунку** (rescue service) picks up immediately. Notice how Адам uses short, urgent phrases: **Допоможіть!** (Help!), **Тут аварія!** (There's an accident!). No long sentences — just the essential information. The operator asks **Де ви?** (Where are you?) and Адам gives the street name and a landmark. Only after confirming the ambulance is coming does the operator ask for personal details.

Now Адам has a second problem — his passport is gone.

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Адам:</span> Ви́бачте, де тут полі́ція? *(Excuse me, where is the police station here?)*</div>


<div class="dialogue-line"><span class="speaker">Перехо́жий:</span> Поліція? Пря́мо і налі́во. *(Police? Straight and to the left.)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Дякую! *(Thanks!)*</div>


</div>

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Адам:</span> До́брий день. Я загуби́в па́спорт. *(Good day. I lost my passport.)*</div>


<div class="dialogue-line"><span class="speaker">Офіце́р:</span> Де ви йо́го загуби́ли? *(Where did you lose it?)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Я не зна́ю. Мо́же, в метро. *(I don't know. Maybe in the metro.)*</div>


<div class="dialogue-line"><span class="speaker">Офіцер:</span> Як ва́ше прі́звище? *(What is your surname?)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Сміт. Адам Сміт. *(Smith. Adam Smith.)*</div>


<div class="dialogue-line"><span class="speaker">Офіцер:</span> Ваш номер телефо́ну? *(Your phone number?)*</div>


<div class="dialogue-line"><span class="speaker">Адам:</span> Нуль дев'яносто три, п'ятсо́т два́дцять один... *(Zero ninety-three, five hundred twenty-one...)*</div>


<div class="dialogue-line"><span class="speaker">Офіцер:</span> До́бре. Запо́вніть цю фо́рму, будь ла́ска. *(Good. Fill out this form, please.)*</div>


</div>

Read both dialogues again and notice three things. First, emergency imperatives open the conversation — **Допоможіть!** and **Ви́кличте!** get immediate attention. Second, when talking to emergency services, location comes before your name: the operator needs to know *where* before *who*. Third, at the police station, the key vocabulary shifts to documents: **паспорт** (passport), **прізвище** (surname), and **фо́рма** (form). Read both dialogues aloud — the rhythm of short emergency phrases will stick in your memory.

## Е́кстрені ситуа́ції (Emergencies)

Ukraine's universal emergency number is **112** (**один один два**). It works from any phone — mobile or landline — and connects you to ambulance, police, or fire services. You can also call specific services directly: **103** reaches the ambulance (**швидка**), and **102** reaches the police (**поліція**). Before your first trip to Ukraine, save these numbers in your phone. You do not need perfect grammar to use them — you need the right phrase at the right moment.

Here are the survival phrases every learner must memorise as fixed chunks. Do not analyze the grammar — just learn them whole:

- **Допоможіть!** — Help!
- **Викличте швидку́!** — Call an ambulance!
- **Викличте полі́цію!** — Call the police!
- **Тут аварія!** — There's an accident here!
- **Тут поже́жа!** — There's a fire here!
- **Люди́ні пога́но!** — Someone is feeling unwell!
- **Ме́ні потрі́бна допомо́га!** — I need help!

You already know **Допоможіть** and **Викличте** — these are imperative forms reviewed from Module 43. The vocabulary is new, but the grammar pattern is familiar. **Аварія** (accident) and **пожежа** (fire) are passive recognition words — you will hear and understand them, and you use them only inside these fixed phrases.

Once the operator answers, they will ask **Де ви?** (Where are you?). Give your location using patterns from A1.5:

- **Я на вулиці...** — I'm on … street.
- **Я біля...** — I'm near...
- **Я в метро...** — I'm in the metro...
- **Адре́са: ву́лиця Хрещатик, буди́нок де́сять.** — Address: Khreshchatyk street, building 10.

:::tip
Know your hotel address in Ukrainian. Programme it into your phone before you travel — if you are stressed in an emergency, reading from your screen is much easier than translating on the fly.
:::

<!-- INJECT_ACTIVITY: quiz-emergency-phrases -->

## Допомога (Getting Help)

At a hospital (**ліка́рня**), three phrases will carry you through the first minutes. **Мені потрі́бен лі́кар** (I need a doctor) uses the fixed chunk **мені потрібен** — treat it as a memorised formula, just as you learned **мені подо́бається** earlier. From Module 53 you already know **У мене боли́ть...** (My … hurts) — plug in **голова́** (head), **спи́на** (back), **рука́** (arm/hand), or **нога́** (leg/foot). If you have allergies, say **У мене алергі́я на...** (I'm allergic to...) followed by the allergen: **ці табле́тки** (these pills), **горі́хи** (nuts), **пеніцилі́н** (penicillin). The word **алергія** looks and sounds almost identical to its English equivalent — one less thing to memorise under pressure.

When Ukrainian comes too fast or you simply cannot follow, use these phrases as your emergency brake — reach for them immediately rather than nodding and hoping:

- **Я не розумі́ю.** — I don't understand.
- **Повторі́ть, будь ласка.** — Please repeat.
- **Говорі́ть пові́льніше, будь ласка.** — Please speak more slowly.
- **Ви гово́рите англі́йською?** — Do you speak English?

**Повторіть** and **говоріть** are imperative forms — the same pattern as **Допоможіть** and **Викличте**. You are not learning new grammar here, just applying familiar patterns in a new, critical context.

Finally, in any emergency — hospital, police station, or phone call — you will need the same block of personal information. Here is your checklist:

- **Мене звати Адам.** — My name is Adam.
- **Моє́ прізвище — Сміт.** — My surname is Smith.
- **Мій номер телефону — нуль дев'яносто три...** — My phone number is zero ninety-three...
- **Я з Кана́ди.** — I'm from Canada.
- **Я загубив паспорт.** — I lost my passport. *(male speaker)*
- **Я загуби́ла паспорт.** — I lost my passport. *(female speaker)*
- **Мій готе́ль — «Прем'є́р Пала́с».** — My hotel is Premier Palace.

Every item here is review from earlier modules — **Мене звати** from Module 2, **Я з** from Module 10, **Мій номер** from Module 20. The difference is the stakes: now you are not introducing yourself at a café, you are giving information that may determine how quickly help reaches you.

<!-- INJECT_ACTIVITY: fill-in-emergency-call -->

<!-- INJECT_ACTIVITY: order-112-dialogue -->

## Summary

The three scenarios in this module — calling **112** for an accident, reporting a lost document at the **поліція**, and asking for help at the **лікарня** — all follow the same structure. You state the problem, give your location, and share personal details: **ім'я́** (first name), **прізвище** (surname), **номер телефону** (phone number), and **адреса** (address). Master this pattern once and it works everywhere.

Here is your emergency survival kit — a reference block to save on your phone:

- **112** — universal emergency number (**один один два**)
- **Допоможіть! Викличте швидку / поліцію!** — first words to say
- **Тут аварія / пожежа!** — describe the emergency
- **Я на вулиці... / Я біля...** — give your location
- **У мене болить... / Мені потрібен лікар.** — at the hospital
- **Я загубив/загубила [document].** — at the police station
- **Ім'я, прізвище, номер телефону, краї́на, адреса** — personal info always needed

Test yourself with these questions — answer each one aloud in Ukrainian before checking:

- What is Ukraine's universal emergency number? → **112** (**один один два**)
- How do you shout "Help!" in Ukrainian? → **Допоможіть!**
- How do you call an ambulance? → **Викличте швидку!**
- How do you give your street address? → **Я на вулиці [name], будинок [number].**
- How do you say "I lost my passport"? → **Я загубив/загубила паспорт.**
- How do you ask a doctor to repeat something? → **Повторіть, будь ласка.**

<!-- INJECT_ACTIVITY: fill-in-police-hospital -->


<!-- TAB:Словник -->

### Обов'язко́ві та рекомендо́вані слова́

| Сло́во | Переклад | Части́на мо́ви | Рід |
|-------|----------|-------------|-----|
| **допомо́га** | help | ім. | ж. |
| **швидка́** | ambulance (short for швидка допомога) | ім. | ж. |
| **полі́ція** | police | ім. | ж. |
| **ліка́рня** | hospital | ім. | ж. |
| **ава́рія** | accident | ім. | ж. |
| **загуби́ти** | to lose (something) | дієсл. |  |
| **викликати** | to call, to summon | дієсл. |  |
| **поже́жа** | fire | ім. | ж. |
| **поряту́нок** | rescue | ім. | ч. |
| **па́спорт** | passport | ім. | ч. |
| **адре́са** | address | ім. | ж. |
| **но́мер** | number | ім. | ч. |
| **алергі́я** | allergy | ім. | ж. |
| **фо́рма** | form, document | ім. | ж. |
| **буди́нок** | building | ім. | ч. |
| **опера́тор** | operator (emergency services) | ім. | ч. |
| **ру́хатися** | to move | дієсл. |  |
| **перехо́жий** | passerby | ім. | ч. |
| **пря́мо** | straight ahead | присл. |  |
| **налі́во** | to the left | присл. |  |
| **офіце́р** | officer (police) | ім. | ч. |
| **прі́звище** | surname, family name | ім. | с. |
| **запо́внити** | to fill out (a form) | дієсл. |  |
| **лі́кар** | doctor | ім. | ч. |
| **голова́** | head | ім. | ч. |
| **спи́на** | back | ім. | ж. |
| **рука́** | arm, hand | ім. | ж. |
| **нога́** | leg, foot | ім. | ж. |
| **табле́тки** | pills, tablets | ім. | ж. |
| **горі́хи** | nuts | ім. |  |
| **пові́льніше** | more slowly | присл. |  |
| **ім'я́** | first name | ім. | с. |
| **зрозумі́ло** | understood, got it | присл. |  |
| **мі́сце** | place, spot | ім. | с. |
| **мо́же** | maybe, perhaps | дієсл. |  |

### Ви́рази

| Ви́раз | Переклад |
|-------|----------|
| **Допоможіть!** | Help! |
| **служба порятунку** | emergency rescue service |
| **Слухаю вас.** | I'm listening. (formal phone greeting) |
| **Викличте швидку!** | Call an ambulance! |
| **Викличте поліцію!** | Call the police! |
| **Тут аварія!** | There's an accident here! |
| **Тут пожежа!** | There's a fire here! |
| **Людині погано!** | Someone is feeling unwell! |
| **Мені потрібна допомога!** | I need help! |
| **Залишайтеся на місці.** | Stay where you are. |
| **Мені потрібен лікар.** | I need a doctor. |
| **У мене алергія на...** | I'm allergic to... |
| **Я не розумію.** | I don't understand. |
| **Повторіть, будь ласка.** | Please repeat. |
| **Говоріть повільніше, будь ласка.** | Please speak more slowly. |
| **Ви говорите англійською?** | Do you speak English? |
| **Я загубив паспорт.** | I lost my passport. (male speaker) |
| **Я загубила паспорт.** | I lost my passport. (female speaker) |
| **один один два** | one-one-two (112 — universal emergency number) |

### Картки́ — Flashcards

<FlashcardDeck client:only="react" cards={[{ front: "допомо́га", back: "help", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "швидка́", back: "ambulance (short for швидка допомога)", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "полі́ція", back: "police", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ліка́рня", back: "hospital", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "ава́рія", back: "accident", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "загуби́ти", back: "to lose (something)", subtitle: "дієсл." }, { front: "викликати", back: "to call, to summon", subtitle: "дієсл." }, { front: "поже́жа", back: "fire", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "поряту́нок", back: "rescue", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "па́спорт", back: "passport", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "адре́са", back: "address", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "но́мер", back: "number", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "алергі́я", back: "allergy", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "фо́рма", back: "form, document", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "буди́нок", back: "building", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "опера́тор", back: "operator (emergency services)", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "ру́хатися", back: "to move", subtitle: "дієсл." }, { front: "перехо́жий", back: "passerby", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "пря́мо", back: "straight ahead", subtitle: "присл." }, { front: "налі́во", back: "to the left", subtitle: "присл." }, { front: "офіце́р", back: "officer (police)", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "прі́звище", back: "surname, family name", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "запо́внити", back: "to fill out (a form)", subtitle: "дієсл." }, { front: "лі́кар", back: "doctor", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "голова́", back: "head", subtitle: "ім.", tag: "ч.", tagColor: "#0057B8" }, { front: "спи́на", back: "back", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "рука́", back: "arm, hand", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "нога́", back: "leg, foot", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "табле́тки", back: "pills, tablets", subtitle: "ім.", tag: "ж.", tagColor: "#C2185B" }, { front: "горі́хи", back: "nuts", subtitle: "ім." }, { front: "пові́льніше", back: "more slowly", subtitle: "присл." }, { front: "ім'я́", back: "first name", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "зрозумі́ло", back: "understood, got it", subtitle: "присл." }, { front: "мі́сце", back: "place, spot", subtitle: "ім.", tag: "с.", tagColor: "#E65100" }, { front: "мо́же", back: "maybe, perhaps", subtitle: "дієсл." }]} />


<!-- TAB:Зошит -->

:::note
Розши́рені впра́ви для цього́ уро́ку ще в розро́бці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

**Дже́рела — References**

- State Standard 2024, §3
  _Thematic area: health and safety — emergency situations._

**Статті́ — Articles**

- [Something Hurts — Describing Pain in Ukrainian](https://www.ukrainianlessons.com/something-hurts/) (Phrases for doctor visits and emergencies)

**Anna Ohoiko — Ukrainian Lessons**

- [Ukrainian Г vs Ґ](https://www.ukrainianlessons.com/h-g/)
- [Ukrainian Tongue Twisters (Скоромо́вки)](https://www.ukrainianlessons.com/tonguetwisters/)
- [Prepositions У/В vs НА](https://www.ukrainianlessons.com/prepositions-u-na/)
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: emergencies
level: a1

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

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: examples[], prompt
- **classify**: Multi-category sort. Required: instruction, categories[{label, items[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A1.4+ (Module 54/55) — BEGINNER**

The learner knows ~500 words, basic grammar, can form sentences.

**Instructions in simple Ukrainian with English translation in parentheses.**
Example: 'Оберіть правильний варіант (Choose the correct option)'

**All core activity types are appropriate.**


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: general-reading
- **true-false** — Правда чи ні?: Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Answer questions about a text passage


**Use these patterns.** If the pattern library recommends `divide-words` for a syllable module, generate a `divide-words` exercise. If it recommends `group-sort` for gender, generate a `group-sort`. The patterns encode how Ukrainian teachers actually test these concepts.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Every activity MUST have at least 6 items.** Quiz = 6+ questions. Fill-in = 6+ sentences. Match-up = 6+ pairs. True-false = 6+ statements. Group-sort = 6+ items per group minimum. Anagram = 6+ words.
- If you can't think of 6 items, add more examples from the module's vocabulary and content. NEVER submit an activity with fewer than 6 items.
- **3-5 options per quiz/fill-in question** — enough to prevent guessing, not so many to overwhelm.

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
- `mcp__rag__verify_words` / `mcp__rag__verify_word` / `mcp__rag__verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp__rag__search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp__rag__search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp__rag__query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp__rag__query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp__rag__search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp__rag__query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp__rag__search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp__rag__search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp__rag__search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp__rag__search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp__rag__translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp__rag__query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp__rag__query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp__rag__search_style_guide` first (it knows calques). Then `mcp__rag__query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp__rag__verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp__rag__query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp__rag__verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp__rag__search_idioms` for Ukrainian expressions, `mcp__rag__search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp__rag__query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp__rag__query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp__rag__verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp__rag__verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp__rag__verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp__rag__query_pravopys` or `mcp__rag__search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp__rag__verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
