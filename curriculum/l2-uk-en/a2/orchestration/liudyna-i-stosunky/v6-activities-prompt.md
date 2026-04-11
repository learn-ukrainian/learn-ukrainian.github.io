<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/liudyna-i-stosunky.yaml` file for module **4: Яка вона людина? Описуємо людей навколо нас** (a2).

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

- `<!-- INJECT_ACTIVITY: match-character-traits -->`
- `<!-- INJECT_ACTIVITY: quiz-character-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-adjective-agreement -->`
- `<!-- INJECT_ACTIVITY: group-sort-traits -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match personality adjectives to their definitions or example situations
  items: 8
  type: match-up
- focus: 'Choose the correct adjective to complete a person description (Він завжди
    допомагає — він дуже ___: щирий/ледачий/сумний)'
  items: 8
  type: quiz
- focus: Complete sentences describing people with the correct adjective form (agreement
    for gender)
  items: 8
  type: fill-in
- focus: Sort personality adjectives into positive traits and challenging traits
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- впертий (stubborn, persistent)
- чуйний (responsive, caring)
- наполегливий (persistent, determined)
- родич (relative)
- знайомий (acquaintance)
required:
- людина (person, human being)
- стосунок (relationship)
- характер (character, personality)
- зовнішність (appearance)
- привітний (friendly, welcoming)
- щирий (sincere, genuine)
- працьовитий (hardworking)
- терплячий (patient)
- сусід (neighbor)
- описувати (to describe)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Зовнішність: як виглядає людина? (Appearance: What Does a Person Look Like?)

We describe people every day. Whether meeting someone new, looking for a friend, or telling a story about a stranger, you need to know how to describe them. In Ukrainian, we use the verb **описувати** to talk about this action. The noun we focus on is **зовнішність**, which means appearance. This word covers everything you see on the outside, from head to toe. When we want to know about someone's appearance, we ask: «Як він виглядає?» or «Як вона виглядає?».

Щодня ми зустрічаємо різних людей на вулиці чи на роботі. Іноді нам потрібно описати когось для колег. Ми часто говоримо про зовнішність людини, коли шукаємо її в натовпі. Це дуже корисна навичка. Якщо ви не знаєте людину, ви завжди можете запитати: «Як вона виглядає?».

> *Every day we meet different people on the street or at work. Sometimes we need to describe someone for colleagues. We often talk about a person's appearance when we are looking for them in a crowd. This is a very useful skill. If you don't know the person, you can always ask: "What does she look like?".*

When describing physical traits, we start with height and build. We use simple adjective pairs for a quick picture. For height, a person can be **високий** (tall) or **низький** (short). For build, someone might be **худий** or **повний**. We also categorize people by age. We use words like **молодий** for young people and **старий** for older individuals. You can also specify if someone is middle-aged using the phrase **середнього віку**.

Мій брат дуже високий і худий. Він ще зовсім молодий, багато займається спортом і має гарний вигляд. Наш сусід Петро — низький і трохи повний чоловік. Він старий, але дуже активний. А моя мама — жінка середнього віку. Вона має чудову фігуру.

> *My brother is very tall and thin. He is still quite young, does a lot of sports and looks good. Our neighbor Petro is a short and slightly stout man. He is old, but very active. And my mom is a middle-aged woman. She has a wonderful figure.*

:::note
**Quick tip** — When you want to describe someone with an average height or build, use the phrases **середнього зросту** (of average height) or **середньої статури** (of average build).
:::

Next, we move to the face and the eyes. There are two common patterns for eye color. You can say someone *has* a certain color using «У неї...» or «У нього...». Alternatively, use a single adjective like **кароока** (brown-eyed). The most common eye colors are **сині**, **зелені**, **сірі**, and **карі**. We also describe facial features, such as a round face or a straight nose.

У сестри великі карі очі та кругле обличчя. Її чоловік має зелені очі та прямий ніс. Моя донька блакитноока, як і мій батько. Мені подобаються люди, які мають виразні сірі очі. Коли людина усміхається, її обличчя стає набагато красивішим.

> *My sister has large brown eyes and a round face. Her husband has green eyes and a straight nose. My daughter is blue-eyed, just like my father. I like people who have expressive grey eyes. When a person smiles, their face becomes much more beautiful.*

Hair is a key part of any description. In Ukrainian, hair is **волосся**, which is a neuter singular noun. We describe it by color, length, and style. Common colors include **темне**, **світле**, **русяве**, **руде**, and **сиве**. Hair can be **коротке** or **довге**, and its texture **хвилясте** (wavy) or **пряме** (straight). For a specific cut, we use the word **зачіска**.

