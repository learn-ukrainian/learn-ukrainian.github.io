<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/services-and-communication.yaml` file for module **22: На пошті** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-complete-post-office-dialogue-lines-with-correct-dative-forms -->`
- `<!-- INJECT_ACTIVITY: group-sort-service-phrases -->`
- `<!-- INJECT_ACTIVITY: match-up-requests-responses -->`
- `<!-- INJECT_ACTIVITY: quiz-dative-address-forms -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete post office dialogue lines with correct dative forms (Надішліть
    цю посилку ___)
  items: 8
  type: fill-in
- focus: Match service requests to appropriate responses (Допоможіть мені → Звичайно,
    що вам потрібно?)
  items: 8
  type: match-up
- focus: Choose the correct dative address form (дорогому/дорогій/дорогим + name)
  items: 8
  type: quiz
- focus: Sort phrases into categories — requesting (прохання), thanking (подяка),
    giving (давання)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- бандероль (small parcel, book post)
- квитанція (receipt)
- одержувач (recipient)
- відправник (sender)
- індекс (postal code)
required:
- пошта (post office, mail)
- лист (letter)
- конверт (envelope)
- марка (stamp)
- посилка (parcel, package)
- адреса (address)
- надіслати (to send)
- отримати (to receive)
- відправити (to send, to dispatch)
- листоноша (mail carrier)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## На пошті: Базова лексика (~450 words)

The Ukrainian postal service (Укрпошта) plays a vital role in daily life. Even in the digital age, people frequently visit the post office to send gifts to family or receive online shopping orders.

В Україні **пошта** (post office, mail) є дуже важливою. Люди часто ходять туди, щоб надіслати речі рідним або **отримати** (to receive) замовлення. Українці надсилають листи та подарунки не тільки в інші міста, але й за кордон. Це надійний спосіб зв'язку.

> *In Ukraine, the post office (mail) is very important. People often go there to send things to relatives or receive orders. Ukrainians send letters and gifts not only to other cities but also abroad. It is a reliable way of communication.*

When you visit a post office branch, you will see a postbox for outgoing mail. To send a standard **лист** (letter), you need a **конверт** (envelope) and a **марка** (stamp). You must carefully write the destination details and the postal code.

:::tip
**Did you know?**
In Ukrainian, **адреса** (address) is the physical location where you live or send mail. Be careful not to confuse it with the false friend *адрес*, which means a formal written greeting.
:::

Щоб ваш лист швидко знайшов дорогу, вам потрібна правильна адреса. Ви купуєте конверт і марку, а потім пишете індекс. Після цього ви просто кидаєте його в поштову скриньку. Працівники поштового відділення зроблять усе інше.

> *For your letter to quickly find its way, you need the correct address. You buy an envelope and a stamp, and then write the postal code. After that, you simply drop it into the postbox. The post office branch workers will do the rest.*

For larger items, you will send a **посилка** (parcel, package) or a smaller book post called a бандероль. An authentic and common Ukrainian word for a package is пакунок. When you drop off any of these items, the clerk gives you a receipt.

Коли ви відправляєте велику посилку або маленький пакунок, ви отримуєте квитанцію. Ця квитанція дуже важлива, бо там є номер. З цим номером ви знаєте, де зараз ваша бандероль. Ваш пакунок завжди буде в безпеці.

Every interaction involves a sender and a recipient. The person who delivers the mail is the **листоноша** (mail carrier). To express your needs, use perfective verbs like **надіслати** (to send) or **відправити** (to send, to dispatch). You also need verbs like отримати and забрати for receiving items. Always prefer *надіслати* specifically for letters and postcards.

Коли ви на пошті, ви можете сказати: «Я хочу забрати посилку». Або ви можете запитати: «Де можна надіслати листівку?». Відправник дає пакунок працівнику, а одержувач чекає на нього вдома. Іноді листоноша приносить листи прямо до дверей.

> *When you are at the post office, you can say: "I want to pick up a parcel." Or you can ask: "Where can I send a postcard?". The sender gives the package to the worker, and the recipient waits for it at home. Sometimes the mail carrier brings letters right to the doors.*

## Надіслати листа: Діалоги на пошті (~600 words)

Visiting a post office in Ukraine requires knowing a few specific phrases to communicate with the staff. Whether you are sending a simple document or a large box, the interaction usually follows a predictable script. Let's look at a typical conversation when someone wants to buy basic supplies and send a letter.

> — **Клієнт:** Добрий день! Дайте мені, будь ласка, два конверти і марки. Я хочу надіслати листа. *(Good day! Please give me two envelopes and stamps. I want to send a letter.)*
> — **Працівник пошти:** Добрий день. Ось ваші конверти. Куди ви надсилаєте листи? *(Good day. Here are your envelopes. Where are you sending the letters?)*
> — **Клієнт:** Один лист — у Київ, а другий — за кордон, у Польщу. *(One letter is to Kyiv, and the second is abroad, to Poland.)*
> — **Працівник пошти:** Тоді вам потрібні різні марки. Заповніть бланк, будь ласка, для міжнародного листа. *(Then you need different stamps. Please fill out the form for the international letter.)*
> — **Клієнт:** Дякую. Підкажіть мені, де можна надіслати листівку? *(Thank you. Tell me where I can send a postcard?)*
> — **Працівник пошти:** Ви можете просто кинути її в поштову скриньку біля входу. *(You can just drop it in the postbox near the entrance.)*

When you interact with a postal worker, clarity is key. To state your goal directly and politely, you should use the phrase **Я хочу** (I want) followed by an infinitive verb.

Коли ви спілкуєтеся з працівником пошти, треба говорити чітко. Найкращий спосіб зробити це — використати дієслово «хотіти». Наприклад, ви кажете: «Я хочу відправити посилку». Або ви кажете: «Я хочу надіслати листа». Дієслова «відправити» та «надіслати» означають одноразову дію. Ви робите це один раз і отримуєте конкретний результат.

> *When you communicate with a postal worker, you need to speak clearly. The best way to do this is to use the verb "to want". For example, you say: "I want to send a parcel". Or you say: "I want to send a letter". The verbs "to dispatch" and "to send" mean a one-time action. You do this once and get a specific result.*

If you are unsure where to perform an action or find a specific service in the building, you can ask for directions using **Де можна** (Where is it possible to).

Часто люди не знають, де лежать необхідні бланки. Або вони не знають, де стоїть потрібна поштова скринька. Тоді вони ввічливо запитують: «Де можна надіслати листівку?». Працівник пошти завжди допоможе вам. Він покаже, куди саме треба йти.

Let's look at a slightly more complex situation: sending a package internationally. You will need to interact more with the clerk, explain what you are sending, and understand specific terms on the customs forms.

> — **Клієнт:** Добрий день. Я хочу відправити цю бандероль. Це бандероль для сестри в Канаду. *(Good day. I want to send this book post. This is a book post for my sister to Canada.)*
> — **Працівник пошти:** Добре. Давайте її сюди. Вам треба заповнити спеціальну форму. *(Okay. Give it here. You need to fill out a special form.)*
> — **Клієнт:** Допоможіть мені, будь ласка. Що писати тут? *(Help me, please. What to write here?)*
> — **Працівник пошти:** Там, де написано «кому», це **одержувач**. А «від кого» — це **відправник**. *(Where it says "to whom", that is the recipient. And "from whom" is the sender.)*
> — **Клієнт:** Зрозумів. Скільки коштує відправити цю бандероль? *(Understood. How much does it cost to send this book post?)*
> — **Працівник пошти:** Триста гривень. Вона буде в Канаді приблизно через два тижні. *(Three hundred hryvnias. It will be in Canada in approximately two weeks.)*
> — **Клієнт:** Дякую вам за допомогу. Гарного дня! *(Thank you for your help. Have a good day!)*

In service situations, you often need to ask the clerk for assistance. Notice how the customer uses polite request forms to navigate the process smoothly.

Коли ми просимо про допомогу, ми часто використовуємо давальний відмінок. Слова «допоможіть» та «підкажіть» вимагають після себе займенника. Цей займенник відповідає на питання «кому?». Клієнт каже: «Допоможіть мені, будь ласка». Тут слово «мені» — це давальний відмінок від займенника «я».

> *When we ask for help, we often use the dative case. The words "help" and "tell" require a pronoun after them. This pronoun answers the question "to whom?". The customer says: "Help me, please". Here the word "me" is the dative case of the pronoun "I".*

:::info
**Grammar box**
The Dative case is essential for indirect objects. When you ask someone to do something *for you* or give something *to you*, you are the indirect receiver of that action. Verbs like **допомогти** (to help), **дати** (to give), and **підказати** (to suggest/tell) naturally govern the Dative case (**мені**, **вам**, **йому**).
:::

This dialogue also highlights the two main roles in any postal transaction: the sender and the recipient. Understanding these terms is crucial when filling out any official paperwork to ensure the package arrives at its destination.

На кожному бланку є дві дуже важливі графи. Ви повинні правильно написати адресу. Тоді листоноша знає, куди нести пакунок. Відправник — це людина, яка дає пакунок працівнику пошти. Одержувач — це людина, яка чекає на цю посилку вдома.

> *On every form, there are two very important columns. You must correctly write the address. Then the mail carrier knows where to carry the package. The sender is the person who gives the package to the post office worker. The recipient is the person who waits for this parcel at home.*

<!-- INJECT_ACTIVITY: fill-in-complete-post-office-dialogue-lines-with-correct-dative-forms -->

## Просити, дякувати, допомагати: Давальний у сфері послуг (~600 words)

When you are at the **пошта** (post office) or any service center, you will frequently need to ask the staff for assistance. In Ukrainian, when you ask someone to show, explain, or help with a task, the person who receives that action must be in the Dative case. Verbs like **допомагати** (to help), **показувати** (to show), and **пояснювати** (to explain) all require the Dative case.

Працівники пошти завжди готові допомогти. Коли ви не знаєте, як правильно відправити посилку, ви можете попросити про допомогу. Ви кажете працівнику, що він повинен показати чи пояснити інформацію саме вам.

> *Post office workers are always ready to help. When you do not know how to correctly dispatch a parcel, you can ask for help. You tell the worker that they must show or explain the information specifically to you.*

Here are common ways to request assistance:

**Допоможіть мені** заповнити цей бланк. — *Help me fill out this form.*

**Покажіть йому**, як це зробити. — *Show him how to do this.*

**Поясніть нам** правила. — *Explain the rules to us.*

Another crucial situation where the Dative case is mandatory in Ukrainian is when expressing gratitude. Unlike in English where you thank someone as a direct object, in Ukrainian you give your thanks *to* someone. The verb **дякувати** (to thank) strictly governs the Dative case.

:::info
**Grammar box**
The verb **дякувати** always takes the Dative case (**кому?**). You must say **дякую вам** (thank you), never the Accusative. This is a very common mistake for learners, so always remember that gratitude is directed *to* the person.
:::

Після того, як ви отримали допомогу, ви повинні подякувати людині. Якщо листоноша приніс вам лист, ви кажете: «Дякую листоноші за допомогу». Це дуже важливе правило.

> *After you have received help, you must thank the person. If the mail carrier brought you a letter, you say: "I thank the mail carrier for the help". This is a very important rule.*

In addition, the verb **радити** (to advise) takes the Dative case. Workers might suggest how to send your **лист** (letter) using the Instrumental case for the means of transport.

**Раджу вам** надіслати це бандероллю. — *I advise you to send this by book post.*

Працівник радить **мені** відправити речі поштою. — *The worker advises me to dispatch the items by mail.*

<!-- INJECT_ACTIVITY: group-sort-service-phrases -->

The Dative case also explains who an item is intended for. When preparing your package at home, you might ask a friend for a favor and tell them who will receive the gift.

Сьогодні мій сусід іде на пошту. Я маю велику коробку і хочу попросити його про послугу. Це подарунок моїй бабусі. Я кажу сусідові: «Допоможи мені загорнути цю посилку».

> *Today my neighbor is going to the post office. I have a large box and I want to ask him for a favor. This is a gift for my grandmother. I say to the neighbor: "Help me wrap this parcel."*

In this scenario, you use the Dative case multiple times. First, you explain that the gift is for your grandmother (**моїй бабусі**). Then, you give a direct command to your neighbor, asking him to help you (**мені**).

Він радить мені купити гарний папір. Ми разом пакуємо речі, а потім він несе їх у відділення. Я дуже дякую сусідові за допомогу.

> *He advises me to buy nice paper. We pack the items together, and then he carries them to the branch. I thank the neighbor very much for the help.*

When interacting with service workers, you frequently combine polite imperative commands with the Dative case to ask them to perform an action for you.

У сфері послуг ми постійно використовуємо ці форми. Клієнти просять працівників зробити щось для них. Наприклад, ви можете сказати: «Дайте мені конверт, будь ласка». Або ви питаєте: «Скажіть їй, скільки коштує марка».

> *In the service sector, we constantly use these forms. Customers ask workers to do something for them. For example, you can say: "Give me an envelope, please." Or you ask: "Tell her how much a stamp costs."*

Notice how the imperative verb directs the action, and the Dative pronoun specifies the receiver:

**Дай мені** ручку, будь ласка. — *Give me a pen, please.*

**Покажи нам**, де поштова скринька. — *Show us where the postbox is.*

**Скажіть їй** правильну адресу. — *Tell her the correct address.*

These short phrases are polite when combined with "будь ласка" and ensure that you get exactly the help you need.

<!-- INJECT_ACTIVITY: match-up-requests-responses -->

## Написати адресу: Давальний у листуванні (~550 words)

In Ukraine, writing a correct and complete address ensures your mail reaches its destination without delays. When you want to send a letter, a postcard, or a heavy package, you must accurately specify where it is going on the outside of the item. In Ukrainian, we use the specific phrase **надіслати за адресою** (to send to the address). This phrase uses the preposition **за** followed directly by the noun in the Instrumental case. You should never say "по адресу" — this is a common grammatical mistake heavily influenced by Russian and should be avoided. A standard Ukrainian address includes several key components written in a specific order.

Щоб відправити лист або велику посилку, вам потрібна правильна адреса. Спочатку ви завжди пишете поштовий індекс і ваше місто. Потім треба написати назву вулиці, номер будинку і номер квартири. Якщо ви хочете швидко надіслати важливий конверт, уважно перевірте індекс. Листоноша спочатку дивиться на індекс і місто. Ви можете безпечно надіслати листівку або бандероль за цією адресою.

> *To send a letter or a large parcel, you need the correct address. First, you always write the postal code and your city. Then you need to write the street name, building number, and apartment number. If you want to quickly send an important envelope, carefully check the postal code. The mail carrier first looks at the postal code and the city. You can safely send a postcard or a small parcel to this address.*

When you write the recipient's name on an envelope or at the top of a personal letter, you must use the Dative case. The Dative case answers the important question **кому?** (to whom?). This grammatical rule applies to formal letters, casual postcards, and all types of packages. If you want someone to successfully receive your mail, you change their name and any adjectives describing them into the appropriate Dative case forms. This shows respect and clearly indicates the intended receiver of your message or gift.

На конверті завжди є детальна інформація про одержувача. Ми пишемо ім'я людини тільки у давальному відмінку. Наприклад, ви пишете довгий лист дорогому другові Андрію. Або ви хочете відправити теплий подарунок любій бабусі Олені. В офіційних листах ми часто пишемо шановному професорові Петренку. Коли людина має отримати ваш лист, її ім'я стоїть у формі давального відмінка.

> *On the envelope, there is always detailed information about the recipient. We write the person's name only in the Dative case. For example, you are writing a long letter to dear friend Andriy. Or you want to send a warm gift to dear grandmother Olena. In official letters, we often write to respected professor Petrenko. When a person is to receive your letter, their name stands in the form of the Dative case.*

:::info
**Grammar box** — When indicating the destination address on an envelope, always use **за адресою**. Avoid the incorrect phrase "по адресу", which is a direct calque from Russian. Correct Ukrainian requires the preposition **за** with the Instrumental case here.
:::

In Ukrainian, when you address someone using a phrase with multiple words, every single word in that phrase must match in the Dative case. This grammatical concept is called case agreement. The possessive pronoun, the descriptive adjective, the main noun, and the person's specific name must all share the correct Dative endings. Furthermore, for masculine nouns and names, Ukrainians very often prefer the specific endings **-ові** or **-еві** in the Dative case. These endings sound very natural, traditional, and distinctly Ukrainian.

Уявіть, що ви підписуєте дуже велику посилку на пошті. Усі слова у вашій фразі повинні мати форму давального відмінка. Наприклад: «моєму дорогому братові Михайлові». Або: «моїй найкращій подрузі Марії». Ви також можете написати: «нашому новому сусідові». Давальний відмінок гармонійно об'єднує всі ці слова.

> *Imagine that you are signing a very large parcel at the post office. All words in your phrase must have the form of the Dative case. For example: "to my dear brother Mykhailo". Or: "to my best friend Mariia". You can also write: "to our new neighbor". The Dative case harmoniously unites all these words.*

<!-- INJECT_ACTIVITY: quiz-dative-address-forms -->

The Dative case is also absolutely essential when you write the actual written message inside your greeting card or letter. Standard everyday greetings and basic phrases that express giving, sending, or writing all naturally require the Dative case for the recipient. Even if you are just dropping a very short and casual note to a family member, you will use these specific forms to establish a polite and warm connection. Let's look at a typical short message you might quickly write on a postcard directly from the post office branch.

Дорогій подрузі! Пишу тобі з сонячного Києва. Я сьогодні довго була на пошті. Купила дуже гарний конверт і нову марку. Посилаю тобі цей маленький подарунок і мій лист. Я хочу швидко отримати від тебе відповідь. Бажаю тобі гарного і теплого дня!

> *To a dear friend! I am writing to you from sunny Kyiv. I was at the post office for a long time today. I bought a very beautiful envelope and a new stamp. I am sending you this small gift and my letter. I want to quickly receive an answer from you. I wish you a good and warm day!*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: services-and-communication
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

**Level: A2 (Module 22/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

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
