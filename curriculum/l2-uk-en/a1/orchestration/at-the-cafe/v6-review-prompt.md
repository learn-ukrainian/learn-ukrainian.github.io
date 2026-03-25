# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 38: At the Cafe (A1, A1.6 [Food and Shopping])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-038
level: A1
sequence: 38
slug: at-the-cafe
version: '1.2'
title: At the Cafe
subtitle: У кафе — ordering, paying, and cafe culture
focus: communication
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Order food and drinks at a Ukrainian cafe
- Use polite request phrases (Можна...? Дайте, будь ласка...)
- Read a simple Ukrainian menu and ask about items
- Understand Ukrainian cafe culture (tipping, paying)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Ordering at a cafe: — Добрий день! Ось меню. — Дякую. Що ви рекомендуєте?
    — Борщ дуже смачний. — Добре, мені борщ і хліб, будь ласка. — А що будете пити?
    — Каву з молоком. — Добре, одну хвилинку. Polite ordering with будь ласка, мені
    + accusative.'
  - 'Dialogue 2 — Paying the bill: — Рахунок, будь ласка. — Ось, будь ласка. Сто двадцять
    гривень. — Можна карткою? — Так, звичайно. — Дякую, дуже смачно було! — Дякуємо,
    приходьте ще! Paying, complimenting food, tipping.'
- section: Як замовити (How to Order)
  words: 300
  points:
  - 'Ordering patterns: Мені [accusative], будь ласка. (Мені каву, будь ласка.) Можна
    [accusative]? (Можна воду?) Дайте, будь ласка, [accusative]. (Дайте, будь ласка,
    борщ.) Я хочу / Я буду [accusative]. (Я буду салат.) All use accusative from M37
    — real application.'
  - 'Asking about the menu: Що ви рекомендуєте? (What do you recommend?) Це гостре?
    (Is it spicy?) Це з м''ясом? (Is it with meat?) А що це? (What is this?) Скільки
    коштує? (How much?) Є вегетаріанське меню? (Is there a vegetarian menu?)'
- section: Культура кафе (Cafe Culture)
  words: 300
  points:
  - 'Ukrainian cafe culture: Кафе vs ресторан: кафе is casual, ресторан is formal.
    Меню: the waiter brings it, or it''s on the wall/board. Рахунок: ask for the bill
    — it doesn''t come automatically. Чайові (tips): 10% is standard, not obligatory.
    Карткою чи готівкою? (Card or cash?) — most places take cards.'
  - 'Useful cafe phrases: Вільно? / Тут вільно? (Is this seat free?) Можна меню? (Can
    I have the menu?) Ще одну каву, будь ласка. (One more coffee, please.) Без цукру.
    (Without sugar.) З лимоном. (With lemon.) Все було дуже смачно! (Everything was
    delicious!)'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Cafe communication toolkit: Order: Мені [accusative], будь ласка. Ask: Скільки
    коштує? Що рекомендуєте? Pay: Рахунок, будь ласка. Можна карткою? Compliment:
    Дуже смачно! Self-check: Order a full meal (starter, main, drink) at a cafe. Ask
    for the bill and pay.'
vocabulary_hints:
  required:
  - кафе (cafe, n, indecl.)
  - меню (menu, n, indecl.)
  - рахунок (bill, m)
  - замовляти (to order)
  - офіціант (waiter, m)
  - смачно (delicious — adverb)
  - будь ласка (please)
  recommended:
  - ресторан (restaurant, m)
  - рекомендувати (to recommend)
  - чайові (tip/gratuity, pl.)
  - готівка (cash, f)
  - картка (card, f)
  - гостре (spicy — neuter adj.)
  - вегетаріанський (vegetarian — adj.)
activity_hints:
- type: fill-in
  focus: 'Order at a cafe: Мені ___, будь ласка. (choose correct accusative)'
  items:
  - Мені {каву|кава|каві}, будь ласка.
  - Мені {воду|вода|водою}, будь ласка.
  - Мені {борщ|борщу|борщем}, будь ласка.
  - Мені {салат|салату|салатом}, будь ласка.
  - Мені {суп|супу|супом}, будь ласка.
  - Дайте, будь ласка, {чай|чаю|чаєм}.
  - Я буду {піцу|піца|піці}.
  - Можна {хліб|хліба|хлібом}?
