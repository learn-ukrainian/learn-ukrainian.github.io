<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-pronouns.yaml` file for module **17: Мені, тобі, йому...** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-match-nominative-pronoun-to-its-dative-form -->`
- `<!-- INJECT_ACTIVITY: fill-in-dative-pronouns -->`
- `<!-- INJECT_ACTIVITY: true-false-impersonal -->`
- `<!-- INJECT_ACTIVITY: quiz-case-choice -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match nominative pronoun to its dative form (я→мені, ти→тобі, etc.)
  items: 8
  type: match-up
- focus: Complete sentences with the correct dative pronoun based on context
  items: 8
  type: fill-in
- focus: Choose dative or accusative pronoun form in context (тобі vs. тебе)
  items: 8
  type: quiz
- focus: Judge whether impersonal dative sentences (мені холодно, мені бачу) are correct
  items: 8
  type: true-false


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- приємно (pleasant)
- цікаво (interesting)
- сумно (sad (impersonal state))
- важко (difficult, hard)
required:
- давальний відмінок (dative case)
- мені (to me)
- тобі (to you (informal))
- йому (to him, to it)
- їй (to her)
- нам (to us)
- вам (to you (formal/plural))
- їм (to them)
- холодно (cold (impersonal state))
- потрібно (necessary, needed)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Давальний відмінок: Кому? (The Dative Case: To Whom?)

Welcome to the **давальний відмінок** *(dative case)*. The name of this case comes directly from the verb **давати** *(to give)*. This perfectly illustrates its primary function in the Ukrainian language: it points out the recipient of an action. When you give a gift, tell a secret, or send an email, the person on the receiving end is in the dative case. 

To find the dative case in a sentence, we ask two core questions. For people and animals, we ask **«Кому?»** *(To whom?)*. For objects, concepts, or abstract ideas, we ask **«Чому?»** *(To what?)*. 

> Читаємо українською:
> Я купую новий подарунок. *(I am buying a new gift.)*
> Кому я купую подарунок? *(To whom am I buying a gift?)*
> Я купую подарунок мамі. *(I am buying a gift for mom.)*
> Я даю холодну воду. *(I am giving cold water.)*
> Чому я даю воду? *(To what am I giving water?)*
> Я даю воду дереву. *(I am giving water to the tree.)*

Let us look closer at the concept of the indirect object. In a standard sentence, the Nominative case acts as the doer of the action, while the Accusative case is the direct object that is being handled, moved, or affected. The Dative case steps in as the indirect object—the person who benefits from the action, receives the item, or gets the information. It is the target of your generosity or your words.

Think of a simple, foundational interaction: «Я даю книгу тобі» *(I give the book to you)*. Here, **«я»** *(I)* is the active doer in the Nominative case. The word **«книгу»** *(the book)* is the direct object being physically moved, so it takes the Accusative case. Finally, the word **«тобі»** *(to you)* is the ultimate recipient, taking the Dative case. The dative always marks the end destination of the giving or telling process. Understanding this relationship is the key to mastering Ukrainian sentence structure.

> Читаємо українською:
> Брат зараз читає казку. *(The brother is reading a fairytale now.)*
> Брат читає казку малій сестрі. *(The brother is reading a fairytale to the little sister.)*
> Вчитель добре пояснює правило. *(The teacher explains the rule well.)*
> Вчитель пояснює правило новому студенту. *(The teacher explains the rule to the new student.)*

To start using this case immediately, you need a "Starter Kit" of verbs that naturally trigger the dative. Focus on these high-frequency verbs of communication and transfer. The verb **дарувати** *(to gift)* is essential for holidays. The verbs **казати** *(to say)* and **говорити** *(to speak/tell)* introduce shared information. The verb **писати** *(to write)* is used for messages, and **допомагати** *(to help)* shows who receives assistance.

Whenever you use these verbs, the person receiving the action must take the dative form. 

> Читаємо українською:
> Я даю тобі синю ручку. *(I am giving you a blue pen.)*
> Він часто дарує мені квіти. *(He often gifts me flowers.)*
> Вона завжди каже йому правду. *(She always tells him the truth.)*
> Ми сьогодні пишемо вам довгого листа. *(We are writing a long letter to you today.)*
> Вони із радістю допомагають нам. *(They happily help us.)*
> Вчитель пояснює їм нове правило. *(The teacher explains the new rule to them.)*

Let us see how these forms work in a natural setting. Imagine a family gathering where a birthday is being celebrated, and the host is enthusiastically distributing gifts to everyone in the room. This scene relies heavily on personal pronouns in their dative forms.

> — **Іменинник:** Цей великий пакунок — це мій подарунок! *(This big package is my gift!)*
> — **Мама:** Кому цей подарунок? *(To whom is this gift?)*
> — **Іменинник:** **Мені** — цікаву книгу. **Тобі** — солодкий шоколад. *(For me — an interesting book. For you — sweet chocolate.)*
> — **Брат:** А що є для тата? *(And what is there for dad?)*
> — **Іменинник:** **Йому** — теплий зимовий шарф. *(For him — a warm winter scarf.)*
> — **Мама:** А нашій бабусі? *(And for our grandma?)*
> — **Іменинник:** **Їй** — дуже гарні квіти. *(For her — very beautiful flowers.)*
> — **Брат:** А що ми всі будемо їсти? *(And what will we all eat?)*
> — **Іменинник:** **Нам** — великий і смачний торт! *(For us — a big and tasty cake!)*

<!-- INJECT_ACTIVITY: match-up-match-nominative-pronoun-to-its-dative-form -->


## Особові займенники у давальному відмінку (Personal Pronouns in the Dative)

Now that we know the basic function of the dative case, we must learn how it changes our most common words: personal pronouns. In Ukrainian, the pronouns for the first and second person singular undergo a complete transformation. This is called a suppletive form, meaning the base word changes entirely. The pronoun **«я»** *(I)* becomes **«мені»** *(to me)*. The pronoun **«ти»** *(you, informal)* becomes **«тобі»** *(to you)*. You must memorize these two words as a set, because they are the absolute core of daily Ukrainian conversation. Many English speakers try to literally translate phrases like "give me" by using the nominative form, saying incorrect things like "Дай я книгу." This is a major error. You must always use the dative form when you are the recipient. The verb gives the action, and the dative pronoun catches it.

> Читаємо українською:
> Скажи мені правду зараз. *(Tell me the truth now.)*
> Я даю тобі цей новий телефон. *(I am giving you this new phone.)*
> Ця синя сорочка дуже тобі пасує. *(This blue shirt suits you very much.)*
> Мама купує мені смачний торт. *(Mom is buying me a tasty cake.)*
> Чи можу я тобі допомогти сьогодні? *(Can I help you today?)*
> Мені треба купити свіжий хліб. *(I need to buy fresh bread.)*

Next, we look at the third person singular pronouns. These forms are very distinct and help us talk about giving things to other people. The masculine pronoun **«він»** *(he)* and the neuter pronoun **«воно»** *(it)* share the exact same dative form: **«йому»** *(to him / to it)*. The feminine pronoun **«вона»** *(she)* has its own unique form: **«їй»** *(to her)*. Pay special attention to the spelling and pronunciation of «їй». It consists of the letter 'ї' followed by 'й', creating a soft, gliding sound. You will use these pronouns constantly when talking about friends, family members, or colleagues.

> Читаємо українською:
> Я телефоную йому пізно ввечері. *(I am calling him late in the evening.)*
> Ми даруємо їй красиві весняні квіти. *(We are gifting her beautiful spring flowers.)*
> Вчитель дає йому нове цікаве завдання. *(The teacher gives him a new interesting task.)*
> Брат часто пише їй довгі повідомлення. *(The brother often writes her long messages.)*
> Чи ти знаєш, що їй подобається? *(Do you know what she likes?)*
> Ми купили йому чорний зимовий шарф. *(We bought him a black winter scarf.)*

The plural forms of personal pronouns in the dative case are thankfully much simpler and feel more symmetrical to learners. The pronoun **«ми»** *(we)* becomes **«нам»** *(to us)*. The formal or plural pronoun **«ви»** *(you)* becomes **«вам»** *(to you)*. Finally, the third person plural pronoun **«вони»** *(they)* becomes **«їм»** *(to them)*. Notice how these endings share a similar 'м' sound, making them easier to group together in your memory. These plural forms are essential for addressing groups or talking about collective experiences.

> Читаємо українською:
> Наш новий вчитель добре пояснює нам правило. *(Our new teacher explains the rule to us well.)*
> Я щиро дякую вам за вашу допомогу. *(I sincerely thank you for your help.)*
> Нам потрібно їм швидко зателефонувати. *(We need to call them quickly.)*
> Батьки дають нам гроші на нову квартиру. *(Parents give us money for a new apartment.)*
> Директор розповідає їм про важливий проєкт. *(The director tells them about the important project.)*
> Ми радіємо вам і вашим добрим новинам. *(We are happy for you and your good news.)*

When learning the Genitive and Accusative cases, you likely learned that third-person pronouns gain an initial letter 'н' after prepositions (for example, «до нього» or «у неї»). However, the Dative case behaves differently. First, the dative is very rarely used with prepositions in basic speech. When it is used with rare prepositions like **«завдяки»** *(thanks to)*, the pronoun generally does NOT gain an 'н'. Therefore, you will almost always use the standard forms «йому», «їй», and «їм» for the recipient. Do not over-generalize the rule from other cases. Keep it simple: when you give something, tell something, or help someone, use the base dative forms without the extra letter.

> Читаємо українською:
> Завдяки йому ми маємо ці квитки. *(Thanks to him, we have these tickets.)*
> Я розказую їй цю стару історію. *(I am telling her this old story.)*
> Ми допомагаємо їм робити домашнє завдання. *(We are helping them do their homework.)*
> Завдяки їй наш проєкт працює добре. *(Thanks to her, our project works well.)*
> Дай йому трохи часу на відпочинок. *(Give him a little time for rest.)*
> Напиши їм адресу нашого нового офісу. *(Write them the address of our new office.)*

Let us see how these pronouns naturally shift during a conversation. Read this dialogue where two friends are planning a surprise and discussing who gets to know the secret. Pay attention to how the pronouns change based on who is receiving the information.

> — **Максим:** Я маю великий секрет. Я скажу йому цей секрет сьогодні. *(I have a big secret. I will tell him this secret today.)*
> — **Олена:** Це дуже цікаво! А нам ти скажеш? *(This is very interesting! And will you tell us?)*
> — **Максим:** Так, вам я скажу трохи пізніше. *(Yes, I will tell you a little later.)*
> — **Олена:** А що ми скажемо нашим друзям? *(And what will we tell our friends?)*
> — **Максим:** Їм ми скажемо все завтра вранці. *(We will tell them everything tomorrow morning.)*
> — **Олена:** Добре, а їй ми нічого не скажемо? *(Good, and will we not tell her anything?)*
> — **Максим:** Ні, їй це буде великий сюрприз! *(No, for her it will be a big surprise!)*

<!-- INJECT_ACTIVITY: fill-in-dative-pronouns -->


## Мені холодно: Безособові конструкції (Impersonal Constructions)

In English, you say "I am cold" or "She is sad" using the subject "I" or "She." In Ukrainian, many physical and emotional states are not something you "are," but something that "is to you." These are called impersonal constructions because there is no traditional subject doing an action. The person experiencing the feeling is the "logical subject" in the Dative case. Compare a permanent description of identity with a temporary feeling. When you say **«Я щаслива»** *(I am happy)*, you describe your overall state. When you say **«Мені весело»** *(I feel joyful)*, you describe a current feeling happening to you right now. 

> Читаємо українською:
> Я сьогодні дуже щаслива дівчина. *(I am very happy today.)*
> Зараз мені дуже весело на святі. *(I feel very joyful at the party.)*
> Він завжди спокійний і серйозний хлопець. *(He is a calm, serious guy.)*
> Сьогодні йому дуже сумно без друзів. *(He feels sad without friends today.)*
> Вона втомлена після важкого робочого дня. *(She is tired after a hard workday.)*
> Їй важко працювати так багато годин. *(It is hard for her to work long hours.)*
> Ми готові починати новий великий проєкт. *(We are ready to start a big project.)*
> Нам страшно дивитися цей новий фільм. *(It is scary for us to watch this movie.)*

We build these sentences using state adverbs that describe a physical sensation or emotional feeling. You will notice that they almost always end in the neutral letter **-о**. Common examples include **«холодно»** *(cold)*, **«тепло»** *(warm)*, **«сумно»** *(sad)*, **«весело»** *(joyful)*, **«приємно»** *(pleasant)*, and **«цікаво»** *(interesting)*. To say "I am cold," you literally say "To me it is cold": **«Мені холодно»**. To ask if a friend is interested, you ask: **«Тобі цікаво?»**. You do not need a verb like "is" in the present tense. Just pair the Dative pronoun directly with the adverb.

> Читаємо українською:
> Взимку мені завжди дуже холодно. *(In winter I am always very cold.)*
> Тобі цікаво читати цю нову книгу? *(Is it interesting for you to read this book?)*
> Нам дуже приємно вас тут бачити. *(It is very pleasant for us to see you.)*
> Їй весело грати з великим собакою. *(It is joyful for her to play with the dog.)*
> Йому тепло у цій новій куртці. *(He is warm in this new jacket.)*
> Їм нудно сидіти вдома цілий день. *(It is boring for them to sit at home.)*
> Мені дуже соромно за цю велику помилку. *(I am very ashamed of this big mistake.)*
> Вам зручно сидіти на цьому старому кріслі? *(Is it comfortable for you to sit on this chair?)*

We also use the Dative case for modal adverbs expressing necessity, permission, or advice. The most important ones are **«треба»** or **«потрібно»** *(need)*, **«можна»** *(allowed / may)*, and **«варто»** *(should / worth doing)*. When you want to say "I need," you must literally say "To me it is necessary." You absolutely cannot use the word "I" (**я**) here. This is a common mistake for English speakers. Simply add an infinitive verb after these modal adverbs to show what action is needed or allowed.

:::tip Запам'ятайте (Remember)
**Я треба йти.** ❌
**Мені треба йти.** ✅ *(I need to go.)*
:::

> Читаємо українською:
> Мені треба йти додому прямо зараз. *(I need to go home right now.)*
> Тобі потрібно купити новий мобільний телефон. *(You need to buy a new mobile phone.)*
> Вам можна тут сидіти і читати. *(You are allowed to sit here and read.)*
> Йому варто добре відпочити після роботи. *(He should rest well after work.)*
> Їй не можна пити чорну каву. *(She is not allowed to drink black coffee.)*
> Нам треба багато працювати сьогодні ввечері. *(We need to work a lot tonight.)*
> Їм потрібно швидко написати цей довгий лист. *(They need to write this long letter quickly.)*
> Мені варто запитати про це нашого вчителя. *(I should ask our teacher about this.)*

Let us look at how these impersonal constructions sound in a real conversation. Read this dialogue between two friends sitting at a cafe. They discuss their comfort and what they need to order.

> — **Анна:** Тобі тут тепло біля вікна? *(Are you warm near the window?)*
> — **Богдан:** Так, мені приємно тут сидіти. *(Yes, it is pleasant to sit here.)*
> — **Анна:** Мені цікаво, що ти сьогодні замовиш. *(I wonder what you will order today.)*
> — **Богдан:** Мені потрібно випити велику чашку кави. *(I need to drink a big cup of coffee.)*
> — **Анна:** Чому тобі хочеться саме чорної кави? *(Why exactly do you want black coffee?)*
> — **Богдан:** Бо мені сумно без неї зранку. А тобі що треба? *(Because I feel sad without it in the morning. What do you need?)*
> — **Анна:** Мені варто випити гарячий зелений чай. Мені трохи холодно. *(I should drink hot green tea. I am a little cold.)*
> — **Богдан:** Тобі можна взяти ще теплий десерт. *(You can also take a warm dessert.)*
> — **Анна:** Добре, зараз нам можна спокійно відпочити. *(Good, we are allowed to rest calmly now.)*

<!-- INJECT_ACTIVITY: true-false-impersonal -->


## Давальний чи знахідний? (Dative or Accusative?)

Learning to choose between the Dative and Accusative cases is a common challenge. In English, we simply use "you" or "her" for both direct objects and recipients. In Ukrainian, the choice depends entirely on the verb's logic of interaction. Let us look at some minimal pairs where the only difference is the pronoun case.

> Читаємо українською:
> Я бачу тебе щодня. *(I see you every day.)*
> Я кажу тобі правду. *(I tell you the truth.)*
> Він добре знає її. *(He knows her well.)*
> Він часто дзвонить їй. *(He often calls her.)*
> Ми слухаємо вас уважно. *(We listen to you carefully.)*
> Ми даємо вам роботу. *(We give you work.)*

In the first sentence of each pair, the action directly affects the person. You see them, you know them, you listen to them. This requires the Accusative case (**тебе**, **її**, **вас**). In the second sentence, the person is the recipient of the action. You tell something *to* them, call *to* them, give something *to* them. This requires the Dative case (**тобі**, **їй**, **вам**).

How can you quickly decide which case to use? Use this simple strategy: if the action is directed *at* the person or given *to* them, use the Dative case. If the action uses, sees, or directly targets the person as an object, use the Accusative case.

:::tip Важливе правило (Important rule)
**Кому?** *(To whom?)* → Давальний відмінок: **мені, тобі, йому, їй, нам, вам, їм**.
**Кого?** *(Whom?)* → Знахідний відмінок: **мене, тебе, його, її, нас, вас, їх**.
:::

However, you must be careful with False Friends. These are verbs that work differently in English and Ukrainian. A classic example is the verb **допомагати** *(to help)*. In English, you help someone directly. In Ukrainian, you literally give help *to* someone, so this verb always requires the Dative case. 

Other common false friends include **дякувати** *(to thank)* and **заважати** *(to bother / to disturb)*. You must say «дякую тобі» *(I thank to you)*, not «дякую тебе» ❌. You also say «ти заважаєш мені» *(you are bothering to me)*.

> Читаємо українською:
> Я завжди допомагаю моїй сестрі. *(I always help my sister.)*
> Вона допомагає мені робити домашнє завдання. *(She helps me do my homework.)*
> Чи можу я допомогти вам сьогодні? *(Can I help you today?)*
> Брат постійно заважає мені. *(My brother constantly bothers me.)*
> Ми хочемо подякувати їм за подарунок. *(We want to thank them for the gift.)*

Let us see how native speakers switch between these cases naturally in a conversation.

> — **Олег:** Привіт! Я бачу тебе біля метро. *(Hi! I see you near the subway.)*
> — **Ірина:** Привіт! А я саме телефоную тобі. *(Hi! And I am calling you right now.)*
> — **Олег:** Я хочу щиро подякувати тобі за допомогу. *(I want to sincerely thank you for the help.)*
> — **Ірина:** Будь ласка. Я завжди рада допомогти тобі. *(You are welcome. I am always glad to help you.)*
> — **Олег:** Ти добре знаєш мого брата? Він хвалив тебе. *(Do you know my brother well? He praised you.)*
> — **Ірина:** Так, я чудово знаю його. Він теж допомагає мені. *(Yes, I know him perfectly. He also helps me.)*
> — **Олег:** Тоді я дарую вам обом квитки в театр. *(Then I give you both tickets to the theater.)*
> — **Ірина:** О, ми дуже любимо тебе за це! *(Oh, we love you very much for this!)*

<!-- INJECT_ACTIVITY: quiz-case-choice --> [quiz, Choose between Dative and Accusative pronoun forms (e.g., тобі vs тебе) based on the verb in the sentence, 8 items]


## Підсумок (Summary)

Let us review the Dative case of personal pronouns. The paradigm changes significantly from the Nominative case. 

> Читаємо українською:
> **я** → **мені** *(to me)*
> **ти** → **тобі** *(to you)*
> **він / воно** → **йому** *(to him / to it)*
> **вона** → **їй** *(to her)*
> **ми** → **нам** *(to us)*
> **ви** → **вам** *(to you)*
> **вони** → **їм** *(to them)*

We use these forms for two main functions. The first function is the recipient of an action, answering the question **кому?** *(to whom?)*. 

> Читаємо українською:
> Дай **мені** цю книгу. *(Give me this book.)*
> Я кажу **тобі** правду. *(I am telling you the truth.)*

The second function is the logical subject in impersonal sentences, describing states, feelings, and needs.

> Читаємо українською:
> **Мені** холодно. *(I am cold.)*
> **Тобі** потрібно йти. *(You need to go.)*

Before we finish, do a quick self-check. Can you say "To her it is interesting"? It is **«Їй цікаво»**. Do you remember the Dative form of **ми**? It is **нам**. Always ask yourself who receives the action or who feels the state, and you will choose the right pronoun naturally!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-pronouns
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

**Level: A2 (Module 17/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

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
