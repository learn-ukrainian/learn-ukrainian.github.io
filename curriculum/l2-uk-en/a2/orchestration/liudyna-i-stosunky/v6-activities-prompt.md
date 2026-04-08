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

When you meet someone new, talk about a friend, or look at family photos, you often need to describe people. In Ukrainian, the verb to describe is **описувати** (to describe), and the noun for appearance is **зовнішність** (appearance). To ask what someone looks like, we use the question: «Як він виглядає?» (What does he look like?) or «Як вона виглядає?» (What does she look like?).

Let's look at some examples of how we ask and answer this question in everyday life. 

*   Як виглядає твій новий колега? *(What does your new colleague look like?)*
*   Він дуже симпатичний. *(He is very handsome.)*
*   Як вона виглядає? *(What does she look like?)*
*   Вона має гарну зовнішність. *(She has a beautiful appearance.)*
*   Ти можеш описати цю людину? *(Can you describe this person?)*
*   Так, звичайно. *(Yes, of course.)*

Let's start with basic physical traits like height and build. Ukrainian uses contrast pairs to make descriptions easy to remember. We use the adjectives **високий** (tall) and **низький** (short) to talk about height. For build, we use **худий** (thin) and **повний** (stout/full). When we talk about someone's age, we use **молодий** (young), **старий** (old), and the phrase **середнього віку** (middle-aged). 

Here are some natural sentences using these words:

*   Мій брат дуже високий, а сестра — низька. *(My brother is very tall, and my sister is short.)*
*   Цей чоловік худий, а його друг — повний. *(This man is thin, and his friend is stout.)*
*   Вона ще молода, їй тільки двадцять років. *(She is still young, she is only twenty years old.)*
*   Наш сусід — чоловік середнього віку. *(Our neighbor is a middle-aged man.)*
*   Мій дідусь уже старий, але дуже активний. *(My grandfather is already old, but very active.)*

Now let's focus on the face and eyes. There are two common ways to describe eyes in Ukrainian. You can use the construction «У нього/неї...» (He/she has...) or form a compound adjective like **кароока** (brown-eyed). For example, «У неї карі очі» (She has brown eyes) and «Вона кароока» mean the exact same thing. Common eye colors include **сині** (dark blue), **блакитні** (light blue), **зелені** (green), and **сірі** (grey). We can also describe facial features like a **кругле обличчя** (round face) or a **прямий ніс** (straight nose).

*   У неї великі зелені очі. *(She has big green eyes.)*
*   Цей хлопчик блакитноокий. *(This boy is blue-eyed.)*
*   Мій батько має карі очі та прямий ніс. *(My father has brown eyes and a straight nose.)*
*   У цієї дівчини кругле обличчя і сірі очі. *(This girl has a round face and grey eyes.)*
*   Вона має дуже гарне обличчя. *(She has a very beautiful face.)*

When describing hair, we look at color, length, and style. In Ukrainian, hair color is often described as **темне** (dark), **світле** (light/fair), **русяве** (light brown), **руде** (red), or **сиве** (grey). For length and style, we use **коротке** (short), **довге** (long), **хвилясте** (wavy), and **пряме** (straight). If you want to compliment someone's haircut or hairstyle, use the word **зачіска** (haircut/hairstyle).

*   У неї довге хвилясте волосся. *(She has long wavy hair.)*
*   Він має коротке темне волосся. *(He has short dark hair.)*
*   Моя мама має світле пряме волосся. *(My mom has light straight hair.)*
*   У нього дуже модна зачіска. *(He has a very trendy haircut.)*
*   Цей чоловік має сиве волосся. *(This man has grey hair.)*
*   Її руде волосся таке яскраве! *(Her red hair is so bright!)*

### Читаємо українською (Reading Practice)

Let's see how these words are used in a real conversation. Read this dialogue between two friends looking at photos on a phone.