Подруга Олена завжди мала довге русяве волосся. Але вчора вона зробила нову коротку зачіску. Тепер у неї стильне темне волосся. Її брат має руде хвилясте волосся, яке виглядає трохи неохайно. А наш дідусь має зовсім сиве волосся, але модну зачіску.

> *My friend Olena always had long light brown hair. But yesterday she got a new short hairstyle. Now she has stylish dark hair. Her brother has red wavy hair that looks a bit messy. And our grandfather has completely grey hair, but a fashionable haircut.*

Let's see how these descriptions work in a natural conversation. Two friends are looking at photos on a phone and describing the people they see.

> — **Подруга 1:** Дивись, це моя сестра Олена. Вона дуже висока, має довге русяве волосся і великі зелені очі. *(Look, this is my sister Olena. She is very tall, has long light brown hair and large green eyes.)*
> — **Подруга 2:** Вона дуже гарна дівчина! А хто цей чоловік поруч із нею? *(She is a very beautiful girl! And who is this man next to her?)*
> — **Подруга 1:** А це мій сусід, пан Іван. Він уже старий, але дуже ставний чоловік. У нього гарна сива зачіска. *(And this is my neighbor, Mr. Ivan. He is already old, but a very imposing man. He has a nice grey haircut.)*
> — **Подруга 2:** У нього справді дуже приємне обличчя. *(He really has a very pleasant face.)*

## Характер: яка вона людина? (Character: What Kind of Person Is She?)

When we want to know more about someone's personality, we ask about their **характер** (character). In Ukrainian, describing a person's inner qualities is just as important as talking about their appearance. To ask what kind of person someone is, we use the question «Яка вона людина?» or «Який у нього характер?». Let's start with some of the most common positive traits. A person can be **добрий** (kind), **привітний** (friendly or welcoming), and **щирий** (sincere). When you want to emphasize these qualities, you can combine the adjective with the word «людина». Notice how the adjective always matches the gender of the noun. Since «людина» is a feminine noun, we use the feminine form of the adjective, even if we are talking about a man.

Мій новий сусід — дуже привітна людина. Він завжди каже «добрий ранок» і посміхається. Його дружина також дуже добра і щира. Вони приємні люди, і мені подобається з ними спілкуватися. Мій брат — теж дуже добра людина, він завжди готовий вислухати.

> *My new neighbor is a very friendly person. He always says "good morning" and smiles. His wife is also very kind and sincere. They are pleasant people, and I like talking to them. My brother is also a very kind person, he is always ready to listen.*

Beyond basic kindness, we often describe how people behave at work, in school, or when facing challenges. These qualities show a person's approach to their daily tasks and responsibilities. A person who works a lot and loves their job is **працьовитий** (hardworking). Someone you can always rely on to finish a task is **відповідальний** (responsible). When learning a language or doing difficult work, it is important to be **терплячий** (patient). And if you never give up on your goals, you are **наполегливий** (determined or persistent). These adjectives are highly valued in Ukrainian culture, as they show that a person is reliable and dedicated.

Наша нова вчителька дуже відповідальна і терпляча. Вона завжди пояснює складні правила кілька разів. Мій колега Максим — дуже працьовитий хлопець. Він часто працює ввечері, щоб закінчити важливий проєкт. А моя сестра дуже наполеглива, тому вона завжди досягає своєї мети.

> *Our new teacher is very responsible and patient. She always explains difficult rules several times. My colleague Maksym is a very hardworking guy. He often works in the evening to finish an important project. And my sister is very determined, so she always achieves her goal.*

Of course, not all character traits are entirely positive. Sometimes people can be **ледачий** (lazy) and avoid work, or they might be very **серйозний** (serious) and rarely joke. A person who doesn't talk much is **тихий** (quiet). An interesting word in Ukrainian is **впертий** (stubborn). While it can mean that someone refuses to listen to others, it frequently has a positive meaning. 

:::tip
**Did you know?** — In Ukrainian, calling someone **впертий** often means they are principled, stand their ground, and don't give up easily. It is frequently used as a compliment for someone who fights for what is right.
:::

Мій молодший син іноді буває ледачий, коли треба прибирати кімнату. Але в школі він дуже впертий і завжди робить домашнє завдання ідеально. Мій дідусь — тихий і серйозний чоловік, але він має золоте серце.

> *My younger son is sometimes lazy when he needs to clean his room. But at school, he is very stubborn and always does his homework perfectly. My grandfather is a quiet and serious man, but he has a heart of gold.*

