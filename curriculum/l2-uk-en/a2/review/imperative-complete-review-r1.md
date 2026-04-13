## Linguistic Scan
- Factual grammar error: the module derives imperative forms from the wrong infinitives. In [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:63) it says `казати → скажи/скажімо`, `сідати → сядь/сядьмо`, `їхати → поїдь/поїдьмо`, but VESUM confirms these belong to `сказати`, `сісти`, `поїхати`; `казати` gives `кажи/кажімо`, `сідати` gives `сідай/сідаймо`, `їхати` gives `їдь/їдьмо`.
- Factual grammar error: [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:80) teaches `ходімо до парку ... Це доконана дія.` VESUM confirms `ходімо` is the 1pl imperative of imperfective `ходити`.
- Factual grammar error: [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:67) states `Слово «давайте» можна використовувати тільки з інфінітивом`, and the grammar box says `Давайте поговоримо` is incorrect. That contradicts the plan’s own approved pattern `давайте поїдемо`.
- Factual grammar error: the wishes section overstates Instrumental as the only refined norm, and the activity file falsely “corrects” `Діти, будьте уважні!` to `уважними`. Local textbook corpus contains both `Будьте уважні!` and `Будьте уважними!`.

## Exercise Check
- Marker inventory in prose: 5 markers total. Coverage is enough for the 4 planned activity types, but the fill-in marker is duplicated with the same ID at [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:51) and [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:84).
- Injection integrity is broken: the prose expects `unjumble-imperative-sentences`, but the YAML defines `unjumble-wishes-and-commands` at [activities/imperative-complete.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/imperative-complete.yaml:463).
- Exercise logic is wrong in several places: [activities/imperative-complete.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/imperative-complete.yaml:453) maps wrong infinitives to forms (`сідати → сядьмо`, `їхати → поїдьмо`, `йти → ходімо`, `почати → починаймо`), and other items teach false “errors” such as `Давайте поговоримо` and `Діти, будьте уважні!`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All four planned sections and the cooking-class dialogue are present, but the plan explicitly allows `давайте читати, давайте поїдемо`, while the module says `Слово «давайте» можна використовувати тільки з інфінітивом` and bans `Давайте поговоримо`. |
| 2. Linguistic accuracy | 3/10 | `казати → скажи`, `сідати → сядь`, `їхати → поїдь` are wrong lemma-form matches; `ходімо ... Це доконана дія` is false; `Діти, будьте уважні!` is wrongly treated as an error. |
| 3. Pedagogical quality | 5/10 | The module has a clear situation-pattern-practice flow, but it drills incorrect rules in both prose and exercises, so learners would memorize false generalizations. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary such as `хай`, `нехай`, `наказовий спосіб`, `кличний відмінок`, `будь/будьте`, `ходімо`, `давайте`, `щасливою`, `здоровими` appears naturally, and recommended items like `спокійний`, `уважний`, `живи`, `здійснитися`, `мрія` are also used. |
| 5. Exercise quality | 3/10 | The prose duplicates a fill-in marker ID, the unjumble ID does not match between prose and YAML, and the YAML contains wrong answer logic (`сідати → сядьмо`, `їхати → поїдьмо`, `Давайте поговоримо` as false, `Діти, будьте уважні!` as false). |
| 6. Engagement & tone | 8/10 | The chef dialogue and the wishes/toasts material give the lesson some energy and specificity instead of generic gamified filler. |
| 7. Structural integrity | 7/10 | All four H2 sections are present and the pipeline word count is 3137, but duplicate marker IDs and the unjumble ID mismatch create publish-time fragility. |
| 8. Cultural accuracy | 8/10 | The module stays Ukrainian-centered and uses culturally plausible material like cooking-class commands and blessing formulas. |
| 9. Dialogue & conversation quality | 8/10 | The opening exchange has named speakers and a real classroom task, though it stays short and mostly teacher-led. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
  Location: [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:63) — `Дієслово «казати» має наказ «скажи»... Від слова «сідати»... «сядь»... Від слова «їхати»... «поїдь»...`  
  Issue: Wrong infinitive-to-imperative mappings teach incorrect morphology.  
  Fix: Change the infinitives to `сказати`, `сісти`, `поїхати` or change the imperative forms to match `казати`, `сідати`, `їхати`.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
  Location: [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:80) — `Коли ми кажемо «ходімо до парку»... Це доконана дія.`  
  Issue: `ходімо` is imperfective, so the aspect explanation is false.  
  Fix: Say that `ходімо` is an imperfective form that can still refer to one concrete joint action in context.

