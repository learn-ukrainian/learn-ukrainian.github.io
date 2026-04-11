<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/relative-clauses.yaml` file for module **49: Той, який...** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-yakiy-agreement -->`
- `<!-- INJECT_ACTIVITY: true-false-comma-agreement -->`
- `<!-- INJECT_ACTIVITY: quiz-place-connectors -->`
- `<!-- INJECT_ACTIVITY: match-up-sentence-combine -->`
- `<!-- INJECT_ACTIVITY: unjumble-relative-clauses -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Insert the correct form of який (яка, яке, які) into relative clauses, matching
    gender and number
  items: 8
  type: fill-in
- focus: Choose де, куди, or звідки to complete sentences about places
  items: 8
  type: quiz
- focus: Combine two simple sentences into one using a relative clause
  items: 8
  type: match-up
- focus: Judge whether relative clauses have correct agreement and comma placement
  items: 8
  type: true-false
- focus: Reorder words to form correct relative clauses with який/яка/яке and де/куди/звідки
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- котрий (which — formal synonym of який)
- затишний (cozy, comfortable)
- знаходитися (to be located)
- стояти (to stand, to be situated)
required:
- який (which, that — masc.)
- яка (which, that — fem.)
- яке (which, that — neut.)
- які (which, that — pl.)
- де (where — relative)
- куди (where to — relative)
- звідки (where from — relative)
- означальний (attributive, defining)
- описувати (to describe)
- речення (sentence, clause)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Який? Яка? Яке? Які? (Which? What Kind?)

В українській мові ми часто використовуємо **означальні підрядні речення** *(relative clauses)*, щоб описати людину, річ або місце. You already know how simple adjectives describe nouns. For example, you can say «гарна книга» *(a good book)*. Але іноді нам потрібно сказати більше. A relative clause expands this description into a full action. Замість одного слова ми використовуємо ціле речення: «книга, яку я зараз читаю» *(the book that I am reading now)*. This creates a complex structure with two parts. Перша частина — це **головне речення** *(the main clause)*. Друга частина — це **підрядне речення** *(the subordinate clause)*. The relative clause always connects to a specific noun in the main clause to give us more information.

Головне слово для таких речень — це займенник **«який»** *(which, who, that)*. This relative pronoun is the bridge between the two parts. It must always agree in gender with the specific noun it describes in the main sentence. Якщо іменник має чоловічий рід *(masculine)*, ми використовуємо форму «який». «Це будинок, який стоїть біля метро.» *(This is the house that stands near the subway.)* Якщо іменник має жіночий рід *(feminine)*, нам потрібна форма «яка». «Ось квартира, яка має три кімнати.» *(Here is the apartment that has three rooms.)* Якщо іменник має середній рід *(neuter)*, ми беремо форму «яке». «Це місто, яке розташоване на півдні.» *(This is the city that is located in the south.)* Remember this fundamental rule: the gender of «який» comes strictly from the noun it points back to, regardless of its role in the new sentence.

Для множини *(plural)* ми завжди використовуємо форму «які». The plural form is universal and does not change based on gender. It works perfectly for both groups of people and objects, making it very easy to use. Ми можемо говорити про людей: «Це розумні люди, які працюють тут щодня.» *(These are smart people who work here every day.)* Або ми можемо описувати різні речі: «Де ключі, які лежать на цьому столі?» *(Where are the keys that lie on this table?)* Notice the transition from the singular to the plural form. If you have only one phone, you say «телефон, який добре працює» *(a phone that works well)*. But if you have two or more, it becomes «телефони, які добре працюють» *(phones that work well)*. The word «які» simply links the plural noun to the action.

Now, let's look at how the cases *(відмінки)* work. While the exact gender of «який» comes from the main noun, its case comes entirely from its specific role *inside* the subordinate clause. If the relative pronoun is the active subject of the subordinate clause, it stays in the basic Nominative case *(Називний відмінок)*. «Це хлопець, який прийшов до нас вчора.» *(This is the boy who came to us yesterday.)* Here, the boy actively came. But if the relative pronoun is the direct object of the subordinate clause, it must change to the Accusative case *(Знахідний відмінок)*. «Це хлопець, якого я бачив вчора.» *(This is the boy whom I saw yesterday.)* Here, "I" am the subject doing the seeing, and the boy is the object being seen. Для жіночого роду форма «яка» змінюється на «яку» в Знахідному відмінку: «Це цікава книга, яку я читаю.» *(This is the interesting book that I am reading.)* Для істот чоловічого роду форма «який» змінюється на «якого»: «Це мій друг, якого я чекаю.» *(This is my friend whom I am waiting for.)*

There is a strict punctuation rule you must always follow when writing. In Ukrainian grammar, unlike English, you *must* place a comma *(кома)* immediately before the relative pronoun «який». Think of this required comma as a clear "gate" opening to provide more detail about the main noun. You cannot skip this gate. ❌ «Машина яка стоїть там, дуже стара.» ✅ «Машина, яка стоїть там, дуже стара.» *(The car that stands there is very old.)* Ця кома чітко показує, де закінчується головна думка і починається додатковий опис. Це дуже важливе правило.

Also, remember the contrast between questions and relative clauses. You already know «який» as a question word: «Який це фільм?» *(What kind of movie is this?)*. When used as a relative pronoun, it connects sentences instead of asking a question: «Фільм, який ми дивилися вчора, був цікавий.» *(The movie that we watched yesterday was interesting.)* It is the same word, but it has a completely different function.

В українській мові є ще одне дуже популярне слово для таких речень — це **«що»** *(that, who)*. While using «який» is perfectly correct, using «що» for Nominative and Accusative cases is a highly idiomatic Ukrainian pattern. «Це добра людина, що завжди допомагає іншим.» *(This is a kind person who always helps others.)* Слово «що» взагалі не змінює свою граматичну форму в цих відмінках. Воно не має чоловічого, жіночого або середнього роду. Воно також не має множини. This makes it incredibly easy to use in everyday conversation. «Це довгий лист, що я написав вчора.» *(This is a long letter that I wrote yesterday.)* Using «що» instead of «який» makes your speech sound very authentic. It helps you "think in Ukrainian" without translating English structures. You might also encounter the formal synonym **«котрий»** *(which)* in literature or news, but «який» remains the standard for everyday conversation.

Давайте подивимося, як ця граматика працює в реальному житті. Уявіть ситуацію: ріелтор *(real estate agent)* показує нову квартиру клієнту.

> — **Ріелтор:** Це світла квартира, яка має великий балкон. *(This is a bright apartment that has a large balcony.)*
> — **Покупець:** А де те вікно, яке виходить на вулицю? *(And where is that window that faces the street?)*
> — **Ріелтор:** Ось маленька кімната, яка виходить на сусідній парк. *(Here is a small room that faces the neighboring park.)* Це дуже тихе місце. *(This is a very quiet place.)*
> — **Покупець:** Хто ті люди, які стоять біля нашого будинку? *(Who are those people who are standing near our house?)*
> — **Ріелтор:** А, це наш сусід, який живе тут вже десять років. *(Ah, that is our neighbor who has lived here for ten years already.)*

<!-- INJECT_ACTIVITY: fill-in-yakiy-agreement -->
<!-- INJECT_ACTIVITY: true-false-comma-agreement -->

## Де, куди, звідки — місце (Where, Where To, Where From — Place)

Ми вже знаємо, як описувати людей і різні речі. *(We already know how to describe people and different things.)* Для цього ми зазвичай використовуємо слово «який». *(For this we usually use the word "which".)* Але що робити, коли ми хочемо описати певне місце на карті? *(But what to do when we want to describe a certain place on the map?)* When we describe a specific location, destination, or origin, we usually don't use the relative pronoun «який». Instead, Ukrainian uses relative adverbs of place: **«де»** *(where)*, **«куди»** *(where to)*, and **«звідки»** *(where from)*. Ці маленькі слова роблять ваші речення дуже простими і природними. *(These small words make your sentences very simple and natural.)* Вони також ніколи не змінюють свою форму. *(They also never change their form.)* Вам не потрібно думати про складні відмінки. *(You do not need to think about complex cases.)*

Давайте почнемо з найпопулярнішого слова «де». *(Let's start with the most popular word "where".)* Ми використовуємо це слово для статичного місця. *(We use this word for a static place.)* It shows where something is located or where an action happens without any movement. You might think of saying "the restaurant in which we ate" using the complex prepositional construction «в якому». But in everyday spoken Ukrainian, it is much more natural to simply use «де». «Це той самий ресторан, де ми вчора обідали.» *(This is the exact same restaurant where we had lunch yesterday.)* «Ось та гарна вулиця, де я зараз живу.» *(Here is that beautiful street where I live now.)* «Я обов'язково покажу тобі великий будинок, де працює мій старший брат.» *(I will definitely show you the big house where my older brother works.)* Using «де» means you do not need to worry about cases or gender agreement for the location. Це дійсно дуже зручно для щоденного спілкування. *(This is really very convenient for daily communication.)* Завжди ставте кому перед словом «де». *(Always put a comma before the word "where".)*

Але якщо ми говоримо про рух або точний напрямок, слово «де» зовсім не підходить. *(But if we talk about movement or exact direction, the word "where" does not fit at all.)* For direction or motion towards a place, we must use «куди». Це слово показує кінцеву мету нашої подорожі. *(This word shows the final goal of our journey.)* Think of it as "the place to which". «Ми нарешті вибрали місто, куди поїдемо у літню відпустку.» *(We finally chose the city where we will go on summer vacation.)* «Це той новий магазин, куди вона швидко зайшла п'ять хвилин тому.» *(This is that new store where she quickly went in five minutes ago.)* «Я не знаю парк, куди вони пішли гуляти сьогодні вранці.» *(I do not know the park where they went for a walk this morning.)* Завжди уважно дивіться на дієслово. *(Always look carefully at the verb.)* Якщо це дієслово активного руху, як-от «йти», «бігти» або «їхати», використовуйте «куди». *(If it is a verb of active motion, like "to walk", "to run", or "to ride", use "where to".)*

Нарешті, ми маємо цікаве слово «звідки». *(Finally, we have the interesting word "where from".)* Ми використовуємо його, коли говоримо про джерело або самий початок руху. *(We use it when we talk about the source or the very beginning of movement.)* It describes the specific place from which someone or something came. «Це маленьке село, звідки привезли це свіже молоко.» *(This is the small village where this fresh milk was brought from.)* «Я дуже хочу побачити країну, звідки він вчора приїхав.» *(I really want to see the country where he came from yesterday.)* «Ось та нова школа, звідки щойно вийшли радісні діти.» *(Here is that new school where the joyful children just came out from.)* Як і з іншими сполучними словами, перед «звідки» завжди стоїть кома. *(Like with the other connecting words, there is always a comma before "where from".)* Це важливе граматичне правило. *(This is an important grammar rule.)*

Давайте прочитаємо короткий діалог. *(Let's read a short dialogue.)* Клієнт хоче купити нову простору квартиру і активно розпитує про район. *(A client wants to buy a new spacious apartment and actively asks about the neighborhood.)*

> — **Покупець:** Цей новий район виглядає дуже тихим і спокійним. *(This new neighborhood looks very quiet and peaceful.)* Де розташований найближчий парк, куди ми можемо ходити гуляти з нашим собакою? *(Where is the nearest park where we can go for a walk with our dog?)*
> — **Ріелтор:** Великий зелений парк зовсім близько. *(The big green park is very close.)* А ось широка вулиця, де є гарна пекарня і маленька кав'ярня. *(And here is a wide street where there is a nice bakery and a small coffee shop.)*
> — **Покупець:** О, я вже відчуваю цей приємний запах. *(Oh, I already smell this pleasant smell.)*
> — **Ріелтор:** Так, це саме те місце, звідки завжди пахне свіжою кавою і теплим хлібом. *(Yes, this is exactly the place where it always smells of fresh coffee and warm bread.)*
> — **Покупець:** Це просто чудово. *(This is simply wonderful.)* Я дуже люблю місця, де є така затишна атмосфера. *(I really love places where there is such a cozy atmosphere.)*

Отже, запам'ятайте це дуже просте правило. *(So, remember this very simple rule.)* We use «де» for static location ("at which" or "in which"), «куди» for dynamic direction towards a place ("to which"), and «звідки» for clear origin ("from which"). Ці три слова допомагають дуже легко і швидко описувати будь-які локації. *(These three words help to very easily and quickly describe absolutely any locations.)*

<!-- INJECT_ACTIVITY: quiz-place-connectors -->

## Описуємо людей, речі та місця (Describing People, Things, and Places)

Ми вже добре знаємо, як використовувати слова «який», «де», «куди» та «звідки». *(We already know well how to use the words "which", "where", "where to", and "where from".)* Тепер давайте уважно подивимося, як саме вони допомагають нам детально описувати різних людей і предмети. *(Now let's look closely at exactly how they help us describe various people and objects in detail.)* Usually, when we start learning a language, we use very short and simple sentences. Наприклад, ми часто кажемо: «Мій старший брат зараз живе у Польщі. *(For example, we often say: "My older brother lives in Poland now.)* Він працює там лікарем». *(He works there as a doctor.")* Це правильно граматично, але звучить дуже просто і трохи штучно. *(This is absolutely correct grammatically, but it sounds very simple and a bit artificial.)* Складнопідрядні речення роблять наше щоденне мовлення більш **елегантним** *(elegant)*, плавним та природним. *(Complex sentences make our everyday speech more elegant, fluent, and natural.)* Ми можемо легко об'єднати ці дві окремі думки в одну красиву конструкцію. *(We can easily combine these two separate thoughts into one beautiful structure.)* «Мій брат, який працює лікарем, живе зараз у Польщі.» *(My brother, who works as a doctor, lives in Poland now.)* У цьому новому реченні головна інформація — це те, що він живе у Польщі. *(In this new sentence, the main information is that he lives in Poland.)* А підрядна частина «який працює лікарем» — це просто зручний додатковий опис. *(And the subordinate part "who works as a doctor" is just a convenient additional description.)*

Коли ми самостійно будуємо такі довгі речення, дуже важливо уникати однієї типової помилки. *(When we independently build such long sentences, it is very important to avoid one typical mistake.)* English speakers often want to repeat the subject or object inside the relative clause because it feels natural in English. Наприклад, вони часто можуть помилково сказати: «Це та нова книга, яку я читав її...» *(For example, they can often mistakenly say: "This is that new book which I read it...")* Це **зайвий** *(redundant)* займенник, який робить речення неправильним. *(This is a redundant pronoun that makes the sentence absolutely incorrect.)* В українській мові слово «яку» вже повноцінно виконує роль цього конкретного предмета. *(In the Ukrainian language, the word "which" already fully performs the role of this specific object.)* Воно повністю замінює слово «книга» у нашій підрядній частині. *(It completely replaces the word "book" in our subordinate part.)* Тому правильно і природно говорити тільки так: «Книга, яку я читав, була дуже цікава.» ✅ *(Therefore, it is correct and natural to speak only like this: "The book which I read was very interesting.")* Ніколи не додавайте зайві слова «його», «її» або «їх» відразу після слова «який». *(Never add the redundant words "him", "her", or "them" right after the word "which".)*

Також обов'язково зверніть свою увагу на правильну **інтонацію** *(intonation)* у таких довгих фразах. *(Also definitely pay your attention to the correct intonation in such long phrases.)* Коли ми вимовляємо означальне підрядне речення, наш голос завжди трохи змінюється. *(When we pronounce an attributive subordinate clause, our voice always changes a bit.)* The pitch drops slightly for the parenthetical insert, which is the relative clause itself. Потім ваш голос знову повертається до нормального базового рівня для решти головного речення. *(Then your voice returns again to the normal base level for the rest of the main sentence.)* Пам'ятайте, що кома перед словом «який» — це не просто нудний розділовий знак. *(Remember that the comma before the word "which" is not just a boring punctuation mark.)* Це дуже важлива маленька пауза для вашого дихання. *(This is a very important small pause for your breathing.)* It gives the listener a necessary micro-pause to process the descriptive addition. Прочитайте це речення вголос: «Цей розумний студент, [пауза] який сидить там, [пауза] знає всі відповіді.» *(Read this sentence out loud: "This smart student, [pause] who is sitting there, [pause] knows all the answers.")*

Ми можемо додавати більше цікавих деталей і вільно комбінувати різні сполучні слова. *(We can add more interesting details and freely combine different connecting words.)* You can stack information naturally to describe a specific place using multiple relative clauses. Наприклад: «Це **старий** *(old)* будинок, який стоїть на горі і де колись жив відомий поет.» *(For example: "This is an old house which stands on the mountain and where a famous poet once lived.")* Тут ми маємо одразу дві різні підрядні частини. *(Here we have two different subordinate parts at once.)* Перша частина описує сам фізичний предмет: «який стоїть на горі». *(The first part describes the physical object itself: "which stands on the mountain".)* Друга частина описує конкретну локацію: «де колись жив відомий поет». *(The second part describes the specific location: "where a famous poet once lived".)* Це чудово демонструє ваш високий рівень володіння українською мовою. *(This wonderfully demonstrates your high level of Ukrainian language proficiency.)*

Тепер, будь ласка, спробуйте самостійно описати ваш улюблений предмет або якесь особливе місце. *(Now, please, try to independently describe your favorite object or some special place.)* Подумайте про історію цієї речі або про те, де саме вона зараз лежить чи стоїть. *(Think about the history of this thing or about where exactly it is located now.)* Ось один дуже гарний приклад для вас. *(Here is one very good example for you.)* «Мій **улюблений** *(favorite)* предмет — це годинник, який подарував мені дідусь і який завжди показує точний час.» *(My favorite object is a watch, which my grandfather gave me and which always shows the exact time.)* Спробуйте написати схоже складне речення про свій новий телефон або рідне місто. *(Try to write a similar complex sentence about your new phone or hometown.)* Використовуйте всі нові слова, які ви знаєте, і ніколи не забувайте про коми! *(Use all the new words that you know, and never forget about commas!)*

<!-- INJECT_ACTIVITY: match-up-sentence-combine -->
<!-- INJECT_ACTIVITY: unjumble-relative-clauses -->

## Підсумок

Ось найголовніші правила, які вам потрібно пам'ятати з цього уроку. *(Here are the most important rules you need to remember from this lesson.)*

*   Слово «який» завжди копіює **рід** *(gender)* і **число** *(number)* слова, яке воно описує. *(The word "який" always copies the gender and number of the word it describes.)*
*   Ми завжди ставимо кому перед словами «який», «де», «куди» або «звідки». *(We always put a comma before the words "which", "where", "where to", or "where from".)*
*   Use «де» to describe a location, «куди» for a movement, and «звідки» for an origin.
*   Inside the subordinate clause, «який» takes the case required by the verb. *(Наприклад: «Це дівчина, яку я бачу» — Accusative).*
*   А тепер питання для самоперевірки. *(And now a question for self-checking.)* Can you describe your best friend using «який» and «де» in one sentence? Наприклад: «Мій найкращий друг, який живе в Одесі, дуже любить море». *(For example: "My best friend, who lives in Odesa, loves the sea very much.")*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: relative-clauses
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

**Level: A2 (Module 49/60) — ELEMENTARY**

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

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

### Pattern: grammar-numbers [§4.2.1.3]
**Числівники** (Numerals)
- **quiz** — Яке число?: Розпізнати числівники, записані словами / Recognize written number words
- **fill-in** — Напиши цифру словом: Записати числівник словом по-українськи / Write the number as a Ukrainian word
- **match-up** — Цифра → слово: Зіставити цифри з їхніми українськими назвами / Match digits to their Ukrainian word forms
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Числівники складні для написання — давати варіанти на A1

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
