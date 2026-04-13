<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/b1-baseline-past-present.yaml` file for module **1: Минуле і теперішнє** (b1).

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

- `<!-- INJECT_ACTIVITY: group-sort-distribute-verbs-between-i-and-ii-conjugation-classes -->`
- `<!-- INJECT_ACTIVITY: fill-in-tense-forms -->`
- `<!-- INJECT_ACTIVITY: quiz-aspect-id -->`
- `<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->`
- `<!-- INJECT_ACTIVITY: error-correction-aspect -->`
- `<!-- INJECT_ACTIVITY: open-writing-yesterday -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: 'Визначте час і вид дієслова: теперішній/минулий, доконаний/недоконаний'
  items: 10
  type: quiz
- focus: Поставте дієслово у правильну форму теперішнього або минулого часу
  items: 8
  type: fill-in
- focus: 'Розподіліть дієслова: I дієвідміна vs II дієвідміна'
  items: 10
  type: group-sort
- focus: 'З''єднайте видові пари: доконаний ↔ недоконаний (писати ↔ написати)'
  items: 8
  type: match-up
- focus: Знайдіть і виправте помилки у вживанні виду або часу в реченнях
  items: 6
  type: error-correction
- focus: 'Напишіть короткий текст: ''Мій вчорашній день'' — чергуйте доконаний і недоконаний
    вид'
  items: 6
  type: open-writing


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- 'суфікс минулого часу (past tense suffix: -в/-л-)'
- тематичний голосний (thematic vowel — е/є for I, и/і for II conjugation)
- чергування (alternation — consonant changes in conjugation)
- основа інфінітива (infinitive stem — base for past tense formation)
- основа теперішнього часу (present tense stem — base for present forms)
- послідовність дій (sequence of actions — perfective chain)
- тло розповіді (narrative background — imperfective setting)
- постфікс (postfix — -ся/-сь added after the ending)
- безособовий (impersonal — мені не спиться, хочеться)
- узгодження (agreement — verb agrees with subject in gender/number)
required:
- теперішній час (present tense)
- минулий час (past tense)
- дієвідміна (conjugation class — I or II)
- особа (person — 1st, 2nd, 3rd)
- число (number — однина, множина)
- рід (gender — чоловічий, жіночий, середній)
- доконаний вид (perfective aspect — completed action)
- недоконаний вид (imperfective aspect — ongoing action)
- інфінітив (infinitive — the base form ending in -ти/-тися)
- дієвідмінювання (conjugation — changing verb by person and number)
- зворотний (reflexive — verbs with -ся/-сь)
- видова пара (aspectual pair — e.g., писати/написати)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Теперішній час: дієвідміни

