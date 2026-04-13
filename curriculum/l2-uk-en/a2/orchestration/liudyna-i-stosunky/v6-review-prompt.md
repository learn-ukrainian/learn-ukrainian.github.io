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
## Зовнішність: як виглядає людина?

In this section, we will learn how to describe a **людина** (person, human being). When we meet new people, we often want to talk about their **зовнішність** (appearance). Later, we will explore their **характер** (character, personality) and our **стосунок** (relationship) with them.

Ми часто запитуємо одне одного про нових знайомих. Якщо ми хочемо дізнатися про зовнішність, ми питаємо: «Який він на вигляд?». Або ми запитуємо: «Яка її зовнішність?».

> *We often ask each other about new acquaintances. If we want to know about appearance, we ask: "What does he look like?". Or we ask: "What is her appearance?".*

When describing people, we talk about both their looks and personality. Someone might be **працьовитий** (hardworking) and **терплячий** (patient). Let's look at a conversation between two friends viewing photos. They describe a **сусід** (neighbor) who is **привітний** (friendly, welcoming) and **щирий** (sincere, genuine). Notice the difference between a habitual action and a one-time action.

> — **Подруга 1:** Хто це на фото? *(Who is this in the photo?)*
> — **Подруга 2:** Це моя сестра. Вона висока, темноволоса. *(This is my sister. She is tall, dark-haired.)*
> — **Подруга 1:** Яка вона людина? *(What kind of person is she?)*
> — **Подруга 2:** Дуже весела і щира людина. *(A very cheerful and sincere person.)*
> — **Подруга 1:** А хто цей чоловік поруч? *(And who is this man nearby?)*
> — **Подруга 2:** А це мій сусід. Він дуже привітний і працьовитий. *(And this is my neighbor. He is very friendly and hardworking.)*
> — **Подруга 1:** Він хороший сусід? *(Is he a good neighbor?)*
> — **Подруга 2:** Так, він терплячий і завжди допомагає. Учора допоміг мені з валізою. *(Yes, he is patient and always helps. Yesterday he helped me with a suitcase.)*

To describe someone's height, build, and age, we use basic adjectives that must agree in gender and number with the noun they describe. The most common pairs are tall and short, thin and plump, young and old.

Високий чоловік завжди привертає увагу, а висока жінка виглядає елегантно. Мій дідусь старий, але брат ще молодий. Худий хлопець швидко бігає, а повний чоловік іде повільно. Низький хлопчик стоїть поруч із мамою.

> *A tall man always attracts attention, and a tall woman looks elegant. My grandfather is old, but my brother is still young. A thin guy runs fast, but a plump man walks slowly. A short boy stands next to his mom.*

When describing a face, Ukrainian uses beautiful compound adjectives for hair and eyes, combining two words into one single descriptive word. You can also describe these features directly using simple adjectives.

У нього темне волосся, тому він темноволосий. У неї блакитні очі, отже, вона блакитноока. Її брат має світле волосся, він світловолосий. Якщо людина має карі очі, ми кажемо, що вона кароока.

> *He has dark hair, so he is dark-haired. She has blue eyes, therefore, she is blue-eyed. Her brother has light hair, he is light-haired. If a person has brown eyes, we say that they are brown-eyed.*

There are two main ways to state what physical features someone has. You can use the verb "to have" followed by the Accusative case, or the preposition "with" followed by the Instrumental case. Both options are natural when we want to **описувати** (to describe) someone. We will learn the full Instrumental case later.

Вона має карі очі і довге темне волосся. Це дівчина з карими очима і довгим темним волоссям. Він має коротке русяве волосся. Це хлопець із коротким русявим волоссям. 

> *She has brown eyes and long dark hair. This is a girl with brown eyes and long dark hair. He has short blonde hair. This is a guy with short blonde hair.*

When learning to describe people, English speakers often make literal translations that sound unnatural or incorrect in Ukrainian. It is important to think directly in Ukrainian structures.

:::tip
**Did you know?**
When translating "She looks beautiful", you can naturally say «Вона гарно виглядає», «Вона виглядає гарно», «Вона гарна», or «Вона має гарний вигляд», depending on the nuance you want. Also, avoid the Russian calque «самий високий» for "the tallest". The correct Ukrainian superlative uses the prefix **най-**, making it «найвищий».
:::

<!-- INJECT_ACTIVITY: fill-in-complete-sentences-describing-people-with-the-correct-adjective-form-agreement-for-gender -->

## Характер: яка вона людина? (~660 words total)

