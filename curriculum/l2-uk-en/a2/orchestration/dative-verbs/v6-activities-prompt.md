<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-verbs.yaml` file for module **21: Допомагати, дякувати, дзвонити** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-dative-verbs -->`
- `<!-- INJECT_ACTIVITY: match-up-podobatysia -->`
- `<!-- INJECT_ACTIVITY: true-false-age -->`
- `<!-- INJECT_ACTIVITY: quiz-dative-vs-accusative -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete sentences with the correct dative form after dative-governing verbs
  items: 8
  type: fill-in
- focus: Choose dative vs. accusative for the underlined noun/pronoun (допомагати
    мам_ vs. бачити мам_)
  items: 8
  type: quiz
- focus: Match подобатися sentences to their English equivalents (reversed subject
    mapping)
  items: 8
  type: match-up
- focus: Judge whether age expressions use correct dative forms and number agreement
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- довіряти (to trust)
- вибачати (to forgive)
- посміхатися (to smile (at someone))
- співчувати (to sympathize (with someone))
- заздрити (to envy)
required:
- допомагати (to help)
- дякувати (to thank)
- дзвонити (to call, to phone)
- радити (to advise)
- заважати (to bother, to disturb)
- подобатися (to be pleasing to, to like (reversed syntax))
- відповідати (to answer (someone))
- рік (year)
- роки (years (2-4))
- років (years (5+))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Дієслова з давальним відмінком (Verbs That Take the Dative) (~650 words)

> — **Волонтер 1:** Сьогодні чудовий день. Я **допомагаю** (to help) бабусі нести важкі сумки додому. *(Today is a great day. I am helping a grandmother carry heavy bags home.)*
> — **Волонтер 2:** А я зараз **дзвоню** (to call, to phone) другові. Він хоче приїхати і працювати з нами. *(And I am calling a friend right now. He wants to come and work with us.)*
> — **Волонтер 1:** Це чудово. Я також **раджу** (to advise) новій сусідці гарного лікаря. Вона питала мене про це вранці. *(That is great. I am also advising a good doctor to a new neighbor. She asked me about this in the morning.)*
> — **Волонтер 2:** Ми багато робимо сьогодні. Ніхто не сидить без діла. *(We are doing a lot today. No one is sitting idle.)*
> — **Волонтер 1:** Так, мені дуже **подобається** (to be pleasing to, to like (reversed syntax)) допомагати людям у нашому районі! *(Yes, I really like helping people in our neighborhood!)*

In English, many common actions are directed straight at a person or object. You help someone, you thank someone, or you call someone. These verbs take a direct object. However, Ukrainian grammar thinks about these actions differently. In Ukrainian, these specific actions are viewed as being directed *to* or *towards* a recipient. Therefore, the person receiving the help, thanks, or phone call must be in the Dative case, which answers the questions кому? (to whom?) and чому? (to what?). The core group of verbs that require this case includes **допомагати**, **дякувати** (to thank), and **дзвонити**. You must also use the Dative case with **заважати** (to bother, to disturb) and **відповідати** (to answer (someone)). This is a very common source of mistakes for English speakers, so it requires careful attention.

:::info
**Grammar box**
In Ukrainian, the verb **дякувати** never takes a direct object. You cannot use the Accusative case here. You must always say **дякую тобі** (I give thanks *to* you). This is a major difference from English.
:::

Найчастіше ми використовуємо ці дієслова з особовими займенниками. Форми давального відмінка для займенників дуже легко запам'ятати. Запам'ятайте ці слова: мені, тобі, йому, їй, нам, вам, їм. Я завжди допомагаю їй робити домашнє завдання. Він щиро дякує тобі за такий чудовий подарунок. Ми часто дзвонимо їм увечері, щоб дізнатися останні новини. Ти ніколи не заважаєш мені працювати. Вони завжди швидко відповідають нам на всі електронні листи. Я раджу вам прочитати цю цікаву книгу. Ці займенники показують, кому саме ви даєте свою допомогу або пораду.

> *Most often we use these verbs with personal pronouns. The Dative case forms for pronouns are very easy to remember. Memorize these words: мені, тобі, йому, їй, нам, вам, їм. I always help her do homework. He sincerely thanks you for such a wonderful gift. We often call them in the evening to find out the latest news. You never bother me when I work. They always quickly answer all our emails. I advise you to read this interesting book. These pronouns show exactly to whom you give your help or advice.*

When you direct these actions to specific people rather than using pronouns, you must change the nouns into the Dative case. As a quick review, masculine nouns usually take the endings **-ові** or **-еві**, though the shorter endings **-у** or **-ю** are also common. Feminine nouns typically take the ending **-і**. However, you must pay special attention to the crucial consonant alternations that happen in feminine nouns before this ending. The back consonants г, к, and х change to з, ц, and с. For example, the word подруга changes to подрузі, and мама becomes мамі. For masculine nouns, брат becomes братові, and друг becomes другові.

Кожного тижня я дзвоню другові, щоб обговорити останні новини. Ми завжди щиро дякуємо нашій подрузі за підтримку. Лікар радить моєму братові більше відпочивати на свіжому повітрі. Цей шум на вулиці заважає мамі читати книгу. Батько відповідає вчителеві на всі його запитання про школу.

> *Every week I call my friend to discuss the latest news. We always sincerely thank our female friend for her support. The doctor advises my brother to rest more in the fresh air. This noise on the street bothers mom from reading a book. The father answers the teacher to all his questions about school.*

These Dative verbs are highly common in both negative statements and imperative commands. When you tell someone not to do something or ask them for an action, the grammatical structure remains exactly the same. The person receiving the command or the negative action stays in the Dative case. This pattern is essential for everyday conversations, especially when you need to set boundaries or ask for favors politely.

Будь ласка, допоможи мені перекласти цей текст. Не заважай мені зараз, бо я дуже зайнята. Ніколи не дзвони їй так пізно ввечері. Відповідай йому швидко, бо це важлива справа. Завжди дякуй людям за їхню добру роботу. Не радь нам того, чого ти сам не знаєш.

<!-- INJECT_ACTIVITY: fill-in-dative-verbs -->

## Мені подобається: Давальний відмінок досвідника (The Experiencer Dative with подобатися) (~550 words)

When you want to express that you like something in Ukrainian, you will use the verb **подобатися** (to be pleasing to, to like). This verb uses a sentence structure that is completely reversed compared to English. In English, the person who likes something is the grammatical subject (I, you, he), and the thing they like is the direct object. In Ukrainian, the thing that is liked acts as the grammatical subject in the Nominative case, while the person who experiences the feeling is in the Dative case. Literally, you are saying that something "is pleasing to" someone.

Мені дуже подобається тепле літо і море. Тобі подобається ця нова українська пісня. Йому не подобається холодний чай з молоком. Їй завжди подобається гуляти в парку. Нам подобається читати цікаві книжки ввечері. Вам подобається наша нова велика квартира? Їм дуже подобається жити в цьому місті.

> *I really like the warm summer and the sea. You like this new Ukrainian song. He does not like cold tea with milk. She always likes to walk in the park. We like to read interesting books in the evening. Do you like our new big apartment? They really like living in this city.*

Because the thing you like is the actual grammatical subject of the sentence, the verb must agree with it in number. When you like one single thing or an action (a verb in the infinitive), you use the singular form **подобається**. When you like multiple things (a plural noun), the verb changes to the plural form **подобаються**. The Dative pronoun at the beginning of the sentence has absolutely no effect on the ending of the verb.

:::info
**Grammar box**
Always look at the object you are talking about to choose the right verb form. If the object is singular or an infinitive verb, use `подобається`. If the object is plural, use `подобаються`.
:::

Мені подобається цей цікавий фільм про історію. Мені подобаються ці старі чорно-білі фотографії. Тобі подобається смачна кава з молоком? Тобі подобаються такі маленькі затишні кав'ярні? Моєму другові подобається працювати вдома. Моєму другові не подобаються шумні вулиці. Нам подобається ваш новий комп'ютер. Нам дуже подобаються ці розумні студенти.

> *I like this interesting film about history. I like these old black-and-white photographs. Do you like tasty coffee with milk? Do you like such small cozy cafes? My friend likes working at home. My friend does not like noisy streets. We like your new computer. We really like these smart students.*

This reversed agreement rule becomes even more obvious when you talk about the past tense. In English, "I liked" stays the same no matter what you liked. In Ukrainian, the past tense of **подобатися** must match the gender and number of the Nominative subject, not the person who liked it. If the thing you liked is a masculine noun, the verb is **подобався**. For a feminine noun, it is **подобалася**. For a neuter noun, you use **подобалося**. And for plural nouns, you must use the plural form **подобалися**.

Раніше мені дуже подобався цей старий район. Йому подобалася та нова співробітниця на роботі. Нам завжди подобалося велике і тепле море. В дитинстві їй подобалися казки про тварин. Тобі подобався вчорашній концерт у центрі міста? Моїй мамі дуже подобалася ця класична музика. Їм не подобалося жити в селі без інтернету. Нашим друзям подобалися ті смачні українські страви.

> *Earlier, I really liked this old neighborhood. He liked that new female coworker at work. We always liked the big and warm sea. In childhood, she liked fairy tales about animals. Did you like yesterday's concert in the city center? My mom really liked this classical music. They did not like living in the village without the internet. Our friends liked those tasty Ukrainian dishes.*

Asking someone what they like is a great way to start a conversation. To ask questions about preferences, you simply put the question words "що" or "хто" in the Nominative case, and the person you are asking in the Dative case. You can also use the question word "кому" (to whom) to find out who exactly likes a specific thing.

> — **Оксана:** Що тобі подобається робити на вихідних? *(What do you like to do on the weekends?)*
> — **Степан:** Мені подобається читати книжки. А тобі? *(I like to read books. And you?)*
> — **Оксана:** А мені подобається спорт. Чи подобається їм Київ? *(And I like sports. Do they like Kyiv?)*
> — **Степан:** Так, їм дуже подобається це місто. *(Yes, they really like this city.)*
> — **Оксана:** Кому подобається ця гучна музика? *(Who likes this loud music?)*
> — **Степан:** Вона подобається моєму братові. *(My brother likes it.)*

<!-- INJECT_ACTIVITY: match-up-podobatysia --> [match-up, Match подобатися sentences to their English equivalents (reversed subject mapping), 8 items]

## Скільки тобі років? Вік у давальному відмінку (Age in the Dative) (~500 words)

In English, you use the verb "to be" to state your age, saying "I am twenty years old". Ukrainian uses a different logic. Just like with the verb **подобатися**, age is something that happens *to* you. Therefore, the person whose age we are talking about is always in the Dative case. You literally say "To me is twenty years".

Коли ми говоримо про вік, ми завжди використовуємо давальний відмінок. Це дуже важливе правило в українській мові. Ми ставимо особу в давальний відмінок, потім додаємо число, а потім кажемо слово «рік» у правильній формі. Мені двадцять п'ять років. Дідусеві вісімдесят років. Моїй мамі п'ятдесят років.

> *When we talk about age, we always use the dative case. This is a very important rule in the Ukrainian language. We put the person in the dative case, then add the number, and then say the word "year" in the correct form. I am twenty-five years old. Grandpa is eighty years old. My mom is fifty years old.*

:::note
**A matter of being** — In Ukrainian, age is not an attribute you possess, but a state of being assigned to you. Think of it as "years have been given to me".
:::

The most challenging part of expressing age is choosing the correct form for the word "year". The form changes depending on the number that comes immediately before it. There are three different forms you must memorize: **рік** (year), **роки** (years), and **років** (years).

Якщо вік закінчується на число один, ми використовуємо називний відмінок однини — **рік**. Наприклад: дитині один **рік**, братові двадцять один **рік**. Якщо вік закінчується на числа два, три або чотири, нам потрібен називний відмінок множини — **роки**. Наприклад: моєму синові два **роки**, сестрі двадцять три **роки**, другові тридцять чотири **роки**.

> *If the age ends in the number one, we use the nominative singular — year. For example: the child is one year old, the brother is twenty-one years old. If the age ends in the numbers two, three, or four, we need the nominative plural — years. For example: my son is two years old, the sister is twenty-three years old, the friend is thirty-four years old.*

For all other numbers, including five and above, as well as the teen numbers (eleven through nineteen) and zero, you must use the Genitive plural form.

Для всіх інших чисел ми використовуємо форму **років**. Це числа п'ять, шість, сім, вісім, дев'ять, десять, а також усі числа від одинадцяти до дев'ятнадцяти. Також ми використовуємо цю форму для круглих десятків. Наприклад: мені п'ятнадцять **років**, батькові сорок **років**, бабусі шістдесят п'ять **років**.

> *For all other numbers, we use the form years (Genitive plural). These are the numbers five, six, seven, eight, nine, ten, as well as all numbers from eleven to nineteen. We also use this form for round tens. For example: I am fifteen years old, the father is forty years old, the grandmother is sixty-five years old.*

Asking for someone's age is straightforward. You use the question word "скільки" (how much/many) followed by the Dative form of the person you are asking about. The word "років" is always in the Genitive plural in the question because "скільки" requires it.

Щоб запитати про вік, ми кажемо: «Скільки тобі років?». Або ми можемо запитати про інших людей: «Скільки їй років?», «Скільки йому років?», «Скільки вам років?». Якщо ми запитуємо про родичів чи друзів, ми також ставимо їх у давальний відмінок. Наприклад: «Скільки років твоєму братові?», «Скільки років вашій сестрі?», «Скільки років цій дитині?».

> *To ask about age, we say: "How old are you?". Or we can ask about other people: "How old is she?", "How old is he?", "How old are you (plural/formal)?". If we ask about relatives or friends, we also put them in the dative case. For example: "How old is your brother?", "How old is your sister?", "How old is this child?".*

Let's see how these questions and answers look in a natural conversation between friends.

> — **Марко:** Привіт, Олено! Твій брат часто мені допомагає. Я хочу купити йому подарунок. Скільки йому років? *(Hi, Olena! Your brother often helps me. I want to buy him a gift. How old is he?)*
> — **Олена:** Привіт! Моєму братові двадцять один рік. А що ти хочеш купити? *(Hi! My brother is twenty-one years old. And what do you want to buy?)*
> — **Марко:** Нову комп'ютерну гру. А скільки років твоїй молодшій сестрі? *(A new computer game. And how old is your younger sister?)*
> — **Олена:** Їй тільки чотири роки. Вона дуже любить гратися. *(She is only four years old. She really likes to play.)*
> — **Марко:** Зрозуміло. До речі, а скільки років вашому дідусеві? Я знаю, що у нього скоро свято. *(I see. By the way, how old is your grandpa? I know he has a holiday soon.)*
> — **Олена:** Так, нашому дідусеві скоро сімдесят п'ять років. *(Yes, our grandpa will soon be seventy-five years old.)*

<!-- INJECT_ACTIVITY: true-false-age -->

## Давальний чи знахідний? Порівняння (Dative vs. Accusative with Verbs) (~500 words)

As your Ukrainian vocabulary grows, you will need to choose between the Dative and Accusative cases when using verbs. Conceptually, these two cases serve very different grammatical functions. The Accusative case is used for direct objects. It marks the person or thing that is directly acted upon by the verb. In contrast, the Dative case is used for indirect objects. It marks the recipient, the beneficiary, or the experiencer of an action. For example, when you use **допомагати** (to help), the action is directed toward someone. Similarly, when you need to use **дякувати** (to thank), you are directing your gratitude to a recipient.

Багато поширених дієслів в українській мові завжди вимагають знахідного відмінка. Це дієслова, які позначають пряму дію на певний об'єкт. Для перевірки ми ставимо питання «кого?» або «що?». Наприклад, дієслова «бачити», «знати», «любити» та «чекати» мають прямий додаток. Якщо ви кажете «Я бачу маму», слово «мама» стоїть у знахідному відмінку. Розглянемо інші типові приклади. «Він дуже любить старшого брата». «Ми чекаємо сестру біля школи». «Вона добре знає цього лікаря». У цих ситуаціях дія прямо спрямована на людину, тому ми використовуємо тільки знахідний відмінок.

> *Many common verbs in Ukrainian always require the accusative case. These are verbs that denote a direct action on a certain object. To check, we ask the questions "whom?" or "what?". For example, the verbs "to see", "to know", "to love", and "to wait" take a direct object. If you say "I see mom", the word "mom" is in the accusative case. Let's look at other typical examples. "He really loves his older brother." "We are waiting for the sister near the school." "She knows this doctor well." In these situations, the action is directed straight at the person, so we only use the accusative case.*

Let's look at some minimal pairs to see the difference clearly. When you use **дзвонити** (to call, to phone) or **радити** (to advise), the person is the recipient of the call or the advice. The action is not physically impacting them as a direct object. Therefore, they require the Dative case.

:::info
**Grammar box**
Some verbs can be confusing. If you use **заважати** (to bother, to disturb), remember that you are being a disturbance *to* someone. Likewise, when you need to **відповідати** (to answer (someone)), you direct your answer *to* them. Both take the Dative case!
:::

Порівняймо дієслова з різним відмінковим керуванням у коротких реченнях. Зліва ми використовуємо знахідний відмінок, а справа — давальний. Уважно подивіться на закінчення іменників. Я бачу маму, але я допомагаю мамі. Він знає брата, але він радить братові. Ми любимо подругу, але ми дзвонимо подрузі. Вона чекає лікаря, але вона дякує лікарю. Студент слухає викладача, але студент відповідає викладачеві. У першому випадку людина є об text об'єктом дії, а в другому — отримувачем.

> *Let's compare verbs with different case government in short sentences. On the left we use the accusative case, and on the right — the dative. Look carefully at the noun endings. I see mom, but I help mom. He knows the brother, but he advises the brother. We love the friend, but we call the friend. She waits for the doctor, but she thanks the doctor. The student listens to the teacher, but the student answers the teacher. In the first case, the person is the object of the action, and in the second — the recipient.*

Some verbs can comfortably take both an indirect object in the Dative case and a direct object in the Accusative case at the exact same time. These are usually verbs of giving or communicating. Also, remember the unique verb **подобатися** (to be pleasing to, to like (reversed syntax)), which always takes a Dative experiencer.

Існують дієслова, які можуть мати два додатки в одному реченні. Спочатку ми зазвичай називаємо отримувача в давальному відмінку. Потім ми вказуємо сам об'єкт у знахідному відмінку. Наприклад, візьмемо дієслово «давати». Я даю другові нову книгу. Тут слово «другові» відповідає на питання «кому?», а слово «книгу» — на питання «що?». Інший гарний приклад — дієслово «розповідати». Вона розповідає нам цікаву історію. Займенник «нам» — це давальний відмінок, а іменник «історію» — знахідний.

Finally, don't forget how we talk about age. You will always use the Dative case for the person, followed by a number and the correct form of the word for year. Depending on the number, you will choose **рік** (year), **роки** (years (2-4)), or **років** (years (5+)).

<!-- INJECT_ACTIVITY: quiz-dative-vs-accusative -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-verbs
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

**Level: A2 (Module 21/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
