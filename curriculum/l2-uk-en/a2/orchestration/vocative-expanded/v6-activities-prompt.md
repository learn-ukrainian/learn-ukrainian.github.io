<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/vocative-expanded.yaml` file for module **27: Пане лікарю! Друже мій!** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-focus-form-the-correct-vocative-of-professional-titles-and-names -->`
- `<!-- INJECT_ACTIVITY: match-professions-vocative -->`
- `<!-- INJECT_ACTIVITY: error-correction-vocative -->`
- `<!-- INJECT_ACTIVITY: quiz-register-choice -->`
- `<!-- INJECT_ACTIVITY: group-sort-registers -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Form the correct vocative of professional titles and names (пане _____, пані
    _____)
  items: 8
  type: fill-in
- focus: Choose the correct vocative register for a given social situation
  items: 8
  type: quiz
- focus: Match nominative forms to their vocative equivalents (лікар → лікарю, вчитель
    → вчителю, друг → друже)
  items: 8
  type: match-up
- focus: Fix vocative errors (*пан лікар → пане лікарю, *друже моя → подруго моя,
    *Мій друже → Друже мій)
  items: 8
  type: error-correction
- focus: Sort vocative forms by register (formal, professional, emotional)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- добродій (sir (literary/diaspora))
- добродійка (madam (literary/diaspora))
- емоційний (emotional)
- ніжний (tender, affectionate)
- колега (colleague)
required:
- кличний (vocative (case))
- звертання (address, appeal)
- пан (Mr., sir)
- пані (Mrs., Ms., madam)
- лікар (doctor)
- вчитель (teacher)
- друг (friend)
- ввічливий (polite)
- офіційний (official, formal)
- професія (profession)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Пане, пані: формальне звертання (Formal Address)

У базовому курсі ми вивчали прості форми звертання. Ви знаєте, як сказати **«Тарасе!»** *(Taras!)* або **«Олено!»** *(Olena!)*. Але для роботи та **офіційних** *(official, formal)* ситуацій нам потрібні формальні **звертання** *(addresses)*. Ukrainian culture highly values polite and formal address in professional or unfamiliar settings. The vocative case (**кличний відмінок** *(vocative case)*) is mandatory when you address someone directly. Using the nominative case for address is a serious grammatical error and is often considered a Russianism. Якщо ви скажете **«Привіт, Наталя!»** *(Hi, Nataliya!)*, це звучить неприродно. Українці так не говорять. Правильно казати **«Привіт, Наталю!»** *(Hi, Nataliya!)*. Для поваги ми додаємо слова **пан** *(Mr., sir)* та **пані** *(Mrs., Ms., madam)*. Отже, ми кажемо **«Пані Маріє!»** *(Ms. Mariia!)* замість просто «Маріє». Це дуже важливе правило нашої мови.

Ми часто використовуємо конструкцію «пане» або «пані» плюс **професія** *(profession)*. The word **«пане»** *(sir)* is the vocative form of «пан», and it triggers the vocative case in the following noun. Both words must change. For hard-stem masculine nouns, the ending is usually **-е**. Ми кажемо: **«пане директоре»** *(Mr. director)*, **«пане професоре»** *(Mr. professor)*, **«пане міністре»** *(Mr. minister)*. For soft-stem masculine nouns, the ending is **-ю**. Тому правильно казати: **«пане лікарю»** *(Mr. doctor)*, **«пане вчителю»** *(Mr. teacher)*, **«пане водію»** *(Mr. driver)*. For women, the word «пані» is invariable (it never changes its form). However, the feminine profession takes the vocative ending **-о**. В українській мові ми активно використовуємо жіночі форми професій. Тому ми кажемо: **«пані вчителько»** *(Ms. teacher)*, **«пані директорко»** *(Ms. director)*, **«пані лікарко»** *(Ms. doctor)*. Це показує вашу повагу.

Ми також можемо використовувати ці слова з прізвищами людей. When we address a man by his surname, the surname must also be in the vocative case if it is a declinable noun. Masculine surnames ending in -о or -ко typically take the **-у** ending in the vocative. Тому ми кажемо: **«пане Коваленку»** *(Mr. Kovalenko)*, **«пане Шевченку»** *(Mr. Shevchenko)*, **«пане Ковальчуку»** *(Mr. Kovalchuk)*. The grammatical rule is very different for women. As we know, «пані» does not change. In addition, feminine surnames ending in a consonant or in -о/-ко are indeclinable in Ukrainian grammar. Вони завжди мають форму називного відмінка. Тому ми кажемо: **«пані Коваленко»** *(Ms. Kovalenko)*, **«пані Шевченко»** *(Ms. Shevchenko)*, **«пані Ковальчук»** *(Ms. Kovalchuk)*. Це правило треба запам'ятати.

Слова «пан» і «пані» мають глибоке історичне коріння в українській культурі. Вони існували багато століть. During the Soviet era, these traditional polite forms were actively suppressed and banned from official language. The regime replaced them with the word **«товариш»** *(comrade)* to enforce artificial equality and Russian linguistic norms. Сьогодні використання слів «пане» та «пані» — це ваш свідомий вибір. It strongly signals authentic, decolonized Ukrainian identity and respect for the listener. Це справжнє повернення до нашої рідної мови. Ви можете часто почути цю красиву форму в давніх текстах і народних піснях. Є відома різдвяна колядка: **«Добрий вечір тобі, пане господарю!»** *(Good evening to you, Mr. host!)*.

В українській мові також є красиві слова **«добродій»** *(sir, gentleman)* та **«добродійка»** *(madam, lady)*. Вони теж мають спеціальні форми кличного відмінка: **«добродію»** *(sir)* та **«добродійко»** *(madam)*. These are older, highly literary alternatives to «пане» and «пані». Today, they are much less common in everyday street conversation or modern slang. However, they remain very polite, highly respected forms used in formal writing, official letters, or by the Ukrainian diaspora. В офіційному листі ви пишете: **«Шановний добродію!»** *(Honorable sir!)* або **«Вельмишановна добродійко!»** *(Highly honorable madam!)*. Це звучить дуже інтелігентно та надзвичайно **ввічливо** *(politely)*. Використовуйте ці слова для створення особливого стилю.

<!-- INJECT_ACTIVITY: fill-in-focus-form-the-correct-vocative-of-professional-titles-and-names -->


## Професійні звертання (Professional Vocative)

Уявіть ситуацію на роботі або в університеті. Ви хочете звернутися до свого керівника, викладача або колеги. В українській мові ми використовуємо спеціальний кличний відмінок для назв **професій** *(professions)*. For masculine professional titles, the vocative ending depends directly on the final consonant of the word. Якщо слово закінчується на твердий приголосний звук, ми зазвичай додаємо закінчення **-е**. Наприклад, **інженер** *(engineer)* стає «інженере». Слово **майстер** *(master, foreman)* стає «майстре». Якщо слово закінчується на м'який приголосний звук, ми додаємо закінчення **-ю**. Наприклад, **лікар** *(doctor)* має форму «лікарю», а **вчитель** *(teacher)* стає «вчителю». Слово **водій** *(driver)* також має форму «водію». There is an important note about masculine words ending in the -ер or -ор suffixes, like **професор** *(professor)* or **директор** *(director)*. These are hard stems in Ukrainian, so they always take the -е ending: «професоре», «директоре». Ми часто використовуємо ці форми в офіційній розмові.

Українська мова має дуже красиву та важливу особливість. Ми активно, часто та природно використовуємо **фемінітиви** *(femininitives)* у повсякденному житті. Це жіночі форми назв професій та соціальних ролей. For women, we use the first declension pattern that you learned previously in the A1 level. Більшість таких сучасних слів закінчується на суфікс **-ка** або на літеру **-а**. У кличному відмінку ці слова завжди і без винятків мають закінчення **-о**. Наприклад, слово **вчителька** *(female teacher)* стає «вчителько». Слово **лікарка** *(female doctor)* має форму «лікарко», а **журналістка** *(female journalist)* легко стає «журналістко». Популярне слово **директорка** *(female director)* має правильну форму «директорко». This reinforces the "feminine-hard" declension pattern perfectly. Ми можемо сказати просто «лікарко». Або ми додаємо слово «пані» для більшої поваги: «пані лікарко». Це звучить дуже ввічливо, професійно та сучасно.

Існують також спеціальні слова, які ми однаково використовуємо для чоловіків і для жінок. Наприклад, популярне слово **колега** *(colleague)*. Це слово має спільний рід. У кличному відмінку воно завжди має форму «колего». Ми з повагою кажемо «колего Андрію» або «колего Маріє». Інше важливе слово у цій групі — це **суддя** *(judge)*. Воно закінчується на м'який приголосний, тому в кличному відмінку завжди має форму «суддю». Також є класичне слово **товариш** *(friend, comrade)*. Це іменник мішаної групи. У кличному відмінку він має закінчення **-у**. Тому ми кажемо «товаришу». Пам'ятайте ці спеціальні форми, коли ви працюєте або навчаєтесь в українському колективі.

Давайте подивимося, як це працює в реальному щоденному житті. Олег прийшов у поліклініку або **лікарню** *(clinic, hospital)*. Він має проблему зі здоров'ям і хоче поговорити з лікарем. Notice how Oleh starts the conversation with a formal title, and the doctor responds using Oleh's surname in the vocative case. This grammatical choice shows professional respect and social distance on both sides.

> — **Пацієнт (Олег):** Добрий день! Пане лікарю, мені потрібна допомога. *(Good day! Mr. doctor, I need help.)*
> — **Лікар:** Добрий день. Сідайте, будь ласка. Добре, пане Ковальчуку, що вас турбує? *(Good day. Sit down, please. Alright, Mr. Kovalchuk, what is bothering you?)*
> — **Пацієнт (Олег):** У мене дуже сильно болить голова. *(I have a very bad headache.)*
> — **Лікар:** Зрозуміло. Я дам вам ліки, пане Олегу. *(I understand. I will give you medicine, Mr. Oleh.)*
> — **Пацієнт (Олег):** Дякую, лікарю. Ви дуже добрі. *(Thank you, doctor. You are very kind.)*

У цьому короткому діалозі ми бачимо класичний приклад офіційної української поваги. Тепер ви знаєте, як правильно та ввічливо говорити з лікарем або зі своїм директором.

<!-- INJECT_ACTIVITY: match-professions-vocative -->


## Друже мій, люба моя: емоційний кличний (Emotional Vocative)

Коли ми говоримо з близькими друзями або родиною, ми також активно використовуємо кличний відмінок. Це робить нашу мову теплою та емоційною. Подивіться на дуже популярне слово **друг** *(friend)*. У кличному відмінку приголосний звук «г» завжди змінюється на «ж». Тому ми маємо казати «друже», а не «другу». Це дуже важливе правило української мови. Наприклад, ми часто кажемо: «Привіт, друже! Як твої справи?». Але жіноча форма **подруга** *(female friend)* має іншу структуру. Вона має твердий приголосний в кінці слова. Тому ми просто додаємо закінчення **-о**. Ми кажемо «подруго». Наприклад: «Моя люба подруго, я так рада тебе бачити!». Також ми використовуємо емоційні прикметники для звертання. Наприклад, **любий** *(dear - masculine)* та **люба** *(dear - feminine)*. When we use adjectives as forms of address, they always stay in the nominative case. Вони ніколи не змінюють свою форму. Ми завжди кажемо «люба» або «любий» без змін.

Українці часто кажуть, що їхня рідна мова **пісенна** *(song-like)* та дуже **ніжна** *(tender)*. Це тому, що ми дуже любимо використовувати **пестливі форми** *(diminutive forms)*. Ми використовуємо їх кожного дня, коли говоримо з дітьми або нашими коханими. For these affectionate addresses, the vocative case is especially rich and natural. Найпопулярніші теплі слова — це **серденько** *(sweetheart, little heart)* та **сонечко** *(sunshine, little sun)*. Neuter nouns ending in -ко usually keep their exact form in the vocative case, or they can take the -о ending, which looks exactly the same in writing. Тому ми кажемо: «Спи, моє сонечко» або «Ходи сюди, серденько». Для дівчат ми часто використовуємо красиве слово **зіронька** *(little star)*. У кличному відмінку це слово має форму «зіронько». Також популярне ім'я Люба має ніжну форму **Любочка** *(darling)*. Ми лагідно кличемо її «Любочко». Це звучить дуже приємно.

In Ukrainian, we have a very specific word order when we use possessive pronouns in the vocative case. Unlike in English, where you normally say "My friend", Ukrainian strongly prefers the grammatical pattern "Noun + Pronoun". Тому ми зазвичай кажемо «Друже мій!», а не «Мій друже!». Цей порядок слів звучить набагато природніше та емоційніше. Так само ми завжди говоримо «Мамо моя!», «Подруго моя!» або «Брате мій!». It is also very important to remember that possessive pronouns like **мій** *(my - masculine)* and **моя** *(my - feminine)* do not change their form. They always stay in the nominative case when used in a direct address. Ви змінюєте тільки сам іменник.

The vocative case is also perfectly preserved in many common emotional exclamations. Наприклад, коли ми дуже дивуємося, ми кажемо «**Боже мій!**» *(My God!)*. Це правильний кличний відмінок від слова «Бог». Інше дуже популярне слово — це «**Господи!**» *(Lord!)*. Ми використовуємо ці слова щодня як сильні емоційні вигуки. What happens when we address a group of people? In the plural, the vocative case is usually identical to the nominative plural. Тому ми просто кажемо «Друзі!» *(Friends!)* або «Колеги!» *(Colleagues!)*. But there is one major historical exception. Слово «пани» у кличному відмінку має спеціальну форму «**Панове!**» *(Gentlemen! / Sirs! / Ladies and Gentlemen!)*. Це дуже красиве та поважне українське звертання.

Давайте подивимося на нову ситуацію. Після візиту до лікаря Олег телефонує своєму другу. Він хоче розповісти йому хороші новини. Notice how the formal register from the clinic completely disappears, and Oleh uses warm, emotional vocative forms.
> — **Олег:** Алло! Привіт, друже мій! Як ти? *(Hello! Hi, my friend! How are you?)*
> — **Друг:** Привіт, Олеже! Я добре. Як твій візит до лікаря? *(Hi, Oleh! I am good. How was your visit to the doctor?)*
> — **Олег:** Усе чудово! Лікар каже, що я здоровий. Я дуже радий! *(Everything is great! The doctor says I am healthy. I am very happy!)*
> — **Друг:** Це супер! Твоя дружина вже знає? *(That is super! Does your wife already know?)*
> — **Олег:** Ще ні. Зараз буду дзвонити їй. Скажу: «Кохана моя, усе добре, не хвилюйся, моє сонечко!». *(Not yet. I will call her now. I will say: "My beloved, everything is fine, don't worry, my sunshine!".)*
> — **Друг:** Добре, друже. Тоді до зустрічі! *(Good, friend. Then see you later!)*

<!-- INJECT_ACTIVITY: error-correction-vocative -->


## Який кличний обрати? (Choosing the Right Vocative)

У повсякденному житті ми постійно змінюємо дистанцію спілкування. The vocative case is your main tool to show exactly how close or formal you want to be. Коли ви говорите з незнайомими людьми, ви використовуєте офіційний стиль. Наприклад, ви кажете «**пане Ковальчуку**» *(Mr. Kovalchuk)* або «**пані директорко**» *(Madam Director)*. Для фахівців ми обираємо професійний кличний відмінок, як-от «**лікарю**» *(doctor)* або «**офіціанте**» *(waiter)*. Якщо ви знаєте людину, але зберігаєте дистанцію, найкращий вибір — це нейтрально-ввічливий стиль. Ми кажемо «**пані Олено**» *(Ms. Olena)* або «**пане Андрію**» *(Mr. Andriy)*. З друзями ми використовуємо звичайні імена: «**Тарасе**» *(Taras)* чи «**Анно**» *(Anna)*. А для найрідніших маємо інтимний стиль: «**серденько**» *(sweetheart)*. If you choose the wrong register, you might sound cold to a friend or overly familiar to a boss.

Давайте розглянемо практичні життєві ситуації. Уявіть, що ви пишете електронний лист викладачу в університет. Ви повинні почати лист так: «**Шановний пане професоре!**» *(Dear Mr. Professor!)*. Це показує вашу повагу до його статусу. У ресторані ви кличете працівника просто: «**Пане офіціанте!**» *(Mr. Waiter!)*. А коли ви зустрічаєте сусіда, ви кажете: «**Пане Степане, добрий день!**» *(Mr. Stepan, good day!)*. First names in the vocative case without the titles "пан" or "пані" act as the perfect middle ground of politeness. Ми часто використовуємо їх на роботі з колегами. Ви кажете «**Маріє**» *(Maria)* або «**Олеже**» *(Oleh)*. Це звучить привітно, але не занадто інтимно.

Коли іноземці вивчають українську мову, вони часто роблять типові помилки. The most common pitfall is using the nominative case for direct address. Ніколи не кажіть «*Привіт, Іван!*». Правильна форма завжди вимагає кличного відмінка: «**Привіт, Іване!**» *(Hi, Ivan!)*. Another frequent error is mixing up gender agreement in possessive phrases. Не можна казати «*друже моя*», тому що «друг» — це чоловічий рід. Жінці ми завжди кажемо «**подруго моя**» *(my friend)*. Також існує класична проблема з популярним ім'ям Ігор. Many learners fall into the trap of using the archaic form "Ігоре". The modern standard rule treats this name as a soft-stem noun. Тому єдина правильна форма сьогодні — це «**Ігорю**» *(Ihor)*. Запам'ятайте її!

Кличний відмінок — це набагато більше, ніж просто граматичне правило. It is a profound mark of respect and a reflection of Ukrainian cultural identity. Коли ви використовуєте правильну форму, ви будуєте невидимий міст до людини. Ви показуєте, що ви відчуваєте контекст ситуації та поважаєте співрозмовника. Українська мова звучить дуже мелодійно саме завдяки цим м'яким закінченням. Слова «**мамо**» *(mom)*, «**брате**» *(brother)* або «**колего**» *(colleague)* роблять нашу комунікацію теплою та живою. The vocative case is the true music of the Ukrainian language. Використовуйте його щодня, і ви побачите приємну реакцію людей на ваші слова.

<!-- INJECT_ACTIVITY: quiz-register-choice -->
<!-- INJECT_ACTIVITY: group-sort-registers -->


## Підсумок

Давайте згадаємо головне правило цієї теми. Кличний відмінок має три основні закінчення. Ми використовуємо закінчення **-о** для твердої групи жіночого роду: **Оксано** *(Oksana)*, **мамо** *(mom)*. Закінчення **-е** працює для чоловічого роду твердої групи: **пане** *(sir)*, **друже** *(friend)*. А закінчення **-ю** ми додаємо до м'якої групи та пестливих форм: **лікарю** *(doctor)*, **бабусю** *(grandma)*.

Remember that formal addresses require the vocative for the title and the profession, but a surname stays in the nominative.

Перевірте себе! *(Check yourself!)*
1. Як звернутися до вчителя чоловіка? *(How to address a male teacher?)* — **Пане вчителю!** *(Mr. Teacher!)*
2. Як сказати «My friend» українською? *(How to say "My friend" in Ukrainian?)* — **Друже мій!** *(My friend!)*
3. Чи змінюється прізвище жінки після слова «пані»? *(Does a woman's surname change after the word "Ms."?)* — Ні, воно не змінюється. Ми кажемо: **пані Шевченко** *(Ms. Shevchenko)*.
4. Яка форма є стандартною для імені Олег? *(Which form is standard for the name Oleh?)* — **Олегу!** *(Oleh!)*

Тепер ви готові спілкуватися українською ввічливо та природно. *(Now you are ready to communicate in Ukrainian politely and naturally.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: vocative-expanded
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

**Level: A2 (Module 27/60) — ELEMENTARY**

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

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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