> — **Олена:** Дивись, це моя сестра Ганна. *(Look, this is my sister Hanna.)*
> — **Марія:** Яка вона гарна! Вона дуже висока. *(How beautiful she is! She is very tall.)*
> — **Олена:** Так, висока і струнка. Вона має довге русяве волосся і великі зелені очі. *(Yes, tall and slim. She has long light brown hair and big green eyes.)*
> — **Марія:** Вона схожа на тебе. А хто це поруч із нею? *(She looks like you. And who is this next to her?)*
> — **Олена:** А це наш сусід, пан Іван. *(And this is our neighbor, Mr. Ivan.)*
> — **Марія:** Він виглядає дуже серйозно. *(He looks very serious.)*
> — **Олена:** Він уже старий, але дуже ставний чоловік. Він завжди має ідеальну зачіску. *(He is already old, but a very stately man. He always has a perfect haircut.)*


## Характер: яка вона людина? (Character: What Kind of Person Is She?)

When we want to describe someone's inner world, we talk about their **характер** (character or personality). While appearance is what we see first, character is what makes a person who they are. In Ukrainian, when we ask «Яка він людина?» (What kind of person is he?), we expect to hear about personality traits. Let's start with some of the most common positive traits. A person who is open and genuine is **щирий** (sincere). Someone who is always glad to see you and treats you warmly is **привітний** (friendly/welcoming). A person who does good things for others is **добрий** (kind), and someone who is always ready to listen and help is **чуйний** (responsive/empathetic). You can use these adjectives directly or with the word **людина** (person).

* Мій новий знайомий — дуже щира людина. *(My new acquaintance is a very sincere person.)*
* Вона завжди привітна з усіма. *(She is always friendly with everyone.)*
* Наш сусід дуже добрий і чуйний. *(Our neighbor is very kind and responsive.)*
* Це щирий і веселий хлопець. *(This is a sincere and cheerful guy.)*
* Яка вона людина? Вона привітна і добра. *(What kind of person is she? She is friendly and kind.)*

When describing how people approach their work, studies, or daily tasks, we use a different set of adjectives. A person who loves to work and does it well is **працьовитий** (hardworking). Someone you can always rely on to do what they promised is **відповідальний** (responsible). If a person can calmly wait or deal with difficulties without getting angry, they are **терплячий** (patient). And someone who doesn't give up until they reach their goal is **наполегливий** (persistent/determined). These words are very useful when talking about colleagues, classmates, or family members who help you.

* Моя мама — дуже працьовита жінка, вона ніколи не сидить без діла. *(My mom is a very hardworking woman, she never sits idle.)*
* Наш новий колега дуже відповідальний. *(Our new colleague is very responsible.)*
* Вчитель має бути терплячим. *(A teacher must be patient.)*
* Цей студент наполегливий, тому він має гарні результати. *(This student is determined, so he has good results.)*
* Вона працьовита і завжди виконує свої обіцянки. *(She is hardworking and always keeps her promises.)*
* Мій брат не дуже терплячий, він хоче все відразу. *(My brother is not very patient, he wants everything at once.)*

Of course, people are complex, and we don't only have positive traits. Sometimes people don't want to work, then we say they are **ледачий** (lazy). A person who rarely smiles and focuses on serious matters is **серйозний** (serious). Someone who doesn't talk much is **тихий** (quiet). A very interesting word in Ukrainian is **впертий** (stubborn/persistent). While it can mean someone who refuses to listen to others, Ukrainians often use «впертий» in a positive way to describe someone who is highly principled and refuses to give up on their goals.

* Цей кіт такий ледачий, він спить цілий день. *(This cat is so lazy, he sleeps all day.)*
* Мій батько дуже серйозний чоловік. *(My father is a very serious man.)*
* Моя сестра тиха, але дуже розумна. *(My sister is quiet, but very smart.)*
* Він впертий, тому обов'язково знайде правильне рішення. *(He is stubborn, so he will definitely find the right solution.)*
* Іноді бути впертим — це добре. *(Sometimes being stubborn is a good thing.)*

