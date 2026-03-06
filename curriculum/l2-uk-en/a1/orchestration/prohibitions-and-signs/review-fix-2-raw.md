✅ Message sent to Gemini (ID: 21313) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #21313...
📨 Message #21313
   From: gemini → To: gemini
   Type: query
   Task: prohibitions-and-signs-review-fix-2
   Time: 2026-03-06T08:05:52.070607+00:00

============================================================

# Gemini Review Fix: Targeted Repair via FIND/REPLACE

> **You are an expert Ukrainian language editor applying targeted fixes.**
> You have NO tools — output FIND/REPLACE pairs only.
> The build system will apply your fixes programmatically.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original.
- **PRESERVE the author's intent.** Rewrite poorly explained content to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your fixes should read like the original author wrote them on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information).

---

## Fix Plan (from review)

## Critical Issues Found

### Issue 1: Massive Linguistic Hallucination («роботу» means "opened")
**Location**: Section `На вулиці — On the street`, Subsection `Відчинено чи зачинено: точність слів`, and `Підсумок`
**Problem**: The LLM catastrophically confused the words «відкрито» (opened) and «робота» (work). It claims that the word "роботу" is used incorrectly by people to mean that a door is opened. 
- `Ми не кажемо «роботу» про двері.`
- `Many people mistakenly use the incorrect words «роботу» (opened up/discovered) and «закрито»...`
- `Яке точне українське слово ми маємо завжди використовувати замість русизму «роботу»...`
This is completely fabricated. The common error is using «відкрито» instead of «відчинено».
**Fix**: Replace all instances of «роботу» in this context with «відкрито».

### Issue 2: Direct English Calques
**Location**: Throughout the text.
**Problem**: The text frequently translates English idioms directly into Ukrainian, resulting in unnatural phrasing. 
- `Знак не говорить до людини.` (The sign does not speak to a person) - Unnatural.
- `Ви можете зберегти гроші.` (You can save money) - In Ukrainian, "зберегти" means to keep safe. For discounts, it is "заощадити" or "зекономити".
- `Бізнес хоче мати увагу.` (Business wants to have attention) - Unnatural verb choice.
**Fix**: Use natural Ukrainian equivalents (e.g., «звертається до», «заощадити гроші», «привернути увагу»).

### Issue 3: Incorrect Dative Construction
**Location**: Section `Розклади та оголошення` and `Підсумок`
**Problem**: The text uses the preposition «для» where a simple dative pronoun is required.
- `Ці навички дають для вас спокій.` 
- `Наша мета — дати для вас впевненість.`
**Fix**: Remove "для" and use the dative pronoun directly: `дають вам спокій`, `дати вам впевненість`.

### Issue 4: Confusing / Robotic LLM Phrasing
**Location**: Section `Попередження — Warnings`, Subsection `Складні прості фрази`
**Problem**: The header «Складні прості фрази» is an oxymoron that makes no sense. The explanation is also robotic: `Це слово і слово. Вони стоять поруч.` Additionally, there is a repetition typo: `Великий великий простір має іншу назву.`
**Fix**: Rename the header to «Фрази без дієслів», fix the robotic text to «Це два слова», and remove the duplicate word.

---

## Ukrainian Language Issues

