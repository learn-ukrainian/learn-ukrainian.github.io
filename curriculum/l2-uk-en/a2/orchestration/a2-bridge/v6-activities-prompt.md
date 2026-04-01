<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/a2-bridge.yaml` file for module **1: Ласкаво просимо до рівня А2** (a2).

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

- focus: Case Identification Drill
  items: 8
  type: quiz
- focus: Phonological Alternation Pairs
  items: 8
  type: fill-in
- focus: Euphony Choice Exercise
  items: 8
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- милозвучність (euphony, melodiousness)
- огляд (review, overview)
- система (system)
- правило (rule)
required:
- відмінок (case)
- називний (nominative)
- знахідний (accusative)
- місцевий (locative)
- кличний (vocative)
- чергування (alternation)
- голосний (vowel)
- приголосний (consonant)
- наголос (stress (accent))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пригадуємо відмінки (Reviewing Cases)

> — **Оксана Іванівна:** Добрий день! Сідайте, будь ласка. Як вас звати?
> — **Алекс:** Добрий день! Мене звати Алекс.
> — **Оксана Іванівна:** Дуже приємно, Алексе! Звідки ви?
> — **Алекс:** Я з Канади. Я з Торонто.
> — **Оксана Іванівна:** О, чудово! Скільки вам років?
> — **Алекс:** Мені двадцять п'ять.
> — **Оксана Іванівна:** А що ви вивчаєте?
> — **Алекс:** Я вивчаю українську мову. Я дуже хочу розмовляти вільно.
> — **Оксана Іванівна:** Прекрасно! А де ви зараз живете?
> — **Алекс:** Я живу в Києві. Вже два місяці.
> — **Оксана Іванівна:** Алексе, знаєте що? Ви вже використали чотири відмінки — просто не знаєте їхніх назв. Сьогодні ми це виправимо!

Did you notice what just happened? In this short conversation, Alex used four different **відмінки** (grammatical cases) without even realizing it. «Я з Канади» uses the genitive. «Мені двадцять п'ять» uses the dative. «Я вивчаю українську мову» uses the accusative. «Я живу в Києві» uses the locative. You already know more than you think — now it is time to give these patterns proper names.

Ukrainian nouns and adjectives change their endings depending on their role in the sentence. This process is called **відмінювання** (declension). Ukrainian has seven **відмінки** (cases) in total. During A1, you encountered four of them in everyday phrases — you just did not learn their formal names yet. Each case answers a specific pair of diagnostic questions — **Хто? Що?** (Who? What?) — and each one connects to particular **прийменники** (prepositions) or appears without any preposition at all. Mastering these questions is the key to identifying cases in real Ukrainian speech.

### Називний відмінок (Nominative — Хто? Що?)

The nominative is the **суб'єкт** (subject) case — it identifies who is doing the action or what simply exists. When you say «Студент читає книгу», the word «студент» is in the nominative because it answers the question **Хто читає?** Here are more examples:

- «Новий студент читає.» — A new student is reading.
- «Гарна книга лежить на столі.» — A beautiful book is lying on the table.
- «Велике місто живе.» — A big city lives.

Notice how adjectives agree with their nouns in gender: **новий** (masculine), **нова** (feminine), **нове** (neuter). The nominative is also the dictionary form of a noun — the form you look up when searching for a word. Gender determines the typical ending: «студент» (masculine, zero ending), «студентка» (feminine, ending -а), «місто» (neuter, ending -о). Whenever you need to find a word in a dictionary, you are looking for its nominative form.

### Знахідний відмінок (Accusative — Кого? Що?)

The accusative marks the **прямий об'єкт** (direct object) — the thing or person being acted upon. When you say «Я читаю книгу», the word «книгу» answers the question **Що я читаю?**

The rules for forming the accusative depend on gender and animacy:

- Feminine nouns take the ending -у or -ю: «книга → книгу», «кава → каву», «земля → землю», «Україна → Україну».
- Neuter nouns and masculine inanimate nouns look exactly like the nominative: «Я читаю лист», «Я п'ю молоко».
- For animate masculine nouns, the accusative looks like the genitive: «Я бачу студента», «Я знаю викладача».

You already used the accusative throughout A1 without knowing it. Think back to these familiar sentences:

- «Я вивчаю українську мову.» — I study the Ukrainian language.
- «Я п'ю каву.» — I drink coffee.
- «Я читаю книгу.» — I read a book.
- «Я люблю Україну.» — I love Ukraine. (feminine accusative)

The diagnostic question **Кого?** (Whom?) applies to people and animals. **Що?** (What?) applies to everything else.

### Місцевий відмінок (Locative — Де? На кому? На чому?)

The locative is the only case that never appears alone — it always requires a **прийменник** (preposition). The two most common prepositions are **в/у** (in, inside) and **на** (on, at):

- «в Києві» — in Kyiv
- «в університеті» — at the university
- «у школі» — in school
- «на уроці» — in a lesson
- «на концерті» — at a concert
- «на роботі» — at work

The ending pattern for nouns follows a general rule: hard stems take -і (місто → у місті, університет → в університеті), and soft stems also take -і or -ї (земля → на землі). Adjectives change too: «новий» becomes «у новому місті» (neuter/masculine), and «нова» becomes «у новій школі» (feminine). Whenever you describe where something is located, you are using the locative case.

### Кличний відмінок (Vocative — звертання)

The vocative case is used when you address someone directly — it is the case of **звертання** (direct address). You form it from the nominative:

- «Марія → Маріє!»
- «Тарас → Тарасе!»
- «Олексій → Олексію!»
- «Оксана → Оксано!»
- «Надія → Надіє!»

The basic patterns: masculine nouns with hard stems take -е (Тарасе); masculine nouns with soft stems take -ю (Олексію); feminine nouns ending in -а take -о (Оксано); feminine nouns ending in -я take -е (Маріє, Надіє).

Ukrainian uses the vocative where English simply uses the nominative. Compare: «Оксано, де ти?» means "Oksana, where are you?" — but Ukrainian changes the name itself. As the textbook puts it: «Сідайте, будь ласка, бабусю» (Заболотний, Grade 5) — even «бабуся» (grandmother) shifts to the vocative «бабусю» when you speak to her directly.

### Повна карта відмінків (The Full Case Map)

Now you can see all seven Ukrainian cases together. You already know the first four — the remaining three are your goal for A2:

1. **Називний** (Хто? Що?) — суб'єкт: who does the action.
2. **Знахідний** (Кого? Що?) — прямий об'єкт: what is acted upon.
3. **Місцевий** (Де? На кому? На чому?) — місце: location, always with a preposition.
4. **Кличний** (звертання) — адресат: the person you address directly.
5. **Родовий** (Кого? Чого?) — belonging, absence, origin. «Я з Канади» — you already used it!
6. **Давальний** (Кому? Чому?) — the recipient. «Мені двадцять п'ять» — you used this one too!
7. **Орудний** (Ким? Чим?) — instrument, accompaniment. How something is done or who accompanies.

Look back at the dialogue. «Я з Канади» uses the родовий. «Мені двадцять п'ять» uses the давальний. You have been touching these cases in real speech since A1 — A2 is where you learn to use them consciously and confidently.

Ви вже знаєте чотири. Три нових — це ваша ціль на рівні А2.

<!-- INJECT_ACTIVITY: quiz, Case Identification Drill — 8 items: identify which of the 4 A1 cases (називний, знахідний, місцевий, кличний) is used by an underlined noun, and which question it answers. Draw sentences from the dialogue and paragraphs: «Я вивчаю *українську мову*.» (знахідний — Що?), «Ми живемо *в Канаді*.» (місцевий — Де?), «*Маріє*, де твій зошит?» (кличний — звертання), «*Студент* читає книгу.» (називний — Хто?), «Я п'ю *каву*.» (знахідний — Що?), «Алекс живе *в Києві*.» (місцевий — Де?), «*Оксано*, добрий день!» (кличний — звертання), «*Книга* лежить на столі.» (називний — Що?) -->


## Магія української фонології (The Magic of Ukrainian Phonology)

Ukrainian phonology follows precise, systematic rules — what looks like an "exception" is almost always a pattern with a name. In A1, you may have noticed that «стіл» becomes «стола», or that «рука» becomes «ручка». These are not random changes. They follow two types of alternation: **чергування голосних** (vowel alternation) and **чергування приголосних** (consonant alternation). Once you understand these rules, you can predict forms you have never seen before. The same logic applies to **наголос** (stress) — it shifts within paradigms, and knowing the pattern means knowing the word.

### Чергування голосних: о/е → і (Vowel Alternation in Closed Syllables)

The core rule works like this: when a syllable becomes closed (ends in a consonant), the vowel **о** or **е** shifts to **і**. An **open syllable** ends in a vowel sound; a **closed syllable** ends in a consonant sound. Compare: «стіл» is one closed syllable — the vowel is **і**. But «стола» splits into two open syllables: «сто-ла» — so the vowel returns to **о**. The shift happens automatically based on the syllable structure of each form.

More pairs demonstrate the same pattern. «Ніж» (knife) has a closed syllable, so the vowel is **і**. Its genitive form «ножа» opens the syllable — back to **о**. Similarly: «кінь» (horse) / «коня», «лід» (ice) / «льоду». The test is straightforward: look at the genitive singular. If the syllable opens, you see **о** or **е** where the nominative has **і**.

Even proper nouns follow this rule. «Київ» has a closed final syllable with the vowel **и** (this is a different historical pattern), but the genitive «Києва» shows the syllable opening. Practice reading these minimal pairs aloud — the vowel shift is audible. «Ніж» sounds tighter and higher than «ножа». This alternation is one of the reasons Ukrainian sounds so melodic — the vowels shift to accommodate each word's shape.

### Більше чергувань голосних (More Vowel Alternations)

The same principle applies across the full paradigm. Take «стіл» through three cases: nominative «стіл» (closed syllable, **і**), genitive «стола» (open, **о**), locative «у столі» (the ending **-і** keeps the root vowel as **о** because the syllable splits differently — «сто-лі»). The locative ending **-і** is a reliable anchor: it appears consistently in this case.

Another set: «піч» (oven) / «печі», «сіль» (salt) / «солі». Here the pattern is **і → е** and **і → о** respectively when the syllable opens. «Ліс» (forest) keeps **і** in both nominative and genitive «лісу» — because the stress pattern is different. And «сік» (juice) / «соку» shows **і → о**. Not every word follows the identical direction, because some reflect different historical processes. But the practical question is always the same: before declining a word, ask yourself — is this syllable open or closed in the new form?

### Чергування приголосних: перша палаталізація (First Consonant Alternation: г/ж, к/ч, х/ш)

When certain suffixes follow the consonants **г**, **к**, or **х**, these consonants soften into their palatal counterparts: **г → ж**, **к → ч**, **х → ш**. You see this most clearly in diminutives. «Нога» (leg, foot) → «ніжка» (little foot): the root consonant **г** becomes **ж** before the diminutive suffix **-к-**. «Рука» (hand) → «ручка» (little hand, also: pen): **к → ч**. «Муха» (fly) → «мушка» (little fly): **х → ш**.

The same alternation appears in other word-formation contexts. When you see «ручка» in a text, you can immediately identify the root as «рука». When you encounter «книжечка» (little book), you know its base word is «книга» (book) — the **г** shifted to **ж** before the suffix. Recognizing these alternations turns what seems like an obstacle into a reading superpower: you can trace unfamiliar diminutives and derived forms back to their roots.

### Чергування приголосних у місцевому відмінку (Consonant Alternation in the Locative: г/з, к/ц, х/с)

A second type of consonant alternation appears specifically in the locative case. When the locative ending **-і** follows **г**, **к**, or **х**, they shift differently than in diminutives: **г → з**, **к → ц**, **х → с**. Compare: «книга» → «у книзі» (in a book), «рука» → «у руці» (in a hand), «вухо» (ear) → «у вусі» (in an ear).

More examples make the pattern unmistakable: «дорога» (road) → «на дорозі», «нога» → «на нозі», «аптека» (pharmacy) → «в аптеці», «потік» (stream) → «у потоці». This is why «у Луцьку» sounds different from the nominative «Луцьк» — the **к** shifts to **ц** before the locative **-і** ending.

Contrast the locative with the genitive, which keeps the original consonant untouched: «книги», «руки», «вуха». The summary rule is clean: locative **-і** triggers the second alternation; other case endings generally do not.

### Наголос як інструмент (Stress as a Tool)

Ukrainian stress is **вільний** (free) and **рухомий** (mobile) — it can fall on any syllable, and it can shift position within the same word's paradigm. This gives stress two important functions.

First, stress distinguishes words that are otherwise spelled identically. «Замок» with stress on the first syllable means "castle." «Замок» with stress on the second syllable means "lock." «Дорога» stressed on the first syllable is an adjective meaning "expensive" (feminine). «Дорога» stressed on the second syllable is a noun meaning "road."

Second, stress shifts within declension paradigms. «Вода» / «води» / «воду» — the stress moves from the ending to the root and back. «Земля» / «землі» — the same mobility. «Рука» / «руки» — stress jumps from the last syllable to the first. Mobile stress is one of the key reasons that stress dictionaries matter. You need to memorize the stress together with the word, not just the word's spelling. The Авраменко Grade 5 textbook includes a short stress dictionary listing over 200 commonly mispronounced words — a resource worth revisiting whenever you are uncertain.

### Система працює разом (The System Works Together)

These three systems — vowel alternation, consonant alternation, and stress — operate together on every Ukrainian word. When you encounter the locative form «у книзі», you can unpack it completely: the root is «книг-» (from «книга»), the consonant **г** shifted to **з** before the locative ending **-і**, and the stress stays on the root. Nothing about this form is arbitrary.

Every "strange" form in Ukrainian is a predictable output of phonological rules operating on a stem. The learner's task at A2 is not to memorize every individual form — that would be impossible. Instead, your goal is to internalize the rules so that the correct forms generate themselves. This is exactly how native speakers think about their language: not as a list of exceptions, but as a living system where sounds respond to structure.

«Ви вже знаєте правила. Тепер час їх використовувати.»

<!-- INJECT_ACTIVITY: fill-in, Phonological Alternation Pairs — 8 items: base form given (стіл, рука, книга, кінь, нога, піч, лід, дорога), learner fills in the specified declined form (genitive or locative) that triggers the alternation. Answers: стола, у руці, у книзі, коня, на нозі, у печі, льоду, на дорозі. -->


## Милозвучність мови: евфонія (The Melody of Language: Euphony)

The system you have just reviewed — alternations, stress shifts — keeps Ukrainian words internally consistent. But Ukrainian also has rules that govern what happens *between* words. These are called **правила милозвучності** (euphony rules), and their purpose is simple: prevent awkward clusters of consonants or vowels at word boundaries. The language has built-in sound variants for several common particles — **прийменники** (prepositions) and **сполучники** (conjunctions) — that automatically adjust depending on the sounds around them. You already follow many of these rules instinctively when speaking. Now we make the patterns explicit.

### У/В

The preposition meaning "in" or "at" has two forms: **у** and **в**. The choice depends on the sound that comes before and after.

After a vowel sound, use **в**: «Вона в університеті» (She is at the university), «Я живу в Канаді» (I live in Canada), «Він в Одесі» (He is in Odesa). The preceding word ends in a vowel, so **в** flows naturally.

After a consonant sound or at the start of a sentence, use **у**: «Студент у школi» (The student is at school), «У мене є питання» (I have a question), «Увечерi вiн читав» (In the evening he read). The consonant before the preposition needs a vowel buffer.

Special case: before words beginning with **в** or **ф**, always use **у** to avoid stacking two similar sounds: «У Вiнницi» (In Vinnytsia), «у фойє» (in the foyer).

Here is a real textbook example from Litvinova, Grade 5: «Нехай в ваших родинах панує злагода!» This sentence contains an error — the word «нехай» ends in the consonant sound й, so the correct form is «у ваших родинах». Spotting and correcting this kind of mistake is a practical skill you will use constantly.

### І/Й

The conjunction "and" also alternates. Between two consonant sounds, use **і**: «хлiб i масло» (bread and butter), «мати i батько» (mother and father), «зима i лiто» (winter and summer). After a vowel sound, use **й**: «книга й ручка» (book and pen), «Марiя й Тарас» (Maria and Taras), «кава й чай» (coffee and tea). At the start of a sentence, always use **і** regardless of what follows. The two forms mean exactly the same thing — the choice is purely phonetic.

### З/Зі/Із

The preposition "from" or "with" has three variants. Use **з** before most words: «з Києва» (from Kyiv), «з другом» (with a friend), «з молоком» (with milk). Use **зі** before difficult consonant clusters, especially words beginning with з, с, ш, or two or more consonants together: «зi школи» (from school), «зi Львова» (from Lviv), «зi мною» (with me), «зi студентами» (with students). The form **iз** is interchangeable with **з** in most contexts and appears more often in formal writing: «iз задоволенням» (with pleasure).

A practical test: say the phrase aloud. If the consonants pile up and the phrase feels clunky, switch to **зi**.

### Як це працює разом (How It Works Together)

Euphony rules apply in speech first, writing second. Read this sentence aloud: «Вiн в Харковi й у Одесi.» The first **в** is correct — «вiн» ends in a consonant н, but the н in «він» is actually followed by a vowel-like environment because the phrase is rapid speech; however, more precisely, «він» ends in a consonant, so this should be «у Харкові». Correction: «Він у Харкові й в Одесі.» Now **у** follows the consonant н, and **в** follows the vowel й. Read Ukrainian texts aloud daily, noticing where the alternations occur — making this automatic takes practice.

«Читайте вголос — вухо знає правила краще за очі.»

<!-- INJECT_ACTIVITY: match-up, Euphony Choice Exercise — 8 items: sentence frame with a blank, learner matches the correct particle (у or в / і or й / з or зі). Items cover all three alternation types. Examples: «Вона живе ___ Харкові.» (у) / «Марта ___ Іван прийшли.» (й) / «Він повернувся ___ школи.» (зі) -->


## Що нас чекає на рівні А2? (What Awaits Us in A2?)

The A2 level is built around four major themes, and they arrive in a deliberate sequence — each one unlocking new expressive power.

The first theme is **вид дієслова** (verbal aspect). Ukrainian verbs come in pairs: **доконаний вид** (perfective aspect) marks a completed action, while **недоконаний вид** (imperfective aspect) marks an ongoing or habitual one. Consider the pair **написати** (to write — completed) and **писати** (to write — ongoing), or **прочитати** (to read through — completed) and **читати** (to read — ongoing). Once you understand aspect, you can talk about past and future events with precision that English often leaves vague.

The second theme is **повна система відмінків** (the complete case system). In A1, you worked with four cases. A2 introduces the remaining three: **родовий** (genitive — possession, absence), **давальний** (dative — recipient, addressee), and **орудний** (instrumental — tool, accompaniment). These three cases are the backbone of fluent Ukrainian. You will learn to say «немає часу» (there is no time), «книга друга» (a friend's book), «дати другові» (to give to a friend), «телефонувати мамі» (to call mom), «писати ручкою» (to write with a pen), «йти з другом» (to go with a friend). Seven cases total — and by A2's end, you will use all of them.

The third theme is **дієвідмінювання** (verb conjugation) — learning the patterns that govern how verbs change by person and number, including common irregular verbs. The fourth is **дієслова руху** (verbs of motion): «іти» (to go on foot), «їхати» (to go by transport), «летіти» (to fly), and their prefixed variants that express direction, departure, and arrival.

In A1, your sentences lived in the present tense: «Я читаю книгу» (I am reading a book). That was enough to get started. At A2, the same thought branches into new directions. You will say: «Я прочитав книгу» (I read the book — perfective past, meaning you finished it). You will say: «Я читатиму книгу» (I will be reading a book — imperfective future, meaning the process will be ongoing). You will say: «Це книга мого друга» (This is my friend's book — genitive showing possession). You will say: «Я дав книгу другові» (I gave the book to my friend — dative marking the recipient). These are not just new grammatical forms — they are new thoughts. Each sentence expresses something you simply could not say at A1. This is where Ukrainian starts to feel like a language you can actually live in, not just survive in.

A1 equipped you with approximately 500 high-frequency words. By the end of A2, you will have encountered and practiced around 1,200 words — the threshold at which learners begin to handle simple authentic texts without constant dictionary lookups. Here is practical advice for right now: find a short Ukrainian children's story — a **казка** (fairy tale) — and read one paragraph per day. Do not translate word by word. Instead, notice what you already recognize. Every case ending you spot, every verb form that looks half-familiar — that is your A1 foundation working. By A2's end, you will fully understand every form you are now only glimpsing.

Рівень А2 — це кінець початку. You are leaving the stage where everything needs explaining and entering the stage where Ukrainian starts to explain itself. The three new cases, the aspect system, the motion verbs — they are not obstacles. They are tools. And like all good tools, once you learn to hold them, you will wonder how you ever managed without them. Ласкаво просимо до нового етапу.

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: a2-bridge
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

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: prompt. Optional: min_words, model_answer, evaluation_criteria[]
- **reading**: Required: passage, questions[]
- **source-evaluation**: Required: source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 1/60) — ELEMENTARY**

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
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
