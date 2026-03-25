# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 39: Shopping (A1, A1.6 [Food and Shopping])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-039
level: A1
sequence: 39
slug: shopping
version: '1.2'
title: Shopping
subtitle: Скільки коштує? — prices, quantities, and buying things
focus: communication
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Ask and understand prices (Скільки коштує?)
- Use Ukrainian currency (гривня, копійка) and numbers with prices
- Buy things at a shop or market using polite phrases
- Express quantities (кілограм, літр, пачка, пляшка)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At the market: — Скільки коштує кілограм яблук? — Сорок гривень.
    — А помідори? — Тридцять п''ять гривень за кілограм. — Дайте, будь ласка, два
    кілограми помідорів і кілограм яблук. — Сімдесят п''ять гривень. — Ось, будь ласка.
    Prices, quantities, polite buying at the market.'
  - 'Dialogue 2 — At the supermarket: — Вибачте, де тут хліб? — Хліб у третьому ряді.
    — А молоко? — Молоко в холодильнику, там. — Скільки коштує цей сир? — Сто двадцять
    гривень. — Дорого! А є дешевший? — Так, ось цей — вісімдесят. Navigation, asking
    prices, comparing (дорого/дешево).'
- section: Скільки коштує? (How Much?)
  words: 300
  points:
  - 'Price patterns: Скільки коштує [item]? — [number] гривень/гривні/гривня. Скільки
    коштують [plural item]? — verb agrees with plural. Currency: гривня (1), гривні
    (2-4), гривень (5+). Копійка: one hundredth of a гривня (often rounded).'
  - 'Numbers with prices (review from M12): 21 гривня, 32 гривні, 45 гривень, 100
    гривень. Дорого! (Expensive!) Дешево! (Cheap!) Нормальна ціна. (Fair price.) Є
    знижка? (Is there a discount?) За все — [total]. (Total.)'
- section: Де купити? (Where to Buy)
  words: 300
  points:
  - 'Shopping locations: магазин (shop), супермаркет (supermarket), ринок (market),
    аптека (pharmacy), крамниця (store — Ukrainian synonym for магазин). Specific:
    м''ясний відділ (meat section), молочний (dairy section).'
  - 'Quantity words: кілограм (kilogram): кілограм яблук, два кілограми помідорів.
    літр (liter): літр молока, два літри соку. пачка (pack): пачка масла, пачка чаю.
    пляшка (bottle): пляшка води, пляшка соку. буханка (loaf): буханка хліба. All
    use genitive after quantity — taught as chunks at A1.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Shopping toolkit: Ask: Скільки коштує? Де тут [item]? Buy: Дайте, будь ласка,
    [quantity] [item]. React: Дорого! / Дешево! / Добре, беру. Pay: Скільки за все?
    Можна карткою? Self-check: Buy 3 items at a market. Ask the price, choose a quantity,
    pay.'
vocabulary_hints:
  required:
  - коштувати (to cost)
  - скільки (how much/many)
  - гривня (hryvnia, f)
  - ціна (price, f)
  - магазин (shop, m)
  - ринок (market, m)
  - купувати (to buy)
  - дорого (expensive — adverb)
  - дешево (cheap — adverb)
  recommended:
  - копійка (kopeck, f)
  - кілограм (kilogram, m)
  - літр (liter, m)
  - пляшка (bottle, f)
  - пачка (pack, f)
  - знижка (discount, f)
  - супермаркет (supermarket, m)
  - гроші (money, pl.)
  - готівка (cash, f)
activity_hints:
- type: fill-in
  focus: Скільки коштує ___? — ___ гривень. (match items with prices)
  items:
  - Скільки коштує {хліб|хліба}? — Двадцять гривень.
  - Скільки коштує {вода|воду}? — Десять гривень.
  - Скільки коштує {сир|сиру}? — Сто гривень.
  - Скільки коштують {яблука|яблук}? — Сорок гривень.
  - Скільки коштують {помідори|помідорів}? — Тридцять гривень.
  - Скільки коштує {молоко|молока}? — П'ятдесят гривень.
  - Скільки коштує {сік|соку}? — Шістдесят гривень.
  - Скільки коштують {банани|бананів}? — Сімдесят гривень.
- type: quiz
  focus: 'Choose correct: 23 (гривня / гривні / гривень)'
  items:
  - question: 21 ___
    options:
    - гривня
    - гривні
    - гривень
  - question: 32 ___
    options:
    - гривні
    - гривня
    - гривень
  - question: 45 ___
    options:
    - гривень
    - гривня
    - гривні
  - question: 100 ___
    options:
    - гривень
    - гривня
    - гривні
  - question: 1 ___
    options:
    - гривня
    - гривні
    - гривень
  - question: 3 ___
    options:
    - гривні
    - гривня
    - гривень
  - question: 10 ___
    options:
    - гривень
    - гривня
    - гривні
  - question: 54 ___
    options:
    - гривні
    - гривня
    - гривень