- `головні слова для орієнтації`: "Орієнтація" is less natural here than "орієнтування" (navigating/finding one's way).
- `Вона дає ввічливе спілкування`: Unnatural phrasing ("It gives polite communication"). Should be "Це допомагає спілкуватися ввічливо."
- `Вони стоять біля електрики`: "Біля електрики" is a sloppy translation of "near electricity". It should be "біля електричних приладів" (near electrical devices).

---

## Fix Plan to Reach PASS

1. **Eradicate the "роботу" hallucination:** Systematically replace "роботу" with "відкрито" in the prose, the myth-buster callout, and the review questions.
2. **Fix Calques:** Change "зберегти гроші" to "заощадити", "мати увагу" to "привернути увагу", and fix the "говорить до" constructions.
3. **Fix Prepositions:** Remove "для" in "дати для вас".
4. **Smooth out LLM tone:** Rename the "Складні прості фрази" header, fix the "слово і слово" robotic sentence, and fix the "Великий великий" typo.
5. **Vocabulary context:** Ensure "орієнтування" is used instead of "орієнтації".

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 3746/1200 (raw: 4041) | pedagogy: 3 violations
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/prohibitions-and-signs-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/prohibitions-and-signs.md`

```markdown
<!-- SCOPE
Covers: Reading public signs, infinitive prohibitions, warning exclamations, schedules, urban navigation
Not covered:
  - Buying transport tickets → a1-56
Related: a1-54 (Checkpoint Communication), a1-52 (Travel and Transport)
-->

# Prohibitions and Signs

> **Чому це важливо?**
>
> Нове місто має багато знаків. Ви бачите знаки щодня. Читати знаки дуже важливо. Це ваш комфорт. Це ваша безпека. Ви мусите розуміти правила. Українські міста мають свої правила. Вивіски мають іншу граматику. Сьогодні ми вивчаємо цю тему.
>
> Navigating in a new city is always a complex and interesting task. You see a lot of visual information around you every day. Reading signs is critically important for your personal comfort. You must clearly understand what is allowed and what is strictly forbidden. This is a matter not only of knowing the language but also of your safety. Ukrainian cities have their own very specific visual culture. We use special grammatical constructions on signs. Therefore, today we pay separate and deep attention to this topic.

## Заборони — Prohibitions

### Інфінітив на вивісках
Офіційні заборони мають правила. Вони використовують інфінітив. Це нейтральний стиль. Знак не звертається до конкретної людини. Знак дає загальне правило. Інфінітив звучить дуже офіційно. Типові заборони — не курити, не входити. Інша заборона — не торкатися. Ви бачите ці слова часто. Парки та музеї мають такі знаки. Вони є частиною міста.



*   «У цьому парку не курити!»
*   «Службове приміщення: не входити!»
*   «Експонати руками не торкатися!»

These examples show how direct and uncompromising the infinitive can be. When you read such a sign, you instantly understand that there are no exceptions to this rule.

### Особисті команди чи загальні правила
Українська мова має дві різні ситуації. Перша — це команди. Друга — це загальні правила. Ми говоримо прямо і беремо наказовий спосіб. Ми пишемо правило і беремо інфінітив. Порівняйте ці два підходи. Заборона має інфінітив. Це сувора табличка. Наказовий спосіб має емоції. Мати так каже дитині. Ця різниця дуже важлива. Вона допомагає спілкуватися ввічливо.



| Ситуація | Граматика | Приклад |
| :--- | :--- | :--- |
| Напис на скляних дверях | Інфінітив (Infinitive) | Не входити! |
| Розмова з близьким другом | Наказовий спосіб (Imperative) | Не заходь! |
| Дерев'яна табличка в лісі | Інфінітив (Infinitive) | Не смітити! |
| Прохання до свого колеги | Наказовий спосіб (Imperative) | Не сміти! |

Using the imperative mood on a public sign would look too aggressive and inappropriately familiar. Conversely, using the infinitive in a personal, face-to-face conversation would sound like the mechanical speech of a robot. Always match your grammar to the specific social context.

### Базова навігація: Вхід і Вихід
Ви маєте знати головні слова для орієнтування. Без цих слів ви можете загубитися. Одне слово показує шлях всередину. Інше слово показує шлях на вулицю. Ви часто бачите червоний знак. Це сувора заборона. Ви не можете йти далі. Такі знаки висять на дверях. Розуміння цих слів допомагає всім.

You must learn to automatically recognize key words for spatial orientation. Without these basic words, you can very easily get lost in a large building. One important word shows exactly where your route inside begins. Another word shows the safe path to the street. Very often you will see a red warning sign about a strict prohibition. It means that you categorically cannot go any further. Such signs usually hang on doors for staff or on technical warehouses. Understanding these short words helps avoid awkward life situations. The core vocabulary here is **вхі́д** (entrance) and **ви́хід** (exit). The strict prohibition phrase is **вхі́д заборо́нено** (entrance forbidden).

*   «Головний вхід знаходиться відразу праворуч від першої каси.»
*   «Аварійний вихід має бути завжди абсолютно вільним для людей.»
*   «Службова територія охорони: стороннім вхід заборонено!»

> [!tip] Життєво важливий знак
> If you are ever confused inside a massive shopping mall or a hospital, look up at the ceiling. In Ukraine, standard safety regulations require illuminated green signs with a running person icon. These signs always have the word **ВИХІД** written in bold, easily readable letters. Memorize the visual shape of this word—it is essential for your personal safety in emergencies.

## Попередження — Warnings

Місто може мати небезпеку. Небезпека буває раптова. Ви не маєте часу читати довгі тексти. Потрібна швидка реакція. Українська мова має короткі слова. Вони працюють як візуальні сирени. Водії та пішоходи бачать їх. Ви маєте знати ці сигнали. Це ваш базовий словник. Його треба знати добре.



### Короткі попередження
Іноді ми маємо привернути увагу. Ми використовуємо короткі слова. Вони працюють як сигнали тривоги. Їх пишуть великими літерами. Вони мають червоний знак оклику. Вони звучать дуже чітко. Вони рятують життя на дорогах. Ви не маєте часу на аналіз. Ви маєте реагувати швидко.

Sometimes we need to instantly grab another person's attention. For this, we use short exclamatory words instead of full sentences. They function as completely independent alarm signals. Usually, they are written in capital letters and necessarily have a red exclamation mark at the end. They sound extremely clear, very loud, and maximally imperative. These short adjectives and adverbs save lives on fast roads and large construction sites. You should not stop to analyze their grammatical structure. You must react to them absolutely instinctively and quickly. The most critical words are **ува́га** (attention), **обере́жно** (carefully/caution), and **небезпе́чно** (dangerous).

— Увага! Цей швидкий потяг відправляється з першої колії.
— Обережно! Скляні двері автоматично зачиняються.
— Небезпечно! Ніколи не підходьте близько до краю платформи.

These exclamations are often broadcast over public loudspeakers at train stations or printed in bold red font on warning triangles. They command immediate focus and action.

### Фрази без дієслів
Багато знаків не мають дієслів. Це прості фрази. Це два слова. Вони стоять поруч. Формат дає максимум інформації. Ви часто бачите яскраві знаки. Вони стоять біля електричних приладів.

Many warning signs do not contain any verbs at all. They are built as simple but extremely effective noun phrases. This is a short combination of a descriptive adjective and its corresponding noun. The adjective usually stands directly before the noun. It strictly agrees with it in gender, number, and case. This concise format allows conveying the maximum amount of important information with a minimum number of short words. You will very often see such bright signs during the cleaning of premises or near electrical transformers. A common example is the yellow sign **мо́кра підло́га** (wet floor). Another critically important sign is **висо́ка напру́га** (high voltage).

*   **Обережно, мокра підлога!**
*   **Стій! Висока напруга!**
*   **Увага! Глибока яма.**

> [!warning] Пріоритет вашої безпеки
> Warning signs explicitly protect your personal safety and health. These are high-priority vocabulary items that you absolutely must not ignore. If you see a yellow plastic triangle or a bright red metal circle with phrases like **висока напруга** or words like **обережно**, pay immediate attention to your physical surroundings. Never treat these signs as mere suggestions.

### Київське метро: «Не притулятися»
Велике місто має візуальні символи. Київ має такий символ. Це фраза з метро. Сині вагони мають напис. Це класичний заперечний інфінітив. Фраза має чітке правило. Пасажири не можуть спиратися на двері. Вона лунає щодня тисячі разів. Це частина фольклору.

Every large historical city has its own unique visual symbols. In the capital of Ukraine, one short phrase from the city metropolitan has become such an unusual symbol. On the glass doors of every blue car, there is a famous sign. It is an absolutely classic example of a Ukrainian negative infinitive. This historical phrase means that passengers are strictly forbidden to lean their backs against the doors during the fast movement of the train. It sounds from the loudspeakers thousands of times a day and has become an integral part of modern urban folklore. The iconic phrase is «Не притулятися» — Do not lean.

*   «Обережно, двері зачиняються. Не притулятися!»
*   «Досвідчені київські пасажири добре знають головне правило: до дверей не притулятися.»

> [!culture] Сучасний символ міста
> The specific phrase «Не притулятися» is so deeply iconic that you can easily find it printed on modern t-shirts, stylish tote bags, and tourist souvenirs in Kyiv. It perfectly illustrates how a very simple grammatical structure—the negative infinitive prohibition—can gracefully move beyond formal rules and become deeply embedded in modern Ukrainian pop culture.

## Розклади та оголошення — Schedules and notices

Життя міста має графіки. Ви маєте знати час. Магазини та аптеки мають розклад. Ви не хочете втрачати час. Українські заклади мають свої години роботи. Вони можуть бути інші. Ви маєте читати яскраві оголошення. Вони дають інформацію про ціни. Цей розділ вчить орієнтуватися у часі.



### Години роботи та перерва
Ви плануєте свій день. Ви маєте знати словник. Головна фраза — години роботи. Ви маєте знати неробочий день. Ви також маєте пам'ятати про перерву. Вона буває вдень. Маленькі магазини мають цей графік. Розуміння дозволить приходити вчасно.

For comfortable planning of your day, you need a specific vocabulary. The main basic phrase for this is the operating hours of the chosen establishment. You also absolutely need to know the word that clearly denotes a non-working day of the week. And, of course, you must always remember the traditional break, which most often happens during the day. Small local shops and government institutions strictly adhere to this old schedule. Understanding these three key concepts will allow you to always arrive on time. The essential terms are **годи́ни робо́ти** (operating hours), **вихі́дний** (day off), and **пере́рва** (break).

*   1. «Підкажіть, будь ласка. Які у вас години роботи у цей вівторок?»
*   2. «Завтра неділя, тому це наш офіційний вихідний день.»
*   3. «Наш маленький магазин зараз не працює, у нас почалася перерва.»

> [!fact] Культура обідньої перерви
> The concept of a scheduled **перерва** (break) remains highly culturally significant in Ukraine. While massive supermarkets and modern corporate chains work continuously, smaller neighborhood shops, post offices, and local government buildings often close their doors completely for one hour, typically from 13:00 to 14:00. This is critical survival knowledge for efficiently running daily errands.

### Формат часу: «з... до...»
Українці часто кажуть про час. Ми беремо прийменник «з». Це початок. Потім ми беремо прийменник «до». Це кінець. Ви можете просто запам'ятати цю форму. Це дуже зручний вираз. Це практичний підхід.

Ukrainians constantly use one specific grammatical construction to indicate time duration. We always take the preposition «з» (from) to accurately indicate the start of an action. Then we take the preposition «до» (to) to indicate its logical end. After these two prepositions, nouns and numerals always stand in the genitive case. But for your basic level, you can simply memorize this form as one indivisible fixed expression. This is an extremely convenient and incredibly practical approach. The standard format looks like **з 9:00 до 18:00** (from 9:00 to 18:00).

— Скажіть. Коли ви зазвичай працюєте?
— Ми відкриті з дев'ятої ранку до шостої вечора щодня.
— Тоді у вас офіційний обід?
— Наша перерва завжди триває з першої до другої години.
— Дякую, тоді я точно прийду до сьомої вечора.

This exact time pattern is absolutely universal across the country. You will see it printed on almost every commercial door. It is the absolute standard way to express a time range in both written schedules and spontaneous spoken Ukrainian conversation.

### Оголошення та акції
Бізнес хоче привернути увагу. Вітрини мають яскраві плакати. Ви побачите там спеціальні слова. Покупці люблять вигідні пропозиції. Це означає зменшення ціни. Ви можете заощадити гроші. Це корисно під час покупок.

Every business actively tries to attract maximum attention of its potential clients. For this, large and very bright posters with text often hang on glass shop windows. You are guaranteed to see a special word for any important information there. For ordinary buyers, the most attractive words are those about beneficial offers and substantial price reductions. They perfectly help to save your own money during daily shopping in a large supermarket. You must instantly recognize the words **оголо́шення** (announcement), **а́кція** (sale/promotion), and **зни́жка** (discount).

*   «Уважно прочитайте це нове офіційне оголошення на інформаційній дошці.»
*   «Сьогодні в нашому місцевому супермаркеті проходить дійсно велика акція.»
*   «Вони зараз пропонують неймовірну знижку п'ятдесят відсотків на весь зимовий одяг.»

> [!context] Справжнє значення акції
> The word **акція** looks like the English word "action", but it is a notorious "false friend" in this specific context. In retail and commerce, it specifically means a special offer, a promotional campaign, or a big sale. If you see a yellow or bright red price tag prominently featuring the bold word **акція**, it means that specific item is currently sold at a heavily reduced promotional price.

### Розклад руху транспорту
Ви маєте читати табло. Вокзали мають електронні табло. Головне слово — це графік руху. Ви шукаєте час відправлення. Ви шукаєте час прибуття. Ви перевіряєте цифри вашого напрямку. Ці навички дають вам спокій. Ви ніколи не загубитеся.

During long journeys across the country, you must be able to correctly read the electronic boards at noisy train stations. The most important key word for a successful and calm trip is the timetable of fast trains or buses. In this long digital list, you constantly look for the time when the transport leaves the station and the time when it arrives at the place. You must also strictly and very carefully check the numbers of your specific direction. These skills guarantee that you will never get lost. The critical words are **ро́зклад** (schedule/timetable), **відпра́влення** (departure), **прибуття́** (arrival), and **но́мер маршру́ту** (route number).

*   «Скажіть, де саме можна подивитися актуальний розклад швидкісних поїздів до Львова?»
*   «Точний час відправлення нашого жовтого автобуса — сімнадцята година рівно.»
*   «Цей синій номер маршруту точно їде прямо до історичного центру?»

These specific transport words connect directly to the travel vocabulary you learned previously. Reading a complex train or bus timetable perfectly combines your practical knowledge of numbers, specific time formats, and essential transport terms into one highly useful real-world skill.

## На вулиці — On the street

Ви маєте швидко читати таблички. Міста мають свою систему назв. Ви маєте знати прості слова. Це ваша фізична безпека. Цей розділ має важливі нюанси. Це слова про двері та магазини. Ми вивчаємо правильні норми.



### Вулиці, площі, провулки
Україна має три типи доріг. Базове слово — це звичайна дорога. Великий відкритий простір має іншу назву. Вузька дорога має третє слово. Таблички мають скорочені слова. Це економить місце на знаках.

In Ukraine, there are three main types of urban roads that you will often see on paper maps. The basic word denotes a regular city road with residential houses. A large and wide open space, often right in the historical city center, has a different name. A short and narrow road that connects larger roads is called by a third special word. On real street signs and plaques, these long words are almost always written in an abbreviated form to save space. You must thoroughly learn the words **ву́лиця** (street), **пло́ща** (square), and **прову́лок** (lane).

| Повне слово | Скорочення | Типовий приклад |
| :--- | :--- | :--- |
| вулиця | вул. | вул. Хрещатик |
| площа | пл. | пл. Ринок |
| провулок | пров. | пров. Музейний |

Recognizing these standard abbreviations is absolutely crucial for daily navigation. When you use a digital map application on your phone or read a printed business card, the address will almost certainly be written using these specific short forms rather than the fully spelled-out words.

### Транспорт та пішоходи
Ви маєте знати слова дороги. Це ваша безпека. Одне слово розуміють всі водії. Інша фраза означає безпечний перехід. Місце очікування транспорту має назву. Метро також має спеціальне слово. Воно дозволяє змінити лінію.

For your personal safety, you must flawlessly know key road terminology. One popular English word is understood by all drivers without any translation. But you critically need to know the long Ukrainian phrase for a safe road crossing. A special place for the long wait for city transport also has its own name. And in a massive metropolitan, you constantly look for the word that allows changing the line deep underground. The essential vocabulary includes **стоп** (stop), **пішохі́дний перехі́д** (pedestrian crossing), **зупи́нка** (stop), and **перехі́д** (crossing/transfer).

*   «Кожен водій обов'язково зупинився перед великим червоним знаком "Стоп".»
*   «Ми завжди безпечно переходимо широку дорогу лише через пішохідний перехід.»
*   «Це остання кінцева зупинка нашого старого трамвая, всім пасажирам треба вийти.»
*   «На жаль, довгий підземний перехід на синю лінію метро зараз не працює.»

These important terms help you move safely through very heavy urban traffic and successfully navigate complex underground transport systems. Always remember to cross the street only exactly where you see the painted pedestrian crossing sign on the asphalt.

### Відчинено чи зачинено: точність слів
Українська мова має точні слова. Ми говоримо про графік роботи магазину. Ми вживаємо конкретні слова. Ви можете зайти всередину. Цей статус має спеціальне слово. Вхід зараз не працює. Цей статус має інше слово. Це єдина правильна норма. Ми не кажемо «відкрито» про двері.

The Ukrainian language is extremely beautiful and perfectly precise in its daily phrasing. When we talk about the operating schedule of a shop or the physical state of a door, we use very specific words. If you can freely go inside, the status of this room is denoted by a special word. If the entrance is temporarily unavailable to you, then the status is denoted by another word. This is the only correct, absolutely pure literary norm. We never use words that mean discovering something new to describe regular wooden doors. The strictly correct words are **відчи́нено** (open) and **зачи́нено** (closed).

*   «Вибачте, але наш новий офіс зараз зачинено, у нас почалася велика обідня перерва.»
*   «Ці важкі дерев'яні двері відчинено, будь ласка, сміливо заходьте всередину.»
*   «Сьогодні центральний державний банк повністю зачинено на офіційний вихідний.»

> [!myth-buster] Деколонізація словника
> Many people mistakenly use the incorrect words «відкрито» (opened up/discovered) and «закрито» (covered/concluded) for shops and doors. This is a direct consequence of long-term Russian linguistic interference, commonly known as Surzhyk. In proper Ukrainian, you "open" (відкривати) a fascinating book, a brand-new continent, or your deep feelings. But physical barriers, such as wooden doors, glass windows, and commercial shops, are strictly **відчинені** (opened) or **зачинені** (closed). Consistently using the correct terminology demonstrates your deep respect for the authenticity of the language.

## Підсумок і Практика — Summary and Practice

Час застосувати ваші знання. Наша мета — дати вам впевненість. Ми беремо кілька типових ситуацій. Ви зустрінете їх в Україні. Ви маєте аналізувати інформацію швидко. Ви маєте розуміти знаки без словника. Це крок до мовної самостійності.



### Читаємо вивіски
Уявіть прогулянку Києвом. Ви гуляєте центром міста. Навколо вас багато інформації. Вікна мають яскраві написи. Ви маєте миттєво розуміти сенс. Ви маєте знати граматику. Прочитайте ці чотири сценарії. Зробіть правильні висновки.

Imagine that you have come to sunny Kyiv for the first time and are slowly walking through the historical center of this beautiful city. Around you is a multitude of bright visual information on walls and large windows. You must be able to instantly understand the deep meaning of these signs and their specific grammatical structure. Read these four typical urban scenarios very carefully and draw your own correct conclusions.

1.  **Ситуація перша.** Ви біля офісу. Двері мають напис «Не входити!». Це типовий інфінітив. Це сувора заборона. Ви не маєте права заходити.
2.  **Ситуація друга.** Ви бачите жовту табличку. Напис каже «Обережно, мокра підлога!». Це фраза про небезпеку. Ви йдете дуже повільно.
3.  **Ситуація третя.** Ці двері мають знак. Напис каже «Вхід заборонено». Це найвища заборона. Це небезпечна територія.
4.  **Ситуація четверта.** Двері кав'ярні мають напис. Напис каже «Відчинено». Ви можете заходити всередину. Ви можете замовляти каву.

Scenario one. You stand before an absolutely new office. On the glass doors is a red sign: «Не входити!» (Do not enter!). This is a typical Ukrainian infinitive. It means a strict and categorical prohibition. You have no right to go in there. Scenario two. You see a yellow plastic plaque on the floor: «Обережно, мокра підлога!». This is a classic noun phrase with an important warning. You must walk there very slowly and maximally carefully. Scenario three. On the metal doors of a large warehouse hangs a sign: «Вхід заборонено» — Entrance forbidden. This means the highest level of prohibition for people. This is a private or very dangerous territory. Scenario four. On the wooden doors of a small coffee shop is beautifully written: «Відчинено» (Open). This means you can boldly go inside and order your favorite coffee.

### Аналізуємо розклад
Розглянемо графік роботи аптеки. Ви стоїте перед табличкою. Ви маєте купити ліки. Прочитайте цей текст. Знайдіть правильні відповіді. Ця вправа тренує вас. Ви краще орієнтуєтеся у часі.

Let's examine in detail and carefully the real operating schedule of a typical Ukrainian pharmacy in a residential area. You are standing in front of a white plastic plaque on the entrance doors. You urgently need to buy important medicine for your sick friend. Read this short informative text and quickly find the correct answers to three logical questions. This very simple exercise perfectly trains your ability to efficiently navigate in urban time.

**Години роботи:**
Понеділок - П'ятниця: з 8:00 до 20:00
Субота: з 9:00 до 15:00
Неділя: вихідний
Перерва: з 13:00 до 14:00

*   Питання: **Чи працює ця конкретна аптека в неділю?**
    Відповідь: Ні, на білій табличці чітко написано слово «вихідний».
*   Питання: **Чи можна успішно купити ліки о тринадцятій тридцять у вівторок?**
    Відповідь: Ні, у цей конкретний час у всіх працівників триває «перерва».
*   Питання: **О котрій годині ця аптека відчиняється у звичайний понеділок?**
    Відповідь: Вона починає повноцінно працювати рівно «з 8:00».

By regularly analyzing such simple informational texts, you prepare yourself for a comfortable and totally independent life in Ukraine. You no longer need to constantly guess if a specific place is currently open or completely closed.

### Інфінітив проти наказового способу
Наприкінці уроку ми закріпимо правило. Різниця між формальним та неформальним стилем важлива. Іноземці часто роблять помилку. Вони перекладають команди буквально. Вони беруть наказовий спосіб для вивісок. Але українська мова вимагає формального підходу.

At the very end of our theoretical lesson, we must reliably and forever consolidate the most important grammatical rule. The contextual difference between formal and informal registers of communication is absolutely key to your success. Foreigners very often make this typical and unfortunate mistake. They try to translate their commands directly using the imperative mood on printed signs. But the Ukrainian language always strictly requires a much more formal approach.

| Англійський оригінал | Офіційні знаки | Пряма розмова |
| :--- | :--- | :--- |
| Don't enter the room! | Не входити! | Не заходь! |
| Don't smoke here! | Не курити! | Не кури! |
| Don't touch this! | Не торкатися! | Не чіпай! |

Please memorize this vital grammatical distinction forever. Always use the neutral and impersonal infinitive when you are reading or writing official public rules. Only use the emotional imperative mood when you are speaking directly to a known person in a private conversation.

---

### Підсумок

Сьогодні ви вивчили читання вивісок. Ви знаєте про інфінітив. Ви знаєте короткі слова про небезпеку. Ви розумієте графік роботи. Ви можете знаходити площу на карті. Ви знаєте слова для відкритих дверей. Ці знання роблять життя безпечним. Ви можете орієнтуватися вільно.

Today you successfully and deeply learned how to correctly read and understand Ukrainian city signs. Now you perfectly know that official public prohibitions always use the impersonal infinitive. You can instantly recognize short exclamatory words about real danger on the street. You understand very well how to quickly read a business operating schedule and find the needed city square on a map. You also firmly learned the strictly correct literary words for open and closed doors. This fundamental knowledge makes your daily life in a large city safe and maximally comfortable. You can now freely navigate without any outside help.

**Перевірте себе:**
1. Яку саме граматичну форму дієслова ми обов'язково використовуємо на офіційних знаках заборони?
2. Які три короткі слова-вигуки ми найчастіше використовуємо для миттєвого попередження про небезпеку?
3. Що конкретно означає стандартна фраза «перерва з 13:00 до 14:00» на магазині?
4. Яке точне українське слово ми маємо завжди використовувати замість русизму «відкрито», коли говоримо про двері?
5. Яке стандартне скорочення постійно використовується для слова «вулиця» на міських адресних табличках?
6. Чим граматично та ситуативно відрізняється суворе правило «Не торкатися!» від дружнього прохання «Не чіпай!»?

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/prohibitions-and-signs.yaml`

```yaml
- type: match-up
  title: "Match the Sign to Its Meaning"
  instruction: "Connect each Ukrainian sign with its correct English translation."
  pairs:
    - left: "Не курити!"
      right: "No smoking!"
    - left: "Не входити!"
      right: "Do not enter!"
    - left: "Не торкатися!"
      right: "Do not touch!"
    - left: "Вхід заборонено!"
      right: "Entrance forbidden!"
    - left: "Обережно!"
      right: "Careful!"
    - left: "Увага!"
      right: "Attention!"
    - left: "Небезпечно!"
      right: "Dangerous!"
    - left: "Мокра підлога"
      right: "Wet floor"
    - left: "Висока напруга"
      right: "High voltage"
    - left: "Пішохідний перехід"
      right: "Pedestrian crossing"
    - left: "Зачинено"
      right: "Closed"
    - left: "Відчинено"
      right: "Open"
- type: quiz
  title: "Sign Comprehension"
  instruction: "Choose the correct answer for each question about signs."
  items:
    - question: "What does the sign 'Зачинено' mean?"
      options:
        - text: "Closed"
          correct: true
        - text: "Open"
          correct: false
        - text: "Entrance"
          correct: false
        - text: "Exit"
          correct: false
    - question: "What does the sign 'Відчинено' mean?"
      options:
        - text: "Open"
          correct: true
        - text: "Closed"
          correct: false
        - text: "Push"
          correct: false
        - text: "Pull"
          correct: false
    - question: "Which sign means 'No smoking!'?"
      options:
        - text: "Не курити!"
          correct: true
        - text: "Не входити!"
          correct: false
        - text: "Не торкатися!"
          correct: false
        - text: "Вхід заборонено!"
          correct: false
    - question: "How do you say 'Entrance forbidden!'?"
      options:
        - text: "Вхід заборонено!"
          correct: true
        - text: "Вихід заборонено!"
          correct: false
        - text: "Не входити!"
          correct: false
        - text: "Не курити!"
          correct: false
    - question: "Which Ukrainian word means 'Attention!'?"
      options:
        - text: "Увага!"
          correct: true
        - text: "Обережно!"
          correct: false
        - text: "Небезпечно!"
          correct: false
        - text: "Стоп!"
          correct: false
    - question: "Which phrase translates to 'Wet floor'?"
      options:
        - text: "Мокра підлога"
          correct: true
        - text: "Висока напруга"
          correct: false
        - text: "Пішохідний перехід"
          correct: false
        - text: "Години роботи"
          correct: false
    - question: "What does 'Вихідний' mean on a store's schedule?"
      options:
        - text: "Day off / Closed day"
          correct: true
        - text: "Operating hours"
          correct: false
        - text: "Lunch break"
          correct: false
        - text: "Discount"
          correct: false
    - question: "What does the word 'Перерва' mean?"
      options:
        - text: "Break / Lunch break"
          correct: true
        - text: "Schedule"
          correct: false
        - text: "Departure"
          correct: false
        - text: "Arrival"
          correct: false
    - question: "Which abbreviation is used for 'вулиця' (street)?"
      options:
        - text: "вул."
          correct: true
        - text: "пл."
          correct: false
        - text: "пров."
          correct: false
        - text: "буд."
          correct: false
    - question: "Which sign indicates a pedestrian crossing?"
      options:
        - text: "Пішохідний перехід"
          correct: true
        - text: "Зупинка"
          correct: false
        - text: "Підземний перехід"
          correct: false
        - text: "Стоп"
          correct: false
- type: true-false
  title: "True or False: Schedules and Signs"
  instruction: "Decide if the statements are true or false based on the lesson."
  items:
    - statement: "The sign 'Відчинено' means that a store is closed."
      correct: false
      explanation: "It means open. 'Зачинено' means closed."
    - statement: "The word 'Вхід' means 'Entrance'."
      correct: true
    - statement: "A 'перерва' is a designated break when small shops might close."
      correct: true
    - statement: "'Обережно' is a warning word that means 'Dangerous!'."
      correct: false
      explanation: "It means Careful or Caution. 'Небезпечно' means Dangerous."
    - statement: "The abbreviation 'пл.' stands for 'площа' (square)."
      correct: true
    - statement: "'Мокра підлога' warns you about high voltage."
      correct: false
      explanation: "It warns about a wet floor. High voltage is 'Висока напруга'."
    - statement: "In the schedule format 'з 9:00 до 18:00', the word 'до' means 'to' or 'until'."
      correct: true
    - statement: "The word 'Вихід' means 'Exit'."
      correct: true
- type: fill-in
  title: "Complete the Sign"
  instruction: "Fill in the missing word for each sign or notice."
  items:
    - sentence: "Вхід ___!"
      answer: "заборонено"
      options:
        - "заборонено"
        - "зачинено"
        - "відчинено"
        - "дозволено"
    - sentence: "Мокра ___"
      answer: "підлога"
      options:
        - "підлога"
        - "напруга"
        - "вулиця"
        - "зупинка"
    - sentence: "Висока ___"
      answer: "напруга"
      options:
        - "напруга"
        - "підлога"
        - "перерва"
        - "площа"
    - sentence: "Пішохідний ___"
      answer: "перехід"
      options:
        - "перехід"
        - "вхід"
        - "вихід"
        - "зупинка"
    - sentence: "Не ___!"
      answer: "курити"
      options:
        - "курити"
        - "входити"
        - "торкатися"
        - "робити"
    - sentence: "Години ___"
      answer: "роботи"
      options:
        - "роботи"
        - "перерви"
        - "зупинки"
        - "вулиці"
    - sentence: "Магазин ___."
      answer: "зачинено"
      options:
        - "зачинено"
        - "відчинено"
        - "заборонено"
        - "обережно"
    - sentence: "Кафе ___."
      answer: "відчинено"
      options:
        - "відчинено"
        - "зачинено"
        - "заборонено"
        - "увага"
- type: group-sort
  title: "Sort the Terms"
  instruction: "Categorize the terms into Warnings/Dangers and Schedules/Notices."
  groups:
    - name: "Warnings and Dangers"
      items:
        - "Увага"
        - "Обережно"
        - "Небезпечно"
        - "Мокра підлога"
        - "Висока напруга"
    - name: "Store Schedules and Notices"
      items:
        - "Розклад"
        - "Вихідний"
        - "Перерва"
        - "Оголошення"
        - "Акція"
- type: match-up
  title: "Match the Street Term"
  instruction: "Connect the abbreviation or word to its English meaning."
  pairs:
    - left: "вул. (вулиця)"
      right: "street"
    - left: "пл. (площа)"
      right: "square"
    - left: "пров. (провулок)"
      right: "lane"
    - left: "зупинка"
      right: "transport stop"
    - left: "перехід"
      right: "crossing"
    - left: "розклад"
      right: "schedule"
    - left: "знижка"
      right: "discount"
    - left: "оголошення"
      right: "announcement"
    - left: "акція"
      right: "sale or promotion"
- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form correct Ukrainian sentences from the lesson."
  items:
    - words:
        - "Ми"
        - "часто"
        - "бачимо"
        - "знаки"
      answer: "Ми часто бачимо знаки"
    - words:
        - "Це"
        - "дуже"
        - "важлива"
        - "інформація"
      answer: "Це дуже важлива інформація"
    - words:
        - "Кожен"
        - "магазин"
        - "має"
        - "свій"
        - "розклад"
      answer: "Кожен магазин має свій розклад"
    - words:
        - "Ми"
        - "читаємо"
        - "їх"
        - "щодня"
      answer: "Ми читаємо їх щодня"
    - words:
        - "Люди"
        - "читають"
        - "їх"
        - "щодня"
      answer: "Люди читають їх щодня"
    - words:
        - "Час"
        - "роботи"
        - "пишуть"
        - "дуже"
        - "просто"
      answer: "Час роботи пишуть дуже просто"
    - words:
        - "Знаки"
        - "це"
        - "важлива"
        - "частина"
        - "міста"
      answer: "Знаки це важлива частина міста"
    - words:
        - "Там"
        - "є"
        - "розклад"
        - "руху"
      answer: "Там є розклад руху"
- type: true-false
  title: "True or False: Sign Language"
  instruction: "Test your knowledge about the grammatical forms used on Ukrainian signs."
  items:
    - statement: "'Не курити' is a direct personal command used by a person speaking to you."
      correct: false
      explanation: "It is an impersonal public sign using the infinitive form."
    - statement: "Public prohibition signs usually use the infinitive form of the verb."
      correct: true
      explanation: "Forms like 'входити' and 'торкатися' are infinitives."
    - statement: "'Зачинено' is used for doors and shops to mean 'closed'."
      correct: true
    - statement: "'Закрито' is the best and most precise word to use when a shop is closed."
      correct: false
      explanation: "This is incorrect Surzhyk. You should use 'Зачинено'."
    - statement: "'Відчинено' means that a store or cafe is currently open."
      correct: true
    - statement: "'Відкрито' is the correct Ukrainian word for an open door."
      correct: false
      explanation: "Doors are 'відчинені', not 'відкриті'."
    - statement: "'Не чіпай!' is a direct personal command."
      correct: true
      explanation: "This is used when a person speaks directly to you."
    - statement: "'Не торкатися!' is an impersonal infinitive sign."
      correct: true
      explanation: "You will see this on signs, such as in a museum."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/prohibitions-and-signs.yaml`

```yaml
items:
  - lemma: "не курити"
    translation: "no smoking"
    pos: "phrase"
  - lemma: "увага"
    translation: "attention"
    pos: "noun"
    gender: "f"
  - lemma: "обережно"
    translation: "caution / carefully"
    pos: "adverb"
  - lemma: "вхід"
    translation: "entrance"
    pos: "noun"
    gender: "m"
  - lemma: "вихід"
    translation: "exit"
    pos: "noun"
    gender: "m"
  - lemma: "зачинено"
    translation: "closed"
    pos: "adverb"
  - lemma: "відчинено"
    translation: "open"
    pos: "adverb"
  - lemma: "розклад"
    translation: "schedule"
    pos: "noun"
    gender: "m"
  - lemma: "вихідний"
    translation: "day off"
    pos: "noun"
    gender: "m"
  - lemma: "перерва"
    translation: "break"
    pos: "noun"
    gender: "f"
  - lemma: "небезпечно"
    translation: "dangerous"
    pos: "adverb"
  - lemma: "пішохідний"
    translation: "pedestrian"
    pos: "adjective"
  - lemma: "перехід"
    translation: "crossing / transfer"
    pos: "noun"
    gender: "m"
  - lemma: "зупинка"
    translation: "stop"
    pos: "noun"
    gender: "f"
  - lemma: "вулиця"
    translation: "street"
    pos: "noun"
    gender: "f"
  - lemma: "площа"
    translation: "square"
    pos: "noun"
    gender: "f"
  - lemma: "провулок"
    translation: "lane"
    pos: "noun"
    gender: "m"
  - lemma: "оголошення"
    translation: "announcement"
    pos: "noun"
    gender: "n"
  - lemma: "знижка"
    translation: "discount"
    pos: "noun"
    gender: "f"
  - lemma: "акція"
    translation: "sale / promotion"
    pos: "noun"
    gender: "f"
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, locate the exact text in the file contents above
2. Output a FIND/REPLACE pair with the exact text and the corrected version
3. Prioritize: **audit gate failures first**, then review issues
4. Only fix issues documented above — no silent extra changes
5. Maximum **15 FIND/REPLACE pairs** total

---

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections unless the Fix Plan explicitly requests it
- If nothing needs fixing, output an empty fix block
- FIND text must match the file contents EXACTLY (copy-paste from above)

---

## Output Format

You MUST use these exact delimiters:

```
===SECTION_FIX_START===
FILE: [filename]
FIND:
[exact text from the file — must match character-for-character]
REPLACE:
[corrected text]
---
FILE: [filename]
FIND:
[exact text]
REPLACE:
[corrected text]
---
[... more pairs, max 15 ...]
===SECTION_FIX_END===
```

If no fixes are needed:

```
===SECTION_FIX_START===
(No fixes needed — all issues resolved)
===SECTION_FIX_END===
```

After the fix block, output a friction report:

```
===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: {what you were doing}
**Friction Type**: NONE | TEXT_NOT_FOUND | ...
**Raw Error**: {actual issue or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done
- Do NOT output ===REVIEW_START=== or ===FACTUAL_REVIEW_START=== blocks
- Do NOT use Edit tool or any other tool — you have NO tool access
- Output ONLY FIND/REPLACE pairs within the delimiters above
- Maximum 15 FIND/REPLACE pairs


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 15 min timeout]...
===SECTION_FIX_START===
(No fixes needed — all issues resolved)
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Searching for target text to apply the Review Plan
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: None of the targeted errors from the Fix Plan exist in the provided file contents. The text has already been updated with the correct phrases (e.g., "відкрито" is already used instead of "роботу", "заощадити" instead of "зберегти", "вам" instead of "для вас", and the header is already "Фрази без дієслів").
**Self-Correction**: Outputted that no fixes are needed, as all specified review issues are already fully resolved in the provided markdown. I did not attempt to guess the 3 pedagogy violations since their details were not included in the prompt and silent extra changes are forbidden.
**Proposed Tooling Fix**: Ensure the pipeline does not feed an already-fixed file state back into the review-fix loop without updating the Fix Plan, and provide the exact `audit.log` excerpts when asking the agent to resolve specific audit gate failures like pedagogy violations.
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (1139 chars)
✅ Message sent to Claude (ID: 21316)
✓ Message 21316 acknowledged
   Auto-acknowledged reply #21316 (stdout delivery — no inbox accumulation)
⚠️  GitHub issue creation failed: could not add label: 'review-result' not found

✓ Message 21313 acknowledged
