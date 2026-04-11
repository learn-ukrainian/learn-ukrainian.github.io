<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/instrumental-profession.yaml` file for module **26: Я буду вчителькою** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-put-profession-nouns-into-instrumental-after -->`
- `<!-- INJECT_ACTIVITY: match-verb-complement -->`
- `<!-- INJECT_ACTIVITY: quiz-nom-vs-inst -->`
- `<!-- INJECT_ACTIVITY: fill-in-answer-questions-about-professions-using-full-instrumental-sentences -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put profession nouns into Instrumental after бути/стати/працювати
  items: 8
  type: fill-in
- focus: Match verbs (захоплюватися, цікавитися, пишатися) to correct Instrumental
    complements
  items: 8
  type: match-up
- focus: Choose Nominative or Instrumental for the profession noun based on tense
  items: 8
  type: quiz
- focus: Answer questions about professions using full Instrumental sentences
  items: 8
  type: fill-in


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- програміст (programmer)
- кухар (cook, chef)
- перукар (hairdresser)
- мріяти (to dream)
- володіти (to master, to possess)
required:
- професія (profession)
- фах (profession, specialty)
- працювати (to work)
- стати (to become)
- захоплюватися (to be passionate about)
- цікавитися (to be interested in)
- пишатися (to be proud of)
- займатися (to be engaged in, to do (a sport/activity))
- лікар (doctor)
- вчитель (teacher (male))
- вчителька (teacher (female))
- інженер (engineer)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Бути ким? Професія в орудному відмінку (To Be Whom? Profession in the Instrumental)

Як ми говоримо про **професію** *(profession)* українською мовою? Найпростіший спосіб — це використати називний відмінок. Ми ставимо тире між людиною і її професією. Наприклад, ми кажемо: «Мій тато — **інженер** *(engineer)*». Або ми можемо сказати: «Моя мама — **лікар** *(doctor)*». Це дуже зручна конструкція для теперішнього часу. In the present tense, when we simply state someone's static identity, we use the Nominative case. We do not use the verb «є» (is/are) in these sentences. The dash replaces the verb. Але що робити, коли ми говоримо про минулий чи майбутній час? As soon as we talk about the past, the future, or use specific action verbs, the rules change. The Nominative case is no longer enough. The Instrumental case becomes mandatory to show that someone holds a specific position. Ми використовуємо орудний відмінок, щоб показати тимчасову або набуту роль.

Давайте уважно подивимося на дієслово «**бути**» *(to be)*. У теперішньому часі ми зазвичай пропускаємо слово «є». Ми просто кажемо: «Я — вчитель». Але ми не можемо ігнорувати дієслово «бути» у минулому та майбутньому часі. When we use words like «**був**» *(was)*, «**була**» *(was)*, «**буду**» *(will be)*, or «**буде**» *(will be)*, we are describing a status held over a certain period of time. Because this is an acquired role, the noun that follows must take the Instrumental case. Наприклад, ми кажемо: «Він був лікарем». Ми також кажемо: «Вона буде **програмісткою** *(programmer, female)*». Або: «Ми були студентами». You cannot say «Він був лікар». This is a very common grammatical mistake. Always remember this important rule: past and future forms of the verb «бути» require the Instrumental case for professions.

Як правильно утворити орудний відмінок для жіночих професій? Сучасна українська мова дуже активно використовує фемінітиви. Це слова, які позначають професії жінок. Усі ці іменники належать до першої відміни. Feminine nouns ending in a hard consonant + -а take the ending **-ою**. Наприклад, слово «**вчителька**» *(teacher, female)* стає формою «вчителькою». Слово «**менеджерка**» *(manager, female)* стає формою «менеджеркою». Feminine nouns ending in a soft consonant + -я, or a mixed consonant + -а, take the ending **-ею**. Наприклад, слово «**будівельниця**» *(builder, female)* стає формою «будівельницею». Слово «**продавчиня**» *(seller/shop assistant, female)* стає формою «продавчинею». В українській мові це стандартна норма. Ми завжди кажемо: «Оксана була лікаркою». Ми не кажемо: «Оксана була лікар». Using feminine forms is the natural and grammatically correct way to speak about women's professions.

Тепер давайте поговоримо про чоловічі професії. Більшість із них — це іменники чоловічого роду другої відміни. Masculine nouns ending in a hard consonant take the ending **-ом**. Наприклад, слово «інженер» стає формою «інженером». Слово «програміст» стає формою «програмістом». Masculine nouns ending in a soft consonant or a mixed consonant take the ending **-ем** or **-єм**. Наприклад, слово «**вчитель**» *(teacher, male)* стає формою «вчителем». Слово «**водій**» *(driver)* стає формою «водієм». Pay special attention to nouns ending in the letter -р. Some belong to the hard group and take -ом, while others belong to the soft or mixed group and take -ем. It is best to check a good dictionary. Наприклад, слово «**директор**» *(director)* має тверду основу. Тому правильна форма — «директором». Але слово «лікар» належить до м'якої групи. Тому ми завжди кажемо «лікарем».

Найчастіше ми говоримо про професії, коли пояснюємо, ким ми працюємо зараз. Для цього ми використовуємо дієслово «**працювати**» *(to work)*. In English, you usually say "I work as a manager". Many language learners try to translate this literally into Ukrainian. They use the word «як» (as). Do not do this! The phrase "Я працюю як програміст" is incorrect and unnatural. В українській мові дієслово «працювати» з орудним відмінком автоматично означає "to work as". Вам не потрібні жодні додаткові слова. Ми просто кажемо: «Мій брат працює **архітектором** *(architect)*». Ми кажемо: «Вона працює журналісткою у великому місті». Це найприродніший спосіб розповісти про свою роботу. Просто запам'ятайте цю конструкцію: дієслово «працювати» плюс назва професії в орудному відмінку.

<!-- INJECT_ACTIVITY: fill-in-put-profession-nouns-into-instrumental-after -->

## Дієслова з орудним відмінком (Verbs That Take the Instrumental)

Окрім назв професій, орудний відмінок має ще одну дуже важливу функцію в українській мові. In Ukrainian, there is a special group of verbs that always require the Instrumental case. They do not need any prepositions like «з» *(with)* or «над» *(above)*. These verbs usually describe our internal states, deep passions, or specific ways we engage with the world. Think of the object as the metaphorical "instrument" that causes your interest, pride, or activity. Коли ми говоримо про наші хобі чи інтереси, ми часто використовуємо саме ці дієслова. Це робить нашу щоденну мову багатою, точною та природною. Let us look at the most common verbs in this grammatical category. Вони будуть дуже корисні для щоденного спілкування з новими друзями.

Два найпопулярніші дієслова для опису хобі — це «**захоплюватися**» *(to be passionate about)* та «**цікавитися**» *(to be interested in)*. Both verbs are reflexive, meaning they end in the particle -ся. They belong to different conjugation groups, so you must pay attention to their endings. Дієслово «захоплюватися» належить до першої дієвідміни. Ми кажемо: «Я **захоплююся** *(I am passionate about)* класичною музикою». «Він завжди захоплюється активним спортом». Дієслово «цікавитися» належить до другої дієвідміни. Pay close attention to the letter «л» that appears in the first person singular form. Ми кажемо: «Я **цікавлюся** *(I am interested in)* сучасною літературою». «Вона глибоко цікавиться історією України». Both verbs are followed directly by a noun in the Instrumental case. Чим ти цікавишся у вільний час? Мої нові друзі дуже захоплюються сучасним мистецтвом.

Інша важлива група дієслів описує нашу щиру гордість та глибоке захоплення красою. Дієслово «**пишатися**» *(to be proud of)* є надзвичайно важливим у сучасній українській культурі. Ми дуже часто говоримо про те, що викликає у нас велику повагу. Ми кажемо: «Ми завжди пишаємося нашою незалежною країною». «Я пишаюся своїм розумним сином». «Вона пишається своїми професійними успіхами». Дієслово «**милуватися**» *(to admire)* ми зазвичай використовуємо, коли дивимося на щось дуже гарне. Usually, this beautiful verb describes a visual appreciation of nature, architecture, or art. Ми кажемо: «Іноземні туристи милуються неймовірним краєвидом». «Я дуже люблю милуватися яскравим зоряним небом». «Ми довго милуємося старою міською архітектурою». Ці дієслова також завжди вимагають орудного відмінка без жодних прийменників.

Коли ми говоримо про нашу активну діяльність або глибокі практичні знання, ми використовуємо інші дієслова. Дієслово «**займатися**» *(to be engaged in, to do)* описує регулярну фізичну чи розумову активність. It is very important to distinguish the verb «займатися» from «працювати». We use «працювати» for our actual job title, but «займатися» for the broader field or activity. Ми кажемо: «Він працює головним менеджером, але успішно займається великим бізнесом». «Я займаюся спортивною йогою щоранку». Дієслово «**володіти**» *(to master, to possess)* ми найчастіше використовуємо для іноземних мов або спеціальних навичок. Ми кажемо: «Вона чудово володіє українською мовою». «Мій молодший брат добре володіє комп'ютером». Усі ці слова допомагають нам максимально точно описати наші реальні вміння.

<!-- INJECT_ACTIVITY: match-verb-complement -->

Тепер ми можемо успішно об'єднати інформацію про нашу професію та наші особисті інтереси. Це допомагає створювати граматично складні, але дуже природні речення. We can use multiple Instrumental nouns in one sentence if they are connected to different verbs. Наприклад, ми можемо сказати так: «За **фахом** *(profession, specialty)* я вчитель. Але зараз я працюю перекладачем і захоплююся художньою фотографією». Тут ми бачимо називний відмінок для базової ідентифікації. А потім ми використовуємо орудний відмінок для поточної роботи і хобі. Або ось інший чудовий приклад: «Моя старша сестра стала чудовою лікаркою. Вона цікавиться сучасною медициною і пишається своєю складною роботою». Такі розгорнуті конструкції звучать надзвичайно по-українськи. Ви можете тепер легко розповідати про себе, свої майбутні мрії та щоденні захоплення.

<!-- INJECT_ACTIVITY: quiz-nom-vs-inst -->

## Хто ти за фахом? (What Is Your Profession?)

Коли ми зустрічаємо нових людей, ми часто розмовляємо про роботу та кар'єру. How do we ask about someone's career in Ukrainian? У нас є кілька корисних запитань для різних життєвих ситуацій. Найбільш популярне запитання — це «**Ким ти працюєш?**» *(Who do you work as? / What is your job?)*. Це запитання завжди фокусується на вашій поточній роботі сьогодні. Якщо ми хочемо запитати про університетську освіту та спеціальність, ми говоримо інакше: «**Хто ти за фахом?**» *(What is your profession/specialty?)*. Слово «**фах**» *(profession, specialty)* — це чудовий український синонім до слів «**професія**» або «**спеціальність**». We use it when we talk about our formal training or our university degree. А якщо ми розмовляємо з дитиною або молодим студентом про майбутнє, ми запитуємо: «**Ким ти хочеш стати?**» *(Who do you want to become?)*. Усі ці запитання вимагають від нас логічної відповіді в орудному відмінку.

Давайте подивимося, як ці фрази працюють у реальній розмові. Олена та Андрій — колишні однокласники. Вони зустрілися на зустрічі випускників через п'ять років після школи.
> — **Олена:** Привіт, Андрію! Скільки літ, скільки зим! *(Hi, Andriy! Long time no see!)*
> — **Андрій:** Олено, привіт! Я так радий тебе бачити. Як твої справи? Хто ти тепер за фахом?
> — **Олена:** Усе чудово, дякую! Я стала **лікаркою** *(doctor - female)*, як і хотіла. Тепер працюю в центральній лікарні. А ти? Ким ти працюєш?
> — **Андрій:** Ого, я дуже пишаюся тобою! А я в школі мріяв бути **музикантом** *(musician)*, але життя змінилося. Я закінчив університет і став **програмістом** *(programmer)*.
> — **Олена:** Це також чудова сучасна професія! Ти працюєш у великій компанії?
> — **Андрій:** Так, і мені дуже подобається. Проте я все ще захоплююся гітарою у свій вільний час.

У світі існує дуже багато цікавих та важливих професій. Давайте вивчимо кілька нових назв для вашого активного словника. Сучасна українська мова активно і природно використовує жіночі форми професій.
Слово «**перукар**» або «**перукарка**» *(hairdresser)* описує людину, яка робить людям гарні зачіски. Моя улюблена перукарка працює у сучасному салоні краси біля мого дому.
Слово «**кухар**» або «**кухарка**» *(cook, chef)* означає людину, яка професійно і смачно готує їжу. Мій дядько — дуже талановитий кухар у відомому італійському ресторані.
Слово «**журналіст**» або «**журналістка**» *(journalist)* — це людина, яка пише цікаві статті або знімає телевізійні репортажі. Відома українська журналістка зараз бере важливе інтерв'ю у президента.
Слово «**музикант**» або «**музикантка**» *(musician)* стосується людей класичного або сучасного мистецтва. Талановитий музикант грає на скрипці в національному театрі.
І нарешті, «**юрист**» або «**юристка**» *(lawyer)* — це серйозний спеціаліст із державних законів. Моя розумна старша сестра працює успішною юристкою в центрі Києва.

В українській мові є дуже популярні сталі вирази, які ми використовуємо для розмов про кар'єру. Коли ваша щоденна робота відповідає вашому університетському диплому, ми кажемо: «**працювати за фахом**» *(to work in one's field)*. Це означає, що ви ефективно використовуєте свою освіту. Наприклад: «Олена закінчила медичний університет і тепер працює за фахом». Але досить часто буває так, що дорослі люди повністю змінюють свій життєвий шлях. Тоді ми використовуємо фразу «**працювати не за фахом**» *(to work outside one's field)*. Наприклад: «Він економіст за фахом, але працює не за фахом, бо він став успішним фотографом».
When we talk about our career goals and deep ambitions, we use the verb «**мріяти**» *(to dream)*. You can say «мріяти про нову професію» using the preposition «про» and the Accusative case. However, it is much more natural to say what you want to *be*. In this exact situation, we use the construction «**мріяти стати**» *(to dream of becoming)* followed by the Instrumental case. Ми часто кажемо: «Молодий студент серйозно мріє стати відомим юристом». Або ми можемо сказати так: «Ця маленька дівчинка дуже мріє стати талановитою художницею».

<!-- INJECT_ACTIVITY: fill-in-answer-questions-about-professions-using-full-instrumental-sentences -->

## Практика: Ким бути? (Practice: Who to Be?)

Зараз ми будемо практикувати нові граматичні структури. Let's do a deep dive into transformation drills. We need to practice the mental shift from stating a simple identity to describing an action or a future goal. Візьмемо для прикладу слово «**художник**» *(artist)*.

Перший рівень — це проста ідентифікація в теперішньому часі. Ми використовуємо називний відмінок. 
«Він — художник» *(He is an artist)*.

Другий рівень — це опис професійної дії. Тут ми маємо дієслово «**працювати**» *(to work)*. Воно вимагає орудного відмінка.
«Він працює художником» *(He works as an artist)*.

Третій рівень — це опис амбіцій або планів на майбутнє. Тут ми використовуємо дієслова «**хотіти**» *(to want)* та «**стати**» *(to become)*. Дієслово «стати» завжди вимагає орудного відмінка.
«Він хоче стати відомим художником» *(He wants to become a famous artist)*.

Ці три рівні показують, як змінюється форма слова. The grammatical trigger is always the verb. If there is no verb (or a hidden present tense "to be"), use Nominative. If you use verbs of becoming or working, use Instrumental.

Тепер давайте поговоримо про нашу родину та друзів. This kind of practice is very important. Narrating the lives of others helps you apply the Instrumental case to third-person descriptions. Ці описи дуже часто зустрічаються на іспитах рівня А2.

Ось кілька гарних прикладів:
«Моя молодша сестра цікавиться медициною, тому вона хоче стати **лікаркою**» *(My younger sister is interested in medicine, so she wants to become a doctor)*.
«Мій старший брат займається спортом, він мріє бути **тренером**» *(My older brother does sports, he dreams of being a coach)*.
«Мій тато захоплюється кулінарією, він працює **кухарем**» *(My dad is passionate about cooking, he works as a chef)*.
«Моя мама любить математику, вона працює **бухгалтером**» *(My mom loves math, she works as an accountant)*.

У цих реченнях ми спочатку називаємо хобі або інтерес людини. Після цього ми пояснюємо її професію або мету. We use the verbs of interest in the first clause. Then we use the verbs of profession in the second clause.

Діти дуже часто говорять про свої мрії. Їхні бажання можуть швидко змінюватися. Давайте прочитаємо коротку розмову між мамою та її маленьким сином. Цей веселий діалог показує зв'язок між дитячим захопленням та майбутньою професією.

> — **Дитина:** Мамо, коли я виросту, я буду **ветеринаром**! *(Mom, when I grow up, I will be a veterinarian!)*
> — **Мама:** Це чудова ідея, синку! Але чому саме ветеринаром? *(That's a great idea, son! But why exactly a veterinarian?)*
> — **Дитина:** Бо я дуже захоплююся тваринами. Я хочу їм допомагати. *(Because I am very passionate about animals. I want to help them.)*
> — **Мама:** А ким хоче стати твій друг Сашко? *(And what does your friend Sashko want to become?)*
> — **Дитина:** Сашко постійно малює. Він мріє стати **архітектором**. *(Sashko draws constantly. He dreams of becoming an architect.)*
> — **Мама:** Які у вас серйозні плани на майбутнє! *(What serious plans for the future you have!)*

Notice how the child naturally uses the Instrumental case. The causal link between the passion and the goal makes the conversation sound authentic and logical.

## Підсумок

Ми чудово попрацювали сьогодні! *(We worked wonderfully today!)* Тепер ви знаєте, як розповідати про професії та інтереси. *(Now you know how to talk about professions and interests.)* Let's quickly review the core rules. Для простої ідентифікації в теперішньому часі ми використовуємо тире та називний відмінок. *(For simple identification in the present tense, we use a dash and the Nominative case.)* «Він — лікар» *(He is a doctor)*. Але якщо ми говоримо про минулий час, майбутній час або зміну статусу, нам потрібен орудний відмінок. *(But if we talk about the past tense, future tense, or a change of status, we need the Instrumental case.)* Дієслова «**бути**» *(to be)* у минулому та майбутньому, а також «**стати**» *(to become)* і «**працювати**» *(to work)* завжди вимагають орудного відмінка. *(The verbs "to be" in the past and future, as well as "to become" and "to work", always require the Instrumental case.)*

Remember the key endings for professions. Чоловічі професії зазвичай мають закінчення «-ом» або «-ем». *(Masculine professions usually have the ending "-om" or "-em".)* Наприклад: «інженером» *(as an engineer)*, «вчителем» *(as a teacher)*. Жіночі професії отримують закінчення «-ою» або «-ею». *(Feminine professions get the ending "-oiu" or "-eiu".)* Наприклад: «лікаркою» *(as a doctor)*, «будівельницею» *(as a builder)*.

We also learned four important verbs that express passion and activity. Ці дієслова завжди працюють з орудним відмінком. *(These verbs always work with the Instrumental case.)* Ось ця велика четвірка: «**захоплюватися**» *(to be passionate about)*, «**цікавитися**» *(to be interested in)*, «**пишатися**» *(to be proud of)* та «**займатися**» *(to be engaged in)*. Використовуйте їх, щоб робити ваші розповіді цікавими. *(Use them to make your stories interesting.)* До нових зустрічей! *(Until next time!)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: instrumental-profession
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

**Level: A2 (Module 26/60) — ELEMENTARY**

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
