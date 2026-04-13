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
## Діалоги (Dialogues)

In Ukraine, you can shop in a **супермаркет** (supermarket) or at a **ринок** (market). At the market, you often ask the seller directly about prices, so it is a useful place to practice shopping phrases.

> **(На ринку / At the market)**
> **Покупець:** Добрий день! Скільки коштує кілограм яблук? *(Good day! How much does a kilogram of apples cost?)*
> **Продавець:** Сорок гривень. *(Forty hryvnias.)*
> **Покупець:** А помідори? *(And the tomatoes?)*
> **Продавець:** Тридцять п'ять гривень за кілограм. *(Thirty-five hryvnias per kilogram.)*
> **Покупець:** Дайте, будь ласка, два кілограми помідорів і кілограм яблук. *(Give me, please, two kilograms of tomatoes and a kilogram of apples.)*
> **Продавець:** Сімдесят п'ять гривень. *(Seventy-five hryvnias.)*
> **Покупець:** Ось, будь ласка. *(Here you go.)*

Key phrases here are **Дайте, будь ласка...**, **кілограм яблук**, and **два кілограми помідорів**. At A1, learn them as short shopping chunks.

> **(У супермаркеті / At the supermarket)**
> **Мама:** Вибачте, де тут хліб? *(Excuse me, where is the bread here?)*
> **Працівник:** Хліб у третьому ряду. *(The bread is in the third aisle.)*
> **Мама:** А молоко? *(And the milk?)*
> **Працівник:** Молоко в холодильнику, там. *(The milk is in the fridge, there.)*
> **Дочка:** Мамо, скільки коштує цей сир? *(Mom, how much does this cheese cost?)*
> **Мама:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
> **Дочка:** Дорого! А є дешевший? *(Expensive! Is there a cheaper one?)*
> **Мама:** Так, ось цей — вісімдесят. *(Yes, this one — eighty.)*
> **Дочка:** А скільки коштує ковбаса? *(And how much does the sausage cost?)*
> **Працівник:** Ковбаса — сто двадцять гривень. *(The sausage is one hundred twenty hryvnias.)*
> **Мама:** А масло? *(And the butter?)*
> **Працівник:** Шістдесят п'ять гривень. *(Sixty-five hryvnias.)*

In a large store, **де тут...?**, **Дорого!**, and **А є дешевший?** are useful short phrases.

## Скільки коштує? (How Much?)

The most important question in your shopping toolkit is **Скільки коштує...?** (How much does it cost?). You must pay close attention to the item you are asking about, as the verb must agree with the noun. If you are buying a single or uncountable item, use the singular verb form **коштує**. If you are pointing to a plural item, the verb must take the plural form **коштують**.

*   **Скільки коштує хліб?** *(How much does the bread cost?)*
*   **Скільки коштує молоко?** *(How much does the milk cost?)*
*   **Скільки коштують яблука?** *(How much do the apples cost?)*
*   **Скільки коштують помідори?** *(How much do the tomatoes cost?)*

The official currency of Ukraine is the **гривня** (hryvnia). When stating a **ціна** (price), the ending of the word changes depending on the specific number before it. This is a fundamental rule of noun-number agreement in Ukrainian.

*   Ends in 1 (except 11): singular **гривня**.
    *   **Одна гривня.** *(One hryvnia.)*
    *   **Двадцять одна гривня.** *(Twenty-one hryvnias.)*
*   Ends in 2, 3, or 4 (except 12-14): plural **гривні**.
    *   **Дві гривні.** *(Two hryvnias.)*
    *   **Тридцять чотири гривні.** *(Thirty-four hryvnias.)*
*   Ends in 5-9, 0, or any of the teens (11-19): plural **гривень**.
    *   **П'ять гривень.** *(Five hryvnias.)*
    *   **Сорок гривень.** *(Forty hryvnias.)*

The smaller unit of currency is the **копійка** (kopeck), representing one hundredth of a hryvnia. The grammar rules for its endings are identical: **одна копійка**, **дві копійки**, **п'ять копійок**. However, physical kopecks are less common today. Prices are frequently rounded to the nearest ten kopecks or whole hryvnia, so you will hear **гривня** much more often than **копійка**.

Let's apply numbers directly to prices. Notice how the last digit entirely determines the currency's form.

*   **Скільки коштує кава? Двадцять одна гривня.** *(How much is the coffee? Twenty-one hryvnias.)*
*   **Скільки коштує чай? Тридцять дві гривні.** *(How much is the tea? Thirty-two hryvnias.)*
*   **Скільки коштує торт? Сорок п'ять гривень.** *(How much is the cake? Forty-five hryvnias.)*
*   **Скільки коштує сир? Сто гривень.** *(How much is the cheese? One hundred hryvnias.)*

<!-- INJECT_ACTIVITY: fill-in-prices -->

Before handing over your **гроші** (money), you might react to the final total. If you feel it is too high, exclaim **Дорого!** (Expensive!). If it is a fantastic deal, happily say **Дешево!** (Cheap!) or **Нормальна ціна.** (Fair price.). To ask for the final sum, use **Скільки за все?** (How much for everything?). You might also politely ask **Є знижка?** (Is there a discount?).

Here is a short example of calculating a total in an everyday scenario:

> **Це яблуко коштує десять гривень. Вода коштує двадцять гривень. За все я плачу тридцять гривень.**
> *(This apple costs ten hryvnias. The water costs twenty hryvnias. For everything I pay thirty hryvnias.)*

<!-- INJECT_ACTIVITY: quiz-currency -->

## Де купити? (Where to Buy)

Where exactly do you go to **купувати** (to buy) what you need? A standard shop is called a **магазин** (shop), while a very large one is a **супермаркет** (supermarket). A smaller, local shop is often called a **крамниця** (store — an authentic Ukrainian synonym for магазин). For fresh produce or homemade goods, you visit the **ринок** (market). Finally, for medicine or vitamins, you go to an **аптека** (pharmacy).

Inside a large store or covered market, products are grouped into sections. If you want sausage, chicken, or pork, find the **м'ясний відділ** (meat section). For milk, butter, or cottage cheese, look for the **молочний відділ** (dairy section).

*   **Вибачте, де молочний відділ?** *(Excuse me, where is the dairy section?)*
*   **М'ясний відділ там, у другому ряду.** *(The meat section is there, in the second aisle.)*

For drinks or prepared food, you might also go to a **кафе** (cafe) or a **ресторан** (restaurant).

<!-- INJECT_ACTIVITY: match-up-locations -->

When asking for a product, you rarely ask for just "water" or "apples"; you specify an exact quantity. In Ukrainian grammar, the item following a quantity word changes its ending. It takes a form called the genitive case, which indicates "of something" (like a liter *of* milk). At this introductory level, simply learn these combinations as fixed chunks.

For solid goods and produce, the standard measurement is a **кілограм** (kilogram).

*   **Дайте, будь ласка, кілограм яблук.** *(Give me, please, a kilogram of apples.)*
*   **Я хочу купити два кілограми помідорів.** *(I want to buy two kilograms of tomatoes.)*

For liquids, you use a **літр** (liter).

*   **Дайте, будь ласка, літр молока.** *(Give me, please, a liter of milk.)*
*   **Скільки коштують два літри соку?** *(How much do two liters of juice cost?)*

Here is how you might describe a quick trip to the grocery store:

> **Я йду в супермаркет. Я купую літр молока і два кілограми яблук. Вони дуже свіжі.**
> *(I am going to the supermarket. I am buying a liter of milk and two kilograms of apples. They are very fresh.)*

Packaged goods have specific quantity words. A standard package is a **пачка** (pack). A liquid container is a **пляшка** (bottle). For bread, you ask for a **буханець** (loaf).

*   **Скільки коштує пачка масла?** *(How much does a pack of butter cost?)*
*   **Дайте, будь ласка, пачку чаю.** *(Give me, please, a pack of tea.)*
*   **Де тут пляшка води?** *(Where is a bottle of water here?)*
*   **Я хочу купити буханець хліба.** *(I want to buy a loaf of bread.)*

:::tip
You might sometimes hear the words «буханка», «буханець», or «хлібина» for a loaf of bread. **Буханець** and **хлібина** are good everyday Ukrainian options, and **буханка** also exists in Ukrainian.
:::

<!-- INJECT_ACTIVITY: fill-in-quantities -->

## Підсумок — Summary

Let's recap your essential shopping toolkit. You now know how to navigate a store, ask for items, and handle prices. When you enter a **магазин** or approach a seller at a **ринок**, locate what you need with **Де тут...?** (Where is... here?). Then, ask the price using **Скільки коштує?** for one item or **Скільки коштують?** for many. You politely request your goods by stating **Дайте, будь ласка...** followed by a quantity like a **літр** or a **кілограм**. React to the price by saying **Дорого!** or **Дешево!**, and confirm your purchase with **Добре, беру.** (Good, I'll take it.). Finally, wrap up the transaction by asking **Скільки за все?** (How much for everything?) and checking **Можна карткою?** (Can I pay by card?) if you don't have enough **готівка** (cash).

Here is a short summary of a successful shopping trip:

> **Я на ринку. Я запитую продавця: «Скільки коштують помідори?». Це дуже хороша ціна. Я беру два кілограми.**
> *(I am at the market. I ask the seller: "How much do the tomatoes cost?". This is a very good price. I take two kilograms.)*

Here is a quick question-and-answer review of the most important patterns from this module. Use these as a self-check before your next trip to the market.

*   **Як запитати ціну на помідори?** *(How to ask the price of tomatoes?)*
    *   **Скільки коштують помідори?** *(How much do the tomatoes cost?)*
*   **Як попросити два кілограми яблук?** *(How to ask for two kilos of apples?)*
    *   **Дайте, будь ласка, два кілограми яблук.** *(Give me, please, two kilograms of apples.)*
*   **Як сказати, що ціна зависока?** *(How to say the price is too high?)*
    *   **Це дорого!** *(This is expensive!)*
*   **Як дізнатися загальну суму до сплати?** *(How to ask for the total sum to pay?)*
    *   **Скільки за все?** *(How much for everything?)*
*   **Як запитати про форму оплати?** *(How to ask about the payment method?)*
    *   **Можна карткою чи потрібна готівка?** *(Can I pay by card or is cash needed?)*
</generated_module_content>

**PIPELINE NOTE — Word count: 1525 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 139 words | Not found: 0 words

All 139 other words are confirmed to exist in VESUM.

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
