# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 41: Checkpoint: Food and Shopping (A1, A1.6 [Food and Shopping])
**Writer:** Gemini Pro
**Word target:** 1000

## Plan (source of truth)

<plan_content>
module: a1-041
level: A1
sequence: 41
slug: checkpoint-food-shopping
version: '1.2'
title: 'Checkpoint: Food and Shopping'
subtitle: Can you order food and buy things in Ukrainian?
focus: review
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1000
objectives:
- Demonstrate food and drink vocabulary in context
- Use accusative case correctly for both inanimate and animate nouns
- Order at a cafe and buy things at a shop/market
- Combine all A1.6 skills in connected scenarios
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M36-M40: Can you name 10 foods and 5 drinks? (M36) Can you
    say what you eat/drink using accusative? (M37) Can you order at a cafe? (M38)
    Can you ask prices and buy things? (M39) Can you use accusative for people? (M40)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using vocabulary from M36-M40. Content: Anna goes to the
    market, buys food, then goes to a cafe. She orders борщ and каву з молоком, asks
    for the bill, then meets a friend and introduces her brother. Uses food vocabulary,
    accusative inanimate and animate, cafe phrases.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.6: 1. Food/drink vocabulary: їжа, напої, meals (M36) 2.
    Accusative inanimate: masc = nom, fem -а→-у (M37) 3. Ordering: Мені каву, будь
    ласка (M38) 4. Prices: Скільки коштує? Гривня/гривні/гривень (M39) 5. Accusative
    animate: fem -а→-у, masc = genitive (M40) 6. Chunks: кава з молоком, кілограм
    яблук (M36, M39)'
- section: Діалог (Connected Dialogue)
  words: 200
  points:
  - 'A day of food and shopping: — Що ти їш на сніданок? — Я їм кашу і п''ю каву з
    молоком. — Потім іду на ринок. Скільки коштують помідори? — Тридцять гривень.
    — Дайте кілограм, будь ласка. — Потім у кафе: Мені борщ і воду, будь ласка. —
    О, я бачу Олену! Олено, привіт! Ти знаєш мого брата? Combines all A1.6 skills
    in one realistic day.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'A1.6 achievement summary: You can talk about food and drinks. You can use accusative
    for things AND people. You can order at a cafe and pay. You can shop at a market
    and ask prices. Next: A1.7 — Communication (phone, email, making plans).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Accusative check: choose correct form for inanimate AND animate nouns'
  items:
  - question: Я їм ___.
    options:
    - салат
    - салата
    - салату
  - question: Я бачу ___.
    options:
    - брата
    - брат
    - брату
  - question: Я п'ю ___.
    options:
    - воду
    - вода
    - води
  - question: Я знаю ___.
    options:
    - Олену
    - Олена
    - Олени
  - question: Я люблю ___.
    options:
    - борщ
    - борща
    - борщу
  - question: Я чекаю ___.
    options:
    - друга
    - друг
    - другу
  - question: Я купую ___.
    options:
    - хліб
    - хліба
    - хлібу
  - question: Я бачу ___.
    options:
    - лікаря
    - лікар
    - лікарю
  - question: Я їм ___.
    options:
    - піцу
    - піца
    - піци
  - question: Я люблю ___.
    options:
    - маму
    - мама
    - мами
- type: fill-in
  focus: Complete the cafe + market dialogue with correct forms
  items:
  - — Що ти їш на сніданок? — Я їм {кашу|каша|каші} і п'ю каву.
  - — Потім іду на ринок. Скільки {коштують|коштує|коштувати} помідори?
  - — Тридцять {гривень|гривні|гривня}.
  - — Дайте {кілограм|літр|пляшку} яблук, будь ласка.
  - '— Потім у кафе: {Мені|Я|Меня} борщ і воду, будь ласка.'
  - — Рахунок, будь ласка. Можна {карткою|картка|картки}?
  - — О, я бачу {Олену|Олена|Олени}! Олено, привіт!
  - — Ти знаєш мого {брата|брат|братом}?
- type: group-sort
  focus: 'Sort accusative forms: inanimate (що?) vs animate (кого?)'
  groups:
  - name: Inanimate (що?)
    items:
    - борщ
    - хліб
    - сік
    - чай
    - сир
  - name: Animate (кого?)
    items:
    - брата
    - лікаря
    - сусіда
    - друга
    - вчителя