- type: fill-in
  focus: 'At the market: Дайте ___ (кілограм/літр/пляшка) ___.'
  items:
  - Дайте {кілограм|літр|пляшку} яблук.
  - Дайте {літр|кілограм|пачку} молока.
  - Дайте {пляшку|кілограм|літр} води.
  - Дайте {пачку|літр|пляшку} чаю.
  - Дайте {буханку|літр|кілограм} хліба.
  - Дайте {кілограм|літр|пляшку} помідорів.
- type: match-up
  focus: Where do you buy it? Match item to shop type.
  items:
  - помідори: ринок
  - м'ясо: м'ясний відділ
  - сир: молочний відділ
  - хліб: крамниця
  - молоко: супермаркет
  - вода: магазин
  - кава: кафе
  - борщ: ресторан
connects_to:
- a1-040 (People Around Me)
prerequisites:
- a1-038 (At the Cafe)
grammar:
- Скільки коштує/коштують? — singular/plural agreement
- 'Currency: гривня/гривні/гривень (1/2-4/5+)'
- 'Quantity + genitive as chunks: кілограм яблук, літр молока'
register: розмовний
references:
- title: ULP Season 1, Episode 31
  url: https://www.ukrainianlessons.com/episode31/
  notes: Shopping vocabulary, prices, quantities.
- title: State Standard 2024, Topic 3 (купівля)
  notes: 'Communicative situation: shopping, prices, paying.'

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Walking into a local Ukrainian food space is a rich cultural experience. You might visit a modern, brightly lit **супермаркет** (supermarket), where everything is self-service and prices are clearly labeled on the shelves. Or you might explore a bustling, vibrant **ринок** (market), where seasonal produce is piled high on wooden tables, and interacting directly with the vendor is the only way to buy your groceries.

When you want to **купувати** (to buy) food, the interactions follow very predictable, highly useful scripts. You need to know how to ask for an item, inquire about the **ціна** (price), and complete the transaction politely without needing complex grammar.

Let us observe a typical interaction at a local fruit and vegetable stall. Notice how the customer uses the phrase **Дайте, будь ласка** (Give me, please). In Ukrainian, this is the universal, perfectly polite way to ask for something at a shop or market. It is much simpler and more direct than English equivalents like "Could I possibly have..."

<div class="dialogue">


**Покупець:** Скільки коштує кілограм яблук? *(How much does a kilogram of apples cost?)*


**Продавець:** Сорок гривень. *(Forty hryvnias.)*


**Покупець:** А помідори? *(And the tomatoes?)*


**Продавець:** Тридцять п'ять гривень за кілограм. *(Thirty-five hryvnias per kilogram.)*


**Покупець:** Дайте, будь ласка, два кілограми помідорів і кілограм яблук. *(Give me, please, two kilograms of tomatoes and a kilogram of apples.)*


**Продавець:** Сімдесят п'ять гривень. *(Seventy-five hryvnias.)*


**Покупець:** Ось, будь ласка. *(Here you go.)*


</div>

At the **ринок**, you must communicate directly to get what you need. In contrast, at a large **супермаркет**, you often need to ask for directions to find specific aisles. You might also want to compare products and express your opinion on the price before deciding.

Here is a common scenario when looking for basic staples in a larger store:

<div class="dialogue">


**Покупець:** Вибачте, де тут хліб? *(Excuse me, where is the bread here?)*


**Продавець:** Хліб у третьому ряді. *(The bread is in the third aisle.)*


**Покупець:** А молоко? *(And the milk?)*


**Продавець:** Молоко в холодильнику, там. *(The milk is in the fridge, there.)*


**Покупець:** Скільки коштує цей сир? *(How much does this cheese cost?)*


**Продавець:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*


**Покупець:** Дорого! А є дешевший? *(Expensive! Is there a cheaper one?)*


**Продавець:** Так, ось цей — вісімдесят. *(Yes, this one here is eighty.)*


</div>

Both dialogues show the absolute essentials of daily shopping: asking for a location, confirming the price, making a choice, and handling **гроші** (money).

## Скільки коштує? (How Much?)

The single most important question you will use while navigating shops in Ukraine is **Скільки коштує?** (How much does it cost?).

The verb **коштувати** (to cost) changes its form depending on whether the item you are asking about is singular or plural.