When we describe a person's character, we often talk about what they *usually* do. Because personality traits are constant, we use imperfective verbs for these habitual actions. For example, to prove someone is kind, you might say «Він завжди допомагає» (He always helps). However, if you want to give a specific example of their character from the past, an action that happened once and was completed, you use a perfective verb. You might say «Учора він мені допоміг» (Yesterday he helped me). This contrast is very natural in Ukrainian storytelling.

* Цей хлопець добрий, він завжди допомагає людям. *(This guy is kind, he always helps people.)*
* Учора він допоміг мені з валізою. *(Yesterday he helped me with my suitcase.)*
* Вона відповідальна і завжди робить домашнє завдання. *(She is responsible and always does her homework.)*
* Сьогодні вона теж зробила всі вправи. *(Today she also did all the exercises.)*
* Мій колега працьовитий, він постійно працює. *(My colleague is hardworking, he constantly works.)*
* Учора він попрацював дуже добре. *(Yesterday he worked very well.)*

### Читаємо українською (Reading Practice)

Let's see how these words are used when discussing people at work. Read this dialogue between a new employee and an experienced colleague.

> — **Антон:** Добрий день! Я Антон, новий дизайнер. *(Good day! I am Anton, the new designer.)*
> — **Марина:** Вітаю, Антоне! Я Марина. Рада знайомству. *(Greetings, Anton! I am Maryna. Nice to meet you.)*
> — **Антон:** Марино, розкажіть, будь ласка, яка наша керівниця? *(Maryna, please tell me, what kind of person is our female manager?)*
> — **Марина:** Вона дуже відповідальна і справедлива, але іноді буває дуже серйозна. *(She is very responsible and fair, but sometimes she is very serious.)*
> — **Антон:** Зрозуміло. А колеги? Які вони? *(Understood. And the colleagues? What are they like?)*
> — **Марина:** Усі привітні і добрі. Особливо Максим, він завжди допомагає новим працівникам. *(Everyone is friendly and kind. Especially Maksym, he always helps new employees.)*
> — **Антон:** Це чудово! Я трохи хвилювався. *(That's great! I was a little worried.)*
> — **Марина:** Не хвилюйся, у нас дуже хороший колектив. *(Don't worry, we have a very good team.)*

<!-- INJECT_ACTIVITY: match-character-traits -->
<!-- INJECT_ACTIVITY: quiz-character-choice -->


## Люди навколо нас: родичі, друзі, знайомі (People Around Us)

In Ukrainian culture, we are very specific about how we name our relationships. In English, you might call someone a "friend" even if you just met them at a party, but in Ukrainian, we are more careful with our words. Not everyone we know is a **друг** (friend — male) or **подруга** (friend — female). A true friend is someone very close to you, someone you trust completely. For people you know from school, work, or sports, we often use the word **товариш** (comrade / buddy). If you just know someone's name and say hello on the street, that person is a **знайомий** (acquaintance — male) or **знайома** (acquaintance — female). 

* Це мій найкращий друг, **ми дружимо давно**. *(This is my best friend, we have been friends for a long time.)*
* Олена — моя хороша подруга. *(Olena is my good friend.)*
* Він не мій друг, він просто знайомий. *(He is not my friend, he is just an acquaintance.)*
* Ми з Антоном старі товариші. *(Anton and I are old buddies.)*
* У мене є багато знайомих у цьому місті. *(I have many acquaintances in this city.)*

Another very important group of people in our daily lives are our neighbors. In Ukrainian, a male neighbor is a **сусід**, and a female neighbor is a **сусідка**. Because many Ukrainians live in large apartment buildings, neighbors often know each other well and form a small community. They might borrow some sugar, watch your pet when you are away, or just chat near the entrance. A good neighbor is someone who is friendly and always ready to help.

* **Мій сусід живе поруч**. *(My neighbor lives nearby.)*
* Моя сусідка дуже привітна жінка. *(My neighbor is a very friendly woman.)*
* Наші сусіди часто допомагають нам. *(Our neighbors often help us.)*
* Цей молодий сусід завжди вітається. *(This young neighbor always says hello.)*
* Ми знаємо всіх сусідів у нашому будинку. *(We know all the neighbors in our building.)*

Of course, the closest people are our family. You already know words like mother, father, brother, and sister. The general word for a family member is **родич** (relative). Let's expand our family tree a bit. A male cousin is a **двоюрідний брат**, and a female cousin is a **двоюрідна сестра**. We also have **дядько** (uncle) and **тітка** (aunt). In Ukrainian families, cousins are often as close as siblings. Now, we can use the adjectives we learned earlier to describe them completely.

* Мій дядько — високий і дуже серйозний чоловік. *(My uncle is a tall and very serious man.)*
* Моя тітка має світле волосся, вона дуже весела. *(My aunt has light hair, she is very cheerful.)*
* Це мій двоюрідний брат, він надзвичайно працьовитий. *(This is my cousin, he is extremely hardworking.)*
* У мене є багато родичів в Україні. *(I have many relatives in Ukraine.)*
* Моя двоюрідна сестра — тиха, але дуже розумна людина. *(My cousin is a quiet, but very smart person.)*

How do we act toward these people? To describe relationships, we use specific verbs of interaction. When we talk about helping or trusting someone, Ukrainian grammar requires the Dative case for the person receiving the action. For example, we use **допомагати** (to help) and **довіряти** (to trust) with the Dative. If we want to say we respect someone, we use the verb **поважати** (to respect) with the Accusative case. You will learn the full Dative case rules later, but for now, remember these common pronoun patterns: **мені** (to me) and **нам** (to us).

* **Вона мені довіряє** свої таємниці. *(She trusts me with her secrets.)*
* **Він нам завжди допомагає** в саду. *(He always helps us in the garden.)*
* Я довіряю своєму другові. *(I trust my friend.)*
* Ми дуже поважаємо нашого керівника. *(We highly respect our manager.)*
* Хороший сусід завжди допомагає сусідам. *(A good neighbor always helps neighbors.)*
* Батьки поважають мій вибір. *(Parents respect my choice.)*

### Читаємо українською (Reading Practice)

Read this short dialogue where two friends look at some photos and discuss the people in them. Pay attention to how they describe relationships and character traits.

> — **Оксана:** Хто це на фотографії? Це твій родич? *(Who is this in the photograph? Is this your relative?)*
> — **Тарас:** Ні, це мій сусід і старий товариш, Ігор. Ми дружимо давно. *(No, this is my neighbor and old buddy, Ihor. We have been friends for a long time.)*
> — **Оксана:** Який він? Він виглядає дуже серйозним. *(What is he like? He looks very serious.)*
> — **Тарас:** Так, він серйозний, але дуже чуйний і добрий. Він завжди допомагає мені. *(Yes, he is serious, but very responsive and kind. He always helps me.)*
> — **Оксана:** Це чудово, коли є такі знайомі. А поруч з ним — його сестра? *(It is great when there are such acquaintances. And next to him — is that his sister?)*
> — **Тарас:** Ні, це його двоюрідна сестра, Марія. Я їй дуже довіряю. *(No, that is his cousin, Mariia. I trust her a lot.)*
> — **Оксана:** Вона дуже симпатична і має гарні карі очі. *(She is very cute and has beautiful brown eyes.)*
> — **Тарас:** І вона дуже працьовита. Ми всі її поважаємо. *(And she is very hardworking. We all respect her.)*

<!-- INJECT_ACTIVITY: fill-in-adjective-agreement -->
<!-- INJECT_ACTIVITY: group-sort-traits -->


## Описуємо людину цілком (Describing a Person Fully)

To describe a person fully, we usually combine three details: who they are to us, what they look like, and what kind of person they are. Here is a complete profile.

* Це мій найкращий друг Андрій. *(This is my best friend Andrii.)*
* Він високий і спортивний хлопець із темним волоссям. *(He is a tall and athletic guy with dark hair.)*
* Андрій дуже веселий і завжди допомагає друзям. *(Andrii is very cheerful and always helps friends.)*

This structure gives a clear picture of the person. You start with the relationship, add physical details, and finish with their personality.

### Порівнюємо різних людей (Comparing Different People)

When we describe people we know, we often contrast their traits. Notice how we combine physical descriptions with character adjectives in these examples.

* Моя працьовита колега Олена — невисока жінка. *(My hardworking colleague Olena is a short woman.)*
* Вона має коротке світле волосся і карі очі. *(She has short light hair and brown eyes.)*
* Олена дуже серйозна і відповідальна. *(Olena is very serious and responsible.)*

Now we can describe someone with a completely different energy:

* А це моя весела сусідка Марія. *(And this is my cheerful neighbor Mariia.)*
* Вона повна і має довге русяве волосся. *(She is plump and has long dark blond hair.)*
* Марія — дуже щира і привітна людина. *(Mariia is a very sincere and welcoming person.)*

Both descriptions follow our pattern but paint completely different pictures.

### Читаємо українською (Reading Practice)

Read this short conversation where two friends look at a photo. Notice how they blend physical appearance with character traits.

> — **Тарас:** Хто це на фото? *(Who is this in the photo?)*
> — **Оксана:** Це мій дідусь Іван. *(This is my grandfather Ivan.)*
> — **Тарас:** Він дуже високий і сильний чоловік. *(He is a very tall and strong man.)*
> — **Оксана:** Так, він старий, але має добрі блакитні очі. *(Yes, he is old, but he has kind blue eyes.)*
> — **Тарас:** Який у нього характер? *(What is his character like?)*
> — **Оксана:** Мій дідусь — надзвичайно розумна і спокійна людина. Я його дуже поважаю, бо він завжди мені допомагає. *(My grandfather is an extremely smart and calm person. I respect him a lot because he always helps me.)*

:::tip Культурний контекст (Cultural Note)
In Ukrainian culture, we value a person's inner qualities more than their physical appearance. Calling someone **красива людина** *(a beautiful person)* usually refers to their looks. However, calling someone **гарна людина** *(a good person)* or **добра людина** *(a kind person)* is a much deeper compliment. It means they have a good heart and treat others well. When Ukrainians say «Він справді добра людина» *(He is a truly kind person)*, it is the highest praise you can give.
:::


## Підсумок — Summary

We have learned how to fully describe the people in our lives. Now you can talk about someone's appearance, whether they are **високий** *(tall)* or have **карі очі** *(brown eyes)*. You also know how to describe their inner qualities, such as being **щирий** *(sincere)* or **працьовитий** *(hardworking)*. Finally, you can explain who this person is to you: a **знайомий** *(acquaintance)*, a **родич** *(relative)*, or a **сусід** *(neighbor)*.

Let’s look at one final example that brings everything together:

* Це мій новий знайомий Віктор. *(This is my new acquaintance Viktor.)*
* Він високий чоловік із темним волоссям. *(He is a tall man with dark hair.)*
* Віктор — дуже привітна і розумна людина. *(Viktor is a very welcoming and smart person.)*
* Він завжди допомагає іншим. *(He always helps others.)*

Now it is your turn to practice. Try to answer these questions in Ukrainian:

1. **Як виглядає ваша найкраща подруга?** *(What does your best friend look like?)*
2. **Який характер у вашого сусіда?** *(What is your neighbor's character like?)*
3. **Яка ви людина — тиха чи весела?** *(What kind of person are you — quiet or cheerful?)*

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
