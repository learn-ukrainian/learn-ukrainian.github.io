<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/advanced-pronouns.yaml` file for module **63: Займенники (деталі)** (b1).

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

- `<!-- INJECT_ACTIVITY: reading-interrogative-relative -->`
- `<!-- INJECT_ACTIVITY: fill-in-interrogative-relative -->`
- `<!-- INJECT_ACTIVITY: quiz-interrogative-relative -->`
- `<!-- INJECT_ACTIVITY: essay-reflexive-self -->`
- `<!-- INJECT_ACTIVITY: error-correction-reflexive-self -->`
- `<!-- INJECT_ACTIVITY: match-up-reflexive-self -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Прочитайте текст про питально-відносні займенники і дайте відповіді на запитання.
  type: reading
- focus: Напишіть 5 речень, використовуючи нову лексику з розділу «Зворотний займенник
    себе».
  type: essay-response
- focus: Вставте правильну граматичну форму у реченнях на тему питально-відносні займенники.
  type: fill-in
- focus: Знайдіть і виправте помилки у реченнях на тему зворотний займенник себе.
  type: error-correction
- focus: 'Оберіть правильний варіант: лексика та граматика з розділу «Питально-відносні
    займенники».'
  type: quiz
- focus: З'єднайте терміни з розділу «Зворотний займенник себе» з їхніми визначеннями.
  type: match-up


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- хто-небудь (anyone — in questions/hypotheticals)
- дехто (some people — де- prefix)
- абиякий (any old — casual/dismissive indefinite)
- котрий (which — literary synonym of який)
- собою (with oneself — Ор.в. of себе)
- свій (one's own — reflexive possessive)
required:
- займенник (pronoun)
- питально-відносний (interrogative-relative)
- зворотний (reflexive — себе)
- неозначений (indefinite — хтось, будь-хто)
- заперечний (negative — ніхто, ніщо)
- себе (oneself — reflexive pronoun, no Н.в.)
- хтось (someone — known to speaker)
- будь-хто (anyone — no specificity)
- ніхто (nobody)
- ніщо (nothing)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Питально-відносні займенники

Питально-відносні займенники — це особлива група слів, яка виконує дві різні граматичні функції. З одного боку, вони допомагають нам ставити запитання. Ми використовуємо слова «хто», «що», «який», «чий» та «котрий», коли хочемо дізнатися нову інформацію про особу, предмет, ознаку чи належність. Наприклад: «Хто це прийшов?», «Що ти сьогодні бачив?», «Який фільм ми будемо дивитися?». У таких випадках ці слова є питальними займенниками. З іншого боку, ті самі слова можуть виконувати роль відносних займенників. Тоді вони вже не ставлять запитань, а об'єднують частини складного речення. Вони стоять на межі головного та підрядного речень, пов'язуючи їх між собою. Наприклад: «Це та людина, яка знає всі відповіді», або «Я пам'ятаю те, що я бачив учора». У цих реченнях відносний займенник вказує на слово з головного речення і водночас є повноцінним членом підрядного речення. Ця подвійна природа робить їх універсальними інструментами в українській мові.

> *Interrogative-relative pronouns are a special group of words that perform two different grammatical functions. On one hand, they help us ask questions. We use words like "хто", "що", "який", "чий", and "котрий" when we want to find out new information about a person, object, characteristic, or possession. For example: "Who came here?", "What did you see today?", "What movie are we going to watch?". In such cases, these words are interrogative pronouns. On the other hand, the exact same words can act as relative pronouns. Then they no longer ask questions, but connect parts of a complex sentence. They stand at the boundary of the main and subordinate clauses, linking them together. For example: "This is the person who knows all the answers", or "I remember what I saw yesterday". In these sentences, the relative pronoun refers back to a word from the main clause and simultaneously serves as a full member of the subordinate clause. This dual nature makes them versatile tools in the Ukrainian language.*

Займенники «хто» та «що» є базовими для цієї групи. Вони не мають ознак роду чи числа, але змінюються за відмінками. Займенник «хто» вказує на людей та тварин, тобто на істот. Його відмінювання треба запам'ятати: у називному відмінку — хто, у родовому та знахідному — кого, у давальному — кому, в орудному — ким, а в місцевому — на кому. Наприклад: «Кого ти сьогодні зустрів?», або «Це студент, кому я дав книгу». Займенник «що» вказує на неживі предмети, явища та абстрактні поняття. Його парадигма виглядає так: називний та знахідний — що, родовий — чого, давальний — чому, орудний — чим, місцевий — на чому. Наприклад: «Чим ти зараз цікавишся?», або «Це тема, у чому я добре розбираюся». Важливо пам'ятати ці форми, оскільки вони стануть основою для утворення багатьох інших, більш складних займенників. Відмінювання цих двох коротких слів зустрічається в мовленні постійно, тому їхня автоматизація є критичною для вільного спілкування.

:::info
**Займенники «хто» і «що»** — це фундамент української системи займенників. Зверніть увагу, що прийменники завжди стоять перед займенником і ніколи не розривають його основу: *з ким*, *до чого*, *на кому*.
:::

Займенники «який», «чий» та «котрий» вказують на ознаку або належність і змінюються за родами, числами та відмінками. Їхня поведінка дуже нагадує прикметники. Займенник «який» відмінюється як звичайний прикметник твердої групи. У чоловічому роді він має форми: якого, якому, яким, на якому. Займенник «котрий» також дотримується парадигми твердої групи прикметників і змінюється аналогічно: котрого, котрому, котрим. А от займенник «чий» має дещо специфічне відмінювання, яке нагадує м'яку групу, але з певними особливостями. Його форми у чоловічому роді: чийого, чийому (або чиєму), чиїм, на чийому. У жіночому роді він має форми: чия, чиєї, чиїй, чию, чиєю, на чиїй. У множині: чиї, чиїх, чиїм, чиїми, на чиїх. Ці займенники узгоджуються з іменником, до якого вони належать. Якщо ви запитуєте про книгу, ви скажете: «Чию книгу ти взяв?» або «Яку книгу ти читаєш?». Відмінкові закінчення цих займенників допомагають точно передати граматичний зв'язок у реченні.

Хоча займенники «який» та «котрий» іноді здаються схожими, вони мають чіткі смислові відмінності. Займенник «який» використовується для того, щоб запитати про характеристику, якість або властивість предмета чи особи. Наприклад: «Який це фільм?», «Яка сьогодні погода?», «Які плани на вечір?». Натомість займенник «котрий» вказує на порядок предметів при лічбі або на вибір одного варіанта з кількох можливих. Найчастіше ми використовуємо його, коли запитуємо про час: «Котра зараз година?». Також ми питаємо «Котрий вагон наш?», коли шукаємо своє місце у поїзді. В українській мові поширеною помилкою є вживання «який» замість «котрий» у питаннях про час або номер. У ролі відносних займенників «який» і «котрий» можуть бути абсолютними синонімами. Наприклад, можна сказати «Книжка, яку я читаю» або «Книжка, котру я читаю». Однак варіант із «котру» звучить більш книжно та літературно, тоді як «яку» є нейтральним і повсякденним.

:::note
**«Який» чи «котрий»?** — Якщо ви питаєте про якість (добрий, цікавий, нудний) — використовуйте *який*. Якщо ви питаєте про порядок (перший, п'ятий) або точний час — використовуйте *котрий*.
:::

Коли питально-відносні займенники виконують роль відносних, вони стають сполучними словами у складнопідрядних реченнях. Їхня граматична форма залежить від двох різних факторів. По-перше, такі займенники як «який», «чий» та «котрий» завжди узгоджуються у роді та числі з тим словом у головному реченні, на яке вони вказують. По-друге, їхній відмінок повністю визначається їхньою синтаксичною роллю всередині підрядного речення. Розглянемо приклад: «Я знаю жінку, чия дитина тут грається». У головному реченні слово «жінку» стоїть у знахідному відмінку і має жіночий рід. Відносний займенник «чия» бере від цього слова жіночий рід та однину. Проте у своєму підрядному реченні займенник «чия» узгоджується з підметом «дитина», тому стоїть у називному відмінку. Інший приклад: «Це проєкт, яким ми пишаємося». Слово «проєкт» чоловічого роду, тому маємо чоловічий рід. Але в підрядному реченні дієслово «пишатися» вимагає орудного відмінка, тому ми використовуємо форму «яким». Це правило гарантує правильну побудову складних речень.

<!-- INJECT_ACTIVITY: reading-interrogative-relative -->
<!-- INJECT_ACTIVITY: fill-in-interrogative-relative -->
<!-- INJECT_ACTIVITY: quiz-interrogative-relative -->

## Зворотний займенник себе

Зворотний займенник «себе» вказує на те, що дія повністю спрямована на самого виконавця. Цей займенник є граматично унікальним, адже він принципово не має форми називного відмінка. Також він ніколи не змінюється за родами чи числами. Логіка цієї відсутності дуже проста: підмет, тобто активний виконавець дії, ніколи не може бути об'єктом у називному відмінку. Займенник «себе» завжди вказує на підмет речення, незалежно від того, яка це граматична особа: перша, друга чи третя. Наприклад, ми кажемо: «Я бачу себе у великому дзеркалі», «Ти прекрасно бачиш себе», «Вони завжди бачать себе лідерами». У всіх цих різноманітних випадках форма зворотного займенника залишається незмінною, хоча підмети постійно змінюються. Це робить його дуже зручним та універсальним інструментом для вираження рефлексивних дій у щоденному мовленні.

Хоча цей особливий займенник не має називного відмінка, він повноцінно змінюється за всіма іншими відмінками української мови. Його повна граматична парадигма виглядає так: родовий — себе, давальний — собі, знахідний — себе, орудний — собою, місцевий — на собі. Кожна з цих форм має свої специфічні та дуже типові контексти щоденного вживання. Форма давального відмінка «собі» часто використовується тоді, коли дія виконується для власної користі, задоволення або особистого інтересу. Наприклад, ми часто кажемо «купити собі нову цікаву книгу», «заварити собі гарячого чаю» або «уявити собі дуже складну ситуацію». Натомість форма орудного відмінка «собою» найчастіше передає глибокий внутрішній стан людини або її емоційне задоволення від результату. Коли людина досягає великого успіху після тривалої праці, вона з гордістю може сказати, що цілком «задоволена собою».

В українській мові існує надзвичайно багато сталих висловів, фразеологізмів та ідіом із цим зворотним займенником. Дуже важливо добре запам'ятати дієслово «почуватися» або конструкцію «почувати себе», яка описує загальний стан здоров'я: «Як ти себе почуваєш сьогодні після вчорашнього тренування?». Поширений вираз «сам по собі» означає щось незалежне, те, що існує окремо від іншого впливу: «Цей архітектурний проєкт цікавий сам по собі». Якщо щось є дуже посереднім, не вражає або має не дуже високу якість, ми використовуємо розмовну фразу «так собі»: «Новий фільм у кінотеатрі був так собі, нічого особливого». Коли людина говорить чи дарує щось від власного імені, вона каже «від себе». А якщо комусь раптом стає страшно чи ніяково, ми використовуємо влучний вираз «не по собі»: «Мені одразу стало не по собі від його холодних слів».

:::tip
**«Сам по собі» чи «само собою»?** — Вираз *сам по собі* підкреслює унікальність та незалежність предмета або особи. Натомість фраза *само собою* (часто звучить як *само собою зрозуміло*) означає щось цілком очевидне, те, що не потребує жодних додаткових пояснень чи логічних доказів.
:::

Критично важливо чітко розрізняти зворотний займенник «себе» та присвійний займенник «свій», адже вони виконують різні функції. Займенник «себе» виступає в ролі прямого чи непрямого об'єкта дії. Він фізично або емоційно приймає цю дію на себе. Натомість займенник «свій» вказує лише на зворотну належність. Він показує, що певний предмет належить безпосередньо виконавцю дії. Порівняйте ці два короткі речення, щоб зрозуміти ключову різницю. У реченні «Він дуже любить себе» займенник виступає об'єктом: хлопець спрямовує свою любов на власну персону. А в реченні «Він дуже любить свою роботу» займенник «свою» лише вказує на те, чия це саме робота. Обидва ці слова відсилають нас назад до підмета речення, але вони займають різні синтаксичні позиції. Слово «себе» завжди відмінюється як іменник. Натомість слово «свій» відмінюється як звичайний прикметник і завжди граматично узгоджується з наступним словом.

> *It is critically important to clearly distinguish between the reflexive pronoun "себе" and the possessive pronoun "свій", as they perform absolutely different functions. The pronoun "себе" acts as a direct or indirect object of the action. It physically or emotionally receives this action. In contrast, the pronoun "свій" only indicates reflexive ownership. It shows that a certain object belongs directly to the doer of the action. Compare these two short sentences to understand the key difference. In the sentence "Він дуже любить себе" (He really loves himself), the pronoun acts as the object: the boy directs his love at his own person. But in the sentence "Він дуже любить свою роботу" (He really loves his job), the pronoun "свою" only indicates whose job it exactly is. Both of these words refer back to the subject of the sentence, but they occupy completely different syntactic positions. The word "себе" is always declined like a noun. Instead, the word "свій" is declined like a regular adjective and always grammatically agrees with the following word.*

English speakers often make a critical mistake when translating sentences like "He told a story about his sister." If you say «Він розповів про його сестру», a Ukrainian will automatically assume he is talking about *another man's* sister. The distinction is strict. Because the subject (he) owns the object (sister), you must always use the reflexive possessive pronoun: «Він розповів про свою сестру».

<!-- INJECT_ACTIVITY: essay-reflexive-self -->
<!-- INJECT_ACTIVITY: error-correction-reflexive-self -->
<!-- INJECT_ACTIVITY: match-up-reflexive-self -->

## Неозначені займенники

Indefinite pronouns express uncertainty about a person, object, or their qualities. We use them when we do not know exactly who or what we are talking about, or when the specific identity simply does not matter. In Ukrainian, these pronouns are built systematically. You take a base interrogative pronoun, such as «хто», «що», or «який», and attach specific particles to it. These particles can act as prefixes or suffixes.

Як зазначає Заболотний у підручнику для 6 класу (с. 203), українська мова має великий набір часток для творення неозначених займенників: -сь, де-, аби-, будь-, -небудь, хтозна-, казна-. Вибір частки залежить від того, наскільки добре мовець знає об'єкт. Наприклад, частки -сь та де- зазвичай вказують на те, що особа чи предмет існують, але залишаються невідомими для слухача. Натомість частки будь- та -небудь показують, що йдеться про будь-кого чи будь-що, і конкретний вибір не має жодного значення.

> *The Ukrainian language has a large set of particles for creating indefinite pronouns: -сь, де-, аби-, будь-, -небудь, хтозна-, казна-. The choice of particle depends on how well the speaker knows the object. For example, the particles -сь and де- usually indicate that a person or object exists, but remains unknown to the listener. In contrast, the particles будь- and -небудь show that it is about absolutely anyone or anything, and the specific choice does not matter at all.*

The spelling of these newly formed pronouns is one of the most important rules you must master. It might look intimidating at first, but Ukrainian students learn a simple mnemonic phrase in school: «Аби десь, але разом». This phrase contains the particles that are always written together with the pronoun.

Займенники з частками аби-, де- та -сь завжди пишуться разом. Тому ми маємо такі слова, як «хтось», «абихто» та «дещо». Натомість частки будь-, -небудь, казна- та хтозна- завжди приєднуються до займенника через дефіс. Так утворюються слова «будь-який», «хто-небудь» або «хтозна-що». Проте існує одне критично важливе правило: якщо між часткою та самим займенником з'являється прийменник, усі три слова пишуться окремо.

> *Pronouns with the particles аби-, де-, and -сь are always written together. Therefore, we have words like "хтось", "абихто", and "дещо". In contrast, the particles будь-, -небудь, казна-, and хтозна- are always attached to the pronoun with a hyphen. This is how the words "будь-який", "хто-небудь", or "хтозна-що" are formed. However, there is one critically important rule: if a preposition appears between the particle and the pronoun itself, all three words are written separately.*

This preposition rule is a defining feature of Ukrainian grammar. If you want to say "with anyone" using the pronoun «будь-хто», the preposition «з» physically splits the word. The particle detaches from the front, creating the phrase «будь з ким». The same happens with «казна-хто», which becomes «казна у кого» when combined with the preposition «у». Notice that suffixes like «-сь» and «-небудь» stay attached to the end of the declined pronoun, so the preposition simply goes before the whole word: «з кимось» or «до кого-небудь».

:::info
**Правопис неозначених займенників**
- **Разом:** хтось, дещо, абиякий
- **Через дефіс:** будь-хто, що-небудь, казна-чий
- **Окремо:** будь до кого, казна з чим, аби в чому
:::

While English relies heavily on words like "someone" or "anyone", Ukrainian nuances are much more precise. The difference between «хтось», «хто-небудь», and «будь-хто» lies entirely in the speaker's intention and the context of the sentence.

Займенник «хтось» означає конкретну особу, про яку мовець знає, але не називає її прямо. Наприклад, у реченні «Хтось стукає у двері» ми розуміємо, що там стоїть реальна людина. Займенник «хто-небудь» використовується для гіпотетичних ситуацій, часто в питаннях чи проханнях, коли йдеться про невідому особу взагалі. Ви можете запитати: «Чи є тут хто-небудь?». А от займенник «будь-хто» підкреслює повну відсутність обмежень. Фраза «Будь-хто може це прочитати» означає, що кожна людина має таку можливість, незалежно від її особистості.

> *The pronoun "хтось" means a specific person whom the speaker knows about but does not name directly. For example, in the sentence "Someone is knocking on the door," we understand that a real person is standing there. The pronoun "хто-небудь" is used for hypothetical situations, often in questions or requests, when it is about an unknown person in general. You might ask: "Is anyone here?". But the pronoun "будь-хто" emphasizes a complete absence of restrictions. The phrase "Anyone can read this" means that absolutely every person has this opportunity, regardless of their identity.*

Beyond the standard indefinite pronouns, Ukrainian has several highly expressive particles that add emotional color to your speech. These are often used in informal contexts or literature to convey dismissiveness, extreme uncertainty, or vagueness.

Частка аби- часто додає відтінок зневаги або байдужості. Наприклад, слово «абиякий» описує предмет дуже низької якості, який зробили без старання. Частки казна- та хтозна- виражають надзвичайну невпевненість мовця, ніби лише вищі сили знають відповідь: «Він приніс хтозна-що». На противагу їм, займенники з часткою де-, такі як «дехто» або «дещо», вказують на певну групу людей чи речей, які добре відомі мовцю, але він навмисно згадує про них дуже туманно.

> *The particle аби- often adds a shade of dismissiveness or indifference. For example, the word "абиякий" describes an object of very low quality, which was made without effort. The particles казна- and хтозна- express the speaker's extreme uncertainty, as if only higher powers know the answer: "He brought who knows what." In contrast to them, pronouns with the particle де-, such as "дехто" or "дещо", indicate a certain group of people or things that are well known to the speaker, but he deliberately mentions them very vaguely.*

## Заперечні займенники

When we need to express the complete absence of a person, object, characteristic, or quantity, we rely on negative pronouns. These are formed simply by adding the prefix **ні-** to the basic interrogative pronouns you already know. For example, «хто» (who) becomes «ніхто» (nobody), and «що» (what) becomes «ніщо» (nothing). The same logic applies to adjectives and quantities: «який» becomes «ніякий» (no kind of / none), «чий» becomes «нічий» (nobody's), and «скільки» becomes «ніскільки» (not at all / none). Because they are built directly on top of interrogative pronouns, their declension is identical. You decline the base word while keeping the prefix attached. If you know how to decline «хто» through all seven cases, you already know how to decline «ніхто». The Genitive «кого» becomes «нікого», the Dative «кому» becomes «нікому», and the Instrumental «ким» becomes «ніким».

Заперечні займенники допомагають нам описати порожнечу, відсутність або повну відмову від чогось. Якщо ви питаєте, чия це річ, і вона не належить жодній людині у світі, ви впевнено кажете, що це нічия річ. Коли ми говоримо про ситуацію, де немає жодного вибору або жодного шансу на успіх, ми використовуємо займенник ніякий. Цей заперечний префікс завжди пишеться разом із самим займенником, якщо між ними немає інших слів. Це базове правило правопису, яке потрібно пам'ятати завжди.

> *Negative pronouns help us describe emptiness, absence, or a complete rejection of something. If you ask whose thing this is, and it does not belong to any person in the world, you confidently say that it is nobody's thing. When we talk about a situation where there is no choice or no chance of success, we use the pronoun "ніякий" (no kind of). This negative prefix is always written together with the pronoun itself if there are no other words between them. This is a basic spelling rule that you must always remember.*

:::info **Відмінювання заперечних займенників**
The declension matches the base pronoun perfectly. For instance, the Instrumental case of «що» is «чим», so "with nothing" is «нічим». The Dative case of «хто» is «кому», making "to nobody" «нікому».
:::

However, Ukrainian syntax has a very distinct and elegant feature when it comes to negative pronouns and prepositions. This is known as the preposition split rule, a key feature highlighted in Ukrainian school textbooks (e.g., Zabolotnyi, Grade 6, p. 204). If a negative pronoun needs to be used with any preposition, that preposition physically splits the word in two. The prefix **ні-** detaches from the front of the base pronoun, and the preposition slides right into the middle. This creates a three-word phrase that is always written separately. For instance, if you want to say "with nobody", you take «ніхто», change it to the Instrumental case «ніким», and then insert the preposition «з» into the split. The resulting phrase is «ні з ким». Writing *«нізким» as a single word is a severe grammatical error. The exact same rule applies to all prepositions and all negative pronouns. If you want to say "about nothing", it becomes «ні про що» (not *«ніпрощо»). If you want to say "in no kind of", it splits into «ні в якому». This separating behavior is a unique characteristic that distinguishes Ukrainian from many other European languages.

As highlighted by Lytvinova (Grade 6, p. 269), another fascinating layer of Ukrainian negative pronouns is how their meaning changes entirely based on where the stress falls. This is a crucial phonetic nuance, particularly important for the Genitive forms «нікого» and «нічого». If you place the stress on the root of the word—«нікого» or «нічого»—you are simply stating that someone or something is completely absent. It is a factual statement of non-existence. But if you shift the phonetic stress to the prefix—«нíкого» or «нíчого»—the meaning transforms into a lack of opportunity or possibility to do something. It implies that there is an action you want or need to perform, but no available target for that action.

У кімнаті зараз нікого немає, тому що всі студенти вже пішли додому. Мені нíкого спитати про правильну дорогу, бо ця вулиця зовсім порожня. Я щойно відкрив свій холодильник, але там нічого немає. Мені нíчого їсти сьогодні ввечері, тому доведеться йти в найближчий магазин.

> *There is nobody in the room right now because all the students have already gone home. I have absolutely nobody to ask about the right way because this street is completely empty. I just opened my fridge, but there is nothing there. I have nothing to eat tonight, so I will have to go to the nearest store.*

Finally, you must master the double negation rule, which is a fundamental hallmark of Slavic syntax. In English, grammar rules dictate that you use a single negative word per clause: you say either "Nobody knows" or "He knows nothing". If you translate this logic literally into Ukrainian and say *«Ніхто знає», it sounds completely incomplete and broken to a native speaker. In Ukrainian, the presence of any negative pronoun in a sentence absolutely requires the negative particle **не** to be placed directly before the verb. You must negate both the subject or object and the action itself. The correct and only way to phrase this is «Ніхто не знає» (which translates literally to "Nobody does not know"). This rule is absolute and applies across all contexts: «Я нічого не бачу» (I see nothing), «Ми ні з ким не розмовляли» (We spoke with nobody). Embracing this double negation structure is essential for building natural, fluent Ukrainian sentences and avoiding awkward interference from your native language.

## Займенники в контексті

To truly master advanced pronouns, you need to see how they operate together to build a narrative. Read the following detective excerpt and pay close attention to how indefinite, negative, and reflexive pronouns drive the mystery forward.

Хтось залишив двері кабінету відчиненими. Я зазирнув усередину і тихо запитав себе: хто це міг бути? Ніхто не відповів. У кімнаті нікого не було, але я відчував чиюсь присутність. На столі лежало щось дивне — старий щоденник, який не належав нікому з нас. Будь-хто міг зайти сюди і взяти те, що йому було потрібно. Але що саме шукав цей хтось? Я ретельно оглянув приміщення. На підлозі не було нічиїх слідів, а у вікні не виднілося нічого підозрілого. Я ні з ким не говорив про цей кабінет. Дехто з колег вважав професора диваком, який тримається сам по собі. Він нікому не довіряв свої дослідження і ні з ким не ділився відкриттями. Якийсь таємний мотив змусив когось проникнути сюди. Я ще раз оглянув кімнату, намагаючись уявити собі події останньої години. Я поклав щоденник у сумку і вирішив, що завтра розпитаю будь-кого, хто чергував на поверсі. Наразі мені нічого було робити.

> *Someone had left the office door open. I peeked inside and quietly asked myself: who could it be? Nobody answered. There was no one in the room, but I felt someone's presence. Something strange lay on the desk — an old diary that belonged to none of us. Anyone could have come in here and taken what they needed. But what exactly was this someone looking for? I thoroughly inspected the room. There were nobody's footprints on the floor, and nothing suspicious could be seen in the window. I had spoken with no one about this office. Some colleagues considered the professor an eccentric who keeps to himself. He trusted no one with his research and shared his discoveries with no one. Some secret motive forced someone to break in here. I surveyed the room once more, trying to imagine the events of the last hour to myself. I put the diary in my bag and decided that tomorrow I would question anyone who was on duty on the floor. For now, there was nothing for me to do.*

This same principle applies to everyday conversations. Consider a brief dialogue about a mysterious event:

> — Хтось тобі дзвонив?
> — Ні, мені ніхто не дзвонив.
> — Може, хто-небудь із сусідів?
> — Ні, ні з ким я не розмовляв.

Pronouns are equally crucial in abstract discussions. Read this philosophical debate from a university seminar. 

> — **Професор:** Сьогодні ми говоримо про істину. Кожен має свою думку, але чи існує об'єктивна реальність? *(Today we are talking about truth. Everyone has their own opinion, but does objective reality exist?)*
> — **Олена:** Мені здається, що будь-яка відповідь може бути правильною за певних умов. Ніщо не є хибним. *(It seems to me that any answer can be correct under certain conditions. Nothing is absolutely false.)*
> — **Марко:** Я ні з чим не можу погодитися. Якщо все правильно, то істина втрачає сенс. Ніхто не може заперечити очевидні факти. *(I cannot agree with anything. If everything is correct, then truth loses its meaning. Nobody can deny obvious facts.)*
> — **Олена:** Але дехто з нас бачить факти інакше! Те, що для тебе очевидне, для когось іншого — ілюзія. Люди часто обманюють самі себе. *(But some of us see facts differently! What is obvious to you is an illusion for someone else. People often deceive themselves.)*
> — **Професор:** Це цікава думка. Хто-небудь хоче додати щось до слів Олени? Чия позиція вам ближча? *(This is an interesting thought. Does anyone want to add something to Olena's words? Whose position is closer to you?)*
> — **Андрій:** Я згоден з Марком. Ми не можемо просто вигадувати будь-що. Інакше ми ніколи ні до чого не дійдемо в наших дискусіях. *(I agree with Marko. We cannot just invent anything. Otherwise, we will never arrive at anything in our discussions.)*

When analyzing these texts, you can see how advanced pronouns fluidly connect ideas. In the detective story, indefinite pronouns like «хтось» and «щось» build suspense by pointing to a specific but unknown entity. The detective also uses the reflexive pronoun in the phrases «запитав себе» and «уявити собі», demonstrating how the action reflects back onto the subject regardless of the grammatical person.

The dialogue showcases the unique interaction between negative pronouns and prepositions. When Marko says «ні з чим не можу погодитися», he uses the Instrumental case form of «ніщо», which is «нічим». However, because the verb requires the preposition «з», it splits the negative pronoun into three separate words: «ні з чим». We see this exact same structural behavior when Andriy says «ні до чого не дійдемо», where the preposition «до» splits the Genitive form «нічого» into «ні до чого».

:::info
**Spelling reminder**
Remember that indefinite pronouns formed with the prefixes «будь-» and «-небудь» are always hyphenated (e.g., «будь-яка», «хто-небудь»), while those with «де-» and «-сь» are written as a single, joined word (e.g., «дехто», «щось»).
:::

You can also observe the strict application of the double negation rule. In Ukrainian, saying "nobody answered" requires negating both the pronoun and the verb: «ніхто не відповів». Similarly, "trusted no one" becomes «нікому не довіряв». This dual structure is mandatory for all negative pronouns across all cases. If you were to translate English logic directly and say «ніхто відповів», it would sound completely ungrammatical. The negative particle «не» is the anchor that holds the entire negative sentence together.

Finally, notice how the definitive pronoun «кожен» sets the stage in the dialogue. When the professor says «Кожен має свою думку», he uses it to refer to all individuals within a group, highlighting the universal nature of the statement before the students begin to debate the specifics using indefinite and negative forms.

## Означальні займенники

The final category of pronouns you need to master at the B1 level is the definitive pronouns (означальні займенники, taught in Zabolotnyi Grade 6, p. 201). These words help us generalize or identify specific entities within a larger group. The core set includes **кожен** (every) and **весь** (all), which provide complete coverage without exceptions. It also includes words like «сам», «самий», and «інший», which help with precise isolation. Unlike indefinite pronouns which leave things vague, definitive pronouns make exact statements.

Означальні займенники часто зустрічаються в текстах про суспільство, філософію або історію. Наприклад, кожен громадянин має певні права. Увесь світ спостерігав за цими важливими подіями. Іноді людина сама обирає свій шлях, не чекаючи допомоги від інших.

> *Definitive pronouns are often found in texts about society, philosophy, or history. For example, every citizen has certain rights. The entire world watched these important events. Sometimes a person chooses their path alone, not waiting for help from others.*

Most definitive pronouns decline exactly like hard-stem adjectives. However, the pronoun **весь** (all) has an irregular declension paradigm. Because it is used so frequently, these forms are essential to memorize.

У чоловічому роді займенник має форми весь або увесь у називному відмінку. У родовому відмінку ми кажемо всього, у давальному — всьому, а в орудному використовуємо форму всім. У місцевому відмінку правильним варіантом буде на всьому. Жіночий рід має форми вся, всієї, всій, всю, всією, на всій, а середній рід — все, всього, всьому, все, всім, на всьому.

> *In the masculine gender, the pronoun has the forms "весь" or "увесь" in the Nominative case. In the Genitive case, we say "всього", in the Dative — "всьому", and in the Instrumental we use the form "всім". In the Locative case, the correct option will be "на всьому". The feminine gender has the forms "вся", "всієї", "всій", "всю", "всією", "на всій", and the neuter gender — "все", "всього", "всьому", "все", "всім", "на всьому".*

:::info
**Plural forms and Euphony**
In the plural, the pronoun for 'all' translates to **всі** (all). It declines as: Р.в. *всіх*, Д.в. *всім*, Зн.в. *всіх* or *всі*, Ор.в. *всіма*, М.в. *на всіх*. Notice how Ukrainian euphony dictates the use of the variants. To avoid difficult consonant clusters, Ukrainian inserts a vowel into prepositions. For example, the preposition «з» changes to «зі» before the Instrumental plural form, resulting in the phrase **зі всіма** (with everyone). This is the exact same principle that gives us «зі мною».
:::

One of the most common pitfalls for learners is distinguishing between the pronouns **сам** (self) and **самий** (the very). While they look incredibly similar, they serve completely different functions. The first emphasizes independence or lack of assistance, translating to 'oneself' or 'alone'. The second emphasizes exact identity or extreme location, translating to 'the same'.

Я сам можу перекласти цей текст, мені не потрібен словник. У цьому реченні займенник показує, що дія виконується самостійно. Але якщо ми хочемо вказати на конкретну людину, ми скажемо інакше. Це той самий професор, який читав нам лекцію вчора. Також ми можемо сказати, що зустріч відбулася в самому центрі міста.

> *I can translate this text myself, I do not need a dictionary. In this sentence, the pronoun shows that the action is performed independently. But if we want to point to a specific person, we will say it differently. This is the same professor who gave us a lecture yesterday. We can also say that the meeting took place in the very center of the city.*

The remaining core definitive pronouns, **інший** (other) and **кожен** (every), are straightforward. They decline exactly like standard adjectives. You simply match their gender, number, and case to the noun they modify. Therefore, 'to every student' becomes «кожному студенту» in the Dative case, and 'with other people' becomes «з іншими людьми» in the Instrumental case. Mastering these adjectival endings will allow you to construct precise descriptions.

## Підсумок

У цьому модулі ми детально розглянули шість ключових розрядів займенників. Їхнє правильне використання дозволяє будувати складні речення, ставити точні запитання та виражати найтонші відтінки значень — від повної відсутності до абсолютної впевненості. Зворотний займенник показує, що дія спрямована на самого діяча. Неозначені вказують на невідомі об'єкти, а заперечні підкреслюють їхню відсутність. Означальні займенники виражають повноту або ідентичність. Особливу увагу варто звернути на правопис: частки можуть писатися разом, через дефіс або окремо, якщо з'являється прийменник.

> *In this module, we have examined six key categories of pronouns in detail. Their correct use allows you to build complex sentences, ask precise questions, and express the subtlest shades of meaning — from complete absence to absolute certainty. The reflexive pronoun shows that an action is directed at the doer. Indefinite pronouns point to unknown objects, while negative pronouns emphasize their absence. Definitive pronouns express completeness or identity. Special attention should be paid to spelling: particles can be written together, hyphenated, or separately if a preposition appears.*

| Розряд (Category) | Основні займенники (Core Pronouns) | Ключові правила (Key Rules & Nuances) |
| :--- | :--- | :--- |
| **Особові** (Personal) | я, ти, він, вона, ми, ви, вони | Require an inserted «н-» after prepositions («до нього», «з нею»). |
| **Питально-відносні** (Interrogative-Relative) | хто, що, який, чий, котрий | Used for direct questions or to connect relative clauses. |
| **Зворотний** (Reflexive) | себе (себе, собі, собою) | No Nominative case. Always refers back to the subject. |
| **Неозначені** (Indefinite) | хтось, будь-хто, що-небудь, дехто | Spelling rules: «-сь», «де-» (together); «будь-», «-небудь» (hyphenated). |
| **Заперечні** (Negative) | ніхто, ніщо, ніякий, нічий | Double negation is mandatory. Prepositions split the word («ні з ким»). |
| **Означальні** (Definitive) | кожен, весь, сам, самий, інший | «Весь» has an irregular declension. «Сам» (alone) vs «самий» (the same). |

:::info
**Spelling Check**
Remember the golden rules for indefinite and negative pronouns. Particles like «-сь» and «де-» are always written together (хтось, дехто). Particles like «будь-» and «-небудь» always require a hyphen (будь-який, що-небудь). However, the moment a preposition enters a negative pronoun, the structure breaks into three separate words (ні в кого, ні про що).
:::

**Питання для самоперевірки**

**1. Чому заперечні займенники пишуться трьома словами (ні з ким)?**

If a preposition appears between the negative particle «ні-» and the pronoun itself, it splits the word apart. Ukrainian does not allow a preposition to stand before a whole negative pronoun. Therefore, instead of the incorrect «з ніким», we always write «ні з ким», «ні в чому», or «ні до кого».

**2. Яка різниця між нікого і нíкого?**

The difference lies in the stress and the resulting meaning. The form «нікого» (stress on the root) indicates the physical absence of people, translating to 'nobody' (for example, «Там нікого немає»). The form «нíкого» (stress on the prefix) implies a lack of choice or an impossible action, translating to 'nobody to [verb]' (for example, «Мені нікого спитати»).

**3. Чому зворотний займенник себе не має називного відмінка?**

The reflexive pronoun «себе» can never act as the main doer (the subject) of a sentence. Its sole grammatical purpose is to reflect the action back onto the subject. Because the Nominative case is strictly reserved for subjects, «себе» exists only in the oblique cases, such as «себе», «собі», and «собою».

**4. Коли ми використовуємо -небудь замість -сь?**

The suffix «-сь» (like in «хтось» or «щось») points to a specific but unknown entity that actually exists; it is used for stating facts. The suffix «-небудь» (like in «хто-небудь» or «що-небудь») expresses absolute indefiniteness or 'anyone/anything at all'. You will most often use it in questions, open requests, or hypothetical scenarios where the specific identity truly does not matter.

**Preview:** In the next module, *Житло і оренда*, you will apply all the grammar from this phase in a highly practical communication context.
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: advanced-pronouns
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

**Level: B1 (Module 63)**

**Instructions in Ukrainian.** All activity types appropriate.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


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
