<!-- version: 1.2.0 | updated: 2026-04-12 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/liudyna-i-stosunky.yaml` file for module **4: Яка вона людина? Описуємо людей навколо нас** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | 12 | 12+ | inline + workbook combined |
| Inline (lesson tab) | 4 | 6 | one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | 8 | 11 | extended practice |
| Items per activity | 8 | — | each activity must have at least 8 items (unless its type cap is lower — see Activity Type Reference below) |

**You MUST ship at least 4 inline activities AND at least 8 workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **0** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level. (If `0` is `0`, the audit profile for this level does not enforce type diversity — but variety still produces a better lesson, so aim for 4+ types when the workbook allows it.)

---

## Allowed types for THIS level

- **Inline (lesson) types:** quiz, true-false, fill-in, match-up, group-sort, classify, mark-the-words
- **Inline priority (preferred):** fill-in, match-up, true-false, quiz
- **Workbook types:** cloze, error-correction, fill-in, unjumble, translate, match-up, group-sort, odd-one-out, observe, phrase-table, quiz, true-false, mark-the-words
- **Workbook priority (preferred):** error-correction, cloze, unjumble, translate, fill-in
- **FORBIDDEN at this level:** anagram, essay-response, critical-analysis, reading, comparative-study, authorial-intent, etymology-trace, translation-critique, source-evaluation, debate, paleography-analysis, dialect-comparison, transcription, image-to-letter, letter-grid, watch-and-repeat, divide-words, count-syllables, pick-syllables, highlight-morphemes, grammar-identify

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 4–6 quick checks after key teaching points. Workbook = 8–11 deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: fill-in-complete-sentences-describing-people-with-the-correct-adjective-form-agreement-for-gender -->`
- `<!-- INJECT_ACTIVITY: group-sort-traits -->`
- `<!-- INJECT_ACTIVITY: match-up-definitions -->`
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`
- `<!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->`
- `<!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->`

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

У нього темне волосся, тому він темноволосий. У неї сині очі, отже, вона синьоока. Її брат має світле волосся, він світловолосий. Якщо людина має карі очі, ми кажемо, що вона кароока.

> *He has dark hair, so he is dark-haired. She has blue eyes, therefore, she is blue-eyed. Her brother has light hair, he is light-haired. If a person has brown eyes, we say that they are brown-eyed.*

There are two main ways to state what physical features someone has. You can use the verb "to have" followed by the Accusative case, or the preposition "with" followed by the Instrumental case. Both options are natural when we want to **описувати** (to describe) someone. We will learn the full Instrumental case later.

Вона має карі очі і довге темне волосся. Це дівчина з карими очима і довгим темним волоссям. Він має коротке русяве волосся. Це хлопець із коротким русявим волоссям. 

> *She has brown eyes and long dark hair. This is a girl with brown eyes and long dark hair. He has short blonde hair. This is a guy with short blonde hair.*

When learning to describe people, English speakers often make literal translations that sound unnatural or incorrect in Ukrainian. It is important to think directly in Ukrainian structures.

:::tip
**Did you know?**
When translating "She looks beautiful", do not use the literal «Вона виглядає гарно». In Ukrainian, this implies she is actively looking at something beautifully with her eyes! Instead, use «Вона гарна» (She is beautiful) or «Вона має гарний вигляд» (She has a good look). Also, avoid the Russian calque «самий високий» for "the tallest". The correct Ukrainian superlative uses the prefix **най-**, making it «найвищий».
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

<!-- INJECT_ACTIVITY: quiz-aspect-choice -->

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

Він мій сусід — живе поруч, завжди привітний і готовий допомогти. Моя нова колега дуже працьовитий спеціаліст, вона працює в нашому відділі. Зазвичай мої сусіди тихі, ми зустрічаємося тільки вранці.

> *He is my neighbor — he lives nearby, is always friendly and ready to help. My new colleague is a very hardworking specialist, she works in our department. Usually, my neighbors are quiet, we only meet in the morning.*

Relationships are defined by how we act toward one another. When we want to describe these dynamics, we use verbs paired with personal pronouns. Some verbs take the Accusative case, answering "who" receives the action, while others take the Dative case, answering "to whom" the action is directed.

Моя сестра завжди каже правду, тому вона мені довіряє. Мій керівник дуже серйозний, але він мене поважає як професіонала. Мої батьки живуть далеко, проте вони нам допомагають.

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

<!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->

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

<!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: liudyna-i-stosunky
level: a2

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# (12 total / 4–6 inline / 8–11 workbook,
# 8+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:                     # ← real output: ≥ 8 items
      - question: "_____ стіл"
        options: ["мій", "моя", "моє", "мої"]
        correct: 0             # 0-based index
      - question: "Це ____ книга."
        options: ["мій", "моя", "моє", "мої"]
        correct: 1
      # ... add at least 8 items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:                     # ← real output: ≥ 8 items
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]
      - sentence: "Це ____ вікно."
        answer: "моє"
        options: ["мій", "моя", "моє"]
      # ... ≥ 8 items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "З'єднайте пари"
    pairs:                     # ← real output: ≥ 8 pairs
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"
      # ... ≥ 8 pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Чоловічий рід"
        items: ["стіл", "олівець", "будинок"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["книга", "ручка", "школа"]
      - label: "Середній рід"
        items: ["вікно", "море", "молоко"]

  - id: true-false-grammar
    type: true-false
    instruction: "Правда чи ні?"
    items:                     # ← real output: ≥ 8 items
      - statement: "«Книга» — це чоловічий рід."
        correct: false
        explanation: "Книга закінчується на -а, отже жіночий рід."
      # ... ≥ 8 items total

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
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "Це ____ кімната."` with `answer: "моя"`. The validator REJECTS `{word}` format.**
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

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: 12 activities.** Inline: 4–6. Workbook: 8–11. The audit gate FAILS the module if you ship fewer.
- **Type diversity: workbook MUST cover ≥5 distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: 8 items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ 8.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
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

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **at least 4** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least 8** workbook activities.
- [ ] **Total ≥ 12.**
- [ ] **Every** activity has **at least 8** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least 0 distinct activity types** (or 4+ when 0 = 0 and the workbook size allows it). I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is between 4 and 6. I did NOT create more injection markers than 6.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
