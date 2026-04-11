<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 39: Shopping (A1, A1.6 [Food and Shopping])
**Writer:** Gemini
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
dialogue_situations:
- setting: 'At a Ukrainian supermarket — comparing prices of: хліб (m, bread) — 25
    грн, молоко (n, milk) — 42 грн, сир (m, cheese) — 89 грн, ковбаса (f, sausage)
    — 120 грн, масло (n, butter) — 65 грн. Скільки коштує сир? А молоко?'
  speakers:
  - Мама
  - Дочка
  motivation: Prices with хліб(m), молоко(n), сир(m), ковбаса(f), масло(n)
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
## Діало́ги — Dialogues

When you visit Ukraine, you will notice a distinct difference between traditional shopping and modern retail. A traditional market, known as a **ри́нок** (market) or **база́р** (bazaar), is a lively, bustling place where you can find fresh, local produce directly from farmers. It is a highly communicative environment where talking to the seller is part of the experience. On the other hand, a modern **суперма́ркет** (supermarket) offers convenience and fixed prices. The conversations below show a mother, **Ма́ма**, and her daughter, **Дочка́**, shopping for dinner in both of these authentic Ukrainian settings.

> **(На ри́нку / At the market)**
> **Мама:** До́брий день! Скі́льки ко́шту́є кілогра́м я́блук? *(Good day! How much does a kilogram of apples cost?)*
> **Продаве́ць:** Соро́к гри́вень. *(Forty hryvnias.)*
> **Мама:** А помідо́ри? *(And tomatoes?)*
> **Продавець:** Три́дцять п'ять гривень за кілограм. *(Thirty-five hryvnias per kilogram.)*
> **Мама:** Да́йте, будь ла́ска, два кілогра́ми помідо́рів і кілограм яблук. *(Give me, please, two kilograms of tomatoes and a kilogram of apples.)*
> **Продавець:** Сто де́сять гривень. *(One hundred ten hryvnias.)*
> **Мама:** Ось, будь ласка. *(Here you go, please.)*
> **Продавець:** Дякую! *(Thank you!)*

:::note
**The Ukrainian Market Culture**
A traditional Ukrainian **ринок** (market) is not just a place to buy food; it is a vital social hub. You will often see people chatting with their favorite sellers, asking about their families, and selecting the freshest produce straight from the garden. It is a much more personal experience than visiting a supermarket!
:::

> **(У суперма́ркеті / At the supermarket)**
> **Мама:** Ви́бачте, де тут хліб? *(Excuse me, where is the bread here?)*
> **Працівни́к:** Хліб у тре́тьому ря́ді. *(The bread is in the third aisle.)*
> **Дочка:** А молоко́? *(And milk?)*
> **Працівник:** Молоко в холоди́льнику, там. *(The milk is in the fridge, over there.)*
> **Мама:** Скільки коштує цей сир? *(How much does this cheese cost?)*
> **Дочка:** Сто два́дцять гривень. *(One hundred twenty hryvnias.)*
> **Мама:** До́рого! А є деше́вший? *(Expensive! And is there a cheaper one?)*
> **Дочка:** Так, ось цей — вісімдеся́т. *(Yes, this one here — eighty.)*

The core food items that appeared in these conversations, along with a few others, are essential vocabulary. You will hear these words every time you visit a grocery store or market: **хліб** (bread), **молоко** (milk), **сир** (cheese), **ковбаса́** (sausage), and **ма́сло** (butter). Memorize these everyday essentials before we explore how to handle numbers and money.

## Скільки коштує? — How Much?

To navigate any shop successfully, you must learn how to ask for prices. The most important verb for this situation is **ко́штува́ти** (to cost). Because Ukrainian grammar requires the verb to agree with the noun, we use two different forms depending on whether the item is singular or plural. If you are asking about one single item, such as a loaf of bread, use the singular form: **Скільки коштує...?** (How much does ... cost?). If you are asking about multiple items, like apples, use the plural form: **Скільки ко́шту́ють...?** (How much do ... cost?). These examples show the pattern in action:

- **Скільки коштує хліб?** (How much does the bread cost?)
- **Скільки коштує масло?** (How much does the butter cost?)
- **Скільки коштує вода́?** (How much does the water cost?)
- **Скільки коштують я́блука?** (How much do the apples cost?)
- **Скільки коштують я́йця?** (How much do the eggs cost?)
- **Скільки коштують помідори?** (How much do the tomatoes cost?)

:::caution
**Agreement Matters**
Remember that **коштувати** (to cost) must match the noun it describes. A common mistake is to use the singular **коштує** for plural items like **яблука** (apples). Always check if you are buying one thing or many things before you ask the price!
:::