- type: quiz
  focus: What do you say? Match situation to phrase (order/pay/ask/compliment)
  items:
  - question: You want to order coffee. What do you say?
    options:
    - Мені каву, будь ласка.
    - Рахунок, будь ласка.
    - Що ви рекомендуєте?
  - question: You want to pay. What do you say?
    options:
    - Рахунок, будь ласка.
    - Можна меню?
    - Це гостре?
  - question: You want to know the price. What do you say?
    options:
    - Скільки коштує?
    - Це з м'ясом?
    - Тут вільно?
  - question: You want to ask for a recommendation. What do you say?
    options:
    - Що ви рекомендуєте?
    - Є вегетаріанське меню?
    - Все було дуже смачно!
  - question: You want to praise the food. What do you say?
    options:
    - Все було дуже смачно!
    - Можна карткою?
    - Без цукру.
  - question: You want to know if a seat is free. What do you say?
    options:
    - Тут вільно?
    - Ще одну каву, будь ласка.
    - Рахунок, будь ласка.
  - question: You want to ask if the dish is spicy. What do you say?
    options:
    - Це гостре?
    - Це з м'ясом?
    - Скільки коштує?
  - question: You want to pay by card. What do you say?
    options:
    - Можна карткою?
    - Є вегетаріанське меню?
    - Що ви рекомендуєте?
- type: fill-in
  focus: Complete the cafe dialogue with correct phrases
  items:
  - — Добрий день! Ось {меню|рахунок|картка}.
  - — Дякую. Що ви {рекомендуєте|коштуєте|платите}?
  - — Борщ дуже {смачний|гострий|вільний}.
  - — Добре, {мені|я|мене} борщ і хліб, будь ласка.
  - — А що будете {пити|їсти|читати}?
  - — Каву з молоком. — Добре, одну {хвилинку|годину|каву}.
- type: match-up
  focus: Match Ukrainian cafe phrases with their functions
  items:
  - Рахунок, будь ласка.: Asking for the bill
  - Що ви рекомендуєте?: Asking for advice
  - Мені борщ, будь ласка.: Ordering food
  - Скільки коштує?: Asking the price
  - Можна карткою?: Asking about payment method
  - Дуже смачно!: Complimenting the food
  - Тут вільно?: Asking for a seat
  - Можна меню?: Asking to see the options
connects_to:
- a1-039 (Shopping)
prerequisites:
- a1-037 (I Eat, I Drink)
grammar:
- Мені + accusative (ordering pattern)
- Можна + accusative (polite request)
- 'Review: accusative inanimate from M37'
register: розмовний
references:
- title: ULP Season 1, Episodes 11-12
  url: https://www.ukrainianlessons.com/episode11/
  notes: Ordering at a cafe, restaurant vocabulary.
- title: State Standard 2024, Topic 3 (ресторан)
  notes: 'Communicative situation: ordering food and drinks.'

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Walking into a Ukrainian **кафе** (cafe) is a wonderful experience. Whether you are grabbing a quick morning coffee or sitting down for a full meal, knowing the right phrases will make the interaction smooth and polite. In this module, we will learn how to ask for a table, order food and drinks, and pay the bill. 

Let us start by listening in on two typical conversations. Read through the first dialogue, where a customer is ready to order. Pay attention to how the customer politely asks for recommendations and requests specific items.

<div class="dialogue">


**Офіціант:** Добрий день! Ось меню. *(Good day! Here is the menu.)*


**Клієнт:** Дякую. Що ви рекомендуєте? *(Thank you. What do you recommend?)*


**Офіціант:** Борщ дуже смачний. *(The borscht is very delicious.)*


**Клієнт:** Добре, мені борщ і хліб, будь ласка. *(Good, borscht and bread for me, please.)*


**Офіціант:** А що будете пити? *(And what will you drink?)*