If you are asking about one item (singular), use **коштує**:
* **Скільки коштує хліб?** *(How much does the bread cost?)*
* **Скільки коштує вода?** *(How much does the water cost?)*
* **Скільки коштує сир?** *(How much does the cheese cost?)*
* **Скільки коштує молоко?** *(How much does the milk cost?)*
* **Скільки коштує сік?** *(How much does the juice cost?)*

If you are asking about multiple items (plural), use **коштують**:
* **Скільки коштують яблука?** *(How much do the apples cost?)*
* **Скільки коштують помідори?** *(How much do the tomatoes cost?)*
* **Скільки коштують банани?** *(How much do the bananas cost?)*

:::fill-in
title: "Скільки коштує чи коштують?"
---
- sentence: "Скільки коштує {хліб|хліба}? — Двадцять гривень."
- sentence: "Скільки коштує {вода|воду}? — Десять гривень."
- sentence: "Скільки коштує {сир|сиру}? — Сто гривень."
- sentence: "Скільки коштують {яблука|яблук}? — Сорок гривень."
- sentence: "Скільки коштують {помідори|помідорів}? — Тридцять гривень."
- sentence: "Скільки коштує {молоко|молока}? — П'ятдесят гривень."
- sentence: "Скільки коштує {сік|соку}? — Шістдесят гривень."
- sentence: "Скільки коштують {банани|бананів}? — Сімдесят гривень."
:::

### The Ukrainian Currency

When the vendor answers your question, they will use the national currency: the **гривня** (hryvnia). This word has a fascinating history. During the era of Kyivan Rus, a **гривня** was a physical silver or gold ingot used for major trade. Today, it is the paper and digital currency of independent Ukraine.

The word **гривня** changes its form based on the number that comes right before it. This is a core rule of Ukrainian counting that applies to all nouns, but it is easiest to learn with money.

* Ends in 1: use **гривня**.
* Ends in 2, 3, 4: use **гривні**.
* Ends in 5, 6, 7, 8, 9, 0, or is a teen (11-19): use **гривень**.

Let us look at some exact prices. Read the numbers and notice how the currency ending shifts to match the final digit:
* **Одна гривня.** *(One hryvnia.)*
* **Дві гривні.** *(Two hryvnias.)*
* **Двадцять одна гривня.** *(Twenty-one hryvnias.)*
* **Тридцять дві гривні.** *(Thirty-two hryvnias.)*
* **Сорок п'ять гривень.** *(Forty-five hryvnias.)*
* **Сто гривень.** *(One hundred hryvnias.)*

The smaller unit of money is the **копійка** (kopeck). One hryvnia equals one hundred kopecks. The word behaves identically to the main currency when counting:
* **Одна копійка.** *(One kopeck.)*
* **Дві копійки.** *(Two kopecks.)*
* **П'ятдесят копійок.** *(Fifty kopecks.)*

:::quiz
title: "Choose the correct currency form"
---
- q: "21 ___"
  o: ["гривня", "гривні", "гривень"]
  a: 0
- q: "32 ___"
  o: ["гривні", "гривня", "гривень"]
  a: 0
- q: "45 ___"
  o: ["гривень", "гривня", "гривні"]
  a: 0
- q: "100 ___"
  o: ["гривень", "гривня", "гривні"]
  a: 0
- q: "1 ___"
  o: ["гривня", "гривні", "гривень"]
  a: 0
- q: "3 ___"
  o: ["гривні", "гривня", "гривень"]
  a: 0
- q: "10 ___"
  o: ["гривень", "гривня", "гривні"]
  a: 0
- q: "54 ___"
  o: ["гривні", "гривня", "гривень"]
  a: 0
:::

### Reacting to Prices

Once you hear the price, you might want to express your reaction to the vendor or to your shopping companion. These adverbs act as complete statements on their own.

If something costs a lot, you say:
* **Дорого!** *(Expensive!)*

If the price is very low, you say:
* **Дешево!** *(Cheap!)*

If the price is reasonable and exactly what you expected, you can say:
* **Нормальна ціна.** *(A fair price.)*

Sometimes, especially at a market where prices are not printed on barcodes, you might want to negotiate or ask for a deal. You can politely ask:
* **Є знижка?** *(Is there a discount?)*

When you are ready to pay for everything in your basket, you ask for the total sum:
* **Скільки за все?** *(How much for everything?)*
* **За все — сто гривень.** *(For everything — one hundred hryvnias.)*

## Де купити? (Where to Buy)

Where do you go when you need groceries, medicine, or supplies? Ukraine offers a huge variety of retail experiences, from massive modern hypermarkets to tiny, specialized neighborhood shops.