- type: quiz
  focus: What do you say? Match shopping/cafe situations to correct phrases
  items:
  - question: 'You want to order coffee:'
    options:
    - Мені каву, будь ласка.
    - Скільки коштує?
    - Тут вільно?
  - question: 'You ask for the price:'
    options:
    - Скільки коштує?
    - Можна карткою?
    - Що ви рекомендуєте?
  - question: 'You want to pay with a card:'
    options:
    - Можна карткою?
    - Рахунок, будь ласка.
    - Дорого!
  - question: 'You ask for the bill:'
    options:
    - Рахунок, будь ласка.
    - Мені борщ.
    - Все було дуже смачно!
  - question: 'You ask for 1 kg of apples:'
    options:
    - Дайте кілограм яблук.
    - Скільки коштує?
    - Можна меню?
  - question: 'You think the price is high:'
    options:
    - Дорого!
    - Дешево!
    - Нормальна ціна.
  - question: 'You ask if a seat is free:'
    options:
    - Тут вільно?
    - Можна меню?
    - Рахунок, будь ласка.
  - question: 'You compliment the food:'
    options:
    - Все було дуже смачно!
    - Можна карткою?
    - Це гостре?
connects_to:
- a1-042 (next module in A1.7)
prerequisites:
- a1-040 (People Around Me)
grammar:
- 'Review: accusative inanimate (M37) and animate (M40)'
- 'Review: ordering patterns (M38) and price patterns (M39)'
- 'Review: з + noun chunks (M36, M39)'
register: розмовний
references:
- title: Synthesis of M36-M40 content
  notes: No new material — review and integration of A1.6 phase.

</plan_content>

## Generated Content

<generated_module_content>
## Що ми знаємо? (What Do We Know?)

You now possess the practical, everyday Ukrainian skills needed for food and shopping. The ability to buy food, order a meal, and identify people correctly makes you highly functional in any Ukrainian city.

Think about the following questions. Can you confidently do these tasks?

First, can you name ten foods (**їжа** means "food") and five drinks (**напої** means "drinks")? Recall vocabulary words like **хліб** (bread), **м'ясо** (meat), **вода** (water), and **сік** (juice). 

Second, can you say what you eat and drink using the accusative case? When a word is the direct object of your action, it changes.
*   **Я їм піцу.** (I eat pizza.)
*   **Я п'ю воду.** (I drink water.)

Third, can you order at a cafe? You use specific phrases to ask for what you want politely.
*   **Мені каву, будь ласка.** (Coffee for me, please.)

Fourth, can you ask for prices and buy things at the market (**ринок**) or in a shop?
*   **Скільки коштує?** (How much does it cost?)

Finally, can you use the accusative case for people? People trigger special endings for masculine nouns.
*   **Я бачу лікаря.** (I see the doctor.)

These questions form the foundation of this checkpoint. Match some common situations to test your memory.

:::quiz
title: "What do you say?"
---
- q: "You want to order coffee:"
  o: ["Мені каву, будь ласка.", "Скільки коштує?", "Тут вільно?"]
  a: 0
- q: "You ask for the price:"
  o: ["Скільки коштує?", "Можна карткою?", "Що ви рекомендуєте?"]
  a: 0
- q: "You want to pay with a card:"
  o: ["Можна карткою?", "Рахунок, будь ласка.", "Дорого!"]
  a: 0
- q: "You ask for the bill:"
  o: ["Рахунок, будь ласка.", "Мені борщ.", "Все було дуже смачно!"]
  a: 0
- q: "You ask for 1 kg of apples:"
  o: ["Дайте кілограм яблук.", "Скільки коштує?", "Можна меню?"]
  a: 0
- q: "You think the price is high:"
  o: ["Дорого!", "Дешево!", "Нормальна ціна."]
  a: 0
- q: "You ask if a seat is free:"
  o: ["Тут вільно?", "Можна меню?", "Рахунок, будь ласка."]
  a: 0
- q: "You compliment the food:"
  o: ["Все було дуже смачно!", "Можна карткою?", "Це гостре?"]
  a: 0
:::

## Читання (Reading Practice)

These skills come together in everyday scenarios. Read the story about Anna’s morning. She visits the market, goes to a cafe, and meets some friends. Pay attention to how the nouns change their endings when they are the object of her actions (accusative case).