When we talk about someone's character, we often describe their actions. We judge what kind of person someone is based on what they do. To describe habitual behavior or permanent character traits, we use imperfective verbs. For example, if someone is kind, we say «він завжди допомагає» (he always helps). However, if we want to give a specific example or proof of their character from a past event, we use perfective verbs. We say «вчора він мені допоміг» (yesterday he helped me).

Мій друг Андрій — дуже чуйна людина. Він завжди допомагає своїм друзям, коли у них є проблеми. Наприклад, минулого тижня він допоміг мені відремонтувати машину. Оксана дуже відповідальна, вона завжди купує квитки заздалегідь. Учора вона купила нам квитки на поїзд.

> *My friend Andriy is a very responsive person. He always helps his friends when they have problems. For example, last week he helped me repair my car. Oksana is very responsible, she always buys tickets in advance. Yesterday she bought us train tickets.*

Let's look at how people discuss character and personality in a workplace setting. Imagine it is someone's first day at a new office.

> — **Новий працівник:** Розкажи мені трохи про нашу команду. Яка наша керівниця? *(Tell me a little about our team. What is our manager like?)*
> — **Досвідчений колега:** Вона дуже відповідальна і справедлива, але іноді буває дуже серйозна. *(She is very responsible and fair, but sometimes she is very serious.)*
> — **Новий працівник:** А інші колеги? *(And the other colleagues?)*
> — **Досвідчений колега:** Усі дуже привітні, особливо Максим. Він завжди підказує новим працівникам. *(Everyone is very friendly, especially Maksym. He always gives tips to new employees.)*

<!-- INJECT_ACTIVITY: match-character-traits -->
<!-- INJECT_ACTIVITY: quiz-character-choice -->

## Люди навколо нас: родичі, друзі, знайомі (People Around Us)

When we talk about the people around us, we need to know exactly how to name our relationships. In English, the word "friend" can cover a wide range of people, from someone you have known since childhood to someone you occasionally chat with at work. Ukrainian makes clearer distinctions based on closeness and context.

Найближча людина для нас — це друг або подруга. З друзями ми часто проводимо вільний час і ділимося секретами. Для справжніх друзів зовнішність не має великого значення, головне — це щирий характер. Наприклад, ми з Оксаною дружимо давно. Інше важливе слово — це товариш. Товариш — це людина, з якою ми вчимося або працюємо. А якщо ми просто знаємо людину, але не спілкуємося близько, це знайомий або знайома. 

> *The closest person to us is a male friend or a female friend. We often spend our free time and share secrets with friends. For true friends, appearance does not have a great meaning; the main thing is a sincere character. For example, Oksana and I have been friends for a long time. Another important word is a comrade. A comrade is a person with whom we study or work. And if we simply know a person but don't communicate closely, it is an acquaintance (male or female).*

Community and local connections are a significant part of daily life. The people who live in the same building or on the same street form a unique social circle.

Людина, яка живе поруч із вами, — це сусід або сусідка. В Україні сусіди часто не просто живуть поруч, а активно спілкуються і допомагають одне одному. Мій сусід живе поруч, на першому поверсі. Він дуже привітний і чуйний чоловік. Ми часто зустрічаємося вранці і бажаємо одне одному гарного дня. У нашому будинку всі сусіди — це одна велика команда.

> *The person who lives next to you is a neighbor (male or female). In Ukraine, neighbors often don't just live nearby, but actively communicate and help each other. My neighbor lives nearby, on the first floor. He is a very friendly and responsive man. We often meet in the morning and wish each other a good day. In our building, all the neighbors are one big team.*

:::tip
**Did you know?** — In Ukrainian apartment buildings, it is very common to know your neighbors well. People might borrow sugar or salt, help water the plants when someone is on vacation, or collectively take care of the yard. A good **сусід** is considered a blessing.
:::

Beyond our friends and neighbors, our core support system is our family. Let's recap some family vocabulary and practice using the descriptive adjectives we learned earlier to talk about our relatives.

Звісно, найважливіші люди — це наша родина. Ми можемо легко описувати наших родичів. У мене є впертий, але веселий дядько і дуже терпляча тітка. Мій двоюрідний брат — наполегливий студент, він живе в іншому місті. Усі мої родичі — це дуже працьовиті люди. Ми часто зустрічаємося на свята.

> *Of course, the most important people are our family. We can easily describe our relatives. I have a stubborn but cheerful uncle and a very patient aunt. My cousin is a determined student; he lives in another city. All my relatives are very hardworking people. We often meet for holidays.*

When we describe our relationships, we often focus on how people treat each other and what actions define their connection. To express this, we use specific verbs of interaction. Notice that some verbs, like "to trust" and "to help", preview a new grammatical pattern — the Dative case, which points to the receiver of the action.

