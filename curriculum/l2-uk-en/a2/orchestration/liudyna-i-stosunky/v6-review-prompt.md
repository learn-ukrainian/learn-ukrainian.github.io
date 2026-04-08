<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 4: Яка вона людина? Описуємо людей навколо нас (A2, A2.1 [Foundation and Aspect Introduction])
**Writer:** Gemini
**Word target:** 2000

## Plan (source of truth)

<plan_content>
module: a2-004
level: A2
sequence: 4
slug: liudyna-i-stosunky
version: '1.0'
title: Яка вона людина? Описуємо людей навколо нас
subtitle: Зовнішність, характер та стосунки — описуємо рідних, друзів і знайомих
focus: communication
pedagogy: PPP
phase: A2.1 [Foundation and Aspect Introduction]
word_target: 2000
objectives:
  - Learner can describe a person's appearance using basic adjectives and noun
    phrases (високий, темноволосий, з карими очима).
  - Learner can describe a person's character using personality adjectives
    (привітний, щирий, працьовитий, терплячий).
  - Learner can talk about relationships and people in their life (родич, сусід,
    колега, знайомий) using appropriate vocabulary.
  - Learner can recognize imperfective/perfective aspect in context when
    describing habitual vs. one-time actions of people they know.
dialogue_situations:
  - setting: 'Two friends looking at photos on a phone — describing family members
      and friends: Це моя сестра. Вона висока, темноволоса. Дуже весела і щира
      людина. А це мій сусід — він завжди допомагає (impf). Учора допоміг (pf)
      мені з валізою.'
    speakers:
      - Подруга 1
      - Подруга 2
    motivation: 'Natural context for describing people: appearance + character +
      aspect contrast (допомагає/допоміг)'
  - setting: 'New colleague at work — introducing yourself and asking about the
      team: Хто ваш керівник? Який він? — Він дуже відповідальний і справедливий.
      А колеги? — Усі привітні, особливо Оксана — вона завжди підказує (impf)
      новим працівникам.'
    speakers:
      - Новий працівник
      - Досвідчений колега
    motivation: 'Workplace introductions: describing colleagues'' character with
      imperfective habitual actions'
content_outline:
  - section: 'Зовнішність: як виглядає людина? (Appearance: What Does a Person Look Like?)'
    words: 500
    points:
      - 'Core appearance vocabulary: високий/низький, худий/повний, молодий/старий,
        темноволосий/світловолосий, кароокий/блакитноокий.'
      - 'Describing with мати and з + instrumental (preview): Вона має карі очі /
        Вона з карими очима. Note: instrumental is previewed here but formally
        taught later in A2.4.'
      - 'Practice describing people from photos or illustrations — building
        multi-adjective descriptions. Agreement: високий чоловік, висока жінка.'
  - section: 'Характер: яка вона людина? (Character: What Kind of Person Is She?)'
    words: 600
    points:
      - 'Positive traits: привітний, щирий, чуйний, добрий, веселий, розумний,
        працьовитий, терплячий, відповідальний, наполегливий.'
      - 'Challenging traits (not just "negative"): впертий, сумний, ледачий,
        серйозний, тихий. Ukrainian perspective — впертий can be positive
        (persistent, principled).'
      - 'Sentence patterns for describing character: Він дуже добрий. Вона —
        щира людина. Мій брат — працьовитий і відповідальний.'
      - 'Aspect integration: habitual character traits use imperfective — Він
        завжди допомагає (impf, always helps). One-time proof of character uses
        perfective — Він допоміг (pf) мені вчора (he helped me yesterday).'
  - section: 'Люди навколо нас: родичі, друзі, знайомі (People Around Us)'
    words: 550
    points:
      - 'Relationship vocabulary: родич, мати/батько, брат/сестра, дідусь/бабуся,
        дядько/тітка, друг/подруга, товариш, сусід/сусідка, колега, знайомий.'
      - 'Talking about relationships: Ми дружимо вже п''ять років. Вона — моя
        найкраща подруга. Він мій сусід — живе поруч.'
      - 'Describing how someone acts toward you: Вона мені довіряє. Він мене
        поважає. Вони нам допомагають.'
      - 'Natural conversation about people: responding to "А хто це?" and
        "Який він/яка вона?"'
  - section: 'Описуємо людину цілком (Describing a Person Fully)'
    words: 350
    points:
      - 'Combining appearance + character + relationship in a short paragraph:
        Мій друг Андрій — високий хлопець із карими очима. Він дуже веселий
        і щирий. Ми познайомилися в університеті.'
      - 'Practice: learner describes 2-3 people they know using the full
        pattern (who they are, what they look like, what their character is).'
      - 'Cultural note: Ukrainians often describe people through their actions
        and character more than physical appearance — "Добра людина" is a
        powerful compliment.'
