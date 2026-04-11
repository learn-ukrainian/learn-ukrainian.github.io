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

> — **Дарина:** Олексію, привіт! Сто років тебе не бачила. Як твої справи після літа? *(Oleksiy, hi! I haven't seen you in ages. How are things after the summer?)*
> — **Олексій:** Привіт, Дарино! Усе чудово. Я ж все літо працював у видавництві. *(Hi, Daryna! Everything is great. I worked at the publishing house all summer.)*
> — **Дарина:** Ого, цікаво! А зараз що робиш? *(Wow, interesting! And what are you doing right now?)*
> — **Олексій:** Пишу статтю для нашого нового журналу. Тема дуже складна, тому постійно сиджу в бібліотеці або тут, у кав'ярні. *(I am writing an article for our new magazine. The topic is very complex, so I constantly sit in the library or here in the café.)*
> — **Дарина:** Розумію тебе. Я теж зараз багато читаю для університету. *(I understand you. I am also reading a lot for the university right now.)*

The present tense in Ukrainian describes actions that are happening right now, at the moment of speech, or actions that occur regularly and constantly. When you want to talk about your daily routines, your current projects, or general facts, you use the present tense.

Теперішній час в українській мові мають лише дієслова недоконаного виду. Це логічно: якщо дія відбувається саме зараз, у момент мовлення, вона ще триває і не може бути завершеною. Тому дієслова доконаного виду форм теперішнього часу не утворюють.

> *The present tense in the Ukrainian language is only formed by verbs of the imperfective aspect. This is logical: if an action is happening right now, at the moment of speech, it is still ongoing and cannot be completed. Therefore, perfective verbs do not form present tense forms.*

Ukrainian verbs in the present tense change according to person and number. This process is called conjugation. Depending on the personal endings, all Ukrainian verbs are divided into two groups: the first conjugation and the second conjugation.

До першої дієвідміни належать дієслова, які в особових закінченнях мають тематичний голосний «е» або «є». У першій особі однини вони закінчуються на «-у» або «-ю», а в третій особі множини — на «-уть» або «-ють». Повні закінчення такі: -у(-ю), -еш(-єш), -е(-є), -емо(-ємо), -ете(-єте), -уть(-ють).

> *The first conjugation includes verbs that have the thematic vowel "е" or "є" in their personal endings. In the first person singular they end in "-у" or "-ю", and in the third person plural — in "-уть" or "-ють". The full endings are: -у(-ю), -еш(-єш), -е(-є), -емо(-ємо), -ете(-єте), -уть(-ють).*

Подивімося на повну парадигму для дієслів «писати» та «знати». Я пишу, знаю.
 Ти пишеш, знаєш. Він, вона, воно пише, знає. Ми пишемо, знаємо. Ви пишете, знаєте. Вони пишуть, знають. Зверніть увагу, як голосний зберігається у всіх формах, крім першої особи однини та третьої особи множини.

The second conjugation uses a different thematic vowel.

Дієслова другої дієвідміни мають у своїх закінченнях тематичний голосний «и» або «ї». Для першої особи однини закінчення залишаються «-у» або «-ю», але третя особа множини закінчується на «-ать» або «-ять». Отже, система закінчень виглядає так: -у(-ю), -иш(-їш), -ить(-їть), -имо(-їмо), -ите(-їте), -ать(-ять).

> *Verbs of the second conjugation have the thematic vowel "и" or "ї" in their endings. For the first person singular, the endings remain "-у" or "-ю", but the third person plural ends in "-ать" or "-ять". Thus, the system of endings looks like this: -у(-ю), -иш(-їш), -ить(-їть), -имо(-їмо), -ите(-їте), -ать(-ять).*

Розглянемо дієвідмінювання на прикладі типових слів «робити» та «говорити». Я роблю, говорю. Ти робиш, говориш. Він, вона, воно робить, говорить. Ми робимо, говоримо. Ви робите, говорите. Вони роблять, говорять. Голосний «и» чітко чути в більшості форм.

It can sometimes be difficult to look at an infinitive and immediately know which conjugation class it belongs to based purely on the spelling of the dictionary form.

:::tip
**The third person plural trick** — the most reliable way to identify the conjugation class is to look at the form for «вони» (they). If the verb ends in «-уть» or «-ють», it belongs to the first conjugation. If it ends in «-ать» or «-ять», it belongs to the second conjugation.
:::

Цей метод допомагає з дієсловами, які виглядають як винятки. Наприклад, слово «хотіти» закінчується на «-іти», як багато дієслів другої дієвідміни. Але форма третьої особи множини — «хочуть» (а не «хотять»). Тому це перша дієвідміна. Слово «стояти» закінчується на «-яти», але ми кажемо «стоять» (а не «стоють»), тому це друга дієвідміна.

When you conjugate verbs, you might notice that sometimes the final consonant of the root changes before the ending. This phenomenon is called consonant alternation. 

В українській мові чергування приголосних у теперішньому часі найчастіше відбувається лише в першій особі однини для дієслів другої дієвідміни. Наприклад, звук «д» змінюється на «дж» (сидіти — сиджу, водити — воджу). Звук «с» змінюється на «ш» (просити — прошу). Звук «з» переходить у «ж» (возити — вожу).

> *In the Ukrainian language, consonant alternation in the present tense most often occurs only in the first person singular for verbs of the second conjugation. For example, the sound "д" changes to "дж" (сидіти — сиджу, водити — воджу). The sound "с" changes to "ш" (просити — прошу). The sound "з" changes to "ж" (возити — вожу).*

Крім того, губні приголосні «б», «п», «в», «м», «ф» отримують додатковий звук «л» перед закінченням «-ю». Тому ми кажемо любити — люблю, робити — роблю, спати — сплю. В усіх інших особах основа залишається без змін (ти робиш, він любить).

:::info
**Decolonization marker** — a key feature of the modern Ukrainian language is the dropping of the final «-ть» in the third person singular for verbs of the first conjugation. We say «він знає», «вона пише», «воно несе». In Russian, this ending is preserved. This morphological difference is a strong marker of Ukrainian linguistic identity.
:::

<!-- INJECT_ACTIVITY: group-sort-distribute-verbs-between-i-and-ii-conjugation-classes -->

## Минулий час: утворення і вживання

The formation of the past tense in the Ukrainian language is a fairly simple and logical process that builds upon the dictionary form of the word. To get the past tense form, you take the infinitive stem and add the appropriate suffixes. The infinitive stem is the part of the word that remains if you drop the ending «-ти». To this stem, you add the suffix «-в» for the masculine gender. For the feminine gender, you use the suffix «-л-» followed by the ending «-а». For the neuter gender, you use the suffix «-л-» followed by the ending «-о». Finally, for the plural form, you use the suffix «-л-» followed by the ending «-и». For example, if you take the word «читати», its stem is «чита-». By adding the suffixes, you get the complete set of forms: він читав, вона читала, воно читало, and вони читали. This reliable principle works perfectly for the vast majority of Ukrainian verbs, regardless of their conjugation class. The past tense gives you the essential ability to narrate stories, share personal memories, and describe events that have already occurred in the past.

Коли ми використовуємо дієслова в теперішньому часі, ми повинні змінювати їхні закінчення залежно від особи, яка виконує дію. Минулий час працює за зовсім іншою логікою. У минулому часі дієслова повністю ігнорують граматичну категорію особи. Замість цього вони повинні узгоджуватися з підметом у роді та числі. Це фундаментальна концепція, яка називається граматичним узгодженням. В англійській мові форма минулого часу залишається однаковою незалежно від того, хто виконує дію. В українській мові дієслово працює як дзеркало, що відображає стать і кількість виконавців дії. Якщо чоловік говорить про себе, він використовує форму чоловічого роду і каже «я читав». Якщо говорить жінка, вона обов'язково повинна сказати «я читала». Якщо в дії беруть участь кілька людей, ми завжди використовуємо форму множини «ми читали».

:::info
**Grammar box** — The pronoun **ти** (you) takes either a masculine or a feminine verb in the past tense, depending entirely on the gender of the person you are speaking to.
:::

Звичайно, кожне правило має свої винятки, і українська мова має особливу групу дієслів минулого часу. Деякі дієслова мають основу інфінітива, яка закінчується на приголосний звук. Наприклад, це такі базові слова, як «нести», «могти» або «бігти». Для цих дієслів форма чоловічого роду в минулому часі утворюється без суфікса «-в». Ми просто використовуємо чисту основу: він ніс, він міг, він біг. Крім того, у цих словах часто відбувається фонетичне чергування голосних звуків. Голосні «о» або «е» переходять у звук «і» в закритому складі, тобто такому, що закінчується на приголосний. Тому ми кажемо «він ніс», де склад закритий. Але коли ми додаємо закінчення для жіночого роду чи множини, склад стає відкритим, і початковий голосний звук повертається. Тому ми кажемо: вона несла, вони несли. Аналогічно працює слово «могти»: він міг, але вона могла.

:::tip
**Did you know?** — The vowels **о** and **е** disappearing or changing to **і** is one of the most common phonetic rules in Ukrainian, known as the rule of open and closed syllables.
:::

Let's revisit the dialogue from the beginning of this module where two friends were catching up at a café. In their conversation, we can see exactly how this grammatical agreement functions in natural speech. Олексій says, «Я працював у видавництві». Because he is a man, he uses the masculine suffix «-в» to describe his past employment. Later, describing a shared trip with his friends, he says, «Минулого літа ми їздили до Львова». Here, the subject is «ми» (we), which requires the plural suffix «-л-» and the plural ending «-и». The verb automatically adapts to match the plural number of the subject. Whenever you narrate your own past experiences, you must constantly be aware of your own gender identity and choose the correct verb ending accordingly.

Одна з найпоширеніших помилок серед студентів — це неправильне узгодження роду в минулому часі. Часто можна почути речення на кшталт: «Моя сестра сказав». Це відбувається тому, що студенти забувають про необхідність адаптувати дієслово до підмета. Важливо пам'ятати, що дієслово в минулому часі — це дзеркало суб'єкта. Якщо підмет має жіночий рід, як слово «сестра», дієслово обов'язково повинно мати закінчення жіночого роду: «Моя сестра сказала». Так само треба бути уважним, коли ви звертаєтеся до когось на «ти». Якщо ви питаєте чоловіка, ви кажете: «Де ти був?». Але якщо ви питаєте жінку, ви повинні запитати: «Де ти була?».

> *One of the most common mistakes among students is incorrect gender agreement in the past tense. Often you can hear sentences like: "Моя сестра сказав". This happens because students forget about the need to adapt the verb to the subject. It is important to remember that the verb in the past tense is a mirror of the subject. If the subject has a feminine gender, like the word "сестра", the verb must absolutely have a feminine ending: "Моя сестра сказала". Similarly, you need to be careful when you address someone as "ти". If you are asking a man, you say: "Де ти був?". But if you are asking a woman, you must ask: "Де ти була?".*

Минулий час використовується для різних цілей у розповіді. Ви можете використовувати його для опису тривалих станів у минулому або для переліку послідовних подій. Українська мова має два різні види дієслів, щоб передати ці відтінки значень. Форми «робив» і «зробив» обидві існують у минулому часі, але вони означають різні речі. Слово «робив» показує процес дії, тоді як слово «зробив» акцентує увагу на результаті та завершеності. Вибір правильного слова залежить від того, чи хочете ви описати фон історії, чи конкретну дію, яка змінила ситуацію. Ми детальніше розглянемо цю різницю в наступних розділах.

<!-- INJECT_ACTIVITY: fill-in-tense-forms -->

## Вид дієслова: доконаний і недоконаний

When narrating past events or describing actions in Ukrainian, you must make a fundamental choice that simply does not exist in English in the same way. This is the critical concept of aspect, or «вид дієслова». Every verb in the Ukrainian language inherently belongs to one of two categories: the imperfective aspect («недоконаний вид») or the perfective aspect («доконаний вид»). The imperfective aspect focuses entirely on the process, duration, or repetition of an action. It answers the question «що робити?». You can think of it as watching a continuous video recording of an event as it unfolds over time, without any clear beginning or end. The perfective aspect, on the other hand, focuses on the result, the successful completion, or the absolute boundary of an action. It answers the question «що зробити?». Think of the perfective aspect as a photograph capturing the final outcome of an event. For example, the verb «писати» (to write) is imperfective, representing the ongoing act of writing a letter. Its perfective partner, «написати», means to successfully complete the writing process, producing a finished letter that is ready to be sent.

Вид дієслова нерозривно пов'язаний із граматичним часом. Дієслова недоконаного виду мають три повноцінні часи: минулий, теперішній та майбутній. Ви можете вільно сказати «я писав», «я пишу» та «я буду писати». Натомість дієслова доконаного виду мають лише дві часові форми: минулий та майбутній час. Вони принципово не можуть мати форми теперішнього часу. Чому так відбувається? Логіка української мови підказує, що дія, яка відбувається просто зараз, у момент мовлення, за визначенням не може бути завершеною. Якщо ви зараз виконуєте дію, вона є процесом. Тому форма «я напишу», хоча й виглядає за своєю структурою та закінченнями подібно до теперішнього часу, насправді є простою формою майбутнього часу. Вона означає, що ви гарантуєте певний результат у майбутньому. Коли студенти намагаються буквально перекласти англійське "I am reading" і помилково використовують доконаний вид, це звучить для носіїв мови дуже неприродно.

> *Verb aspect is inextricably linked to grammatical tense. Imperfective verbs have three full tenses: past, present, and future. You can freely say "I was writing", "I am writing", and "I will write". In contrast, perfective verbs have only two tense forms: past and future. They fundamentally cannot have a present tense form. Why does this happen? The logic of the Ukrainian language suggests that an action happening right now, at the moment of speech, cannot be completed by definition. If you are performing an action now, it is a process. Therefore, the form "я напишу", although it looks similar in structure and endings to the present tense, is actually a simple future tense form. It means that you guarantee a certain result in the future. When students try to literally translate the English "I am reading" and mistakenly use the perfective aspect, it sounds very unnatural to native speakers.*

To successfully navigate this system, you need to learn verbs in aspectual pairs («видові пари»). While there is not one single universal rule for forming these pairs, there are highly predictable patterns that you will quickly recognize. The most common method is prefixation, where a specific prefix is added to an imperfective verb to make it perfective. For example, «читати» (to read) becomes «прочитати» (to finish reading), and «робити» (to do) becomes «зробити» (to get done). Another frequent pattern is suffixation, which often works in reverse: changing a suffix transforms a perfective verb into an imperfective one, highlighting the ongoing, extended nature of the action. We see this in pairs like «вирішити» (perfective) and «вирішувати» (imperfective), or «показати» and «показувати». Finally, some of the most common everyday actions use entirely suppletive pairs. These are pairs where the two verbs come from completely different roots. You must simply memorize that the imperfective «брати» (to take) pairs with the perfective «взяти», and «говорити» (to speak or to say) pairs with «сказати».

:::info
**Grammar box** — The prefix in a perfective verb does not always just change the aspect; it can sometimes alter the subtle nuance or meaning of the verb. However, in a true aspectual pair like «робити» and «зробити», the prefix merely adds the idea of "completion" without changing the fundamental dictionary definition.
:::

Вибір правильного виду в минулому часі залежить від того, на чому ви хочете зосередити увагу співрозмовника. Порівняйте два питання: «Що ти робив учора?» та «Що ти зробив учора?». Перше питання цікавиться вашим проведенням часу, звичайним процесом. На нього логічно відповісти: «Я читав книжку дві години». Тут ми бачимо типовий недоконаний вид, який підкреслює тривалість дії. Друге питання вимагає чіткого звіту про результати. На нього краще відповісти: «Я прочитав книжку». Це означає, що ви дійшли до останньої сторінки, і дія має логічний кінець. Якщо ви скажете «Я вчора прочитав книжку три години», це буде серйозною граматичною помилкою, адже доконаний вид несумісний із вказівкою на тривалість процесу. Українці відчувають цю різницю інтуїтивно, завжди обираючи між описом загального фону та фіксацією конкретного досягнення.

Mastering this nuanced distinction between perfective and imperfective verbs is arguably the most crucial step in making your Ukrainian sound authentic and fluent. It shifts your speech from sounding like a mechanical, direct translation of English grammar into something that naturally reflects the traditional Ukrainian way of viewing the world. English relies heavily on complex tense structures like the Past Continuous or the Present Perfect to convey subtle shifts in time and completion. Ukrainian achieves this same elegance simply by selecting the correct verb aspect. This system keeps the basic tense structure remarkably straightforward while packing the verb itself with profound, built-in meaning about the boundaries of time, process, and ultimate completion.

<!-- INJECT_ACTIVITY: quiz-aspect-id -->
<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->

## Вид у розповіді: послідовність і тло

When we tell a story, we are essentially painting a picture with time. In Ukrainian, verb aspect is your primary tool for this artistic process. To create a dynamic and natural-sounding narrative, we divide actions into two distinct categories: the foreground and the background. The foreground consists of the main sequential events that drive the story forward. These are completed actions, and they absolutely require the perfective aspect. Think of them as the solid steps on a staircase: he woke up, he got dressed, and he left the house. Each action must finish completely before the next one can begin. The background, on the other hand, sets the scene. It describes the weather conditions, the emotional state of the characters, or ongoing situations that surround the main events. For this, we rely on the imperfective aspect. It is the broad canvas upon which the specific events happen: the sun was shining brightly, people were walking in the park, and a soft breeze was blowing. Understanding this division is the key to telling stories like a native speaker.

Уявіть, що ви розповідаєте друзям про свій типовий ранок. Спочатку ви створюєте загальне тло: надворі яскраво світило сонце, співали ранкові пташки, а на кухні приємно пахло свіжою кавою. Це все дієслова недоконаного виду, які чудово описують процес та атмосферу. А потім починається ваша основна дія: я раптом прокинувся, швидко встав з ліжка, вмився холодною водою і смачно поснідав. Тут ми чітко бачимо ланцюжок подій, де кожне дієслово доконаного виду фіксує конкретний результат і активно рухає вашу історію вперед.

> *Imagine you are telling friends about your typical morning. First, you create the general background: outside the sun was shining brightly, morning birds were singing, and the kitchen smelled pleasantly of fresh coffee. These are all imperfective verbs that perfectly describe the process and atmosphere. And then your main action begins: I suddenly woke up, quickly got out of bed, washed my face with cold water, and had a tasty breakfast. Here we clearly see a chain of events where each perfective verb records a specific result and actively moves your story forward.*

The true magic of storytelling happens when these two aspectual layers interact with each other. A very common narrative technique is to have a calm, ongoing background action suddenly interrupted by a new, completed event. In Ukrainian, we typically connect these two different aspects with words like **коли** (when) or **раптом** (suddenly). The ongoing action always takes the imperfective aspect, establishing the setting, while the quick interrupting event demands the perfective aspect.

Я спокійно обідав у затишному кафе, коли несподівано зателефонував мій старий друг Тарас. Ми їхали в переповненому автобусі вже дві години, і раптом він різко зупинився посеред дороги. У цих реченнях тривала дія слугує своєрідним фоном для швидкої, результативної події, яка раптово змінює всю ситуацію. Такий контраст робить розповідь живою та цікавою.

Contrast this dramatic interruption with a situation where two actions happen simultaneously without interfering with each other. If you want to describe parallel processes, both verbs must remain imperfective. You will often use the word **поки** (while) to build this specific structure. For example, you can say **Поки я обідав, Тарас читав новини** (*While I was having lunch, Taras was reading the news*). This creates a sense of shared time and ongoing activity without advancing the narrative.

Because English relies heavily on surrounding context or prepositions rather than the verb form itself to show completion, learners frequently make critical errors when adding time markers to their Ukrainian sentences. A classic grammatical mistake is combining a perfective verb with a specific duration of time. In English, you can simply say you read for an hour and let the context decide if you finished the book. In Ukrainian, the verb itself forces you to declare your intention. You cannot mix a verb that declares finality with a time phrase that describes an ongoing process.

:::info
**Grammar box** — Never use a perfective verb with phrases that indicate duration, like **дві години** (two hours) or **весь день** (all day). If you specify how long an action lasted, you are inherently focusing on the process, which strictly demands the imperfective aspect.
:::

Consider the incorrect sentence **Вчора я прочитав книжку три години** (*Yesterday I finished reading a book for three hours*). A native Ukrainian speaker will be very confused by this phrasing. The perfective verb «прочитати» guarantees that you reached the absolute end of the action, but the phrase «три години» describes the ongoing, extended process of reading. These two conceptual ideas clash violently. You must consciously choose your conversational focus: either the continuous process or the final result. If you focus on the process, say **Вчора я читав книжку три години** (*Yesterday I was reading a book for three hours*). If you focus on the result, simply say **Вчора я прочитав цю книжку** (*Yesterday I finished reading this book*). Always prioritize the strict logic of result over process when deciding to use the perfective aspect in your past tense narratives.

To truly understand how aspect dramatically shapes a narrative, let us look at the exact same sequence of past events told in two completely different ways. The first version focuses purely on facts, achievements, and forward momentum, using only perfective verbs. This creates a fast-paced sequence where each action triggers the next. It feels like a checklist of accomplishments.

Вчора ми нарешті приїхали до Києва. Ми швидко вийшли з гамірного вокзалу, взяли жовте таксі та поїхали прямо до центру міста. Там ми знайшли гарне кафе, замовили традиційний борщ і смачно пообідали. Після цього ми купили квитки в кіно та подивилися новий фільм.

This version is exceptionally clear and efficient, reading almost like a formal police report or a checklist of completed tasks. It is purely focused on the foreground. Notice how the entire emotional vibe changes when we shift our focus away from the results. We can emphasize the process and the lived experience using imperfective verbs.

Вчора ми цілий день гуляли сонячним Києвом. Ми повільно йшли широкими вулицями, із захопленням роздивлялися старовинну архітектуру та слухали талановитих вуличних музикантів. У маленькому кафе ми довго сиділи біля вікна та не поспішаючи їли гарячий борщ. Увечері ми знову блукали містом, насолоджуючись теплою погодою.

By simply changing the verb aspect, the exact same story transforms from a dry list of completed tasks into a rich, immersive, and atmospheric memory. Mastering this subtle shift between sequence and background gives you complete artistic control over the mood and flow of your Ukrainian sentences. You are no longer just reporting facts; you are painting a vibrant picture for your listener. This is the true power of the Ukrainian aspectual system.

<!-- INJECT_ACTIVITY: error-correction-aspect -->
<!-- INJECT_ACTIVITY: open-writing-yesterday -->

## Дієслова на -ся: зворотні дієслова

Many learners assume that verbs ending in **-ся** or **-сь** are strictly reflexive, meaning the action is performed upon oneself. While often true, the Ukrainian postfix **-ся** is a much broader grammatical tool. It alters the relationship between the subject and the action in several distinct ways. We can group these verbs into four main categories based on their core meaning.

Перша категорія — це власне зворотні дієслова. Тут дія дійсно спрямована на самого діяча: «я миюся» або «вона одягається». Друга категорія — взаємна дія. Кілька людей виконують дію одне до одного: «ми зустрічаємося» або «вони цілуються». Третя категорія описує внутрішній, емоційний стан. Дієслова «радуватися», «дивуватися» чи «хвилюватися» показують почуття без зовнішнього об'єкта.

> *The first category is strictly reflexive verbs. Here, the action is indeed directed at the doer: "I wash myself" or "she dresses herself." The second category is mutual action. Several people perform an action toward each other: "we meet" or "they kiss." The third category describes an internal, emotional state. Verbs like "to rejoice," "to be surprised," or "to worry" show feelings without an external object.*

Finally, the fourth category consists of impersonal verbs. These describe states or desires that seem to happen to us independently of our will. You will often hear native speakers say **мені не спиться** (I can't sleep) or **їй хочеться** (she feels like). Notice how the subject in these sentences is in the dative case, positioning the person as the receiver of the state rather than the active doer.

When writing verbs with the **-ся** postfix, the most common spelling mistake made by both learners and native speakers involves the soft sign. In the present tense, you must pay close attention to the difference between the second person (you) and the third person (he/she/it/they).

Дієслова на «-ться» для третьої особи ми завжди пишемо з м'яким знаком. Наприклад, ви можете сказати: він щиро усміхається, вона уважно вчиться, вони голосно сміються. Але дієслова на «-шся» для другої особи ми завжди пишемо без м'якого знака: ти радісно усміхаєшся, ти добре вчишся. Якщо питання звучить як «що робить?» або «що роблять?», обов'язково потрібен м'який знак. Якщо ж питання звучить як «що робиш?», м'який знак писати заборонено.

The confusion usually arises because of how these words are pronounced. In natural speech, the ending **-ться** is pronounced smoothly as a long, soft «цця» sound, making the soft sign hard to hear. Meanwhile, **-шся** sounds exactly as it is written. Trust the grammatical person, not just your ear.

:::info
**Grammar box** — The golden rule of the soft sign: The second person **ти** (you) never takes a soft sign before the postfix: **ти дивишся** (you look). The third person **він/вона** (he/she) always takes a soft sign: **вона дивиться** (she looks).
:::

Another mechanical rule to master is the alternation between the full postfix **-ся** and its shortened form **-сь**. This change is driven purely by phonetics to make the language flow smoothly. If the verb ending before the postfix is a consonant, you must use **-ся**. If the verb ending is a vowel, you should shorten the postfix to **-сь**.

Розглянемо минулий час дієслова «вчитися». Коли ми говоримо про чоловіка, дієслівна форма закінчується на приголосний звук «в». Тому ми додаємо повний варіант постфікса: він вчився. Але для жінки, середнього роду чи множини основа закінчується на голосний звук. Тоді цей постфікс можна скоротити: вона вчилася або вона вчилась, вони вчилися або вони вчились. Обидва варіанти є граматично правильними, проте коротка форма «-сь» звучить набагато швидше та природніше у щоденній розмові.

In the present tense, the conjugation follows the standard rules, with the postfix securely attached at the very end: **я вчуся, ти вчишся, він вчиться, ми вчимося, ви вчитеся, вони вчаться**. As you can see, the verb changes normally according to its conjugation class while the postfix remains attached. Your main task is to learn to perceive this word as a single whole, not as a verb with a separate addition.

To truly integrate these verbs into your active vocabulary, you must practice using them to describe your states and emotions. Reflexive verbs are incredibly common in daily Ukrainian conversations, especially when asking about someone's well-being or sharing your own feelings. Let us look at a natural dialogue between two friends discussing an upcoming event.

> — **Марія:** Як ти почуваєшся перед іспитом? *(How do you feel before the exam?)*
> — **Олег:** Я дуже хвилююся. Мені навіть не спиться вночі. *(I am very worried. I can't even sleep at night.)*
> — **Марія:** Не переживай так сильно. Я впевнена, що тобі все вдасться. *(Don't worry so much. I am sure everything will work out for you.)*
> — **Олег:** Сподіваюся. Ми ж так довго готувалися. *(I hope so. We prepared for so long, after all.)*

Notice how **хвилююся** (I worry) and **почуваєшся** (you feel) express internal states. The impersonal construction **мені не спиться** perfectly captures the feeling of insomnia happening *to* Oleg, rather than him actively choosing not to sleep. The verb **вдасться** (will work out / will succeed) is another essential reflexive verb that is almost always used in the third person. Mastering these natural expressions will make your Ukrainian sound much more authentic and emotionally resonant.

## Підсумок

Час підбити підсумки та скласти всі пазли цієї граматичної картини в єдине ціле. Найважливіший висновок цього модуля полягає в тому, що час і вид дієслова — це не дві окремі теми, а єдина система. Вид дієслова безпосередньо визначає, які часові форми воно може мати.

> *It is time to summarize and put all the pieces of this grammatical picture together. The most important conclusion of this module is that verb tense and aspect are not two separate topics, but a single system. The aspect of a verb directly determines which tense forms it can have.*

Дієслова недоконаного виду описують дію як процес, тому вони мають форми у всіх трьох часах: у минулому («я писав»), у теперішньому («я пишу») та в майбутньому («я буду писати» або «я писатиму»). Дієслова доконаного виду позначають завершену дію або результат. Оскільки дія, що відбувається зараз, ще не може бути завершеною, доконаний вид не має форми теперішнього часу. Він існує лише в минулому («я написав») та майбутньому («я напишу»).

:::info
**Grammar box** — The Aspect-Tense Matrix
- **Недоконаний вид** (Imperfective): Минулий (писав), Теперішній (пишу), Майбутній (писатиму / буду писати).
- **Доконаний вид** (Perfective): Минулий (написав), Майбутній (напишу).

Remember: If a verb answers the question «що зробити?», you cannot put it in the present tense.
:::

Тепер час перевірити ваші знання. Провідміняйте дієслово «бачити» в теперішньому часі. Правильні форми: я бачу, ти бачиш, він бачить, ми бачимо, ви бачите, вони бачать. Далі, утворіть усі форми минулого часу дієслова «нести». Пам'ятайте про відсутність суфікса в чоловічому роді: він ніс, вона несла, воно несло, вони несли.

> *Now it is time to check your knowledge. Conjugate the verb "бачити" (to see) in the present tense. The correct forms are: я бачу, ти бачиш, він бачить, ми бачимо, ви бачите, вони бачать. Next, form all past tense forms of the verb "нести" (to carry). Remember the absence of a suffix in the masculine gender: він ніс, вона несла, воно несло, вони несли.*

Визначте вид таких дієслів: «гуляв», «побачив», «шукала», «знайшла», «працювали». Дієслова «гуляв», «шукала» та «працювали» відповідають на питання «що робив?» або «що робила?» і означають процес, тому це недоконаний вид. «Побачив» і «знайшла» відповідають на питання «що зробив?» або «що зробила?» і вказують на результат, отже, це доконаний вид. Яка дієвідміна у дієслова «хотіти»? Це виняток. Воно належить до першої дієвідміни, тому в третій особі множини ми кажемо «вони хочуть».

У наступному модулі ми зробимо крок у майбутнє. Ми детально розберемо майбутній час і дізнаємося, чому в українській мові існує аж три способи говорити про дії, які ще не відбулися. Ви навчитеся розрізняти просту форму («зроблю»), складену («буду робити») та унікальну синтетичну форму («робитиму»), яка є візитною карткою української мови.

> *In the next module, we will take a step into the future. We will analyze the future tense in detail and learn why there are as many as three ways to talk about actions that have not yet happened in the Ukrainian language. You will learn to distinguish between the simple form ("зроблю"), the compound form ("буду робити"), and the unique synthetic form ("робитиму"), which is a hallmark of the Ukrainian language.*

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