> — **Новий працівник:** Хто наш керівник? Який він? *(Who is our manager? What is he like?)*
> — **Досвідчений колега:** Він дуже відповідальний і справедливий. *(He is very responsible and fair.)*
> — **Новий працівник:** А інші колеги? *(And the other colleagues?)*
> — **Досвідчений колега:** Усі привітні, особливо Оксана — вона завжди підказує новим працівникам. *(Everyone is friendly, especially Oksana — she always helps new employees.)*

When you start a new job, move to a new city, or meet new friends, you naturally want to know what kind of **людина** (person, human being) you are dealing with. In Ukrainian culture, when someone asks «який він?» or «яка вона?», they are usually asking you to **описувати** (to describe) their **характер** (character, personality) rather than just their physical appearance. It is common to focus on a person's inner qualities and how they treat others. If you want to ask specifically about personality to avoid any confusion, the best and most natural question is «яка вона людина?» or «який у нього характер?».

There is a rich variety of wonderful adjectives you can use to describe positive traits in Ukrainian. A good colleague or a close friend is usually **привітний** (friendly, welcoming), **щирий** (sincere, genuine), and **чуйний** (responsive, caring). 

In a professional setting or at the university, we highly value people who are **розумний** (smart), **працьовитий** (hardworking), and **відповідальний** (responsible). 

When learning a new language or starting a difficult hobby, it is also very helpful if your teacher is **терплячий** (patient) and **веселий** (cheerful). To describe a strong inner drive, we say someone is **наполегливий** (persistent, determined).

Мій старший брат — дуже працьовитий і відповідальний. Він завжди багато працює і ніколи не забуває про свої обов'язки. Моя нова колега — дуже щира і чуйна людина, з якою приємно говорити. Наш керівник — суворий, але терплячий і наполегливий.

> *My older brother is very hardworking and responsible. He always works a lot and never forgets about his duties. My new colleague is a very sincere and caring person with whom it is pleasant to talk. Our manager is strict, but patient and persistent.*

Of course, not everyone is always cheerful and easygoing. Sometimes we need to describe more complex or challenging traits. A person might simply be **сумний** (sad) today, or they might be naturally **серйозний** (serious) and **тихий** (quiet) in group settings. 

Sometimes people do not want to work at all, so we call them **ледачий** (lazy). You might also meet someone who refuses to change their mind, whom we call **впертий** (stubborn).

:::tip
**Did you know?**
The word **впертий** (stubborn) is not always a negative trait in Ukrainian culture. While it can mean that someone refuses to listen to reason, it often means that a person is persistent, principled, and determined to achieve their goals despite obstacles. It can be a strong compliment!
:::

<!-- INJECT_ACTIVITY: group-sort-traits -->
<!-- INJECT_ACTIVITY: match-up-definitions -->

How do we know what kind of character a person has? We usually look at their daily actions and how they treat others over time, like how a **сусід** (neighbor) acts in your building. In Ukrainian, we often prove a character trait by describing what a person regularly does. Because these are habitual, repeated actions, we must use verbs in the imperfective aspect. The word «завжди» (always) or the phrase «кожного дня» (every day) is a great hint that we need an imperfective verb to show a permanent personality trait.

Мій сусід дуже привітний, тому що він завжди приємно спілкується з усіма. Мій друг щирий, бо він завжди говорить правду і ніколи не бреше. Наша колега Оксана надзвичайно чуйна — вона завжди підказує і допомагає новим працівникам у нашому офісі.

> *My neighbor is very friendly because he always communicates pleasantly with everyone. My friend is sincere because he always tells the truth and never lies. Our colleague Oksana is extremely caring — she always suggests and helps new employees in our office.*

While the imperfective aspect shows a habitual trait, we use the perfective aspect to describe a specific, one-time action that serves as a single proof of a person's character. The perfective aspect focuses on the completed result. If a colleague is generally helpful, they «завжди допомагають» (always help — imperfective). But if they helped you complete a specific, difficult project yesterday, you use the perfective aspect to highlight that completed action.

Вона справді хороша людина, бо вона допомогла мені вчора з важким завданням. Мій друг дуже розумний і надійний — він підказав мені правильне рішення, коли я мав проблему.

> *She is a truly good person because she helped me yesterday with a difficult task. My friend is very smart and reliable — he suggested the right solution to me when I had a problem.*

:::info
**Grammar box**
Compare the two aspects when describing people:
**Імперфектив (Imperfective):** Вона завжди підказує. *(She always helps/suggests — a habitual trait that makes her a helpful person).*
**Перфектив (Perfective):** Вона підказала мені вчора. *(She helped/suggested yesterday — a one-time action showing her good character).*
:::

