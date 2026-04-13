<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/because-and-although.yaml` file for module **47: Тому що, бо, хоча** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-match-two-halves-of-sentences-with-with -->`
- `<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-compound-sentences-with-and -->`
- `<!-- INJECT_ACTIVITY: group-sort-sort-conjunctions-into-vs-vs -->`
- `<!-- INJECT_ACTIVITY: quiz-choose-the-correct-conjunction-to-complete-sentences -->`
- `<!-- INJECT_ACTIVITY: fill-in-complete-compound-sentences-by-adding-the-missing-clause-after-the-conjunction -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the correct conjunction (тому що, бо, хоча, але) to complete sentences
  items: 8
  type: quiz
- focus: Complete compound sentences by adding the missing clause after the conjunction
  items: 8
  type: fill-in
- focus: Match two halves of sentences — причина with наслідок, допуст with результат
  items: 8
  type: match-up
- focus: Sort conjunctions into причина (тому що, бо) vs. допуст (хоча) vs. протиставлення
    (але, проте, однак)
  items: 8
  type: group-sort
- focus: Reorder words to form correct compound sentences with тому що, бо, and хоча
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- допуст (concession)
- зате (but then, on the other hand)
- навпаки (on the contrary)
- незважаючи на (despite)
required:
- тому що (because)
- бо (because — colloquial)
- хоча (although, even though)
- але (but)
- проте (however, yet)
- однак (however)
- причина (reason, cause)
- сполучник (conjunction)
- складне речення (complex sentence)
- тому (therefore, that is why)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чому? Тому що... / Бо... (Why? Because...) (~770 words total)

Університетське життя завжди повне складних рішень. Кожного дня студенти обирають: піти на лекцію чи залишитися вдома? Для цього ми використовуємо спеціальні слова, які допомагають нам будувати логічні аргументи. Послухайте коротку розмову двох друзів перед важливою парою.

> *University life is always full of difficult decisions. Every day, students choose: to go to a lecture or stay home? To do this, we use special words that help us build logical arguments. Listen to a short conversation between two friends before an important class.*

> — **Студент 1:** Я сьогодні не піду на пару, бо дуже хворію. *(I won't go to class today, because I am very sick.)*
> — **Студент 2:** Але тобі треба піти, тому що завтра важлива контрольна! *(But you need to go, because tomorrow is an important test!)*
> — **Студент 1:** Ох... Хоча я страшенно втомився, я все одно піду. *(Oh... Even though I am terribly tired, I will go anyway.)*

When you want to explain the **причина** (reason) for an action, you need to answer the question «Чому?». In Ukrainian grammar, we use a **складне речення** (complex sentence) to connect the main action with its explanation. To link these two parts together, we use a special linking word called a **сполучник** (conjunction). The two most common causal conjunctions you will hear every day are «тому що» and «бо». Both of them translate directly to the English word "because".

While both «тому що» and «бо» mean "because", they feel slightly different in practice. The phrase «тому що» is neutral and versatile. You will see it in official documents and literature, but people also use it frequently in everyday speech. On the other hand, the short word «бо» is highly colloquial and native to Ukrainian. You will hear it constantly in casual conversations and friendly chats.

Багато людей думають, що коротке слово «бо» — це неправильна мова або якийсь діалект. Але це велика помилка! Слово «бо» — це питоме українське слово, яке має дуже давню історію. Наші письменники та поети завжди використовували його у своїх творах. 

> *Many people think that the short word "бо" is incorrect language or some kind of dialect. But this is a big mistake! The word "бо" is an authentic Ukrainian word that has a very long history. Our writers and poets have always used it in their works.*

:::tip
**Don't fear the short word**
Some learners worry that the word «бо» sounds uneducated. This is a myth! It is a core part of the Ukrainian language, widely used across all regions and social groups.
:::

When writing such sentences, punctuation is strict. You must always place a comma immediately before the conjunction that introduces the reason. So, the comma goes right before the word «бо», or right before the full phrase «тому що». Note that the comma never goes inside the phrase «тому що». You can start a sentence with «тому що» when directly answering a question, but you should avoid starting a sentence with «бо». 

Let's look at a few real-life examples showing how we express cause:

* **Я не прийшов на зустріч, тому що був дуже зайнятий.** — *I didn't come to the meeting, because I was very busy.*
* **Вона вивчає українську мову, бо хоче краще розуміти друзів.** — *She is studying the Ukrainian language, because she wants to better understand her friends.*
* **Ми купили квитки заздалегідь, тому що вони були дешеві.** — *We bought tickets in advance, because they were cheap.*
* **Я одягнув теплу куртку, бо надворі сильний вітер.** — *I put on a warm jacket, because there is a strong wind outside.*

Ці слова можна знайти не лише у побутових розмовах, але й у народній мудрості. Одне з найвідоміших прислів'їв каже: «Держімося землі, бо земля держить нас». Це означає, що ми маємо дбати про свою батьківщину, щоб вона дбала про нас.

> *These words can be found not only in everyday conversations, but also in folk wisdom. One of the most famous proverbs says: "Let's hold on to the earth, because the earth holds us." This means that we must take care of our homeland so that it takes care of us.*

A great way to practice is to combine two simple sentences into one fluent thought. Imagine you have two facts: «Погода була погана.» (The weather was bad.) and «Ми залишилися вдома.» (We stayed home.). You can easily link them: «Ми залишилися вдома, тому що погода була погана.»

The word **тому** (therefore) flips the relationship. It introduces the *result* rather than the *cause*. Let's look at how the previous weather example changes when we use this new word:

* **Погода була погана, тому ми залишилися вдома.** — *The weather was bad, therefore we stayed home.*

Спробуйте будувати такі речення кожного дня. Коли ви йдете в магазин, скажіть собі: «Я йду в магазин, бо вдома немає хліба». Це дуже корисна вправа для вашого мозку.

## Хоча... (Although...) (~660 words total)

Things do not always happen the way we expect. To express a contrast between an expectation and the actual reality, we use the word **хоча** (although, even though). This word introduces a special type of dependent clause called a **допуст** (concession). It shows that the situation in one part of your sentence makes the action in the other part surprising.

Коли ми плануємо свій день, ми часто дивимося на прогноз погоди. Якщо на вулиці йде дощ або дуже холодно, логічно просто залишитися вдома. Але іноді наші плани або бажання є набагато сильнішими за зовнішні обставини. Наприклад, ми можемо сказати: «Хоча надворі холодно, ми пішли гуляти». У цьому короткому реченні перша частина описує погані умови. Друга частина показує нашу дію, яка успішно відбулася всупереч цим складним умовам. Це дуже корисна структура для повсякденного спілкування.

> *When we plan our day, we often look at the weather forecast. If it is raining or very cold outside, it is logical to simply stay home. But sometimes our plans or desires are much stronger than external circumstances. For example, we can say: "Although it is cold outside, we went for a walk." In this short sentence, the first part describes the bad conditions. The second part shows our action, which successfully happened despite these difficult conditions. This is a very useful structure for everyday communication.*

Learners often confuse **хоча** with the simpler **сполучник** (conjunction) **але** (but). While both words express a contrast, they function differently. The word «але» simply connects two equal, contrasting facts. The word «хоча» makes one fact dependent on the other, putting the focus entirely on the unexpected outcome.

Давайте порівняємо дві дуже схожі ситуації. Перший базовий варіант: «Він втомився, але продовжив працювати». Тут ми маємо два абсолютно рівні прості факти. Людина має сильну втому, проте вона працює далі. Це звичайне протиставлення двох дій. Другий складніший варіант: «Хоча він втомився, він продовжив працювати». Тут ми робимо сильний акцент на тому, що його робота є несподіваним результатом. Ми підкреслюємо його зусилля, зважаючи на його втому. Важливо пам'ятати одну критичну річ про цю граматику. Студенти часто кажуть: «Хоча він втомився, але він працював». Для вашого рівня краще завжди уникати такої подвійної конструкції. Використовуйте у своєму реченні тільки один сполучник — або «хоча», або «але».

> *Let's compare two very similar situations. The first basic variant: "He was tired, but he continued to work." Here we have two absolutely equal simple facts. The person has strong fatigue, yet they work further. This is a normal contrast of two actions. The second more complex variant: "Although he was tired, he continued to work." Here we put a strong emphasis on the fact that his work is an unexpected result. We highlight his effort, considering his fatigue. It is important to remember one critical thing about this grammar. Students often say: "Although he was tired, but he worked." For your level, it is better to always avoid such a double construction. Use only one conjunction in your sentence — either "although" or "but".*

One of the great advantages of building a **складне речення** (complex sentence) with **хоча** is its positional flexibility. The dependent clause can easily be placed either at the very beginning of your sentence or in the second half. This allows you to decide which information your listener hears first. Just remember to always separate the two parts with a comma.

Ви можете вільно змінювати порядок частин у вашому складному реченні. Наприклад, ви можете сказати: «Ми пішли на прогулянку, хоча йшов дощ». У цьому випадку головна інформація звучить найпершою. Або ви можете повністю змінити структуру: «Хоча йшов дощ, ми пішли на прогулянку». Зміст залишається абсолютно однаковим, але акцент трохи змінюється. Головне правило, яке ви повинні завжди пам'ятати, стосується пунктуації. Незалежно від того, де саме стоїть ця частина, ви завжди повинні відділяти її комою. Якщо вона стоїть на початку, кома ставиться після неї. Якщо вона стоїть другою, кома ставиться безпосередньо перед нею.

:::info
**Мелодія мови (Speech melody)**
В українській мові речення з цим сполучником мають дуже красиву інтонацію. Частина речення зі словом «хоча» зазвичай закінчується легким підвищенням голосу. Це показує, що думка ще не закінчена. Потім, у головній частині речення, голос повільно падає вниз. Ваша інтонація природно веде слухача до несподіваного результату.

> *In the Ukrainian language, sentences with this conjunction have a very beautiful intonation. The part of the sentence with the word "although" usually ends with a slight raising of the voice. This shows that the thought is not yet finished. Then, in the main part of the sentence, the voice slowly falls down. Your intonation naturally guides the listener to the unexpected result.*
:::

In everyday conversations, you will frequently hear the shorter word **хоч** instead of the full «хоча». They are exact synonyms, but «хоч» sounds a bit more conversational. You might also encounter formal phrases like **незважаючи на те що** (despite the fact that), which you only need to recognize passively.

Давайте подивимося на кілька живих і дуже типових прикладів. Студент може сказати: «Хоча я вчу українську недовго, я вже розумію багато». Або інший приклад: «Хоч квитки були дорогі, ми поїхали на концерт». Обидва варіанти звучать надзвичайно природно і граматично правильно. У дуже формальних текстах ви також можете часто зустріти довгу фразу «незважаючи на те що». На цьому етапі вам зовсім не обов'язково активно використовувати її у своєму власному мовленні. Достатньо просто впізнавати цю фразу, коли ви читаєте українські новини.

When translating directly from English, learners often make a structural mistake. In English, it is very common to add the word "though" at the very end of a sentence. However, in Ukrainian, the conjunction must always stand at the exact beginning of the dependent clause it introduces.

Деякі іноземні студенти постійно пробують перекладати власні думки абсолютно дослівно. Вони часто кажуть: «Він купив цю машину, вона була дуже стара хоча». Це дуже серйозна структурна помилка. В українській мові потрібно говорити: «Він купив цю машину, хоча вона була дуже стара». Це слово завжди відкриває нову думку, воно ніколи не закриває її. Інший гарний приклад з історії: «Радянська пропаганда так казала, хоча насправді це не було правдою». Зверніть увагу, як слово стоїть чітко на самому початку залежної частини речення. Ніколи не залишайте його наприкінці.

> *Some foreign students constantly try to translate their own thoughts absolutely literally. They often say: "He bought this car, it was very old though." This is a very serious structural mistake. In the Ukrainian language, you must say: "He bought this car, although it was very old." This word always opens a new thought, it never closes it. Another good example from history: "Soviet propaganda said so, although in reality it was not true." Notice how the word stands clearly at the very beginning of the dependent part of the sentence. Never leave it at the end.*

<!-- INJECT_ACTIVITY: match-up-match-two-halves-of-sentences-with-with -->
<!-- INJECT_ACTIVITY: unjumble-reorder-words-to-form-correct-compound-sentences-with-and -->

## Складносурядне речення: і, та, але (Compound Sentences: and, but) (~770 words total)

You already know the basic words used to connect ideas from your earlier studies. Now, we will look at how a coordinating **сполучник** (conjunction) functions within a true **складне речення** (complex sentence). You are familiar with the word «і» (and) and the contrast word **але** (but). To make your Ukrainian sound richer, you can use stylistic alternatives. The word «та» is a beautiful, traditional alternative to «і». For expressing contrast, you can use words like «проте», «однак», and «зате». If you want to show a very strong, direct contrast, you can use the word «навпаки» (on the contrary). Using these alternatives instantly elevates your spoken and written language to a higher level.

Коли ми говоримо, ми часто об'єднуємо дві рівноправні думки. Вони не залежать одна від одної. Ці частини просто існують разом. Наприклад: «Я прийшов додому, і ми разом повечеряли». Тут є дві повноцінні дії. Або інший приклад: «Сергій хотів піти в кіно, але не мав часу». Іноді українці використовують слово «та» замість «і». Вони роблять це, щоб уникнути частих повторень. Ми часто кажемо: «Сонце світить, та вітер дуже холодний». Якщо ви хочете показати сильний контраст, використовуйте «проте» або «однак». Наприклад: «Він довго шукав ключі, однак так і не знайшов їх». Це звучить дуже природно і літературно.

> *When we speak, we often combine two equal thoughts. They do not depend on each other. These parts simply exist together. For example: "I came home, and we had dinner together." Here there are two complete actions. Or another example: "Serhiy wanted to go to the cinema, but did not have time." Sometimes Ukrainians use the word «та» instead of «і». They do this to avoid frequent repetitions. We often say: "The sun is shining, and the wind is very cold." If you want to show a strong contrast, use «проте» or «однак». For example: "He looked for the keys for a long time, however he never found them." This sounds very natural and literary.*

It is important to understand the difference between coordinating conjunctions and subordinating conjunctions. Coordinating words like «і», «та», and «але» link two equal, independent clauses. Neither clause is more important than the other. In contrast, subordinating words link a main clause to a dependent one. For example, **тому що** (because) and **бо** (because — colloquial) introduce a **причина** (reason, cause). 

The word **хоча** (although, even though) introduces a concession. To find the main clause, look for the part of the sentence that can stand completely alone as a logical statement. The dependent clause usually starts with the conjunction and explains why or despite what the main action happened. Because these structures are different, we use them for different purposes. **Тому** (therefore, that is why), it is crucial to choose the right connector for your logical flow.

<!-- INJECT_ACTIVITY: group-sort-sort-conjunctions-into-vs-vs -->

В українській мові є суворі правила щодо ком у складних реченнях. Ви повинні завжди ставити кому перед словами «але», «проте» та «однак». Це правило не має жодних винятків. Ситуація зі словами «і» та «та» є трохи іншою. Якщо ці слова з'єднують два окремі речення, кома потрібна обов'язково. Там має бути свій суб'єкт і своє дієслово. Наприклад: «Почався дощ, і ми швидко побігли додому». Тут є дощ, який почався. І також є ми, які побігли. Але якщо слово просто з'єднує два слова в одному списку, кома не ставиться. Наприклад: «Я купив молоко і хліб».

> *In the Ukrainian language, there are strict rules regarding commas in complex sentences. You must always put a comma before the words «але», «проте», and «однак». This rule has no exceptions. The situation with the words «і» and «та» is a little different. If these words connect two separate sentences, a comma is absolutely necessary. There must be its own subject and its own verb. For example: "The rain started, and we quickly ran home." Here there is the rain that started. And also there are we who ran. But if the word simply connects two words in one list, a comma is not placed. For example: "I bought milk and bread."*

Let us talk about the melody of these sentences. Intonation patterns are very specific when you use different types of conjunctions. In causal sentences, the main clause usually carries a falling tone. Then, the subordinate clause starting with «тому що» or «бо» begins with a slight rise in pitch before settling down at the end. This signals to the listener that an explanation is coming. Concessive sentences work differently. The clause starting with «хоча» usually rises at the end to signal the concession. This upward inflection holds the listener's attention. Then, the main clause follows with a falling tone to deliver the contrasting result. If you use coordinating contrast words like **проте** (however, yet) or **однак** (however), the intonation usually falls evenly on both clauses because they are independent.

:::info
**Intonation tip**
When you use «хоча», always leave your voice slightly "hanging" or raised at the end of that clause. It tells the Ukrainian listener, "Wait, there is a twist coming!" Then drop your pitch for the final, unexpected outcome.
:::

Давайте подивимося, як використовувати ці слова на практиці. Уявіть таку ситуацію. Я прокинувся дуже пізно. Я зовсім не поснідав. Я дуже швидко побіг на роботу. На дорозі був великий затор. Я запізнився в офіс. Цей набір простих фраз звучить неприродно. Тепер ми об'єднаємо ці ідеї. «Хоча я прокинувся пізно, я встиг прийняти душ. Але я зовсім не поснідав вдома. Я побіг на роботу дуже швидко, тому що не хотів запізнитися. Проте я все одно приїхав пізно, бо на вулиці був затор». Цей новий текст має чудовий природний ритм. Він чудово показує причину, контраст і кінцевий результат.

> *Let us see how to use these words in practice. Imagine such a situation. I woke up very late. I did not have breakfast at all. I ran to work very fast. There was a big traffic jam on the road. I was late to the office. This set of simple phrases sounds unnatural. Now we will combine these ideas. "Although I woke up late, I managed to take a shower. But I did not have breakfast at home at all. I ran to work very fast, because I did not want to be late. However I still arrived late, because there was a traffic jam on the street." This new text has a wonderful natural rhythm. It perfectly shows cause, contrast, and the final result.*

<!-- INJECT_ACTIVITY: quiz-choose-the-correct-conjunction-to-complete-sentences -->
<!-- INJECT_ACTIVITY: fill-in-complete-compound-sentences-by-adding-the-missing-clause-after-the-conjunction -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: because-and-although
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

**Level: A2 (Module 47/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-syllables [§4.1.1, §4.1.4]
**Склад і складоподіл** (Syllables and syllable division)
- **divide-words** — Поділи слова на склади: Інтерактивний поділ на склади — натиснути між літерами для вставки дефіса / Interactive syllable division — tap between letters to insert hyphens
  - Instruction: *Поділіть слово на склади*
- **count-syllables** — Порахуй склади: Порахувати склади — кожен голосний = один склад (складотворчі голосні) / Count syllables — each vowel = one syllable (складотворчі голосні)
  - Instruction: *Скільки складів?*
- **pick-syllables** — Вибери закриті/відкриті склади: Визначити тип складу: відкритий (закінчується голосним) чи закритий (приголосним) / Classify syllables as відкритий (ends vowel) or закритий (ends consonant)
  - Instruction: *Оберіть усі закриті склади*
- **odd-one-out** — Четверте зайве: Обрати слово, що не пасує — за кількістю або типом складів / Pick the word that doesn't belong — by syllable count, type, or pattern
  - Instruction: *Яке слово зайве?*
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні навички поділу

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

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
