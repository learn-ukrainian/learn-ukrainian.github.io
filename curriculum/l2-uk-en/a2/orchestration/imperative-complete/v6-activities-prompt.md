<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/imperative-complete.yaml` file for module **44: Хай він прочитає!** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->`
- `<!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->`
- `<!-- INJECT_ACTIVITY: match-up-vocative-wishes -->`
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`
- `<!-- INJECT_ACTIVITY: unjumble-imperative-sentences -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the correct imperative — 3rd person with хай/нехай or 1st plural with
    -мо — from given infinitives
  items: 8
  type: fill-in
- focus: Choose the correct aspect (imperfective or perfective) for imperatives in
    various situations (general advice vs. specific command)
  items: 8
  type: quiz
- focus: Match Vocative + imperative + Instrumental combinations to create correct
    wishes (Оленко + будь + щасливою)
  items: 8
  type: match-up
- focus: Reorder words to form correct imperative sentences — commands, suggestions
    with -мо, and wishes with Vocative + будь + Instrumental
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- спокійний (calm)
- уважний (attentive)
- живи (live — imperative)
- здійснитися (to come true)
- мрія (dream)
required:
- хай (let — particle for 3rd person imperative)
- нехай (let — formal variant)
- наказовий спосіб (imperative mood)
- побажання (wish, blessing)
- кличний відмінок (Vocative case)
- будь / будьте (be — imperative of бути)
- щасливий / щасливою (happy / happy — Instr.f.)
- здоровий / здоровими (healthy / healthy — Instr.pl.)
- ходімо (let's go)
- давайте (let's — suggestion particle)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Хай і нехай: Наказ для третіх осіб (3rd Person Imperatives) (~600 words)

> — **Шеф-кухар:** Увага, шановні учні! Наріжте цибулю дуже дрібно. *(Attention, dear students! Chop the onion very finely.)*
> — **Максим:** Я вже нарізав. Що робити далі? *(I have already chopped it. What to do next?)*
> — **Шеф-кухар:** Тепер хай вода закипить у великій каструлі. *(Now let the water boil in a large pot.)*
> — **Оксана:** Вода вже кипить, шефе! *(The water is already boiling, chef!)*
> — **Шеф-кухар:** Чудово. Помішаймо соус разом. Нехай соус настоїться рівно п'ять хвилин. *(Excellent. Let's stir the sauce together. Let the sauce infuse for exactly five minutes.)*
> — **Учасники класу:** Так, шефе! Ми все зрозуміли. *(Yes, chef! We understood everything.)*

Ukrainian grammar has a specific and elegant way to give indirect commands, grant permissions, or express wishes directed at a third party. While direct commands are given to the person you are currently talking to, third-person imperatives express what you want someone else or even an inanimate object to do. You form this **наказовий спосіб** (imperative mood) using the special particles **хай** (let) or **нехай** (let) followed immediately by a verb in the third person. You will use either the present tense form for ongoing actions or the future perfective form of the verb for completed results.

Хай він читає цей довгий текст. Нехай вона прочитає його до кінця сьогодні. Хай вони працюють швидше.

> *Let him read this long text. Let her read it through to the end today. Let them work faster.*

The two particles function exactly the same way in a sentence, but they carry a slight stylistic difference that is good to know. The word **нехай** is slightly more formal and is often found in classical literature, official speeches, or older historical texts. The shorter variant **хай** is extremely common in everyday modern speech, casual conversations, and text messages between friends. Both are perfectly correct, and you can interchange them freely without changing the grammar or the core meaning of your sentence.

Хай брат іде додому. Нехай брат іде додому. Хай цей день буде добрим для нас. Нехай цей день буде добрим для нас.

> *Let the brother go home. Let the brother go home. May this day be good for us. May this day be good for us.*

:::info
**Grammar box**
The particles **хай** and **нехай** must be followed by a conjugated verb in the third person (he, she, it, they). Unlike English, which uses "let" followed by an object pronoun and an infinitive ("let him *go*"), Ukrainian never uses an infinitive in this structure.
:::

This grammatical construction serves three main purposes in daily Ukrainian communication. First, you can use it to give an indirect command or instruction to someone who is not present in the room. For example, if you want your colleagues to call you later, you express this instruction through the person you are currently speaking with.

Нехай вони подзвонять мені ввечері. Хай Петро купить свіжий хліб після роботи. Нехай діти граються надворі, поки світить сонце.

> *Have them call me in the evening. Let Petro buy fresh bread after work. Let the children play outside while the sun shines.*

Second, these particles express permission or concession. You use this structure to indicate that you are allowing a situation to happen without interference, or that you simply do not object to someone's actions.

Хай іде, я не проти. Нехай вона спить, сьогодні ж вихідний день. Хай вони роблять цей проєкт так, як хочуть.

> *Let him go, I don't mind. Let her sleep, it's a day off after all. Let them do this project the way they want.*

Third, this pattern is frequently used to express a general wish, often called a **побажання** (wish, blessing), or abstract hopes for the future. The verb must always agree with its grammatical subject in person and number, even in these fixed, idiomatic phrases.

Хай щастить вам у новій роботі! Нехай живе вільна і незалежна країна! Хай усі ваші великі мрії здійсняться!

> *Good luck to you in the new job! May the free and independent country live! May all your big dreams come true!*

The choice of aspect significantly changes the nuance of your command or wish, just as it does with direct commands. An imperfective verb focuses entirely on the process, expressing a general instruction, an ongoing continuous state, or a repeated habitual action. A perfective verb, on the other hand, focuses purely on the final result, indicating a specific, one-time action that needs to be successfully completed.

Хай він пише цей звіт щодня. Хай він напише цей звіт до завтрашнього ранку. Нехай вона читає ту цікаву книгу. Нехай вона прочитає статтю і розкаже нам.

> *Let him write (be writing) this report every day. Let him finish writing this report by tomorrow morning. Let her read that interesting book. Let her read the article through and tell us.*

<!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->

## Читаймо! Ходімо! Перша особа множини (1st Person Plural Imperatives) (~500 words)

When you want to suggest doing something together with friends, English relies on the phrase "Let's". In Ukrainian, you do not need an extra word. Instead, you simply change the ending of the action verb to create the first person plural form of the **наказовий спосіб** (imperative mood). You build this single-word form directly from the base of the second person singular imperative—the basic "you" command form. If the command form for "you" ends in a vowel, such as the letter **й**, you just attach the suffix **-мо** to the end of the word.

Форма для першої особи множини завжди закінчується на суфікс «-мо». Ми беремо звичайний наказ для другої особи однини і додаємо цей суфікс. Наприклад, дієслово «читати» має форму наказу «читай». Ми додаємо «-мо» і отримуємо «читаймо». Дієслово «співати» має форму «співай», тому ми кажемо «співаймо». Це дуже просте і логічне правило.

> *The form for the first person plural always ends with the suffix "-mo". We take the regular command for the second person singular and add this suffix. For example, the verb "to read" has the command form "read". We add "-mo" and get "let's read". The verb "to sing" has the form "sing", so we say "let's sing". This is a very simple and logical rule.*

If the base imperative form for "you" ends in a consonant instead of a vowel, the transformation process is just as straightforward. When the basic command ends in a hard consonant, the connecting vowel **-і-** naturally appears before the **-мо** suffix to make the word easier to pronounce. If the command form ends in a soft consonant, indicated by a soft sign, you keep that soft sign and attach the **-мо** ending directly after it.

Дієслово «робити» має форму наказу «роби». Щоб сказати це разом, ми використовуємо форму «робімо». Дієслово «казати» має наказ «скажи», тому разом ми кажемо «скажімо». Якщо основа закінчується на м'який приголосний, ми зберігаємо м'який знак. Від слова «сідати» ми утворюємо наказ «сядь», а для групи людей кажемо «сядьмо». Від слова «їхати» ми маємо наказ «поїдь», а разом кажемо «поїдьмо».

> *The verb "to do" has the command form "do". To say this together, we use the form "let's do". The verb "to say" has the command "say", so together we say "let's say". If the base ends in a soft consonant, we keep the soft sign. From the word "to sit down" we form the command "sit", and for a group of people we say "let's sit". From the word "to drive" we have the command "drive", and together we say "let's drive".*

You will frequently hear native speakers use the word **давайте** (let's — suggestion particle) followed by an infinitive, such as "давайте читати". This alternative construction is widely understood and often sounds like a gentle proposal. However, you must be extremely careful. While using "давайте" with an infinitive is acceptable in casual everyday speech, combining **давайте** with a conjugated first person plural verb form is considered a direct grammatical error.

В українській мові не можна казати «давайте поговоримо» або «давай підемо». Це велика помилка і калька з російської мови. Правильно казати тільки «поговорімо» або «ходімо». Слово «давайте» можна використовувати тільки з інфінітивом, наприклад, «давайте читати». Але найкраще і найгарніше завжди використовувати чисту форму на «-мо». Це показує вашу повагу до мови.

> *In the Ukrainian language, you cannot say "let's talk" or "let's go" using the Russian-style structure. This is a big mistake and a calque from the Russian language. It is correct to say only "let's talk" or "let's go" using the single word. The word "let's" can be used only with an infinitive, for example, "let's read". But it is always best and most beautiful to use the pure form ending in "-mo". This shows your respect for the language.*

:::info
**Grammar box**
Always avoid the structure `Давай(те) + 1st person plural verb`. The phrase ❌ `Давайте поговоримо` is incorrect. The elegant, standard Ukrainian form is ✅ `Поговорімо`.
:::

These **-мо** forms are incredibly common in everyday Ukrainian life, serving as the standard way to initiate shared activities. You will hear them constantly at work meetings, during outings, and at home. Just like with other command forms, the aspect of the verb you choose changes the nuance. An imperfective verb suggests an ongoing, habitual action, or focuses on the general process. A perfective verb implies a specific, one-time action that you want the group to complete successfully.

Найпопулярніше слово для спільної дії — це **ходімо** (let's go). Ви також часто будете чути фрази «починаймо», «зробімо це» та «поговорімо». Коли ми кажемо «ходімо до парку», ми маємо на увазі одну конкретну поїздку. Це доконана дія. Але коли вчитель каже «читаймо щодня», він просить робити це регулярно. Це недоконана дія, яка показує звичку.

> *The most popular word for a shared action is "let's go". You will also often hear the phrases "let's start", "let's do it", and "let's talk". When we say "let's go to the park", we mean one specific trip. This is a perfective action. But when a teacher says "let's read every day", he is asking to do this regularly. This is an imperfective action that shows a habit.*

<!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->

## Кличний + наказовий + орудний: Побажання (Vocative + Imperative + Instrumental: Wishes) (~600 words)

In Ukrainian culture, expressing a sincere **побажання** (wish, blessing) is a deep tradition that goes far beyond a simple "happy birthday." When Ukrainians raise a glass for a toast or write a greeting card, they use a powerful and elegant grammatical formula. This construction relies on three core elements working perfectly together. First, we use the **кличний відмінок** (Vocative case) to personally address the recipient. Second, we use the **наказовий спосіб** (imperative mood) to deliver the warm command. Finally, we use the Instrumental case to describe exactly what we want them to be or become.

Українці дуже люблять говорити гарні слова на свята. Ми завжди бажаємо рідним людям найкращого в житті. Наша мова має спеціальну формулу для цього. Наприклад, ми часто кажемо: «Оленко, будь щасливою!»

> *Ukrainians really love to say beautiful words on holidays. We always wish our dear people the best in life. Our language has a special formula for this. For example, we often say: "Olenko, be happy!"*

Let us break down the first two components of this formula. We always start with the Vocative case, which makes the wish direct. If you are speaking to your friend Olena, her name changes to «Оленко». The word for mother changes from «мама» to «мамо», and a male friend goes from «друг» to «друже». For plural addresses, the forms «діти» and «друзі» remain the same as their dictionary forms. Once you have their attention, you provide the core command using the verb «бути» (to be). You must use **будь / будьте** (be — imperative of бути) depending on how many people you are addressing.

Коли ми звертаємося до людини, ми обов'язково змінюємо закінчення її імені. Мама стає «мамо», а друг стає «друже». Потім ми додаємо дієслово «бути». Для однієї людини ми кажемо «будь», а для групи людей — «будьте».

> *When we address a person, we necessarily change the ending of their name. The word for mother becomes «мамо», and the word for friend becomes «друже». Then we add the verb "to be". For one person we say «будь», and for a group of people — «будьте».*

The third and final component is the Instrumental case, which attaches to the adjective describing the desired state. For example, the adjective **щасливий / щасливою** (happy / happy — Instr.f.) changes its ending to match the person. The same happens with plural adjectives like **здоровий / здоровими** (healthy / healthy — Instr.pl.).

You apply this same logic to any descriptive word you want to use in your blessing. For example, the word **спокійний** (calm) becomes «спокійною» for a woman, and **уважний** (attentive) becomes «уважними» for a group. The Instrumental case perfectly captures the enduring nature of the state you are wishing upon them.

Мамо, будь спокійною і ніколи не хвилюйся! Діти, завжди будьте уважними на вулиці! Дорогі друзі, будьте здоровими та сильними! Це дуже класичні та правильні речення.

> *Mom, be calm and never worry! Children, always be attentive on the street! Dear friends, be healthy and strong! These are very classic and correct sentences.*

In casual speech, you will absolutely hear people use short forms with the Nominative case, such as «Будь щаслива!» or «Будьте здорові!». These simpler versions are extremely common and perfectly acceptable for informal interactions. However, using the Instrumental case remains the refined, literary standard. When you write a formal greeting card, using the Instrumental case shows that you understand the deep mechanics of the language and adds a layer of profound respect to your greeting.

:::info
**Grammar box**
While short forms like ✅ «Будь здорова!» are popular in casual conversation, the Instrumental case ✅ «Будь здоровою!» is the gold standard for written greetings and formal toasts. It beautifully expresses the idea of *becoming* or *existing* in a certain state.
:::

You can create even more poetic wishes by combining the particles **хай** (let — particle for 3rd person imperative) or **нехай** (let — formal variant) with third-person verbs. In these cases, you are wishing for an external force—like luck or destiny—to act upon the person. 

For instance, you can wish for a **мрія** (dream) to **здійснитися** (to come true). You can also mix these particles with direct commands like **живи** (live — imperative) for a truly monumental blessing.

Оленко, хай тобі завжди щастить у житті! Друже, нехай здійсняться всі твої мрії! Дідусю, живи довго і будь щасливим! Такі слова роблять наше життя набагато світлішим і теплішим.

> *Olenko, may you always have luck in life! Friend, may all your dreams come true! Grandpa, live long and be happy! Such words make our life much brighter and warmer.*

<!-- INJECT_ACTIVITY: match-up-vocative-wishes -->

## Вид дієслова в наказовому способі (Aspect in Imperatives) (~500 words)

The **наказовий спосіб** (imperative mood) is incredibly versatile. You already know how to use **хай** (let — particle for 3rd person imperative) and **нехай** (let — formal variant) for third parties. Now, let us dive into how aspect choice drastically changes the tone of these commands.

You know to say **ходімо** (let's go) for joint actions, rather than the borrowed **давайте** (let's — suggestion particle). We will see that aspect also affects how we suggest doing things together.

You can even form a beautiful **побажання** (wish, blessing) by combining the **кличний відмінок** (Vocative case) with the verb "to be". For example, you use **будь / будьте** (be — imperative of бути) depending on who you address.

These wishes are completed with adjectives in the Instrumental case, such as **щасливий / щасливою** (happy / happy — Instr.f.) or **здоровий / здоровими** (healthy / healthy — Instr.pl.). Aspect plays a subtle but vital role in all these structures.

When giving direct commands, your choice between imperfective and perfective verbs drastically changes the meaning. We use the imperfective aspect for general instructions, repeated actions, or polite invitations. It focuses on the process rather than a final result.

Коли ми даємо загальну пораду, ми використовуємо недоконаний вид. Наприклад, ми кажемо «Читай більше!» або «Пишіть щодня!». Це означає, що дія має бути регулярною. Також цей вид робить наші прохання дуже ввічливими. Коли приходять гості, ми кажемо: «Сідайте, будь ласка». Ми не вимагаємо миттєвого результату, ми просто запрошуємо до дії.

> *When we give general advice, we use the imperfective aspect. For example, we say "Read more!" or "Write every day!". This means the action should be regular. Also, this aspect makes our requests very polite. When guests arrive, we say: "Please sit down". We do not demand an instant result, we just invite to the action.*

On the other hand, the perfective imperative is used for specific, one-time commands where a concrete result is expected right away. It sounds more urgent and direct because it focuses purely on the completion of the action.

Доконаний вид потрібен тоді, коли ми чекаємо на швидкий і конкретний результат. Якщо вчитель хоче, щоб ви закінчили текст, він скаже: «Прочитай цю статтю!». Якщо ви чекаєте на повідомлення, ви скажете: «Напиши мені!». А коли надворі холодно, ви даєте чіткий наказ: «Закрий двері!». Ці форми звучать більш прямолінійно і вимагають негайного виконання.

> *The perfective aspect is needed when we wait for a quick and concrete result. If a teacher wants you to finish a text, he will say: "Read this article!". If you are waiting for a message, you will say: "Write to me!". And when it is cold outside, you give a clear command: "Close the door!". These forms sound more direct and demand immediate execution.*

There is a strict rule for negative imperatives: negative commands almost exclusively use the imperfective aspect. Telling someone NOT to do something implies an ongoing prohibition or stopping a process that is currently happening.

В українській мові негативні накази майже завжди мають недоконаний вид. Коли ми хочемо зупинити дію, ми кажемо: «Не читай це!». Ми також кажемо: «Не відкривайте вікно!». Навіть якщо дія разова, правило залишається суворим. Ми ніби кажемо людині не починати або не продовжувати цей процес. Це звучить природно і правильно для будь-якої заборони.

> *In the Ukrainian language, negative commands almost always have the imperfective aspect. When we want to stop an action, we say: "Don't read this!". We also say: "Don't open the window!". Even if the action is one-time, the rule remains strict. It is as if we are telling the person not to start or not to continue this process. This sounds natural and correct for any prohibition.*

There is one fascinating exception. Using the perfective aspect in a negative command creates a harsh warning or expresses fear of an accidental, sudden result. It is not a prohibition, but a strong caution about a potential danger.

Єдиний виняток — це попередження про небезпеку. Якщо ми використовуємо доконаний вид із запереченням, ми боїмося раптового результату. Класичний приклад — це фраза «Не впади!». Ми не забороняємо людині падати, ми дуже просимо її бути обережною. Отже, загальні поради вимагають недоконаного виду. А конкретні завдання та попередження вимагають доконаного виду.

> *The only exception is a warning about danger. If we use the perfective aspect with negation, we are afraid of a sudden result. A classic example is the phrase "Don't fall!". We are not forbidding the person to fall, we are asking them very much to be careful. Thus, general advice requires the imperfective aspect. And specific tasks and warnings require the perfective aspect.*

:::info
**Grammar box**
Negative commands usually take the imperfective aspect: «Не відкривай двері!» (Don't open the doors — prohibition). Perfective negative commands are only for accidental dangers: «Не впади!» (Don't fall — careful!).
:::

<!-- INJECT_ACTIVITY: quiz-aspect-choice -->
<!-- INJECT_ACTIVITY: unjumble-imperative-sentences -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: imperative-complete
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

**Level: A2 (Module 44/60) — ELEMENTARY**

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