<!-- INJECT_ACTIVITY: quiz-choose-the-correct-adjective-to-complete-a-description -->

## Люди навколо нас: родичі, друзі, знайомі (~600 words total)

We do not live in isolation. Our lives are shaped by the different circles of people around us. In Ukrainian, we use the word **стосунок** (relationship) to describe the connection between people. Every **людина** (person, human being) has a unique personality. Having the right vocabulary helps us explain who someone is to us. Let us look at the different groups of people you might interact with regularly.

Кожна людина будує унікальні стосунки з іншими. Люди навколо нас — це наші рідні, колеги по роботі та просто випадкові перехожі. Ми часто описуємо цих людей, коли розповідаємо про свій день.

> *Every person builds unique relationships with others. The people around us are our family, work colleagues, and just random passersby. We often describe these people when we talk about our day.*

The closest circle usually consists of our family. You likely already know the basic words for parents, siblings, and grandparents. As our families grow, we also talk about our uncles and aunts. When introducing your relatives, it is common to use an adjective like **терплячий** (patient) to describe their personality. 

Це мій дядько, він дуже веселий і завжди жартує. А це моя тітка Олена — вона дуже терпляча і розумна жінка. Мої дідусь і бабуся живуть у селі, ми часто їздимо до них у гості. 

> *This is my uncle, he is very cheerful and always jokes. And this is my aunt Olena — she is a very patient and smart woman. My grandfather and grandmother live in a village, we often go to visit them.*

Outside of our family, we choose our friends and build social circles. We have different words for close friends, casual mates, and simple acquaintances. Ukrainians deeply value a **щирий** (sincere, genuine) friend who has a good **характер** (character, personality). 

Ми дружимо вже п'ять років, тому вона — моя найкраща подруга. Ми разом вчилися в університеті, він мій давній товариш. На вечірці був один мій знайомий, але ми майже не спілкувалися. Ми дуже цінуємо щирих людей.

> *We have been friends for five years already, so she is my best friend. We studied together at the university, he is my old mate. There was an acquaintance of mine at the party, but we barely talked. We really value sincere people.*

:::tip
**Did you know?** The word **знайомий** (acquaintance) acts like an adjective, but we use it as a noun to refer to a person we know. Its feminine form is **знайома**, and the plural is **знайомі**.
:::

Our daily routines also force us to interact with people at work and at home. At your workplace, you interact with colleagues. At home, you share your street or building with a **сусід** (neighbor). It is wonderful when your neighbor is a **привітний** (friendly, welcoming) person. A good colleague is usually **працьовитий** (hardworking).

Він мій сусід — живе поруч, завжди привітний і готовий допомогти. Моя нова колега — дуже працьовита спеціалістка, вона працює в нашому відділі.
 Зазвичай мої сусіди тихі, ми зустрічаємося тільки вранці.

> *He is my neighbor — he lives nearby, is always friendly and ready to help. My new colleague is a very hardworking specialist, she works in our department. Usually, my neighbors are quiet, we only meet in the morning.*

Relationships are defined by how we act toward one another. When we want to describe these dynamics, we use verbs paired with personal pronouns. Some verbs take the Accusative case, answering "who" receives the action, while others take the Dative case, answering "to whom" the action is directed.

Моя сестра добре мене знає, тому вона мені довіряє.
 Мій керівник дуже серйозний, але він мене поважає як професіонала. Мої батьки живуть далеко, проте вони нам допомагають.

> *My sister always tells the truth, so she trusts me. My manager is very serious, but he respects me as a professional. My parents live far away, however, they help us.*

:::info
**Grammar box**
Pay attention to the pronouns when describing actions in relationships:
*   **Довіряти** (to trust) and **допомагати** (to help) use the Dative case: **Вона мені довіряє** (She trusts me).
*   **Поважати** (to respect) uses the Accusative case: **Він мене поважає** (He respects me).
:::

In real life, you will frequently need to properly **описувати** (to describe) people in short, natural exchanges. When looking at photos or introducing someone new, we often start with their identity, then mention their **зовнішність** (appearance) and their character traits.

> — **Марія:** А хто це? *(And who is this?)*
> — **Антон:** Це мій колега, Ігор. *(This is my colleague, Ihor.)*
> — **Марія:** Який він? *(What is he like?)*
> — **Антон:** Він дуже працьовитий і серйозний. *(He is very hardworking and serious.)*
> — **Марія:** А це хто поруч із ним? *(And who is this next to him?)*
> — **Антон:** Це наша спільна знайома. Вона чуйна людина. *(This is our mutual acquaintance. She is a caring person.)*

