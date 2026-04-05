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

When we meet someone new, the first thing we notice is their appearance. In Ukrainian, describing a person's appearance — **зовнішність** — relies heavily on descriptive adjectives. Let's look at how two friends discuss people in a photograph.

> **Подруга 1:** Це твоя сестра на фото? Вона висока, темноволоса. *(Is this your sister in the photo? She is tall, dark-haired.)*
> **Подруга 2:** Так, це моя сестра. Вона дуже весела і щира людина. *(Yes, this is my sister. She is a very cheerful and sincere person.)*
> **Подруга 1:** А це хто поруч із нею? *(And who is this next to her?)*
> **Подруга 2:** А це мій сусід. Він завжди мені допомагає. Учора допоміг мені з валізою. *(And this is my neighbor. He always helps me. Yesterday he helped me with a suitcase.)*

When describing appearance, you need pairs of opposite adjectives. Remember that adjectives in Ukrainian change to match the gender (masculine, feminine, neuter) and number of the noun they describe. Here are the core pairs:

*   **високий** (tall) — **низький** (short)
*   **худий** (thin) — **повний** (plump/full)
*   **молодий** (young) — **старий** (old)
*   **темноволосий** (dark-haired) — **світловолосий** (light-haired/blonde)
*   **кароокий** (brown-eyed) — **блакитноокий** (blue-eyed)

Let's see these adjectives in action. Notice how the endings change depending on who is being described.

*   **Цей чоловік дуже високий.** (This man is very tall.)
*   **Моя подруга низька і худа.** (My friend is short and thin.)
*   **Наш дідусь старий, але дуже активний.** (Our grandfather is old, but very active.)
*   **Ця жінка — повна.** (This woman is plump.)
*   **Мій брат — світловолосий хлопець.** (My brother is a blonde guy.)
*   **Ця дівчинка кароока.** (This girl is brown-eyed.)

In Ukrainian, there are two common ways to describe physical features like eyes (**очі**) or hair (**волосся**). We can use the verb **мати** (to have) with the accusative case, or we can use the preposition **з** (with) followed by the instrumental case. You will learn the full rules for the instrumental case in a later module, but here is a preview of how it looks in common descriptions.

Using **мати** (to have):
*   **Вона має карі очі.** (She has brown eyes.)
*   **Він має світле волосся.** (He has light hair.)
*   **Моя мама має блакитні очі.** (My mom has blue eyes.)
*   **Мій тато має темне волосся.** (My dad has dark hair.)
*   **Ця дівчина має зелені очі.** (This girl has green eyes.)

Using **з** (with) + instrumental case:
*   **Вона — дівчина з карими очима.** (She is a girl with brown eyes.)
*   **Він — хлопець зі світлим волоссям.** (He is a guy with light hair.)
*   **Це жінка з блакитними очима.** (This is a woman with blue eyes.)
*   **Я бачу чоловіка з темним волоссям.** (I see a man with dark hair.)
*   **Це дитина із зеленими очима.** (This is a child with green eyes.)

Note how the endings **-ими** or **-им** appear on the adjectives after the preposition **з** (which becomes **зі** or **із** for easier pronunciation before certain sounds). 

### Читаємо українською (Reading Practice)

**На старій фотографії**
Це стара фотографія моєї родини. Ось мій тато. Він молодий, високий і темноволосий. Він має карі очі. Поруч стоїть моя мама. Вона низька, але дуже струнка. Мама світловолоса і блакитноока. А це я. Я ще маленька дівчинка з карими очима. Ми всі дуже щасливі на цьому фото.

<!-- INJECT_ACTIVITY: fill-in -->

## Характер: яка вона людина? (Character: What Kind of Person Is She?)

A person's appearance is only half the picture. In Ukrainian culture, a person's inner world — their **характер** (character, personality) — is considered much more important. Let's observe a workplace conversation where colleagues discuss character.

> **Новий працівник:** Хто ваш керівник? Який він? *(Who is your manager? What is he like?)*
> **Досвідчений колега:** Він дуже відповідальний і терплячий. *(He is very responsible and patient.)*
> **Новий працівник:** А колеги? *(And the colleagues?)*
> **Досвідчений колега:** Усі привітні, особливо Оксана — вона завжди підказує новим працівникам. *(Everyone is friendly, especially Oksana — she always helps new employees.)*

To describe a person's character, we use specific personality adjectives. Here are the most common positive traits you will hear in everyday conversation:

*   **привітний** (friendly, welcoming)
*   **щирий** (sincere, genuine)
*   **чуйний** (responsive, caring)
*   **добрий** (kind, good)
*   **веселий** (cheerful)
*   **розумний** (smart, intelligent)
*   **працьовитий** (hardworking)
*   **терплячий** (patient)
*   **відповідальний** (responsible)
*   **наполегливий** (persistent, determined)

