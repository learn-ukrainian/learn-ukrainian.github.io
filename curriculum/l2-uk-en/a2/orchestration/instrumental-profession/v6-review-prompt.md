<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 26: Я буду вчителькою (A2, A2.4 [Instrumental Case])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-026
level: A2
sequence: 26
slug: instrumental-profession
version: '1.0'
title: Я буду вчителькою
subtitle: Орудний відмінок для професії та стану; дієслова з орудним відмінком
focus: grammar
pedagogy: PPP
phase: A2.4 [Instrumental Case]
word_target: 2000
objectives:
  - Learner can use the Instrumental case to express profession or status after 
    бути, стати, працювати (бути лікарем, стати вчителькою, працювати 
    інженером).
  - Learner can conjugate and use verbs that require the Instrumental case 
    (захоплюватися, цікавитися, пишатися, займатися).
  - Learner can distinguish Nominative predicate (Я вчитель) from Instrumental 
    predicate (Я буду вчителем) and understand when each is appropriate.
  - Learner can ask and answer questions about professions using Ким? and Хто ти
    за фахом?
dialogue_situations:
  - setting: 'High school reunion — catching up on careers: Я стала лікаркою (f).
      Він працює інженером (m). Вона хоче бути журналісткою (f). А ти?'
    speakers:
      - Колишні однокласники (former classmates)
    motivation: 'Бути + instrumental: лікарка→лікаркою, інженер→інженером'
content_outline:
  - section: 'Бути ким? Професія в орудному відмінку (To Be Whom? Profession in the
      Instrumental)'
    words: 550
    points:
      - 'After бути (past/future), стати, працювати, the profession noun goes into
        Instrumental: Вона була вчителькою. Він стане лікарем. Я працюю інженером.'
      - 'Present tense exception: Я вчитель / Вона вчителька (Nominative, no є). But
        past and future use Instrumental: Він був лікарем. Вона буде програмісткою.'
      - 'Feminine profession nouns in Instrumental: вчителька → вчителькою, лікарка
        → лікаркою, програмістка → програмісткою, журналістка → журналісткою.'
      - 'Masculine profession nouns in Instrumental: лікар → лікарем, кухар → кухарем,
        інженер → інженером, програміст → програмістом, музикант → музикантом.'
      - 'Ukrainian forms both masculine and feminine profession nouns naturally —
        this is standard, not innovation: лікар/лікарка, вчитель/вчителька, кухар/кухарка.'
  - section: 'Дієслова з орудним відмінком (Verbs That Take the Instrumental)'
    words: 550
    points:
      - 'Verbs of interest and passion: захоплюватися (to be passionate about) — захоплюватися
        музикою, спортом, мистецтвом; цікавитися (to be interested in) — цікавитися
        історією, наукою.'
      - 'Verbs of pride and admiration: пишатися (to be proud of) — Я пишаюся Україною,
        сином; милуватися (to admire) — милуватися природою.'
      - 'Verbs of activity: займатися (to be engaged in) — займатися спортом, йогою,
        бізнесом; володіти (to master/possess) — володіти мовою.'
      - 'Conjugation focus: захоплюватися (1st conjugation: захоплююся, захоплюєшся...),
        цікавитися (2nd conjugation: цікавлюся, цікавишся...).'
      - Practice sentences combining profession and interest vocabulary.
  - section: 'Хто ти за фахом? (What Is Your Profession?)'
    words: 500
    points:
      - 'Key question patterns: Ким ти працюєш? Ким ти хочеш стати? Хто ти за фахом?
        Чим ти захоплюєшся?'
      - 'Dialogue: Two people at a party introducing themselves — discussing their
        jobs, what they studied, and what they are passionate about.'
      - 'Common professions for practice: вчитель/вчителька, лікар/лікарка, інженер/
        інженерка, програміст/програмістка, кухар/кухарка, перукар/перукарка, журналіст/журналістка,
        музикант/музикантка.'
      - 'Useful phrases: працювати за фахом (to work in one''s field), мріяти стати...
        (to dream of becoming...).'
  - section: 'Практика: Ким бути? (Practice: Who to Be?)'
    words: 400
    points:
      - 'Transformation drill: Він лікар. → Він працює лікарем. → Він буде лікарем.'
      - 'Sentence building with verb + Instrumental: Мій брат займається програмуванням.
        Моя сестра цікавиться медициною. Я пишаюся своєю родиною.'
      - 'Mini-dialogue: A child telling a parent about future career dreams (Я хочу
        стати ветеринаром! — Чому? — Бо я захоплююся тваринами).'
vocabulary_hints:
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
  recommended:
    - програміст (programmer)
    - кухар (cook, chef)
    - перукар (hairdresser)
    - мріяти (to dream)
    - володіти (to master, to possess)
activity_hints:
  - type: fill-in
    focus: Put profession nouns into Instrumental after бути/стати/працювати
    items: 8
  - type: match-up
    focus: Match verbs (захоплюватися, цікавитися, пишатися) to correct 
      Instrumental complements
    items: 8
  - type: quiz
    focus: Choose Nominative or Instrumental for the profession noun based on 
      tense
    items: 8
  - type: fill-in
    focus: Answer questions about professions using full Instrumental sentences
    items: 8