Описувати людей навколо нас — це дуже корисна навичка. Коли ми знаємо правильні слова, ми можемо легко розповісти про свою родину або колег.

## Описуємо людину цілком

Now it is time to bring everything together. When you fully **описувати** (to describe) someone, you combine details about their identity and **зовнішність** (appearance). This gives a complete picture of the **людина** (person, human being).

Мій сусід Андрій — високий хлопець із карими очима. Він має коротке темне волосся і носить окуляри. Його характер дуже спокійний. Він дуже веселий і добрий. Ми живемо поруч уже п'ять років і часто граємо у футбол.

> *My neighbor Andrii is a tall guy with brown eyes. He has short dark hair and wears glasses. His character is very calm. He is very cheerful and kind. We have lived nearby for five years already and often play football.*

A great portrait also includes their **характер** (character, personality) and your **стосунок** (relationship). For example, you might mention how long you have known your **сусід** (neighbor).

To build your own descriptions effectively, you can follow a simple three-step structure. First, establish the identity by answering «Хто це?» (Who is it?). Next, describe their physical traits by asking «Яка зовнішність?». Finally, complete the portrait by explaining «Який характер?».

Це моя нова колега Олена. Вона невисока і має довге світле волосся. Олена — дуже розумна людина з великим досвідом. Вона завжди уважно слухає інших і швидко допомагає новим працівникам.

> *This is my new colleague Olena. She is short and has long blonde hair. Olena is a very smart person with great experience. She always listens carefully to others and quickly helps new employees.*

We often highlight positive traits when introducing friends or coworkers. It is incredibly helpful to know if a person is naturally **привітний** (friendly, welcoming) or if they are known as a **працьовитий** (hardworking) specialist.

:::tip
**Did you know?**
When Ukrainians talk about others, they often value inner qualities over physical appearance. Calling someone a «добра людина» (good person) is one of the highest compliments you can give. This phrase emphasizes «душевна краса» (inner beauty) and shows that the person is caring, reliable, and treats everyone well.
:::

You can also mention if someone is truly **щирий** (sincere, genuine) in their words, or if they are consistently **терплячий** (patient) when dealing with difficult situations.

Here is a short conversation about people in a photo:

> — **Марко:** Привіт, Анно! А хто цей хлопець на фото? *(Hi, Anna! And who is this guy in the photo?)*
> — **Анна:** Це мій старший брат, Іван. *(This is my older brother, Ivan.)*
> — **Марко:** Який він? У нього дуже суворий вигляд. *(What is he like? He has a very strict look.)*
> — **Анна:** Ні, він просто серйозний. Але він дуже добрий. *(No, he is just serious. But he is very kind.)*
> — **Марко:** А дівчина поруч із ним? Це його дружина? *(And the girl next to him? Is that his wife?)*
> — **Анна:** Ні, це його найкраща подруга Марія. *(No, this is his best friend Mariia.)*
> — **Марко:** Вона має дуже гарне довге волосся. *(She has very beautiful long hair.)*
> — **Анна:** Так, і вона дуже весела та щира людина. *(Yes, and she is a very cheerful and sincere person.)*

### Читаємо українською

Моя родина невелика, але ми дуже дружні. Мій батько — високий чоловік із сивим волоссям. Він дуже відповідальний і завжди багато працює. Моя мати трохи нижча за нього. Вона має коротке світле волосся і зелені очі. Мати — дуже чуйна людина. Вона любить допомагати всім сусідам. Мій молодший брат ще студент. Він іноді буває ледачий, але він дуже веселий хлопець. У нього темне кучеряве волосся. Він любить грати на гітарі вечорами. Ми любимо проводити час разом на вихідних. Зазвичай ми ходимо в кіно або гуляємо в парку.

> *My family is small, but we are very close. My father is a tall man with gray hair. He is very responsible and always works a lot. My mother is a little shorter than him. She has short blonde hair and green eyes. Mother is a very caring person. She loves helping all the neighbors. My younger brother is still a student. He is sometimes lazy, but he is a very cheerful guy. He has dark curly hair. He loves playing the guitar in the evenings. We love spending time together on the weekends. Usually, we go to the movies or walk in the park.*

You now have all the tools needed to talk about the people around you in Ukrainian. For your final practice task, think of two or three people you know well. Write down a short paragraph for each of them using the three-step pattern we practiced.
</generated_module_content>

**PIPELINE NOTE — Word count: 2871 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 339 words | Not found: 10 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Імперфектив — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Анно — NOT IN VESUM
  ✗ Антон — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Перфектив — NOT IN VESUM

All 339 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.