- [PLAN ADHERENCE] [SEVERITY: critical]  
  Location: plan point [plans/a2/imperative-complete.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a2/imperative-complete.yaml:54) allows `давайте поїдемо`, but [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:69) says `Слово «давайте» можна використовувати тільки з інфінітивом`, and the grammar box labels `Давайте поговоримо` incorrect.  
  Issue: The lesson contradicts the source-of-truth plan and turns a stylistic preference into a categorical ban.  
  Fix: Rewrite this section to say that `давайте` can introduce a softer suggestion, while `-мо` forms are the core pattern learners should master first.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
  Location: [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:108) and [activities/imperative-complete.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/imperative-complete.yaml:293) — `the Instrumental case ... is the gold standard` and `Діти, будьте уважні!` → `уважними`.  
  Issue: This mis-teaches nominative predicative wish formulas as errors, although textbook corpus attests both `Будьте уважні!` and `Будьте уважними!`.  
  Fix: Present Instrumental as an important pattern, but explicitly allow standard nominative-predicative wishes and replace the false correction item.

- [EXERCISE QUALITY] [SEVERITY: critical]  
  Location: [activities/imperative-complete.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/imperative-complete.yaml:453) — `сідати → сядьмо`, `їхати → поїдьмо`, `йти → ходімо`, `почати → починаймо`.  
  Issue: Several answer pairs match the wrong infinitive to the wrong imperative form.  
  Fix: Change the infinitives to `сісти`, `поїхати`, `ходити`, `починати`, or change the right-side forms.

- [EXERCISE QUALITY] [SEVERITY: major]  
  Location: [imperative-complete.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/imperative-complete.md:84) and [activities/imperative-complete.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/imperative-complete.yaml:57), plus [activities/imperative-complete.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/imperative-complete.yaml:463).  
  Issue: The second fill-in reuses the first fill-in ID, and the prose marker `unjumble-imperative-sentences` has no matching YAML ID.  
  Fix: Give the second fill-in a distinct ID and rename the unjumble YAML ID to match the prose marker.

## Verdict: REVISE
Multiple critical findings teach wrong Ukrainian morphology and wrong grammar rules, and the activity YAML repeats those errors. The module is structurally usable and vocabulary-rich, but it cannot ship in this state.

<fixes>
- find: |
    Дієслово «робити» має форму наказу «роби». Щоб сказати це разом, ми використовуємо форму «робімо». Дієслово «казати» має наказ «скажи», тому разом ми кажемо «скажімо». Якщо основа закінчується на м'який приголосний, ми зберігаємо м'який знак. Від слова «сідати» ми утворюємо наказ «сядь», а для групи людей кажемо «сядьмо». Від слова «їхати» ми маємо наказ «поїдь», а разом кажемо «поїдьмо».

    > *The verb "to do" has the command form "do". To say this together, we use the form "let's do". The verb "to say" has the command "say", so together we say "let's say". If the base ends in a soft consonant, we keep the soft sign. From the word "to sit down" we form the command "sit", and for a group of people we say "let's sit". From the word "to drive" we have the command "drive", and together we say "let's drive".*
  replace: |
    Дієслово «робити» має форму наказу «роби». Щоб сказати це разом, ми використовуємо форму «робімо». Дієслово «сказати» має наказ «скажи», тому разом ми кажемо «скажімо». Якщо основа закінчується на м'який приголосний, ми зберігаємо м'який знак. Від слова «сісти» ми утворюємо наказ «сядь», а для групи людей кажемо «сядьмо». Від слова «поїхати» ми маємо наказ «поїдь», а разом кажемо «поїдьмо».

    > *The verb «робити» has the command form «роби», so together we say «робімо». The perfective verb «сказати» has the command form «скажи», so together we say «скажімо». From «сісти» we form «сядь» and «сядьмо». From «поїхати» we form «поїдь» and «поїдьмо».*