references:
  - title: Кравцова Grade 4, с. 58
    notes: 'Exercise 159 — "Ким ти мрієш стати?" with profession nouns in Instrumental:
      перукар, кухар, пекар, шахтар, архітектор, маляр, шофер'
  - title: Заболотний Grade 10, с. 153
    notes: Instrumental singular formation for profession nouns (ювіляр, гончар,
      столяр, кулінар, кобзар, редактор)
  - title: 'ULP: Professions in Ukrainian'
    url: https://www.ukrainianlessons.com/season2-lesson18/
    notes: Profession vocabulary and Instrumental usage patterns

</plan_content>

## Generated Content

<generated_module_content>
## Бути ким? Професія в орудному відмінку (~600 words total)

Як ми говоримо про **професію** *(profession)* українською мовою? Найпростіший спосіб — це використати називний відмінок. Ми ставимо тире між людиною і її професією. Наприклад, ми кажемо: «Мій тато — **інженер** *(engineer)*». Або ми можемо сказати: «Моя мама — **лікар** *(doctor)*». Це дуже зручна конструкція для теперішнього часу. In the present tense, when we simply state someone's static identity, we use the Nominative case. We do not use the verb «є» (is/are) in these sentences. The dash replaces the verb. Але що робити, коли ми говоримо про минулий чи майбутній час? As soon as we talk about the past, the future, or use specific action verbs, the rules change. The Nominative case is no longer enough. The Instrumental case becomes mandatory to show that someone holds a specific position. Ми використовуємо орудний відмінок, щоб показати тимчасову або набуту роль.

Давайте уважно подивимося на дієслово «**бути**» *(to be)*. У теперішньому часі ми зазвичай пропускаємо слово «є». Ми просто кажемо: «Я — вчитель». Але ми не можемо ігнорувати дієслово «бути» у минулому та майбутньому часі. When we use words like «**був**» *(was)*, «**була**» *(was)*, «**буду**» *(will be)*, or «**буде**» *(will be)*, we are describing a status held over a certain period of time. Because this is an acquired role, the noun that follows must take the Instrumental case. Наприклад, ми кажемо: «Він був лікарем». Ми також кажемо: «Вона буде **програмісткою** *(programmer, female)*». Або: «Ми були студентами». You cannot say «Він був лікар». This is a very common grammatical mistake. Always remember this important rule: past and future forms of the verb «бути» require the Instrumental case for professions.

Як правильно утворити орудний відмінок для жіночих професій? Сучасна українська мова дуже активно використовує фемінітиви. Це слова, які позначають професії жінок. Усі ці іменники належать до першої відміни. Feminine nouns ending in a hard consonant + -а take the ending **-ою**. Наприклад, слово «**вчителька**» *(teacher, female)* стає формою «вчителькою». Слово «**менеджерка**» *(manager, female)* стає формою «менеджеркою». Feminine nouns ending in a soft or mixed consonant + -я (or -а after soft sounds) take the ending **-ею**. Наприклад, слово «**будівельниця**» *(builder, female)* стає формою «будівельницею». Слово «**продавчиня**» *(seller/shop assistant, female)* стає формою «продавчинею». В українській мові це стандартна норма. Ми завжди кажемо: «Оксана була лікаркою». Ми не кажемо: «Оксана була лікар». Using feminine forms is the natural and grammatically correct way to speak about women's professions.

Тепер давайте поговоримо про чоловічі професії. Більшість із них — це іменники чоловічого роду другої відміни. Masculine nouns ending in a hard consonant take the ending **-ом**. Наприклад, слово «інженер» стає формою «інженером». Слово «програміст» стає формою «програмістом». Masculine nouns ending in a soft consonant or a mixed consonant take the ending **-ем** or **-єм**. Наприклад, слово «**вчитель**» *(teacher, male)* стає формою «вчителем». Слово «**водій**» *(driver)* стає формою «водієм». Pay special attention to nouns ending in the letter -р. Some belong to the hard group and take -ом, while others belong to the soft or mixed group and take -ем. It is best to check a good dictionary. Наприклад, слово «**директор**» *(director)* має тверду основу. Тому правильна форма — «директором». Але слово «лікар» належить до м'якої групи. Тому ми завжди кажемо «лікарем».

Найчастіше ми говоримо про професії, коли пояснюємо, ким ми працюємо зараз. Для цього ми використовуємо дієслово «**працювати**» *(to work)*. In English, you usually say "I work as a manager". Many language learners try to translate this literally into Ukrainian. They use the word «як» (as). Do not do this! The phrase "Я працюю як програміст" is incorrect and unnatural. В українській мові дієслово «працювати» з орудним відмінком автоматично означає "to work as". Вам не потрібні жодні додаткові слова. Ми просто кажемо: «Мій брат працює **архітектором** *(architect)*». Ми кажемо: «Вона працює журналісткою у великому місті». Це найприродніший спосіб розповісти про свою роботу. Просто запам'ятайте цю конструкцію: дієслово «працювати» плюс назва професії в орудному відмінку.