You can **купувати** (to buy) items at several different types of locations:
* **супермаркет** (supermarket) — large, self-service stores with everything you need.
* **магазин** (shop) — a general word for any store.
* **крамниця** (store) — a highly authentic, traditional Ukrainian synonym for a shop.
* **ринок** (market) — an open-air or indoor market, perfect for fresh, seasonal produce.
* **аптека** (pharmacy) — where you buy medicine and health supplies.

Inside a large **супермаркет**, you navigate by sections rather than asking for items directly at a counter. If you need chicken or sausage, you look for the **м'ясний відділ** (meat section). If you need yogurt or cheese, you head to the **молочний відділ** (dairy section).

:::match-up
title: "Where do you buy it?"
---
- left: "помідори"
  right: "ринок"
- left: "м'ясо"
  right: "м'ясний відділ"
- left: "сир"
  right: "молочний відділ"
- left: "хліб"
  right: "крамниця"
- left: "молоко"
  right: "супермаркет"
- left: "вода"
  right: "магазин"
- left: "кава"
  right: "кафе"
- left: "борщ"
  right: "ресторан"
:::

### Expressing Quantities

At the market or specialized shop counters, you cannot just say "give me apples" or "give me water." You need to specify exactly how much you want using standard measurements.

In Ukrainian, words that express a specific quantity (like a kilogram, a liter, or a bottle) act as containers. The substance inside that container always takes a special grammatical form called the genitive case. At this stage, you do not need to memorize the complex rules for this case. Instead, treat these expressions as fixed, highly useful vocabulary chunks.

Learn these quantity containers and how they pair naturally with everyday products:

**Кілограм** (kilogram):
* **кілограм яблук** *(a kilogram of apples)*
* **кілограм помідорів** *(a kilogram of tomatoes)*
* **два кілограми яблук** *(two kilograms of apples)*

**Літр** (liter):
* **літр молока** *(a liter of milk)*
* **літр соку** *(a liter of juice)*
* **два літри води** *(two liters of water)*

**Пляшка** (bottle):
* **пляшка води** *(a bottle of water)*
* **пляшка соку** *(a bottle of juice)*

**Пачка** (pack):
* **пачка масла** *(a pack of butter)*
* **пачка чаю** *(a pack of tea)*

**Буханка** (loaf):
* **буханка хліба** *(a loaf of bread)*

To actually buy these items, you combine the polite request **Дайте, будь ласка** (Give me, please) with your chosen quantity chunk:
* **Дайте, будь ласка, літр молока.** *(Give me, please, a liter of milk.)*
* **Дайте, будь ласка, буханку хліба.** *(Give me, please, a loaf of bread.)*
* **Дайте, будь ласка, кілограм помідорів.** *(Give me, please, a kilogram of tomatoes.)*

Notice that when **пляшка**, **пачка**, or **буханка** follow the command to give, their ending changes to an **-у**. This happens because they are the direct objects of your request. Words ending in consonants, like **кілограм** or **літр**, stay exactly the same.

:::fill-in
title: "At the market"
---
- sentence: "Дайте {кілограм|літр|пляшку} яблук."
- sentence: "Дайте {літр|кілограм|пачку} молока."
- sentence: "Дайте {пляшку|кілограм|літр} води."
- sentence: "Дайте {пачку|літр|пляшку} чаю."
- sentence: "Дайте {буханку|літр|кілограм} хліба."
- sentence: "Дайте {кілограм|літр|пляшку} помідорів."
:::

## Підсумок — Summary

You now possess a complete, highly effective toolkit for navigating a Ukrainian shop or market. The most crucial skill is knowing how to initiate a purchase, specify what you need, and handle the final payment.

Whether you are holding physical **готівка** (cash) or a card, the rhythm of the transaction is always the same.

**1. Ask for the item or its location:**
* **Де тут хліб?** *(Where is the bread here?)*
* **Скільки коштує кілограм яблук?** *(How much does a kilogram of apples cost?)*

**2. Make the request with quantities:**
* **Дайте, будь ласка, пляшку води.** *(Give me, please, a bottle of water.)*
* **Дайте, будь ласка, пачку чаю.** *(Give me, please, a pack of tea.)*

**3. React to the price and decide:**
* **Дорого!** *(Expensive!)*
* **Дешево!** *(Cheap!)*
* **Добре, беру.** *(Good, I will take it.)*

**4. Ask for the total:**
* **Скільки за все?** *(How much for everything?)*
* **Можна карткою?** *(Can I pay by card?)*

With these simple, powerful phrases, you are ready to explore the nearest **супермаркет** or strike up a conversation at the local **ринок**. You can confidently ask about the **ціна**, request specific quantities, and understand the total cost in **гривні** and **копійки**.

**Deterministic word count: 1562 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 108 words | Not found: 0 words

All 108 other words are confirmed to exist in VESUM.

</vesum_verification>