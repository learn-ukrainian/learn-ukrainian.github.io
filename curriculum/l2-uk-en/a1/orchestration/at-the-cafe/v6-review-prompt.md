<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 38: At the Cafe (A1, A1.6 [Food and Shopping])
**Writer:** Gemini
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
dialogue_situations:
- setting: 'A date at a cozy Lviv café — ordering from the menu: кава (f, coffee),
    чай (m, tea), тістечко (n, pastry), круасан (m, croissant), вода (f, water), сік
    (m, juice). Мені каву, будь ласка. А мені — чай і тістечко.'
  speakers:
  - Ростик
  - Іванка
  motivation: Ordering with кава(f), чай(m), тістечко(n), круасан(m)
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

A Ukrainian cafe is a good place to practice short, polite phrases right away. Start with a greeting, listen to the waiter's question, and answer with one clear ordering formula.

> У неділю ми йдемо в **кафе** (cafe). **Офіціант** (waiter) несе **меню** (menu). Ми читаємо меню. Ми замовляємо каву. Ми кажемо "**будь ласка**" (please) і "дякую". Це дуже важливо.
> *On Sunday we go to a cafe. The waiter brings the menu. We read the menu. We order coffee. We say "please" and "thank you". This is very important.*

Imagine a relaxing date at a cozy, dimly lit Lviv café. The air smells of freshly roasted beans. Rostyk and Ivanka sit at a comfortable table near the large window. The waiter approaches to take their order. They will look at the menu, discuss the options, and order coffee, traditional borsch, and a fresh pastry.

> **Офіціант:** Добрий день! Ось меню. *(Good day! Here is the menu.)*
> **Ростик:** Дякую. Що ви рекомендуєте? *(Thank you. What do you recommend?)*
> **Офіціант:** Борщ дуже смачний. Сьогодні також є свіжі салати. *(The borsch is very delicious. Today there are also fresh salads.)*
> **Ростик:** Добре, мені борщ і хліб, будь ласка. *(Good, borsch and bread for me, please.)*
> **Офіціант:** А що будете пити? *(And what will you drink?)*
> **Іванка:** Мені каву з молоком, будь ласка. А ще круасан. *(Coffee with milk for me, please. And also a croissant.)*
> **Офіціант:** Добре, одну хвилинку. *(Good, one minute.)*

Notice how Rostyk and Ivanka order their food. Instead of using complex verbs, they rely on a simple and polite pattern: the word **мені** (to/for me) followed by the item they want in the accusative case. They also use the key question **Що ви рекомендуєте?** (What do you recommend?) to ask the waiter for advice. This straightforward approach helps you sound polite and natural without needing advanced grammar.

After enjoying a pleasant meal and a long conversation, it is time to conclude the date. Rostyk gets the attention of the waiter to ask for the total cost. He will check if he can use his bank card, and Ivanka will make sure to compliment the chef's work before they leave.

> **Ростик:** Рахунок, будь ласка. *(The bill, please.)*
> **Офіціант:** Ось, будь ласка. Сто двадцять гривень. *(Here you go, please. One hundred twenty hryvnias.)*
> **Ростик:** Можна карткою? *(Can I pay by card?)*
> **Офіціант:** Так, звичайно. Ось ваш чек. *(Yes, of course. Here is your receipt.)*
> **Іванка:** Дякую, дуже смачно було! *(Thank you, it was very delicious!)*
> **Офіціант:** Дякуємо, приходьте ще! *(We thank you, come again!)*

When the meal is finished, you must ask for the bill directly. You then confirm your payment method. Finally, it is always polite to leave a sincere compliment about the food before you depart from the table.

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Як замовити (How to Order)

There are several core request formulas you can use when ordering at a cafe. The most versatile and polite approach is to use the phrase **Можна мені, будь ласка, ...?** (Can I please have...?). Another common and direct way to state your choice is to say **Я буду...** (I will have...) or **Я хочу...** (I want...). These phrases function as simple, prefabricated chunks of language that allow you to express exactly what you desire without worrying about complicated verb conjugations in the moment.