У хороших стосунках люди завжди підтримують одне одного. Часто наші стосунки залежать від характеру людини. Я довіряю своєму другові, тому що він щирий. Вона мені довіряє свої таємниці. Ми поважаємо наших батьків і старших родичів. Мій сусід нам завжди допомагає, коли ми маємо проблеми. Це показує, що ми маємо міцні стосунки з людьми навколо нас.

> *In good relationships, people always support each other. Often, our relationships depend on a person's character. I trust my friend because he is sincere. She trusts me with her secrets. We respect our parents and older relatives. My neighbor always helps us when we have problems. This shows that we have strong relationships with the people around us.*

<!-- INJECT_ACTIVITY: fill-in-adjective-agreement -->
<!-- INJECT_ACTIVITY: group-sort-traits -->

## Описуємо людину цілком (Describing a Person Fully)

Now that we know how to talk about appearance, character, and relationships, we can put it all together to create a complete profile of a person. A natural description usually follows a simple pattern: first, we state who the person is to us, then we describe what they look like, and finally, we explain what kind of character they have. Let's look at how this works in practice.

Це мій найкращий друг Андрій. Ми познайомилися в університеті. Він високий і міцний хлопець із темним волоссям. Андрій дуже веселий, привітний і завжди допомагає друзям. Коли я маю проблему, він уважно слухає і дає гарну пораду. Я дуже поважаю його.

> *This is my best friend Andrii. We met at the university. He is a tall and sturdy guy with dark hair. Andrii is very cheerful, friendly, and always helps his friends. When I have a problem, he listens carefully and gives good advice. I respect him very much.*

Let's compare two different people from our daily lives. Notice how we combine physical traits with personality adjectives to create a clear picture of each person and their typical behavior.

Це моя нова колега Олена. Вона невисока, струнка жінка з карими очима. Олена — дуже працьовита, серйозна і відповідальна працівниця. Вона завжди приходить на роботу вчасно. А це моя сусідка Марія. Вона старша жінка, має сиве волосся і приємну усмішку. Марія дуже весела, щира і чуйна. Вона часто пече пироги і пригощає всіх сусідів.

> *This is my new colleague Olena. She is a short, slim woman with brown eyes. Olena is a very hardworking, serious, and responsible worker. She always comes to work on time. And this is my neighbor Mariia. She is an older woman; she has gray hair and a pleasant smile. Mariia is very cheerful, sincere, and responsive. She often bakes pies and treats all the neighbors.*

In Ukrainian culture, how a person acts and treats others is often considered much more important than their physical appearance. 

В Україні ми часто кажемо «вона добра людина» або «він гарна людина». Це означає, що людина має щирий характер, допомагає іншим і нікого не ображає. Краса обличчя чи фігури — це приємно, але внутрішня доброта є набагато важливішою. Ми можемо сказати, що хтось «красивий», якщо говоримо про зовнішність. Але слова «гарна людина» описують саме душу і характер.

> *In Ukraine, we often say "she is a kind person" or "he is a good person". This means that the person has a sincere character, helps others, and offends no one. Beauty of the face or figure is pleasant, but inner kindness is much more important. We can say that someone is "beautiful" if we are talking about appearance. But the words "a good person" describe exactly the soul and character.*

:::tip
**Inner vs. Outer Beauty** — In Ukrainian, the word **красивий** (beautiful, handsome) is strictly used for physical appearance. However, the word **гарний** (good, nice, pretty) is much broader. When you call someone **гарна людина**, you are praising their inner qualities, character, and soul, making it a very powerful and authentic compliment.
:::

## Підсумок — Summary (~150 words)

In this module, we learned how to fully describe the people in our lives. We started with physical appearance, discussing height, hair, and eye color. Then, we explored personality, covering important traits like being sincere, hardworking, or patient. We also practiced identifying our relationships with others, from close relatives to neighbors and acquaintances. By combining appearance, character, and relationship, you can now paint a complete and natural picture of anyone you know. 

Спробуйте відповісти на ці запитання українською мовою. Як виглядає ваша найкраща подруга або ваш найкращий друг? Який характер у вашого сусіда? І головне: яка ви людина — тиха чи весела, серйозна чи дуже товариська? Опишіть своїх рідних та знайомих.

> *Try to answer these questions in Ukrainian. What does your best friend look like? What kind of character does your neighbor have? And most importantly: what kind of person are you — quiet or cheerful, serious or very sociable? Describe your relatives and acquaintances.*

:::note
**Quick tip** — The best way to remember these new adjectives is to look at photos of your friends and family and describe them out loud in Ukrainian.
:::
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: liudyna-i-stosunky
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

**Level: A2 (Module 4/60) — ELEMENTARY**

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

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

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
