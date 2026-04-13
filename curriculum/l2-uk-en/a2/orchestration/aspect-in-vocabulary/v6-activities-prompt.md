<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/aspect-in-vocabulary.yaml` file for module **3: Дієслова ходять парами** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-find-partner -->`
- `<!-- INJECT_ACTIVITY: match-up-fill-in-the-blanks-with-the-correct-pair -->`
- `<!-- INJECT_ACTIVITY: fill-in-categorize -->`
- `<!-- INJECT_ACTIVITY: fill-in-choose-partner -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Find the Partner (Verb Matching)
  items: 8
  type: quiz
- focus: Categorize by Formation Type
  items: 8
  type: fill-in
- focus: Fill in the Blanks with the Correct Pair
  items: 8
  type: match-up
- focus: Choose the Correct Aspect Partner
  items: 8
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- утворювати (to form)
- словник (dictionary)
- запам'ятовувати (to memorize)
- базовий (basic)
required:
- пара (pair)
- префікс (prefix)
- суфікс (suffix)
- корінь (root)
- читати / прочитати (to read)
- писати / написати (to write)
- брати / взяти (to take)
- говорити / сказати (to speak / to say)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Чому дієслова потрібно вчити парами? (Why Verbs Must Be Learned in Pairs) (~450 words)

Let's step into a traditional Ukrainian kitchen. A grandmother is teaching her granddaughter how to make authentic varenyky. Listen closely to the instructions. The grandmother uses different versions of the exact same verbs to explain the cooking process. 

> — **Бабуся:** Ліпи вареники, онучко. *(Keep forming the varenyky, granddaughter.)*
> — **Онучка:** Добре, я ліплю. А як правильно? *(Okay, I am forming them. But how do I do it right?)*
> — **Бабуся:** Дивись. Зліпи один вареник так, щоб тісто було разом. *(Look. Form one varenyk so that the dough is together.)*
> — **Онучка:** Зліпила! Що далі? *(I formed it! What is next?)*
> — **Бабуся:** Тепер вари їх у воді. Вари десять хвилин. *(Now boil them in water. Boil them for ten minutes.)*
> — **Онучка:** А як я дізнаюся, що вони готові? *(And how will I know that they are ready?)*
> — **Бабуся:** Коли звариш, вони будуть нагорі. *(When you have boiled them, they will be on top.)*

Did you notice the subtle difference in the grandmother's instructions? When she says «ліпи» and «вари», she is talking about the ongoing process of cooking. You are standing there, actively working with the dough or watching the boiling water. This is the imperfective aspect, or **недоконаний вид**. It focuses purely on the action itself.

Ми використовуємо недоконаний вид, коли говоримо про процес. Дія триває в часі, і ми не знаємо результату.

> *We use the imperfective aspect when we talk about a process. The action continues in time, and we do not know the result.*

However, when the grandmother says «зліпи» and «звари», she completely shifts the focus. She is no longer talking about the process, but the final, achieved result. You have successfully created one varenyk, or the boiling is finished. This is the perfective aspect, or **доконаний вид**. It focuses strictly on completion.

This brings us to the most important concept in Ukrainian verbs: the aspectual **пара** (pair). In English, you usually show the difference between a process and a result by changing the tense. You say "I was reading" for the process and "I have read" for the result. Ukrainian approaches this quite differently. Instead of using complex grammar tenses, Ukrainian uses pairs of verbs.

Кожне українське дієслово має свою пару. Одне дієслово описує процес, а інше дієслово показує результат.

> *Every Ukrainian verb has its pair. One verb describes the process, and the other verb shows the result.*

Because these verbs work together to describe different phases of the same action, learning a verb without its partner is like learning only half a word. You will always need both parts to communicate effectively in everyday situations.

:::info
**Grammar box** — The core difference always comes down to the question you ask. Imperfective verbs answer the question **що робити?** (what to be doing?). Perfective verbs answer the question **що зробити?** (what to get done?). Notice the tiny «з» at the start of the perfective question!
:::

How do you actually find and learn these pairs? Whenever you look up a verb in a **словник** (dictionary), you will usually see two words listed together. They are traditionally written side by side, with the imperfective form first and the perfective form second. For example, if you look up the word for "to do", you will find «робити / зробити».

Перше слово у словнику — це завжди базова форма. Зазвичай базова форма — це дієслово недоконаного виду.

> *The first word in the dictionary is always the basic form. Usually, the basic form is a verb of the imperfective aspect.*

The imperfective verb is considered the **базовий** (basic) form. It is the raw, pure name of the action. When you want to talk about completing that action, you reach for its perfective partner. Throughout your journey, you should always memorize both forms at the exact same time.

## Спосіб 1: Додавання префікса (Method 1: Adding a Prefix) (~650 words)

The first and most common way to form an aspectual **пара** (pair) is by adding a **префікс** (prefix) to the basic, imperfective verb. Think of it like adding a small grammatical tag to the very beginning of the word to announce, "This action is now successfully finished." This process is highly predictable in its structure, and once you start noticing these short additions, you will be able to recognize perfective verbs instantly in any text.

Найпоширеніший спосіб утворити доконаний вид — це просто додати префікс до базового слова. Коли ми додаємо цей префікс, ми миттєво змінюємо значення дієслова з тривалого процесу на конкретний результат.

> *The most common way to form the perfective aspect is simply to add a prefix to the basic word. When we add this prefix, we instantly change the meaning of the verb from a continuous process to a concrete result.*

The absolute most universal and frequent prefix you will encounter in the Ukrainian language is «по-». In a vast majority of cases, it simply flips the verb from a continuous process into a completed, singular action without changing its core, fundamental meaning at all. It is essentially the default tool the language reaches for to create a perfective partner when no other specific nuance is required.

Якщо ви не знаєте, який саме префікс потрібен новому слову, часто правильним і безпечним варіантом буде саме «по-». Наприклад, ми кажемо «думати», коли процес мислення триває, і «подумати», коли ми вже завершили цю дію. Інші дуже популярні пари — це «снідати» та «поснідати», а також «бачити» і «побачити».

> *If you do not know exactly which prefix a new word needs, often the correct and safe option will be exactly "по-". For example, we say "думати" (to think) when the process of thinking continues, and "подумати" when we have already finished this action. Other very popular pairs are "снідати" (to have breakfast) and "поснідати", as well as "бачити" (to see) and "побачити".*

Another extremely common and vital prefix for everyday communication is «з-». You already know the single most important verb pair that relies on this specific prefix: «робити» (to do or make) becomes «зробити» (to have successfully done or made). However, Ukrainian has a very strict and elegant phonetic rule for this prefix to make pronunciation much smoother and more natural. If the base verb starts with the consonants к, п, т, ф, or х, the voiced prefix «з-» automatically changes its sound and spelling to the voiceless «с-».

:::info
**Grammar box** — A helpful and famous memory trick for the «с-» rule is the phrase «Кафе Птах» (Cafe Bird). It contains exactly the five voiceless consonants (к, ф, п, т, х) that force the prefix «з-» to become «с-».
:::

Тому ми завжди кажемо і пишемо «зробити», але обов'язково «сфотографувати», бо це слово починається на літеру «ф». Ще одна надзвичайно важлива пара, яка ілюструє це фонетичне правило — це «казати» та «сказати».

> *Therefore we always say and write "зробити" (to do), but obligatorily "сфотографувати" (to photograph), because this word begins with the letter "ф". Another extremely important pair that illustrates this phonetic rule is "казати" (to say) and "сказати".*

When an action heavily involves reading, writing, or creating something entirely from scratch, you will frequently see the prefixes «про-» and «на-» attached to the root. These particular prefixes visually and logically signal the total completion of a text-based or creative process. The action has definitively moved from being an open-ended, ongoing activity to a finished, tangible product that you can now look at or share with others.

Коли ми активно працюємо з текстом або інформацією, ми зазвичай використовуємо пару **читати / прочитати**. Якщо ми створюємо щось нове на папері, ми використовуємо пару **писати / написати** або популярні слова «малювати» та «намалювати».

> *When we actively work with text or information, we usually use the pair **читати / прочитати** (to read). If we create something new on paper, we use the pair **писати / написати** (to write) or the popular words "малювати" (to draw) and "намалювати".*

For actions related to preparation, daily consumption, or deep learning, the language frequently relies on the prefixes «при-» and «ви-». The prefix «при-» often implies bringing something to a full state of readiness, while «ви-» frequently implies consuming something completely or extracting knowledge until the very end of the material.

Коли ми успішно готуємо смачну їжу, ми використовуємо пару «готувати» та «приготувати». Коли ми повністю споживаємо свій напій, ми кажемо «пити» і «випити». Для серйозного навчання ми маємо фундаментальну пару «вчити» і «вивчити».

> *When we successfully prepare delicious food, we use the pair "готувати" (to prepare) and "приготувати". When we completely consume our drink, we say "пити" (to drink) and "випити". For serious studying, we have the fundamental pair "вчити" (to learn) and "вивчити".*

To summarize this essential concept, simply adding a prefix is the absolute standard and most frequent method for turning an imperfective, ongoing process into a perfective, achieved result. While different verb families require different specific prefixes, they all serve the exact same underlying grammatical purpose when operating in these pairs. They proudly announce that the action is completely finished and the result is now ready.

Завжди намагайтеся запам'ятовувати нове дієслово одразу разом із його префіксом. Хоча різні префікси можуть іноді додавати невеликі логічні відтінки значення, їхня головна граматична мета тут — чітко показати фінальний результат вашої дії.

> *Always try to memorize a new verb immediately together with its prefix. Although different prefixes can sometimes add small logical nuances of meaning, their main grammatical goal here is to clearly show the final result of your action.*

<!-- INJECT_ACTIVITY: quiz-find-partner -->

## Спосіб 2: Зміна в корені або суфіксі (Method 2: Change in the Root or Suffix) (~650 words)

While adding a prefix is the most popular way to build a perfective verb, it is not the only method. Sometimes, the language takes a different approach. Instead of building a perfective verb from an imperfective one, we take a verb that is already perfective—often one that already has a prefix—and we make it imperfective. We do this by changing the **суфікс** (suffix) at the end of the word or by slightly altering the **корінь** (root) in the middle. This "reverse" pattern allows us to take a one-time, completed action and stretch it out into a continuous, ongoing process.

Цей другий спосіб спочатку здається трохи незвичним, але він дуже логічний. Ми беремо готовий результат і перетворюємо його на довгий процес. Для цього ми змінюємо кінець слова або голосний звук у центрі.

> *This second method seems a bit unusual at first, but it is very logical. We take a ready result and turn it into a long process. To do this, we change the end of the word or the vowel sound in the center.*

The most recognizable tool for this transformation is the addition of the suffixes «-ува-» or «-юва-». When you see these letters expanding the end of a verb, they almost always signal a continuous, imperfective process. A classic example is the verb for making a decision. The perfective form «вирішити» means to decide something once and for all—a quick, mental click. But if you are currently weighing your options and thinking about what to do, you add the suffix to stretch the action into «вирішувати» (to be deciding).

Коли ми використовуємо суфікс «-ува-», дія стає довгою і повільною. Ми можемо вирішувати складну проблему цілий тиждень. Або ми можемо вирішити її за одну хвилину, коли нарешті знаємо правильну відповідь.

> *When we use the suffix "-ува-", the action becomes long and slow. We can be solving a complex problem for a whole week. Or we can solve it in one minute, when we finally know the correct answer.*

Let us look at another highly practical example involving communication. The perfective verb «запитати» means to ask a single question and get it over with. It is a quick, completed action. However, if a journalist is interviewing someone or a curious child is bombarding their parents with questions all day, the action is continuous. To express this ongoing questioning, we change the suffix and use the imperfective verb «запитувати» (to be asking). The core meaning of seeking information remains exactly the same, but the aspect dramatically shifts from a single event to a steady flow.

Маленькі діти дуже люблять запитувати дорослих про все на світі. Вони можуть запитувати про сонце, небо і дерева кожного дня. А іноді дитина хоче запитати тільки одну просту річ перед сном.

> *Small children really love to ask adults about everything in the world. They can be asking about the sun, the sky, and trees every day. And sometimes a child wants to ask just one simple thing before sleep.*

In addition to changing the suffix, Ukrainian verbs frequently undergo a vowel alternation in the root. The most common internal shift you will encounter is the vowel «о» changing to the vowel «а». This internal stretch visually and phonetically mirrors the stretching of the action itself. Consider the essential verb for helping. The perfective form «допомогти» implies a single, successful act of assistance. To turn this into regular, ongoing help, the «о» in the root opens up into an «а», giving us the imperfective form «допомагати».

Хороший друг завжди готовий допомагати у важкі часи. Він допомагає регулярно і не чекає нагороди. Але якщо вам потрібна термінова дія саме зараз, ви просите його допомогти сьогодні ввечері.

> *A good friend is always ready to help in difficult times. He helps regularly and does not wait for a reward. But if you need an urgent action right now, you ask him to help tonight.*

:::info
**Grammar box**
When a verb root changes from «о» to «а» (like допомогти → допомагати), the wider «а» sound naturally takes longer to pronounce. This phonetic stretching perfectly matches the grammatical shift from a quick result to a continuous process!
:::

Sometimes, these suffix changes create pairs that look a bit irregular but are absolutely essential for daily conversation. A perfect example is the verb for answering. If you want to describe the process of giving an answer or being responsible for something, you use the imperfective verb «відповідати». But when you want to focus on the exact moment the answer is given, the ending changes completely, creating the perfective partner «відповісти». Because these words are used so frequently in classrooms and daily life, it is best to memorize them as a set package.

Учитель часто просить студентів відповідати на питання під час уроку. Студенти відповідають по черзі і тренують свої навички. Якщо студент знає матеріал добре, він може відповісти дуже швидко і правильно.

> *The teacher often asks students to answer questions during the lesson. The students answer in turn and practice their skills. If a student knows the material well, he can answer very quickly and correctly.*

To keep these two main methods organized in your mind, think about the direction of the change. Method 1 builds the perfective form by adding a prefix to a basic imperfective base (робити → зробити). It moves from process to result. Method 2 does the exact opposite. It builds the imperfective form by changing the suffix or root of a prefixed perfective base (вирішити → вирішувати). It moves from a completed result back into a continuous process. Both methods achieve the same goal: giving you a matched pair of verbs to express both the journey and the destination of an action.

<!-- INJECT_ACTIVITY: match-up-fill-in-the-blanks-with-the-correct-pair -->

## Спосіб 3: Зовсім інші слова (суплетивізм) (Method 3: Completely Different Words) (~550 words)

So far, you have seen verbs that share obvious family resemblances. You take a basic verb and add a **префікс** (prefix) to create a perfective result. Or, you start with a perfective verb and change its **суфікс** (suffix) or the vowel in its **корінь** (root) to stretch it back into a continuous process. However, some of the oldest and most basic actions in the Ukrainian language do not follow these neat grammatical rules. They form an aspectual pair using two completely different words. This grammatical phenomenon is known as suppletion. You simply have to memorize these pairs as single units of meaning because they do not look alike at all.

Учора я брав книгу в бібліотеці, але не пам'ятаю, де вона. Сьогодні мій брат взяв мою книгу і поклав її на стіл.

> *Yesterday I was taking a book at the library, but I do not remember where it is. Today my brother took my book and put it on the table.*

Our first essential suppletive example is the verb pair **брати / взяти** (to take). The imperfective form «брати» describes the ongoing process, habit, or an attempt to take something. The perfective form «взяти» describes the successful, completed action of having taken the item. You will hear both of these words constantly in everyday conversation, from borrowing items to participating in events. This combination is completely different from predictable verbs like **читати / прочитати** (to read) or **писати / написати** (to write), where the original word remains clearly visible. With suppletive verbs, there are absolutely no structural hints to help you guess the perfective form.

The second crucial **пара** (pair) to learn right now is **говорити / сказати** (to speak / to say). This set perfectly illustrates the difference between an ongoing activity and a single, finalized message. The imperfective verb «говорити» focuses entirely on the process of talking, chatting, or holding a conversation. It is an activity that takes time. The perfective verb «сказати» focuses strictly on the delivery of a specific statement or piece of information. You cannot use the perfective form to describe a long conversation, just as you cannot use the imperfective form to report a single, sharp command.

Мама любить довго говорити по телефону зі своєю сестрою. Вона хотіла сказати мені важливу новину, але забула.

> *Mom likes to speak on the phone for a long time with her sister. She wanted to say an important piece of news to me, but she forgot.*

:::info
**Grammar box**
When you use the verb «говорити», the listener expects to hear about a dialogue or a speech that lasted for a while. When you use «сказати», the listener immediately expects to hear the exact words or the main point that was delivered.
:::

There are a few other common suppletive pairs that you should add to your vocabulary list immediately. For example, the action of catching something is expressed by the pair «ловити» and «піймати». You might spend all morning trying to catch a fish, but you only experience the actual success for a single moment. Similarly, the physical action of putting or placing an object horizontally uses the irregular pair «класти» and «покласти». These verbs are so fundamental to navigating daily life that you simply have to **запам'ятовувати** (to memorize) them right now, which will make your future interactions much smoother and more natural.

Діти люблять ловити м'яч у парку. Вчора мій син нарешті зміг піймати великий м'яч самостійно.

> *Children like to catch a ball in the park. Yesterday my son was finally able to catch a big ball independently.*

Finally, we must warn you about a very common false pair trap that confuses many learners. The imperfective verb «шукати» means to search or to look for something. The perfective verb «знайти» means to find something. Because searching and finding are logically connected in our minds, these two verbs are often taught together as a related sequence of events. However, they are not a true grammatical pair. The actual perfective partner for the first verb is «пошукати» (to search for a bit), while the imperfective partner for the second verb is «знаходити» (to be finding).

Я довго шукав свої ключі у кімнаті. Я радий, що нарешті знайшов їх під ліжком.

> *I searched for my keys in the room for a long time. I am glad that I finally found them under the bed.*

<!-- INJECT_ACTIVITY: fill-in-categorize -->
<!-- INJECT_ACTIVITY: fill-in-choose-partner -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: aspect-in-vocabulary
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

**Level: A2 (Module 3/60) — ELEMENTARY**

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