> Я приходжу в кафе. Я хочу **замовляти** (to order) їжу. Я читаю меню. Я вибираю гарячий суп і холодну воду. Офіціант питає: "Що будете замовляти?" Я кажу: "Мені воду і суп, будь ласка."
> *I arrive at the cafe. I want to order food. I read the menu. I choose hot soup and cold water. The waiter asks: "What will you be ordering?" I say: "Water and soup for me, please."*

Whenever you ask for a specific item using the patterns above, you must place the noun in the accusative case. This is because the food or drink is the direct object of your request. You learned the accusative case rules in Module 37, and a cafe is the perfect place to practice them in a real application. Feminine nouns ending in **-а** change to **-у**, while masculine and neuter inanimate nouns remain the same as their dictionary forms. Here are practical examples:

* **Мені каву, будь ласка.** (Coffee for me, please.) — from **кава**.
* **Можна воду?** (Can I have water?) — from **вода**.
* **Дайте, будь ласка, піцу.** (Give me pizza, please.) — from **піца**.
* **Я буду борщ.** (I will have borsch.) — from **борщ** (masculine, no change).
* **Я хочу салат.** (I want a salad.) — from **салат** (masculine, no change).

Before you make your final decision, you might need to ask the staff a few questions about the dishes. You can easily inquire about ingredients, prices, or dietary options using short questions. The verb **рекомендувати** (to recommend) is very useful in these situations. Here are the most useful phrases for inquiring about the menu:

* **Що ви рекомендуєте?** (What do you recommend?)
* **Це гостре?** (Is it **гостре** — spicy?)
* **Це з м'ясом?** (Is it with meat?)
* **А що це?** (What is this?)
* **Скільки коштує?** (How much does it cost?)
* **Є вегетаріанське меню?** (Is there a **вегетаріанський** — vegetarian menu?)
* **Можна меню, будь ласка?** (Can I have the menu, please?)

When you want to say "to order" in Ukrainian, the standard verbs are **замовляти** (imperfective) and **замовити** (perfective). This is a crucial point for building authentic language skills from the very beginning.

:::caution
**Decolonization Note: Avoid Russianisms**
You might occasionally hear people use the verb **заказати** when referring to ordering food. This is a direct calque (Russianism) and is incorrect in standard Ukrainian. Always use the authentic Ukrainian verbs **замовляти / замовити** when you want to order a meal, a drink, or a service.
:::

Finally, if you are buying a drink or a quick snack at a counter, the barista will almost certainly ask you one highly frequent question: **Вам тут чи з собою?** (For here or to go?). You only need to remember two simple replies for this situation.

* **Тут.** (Here.)
* **З собою.** (To go.)

:::tip
**Listening Comprehension**
When standing at the counter, the barista might speak quickly. Listen closely for the word **тут** (here) or **з собою** (with oneself / to go). Answering with a single word is perfectly polite in a fast-paced environment.
:::

<!-- INJECT_ACTIVITY: fill-in-accusative -->

## Культура кафе (Cafe Culture)

Understanding local customs is just as important as knowing the vocabulary. In Ukraine, there is a distinct difference in formality between a **кафе** and a **ресторан** (restaurant). A cafe is generally casual, perfect for a quick coffee, a sweet pastry, or a light lunch. A restaurant is more formal and is typically meant for a full dinner experience. It is important to note that many common food-related words in Ukrainian are internationalisms borrowed from French and other languages. Words like **кафе**, **меню**, and **десерт** will sound familiar to you. Furthermore, **кафе** and **меню** are indeclinable nouns; they never change their endings, regardless of their role in the sentence.

> Українські кафе дуже затишні. Люди часто п'ють каву або чай. Вони розмовляють або працюють там. Час платити. Ми просимо **рахунок** (bill). Все дуже **смачно** (delicious). Ми залишаємо чайові.
> *Ukrainian cafes are very cozy. People often drink coffee or tea. They talk or work there. It is time to pay. We ask for the bill. Everything is very delicious. We leave a tip.*