**Ранок Анни** (Anna's morning)

Сьогодні субота. (Today is Saturday.) Анна йде на ринок. (Anna goes to the market.) Вона хоче купити продукти. (She wants to buy groceries.)

Анна любить фрукти. (Anna loves fruits.) Вона купує яблука. (She buys apples.)
<div class="dialogue">


**Анна:** Добрий день! Скільки коштують яблука? *(Good day! How much do the apples cost?)*


**Продавець:** П'ятдесят гривень. *(Fifty hryvnias.)*


**Анна:** Дайте кілограм яблук, будь ласка. *(Give me a kilogram of apples, please.)*


</div>


Потім Анна йде у кафе. (Then Anna goes to the cafe.) Вона хоче обідати. (She wants to have lunch.)
<div class="dialogue">


**Анна:** Добрий день! Тут вільно? *(Good day! Is it free here?)*


**Офіціант:** Так, сідайте, будь ласка. Ось меню. *(Yes, sit down, please. Here's the menu.)*


**Анна:** Мені борщ і каву з молоком. *(Borscht and coffee with milk for me.)*


**Офіціант:** Це все? *(Is that all?)*


**Анна:** Так, дякую. *(Yes, thank you.)*


</div>


Анна їсть борщ. (Anna eats borscht.) Вона п'є каву з молоком. (She drinks coffee with milk.) Все було дуже смачно! (Everything was very tasty!)
<div class="dialogue">


**Анна:** Рахунок, будь ласка. Можна карткою? *(The bill, please. Can I pay with a card?)*


**Офіціант:** Так, звичайно. *(Yes, of course.)*


</div>


Раптом Анна бачить Олену і Тараса. (Suddenly Anna sees Olena and Taras.)
<div class="dialogue">


**Анна:** Олено, привіт! *(Olena, hi!)*


**Олена:** Привіт, Анно! Це мій брат. *(Hi, Anna! This is my brother.)*


**Анна:** Дуже приємно! Я знаю твого брата. Ми працюємо разом! *(Very nice! I know your brother. We work together!)*


</div>


Notice how Anna uses **борщ** without changes, but she says **каву** because the feminine word **кава** takes the **-у** ending in the accusative case. Later, she sees **Олену** (feminine person) and knows **брата** (masculine person).

## Граматика (Grammar Summary)

The core grammar rules in this phase focus on mastering the accusative case (the direct object) for both things and people, along with practical phrases for the market and the cafe.

**1. Meals and Food Vocabulary**
You can now discuss your daily eating routines. The main meals are **сніданок** (breakfast), **обід** (lunch), and **вечеря** (dinner).
*   **Я їм суп на обід.** (I eat soup for lunch.)
*   **Я люблю сир.** (I love cheese.)

**2. Accusative Case for Inanimate Objects (Що? / What?)**
When a non-living thing is the direct object of verbs like **їсти** (to eat), **пити** (to drink), or **купувати** (to buy), it takes the accusative case.
*   **Masculine:** Stays the same as the dictionary form.
    *   **Я їм борщ.** (I eat borscht.)
    *   **Я купую хліб.** (I buy bread.)
*   **Feminine:** The ending **-а** changes to **-у**.
    *   **Я п'ю воду.** (I drink water. From **вода**)
    *   **Я їм піцу.** (I eat pizza. From **піца**)

**3. Ordering Food**
Order politely by using **мені** (to me) plus the accusative case.
*   **Мені салат і каву, будь ласка.** (Salad and coffee for me, please.)

**4. Shopping and Prices**
To ask the price, use **Скільки коштує?** (for one item) or **Скільки коштують?** (for multiple items).
*   **Скільки коштує сік?** (How much does the juice cost?)
*   **Тридцять гривень.** (Thirty hryvnias.)

Remember the forms of the currency: **одна гривня** (1), **дві гривні** (2-4), **п'ять гривень** (5+).

**5. Accusative Case for Animate Objects (Кого? / Whom?)**
When the direct object is a person or an animal, the rules change for masculine nouns. We ask **кого?** (whom?).
*   **Feminine:** Still changes **-а** to **-у**, exactly like objects.
    *   **Я бачу маму.** (I see mom. From **мама**)
    *   **Я знаю Олену.** (I know Olena. From **Олена**)
*   **Masculine:** Takes the ending **-а** or **-я**.
    *   **Я бачу брата.** (I see the brother. From **брат**)
    *   **Я чекаю лікаря.** (I wait for the doctor. From **лікар**)

**6. Important Conversational Chunks**
You also learned some highly useful fixed phrases.
*   **Кава з молоком** (Coffee with milk). The word **з** means "with."
*   **Кілограм яблук** (A kilogram of apples). After words of quantity, we use a special plural form.

Sort these accusative forms based on whether they answer the question **що?** (what - inanimate) or **кого?** (whom - animate).

:::group-sort
title: "Sort accusative forms: inanimate (що?) vs animate (кого?)"
---
groups:
  - name: "Inanimate (що?)"
    items: ["борщ", "хліб", "сік", "чай", "сир"]
  - name: "Animate (кого?)"
    items: ["брата", "лікаря", "сусіда", "друга", "вчителя"]
:::

Test your precision with these accusative endings. Check if the noun is a thing or a person to select the correct form.

:::quiz
title: "Accusative check: choose correct form for inanimate AND animate nouns"
---
- q: "Я їм ___."
  o: ["салат", "салата", "салату"]
  a: 0
- q: "Я бачу ___."
  o: ["брата", "брат", "брату"]
  a: 0
- q: "Я п'ю ___."
  o: ["воду", "вода", "води"]
  a: 0
- q: "Я знаю ___."
  o: ["Олену", "Олена", "Олени"]
  a: 0
- q: "Я люблю ___."
  o: ["борщ", "борщем", "борщу"]
  a: 0
- q: "Я чекаю ___."
  o: ["друга", "друг", "другу"]
  a: 0
- q: "Я купую ___."
  o: ["хліб", "хліба", "хлібу"]
  a: 0
- q: "Я бачу ___."
  o: ["лікаря", "лікар", "лікарю"]
  a: 0
- q: "Я їм ___."
  o: ["піцу", "піца", "піци"]
  a: 0
- q: "Я люблю ___."
  o: ["маму", "мама", "мами"]
:::

## Діалог (Connected Dialogue)

This fast-paced dialogue connects all of these situations. Two friends talk about their day, run errands, and grab a bite to eat.

<div class="dialogue">


**Марк:** Що ти їш на сніданок? *(What do you eat for breakfast?)*


**Денис:** Я їм кашу і п'ю каву з молоком. *(I eat porridge and drink coffee with milk.)*


**Марк:** А що ти робиш потім? *(And what do you do later?)*


**Денис:** Потім іду на ринок. *(Then I go to the market.)*


**Денис:** Добрий день! Скільки коштують помідори? *(Good day! How much do the tomatoes cost?)*


**Продавець:** Тридцять гривень. *(Thirty hryvnias.)*


**Денис:** Дайте кілограм, будь ласка. *(Give me a kilogram, please.)*


**Марк:** А де ти обідаєш? *(And where do you have lunch?)*


**Денис:** Потім у кафе. Мені борщ і воду, будь ласка. *(Then in the cafe. Borscht and water for me, please.)*


**Денис:** О, я бачу Олену! Олено, привіт! *(Oh, I see Olena! Olena, hi!)*


**Олена:** Привіт, Денисе! *(Hi, Denys!)*


**Денис:** Ти знаєш мого брата? *(Do you know my brother?)*


</div>


This conversation flows naturally from talking about breakfast routines to executing a transaction at a market, ordering food, and finally greeting a friend and introducing someone. Notice how the dialogue moves across different locations and social situations smoothly, mirroring how you will use these phrases in the real world.

Lock in your understanding of this dialogue with a fill-in exercise.

:::fill-in
title: "Complete the cafe + market dialogue with correct forms"
---
- sentence: "— Що ти їш на сніданок? — Я їм ___ і п'ю каву."
  answer: "кашу"
- sentence: "— Потім іду на ринок. Скільки ___ помідори?"
  answer: "коштують"
- sentence: "— Тридцять ___."
  answer: "гривень"
- sentence: "— Дайте ___ яблук, будь ласка."
  answer: "кілограм"
- sentence: "— Потім у кафе: ___ борщ і воду, будь ласка."
  answer: "Мені"
- sentence: "— Рахунок, будь ласка. Можна ___?"
  answer: "карткою"
- sentence: "— О, я бачу ___! Олено, привіт!"
  answer: "Олену"
- sentence: "— Ти знаєш мого ___?"
  answer: "брата"
:::

## Підсумок — Summary

The skills from this phase are essential for daily life in a Ukrainian-speaking environment.

You can now confidently talk about food and drinks. You understand how the accusative case works—not just for inanimate things like a bowl of borscht, but also for people you meet and interact with. You know the exact phrases to order at a cafe, ask for the bill, and pay with a card. You can shop at a market, ask for prices, and understand the difference between **одна гривня**, **дві гривні**, and **п'ять гривень**.

These are practical conversational tools. Practice using them in your head whenever you go grocery shopping or sit down for a meal. By consistently building these sentences, you will start thinking in Ukrainian rather than translating from English.

Next up is Phase A1.7, where the focus shifts entirely to communication. You will learn how to talk on the phone, write short emails, and make plans with friends.

**Deterministic word count: 1335 words** (calculated by pipeline, do NOT estimate manually)

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

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
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

Verified: 140 words | Not found: 11 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Анни — NOT IN VESUM
  ✗ Анно — NOT IN VESUM
  ✗ Денис — NOT IN VESUM
  ✗ Денисе — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олени — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Олену — NOT IN VESUM
  ✗ Тараса — NOT IN VESUM

All 140 other words are confirmed to exist in VESUM.

</vesum_verification>