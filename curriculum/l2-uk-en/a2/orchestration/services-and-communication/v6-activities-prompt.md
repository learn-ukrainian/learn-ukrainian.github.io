<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/services-and-communication.yaml` file for module **22: На пошті** (a2).

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
## На пошті: Базова лексика (At the Post Office: Essential Vocabulary)

У кожному українському місті чи селі є **пошта** *(post office)*. Національний поштовий оператор України — це відома компанія **«Укрпошта»** *(Ukrposhta)*. Люди часто використовують офіційну назву **відділення зв'язку** *(postal branch)* або просто коротке слово **відділення** *(branch)*. Коли ви заходите всередину, ви бачите різні зони для клієнтів. Там завжди є **каса** *(cash register)*, де люди платять за комунальні послуги. Також там є спеціальне **віконце** *(service window)* для роботи з людьми. Біля віконця працівники компанії допомагають клієнтам оформлювати документи. Українці часто приходять сюди, щоб купити свіжу пресу чи журнали. Але головна мета кожної пошти — це листи та пакунки.

На пошті ви можете побачити багато різних паперових предметів. Найпопулярніший предмет для спілкування — це звичайний **лист** *(letter)*. Це іменник чоловічого роду. Щоб відправити паперовий лист, вам спочатку потрібен **конверт** *(envelope, m)*. На цей конверт обов'язково треба наклеїти маленьку марку. Слово **марка** *(stamp, f)* — це іменник жіночого роду. Якщо ви хочете надіслати важкі речі або одяг, вам потрібна велика **посилка** *(parcel, f)*. Для маленьких предметів або цікавих книг часто використовують слово **бандероль** *(small parcel, f)*. Офіційний документ про оплату послуг — це **квитанція** *(receipt, f)*. Також іноді треба взяти ручку і заповнити спеціальний **бланк** *(form, m)*.

На пошті завжди працюють різні люди, які виконують свої спеціальні ролі. Людина, яка кожного дня приносить листи та газети додому, — це **листоноша** *(mail carrier)*. Цікаво, що це слово може позначати і чоловіка, і жінку. За скляним віконцем у відділенні працює **працівник пошти** *(postal worker)*. Людина, яка приносить свою посилку на пошту, — це **відправник** *(sender, m)*. А людина, яка дуже чекає на цю коробку вдома, — це **одержувач** *(recipient, m)*. Це слово надзвичайно важливе для вивчення української граматики. In Ukrainian grammar, the recipient always requires the Dative case. Ми завжди відправляємо новий лист (кому?) одержувачу. 

Щоб успішно комунікувати на пошті, вам треба знати правильні дієслова. Найголовніші українські слова — це **надіслати** *(to send)* або **відправити** *(to send)*. Вони мають абсолютно однакове значення. Протилежне слово до цих дієслів — це **отримати** *(to receive)*. Працівник може попросити вас: «Спочатку вам треба **заповнити бланк** *(to fill a form)*». Після цього процесу вам необхідно уважно **підписати конверт** *(to address an envelope)*. Там ви чітко пишете адресу відправника та адресу одержувача. Нарешті, на правий кут конверта треба **приклеїти марку** *(to stick a stamp)*. Після цих дій ваш лист чи бандероль повністю готові до подорожі.


## Надіслати листа: Діалоги на пошті (Sending a Letter: Dialogues at the Post Office)

The core grammatical construction for postal services is the verb **надіслати** *(to send)* or **відправити** *(to send)*, followed by what you are sending in the Accusative case, and who receives it in the Dative case. This structure is «надіслати (що?) (кому?)». The Dative case highlights the direct recipient of your action.
Наприклад, ви можете надіслати цікавого листа **другові** *(to a friend)*.
Також ви можете відправити важку посилку **сестрі** *(to a sister)*.
Українці часто кажуть у відділенні: «Я хочу надіслати гарний подарунок **мамі** *(to mom)*».
The recipient is the most important part of this postal transaction. Тому працівник пошти завжди уважно перевіряє адресу одержувача. The Dative case is absolutely essential whenever you transfer any physical object to another person. Без давального відмінка працівник не зрозуміє вашу мету.

Коли ви приходите на пошту, вам часто треба просто купити необхідні речі. Це звичайна і дуже коротка ситуація біля віконця. Вам треба правильно сказати, що ви хочете.
> — **Клієнт:** Доброго дня! Мені потрібні три марки на цей конверт.
> — **Працівник:** Доброго дня! Які саме марки ви хочете сьогодні купити? У нас є звичайні, а також гарні **святкові** *(festive)*.
> — **Клієнт:** Дайте мені, будь ласка, звичайні марки. І ще дайте мені два **міжнародні** *(international)* конверти.
> — **Працівник:** Добре, я зрозумів. Ось ваші нові марки та міжнародні конверти.
> — **Клієнт:** Дякую. **Скільки з мене?** *(How much do I owe?)*
> — **Працівник:** З вас рівно сорок п'ять **гривень** *(hryvnias)*. Ви платите карткою чи готівкою?
> — **Клієнт:** Я плачу готівкою. Ось, візьміть гроші. До побачення!
> — **Працівник:** Дякую, ось ваша решта. На все добре!

У цьому діалозі клієнт використовує прості фрази для швидкої покупки. Фраза «Скільки з мене?» є дуже природною, популярною та ввічливою в Україні. Її часто використовують у магазинах.

Відправити велику або важку річ за кордон — це завжди складніший процес. Вам треба поспілкуватися з працівником відділення і правильно заповнити офіційні документи.
> — **Клієнт:** Добрий день! Я хочу відправити цю бандероль за кордон.
> — **Працівник:** Добрий день! Куди саме ви відправляєте цю бандероль сьогодні?
> — **Клієнт:** Я відправляю це моєму старшому **братові** *(to a brother)* в далеку Канаду. Це його улюблена книга і невеликий сувенір.
> — **Працівник:** Зрозуміло. Тоді, будь ласка, швидко заповніть цей митний бланк. Пишіть адресу одержувача тільки англійською мовою.
> — **Клієнт:** Добре, я зараз усе напишу. Ось мій готовий бланк. Перевірте його, будь ласка.
> — **Працівник:** Дякую, тут усе правильно. Тепер я маю **зважити** *(to weigh)* вашу бандероль на вагах.
> — **Клієнт:** Скажіть, будь ласка, коли мій брат отримає цю посилку?
> — **Працівник:** Ваш брат отримає її приблизно через два або три **тижні** *(weeks)*.
> — **Клієнт:** Це дуже чудово! Дуже вам дякую за допомогу та інформацію!
> — **Працівник:** Нема за що. Звертайтеся ще. Гарного вам дня!

When you form the Dative case for people, pay close attention to the specific noun endings. For masculine nouns denoting people or animals, the most typical and preferred Dative endings are **-ові** or **-еві**. These endings are very common, traditional, and they sound completely natural in spoken Ukrainian.
In our postal examples, we successfully used the forms братові and другові. You simply add -ові to the hard consonant stem of the word.
For feminine nouns ending in -а or -я, the standard Dative ending is **-і**. This changes the final vowel of the noun.
Therefore, the word «сестра» easily becomes сестрі, and the word «мама» becomes мамі. The noun листоноша, which can be masculine or feminine, follows this exact same rule and becomes листоноші.
Завжди пам'ятайте про ці важливі закінчення! Ви постійно використовуєте їх, коли пишете адресу, відправляєте листа або даруєте подарунок. Це база українського спілкування!

<!-- INJECT_ACTIVITY: fill-in, Complete post office dialogue lines with correct dative forms -->


## Просити, дякувати, допомагати: Давальний у сфері послуг (Requesting, Thanking, Helping: Dative in Services)

Українці дуже ввічливі, коли спілкуються у сфері послуг. Вони часто використовують спеціальні дієслова для вираження поваги. Деякі дієслова завжди вимагають давального відмінка. Це дуже важливе правило української граматики.

In English, you might say "thank the worker" or "help the grandmother" using a direct object. In Ukrainian, these verbs demand the Dative case because you are directing your gratitude or assistance *to* someone. You are giving your thanks or giving your help.

Найпопулярніші дієслова тут — це **дякувати** *(to thank)*, **допомагати** *(to help)* та **вибачати** *(to forgive)*. Ви повинні казати «дякувати **працівникові**» *(to thank the worker)*, а не «працівника». Ви кажете «допомагати **бабусі**» *(to help the grandmother)*. Коли ви робите помилку на пошті, ви кажете працівникові: «**Вибачте** *(forgive)* мені, будь ласка». Також сюди належить дієслово **заважати** *(to bother/hinder)*. Ви можете почути: «Я не хочу заважати **людям** *(to the people)*». Ці слова роблять ваше спілкування дуже природним і правильним. Завжди пам'ятайте про закінчення давального відмінка після цих дієслів.

На пошті вам часто потрібна допомога працівників. Ви не завжди знаєте, як правильно заповнити форму. Ви не знаєте, куди йти у великому відділенні. When you need assistance, you combine an imperative verb with a pronoun in the Dative case. Це звучить як ввічливе прохання про допомогу.

For example, you can say: «Допоможіть мені заповнити цю адресу». Це дуже популярна фраза на пошті. Інша корисна фраза: «**Підкажіть** *(prompt/tell)* нам, де тут індекс». Слово «підказати» часто використовують, коли просять коротку інформацію або пораду. Якщо людина не розуміє процес, попросіть працівника: «**Поясніть** *(explain)* їй правила відправлення». Це показує вашу повагу та турботу. Ще одне важливе дієслово — **показувати** *(to show)*. Ви можете сказати: «**Покажіть** *(show)* йому нові поштові марки». Такі конструкції роблять діалог легким і приємним для всіх учасників.

Іноді вам потрібна допомога ваших сусідів або друзів. Уявіть, що у вас є дуже важка посилка. Ви хочете швидко відправити її за кордон. Ви просите сусіда допомогти вам донести її на пошту.

> — **Олег:** Привіт! Допоможи мені, будь ласка. Ця посилка дуже важка.
> — **Іван:** Привіт! Звичайно, я з радістю допоможу тобі. Кому ти відправляєш такі важкі речі?
> — **Олег:** Це великий подарунок **моїй** *(my)* бабусі та **твоєму** *(your)* синові.
> — **Іван:** Зрозуміло. Я **раджу** *(advise)* тобі перевірити вагу на пошті. Це може бути дуже дорого.
> — **Олег:** Дякую тобі за корисну пораду.

Дієслово «радити» також завжди вимагає давального відмінка. Ви можете сказати працівникові пошти: «Я радив йому надіслати це **авіапоштою** *(by airmail)*». Зверніть увагу на присвійні займенники. Вони також приймають форму давального відмінка: моїй бабусі, твоєму синові, нашому другові.

Using pronouns in the Dative case helps make your sentences short and precise. Займенники відіграють тут головну роль. Ви вже добре знаєте ці базові слова: **мені** *(to me)*, **тобі** *(to you)*, **йому** *(to him)*, **їй** *(to her)*. А також форми множини: **нам** *(to us)*, **вам** *(to you, pl/formal)*, **їм** *(to them)*.

На касі ви можете просто сказати: «Дайте мені квитанцію». Вам не треба довго пояснювати всю ситуацію. Ви також можете сказати: «Покажіть нам міжнародні конверти». Після візиту на пошту ви можете сказати друзям: «Я подякував їм за швидку допомогу». Ці маленькі слова роблять ваші речення швидкими та дуже зрозумілими. Вони ідеально підходять для сфери послуг. Там час завжди дуже важливий. Використовуйте ці займенники щодня, і ваша українська звучатиме дуже природно.

<!-- INJECT_ACTIVITY: match-up, Match service requests to appropriate responses -->
<!-- INJECT_ACTIVITY: group-sort, Sort phrases into categories — requesting (прохання), thanking (подяка), giving (давання) -->


## Написати адресу: Давальний у листуванні

Українська адреса має свої чіткі правила. Коли ви пишете адресу на конверті, ви завжди починаєте з імені. Ім'я людини обов'язково стоїть у давальному відмінку. In Ukrainian, the address answers the question "To whom are you sending this?" rather than just stating a location. Тому ми пишемо: Олександрові, Марії, Івану, Олені. Після імені ви пишете назву вулиці та номер будинку. Далі ви уважно вказуєте номер вашої квартири. Наступний рядок — це назва міста або невеликого села. Потім ви обов'язково пишете назву області. Наприкінці ви завжди вказуєте країну та поштовий **індекс** *(postal code)*. Це класична структура для державних поштових послуг. Правильний порядок рядків дуже важливий для пошти. Це допомагає працівникам швидко знайти правильну адресу. Листоноша завжди спочатку дивиться на індекс та місто, а потім шукає вашу вулицю.

Коли ви пишете офіційний лист або святкову листівку, ви часто додаєте прикметники до імені. Adjectives must agree with the noun and the name in gender, number, and case. The exact formula for the Dative case here is: Adjective + Noun + Name. Усі три слова у цій конструкції обов'язково стоять у давальному відмінку. Чоловічий рід має закінчення **-ому**: **дорогому** *(dear)* другові Андрію, **шановному** *(respected)* професорові Петренку. Жіночий рід має закінчення **-ій**: **любій** *(dear/beloved)* бабусі Олені, шановній колезі Анні. Ви ніколи не можете написати «дорогий другові» або «шановна директору». Усі слова у цій фразі повинні мати однакову форму давального відмінка. Це надзвичайно важливе правило української граматики. Такі класичні звернення показують вашу велику повагу до іншої людини. Вони роблять ваш лист дуже ввічливим і приємним для читання.

На пошті ви також можете надіслати гарну **листівку** *(postcard)* своїм родичам або друзям. Коротке повідомлення на листівці також часто потребує знання давального відмінка. Використовуйте стандартні фрази для початку та кінця вашого тексту. Ви можете написати: «Пишу тобі з сонячного Києва» або «Надсилаю вам вітання зі старого Львова». Ці фрази є дуже популярними серед українців. У кінці листа люди часто пишуть гарні побажання. The verb "to wish" in Ukrainian always takes the Dative case for the person you are wishing something to. Ми традиційно кажемо: «Бажаю тобі великого успіху» або «Бажаємо вам міцного здоров'я». Ви можете написати близьким родичам: «Моєму дорогому братові Михайлові! Бажаю тобі веселого свята». Або ви пишете вашим колегам по роботі: «Шановному панові директору! Надсилаю вам нові ділові документи». Ці короткі тексти дуже легко запам'ятати і писати. Вони роблять ваше щоденне спілкування теплим.

<!-- INJECT_ACTIVITY: quiz, Choose the correct dative address form from multiple options -->

Сьогодні багато людей постійно використовують приватні поштові сервіси. Найпопулярніший сервіс в Україні — це компанія «Нова Пошта». Ця сучасна компанія змінила деякі старі поштові слова. Наприклад, замість слова «квитанція» вони використовують слово «**накладна**» *(waybill)*. Ви також отримуєте зручний **номер відстеження** *(tracking number)* у мобільному додатку. Але базова граматика залишається незмінною. У додатку ви завжди бачите слова «одержувач» та «відправник». Система запитує вас: «Кому ви надсилаєте цю посилку?». І ви знову використовуєте давальний відмінок для імені та прізвища. Сучасні цифрові технології змінюють процес відправлення, але не змінюють правила української мови. Давальний відмінок завжди надійно допомагає посилці знайти правильну людину.


## Підсумок

Ось ми і закінчили вивчати тему про пошту. Тепер ви знаєте, як працює **відділення** *(post office branch)* в Україні. Ви також добре розумієте, як правильно використовувати давальний відмінок у сфері послуг. Давайте перевіримо ваші нові знання. Спробуйте відповісти на ці важливі запитання.

Спочатку згадайте граматику. Яке закінчення мають іменники чоловічого роду в давальному відмінку? Наприклад, як зміняться слова «брат», «батько» або «директор», коли ви надсилаєте їм посилку? 

Потім подумайте про листування. Як правильно звернутися до жінки у вашому листі? Ви напишете «любій мамі» чи «люба мамі»? Чому прикметник і іменник повинні мати однакову форму давального відмінка?

Далі згадайте питальні слова. Яке питання ми ставимо, щоб дізнатися адресу одержувача? Ми запитуємо «Кому?» чи ми запитуємо «Де?»? Чому людина — це не місце?

Нарешті, давайте повторимо дієслова. Назвіть три дієслова, які завжди вимагають давального відмінка у сфері послуг. Згадайте слова, які означають допомогу або передачу речей.

Якщо ви можете легко відповісти на всі ці запитання, ви чудово знаєте матеріал. Тепер ви готові самостійно надіслати справжнього листа або велику бандероль з України!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: services-and-communication
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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

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