**Клієнт:** Каву з молоком. *(Coffee with milk.)*


**Офіціант:** Добре, одну хвилинку. *(Good, one minute.)*


</div>

In this exchange, the **офіціант** (waiter) hands over the **меню** (menu). The customer uses the extremely useful phrase **Що ви рекомендуєте?** (What do you recommend?) to get a suggestion. When it is time to **замовляти** (to order), the customer uses the pattern **мені... будь ласка** (for me... please). Notice that **кава** (coffee) changes to **каву** because it is the direct object of the order (the accusative case, which we will review in the next section). 

Now, let us look at the second dialogue. The meal is finished, and the customer is ready to pay and leave.

<div class="dialogue">


**Клієнт:** Рахунок, будь ласка. *(The bill, please.)*


**Офіціант:** Ось, будь ласка. Сто двадцять гривень. *(Here you go, please. One hundred twenty hryvnias.)*


**Клієнт:** Можна карткою? *(Is it possible by card?)*


**Офіціант:** Так, звичайно. *(Yes, of course.)*


**Клієнт:** Дякую, дуже смачно було! *(Thank you, it was very delicious!)*


**Офіціант:** Дякуємо, приходьте ще! *(We thank you, come again!)*


</div>

To finish the meal, the customer asks for the **рахунок** (bill). This is a crucial word to know, as the bill is rarely brought to your table automatically in Ukraine; you must ask for it. The customer then asks **Можна карткою?** (Can I pay by card?), which is widely accepted. Finally, it is always polite to compliment the chef by saying that the food was **смачно** (delicious). 

Take a moment to read through these dialogues again out loud. These are the exact phrases you will hear and use in any Ukrainian cafe or restaurant.

:::fill-in
title: "Complete the cafe dialogue with correct phrases"
---
- — Добрий день! Ось {меню|рахунок|картка}.
- — Дякую. Що ви {рекомендуєте|коштуєте|платите}?
- — Борщ дуже {смачний|гострий|вільний}.
- — Добре, {мені|я|мене} борщ і хліб, будь ласка.
- — А що будете {пити|їсти|читати}?
- — Каву з молоком. — Добре, одну {хвилинку|годину|каву}.
:::

## Як замовити (How to Order)

Now that we have seen how a typical cafe interaction flows, let us break down the exact grammar and phrasing you need to order your food. 

When you want to order something, you cannot simply use the dictionary form of the word. Because you are asking for an object, that object must be in the accusative case. If you recall from our previous modules, inanimate masculine and neuter nouns do not change their endings in the accusative case. However, feminine nouns ending in **-а** change to **-у**. 

Here are the four most common and natural patterns for ordering food or drinks. All of them require the accusative case for the item you are ordering.

**Pattern 1: Мені [accusative], будь ласка**
This translates literally to "To me [item], please." It is the most common, polite, and natural way to order in a cafe.
*   **Мені каву, будь ласка.** (Coffee for me, please.)
*   **Мені борщ, будь ласка.** (Borscht for me, please.)
*   **Мені салат і воду, будь ласка.** (Salad and water for me, please.)

**Pattern 2: Можна [accusative]?**
This translates to "Is it possible [to have an item]?" or "May I have [item]?" It is very polite and often used for small requests.
*   **Можна воду?** (May I have water?)
*   **Можна хліб?** (May I have bread?)
*   **Можна меню?** (May I have the menu?)

**Pattern 3: Дайте, будь ласка, [accusative]**
This means "Give [me], please, [item]." While "give" might sound a bit direct in English, in Ukrainian, as long as you add **будь ласка** (please), it is perfectly polite and standard.
*   **Дайте, будь ласка, борщ.** (Give me the borscht, please.)
*   **Дайте, будь ласка, чай.** (Give me tea, please.)
*   **Дайте, будь ласка, суп.** (Give me soup, please.)

**Pattern 4: Я хочу / Я буду [accusative]**
You can also use verbs directly. **Я хочу** means "I want," and **я буду** means "I will [have]." 
*   **Я хочу піцу.** (I want pizza.)
*   **Я буду салат.** (I will have a salad.)
*   **Я буду воду.** (I will have water.)