vocabulary_hints:
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
  recommended:
    - впертий (stubborn, persistent)
    - чуйний (responsive, caring)
    - наполегливий (persistent, determined)
    - родич (relative)
    - знайомий (acquaintance)
activity_hints:
  - type: match-up
    focus: Match personality adjectives to their definitions or example situations
    items: 8
  - type: quiz
    focus: 'Choose the correct adjective to complete a person description (Він
      завжди допомагає — він дуже ___: щирий/ледачий/сумний)'
    items: 8
  - type: fill-in
    focus: Complete sentences describing people with the correct adjective form
      (agreement for gender)
    items: 8
  - type: group-sort
    focus: Sort personality adjectives into positive traits and challenging traits
    items: 8
references:
  - title: Заболотний Grade 5, §38-42
    notes: Іменник — людина, стосунки, описові тексти
  - title: Большакова Grade 1, §14-16
    notes: Опис людини, зовнішність і характер у дитячих текстах
  - title: 'ULP: How to Describe a Person in Ukrainian'
    url: https://www.ukrainianlessons.com/describing-people/
    notes: Appearance and personality vocabulary

</plan_content>

## Generated Content

<generated_module_content>
## Зовнішність: як виглядає людина? (Appearance: What Does a Person Look Like?)

When you meet someone new, talk about a friend, or look at family photos, you often need to describe people. In Ukrainian, the verb to describe is **описувати** (to describe), and the noun for appearance is **зовнішність** (appearance). To ask what someone looks like, we use the question: «Який він на вигляд?» (What does he look like?) or «Яка вона на вигляд?» (What does she look like?).

Let's look at some examples of how we ask and answer this question in everyday life. 

*   Який на вигляд твій новий колега? *(What does your new colleague look like?)*
*   Він дуже симпатичний. *(He is very handsome.)*
*   Яка вона на вигляд? *(What does she look like?)*
*   У неї гарна зовнішність. *(She has a beautiful appearance.)*
*   Ти можеш описати цю людину? *(Can you describe this person?)*
*   Так, звичайно. *(Yes, of course.)*

Let's start with basic physical traits like height and build. Ukrainian uses contrast pairs to make descriptions easy to remember. We use the adjectives **високий** (tall) and **низький** (short) to talk about height. For build, we use **худий** (thin) and **повний** (stout/full). When we talk about someone's age, we use **молодий** (young), **старий** (old), and the phrase **середнього віку** (middle-aged). 

Here are some natural sentences using these words:

*   Мій брат дуже високий, а сестра — низька. *(My brother is very tall, and my sister is short.)*
*   Цей чоловік худий, а його друг — повний. *(This man is thin, and his friend is stout.)*
*   Вона ще молода, їй тільки двадцять років. *(She is still young, she is only twenty years old.)*
*   Наш сусід — чоловік середнього віку. *(Our neighbor is a middle-aged man.)*
*   Мій дідусь уже старий, але дуже активний. *(My grandfather is already old, but very active.)*