- find: |
    You will frequently hear native speakers use the word **давайте** (let's — suggestion particle) followed by an infinitive, such as "давайте читати". This alternative construction is widely understood and often sounds like a gentle proposal. However, you must be extremely careful. While using "давайте" with an infinitive is acceptable in casual everyday speech, combining **давайте** with a conjugated first person plural verb form is considered a direct grammatical error.

    В українській мові не можна казати «давайте поговоримо» або «давай підемо». Це велика помилка і калька з російської мови. Правильно казати тільки «поговорімо» або «ходімо». Слово «давайте» можна використовувати тільки з інфінітивом, наприклад, «давайте читати». Але найкраще і найгарніше завжди використовувати чисту форму на «-мо». Це показує вашу повагу до мови.

    > *In the Ukrainian language, you cannot say "let's talk" or "let's go" using the Russian-style structure. This is a big mistake and a calque from the Russian language. It is correct to say only "let's talk" or "let's go" using the single word. The word "let's" can be used only with an infinitive, for example, "let's read". But it is always best and most beautiful to use the pure form ending in "-mo". This shows your respect for the language.*

    :::info
    **Grammar box**
    Always avoid the structure `Давай(те) + 1st person plural verb`. The phrase ❌ `Давайте поговоримо` is incorrect. The elegant, standard Ukrainian form is ✅ `Поговорімо`.
    :::
  replace: |
    You will frequently hear native speakers use the word **давайте** (let's — suggestion particle) with an infinitive, such as "давайте читати", and you may also hear it with a first person plural future form, such as "давайте поїдемо". This alternative construction is widely understood and often sounds like a gentle proposal. The synthetic **-мо** forms, however, are shorter and are the core imperative pattern learners should actively master first: **поговорімо**, **ходімо**, **зробімо**.

    В українській мові слово «давайте» можна вживати і з інфінітивом, і з формою майбутнього часу першої особи множини: «давайте читати», «давайте поїдемо». Це м'якша пропозиція. Проте синтетичні форми на «-мо» — «поговорімо», «ходімо», «зробімо» — коротші й типовіші для цього значення, тому їх варто добре засвоїти як основну модель спільної дії.

    > *In Ukrainian, **давайте** can introduce a softer suggestion, but the synthetic **-мо** forms are the main imperative pattern learners should practice first.*

    :::info
    **Grammar box**
    `Давай(те)` can introduce a softer suggestion, but the core pattern for shared action is the synthetic imperative: `Поговорімо`, `Ходімо`, `Зробімо`.
    :::
- find: |
    Найпопулярніше слово для спільної дії — це **ходімо** (let's go). Ви також часто будете чути фрази «починаймо», «зробімо це» та «поговорімо». Коли ми кажемо «ходімо до парку», ми маємо на увазі одну конкретну поїздку. Це доконана дія. Але коли вчитель каже «читаймо щодня», він просить робити це регулярно. Це недоконана дія, яка показує звичку.

    > *The most popular word for a shared action is "let's go". You will also often hear the phrases "let's start", "let's do it", and "let's talk". When we say "let's go to the park", we mean one specific trip. This is a perfective action. But when a teacher says "let's read every day", he is asking to do this regularly. This is an imperfective action that shows a habit.*

    <!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->
  replace: |
    Найпопулярніше слово для спільної дії — це **ходімо** (let's go). Ви також часто будете чути фрази «починаймо», «зробімо це» та «поговорімо». Коли ми кажемо «ходімо до парку», ми маємо на увазі одну конкретну спільну дію, але форма **ходімо** походить від недоконаного дієслова «ходити». А коли вчитель каже «читаймо щодня», він просить робити це регулярно. Це теж недоконаний вид, який показує звичку.

    > *The most popular word for a shared action is "ходімо". In context it can refer to one concrete shared action, but the form itself is imperfective. By contrast, "читаймо щодня" is also imperfective and clearly shows a habitual action.*

    <!-- INJECT_ACTIVITY: fill-in-1st-plural-imperative-mo -->
- find: |
    In casual speech, you will absolutely hear people use short forms with the Nominative case, such as «Будь щаслива!» or «Будьте здорові!». These simpler versions are extremely common and perfectly acceptable for informal interactions. However, using the Instrumental case remains the refined, literary standard. When you write a formal greeting card, using the Instrumental case shows that you understand the deep mechanics of the language and adds a layer of profound respect to your greeting.

    :::info
    **Grammar box**
    While short forms like ✅ «Будь здорова!» are popular in casual conversation, the Instrumental case ✅ «Будь здоровою!» is the gold standard for written greetings and formal toasts. It beautifully expresses the idea of *becoming* or *existing* in a certain state.
    :::
  replace: |
    In casual speech, you will absolutely hear people use short forms with the Nominative case, such as «Будь щаслива!» or «Будьте здорові!». These versions are common and standard in many greetings, wishes, and everyday appeals. The Instrumental case is also an important and productive pattern in wishes, especially in examples like «Будь щасливою!» or «Будьте уважними!».

    :::info
    **Grammar box**
    Both patterns occur in Ukrainian wishes: ✅ «Будь здорова! / Будьте здорові!» and ✅ «Будь здоровою! / Будьте уважними!». Teach the Instrumental pattern as important, but do not treat Nominative predicative forms as errors.
    :::
- find: |
    - id: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives
      type: fill-in
      instruction: Вставте правильну форму дієслова для спільної дії (-мо)
      items:
      - sentence: ____ цей текст разом.
        answer: Читаймо
        options:
        - Читаймо
        - Читаємо
        - Читайте
      - sentence: ____ до парку.
        answer: Ходімо
        options:
        - Ходімо
        - Йдемо
        - Ходіть
      - sentence: ____ про це завтра.
        answer: Поговорімо
        options:
        - Поговорімо
        - Давайте поговоримо
        - Поговоріть
  replace: |
    - id: fill-in-1st-plural-imperative-mo
      type: fill-in
      instruction: Вставте правильну форму дієслова для спільної дії (-мо)
      items:
      - sentence: ____ цей текст разом.
        answer: Читаймо
        options:
        - Читаймо
        - Читаємо
        - Читайте
      - sentence: ____ до парку.
        answer: Ходімо
        options:
        - Ходімо
        - Йдемо
        - Ходіть
      - sentence: ____ про це завтра.
        answer: Поговорімо
        options:
        - Поговорімо
        - Хай ми поговоримо
        - Поговоріть
- find: |
      - source: Let's talk about it tomorrow.
        options:
        - text: Поговорімо про це завтра.
          correct: true
        - text: Давайте поговоримо про це завтра.
          correct: false
        - text: Говорімо про це завтра.
          correct: false
  replace: |
      - source: Let's talk about it tomorrow.
        options:
        - text: Поговорімо про це завтра.
          correct: true
        - text: Хай ми поговоримо про це завтра.
          correct: false
        - text: Говорімо про це завтра.
          correct: false
- find: |
      - sentence: Давайте поговоримо про цей проєкт.
        error: Давайте поговоримо
        correction: Поговорімо
        error_type: construction
        options:
        - Поговорімо
        - Давай поговорити
        - Хай поговоримо
        explanation: 'В українській мові для спільної дії використовується форма на -мо:
          поговорімо.'
  replace: |
      - sentence: Хай ми поговоримо про цей проєкт.
        error: Хай ми поговоримо
        correction: Поговорімо
        error_type: construction
        options:
        - Поговорімо
        - Давай поговорити
        - Хай поговоримо
        explanation: 'Для спільної дії природною моделлю є синтетична форма на -мо:
          поговорімо.'
- find: |
      - sentence: Діти, будьте уважні!
        error: уважні
        correction: уважними
        error_type: word
        options:
        - уважними
        - уважного
        - уважному
        explanation: 'У побажаннях найкраще використовувати орудний відмінок: будьте уважними.'
  replace: |
      - sentence: Діти, будь уважними!
        error: будь
        correction: будьте
        error_type: word
        options:
        - будьте
        - будемо
        - бути
        explanation: 'При звертанні до групи людей потрібна форма другої особи множини: будьте.'
- find: |
      - statement: Фраза «Давайте поговоримо» є правильною і літературною.
        correct: false
        explanation: Це калька. Правильно казати «Поговорімо».
  replace: |
      - statement: Форма «поговорімо» стилістично компактніша, ніж «давайте поговоримо».
        correct: true
        explanation: Обидві конструкції можливі, але синтетична форма «поговорімо» коротша й виразніша.
- find: |
      - left: сказати
        right: скажімо
      - left: сідати
        right: сядьмо
      - left: їхати
        right: поїдьмо
      - left: йти
        right: ходімо
      - left: співати
        right: співаймо
      - left: почати
        right: починаймо
  replace: |
      - left: сказати
        right: скажімо
      - left: сісти
        right: сядьмо
      - left: поїхати
        right: поїдьмо
      - left: ходити
        right: ходімо
      - left: співати
        right: співаймо
      - left: починати
        right: починаймо
- find: |
    - id: unjumble-wishes-and-commands
  replace: |
    - id: unjumble-imperative-sentences
</fixes>