Let's look at how we combine these adjectives in sentences:

*   **Мій брат дуже привітний.** (My brother is very friendly.)
*   **Вона — щира людина.** (She is a sincere person.)
*   **Наш керівник відповідальний і розумний.** (Our manager is responsible and smart.)
*   **Ця жінка дуже працьовита.** (This woman is very hardworking.)
*   **Моя бабуся завжди чуйна.** (My grandmother is always caring.)

Not all traits are entirely positive. There are also challenging traits. However, in Ukrainian culture, some of these can be seen from a different perspective. 

*   **впертий** (stubborn)
*   **сумний** (sad)
*   **ледачий** (lazy)
*   **серйозний** (serious)
*   **тихий** (quiet)

:::note
**Cultural Perspective**
The word **впертий** literally means "stubborn". While often seen as a negative trait (e.g., refusing to listen to reason), Ukrainians also frequently use it as a positive compliment meaning "persistent" or "principled" when someone refuses to give up in the face of difficulty. A person who achieves great success is often described as **впертий**.
:::

Let's look at these challenging traits in context:

*   **Цей хлопець дуже ледачий.** (This guy is very lazy.)
*   **Чому ти сьогодні такий сумний?** (Why are you so sad today?)
*   **Моя сестра дуже вперта.** (My sister is very stubborn.)
*   **Цей студент серйозний і тихий.** (This student is serious and quiet.)
*   **Він впертий, тому завжди перемагає.** (He is stubborn [persistent], that's why he always wins.)

### Expressing Character Through Actions (Aspect Integration)

In Ukrainian, we often describe a person's character not just with adjectives, but by describing what they *do*. This is where verbal aspect becomes crucial. 

When we describe habitual actions — things a person does regularly that prove their character — we use the **imperfective aspect**. 

*   **Він завжди допомагає людям.** (He always helps people. — *Habitual, imperfective*)
*   **Вона часто підказує колегам.** (She often helps colleagues. — *Habitual, imperfective*)
*   **Мій друг завжди працює допізна.** (My friend always works late. — *Habitual, imperfective*)

When we want to give a specific, one-time example that proves a person's character, we use the **perfective aspect**.

*   **Вчора він допоміг мені з проєктом.** (Yesterday he helped me with a project. — *One-time, perfective*)
*   **Вона підказала мені правильну адресу.** (She gave me the right address. — *One-time, perfective*)
*   **Він попрацював у вихідні.** (He worked on the weekend. — *One-time, perfective*)

By combining adjectives and verbs of different aspects, you create a rich, natural portrait of a person.

### Читаємо українською (Reading Practice)

**Моя нова колега**
Це моя нова колега, Олена. Вона дуже розумна і відповідальна жінка. Олена привітна — вона завжди вітається вранці. Вона також дуже працьовита. Олена завжди працює швидко. Учора був складний день, але вона швидко зробила всю роботу. Я думаю, що вона щира і добра людина. 

<!-- INJECT_ACTIVITY: match-up -->
<!-- INJECT_ACTIVITY: group-sort -->

## Люди навколо нас: родичі, друзі, знайомі (People Around Us)

Now that you can describe appearance and character, you need the vocabulary to explain who these people are to you. We are constantly surrounded by different types of relationships — **стосунки**.

Let's see how someone introduces people in a natural conversation:

> **Олег:** А хто це на фотографії? *(And who is this in the photo?)*
> **Марія:** Це мій дядько. Він живе поруч. *(This is my uncle. He lives nearby.)*
> **Олег:** Який він? *(What is he like?)*
> **Марія:** Він мій найкращий друг. Він мене поважає і завжди слухає. *(He is my best friend. He respects me and always listens.)*

Here is the essential vocabulary for relationships:

*   **родич** (relative)
*   **мати / батько** (mother / father)
*   **брат / сестра** (brother / sister)
*   **дідусь / бабуся** (grandfather / grandmother)
*   **дядько / тітка** (uncle / aunt)
*   **друг / подруга** (male friend / female friend)
*   **товариш** (friend / comrade / buddy)
*   **сусід / сусідка** (male neighbor / female neighbor)
*   **колега** (colleague)
*   **знайомий / знайома** (male acquaintance / female acquaintance)

:::tip
**Друг vs Товариш vs Знайомий**
A **друг** is a close, trusted friend. A **товариш** is a casual friend, buddy, or a companion you share activities with. A **знайомий** is simply an acquaintance — someone you know, but are not close to. 
:::

When talking about your relationships, you can use these common sentence patterns:

*   **Це мій близький родич.** (This is my close relative.)
*   **Ми дружимо вже п'ять років.** (We have been friends for five years.)
*   **Вона — моя найкраща подруга.** (She is my best friend.)
*   **Він мій сусід — живе поруч.** (He is my neighbor — he lives nearby.)
*   **Це моя нова знайома.** (This is my new acquaintance.)
*   **Мій дядько і моя тітка живуть там.** (My uncle and my aunt live there.)
*   **Вона моя колега по роботі.** (She is my colleague from work.)

To describe how someone acts toward you in a relationship, you can use verbs that take an object (often in the dative or accusative case).

*   **Вона мені довіряє.** (She trusts me.)
*   **Він мене поважає.** (He respects me.)
*   **Вони нам допомагають.** (They help us.)
*   **Мої батьки мене розуміють.** (My parents understand me.)
*   **Сусіди нам часто телефонують.** (The neighbors often call us.)

If someone asks you **"А хто це?"** (And who is this?), you can respond with their relationship to you. If they ask **"Який він?"** (What is he like?) or **"Яка вона?"** (What is she like?), you can describe their character or actions.

*   **А хто це? Це мій товариш.** (And who is this? This is my buddy.)
*   **Який він? Він дуже веселий і щирий.** (What is he like? He is very cheerful and sincere.)
*   **А хто ця дівчина? Це моя знайома.** (And who is this girl? This is my acquaintance.)
*   **Яка вона? Вона привітна і розумна.** (What is she like? She is friendly and smart.)

### Читаємо українською (Reading Practice)

**Мої сусіди**
Це мій сусід Іван і його дружина Марія. Вони — мої хороші знайомі. Іван дуже працьовитий чоловік. Він часто працює в саду. Марія — дуже чуйна жінка. Вона завжди вітається і запитує про мої справи. Вони нам часто допомагають. Ми поважаємо їх. Вони дуже добрі сусіди.

<!-- INJECT_ACTIVITY: quiz -->

## Описуємо людину цілком (Describing a Person Fully)

You now have all the tools you need to create a complete portrait of a person: who they are to you, what they look like, and what kind of character they possess. 

In Ukrainian, it is natural to combine all these elements into a cohesive description. You start with the relationship, move to the physical appearance, and finish with their inner qualities.

Here is an example of a complete description:

*   **Мій друг Андрій — високий хлопець із карими очима. Він дуже веселий і щирий. Ми познайомилися в університеті.** (My friend Andriy is a tall guy with brown eyes. He is very cheerful and sincere. We met at the university.)
*   **Це моя тітка Олена. Вона низька жінка зі світлим волоссям. Вона надзвичайно терпляча і відповідальна.** (This is my aunt Olena. She is a short woman with light hair. She is extremely patient and responsible.)
*   **Мій новий колега — повний чоловік. Він має блакитні очі. Він дуже розумний і працьовитий.** (My new colleague is a plump man. He has blue eyes. He is very smart and hardworking.)

Notice how these paragraphs flow. They paint a complete picture of the individual. Try to think of two or three people you know and describe them using this exact pattern in your head. 

:::caution
**"Добра людина"**
In English, saying someone is a "good person" can sometimes sound generic or weak. In Ukrainian culture, calling someone **добра людина** is a powerful and highly respected compliment. It implies they are decent, honest, and morally upright. It is often the highest praise you can give someone's character.
:::

### Читаємо українською (Reading Practice)

**Мій найкращий друг**
Мій друг Сергій — дуже цікава людина. Він високий і світловолосий хлопець. Він має блакитні очі. Сергій — мій найкращий друг. Ми дружимо вже десять років. Він надзвичайно відповідальний і щирий. Він завжди мені допомагає. Учора він допоміг мені перекласти текст. Сергій дуже добра людина, і я його поважаю.

## Підсумок — Summary

In this module, you learned how to fully describe the people around you in Ukrainian. You started by learning how to describe physical appearance (**зовнішність**) using descriptive adjective pairs like **високий/низький** and **молодий/старий**, as well as how to describe specific features using **мати** or **з + орудний відмінок**.

You also expanded your vocabulary to describe a person's inner world, their **характер**. You learned positive traits like **щирий** and **працьовитий**, and challenging traits like **впертий** and **ледачий**. Importantly, you saw how to use the imperfective aspect for habitual character traits and the perfective aspect for one-time actions that prove a person's character.

Finally, you learned the vocabulary for relationships (**стосунки**) — from **родичі** to **знайомі** — and how to express how people act toward you. You now have the linguistic tools to confidently answer the questions **"А хто це?"** and **"Який він?"** in any natural conversation.

**Deterministic word count: 2082 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

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
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
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

Verified: 240 words | Not found: 8 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Сергій — NOT IN VESUM
  ✗ ими — NOT IN VESUM

All 240 other words are confirmed to exist in VESUM.

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