When you enter a busy venue, you may need to ask if a table or an empty chair is available. You can simply ask, **Тут вільно?** (Is this seat free?) or just **Вільно?** (Is it free?). Once you are seated, the waiter will usually bring the menu to your table. If they are busy and do not see you immediately, or if the menu is not already on the table, you should politely ask for it by saying: **Можна меню?** (Can I have the menu?). You do not need to wait passively.

You can easily customize your drinks using the preposition **без** (without) with the genitive case, or **з** (with) with the instrumental case. If you need a refill, you simply ask for one more.

* **Ще одну каву, будь ласка.** (One more coffee, please.)
* **Чай без цукру.** (Tea without sugar.)
* **Вода з лимоном.** (Water with lemon.)

When you finish your meal, it is a wonderful gesture to praise the food. Instead of attempting a literal, unnatural translation of an English compliment, you should use the standard Ukrainian phrase: **Все було дуже смачно!** (Everything was very delicious!) or simply say that the food is **смачно**.

When you are ready to pay, it will not be brought to you automatically at the end of the meal. You say: **Рахунок, будь ласка** (The bill, please). The staff will often ask you how you prefer to pay: **Картка чи готівка?** (Card or cash?). Most modern places in Ukraine easily accept cards, so you can confidently ask: **Можна карткою?** (Can I pay by **картка** — card?). If you prefer paper money, you use **готівка** (cash). Finally, leaving **чайові** (tips) is a common practice to show your appreciation for good service. While not strictly obligatory, leaving around ten percent of the total bill is the standard custom in cafes and restaurants.

:::note
**Payment Etiquette**
Unlike in some countries where the tip is automatically added or written on the receipt, tipping in Ukraine is usually handled separately. You can leave the tip in cash on the table or ask the waiter to add it to the card terminal before you tap.
:::

<!-- INJECT_ACTIVITY: quiz-situations -->
<!-- INJECT_ACTIVITY: match-up-phrases -->

## Підсумок — Summary

You now have the essential cafe communication toolkit to comfortably navigate dining out in Ukrainian. You know how to politely place an order using the reliable pattern **Мені [accusative], будь ласка** or by stating **Я буду [accusative]**. You also have the vocabulary to inquire about the menu before making a choice, asking crucial questions such as **Скільки коштує?** (How much does it cost?), **Що рекомендуєте?** (What do you recommend?), and checking if a dish is suitable by asking **Є вегетаріанське меню?** or **Це гостре?**.

> Я дуже люблю українську їжу. Ми часто їмо в кафе. Я завжди замовляю гарячий суп. Мій друг замовляє свіжий салат. Все дуже смачно.
> *I really love Ukrainian food. We often eat at cafes. I always order hot soup. My friend orders fresh salad. Everything is very delicious.*

Beyond just ordering, you are prepared to complete the entire dining experience gracefully. You understand the culture of paying the bill and the importance of asking **Рахунок, будь ласка** when you are ready to pay. You can confirm your payment method by asking **Можна карткою?** instead of relying entirely on cash. Most importantly, you know how to leave a warm, culturally appropriate compliment by telling the staff **Дуже смачно!** to show your appreciation for their hard work.

Use this practical self-check checklist to verify your readiness before you visit a real Ukrainian coffee shop. Read each question carefully and try to formulate the answer in your head before looking at the solution. Practice these functional phrases aloud multiple times until they feel completely natural and effortless to you.

*   **Q: How do you order coffee and a croissant?**
    **A:** Мені каву і круасан, будь ласка.
*   **Q: How do you ask if a dish is spicy?**
    **A:** Це гостре?
*   **Q: How do you ask for the bill?**
    **A:** Рахунок, будь ласка.
*   **Q: How do you say you want to pay by card?**
    **A:** Можна карткою?
*   **Q: How do you compliment the food?**
    **A:** Все було дуже смачно!
</generated_module_content>

**PIPELINE NOTE — Word count: 1818 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 126 words | Not found: 2 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іванка — NOT IN VESUM
  ✗ Ростик — NOT IN VESUM

All 126 other words are confirmed to exist in VESUM.

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
