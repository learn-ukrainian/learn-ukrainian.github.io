<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/sviy-and-sebe.yaml` file for module **56: Своє та себе** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-sviy-vs-possessive -->`
- `<!-- INJECT_ACTIVITY: true-false-sviy-cases -->`
- `<!-- INJECT_ACTIVITY: fill-in-insert-the-correct-case-form-of -->`
- `<!-- INJECT_ACTIVITY: match-up-match-expressions-with-to-their-meanings -->`
- `<!-- INJECT_ACTIVITY: error-correction-find-and-fix-incorrect-usage-of-and -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose свій or мій/його/її based on sentence context
  items: 8
  type: quiz
- focus: Insert the correct case form of себе (себе, собі, собою)
  items: 8
  type: fill-in
- focus: Identify whether свій is used correctly in each sentence
  items: 8
  type: true-false
- focus: Match expressions with себе to their meanings
  items: 8
  type: match-up
- focus: Find and fix incorrect usage of свій and себе (e.g., *Він читає його книгу
    when meaning his own → свою, *Я почуваю себе when missing adverb)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- власний (own, one's own)
- самостійно (independently)
- звичка (habit)
- щоденний (daily)
required:
- свій (one's own)
- себе (oneself, accusative/genitive)
- собі (oneself, dative)
- собою (oneself, instrumental)
- почувати себе (to feel)
- вести себе (to behave)
- горджуся (I am proud)
- уявити (to imagine)
- дзеркало (mirror)
- парасолька (umbrella)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Свій: чий саме? (Свій: Whose Exactly?) (~660 words)

While English uses possessive pronouns like "my" or "his" to show ownership, Ukrainian features a unique, universal possessive pronoun, **свій** (one's own), which changes its meaning depending on who is performing the action in the sentence.

Українська мова має особливе слово для позначення власності. Цей цікавий займенник є абсолютно унікальним. Він ніколи не прив'язаний до однієї конкретної граматичної особи. Він динамічно змінює своє значення залежно від виконавця головної дії. Ми використовуємо його спеціально. Так ми чітко показуємо, що людина також є справжнім власником цього предмета. Коли я особисто роблю якусь дію, я обов'язково використовую це коротке слово. Наприклад, я зараз сиджу вдома на зручному дивані. Я із задоволенням читаю дуже цікаву книгу. Це моя власна книга, яку я купив учора у великому книжковому магазині. Тому я дуже впевнено кажу: «Я читаю свою книгу». У цьому простому реченні слово «свій» чітко показує співрозмовнику єдиного власника. Цей власник предмета — це саме я. Це звучить дуже природно і є золотим стандартом для сучасної української мови.

:::info
**Grammar box**
The core grammatical rule of **свій** is strict: it replaces the regular possessive pronouns ONLY when the possessor of the object is also the grammatical subject of the sentence. If the owner is NOT the subject, you must use regular pronouns (**його**, **її**, etc.) instead.
:::

Наша мова має надзвичайно чітке та дуже строге правило для цього важливого займенника. Ми завжди вживаємо слово «свій», коли фактичний власник предмета виступає як підмет. Підмет — це завжди найголовніша особа, яка активно і самостійно виконує дію. Давайте дуже уважно подивимося на велику різницю між двома схожими життєвими ситуаціями. Молодий хлопець сидить у тихій бібліотеці і зосереджено читає власну книгу. Він приніс цю книгу з дому. Тоді ми впевнено кажемо: «Він читає свою книгу». Тут він одночасно є і активним читачем, і повноправним власником. Але іноді він несподівано бере і читає книгу свого найкращого друга. Тоді ми повинні сказати зовсім інакше: «Він читає його книгу». Тут діяч і справжній власник — це дві абсолютно різні людини.

Чому це граматичне правило таке неймовірно важливе для правильного розуміння? Тому що в третій особі це маленьке слово допомагає нам уникати дуже серйозної плутанини. Українська мова завжди вимагає від нас максимальної точності у повсякденному спілкуванні. Давайте детально розглянемо класичний і дуже яскравий приклад із реального життя. Речення «Він любить свою дружину» має дуже добрий і світлий зміст. Воно прямо означає, що цей чоловік щиро кохає власну законну дружину. Це дуже правильно і цілком логічно для кожної щасливої сім'ї. А от інше речення «Він любить його дружину» має величезну проблему. Воно означає, що він палко кохає дружину якогось іншого, чужого чоловіка! Як ви можете легко побачити, це вже зовсім інша, скандальна історія. Тільки одне маленьке слово повністю і назавжди змінює весь сенс вашої короткої фрази.

Отже, для першої та другої особи наше золоте правило насправді не таке суворе. Воно дозволяє нам мати певну приємну свободу у виборі правильних слів. Ви маєте повне право впевнено сказати «я читаю мою улюблену книгу». Або ви можете сказати «я читаю свою улюблену книгу». Обидва ці варіанти абсолютно правильні. Але саме другий варіант завжди звучить набагато більш природно і красиво для носіїв мови. Те саме просте правило стосується коротких слів «ти», «ми» і «ви». Ви можете вільно обирати те, що вам зараз найбільше подобається. Але для займенників «він», «вона», «воно» і «вони» цей граматичний вибір дуже строгий. Ви просто зобов'язані завжди вживати слово «свій», якщо якась річ належить підмету. Це надійна базова норма нашої мови, яку ніколи не можна свідомо порушувати.

### Читаємо українською (Reading Practice)

Спробуйте зараз яскраво **уявити** (to imagine) типовий, дуже галасливий ранок у великій родині. Коли вдома збирається такий шалений хаос, буває неймовірно важко **почувати себе** (to feel) дійсно спокійно. Маленькі діти часто дуже сильно поспішають до своєї школи. Вони зовсім не вміють **вести себе** (to behave) тихо в такий ранній час доби. 

Старший брат і молодша сестра постійно не можуть швидко поділити свій щоденний теплий одяг. Вони сваряться через великі шкільні сумки та навіть таку річ, як сімейна **парасолька** (umbrella). Звісно, я дуже сильно **горджуся** (I am proud) своєю великою родиною. Я пишаюся **собою** (oneself, instrumental), коли мені вдається всіх швидко і мирно помирити. Але іноді ми досить гучно сваримося через звичайні щоденні побутові дрібниці. У цій складній ситуації дуже важливо щодня чітко розуміти, де саме чия річ зараз лежить. Мама зазвичай намагається їх дуже швидко заспокоїти і зупинити цей конфлікт.

> — **Брат:** Це мій новий теплий светр! Негайно віддай його мені зараз! *(This is my new warm sweater! Give it back to me immediately now!)*
> — **Сестра:** Ні, він точно мій! Я особисто купила його **собі** (oneself, dative) сама вчора у великому магазині! *(No, it's definitely mine! I personally bought it for myself yesterday at the big store!)*
> — **Мама:** Будь ласка, заспокойтеся! Вона взяла свою власну сумку, а зовсім не твою. А він взагалі нас не слухає і просто мовчки дивиться на **себе** (oneself, accusative) у велике **дзеркало** (mirror). *(Please, calm down! She took her own bag, not yours at all. And he isn't listening to us at all and is just silently looking at himself in the large mirror.)*

<!-- INJECT_ACTIVITY: quiz-sviy-vs-possessive -->

## Свій у відмінках (Свій in All Cases) (~500 words)

The pronoun **свій** behaves grammatically just like a regular adjective in the Ukrainian language. This means it must constantly adapt its form to match the noun it describes. It declines exactly like the possessive pronouns **мій** and **твій**, sharing the very same pattern of endings. The most critical rule to remember is that **свій** always agrees in gender, number, and case with the object that is possessed, absolutely never with the person who actually owns it. If a man is reading his own book, the pronoun must match the feminine noun for book, completely ignoring the masculine subject of the sentence. This agreement system guarantees that your sentences remain grammatically connected and clear.

Чоловічий та середній роди мають дуже схожі форми у багатьох відмінках. Називний відмінок чоловічого роду — це завжди слово «свій», а середнього — слово «своє». У родовому відмінку обидва ці роди мають однакову форму «свого». Давальний відмінок також є спільним і має єдину форму «своєму». Знахідний відмінок для чоловічого роду може бути «свій» або «свого», залежно від того, чи є цей об'єкт живим. Для середнього роду це завжди форма «своє». Орудний відмінок для обох родів використовує однакову форму «своїм». У місцевому відмінку ми зазвичай кажемо «на своєму» або просто «на своїм». Наприклад, я щиро горджуся своїм рідним містом і його довгою історією. Він часто думає про свого молодшого брата, коли працює далеко від дому.

Жіночий рід та множина мають свої власні дуже чіткі закінчення, які варто добре запам'ятати. Називний відмінок жіночого роду — це завжди форма «своя». У родовому відмінку ми використовуємо красиве слово «своєї». Давальний відмінок вимагає форми «своїй». Знахідний відмінок дуже легко впізнати за типовим закінченням у слові «свою». Орудний відмінок використовує форму «своєю», а місцевий відмінок знову повертається до форми «на своїй». Множина для всіх без винятку родів починається зі слова «свої». Далі йдуть форми «своїх» для родового відмінка, «своїм» для давального відмінка, «своїми» для орудного відмінка та «на своїх» для місцевого відмінка. Вона завжди охоче допомагає своїй молодшій сестрі робити складні завдання. Він з великим задоволенням розповів усім про свою нову родину.

> *The feminine gender and plural have their own very clear endings that are worth remembering well. The nominative case of the feminine gender is always the form "своя". In the genitive case, we use the beautiful word "своєї". The dative case requires the form "своїй". The accusative case is very easy to recognize by the typical ending in the word "свою". The instrumental case uses the form "своєю", and the locative case returns again to the form "на своїй". The plural for all genders without exception begins with the word "свої". Then come the forms "своїх" for the genitive case, "своїм" for the dative case, "своїми" for the instrumental case, and "на своїх" for the locative case. She always willingly helps her younger sister do difficult tasks. He talked to everyone with great pleasure about his new family.*

Українська мова має багато цікавих сталих виразів, де це коротке слово відіграє дуже важливу роль. Ми часто впевнено кажемо, що кожна подія обов'язково відбудеться **у свій час**, коли ми просто чекаємо правильного моменту. Кожна доросла людина повинна завжди мати **свою думку** про важливі події у світі. Дуже важливо колись успішно **знайти своє місце** у цьому великому суспільстві і бути дійсно корисним. Коли ми зустрічаємо старих надійних друзів, ми радісно кажемо, що це **свої люди**. Ці популярні фрази роблять нашу щоденну розмову набагато багатшою, красивішою та значно більш природною для всіх слухачів.

:::info
**Grammar box** — Always remember the golden rule: the noun that is possessed entirely dictates the ending of **свій**. You must carefully check the gender, number, and case of that noun before you decline the pronoun. The gender or identity of the owner is completely irrelevant to how this pronoun changes its form.
:::

<!-- INJECT_ACTIVITY: true-false-sviy-cases -->

## Себе: зворотний займенник (Себе: The Reflexive Pronoun) (~600 words)

In the beautiful structure of the Ukrainian language, we have a highly useful word that acts exactly like a grammatical mirror. The reflexive pronoun **себе** (oneself, accusative/genitive) reflects an action directly back to the subject of the sentence. Its absolute defining grammatical feature is that it completely lacks a Nominative form. It can never be the main actor of a sentence. Instead, it only exists to show that the doer and the receiver of the action are the exact same person. You will see it very often when someone looks into a **дзеркало** (mirror). This small, powerful word completely replaces the need to say "myself", "yourself", "himself", or "themselves". It adapts effortlessly to whoever is currently speaking.

Цей зворотний займенник має одну дуже приємну особливість для всіх студентів. Він ніколи не змінює свою форму для різних осіб, родів чи чисел. Це коротке слово залишається абсолютно однаковим, коли ми говоримо про мене, тебе чи них. У родовому та знахідному відмінках ми використовуємо форму «себе». Давальний та місцевий відмінки завжди вимагають дуже м'якої форми «собі». Орудний відмінок має свою єдину незмінну форму «собою». Тобі більше не потрібно вчити довгі таблиці закінчень для кожної окремої особи.

> *This reflexive pronoun has one very pleasant feature for all students. It never changes its form for different persons, genders, or numbers. This short word remains absolutely the same when we talk about me, you, or them. In the genitive and accusative cases, we use the form "sebe". The dative and locative cases always require the very soft form "sobi". The instrumental case has its single unchangeable form "sobou". You no longer need to learn long tables of endings for each individual person.*

Let's look much closer at how the Genitive and Accusative forms operate in everyday Ukrainian speech. Because these two cases share the exact same identical form, you will hear it constantly in direct object situations. If you want to say "I see myself", you simply use the Accusative case directly after the active verb. It clearly shows who is receiving the action. When you decide to buy a necessary item for your own benefit, you will frequently use the Genitive case. This is almost always paired with the common preposition "для".

:::info
**Grammar box** — The reflexive pronoun is universally identical for all possible subjects in a sentence. "Я бачу себе" (I see myself), "Ти бачиш себе" (You see yourself), and "Він бачить себе" (He sees himself) all use the exact same word without any modifications.
:::

Давальний відмінок звучить як «собі». Ми дуже часто використовуємо це слово, коли робимо щось корисне для власної вигоди. Наприклад, мій старший брат вчора купив собі велику чашку смачної кави. Також ми можемо просто взяти цей новий зошит собі для цікавої роботи. Орудний відмінок звучить як «собою». Моя найкраща подруга завжди радіє і дуже пишається собою після складного іспиту. Це дуже природний і традиційний спосіб щиро говорити про власні емоції щодня.

> *The dative case sounds like "sobi". We very often use this word when we do something useful for our own benefit. For example, my older brother bought himself a large cup of delicious coffee yesterday. Also, we can simply take this new notebook for ourselves for interesting work. The instrumental case sounds like "sobou". My best friend always rejoices and is very proud of herself after a difficult exam. This is a very natural and traditional way to sincerely talk about one's own emotions every day.*

To truly master natural Ukrainian, you must learn several fixed expressions that rely on these reflexive forms. The dative form is **собі** (oneself, dative), and the instrumental form is **собою** (oneself, instrumental). For instance, to ask how someone is physically doing, we use the phrase **почувати себе** (to feel). When teachers talk about children, they often discuss how well they **вести себе** (to behave). If you do well on a test, you might say **горджуся** (I am proud) to express satisfaction with yourself. Sometimes you just need to **уявити** (to imagine) a situation, which typically takes the dative reflexive form. Also, don't forget to take your **парасолька** (umbrella) with you when it rains! Interestingly, the common reflexive verb suffix "-ся" historically evolved directly from this exact pronoun. Words ending in "-ся" literally mean the action is directed right back at the speaker.

<!-- INJECT_ACTIVITY: fill-in-insert-the-correct-case-form-of -->
<!-- INJECT_ACTIVITY: match-up-match-expressions-with-to-their-meanings -->

## Свій та себе у мовленні (Свій and Себе in Speech) (~440 words)

Using reflexive and possessive pronouns correctly is the secret to sounding natural and idiomatic in daily storytelling. The base possessive form **свій** (one's own) helps you connect actions directly to yourself without sounding repetitive. Let's look at a short reading text about a typical morning routine. This will show you exactly how these pronouns operate in a continuous, realistic context before you look into a **дзеркало** (mirror) and start your day.

Я прокидаюся рано і відразу готую собі смачний сніданок. Потім я швидко збираю свої речі. Я завжди беру свою парасольку, бо погода мінлива. Я йду на свою роботу пішки, бо люблю гуляти. Я почуваю себе добре, коли все йде за планом. Я дивлюся на себе у велике дзеркало перед виходом. Я горджуся собою, коли встигаю зробити всі важливі справи.

> *I wake up early and immediately prepare a delicious breakfast for myself. Then I quickly gather my things. I always take my umbrella because the weather is changeable. I walk to my job because I love walking. I feel good when everything goes according to plan. I look at myself in the large mirror before leaving. I am proud of myself when I manage to do all important tasks.*

Now we need to address typical direct-translation mistakes. English speakers often make predictable errors when translating phrases word-for-word into Ukrainian. First, remember the strict rule about possession and the direct object form **себе** (oneself, accusative/genitive).

Якщо ви кажете «він любить його дружину», це має інше значення. Це означає, що він любить дружину іншого чоловіка. Правильно казати «він любить свою дружину». Також ми не можемо просто сказати «я почуваю себе». Це речення є неповним. Нам потрібен прислівник, щоб показати стан. Можна сказати «я почуваю себе добре» або «погано».

> *If you say "he loves his wife" (using "yogo"), it has a different meaning. It means that he loves another man's wife. It is correct to say "he loves his own wife". Also, we cannot simply say "I feel myself". This sentence is incomplete. We need an adverb to show the state. You can say "I feel good" or "bad".*

The third common mistake involves the English word "myself" when it implies doing something without help. In Ukrainian, you cannot use the reflexive pronoun for this specific meaning. 

Неправильно казати «я зробив це себе». Чоловік повинен сказати «я зробив це сам». Жінка повинна сказати «я зробила це сама». Діти також часто кажуть батькам, що хочуть вести себе добре. Вони хочуть робити всі складні речі самі. Завжди важливо розуміти цей контекст.

> *It is incorrect to say "I did this myself" (using "sebe"). A man must say "I did this myself" (using "sam"). A woman must say "I did this myself" (using "sama"). Children also often tell their parents that they want to behave well. They want to do all difficult things themselves. It is always important to understand this context.*

:::info
**Grammar box** — Do not confuse the reflexive pronoun with the word **сам** (oneself / alone). Use the reflexive pronoun when an action reflects back to you, like looking in a mirror. Use **сам** or **сама** when you do something independently without any help.
:::

Finally, let's see a conversational dialogue demonstrating how these pronouns flow between two friends discussing their habits.

> — **Олена:** Я завжди беру з собою парасольку. А ти? *(I always take an umbrella with me. And you?)*
> — **Тарас:** А я довіряю своїй інтуїції і почуваю себе чудово. *(And I trust my intuition and feel great.)*
> — **Олена:** Я теж завжди намагаюся вести себе добре. *(I also always try to behave well.)*
> — **Тарас:** Я дивлюся на себе у дзеркало і горджуся собою. *(I look at myself in the mirror and I am proud of myself.)*
> — **Олена:** Чи можеш ти уявити собі такий ідеальний день? *(Can you imagine such a perfect day?)*

<!-- INJECT_ACTIVITY: error-correction-find-and-fix-incorrect-usage-of-and -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: sviy-and-sebe
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

**Level: A2 (Module 56/60) — ELEMENTARY**

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

### Pattern: grammar-possession [§4.2.1.4, §4.2.2]
**Присвійність** (Possession)
- **fill-in** — У мене є...: Структура «У мене/тебе/нього є...» — як українська виражає володіння / Structure «У мене/тебе/нього є...» — how Ukrainian expresses possession
  - Instruction: *Вставте правильне слово*
- **fill-in** — Мій, твій, наш...: Обрати присвійний займенник, що узгоджується з родом та числом іменника / Choose possessive pronoun matching noun gender and number
  - Instruction: *Вставте правильну форму*
- **match-up** — Чий? Чия? Чиє?: Зіставити присвійний займенник з іменником за родом / Match possessive pronoun to noun by gender
  - Instruction: *З'єднайте*
- **quiz** — У кого є?: Визначити, хто має щось, за контекстом речення / Determine who has something based on sentence context
**Anti-patterns (DO NOT generate):**
- ❌ translate: «У мене є» — унікальна українська структура. Переклад з англ. «I have» маскує різницю


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