Once you ask the price, you need to understand the answer. The national currency of Ukraine is the **гри́вня** (hryvnia). The word for the currency itself changes its ending depending on the exact number that comes right before it. For the number one, and any number ending in 1 (except those ending in 11), we use the basic dictionary form: **21 гривня** (twenty-one hryvnias). For numbers ending in 2, 3, or 4 (except those ending in 12, 13, or 14), the word takes a plural ending: **32 гри́вні** (thirty-two hryvnias). For numbers ending in 5, 6, 7, 8, 9, or 0, as well as all the teens (11-19), we use the "many" form: **45 гривень** (forty-five hryvnias), **100 гривень** (one hundred hryvnias). You will also see prices that include smaller coins. Traditionally, the hundredth part of a hryvnia is called a **копі́йка** (kopeck). However, it is important to know that **копійка** is a term imposed during the Russian imperial era. The true, historical Ukrainian term for a small coin is **шаг** (shah), which Ukraine is currently working to restore to everyday use.

When you hear the price, you might want to express your reaction to it. You can use simple adverbs to state your opinion clearly. If a price seems too high, you can use the word **дорого** (expensive). If you find a great deal, you can happily use the word **де́шево** (cheap). If the price is exactly what you expected, you can confirm it with the phrase **норма́льна ціна́** (fair price). When shopping at a traditional market, or if you are buying many items at once, you might want to politely ask for a lower price: **Є зни́жка?** (Is there a discount?). Finally, when you have selected everything you need and are ready to finish the transaction, you can ask for the total amount by saying **За все** (Total) or ask the seller directly **Скільки з мене́?** (How much do I owe?). Here are these reactions and questions in action:

- **Це ду́же дорого!** (This is very expensive!)
- **Тут дешево.** (It is cheap here.)
- **Це нормальна ціна.** (This is a fair price.)
- **Є знижка на яблука?** (Is there a discount on apples?)
- **Скільки за все?** (How much for everything?)
- **Скільки з мене?** (How much do I owe?)

<!-- INJECT_ACTIVITY: quiz-currency-choice -->
<!-- INJECT_ACTIVITY: fill-in-prices -->

## Де купи́ти? — Where to Buy

When you step out into a Ukrainian city or town, you will encounter several different types of places to buy your daily goods. A general, everyday shop is simply called a **магази́н** (shop). To describe the action of buying, use the verb **купува́ти** (to buy). If you are visiting a large, modern self-service store with shopping carts and long aisles, you will call it a **супермаркет** (supermarket). You will also frequently see the beautiful, traditional Ukrainian word **крамни́ця** (store), which is an excellent native synonym for a shop. Inside a massive supermarket, you need to know how to navigate between different product zones. For example, if you are looking for chicken or sausage, you will head to the **м'ясни́й відділ** (meat section). If you need to buy yogurt, butter, or cheese, you will look for the **моло́чний відділ** (dairy section). For medicines, you will visit an **апте́ка** (pharmacy). You will use these location words frequently:

- **Ми йдемо́ в магазин.** (We are going to the shop.)
- **Цей супермаркет дуже вели́кий.** (This supermarket is very big.)
- **Наш ринок стари́й.** (Our market is old.)
- **М'ясний відділ там.** (The meat section is there.)
- **Молочний відділ тут.** (The dairy section is here.)

When you ask for food, you rarely just ask for the item itself; you usually need a specific amount. In Ukrainian, quantity words act as a fixed grammatical chunk. The word that comes after the quantity always takes a special ending (the genitive case), which naturally includes the English meaning of the word "of". Memorize these useful combinations as complete phrases:

- **кілограм яблук** (a kilogram of apples)
- **два кілограми помідорів** (two kilograms of tomatoes)
- **літр молока́** (a liter of milk)
- **два лі́три со́ку** (two liters of juice)
- **па́чка ма́сла** (a pack of butter)
- **пачка ча́ю** (a pack of tea)
- **пля́шка во́ди** (a bottle of water)
- **пляшка соку** (a bottle of juice)
- **буха́нка хлі́ба** (a loaf of bread)

:::tip
**The Hidden "Of"**
When you use quantity words like **кілограм** (kilogram) or **літр** (liter), you do not need to add a separate Ukrainian word for "of". The relationship is built directly into the grammar when the second word changes its ending. **Літр молока** literally means "a liter of milk" all by itself!
:::

When it is your turn to speak to the seller, you will use a standard, polite formula to make your request. You should always start with the imperative phrase **Дайте, будь ласка...** (Give me, please...). This is the most natural and respectful way to ask for items in Ukraine. Once the seller has gathered your items, it is time to pay. You have two main payment options: **готі́вка** (cash) or **ка́ртка** (card). If you prefer to pay electronically, you can politely ask the cashier **Мо́жна ка́рткою?** (Is it possible by card?). If you pay with physical money (**гроші**), the seller will hand back your change and say **Ось ре́шта** (Here is the change). Regardless of how you pay, the transaction usually ends when the cashier hands you a small piece of paper and says **Ось ваш чек** (Here is your receipt). These are the most common phrases you will hear and use at the checkout:

- **Дайте, будь ласка, літр молока.** (Give me, please, a liter of milk.)
- **Дайте, будь ласка, кілограм си́ру.** (Give me, please, a kilogram of cheese.)
- **Я хо́чу купити хліб.** (I want to buy bread.)
- **Можна карткою?** (Is it possible by card?)
- **Можна готі́вкою?** (Is it possible with cash?)
- **Ось ва́ша решта.** (Here is your change.)
- **Ось ваш чек.** (Here is your receipt.)

<!-- INJECT_ACTIVITY: fill-in-quantities -->
<!-- INJECT_ACTIVITY: match-up-shops -->

## Підсумок — Summary

You now have a complete and practical toolkit for navigating any shopping scenario in Ukraine. A successful purchase always follows a predictable rhythm of four steps. First, you ask for information to locate items and check prices: **Скільки коштує?** (How much does it cost?) and **Де тут хліб?** (Where is the bread here?). Second, you confidently choose your items and state the quantities you need: **Дайте, будь ласка, кілограм яблук** (Give me, please, a kilogram of apples). Third, you react to the price to ensure it is fair: **Дорого!** (Expensive!), **Дешево!** (Cheap!), or accept it with **До́бре, беру́** (Good, I'll take it). Finally, you complete the transaction by asking for the total and choosing your payment method: **Скільки за все?** (How much for everything?) and **Можна карткою?** (Is it possible by card?). By practicing these exact phrases, you will be prepared for daily life.

When you shop at a traditional Ukrainian market, you will quickly notice a charming cultural habit. Sellers frequently use special diminutive forms of words when speaking to customers. Instead of simply offering a standard potato, they might offer you a **карто́пелька** (little potato). Instead of regular apples, they will proudly show you their **я́блучка** (little apples). They do not use these words because the food is physically small. In Ukrainian culture, adding these gentle, softening endings to words is a way to express warmth, hospitality, and a welcoming attitude toward the buyer. It makes the market feel like a friendly community rather than a cold business transaction. Despite this friendly atmosphere, you must always remember to maintain your own politeness by using the formal pronoun **Ви** (You) when speaking to any seller you do not know personally.

Before you finish this module, take a moment to test your new skills mentally. Imagine yourself in these three common situations and try to form the correct Ukrainian sentences in your head:

- You are standing at a vibrant outdoor market. How do you ask the seller for the exact price of five kilograms of fresh potatoes?
- The seller tells you the price, but it seems much too high for your budget. How do you clearly express to the seller that two hundred hryvnias is too expensive?
- Imagine you need to buy 3 items at a market. How do you successfully ask the price, choose a quantity for each, and pay?
```
</generated_module_content>

**PIPELINE NOTE — Word count: 1868 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 98 words | Not found: 55 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Діало — NOT IN VESUM
  ✗ Працівни — NOT IN VESUM
  ✗ Продаве — NOT IN VESUM
  ✗ Скі — NOT IN VESUM
  ✗ Соро — NOT IN VESUM
  ✗ апте — NOT IN VESUM
  ✗ блук — NOT IN VESUM
  ✗ блучка — NOT IN VESUM
  ✗ вень — NOT IN VESUM
  ✗ вка — NOT IN VESUM
  ✗ вня — NOT IN VESUM
  ✗ вні — NOT IN VESUM
  ✗ вісімдеся — NOT IN VESUM
  ✗ деше — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ жка — NOT IN VESUM
  ✗ жна — NOT IN VESUM
  ✗ зни — NOT IN VESUM
  ✗ йка — NOT IN VESUM
  ✗ йте — NOT IN VESUM
  ✗ йця — NOT IN VESUM
  ✗ крамни — NOT IN VESUM
  ✗ купува — NOT IN VESUM
  ✗ кілогра — NOT IN VESUM
  ✗ льки — NOT IN VESUM
  ✗ льна — NOT IN VESUM
  ✗ льнику — NOT IN VESUM
  ✗ м'ясни — NOT IN VESUM
  ✗ магази — NOT IN VESUM
  ✗ моло — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ пля — NOT IN VESUM
  ✗ помідо — NOT IN VESUM
  ✗ ркет — NOT IN VESUM
  ✗ ркеті — NOT IN VESUM
  ✗ рого — NOT IN VESUM
  ✗ ртка — NOT IN VESUM
  ✗ рткою — NOT IN VESUM
  ✗ сла — NOT IN VESUM
  ✗ сло — NOT IN VESUM
  ✗ стари — NOT IN VESUM
  ✗ суперма — NOT IN VESUM
  ✗ сять — NOT IN VESUM
  ✗ тьому — NOT IN VESUM
  ✗ хлі — NOT IN VESUM
  ✗ чка — NOT IN VESUM
  ✗ чний — NOT IN VESUM
  ✗ шево — NOT IN VESUM

All 98 other words are confirmed to exist in VESUM.

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