:::fill-in
title: "Order at a cafe"
---
- Мені {каву|кава|каві}, будь ласка.
- Мені {воду|вода|водою}, будь ласка.
- Мені {борщ|борщу|борщем}, будь ласка.
- Мені {салат|салату|салатом}, будь ласка.
- Мені {суп|супу|супом}, будь ласка.
- Дайте, будь ласка, {чай|чаю|чаєм}.
- Я буду {піцу|піца|піці}.
- Можна {хліб|хліба|хлібом}?
:::

### Asking Questions About the Menu

Sometimes you need more information before you decide what to order. The menu might have unfamiliar dishes, or you might have dietary preferences. Here are the essential questions you can ask the waiter to make sure you get exactly what you want.

If you are unsure what to choose, you can always ask for a recommendation:
*   **Що ви рекомендуєте?** (What do you recommend?)

If you see an unfamiliar word on the menu, you can simply point and ask:
*   **А що це?** (And what is this?)

If you want to know the price of an item:
*   **Скільки коштує?** (How much does it cost?)

If you have specific preferences about the food itself, you can ask yes/no questions using **це** (this):
*   **Це гостре?** (Is this spicy?)
*   **Це з м'ясом?** (Is this with meat?)

And if you do not eat meat at all, you can ask for a **вегетаріанський** (vegetarian) option:
*   **Є вегетаріанське меню?** (Is there a vegetarian menu?)

By combining your ordering patterns with these questions, you can navigate any dining situation with confidence. You can ask if a dish is spicy, confirm the price, and then confidently say **Мені борщ, будь ласка**.

## Культура кафе (Cafe Culture)

Dining out in Ukraine comes with its own set of cultural norms and expectations. Understanding the difference between a cafe and a **ресторан** (restaurant), as well as knowing how to navigate seating, paying, and tipping, will help you feel like a local.

First, let us look at the venues themselves. A cafe is typically casual. It is a place where you might grab a coffee, eat a quick pastry, or have a simple lunch. A restaurant, on the other hand, is formal. It usually involves a larger menu, a host who seats you, and a longer dining experience. In many modern Ukrainian cities, the line between the two can blur, but generally, a cafe is for everyday visits.

When you walk into a casual cafe, you might need to find your own table. If you see an empty seat but are not sure if it is taken, you can point to it and ask:
*   **Вільно?** (Is it free?)
*   **Тут вільно?** (Is it free here?)

Once you sit down, you need the menu. In some cafes, the menu is written on a large board above the counter. In others, the waiter will bring it to you. If you have been seated but do not have a menu yet, you can catch the waiter's attention and ask:
*   **Можна меню?** (Can I have the menu?)

During your meal, you might want to modify your order or ask for more items. You can use the phrase **ще одну** (one more, feminine accusative) for coffee or water:
*   **Ще одну каву, будь ласка.** (One more coffee, please.)

You can also specify how you want your drinks prepared. Ukrainian cafes offer a wide variety of teas and coffees. You can use the preposition **без** (without) followed by the genitive case, or **з** (with) followed by the instrumental case:
*   **Без цукру.** (Without sugar.)
*   **З лимоном.** (With lemon.)

When you are finished eating, the most important cultural difference to remember is about the bill. In Ukraine, the waiter will almost never bring the bill to your table automatically. Doing so is considered rude, as if they are rushing you to leave. You can sit and talk for as long as you want. When you are finally ready to go, you must explicitly ask for the bill:
*   **Рахунок, будь ласка.** (The bill, please.)

When it is time to pay, you will usually be asked how you want to settle the bill. Ukraine is a highly digital society, and almost everywhere accepts card payments. You can clarify your payment method by asking:
*   **Можна карткою?** (Is it possible by card?)

If you prefer to pay with cash, the word is **готівка** (cash). You can say:
*   **Я плачу готівкою.** (I am paying with cash.)