Now let's focus on the face and eyes. There are two common ways to describe eyes in Ukrainian. You can use the construction «У нього/неї...» (He/she has...), use the preposition **з** + instrumental (with), or form a compound adjective like **кароока** (brown-eyed). For example, «У неї карі очі» (She has brown eyes), «Вона з карими очима» (She is with brown eyes), and «Вона кароока» mean the exact same thing. Common eye colors include **сині** (dark blue), **блакитні** (light blue), **зелені** (green), and **сірі** (grey). We can also describe facial features like a **кругле обличчя** (round face) or a **прямий ніс** (straight nose).

*   У неї великі зелені очі. *(She has big green eyes.)*
*   Цей хлопчик блакитноокий. *(This boy is blue-eyed.)*
*   Мій батько має карі очі та прямий ніс. *(My father has brown eyes and a straight nose.)*
*   У цієї дівчини кругле обличчя і сірі очі. *(This girl has a round face and grey eyes.)*
*   Вона має дуже гарне обличчя. *(She has a very beautiful face.)*

When describing hair, we look at color, length, and style. In Ukrainian, hair color is often described as **темне** (dark), **світле** (light/fair), **русяве** (light brown), **руде** (red), or **сиве** (grey). You can also use compound adjectives like **темноволосий** (dark-haired) and **світловолосий** (fair-haired). For length and style, we use **коротке** (short), **довге** (long), **хвилясте** (wavy), and **пряме** (straight). If you want to compliment someone's haircut or hairstyle, use the word **зачіска** (haircut/hairstyle).

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
> — **Марія:** Він має дуже серйозний вигляд. *(He looks very serious.)*
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
<!-- INJECT_ACTIVITY: group-sort-traits -->

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

How do we act toward these people? To describe relationships (**стосунки**), we use specific verbs of interaction. When we talk about helping or trusting someone, Ukrainian grammar requires the Dative case for the person receiving the action. For example, we use **допомагати** (to help) and **довіряти** (to trust) with the Dative. If we want to say we respect someone, we use the verb **поважати** (to respect) with the Accusative case. You will learn the full Dative case rules later, but for now, remember these common pronoun patterns: **мені** (to me) and **нам** (to us).

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
> — **Оксана:** Який він? Він має дуже серйозний вигляд. *(What is he like? He looks very serious.)*
> — **Тарас:** Так, він серйозний, але дуже чуйний і добрий. Він завжди допомагає мені. *(Yes, he is serious, but very responsive and kind. He always helps me.)*
> — **Оксана:** Це чудово, коли є такі знайомі. А поруч з ним — його сестра? *(It is great when there are such acquaintances. And next to him — is that his sister?)*
> — **Тарас:** Ні, це його двоюрідна сестра, Марія. Я їй дуже довіряю. *(No, that is his cousin, Mariia. I trust her a lot.)*
> — **Оксана:** Вона дуже симпатична і має гарні карі очі. *(She is very cute and has beautiful brown eyes.)*
> — **Тарас:** І вона дуже працьовита. Ми всі її поважаємо. *(And she is very hardworking. We all respect her.)*

<!-- INJECT_ACTIVITY: fill-in-adjective-agreement -->

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

1. **Яка на вигляд ваша найкраща подруга?** *(What does your best friend look like?)*
2. **Який характер у вашого сусіда?** *(What is your neighbor's character like?)*
3. **Яка ви людина — тиха чи весела?** *(What kind of person are you — quiet or cheerful?)*
</generated_module_content>

**PIPELINE NOTE — Word count: 3204 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 307 words | Not found: 11 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Антон — NOT IN VESUM
  ✗ Антоне — NOT IN VESUM
  ✗ Антоном — NOT IN VESUM
  ✗ Віктор — NOT IN VESUM
  ✗ Ганна — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM

All 307 other words are confirmed to exist in VESUM.

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