> — **Олексій:** Привіт, Дарино! Радий тебе бачити. Як минуло твоє літо? *(Hi, Daryna! Glad to see you. How was your summer?)*
> — **Дарина:** Привіт! Літо було чудове. Я багато подорожувала. А ти що робив? *(Hi! Summer was great. I traveled a lot. And what did you do?)*
> — **Олексій:** Я майже все літо працював у Києві. *(I worked in Kyiv almost all summer.)*
> — **Дарина:** О, я пам'ятаю. Ти працював у новому видавництві, так? *(Oh, I remember. You worked in a new publishing house, right?)*
> — **Олексій:** Так, працював там стажистом. А зараз вже працюю постійним автором. *(Yes, I worked there as an intern. And now I already work as a permanent author.)*
> — **Дарина:** Клас! А зараз що робиш? Які маєш проєкти? *(Cool! And what are you doing now? What projects do you have?)*
> — **Олексій:** Якраз пишу велику статтю для журналу. Ми готуємо спеціальний випуск. *(I'm writing a big article for a magazine right now. We are preparing a special issue.)*
> — **Дарина:** Дуже цікаво. Бачу, що ти багато знаєш про цю тему. *(Very interesting. I see that you know a lot about this topic.)*

The present tense in Ukrainian, known as **теперішній час**, describes actions that are happening right at the moment of speech or actions that occur constantly and regularly. When you say that you are drinking coffee right now or that you work every day, you use the present tense. The most crucial rule to remember is that only imperfective verbs, or **недоконаний вид**, can have a present tense form. Because an action happening in the present moment is ongoing and cannot be fully completed yet, perfective verbs simply do not exist in the present tense. If you encounter a verb in the perfective aspect, it will only ever have past or future forms. Mastering the present tense forms is your key to holding natural, flowing conversations about your daily life, your habits, and the world around you. This is the foundation upon which you will build your storytelling skills.

В українській мові дієслова теперішнього часу завжди змінюються за особами та числами. Це означає, що кожному займеннику відповідає своє унікальне закінчення. Залежно від системи цих закінчень, усі дієслова поділяються на дві великі групи, які називаються дієвідмінами. Перша дієвідміна є дуже поширеною. Її головна ознака — це тематичний голосний «е» або «є» у більшості особових форм. До цієї групи належать такі базові слова, як «писати», «знати», «читати» та «працювати». Коли ми відмінюємо дієслово «писати», у першій особі однини ми використовуємо закінчення «-у» або «-ю»: «я пишу». У другій особі з'являється той самий тематичний голосний, тому ми додаємо «-еш» або «-єш»: «ти пишеш». Третя особа однини закінчується просто на «-е» або «-є»: «він пише», «вона знає». У множині система залишається стабільною. Ми використовуємо закінчення «-емо» або «-ємо» для першої особи («ми пишемо»), «-ете» або «-єте» для другої («ви пишете»), та «-уть» або «-ють» для третьої особи («вони пишуть»). Повна парадигма для слова «знати» виглядає так: я знаю, ти знаєш, він знає, ми знаємо, ви знаєте, вони знають.

Друга дієвідміна має зовсім інший тематичний голосний — це звуки «и» або «ї». Характерними прикладами цієї групи є такі популярні дієслова, як «робити», «говорити», «вчити» та «бачити». У першій особі однини закінчення повністю збігаються з першою дієвідміною: ми так само кажемо «я роблю» або «я говорю». Але вже з другої особи починається ключова різниця. Друга особа однини обов'язково має закінчення «-иш» або «-їш»: «ти робиш», «ти говориш». Третя особа однини отримує м'яке закінчення «-ить» або «-їть»: «він робить», «вона говорить». У множині ми також чітко чуємо цей тематичний голосний. Ми кажемо «ми робимо», «ви робите», а для третьої особи множини використовуємо закінчення «-ать» або «-ять»: «вони роблять», «вони говорять». Завжди звертайте особливу увагу на цей голосний під час розмови чи письма, адже він допомагає правильно формувати слова та уникати типових помилок.

:::info
**Grammar box**
If you are unsure which conjugation class a new verb belongs to, the most deterministic way to check is to look at the third person plural form, which corresponds to the pronoun **вони** (they). First conjugation verbs will always end in **-уть** or **-ють** (вони пишуть, вони знають, вони читають). Second conjugation verbs, on the other hand, will always end in **-ать** or **-ять** (вони роблять, вони говорять, вони бачать).
:::

This simple trick is incredibly useful for navigating tricky verbs that look like they belong to one class based on their infinitive form but actually behave differently. For example, the verb **хотіти** (to want) looks like a typical second conjugation verb, but Ukrainians say **вони хочуть**, making it undeniably first conjugation. Conversely, **стояти** (to stand) looks like a first conjugation verb, but it becomes **вони стоять**, which firmly places it in the second conjugation class. Always default to the "вони" test when in doubt, as it will never lead you astray when trying to find the correct thematic vowel.

Під час дієвідмінювання (conjugation) дієслів у теперішньому часі іноді трапляється так, що змінюється не лише саме закінчення, а й приголосний звук безпосередньо перед ним. Це цікаве мовне явище називається чергуванням приголосних. Важливо запам'ятати, що воно найчастіше і найяскравіше відбувається саме у першій особі однини, тобто коли ми говоримо про себе. Наприклад, твердий звук «д» часто змінюється на дзвінкий африкат «дж»: інфінітив «сидіти» перетворюється на форму «я сиджу», а «водити» — на «я воджу». Звук «с» регулярно перетворюється на шиплячий «ш», тому ми впевнено кажемо «я прошу» від дієслова «просити». Губні приголосні, такі як «б» або «п», завжди отримують додатковий м'який звук «л» для зручності вимови. Саме через це правило від слова «любити» ми утворюємо ніжну форму «я люблю», а від слова «робити» отримуємо «я роблю». В усіх інших особах ці приголосні зазвичай залишаються без змін, тому ми продовжуємо казати «ти любиш», «він сидить» або «ми просимо».

:::tip
**Did you know?**
Особливістю української мови є те, що в третій особі однини першої дієвідміни дієслова ніколи не мають м'якого закінчення «-ть». Ми завжди кажемо «він знає», «вона пише» або «він несе». Втрата цього звука є дуже важливою фонетичною рисою, яка історично відрізняє українську від сусідніх мов. Збереження таких унікальних граматичних форм є ключовим маркером нашої глибокої мовної ідентичності.

> *A special feature of the Ukrainian language is that in the third person singular of the first conjugation, verbs never have the soft ending "-ть". We always say "він знає", "вона пише" or "він несе". The loss of this sound is a very important phonetic feature that historically distinguishes Ukrainian from neighboring languages. Preserving such unique grammatical forms is a key marker of our deep linguistic identity.*
:::

<!-- INJECT_ACTIVITY: group-sort-distribute-verbs-between-i-and-ii-conjugation-classes -->

## Минулий час: утворення і вживання

The past tense in Ukrainian is constructed differently from the present tense. Instead of taking the present tense stem, we go back to the infinitive form of the verb. By removing the final **-ти** suffix, we expose the infinitive stem. To this stem, we add specific past tense suffixes: **-в** for masculine singular subjects, and **-л-** followed by a vowel ending for feminine, neuter, and plural subjects. This structure provides a highly regular and reliable system for building the past tense, allowing you to confidently predict the correct form for almost any new verb you encounter.

Для того щоб утворити форму минулого часу, ми беремо основу інфінітива і додаємо відповідні суфікси. Якщо підмет має чоловічий рід, ми використовуємо суфікс «-в», тому від слова «читати» отримуємо форму «він читав». Для жіночого роду ми додаємо суфікс «-л-» та закінчення «-а», що дає нам форму «вона читала». Середній рід вимагає закінчення «-о», тому ми кажемо «воно читало». Для множини, незалежно від роду осіб, ми завжди додаємо закінчення «-и», утворюючи форму «вони читали».

> *To form the past tense, we take the infinitive stem and add the appropriate suffixes. If the subject is masculine, we use the suffix "-в", so from the word "читати" we get the form "він читав". For the feminine gender, we add the suffix "-л-" and the ending "-а", which gives us the form "вона читала". The neuter gender requires the ending "-о", so we say "воно читало". For plural, regardless of the gender of the persons, we always add the ending "-и", creating the form "вони читали".*

This simple mechanical transformation applies to the vast majority of Ukrainian verbs, making the basic formation of the past tense quite predictable once you identify the infinitive stem. You just need to strip away the infinitive marker and attach the correct suffix.

A fundamental difference between the past and present tenses in Ukrainian is how they agree with the subject. In the present tense, verbs change based on the "person" (first, second, or third) doing the action. However, in the past tense, verbs completely ignore the grammatical person. Instead, they agree exclusively with the subject's gender and number. This concept often requires a mental shift for English speakers, who are used to verbs changing by person but never by gender.

This means that "I read", "you read", and "he read" all share the exact same masculine form, **читав**, if the speaker or subject is male. If the speaker or subject is female, "I read", "you read", and "she read" will all use the feminine form, **читала**. In English, the past tense verb "read" or "walked" remains completely unchanged regardless of who is performing the action or their gender identity. In Ukrainian, the past tense verb must dynamically adapt to reflect whether the subject is masculine, feminine, neuter, or plural.

Дієслова минулого часу не змінюються за особами, що є їхньою найважливішою синтаксичною особливістю. Форми «я читав», «ти читав» і «він читав» однакові, якщо йдеться про чоловіка. Головне правило полягає в тому, що дієслово минулого часу завжди працює як дзеркало, яке точно відображає граматичний рід та число свого підмета. Якщо говорить жінка, вона завжди використовуватиме форму з жіночим закінченням для опису своїх дій.

While the standard rule of adding **-в** or **-л-** works flawlessly for most verbs, a distinct group of verbs behaves differently. These are verbs whose infinitive stem ends in a consonant rather than a vowel. For these verbs, the masculine singular form is created without adding any suffix at all, relying instead on internal phonetic shifts to signal the past tense.

:::info
**Grammar box**
When an infinitive stem ends in a consonant (like **нес-ти** or **мог-ти**), the masculine past tense form drops the suffix entirely. More importantly, the root vowel often changes from "о" or "е" to "і" because the syllable becomes closed.
:::

Дієслово «нести» має основу, яка закінчується на приголосний звук «с». Тому форма чоловічого роду утворюється без суфікса «-в», і ми отримуємо коротке слово «ніс». Голосний звук «е» в закритому складі закономірно перетворюється на «і», що є типовим явищем для української фонетики. Але коли ми утворюємо жіночу форму «несла» або множину «несли», склад знову відкривається. Тому звук «е» повертається на своє законне місце, і ми більше не чуємо звука «і» в цих формах. Цей процес чергування є дуже давнім і послідовним.

> *The verb "нести" has a stem that ends in the consonant sound "с". Therefore, the masculine form is created without the suffix "-в", and we get the short word "ніс". The vowel sound "е" in a closed syllable naturally turns into "і", which is a typical phenomenon for Ukrainian phonetics. But when we form the feminine "несла" or plural "несли", the syllable opens up again. Therefore, the sound "е" returns to its rightful place, and we no longer hear the sound "і" in these forms. This process of alternation is very ancient and consistent.*

Other common verbs follow this exact same historical pattern. The verb **могти** (to be able to) becomes **міг** for a masculine subject, but reverts to **могла** for feminine and **могли** for plural. Similarly, **бігти** (to run) transforms into **біг**, but opens up to **бігла** and **бігли**. Recognizing this "о/е" to "і" shift in closed syllables is crucial for mastering these irregular, yet highly frequent, consonant-stem verbs.

Let us revisit the conversation between Олексій and Дарина from the opening dialogue to see these gender and number rules in action. When people tell stories about their own lives, their gender determines the shape of the verbs they use.

У нашій розмові Олексій розповідає про свій професійний досвід і каже: «Я працював у видавництві». Оскільки Олексій є чоловіком, він природно використовує форму чоловічого роду із суфіксом «-в». Коли ж Дарина говорить про свою літню відпустку, вона згадує: «Минулого літа ми їздили до Львова». Тут підмет «ми» вимагає форми множини, тому дієслово отримує відповідне закінчення «-и». Обидва персонажі використовують минулий час для опису свого попереднього досвіду.

> *In our conversation, Oleksiy talks about his professional experience and says: "Я працював у видавництві". Since Oleksiy is a man, he naturally uses the masculine form with the suffix "-в". When Daryna talks about her summer vacation, she mentions: "Минулого літа ми їздили до Львова". Here the subject "ми" requires the plural form, so the verb gets the corresponding ending "-и". Both characters use the past tense to describe their previous experience.*

These examples highlight how the past tense fluidly adapts to the speaker and the number of people involved, seamlessly weaving grammatical agreement into everyday storytelling.

One of the most persistent errors made by learners is forgetting to align the past tense verb with the gender of the subject. Because English past tense verbs are entirely gender-neutral, it is incredibly easy to default to the masculine form in Ukrainian simply because it feels like the "base" past tense word. This mistake is especially common when a female speaker is talking about herself, or when someone is talking about a female friend or family member.

Дуже часто студенти кажуть фрази на кшталт «моя сестра сказав» замість правильного варіанта «моя сестра сказала». Це відбувається через те, що вони забувають перевірити граматичний рід підмета перед тим, як вимовити дієслово. Ви повинні завжди пам'ятати, що в минулому часі дієслово міцно прив'язане до роду особи або предмета, який виконує дію. Без цього узгодження речення звучить дуже неприродно для носіїв мови.

:::tip
**Did you know?**
Historically, the Ukrainian past tense evolved from a compound structure that included a participle. Participles function somewhat like adjectives, which is why the modern past tense still "remembers" how to agree in gender and number, just like an adjective would!
:::

Whenever you narrate a story in the past tense, you must maintain a constant awareness of who or what is driving the action. The verb is an extension of the subject's identity in that specific moment in time.

Beyond its mechanical formation, the past tense is the primary engine for narration. However, simply knowing how to form the past tense is only half the battle. The true complexity arises when we need to choose between describing a chain of completed sequential events or painting a picture of an ongoing past state.

В українській мові існують слова «робив» та «зробив», які обидва належать до минулого часу, але мають різні значення. Форма «робив» описує тривалий процес у минулому, тоді як «зробив» вказує на конкретний і завершений результат цієї дії. Ваша здатність розповідати історії залежить від правильного вибору між цими двома формами.

This critical distinction between the ongoing process and the completed result introduces us to the concept of verbal aspect, which fundamentally dictates how we narrate the past in Ukrainian.

<!-- INJECT_ACTIVITY: fill-in-tense-forms -->

## Вид дієслова: доконаний і недоконаний

The most fundamental concept in the Ukrainian verb system is verbal aspect. Unlike English, which uses complex tense structures like the present continuous or past perfect to express how an action unfolds over time, Ukrainian builds this information directly into the verbs themselves. Almost every action is represented by an aspectual pair, dividing reality into two distinct categories based on boundaries and completion. Learning to navigate these pairs is essential for accurate storytelling and describing your daily life.

В українській мові дієслова поділяються на недоконаний і доконаний вид. Недоконаний вид завжди відповідає на питання «що робити?» і описує дію як тривалий процес, постійну звичку або регулярне повторення. Наприклад, дієслово «писати» показує саму дію в її активному розвитку, без жодної вказівки на її кінець. Доконаний вид відповідає на питання «що зробити?» і незмінно вказує на кінцевий результат, чітку межу або повне завершення дії. Дієслово «написати» означає, що творчий процес успішно закінчився і тепер ми маємо готовий текст перед очима.

> *In the Ukrainian language, verbs are divided into the imperfective and perfective aspects. The imperfective aspect always answers the question "what to do?" and describes an action as a continuous process, constant habit, or regular repetition. For example, the verb "писати" shows the action itself in its active development, without any indication of its end. The perfective aspect answers the question "what to do? (completed)" and invariably indicates a final result, clear boundary, or complete finishing of an action. The verb "написати" means that the creative process has successfully finished and we now have a ready text before our eyes.*

Aspect is tightly linked to the concept of tense, and understanding this relationship is crucial for avoiding common grammatical errors. While an imperfective verb can freely move across the past, present, and future tenses, a perfective verb faces a strict logical restriction regarding the present moment. You can describe a process as happening right now, but you cannot describe a completed result as an ongoing present event. This philosophical distinction shapes the entire conjugation system and dictates which tense forms are even mathematically possible for a given verb.

Дієслова доконаного виду ніколи не мають форм теперішнього часу, адже повністю завершена дія просто не може відбуватися прямо зараз. Якщо конкретний результат уже існує, ця дія автоматично належить до минулого, а якщо результату ще немає, вона є невіддільною частиною майбутнього. Саме тому такі слова, як «напишу» або «зроблю», візуально дуже нагадують форми теперішнього часу, але насправді позначають просту форму майбутнього. Ці дієслова впевнено обіцяють певний результат у майбутньому, а не описують ваш поточний стан чи активний процес у цей момент. Вони завжди дивляться вперед, очікуючи на фінальну точку дії.

To navigate these aspects efficiently, you need to recognize how they group together into aspectual pairs. These pairs usually share a common root but use different prefixes or suffixes to signal whether the action is a process or a completed event. Recognizing these morphological patterns will drastically speed up your vocabulary acquisition. Instead of learning two completely different words, you will learn a single base concept with two aspectual variations.

:::info
**Видові пари**
When learning a new verb, always try to memorize its aspectual pair. Dictionaries often list both forms together because they function as a single semantic unit in the language.
:::

Більшість видових пар утворюється за допомогою різноманітних префіксів, які додаються до базового недоконаного дієслова. Наприклад, від простого слова «читати» ми легко утворюємо доконаний вид «прочитати», а від слова «будувати» — форму «збудувати». Інший дуже поширений спосіб полягає у зміні характерного суфікса всередині слова, як це відбувається у парі «вирішити» та «вирішувати». Існують також унікальні суплетивні пари, де обидва види мають різні фонетичні корені. Найвідоміші та найважливіші приклади таких нестандартних пар — це слова «брати» і «взяти», а також «говорити» і «сказати».

When narrating past events, the choice between these two aspects fundamentally changes the core meaning of your sentence. It immediately shifts the listener's focus from the time you spent doing something to the achievement you unlocked at the end. You are not just choosing an arbitrary grammar form; you are actively choosing the exact perspective of your story. This powerful feature allows for incredibly precise communication about how you experienced a specific event in the past, without needing long descriptive phrases.

:::tip
**Process vs. Result**
A helpful mental shortcut is to associate imperfective verbs with watching a continuous video of the action happening, while perfective verbs are like looking at a single photograph of the final outcome.
:::

Уявіть звичайну ситуацію, коли вас відверто запитують: «Що ти робив учора ввечері?». Це питання фокусується виключно на процесі та вашій зайнятості, тому ви природно відповідаєте недоконаним видом: «Я читав нову книжку дві години». Ви детально описуєте своє заняття, але зовсім не кажете, чи змогли його успішно завершити. Якщо ж вас запитають: «Що ти зробив учора?», співрозмовника цікавить лише конкретний і вимірюваний результат. Тоді ви впевнено використовуєте доконаний вид: «Я прочитав цю книжку до кінця».

Mastering the choice between the imperfective and perfective aspects is what truly elevates your Ukrainian from sounding translated to sounding authentic and natural. English speakers often try to express completion by adding extra adverbs or auxiliary verbs, but in Ukrainian, the aspect itself carries all this vital semantic weight. Trust the verbs to do the heavy grammatical lifting in your storytelling. Once you deeply internalize this binary system, you will find that expressing complex chronological relationships becomes surprisingly elegant and straightforward. It is the true heartbeat of the Ukrainian language.

<!-- INJECT_ACTIVITY: quiz-aspect-id -->
<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->

## Вид у розповіді: послідовність і тло

When you tell a story, you are essentially painting a picture with words. In Ukrainian, the aspect of the verbs you choose acts as your brush, determining whether you are sketching the background scenery or drawing the main action taking place in the foreground. 

Дієслова недоконаного виду створюють тло розповіді. Вони описують атмосферу, паралельні процеси або загальну ситуацію, в якій відбуваються події. Наприклад, коли ви кажете: «Світило сонце, співали пташки, люди гуляли в парку», ви не розповідаєте про конкретну подію, а лише встановлюєте декорації для неї.

> *Imperfective verbs create the background of a narrative. They describe the atmosphere, parallel processes, or the general situation in which events take place. For example, when you say: "The sun was shining, birds were singing, people were walking in the park," you are not telling about a specific event, but only setting the scenery for it.*

Щоб рухати сюжет уперед, ви маєте перейти на доконаний вид. Дієслова доконаного виду формують ланцюжок послідовних дій. Вони відповідають за динаміку та показують конкретні результати: «Він прокинувся, встав, одягнувся і вийшов з дому». Кожне з цих дієслів — це завершений крок, після якого одразу починається наступний. Змішуючи ці два види, ви отримуєте об'ємну і живу розповідь, де на певному тлі розгортається динамічний сюжет.

One of the most common and powerful narrative techniques is using an interrupting action. This happens when an ongoing, continuous process is suddenly broken by a completed event. In Ukrainian, we achieve this seamlessly by combining the imperfective aspect for the background process with the perfective aspect for the interruption, often linked by the words **коли** (when) or **раптом** (suddenly). This contrast instantly tells the listener which action was already happening and which action changed the situation.

Уявіть таку ситуацію: «Я обідав, коли зателефонував Тарас». Тут дієслово «обідав» описує тривалий процес, у який ви були занурені. Натомість дієслово «зателефонував» позначає раптову подію, яка цей процес перервала або просто сталася на його тлі. Вам не потрібно додавати зайві слова, щоб пояснити хронологію — граматичний вид робить це за вас.

:::info
**Parallel vs. Interrupted Actions**
If you want to describe two actions happening at the exact same time without interrupting each other, you must use the imperfective aspect for both verbs, often connected by the word **поки** (while).
«Поки я обідав, Тарас читав новини.» — *While I was having lunch, Taras was reading the news.*
:::

A frequent mistake for English speakers is trying to force the perfective aspect into sentences that describe the explicit duration of an action. Remember the golden rule: the perfective aspect cares exclusively about the final result, never about how long it took to achieve it.

Саме тому речення «Вчора я прочитав книжку три години» є граматично та логічно неправильним. Якщо ви хочете підкреслити тривалість процесу, використовуючи слова на кшталт «три години», «весь день» або «дуже довго», ви зобов'язані використовувати недоконаний вид. Правильний та природний варіант звучить так: «Вчора я читав книжку три години».

If you want to emphasize that you successfully finished the book, you must drop the duration entirely and focus strictly on the achievement itself.

Ви просто кажете співрозмовнику: «Вчора я прочитав книжку». Якщо ж для вас принципово важливо вказати і факт повного завершення дії, і точний час, який ви на це витратили, ви можете скористатися прийменником **за**. Речення «Я прочитав книжку за три години» говорить про встановлений рекорд або певний ліміт часу, потрібний для досягнення фінального результату, а не про сам розслаблений процес читання.

To truly understand how aspect transforms a story, let us look at the exact same events told through two different lenses. First, we will narrate a day in Kyiv using only the perfective aspect. This creates a dry, sequential list of facts, resembling a strict itinerary.

«Я приїхав до Києва. Я пішов на Хрещатик. Я випив каву. Я зустрів друга.» Це ланцюжок послідовних і завершених подій. Ми точно знаємо, що сталося, але зовсім не відчуваємо атмосфери того дня.

> *"I arrived in Kyiv. I went to Khreshchatyk. I drank coffee. I met a friend." This is a chain of sequential and completed events. We know exactly what happened, but we do not feel the atmosphere of that day at all.*

Now, let us rewrite this story using the imperfective aspect to describe the ongoing scene, while keeping the perfective verbs for the main events. The vibe changes completely.

«Коли я приїхав до Києва, йшов теплий дощ. Я пішов на Хрещатик. Там гуляли люди і грали вуличні музиканти. Поки я пив каву, я раптом зустрів друга.» Тепер історія має справжню глибину. Дощ, люди та музиканти створюють недоконане тло, на якому чітко виділяються ваші доконані дії.

:::tip
**The Cinematic Mindset**
Think like a film director. Use the imperfective aspect for wide establishing shots and slow-motion scenes. Switch to the perfective aspect for fast cuts and action sequences.
:::

<!-- INJECT_ACTIVITY: error-correction-aspect -->
<!-- INJECT_ACTIVITY: open-writing-yesterday -->

## Дієслова на -ся: зворотні дієслова

In English, reflexive verbs are often formed by adding words like "myself" or "yourself" after the main verb. In Ukrainian, this function is performed by the postfix **-ся** or **-сь**, which attaches directly to the end of the conjugated verb. Assuming that every verb ending in this postfix is strictly reflexive is a very common trap for English speakers. While it is true that many of these verbs describe actions performed on oneself, the Ukrainian language uses this grammatical category for a much wider range of meanings. You must recognize four distinct categories to use these verbs naturally.

Українські дієслова на -ся мають чотири основні значення. Перша група — це власне зворотні дієслова, де дія спрямована на самого себе. Наприклад, коли ви кажете «я миюся» або «вона одягається», ви буквально миєте себе та одягаєте себе. Друга група — це взаємна дія, яка завжди потребує двох або більше учасників. Слова «зустрічатися», «спілкуватися» або «обійматися» описують процес, який люди виконують разом. Третя категорія описує внутрішній стан людини, її емоції або зміни в природі. Ви можете «хвилюватися» перед іспитом, «дивуватися» несподіваним новинам або просто «радуватися» гарній погоді. І остання, найцікавіша група — це безособові конструкції, які показують, що дія відбувається ніби сама собою, без вашого свідомого контролю.

> *Ukrainian verbs ending in -ся have four main meanings. The first group is strictly reflexive verbs, where the action is directed at oneself. For example, when you say "I wash myself" or "she dresses herself", you literally wash yourself and dress yourself. The second group is mutual action, which always requires two or more participants. Words like "to meet", "to communicate", or "to hug" describe a process that people perform together. The third category describes a person's inner state, emotions, or changes in nature. You can "worry" before an exam, "be surprised" by news, or "rejoice" at the weather. The final group is impersonal constructions, showing that the action happens by itself, without your conscious control.*

Impersonal verbs shift the grammatical subject to the dative case, removing agency from the person experiencing the state. Instead of saying you cannot sleep, you say sleep does not come to you, using phrases like «мені не спиться» (I cannot sleep) or «їй хочеться кави» (she wants coffee). This structure is deeply ingrained in the Ukrainian mindset.

When writing and speaking these verbs in the present tense, you must pay close attention to two specific endings: the third-person (he, she, it, they) and the second-person singular (you). These forms are notorious for causing spelling mistakes because the written form and the spoken sound do not perfectly match.

Найголовніше правило, яке ви повинні запам'ятати на цьому етапі, стосується використання м'якого знака. Якщо дієслово стоїть у третій особі і відповідає на питання «що робить?» або «що роблять?», ви завжди повинні писати закінчення -ться з м'яким знаком. Наприклад, «він вчиться», «вона сміється», «вони спілкуються». Але якщо дієслово стоїть у другій особі і відповідає на питання «що робиш?», м'який знак ніколи не ставиться. Ви пишете «ти вчишся», «ти смієшся», «ти спілкуєшся». Ця орфографічна різниця є критично важливою для правильного письма.

:::info
**Pronunciation of -ться and -шся**
The spelling rule is strict, but the spoken language simplifies the sounds. When you see the ending **-ться** (with the soft sign), you must pronounce it as a long, soft **[цц'а]**. When you see the ending **-шся** (without the soft sign), the sounds blend into a long, soft **[сс'а]**. So, «він вчиться» sounds like *він вчицця*, and «ти вчишся» sounds like *ти вчисся*.
:::

The choice between the full postfix **-ся** and the shortened **-сь** is purely mechanical. Look at the letter immediately preceding the postfix. If the verb ending finishes with a consonant, you attach the full **-ся**. If it finishes with a vowel, you drop the final vowel of the postfix and attach **-сь**. You can see this rhythm clearly when conjugating the verb **вчитися** (to study) in the present tense.

У першій особі однини ми маємо голосний звук у закінченні, тому додаємо короткий постфікс: «я вчуся». У другій і третій особі з'являються приголосні, тому постфікс стає повним: «ти вчишся», «він вчиться». У множині знову повертаються голосні: «ми вчимося», «ви вчитеся». Але в третій особі множини знову маємо приголосний: «вони вчаться». Це чергування відбувається автоматично.

This exact rule applies to the past tense, which makes conjugating reflexive verbs very straightforward once you know the base forms. The masculine past tense form always ends in the consonant **-в**, while the feminine, neuter, and plural forms end in vowels (**-ла**, **-ло**, **-ли**). Therefore, a man speaking about his morning routine will use the full postfix, while a woman will use the short postfix.

Якщо чоловік розповідає про свій ранок, він скаже: «Я вмивався і голився». Оскільки форма минулого часу закінчується на приголосний, він використовує повний постфікс -ся. Але якщо про свій ранок розповідає жінка, форма дієслова змінюється. Вона скаже: «Я вмивалася і фарбувалася». Тут з'являється голосний звук, тому ми використовуємо короткий постфікс -сь. У множині правило працює так само: «ми вмивалися», «ви одягалися», «вони спілкувалися».

Because verbs ending in **-ся** often describe internal states and emotions, they are incredibly common in daily conversations. When you ask someone how they are feeling or offer reassurance, you will almost certainly use these verbs to shift the focus from an external action to an internal experience.

> — **Оксана:** Привіт! Як ти почуваєшся сьогодні? *(Hi! How are you feeling today?)*
> — **Степан:** Привіт. Я трохи хвилююся перед співбесідою. *(Hi. I am worrying a little bit before the interview.)*
> — **Оксана:** Не переживай, ти добре підготувався. Усе вдасться! *(Do not worry, you have prepared well. Everything will work out!)*
> — **Степан:** Сподіваюся. А ти як? Чим займаєшся? *(I hope so. And how are you? What are you doing?)*
> — **Оксана:** Я просто насолоджуюся кавою. Мені сьогодні нікуди не треба поспішати. *(I am just enjoying coffee. I do not need to rush anywhere today.)*

In this brief exchange, almost every statement about a personal state relies on a reflexive verb. Stepan does not say that something is worrying him; he says «я хвилююся» (I am worrying). Oksana reassures him by saying «усе вдасться» (everything will work out) and describes her own relaxed state using «насолоджуюся» (I am enjoying). Mastering these verbs allows you to speak much more naturally about your feelings and relationships.

## Підсумок

Let us bring everything together into a final synthesis. The most important realization of this entire module is that time and aspect are completely intertwined in Ukrainian grammar. Your choice of aspect dictates exactly which tenses are available to you, preventing you from making illogical combinations. 

Недоконаний вид описує дію як процес, тому він має всі три часи. Ми можемо говорити про процес у минулому («я писав»), у теперішньому («я пишу») та в майбутньому («я писатиму»). Натомість доконаний вид фокусується на результаті та межі дії. Оскільки дія, яка відбувається просто зараз, ще не завершена, доконаний вид принципово не може мати теперішнього часу. Він має лише минулий час для вже досягнутого результату («я написав») та майбутній для результату, який ми плануємо отримати («я напишу»).

> *The imperfective aspect describes an action as a process, so it has all three tenses. We can talk about a process in the past ("I was writing"), in the present ("I am writing"), and in the future ("I will be writing"). In contrast, the perfective aspect focuses on the result and the limit of an action. Since an action happening right now is not yet completed, the perfective aspect fundamentally cannot have a present tense. It only has the past tense for an already achieved result ("I wrote") and the future tense for a result we plan to obtain ("I will write").*

:::info
**Система часів і видів (Tense and Aspect System)**

| Час (Tense) | Недоконаний вид (Що робити?) | Доконаний вид (Що зробити?) |
| :--- | :--- | :--- |
| **Минулий** | читав (was reading) | прочитав (read / has read) |
| **Теперішній** | читаю (am reading) | *— (неможливо)* |
| **Майбутній** | читатиму / буду читати (will be reading) | прочитаю (will read) |
:::

Before we move forward, take a moment to verify your understanding. Try to answer these four self-check questions aloud without looking back at the previous sections.

1. Провідміняйте дієслово «бачити» в теперішньому часі для всіх осіб.
2. Утворіть форми минулого часу дієслова «нести» для чоловічого, жіночого, середнього роду та множини.
3. Визначте вид таких дієслів: «гуляв», «побачив», «шукала», «знайшла».
4. Яка дієвідміна у дієслова «хотіти»? Як звучить форма третьої особи множини?

> *1. Conjugate the verb "бачити" in the present tense for all persons. 2. Form the past tense of the verb "нести" for masculine, feminine, neuter gender, and plural. 3. Determine the aspect of these verbs: "гуляв", "побачив", "шукала", "знайшла". 4. What conjugation class does the verb "хотіти" belong to? How does the third-person plural form sound?*

If you can confidently say «я бачу, ти бачиш, він бачить», remember that the consonant-stem past tense forms are «ніс, несла, несло, несли», correctly identify that «побачив» and «знайшла» represent perfective completed actions, and recall that «хотіти» unexpectedly takes the first conjugation ending «вони хочуть», 

Now that you have refreshed your knowledge of the present and past tenses, and deeply explored the logic of aspect, you hold the master key to the Ukrainian verb system. In the next module, we will step into the future.

Вид дієслова — це фундамент, на якому будується майбутній час. В українській мові існує аж три способи говорити про майбутнє. Ми можемо сказати «я зроблю», «я буду робити» або використати унікальну синтетичну форму «я робитиму». Ваш вибір між цими трьома варіантами залежатиме виключно від того, чи ви хочете описати тривалий процес, чи плануєте гарантувати чіткий результат.

> *Verb aspect is the foundation upon which the future tense is built. In the Ukrainian language, there are as many as three ways to talk about the future. We can say "я зроблю" (I will do), "я буду робити" (I will be doing), or use the unique synthetic form "я робитиму" (I will be doing). Your choice between these three options will depend entirely on whether you want to describe an ongoing process or plan to guarantee a clear result.*
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: b1-baseline-past-present
level: b1

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

**Level: B1 (Module 1)**

**Instructions in Ukrainian.** All activity types appropriate.


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
2. Run `query_cefr_level` on any word you're unsure about — it must be b1-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