Finally, there is the question of **чайові** (tips). Tipping in Ukraine is standard but not strictly obligatory in every single scenario. In a sit-down cafe or restaurant, it is customary to leave a 10% tip if you are happy with the service. Some high-end places might include a service charge automatically, but usually, you leave tips on the table or ask the waiter to add it to the card terminal before you tap. 

To show your appreciation for the meal, you can use the word **смачно** (delicious). It is very polite to say:
*   **Все було дуже смачно!** (Everything was very delicious!)

:::quiz
title: "What do you say?"
---
- question: "You want to order coffee. What do you say?"
  options: ["Мені каву, будь ласка.", "Рахунок, будь ласка.", "Що ви рекомендуєте?"]
  answer: 0
- question: "You want to pay. What do you say?"
  options: ["Рахунок, будь ласка.", "Можна меню?", "Це гостре?"]
  answer: 0
- question: "You want to know the price. What do you say?"
  options: ["Скільки коштує?", "Це з м'ясом?", "Тут вільно?"]
  answer: 0
- question: "You want to ask for a recommendation. What do you say?"
  options: ["Що ви рекомендуєте?", "Є вегетаріанське меню?", "Все було дуже смачно!"]
  answer: 0
- question: "You want to praise the food. What do you say?"
  options: ["Все було дуже смачно!", "Можна карткою?", "Без цукру."]
  answer: 0
- question: "You want to know if a seat is free. What do you say?"
  options: ["Тут вільно?", "Ще одну каву, будь ласка.", "Рахунок, будь ласка."]
  answer: 0
- question: "You want to ask if the dish is spicy. What do you say?"
  options: ["Це гостре?", "Це з м'ясом?", "Скільки коштує?"]
  answer: 0
- question: "You want to pay by card. What do you say?"
  options: ["Можна карткою?", "Є вегетаріанське меню?", "Що ви рекомендуєте?"]
  answer: 0
:::

## Підсумок — Summary

You now have a complete communication toolkit for dining in Ukraine. Let us review the essential phrases you will use from the moment you walk into a cafe until the moment you leave.

**Step 1: Arriving and Seating**
When you enter, you might need to check if a table is available.
*   **Тут вільно?** (Is it free here?)
*   **Можна меню?** (Can I have the menu?)

**Step 2: Asking Questions**
Before you make your choice, you can gather more information about the dishes.
*   **Що ви рекомендуєте?** (What do you recommend?)
*   **Скільки коштує?** (How much does it cost?)
*   **Це гостре?** (Is this spicy?)
*   **Є вегетаріанське меню?** (Is there a vegetarian menu?)

**Step 3: Ordering**
When you are ready, use the accusative case to confidently state what you want.
*   **Мені борщ, будь ласка.** (Borscht for me, please.)
*   **Мені каву, будь ласка.** (Coffee for me, please.)
*   **Я буду салат.** (I will have a salad.)
*   **Дайте, будь ласка, воду.** (Give me water, please.)

**Step 4: Customizing**
You can adjust your order with simple prepositional phrases.
*   **Без цукру.** (Without sugar.)
*   **З лимоном.** (With lemon.)
*   **Ще одну каву, будь ласка.** (One more coffee, please.)

**Step 5: Paying and Leaving**
Remember that you must initiate the payment process.
*   **Рахунок, будь ласка.** (The bill, please.)
*   **Можна карткою?** (Is it possible by card?)
*   **Дуже смачно!** (Very delicious!)
*   **Дякую!** (Thank you!)

:::match-up
title: "Match the phrases"
---
- left: "Рахунок, будь ласка."
  right: "Asking for the bill"
- left: "Що ви рекомендуєте?"
  right: "Asking for advice"
- left: "Мені борщ, будь ласка."
  right: "Ordering food"
- left: "Скільки коштує?"
  right: "Asking the price"
- left: "Можна карткою?"
  right: "Asking about payment method"
- left: "Дуже смачно!"
  right: "Complimenting the food"
- left: "Тут вільно?"
  right: "Asking for a seat"
- left: "Можна меню?"
  right: "Asking to see the options"
:::

**Deterministic word count: 1772 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 98 words | Not found: 0 words

All 98 other words are confirmed to exist in VESUM.

</vesum_verification>