<!-- INJECT_ACTIVITY: fill-in-put-profession-nouns-into-instrumental-after -->

## Дієслова з орудним відмінком

Окрім назв професій, орудний відмінок має ще одну дуже важливу функцію в українській мові. In Ukrainian, there is a special group of verbs that always require the Instrumental case. They do not need any prepositions like «з» *(with)* or «над» *(above)*. These verbs usually describe our internal states, deep passions, or specific ways we engage with the world. Think of the object as the metaphorical "instrument" that causes your interest, pride, or activity. Коли ми говоримо про наші хобі чи інтереси, ми часто використовуємо саме ці дієслова. Це робить нашу щоденну мову багатою, точною та природною. Let us look at the most common verbs in this grammatical category. Вони будуть дуже корисні для щоденного спілкування з новими друзями.

Два найпопулярніші дієслова для опису хобі — це «**захоплюватися**» *(to be passionate about)* та «**цікавитися**» *(to be interested in)*. Both verbs are reflexive, meaning they end in the particle -ся. They belong to different conjugation groups, so you must pay attention to their endings. Дієслово «захоплюватися» належить до першої дієвідміни. Ми кажемо: «Я **захоплююся** *(I am passionate about)* класичною музикою». «Він завжди захоплюється активним спортом». Дієслово «цікавитися» належить до другої дієвідміни. Pay close attention to the letter «л» that appears in the first person singular form. Ми кажемо: «Я **цікавлюся** *(I am interested in)* сучасною літературою». «Вона глибоко цікавиться історією України». Both verbs are followed directly by a noun in the Instrumental case. Чим ти цікавишся у вільний час? Мої нові друзі дуже захоплюються сучасним мистецтвом.

Інша важлива група дієслів описує нашу щиру гордість та глибоке захоплення красою. Дієслово «**пишатися**» *(to be proud of)* є надзвичайно важливим у сучасній українській культурі. Ми дуже часто говоримо про те, що викликає у нас велику повагу. Ми кажемо: «Ми завжди пишаємося нашою незалежною країною». «Я пишаюся своїм розумним сином». «Вона пишається своїми професійними успіхами». Дієслово «**милуватися**» *(to admire)* ми зазвичай використовуємо, коли дивимося на щось дуже гарне. Usually, this beautiful verb describes a visual appreciation of nature, architecture, or art. Ми кажемо: «Іноземні туристи милуються неймовірним краєвидом». «Я дуже люблю милуватися яскравим зоряним небом». «Ми довго милуємося старою міською архітектурою». Ці дієслова також завжди вимагають орудного відмінка без жодних прийменників.

Коли ми говоримо про нашу активну діяльність або глибокі практичні знання, ми використовуємо інші дієслова. Дієслово «**займатися**» *(to be engaged in, to do)* описує регулярну фізичну чи розумову активність. It is very important to distinguish the verb «займатися» from «працювати». We use «працювати» for our actual job title, but «займатися» for the broader field or activity. Ми кажемо: «Він працює головним менеджером, але успішно займається великим бізнесом». «Я займаюся спортивною йогою щоранку». Дієслово «**володіти**» *(to master, to possess)* ми найчастіше використовуємо для іноземних мов або спеціальних навичок. Ми кажемо: «Вона чудово володіє українською мовою». «Мій молодший брат добре володіє комп'ютером». Усі ці слова допомагають нам максимально точно описати наші реальні вміння.

<!-- INJECT_ACTIVITY: match-verb-complement -->

Тепер ми можемо успішно об'єднати інформацію про нашу професію та наші особисті інтереси. Це допомагає створювати граматично складні, але дуже природні речення. We can use multiple Instrumental nouns in one sentence if they are connected to different verbs. Наприклад, ми можемо сказати так: «За **фахом** *(profession, specialty)* я вчитель. Але зараз я працюю перекладачем і захоплююся художньою фотографією». Тут ми бачимо називний відмінок для базової ідентифікації. А потім ми використовуємо орудний відмінок для поточної роботи і хобі. Або ось інший чудовий приклад: «Моя старша сестра стала чудовою лікаркою. Вона цікавиться сучасною медициною і пишається своєю складною роботою». Такі розгорнуті конструкції звучать надзвичайно по-українськи. Ви можете тепер легко розповідати про себе, свої майбутні мрії та щоденні захоплення.

<!-- INJECT_ACTIVITY: quiz-nom-vs-inst -->

## Хто ти за фахом?

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

## Практика: Ким бути?

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
</generated_module_content>

**PIPELINE NOTE — Word count: 2636 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 2000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 694 words | Not found: 8 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрій — NOT IN VESUM
  ✗ Андрію — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Сашко — NOT IN VESUM
  ✗ українськи — NOT IN VESUM

All 694 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
