<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 39: Shopping (A1, A1.6 [Food and Shopping])
**Writer:** Claude
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
## Діало́ги (Dialogues)

Taras is at a busy outdoor **ри́нок** (market) in Kyiv. He needs **я́блука** (apples) and **помідо́ри** (tomatoes). Listen to how he asks the price, hears the total, and places his order.

> — **Тара́с:** До́брий день! *(Good day!)*
> — **Продаве́ць:** Добрий день! *(Good day!)*
> — **Тарас:** Скі́льки ко́штує кілогра́м я́блук? *(How much does a kilogram of apples cost?)*
> — **Продавець:** Соро́к гри́вень. *(Forty hryvnias.)*
> — **Тарас:** А помідори? *(And tomatoes?)*
> — **Продавець:** Три́дцять п'ять гривень за кілограм. *(Thirty-five hryvnias per kilogram.)*
> — **Тарас:** Да́йте, будь ла́ска, два кілогра́ми помідо́рів і кілограм яблук. *(Please give me two kilograms of tomatoes and a kilogram of apples.)*
> — **Продавець:** Сімдеся́т п'ять гривень, будь ласка. *(Seventy-five hryvnias, please.)*
> — **Тарас:** Ось, будь ласка. *(Here you go.)*
> — **Продавець:** Дякую! До поба́чення! *(Thank you! Goodbye!)*

Two key phrases to notice here. First, **за кілограм** means "per kilogram" — the vendor states the unit price. Second, **Дайте, будь ласка** followed by a quantity and an item is the standard buying request at any Ukrainian market or shop.

Now a different setting. **Ма́ма** (Mom) and **Дочка́** (Daughter) are in a **суперма́ркет** (supermarket). They need to find bread, compare cheese prices, and pay.

> — **Дочка:** Ма́мо, де тут хліб? *(Mom, where is the bread here?)*
> — **Мама:** Хліб у тре́тьому ря́ді. *(Bread is in the third aisle.)*
> — **Дочка:** А молоко́? *(And milk?)*
> — **Мама:** Молоко в холоди́льнику, там. *(Milk is in the fridge, over there.)*
> — **Дочка:** Скільки коштує цей сир? *(How much does this cheese cost?)*
> — **Мама:** Сто два́дцять гривень. *(One hundred twenty hryvnias.)*
> — **Дочка:** До́рого! А є деше́вший? *(Expensive! Is there a cheaper one?)*
> — **Мама:** Так, ось цей — вісімдеся́т. *(Yes, this one — eighty.)*
> — **Дочка:** До́бре, беру́. *(OK, I'll take it.)*
> — **Мама:** Скільки за все? *(How much is everything?)*
> — **Каси́р:** Сто сорок сім гривень. *(One hundred forty-seven hryvnias.)*
> — **Мама:** Мо́жна ка́рткою? *(Can I pay by card?)*
> — **Касир:** Так, звича́йно. Дякуємо за поку́пку! *(Yes, of course. Thanks for the purchase!)*

:::tip
Four phrases from this dialogue to memorize now: **Дорого!** (Expensive!), **Добре, беру.** (OK, I'll take it.), **Скільки за все?** (How much total?), **Можна карткою?** (Can I pay by card?)
:::

## Скільки коштує? (How Much?)

The question **Скільки коштує?** (How much does it cost?) uses the verb **ко́штувати** (to cost) in third person singular. When the item is plural, the verb changes: **Скільки ко́штують?** (How much do they cost?). The verb agrees with the item — singular item, singular verb; plural item, plural verb. Compare:

- **Скільки коштує хліб?** — How much does the bread cost?
- **Скільки коштує молоко?** — How much does the milk cost?
- **Скільки коштують яблука?** — How much do the apples cost?
- **Скільки коштують помідори?** — How much do the tomatoes cost?

The word **гри́вня** (hryvnia — Ukraine's currency) changes form depending on the number before it. Learn this as a pattern rather than a grammar rule. After **1**, use **гривня**. After **2, 3, 4** (and compounds ending in them), use **гри́вні**. After **5 and above**, use **гривень**. Here are real prices to practice:

- **1 гривня** — one hryvnia
- **2 гривні** — two hryvnias
- **4 гривні** — four hryvnias
- **5 гривень** — five hryvnias
- **20 гривень** — twenty hryvnias
- **21 гривня** — twenty-one hryvnias (ends in 1 → гривня)
- **32 гривні** — thirty-two hryvnias (ends in 2 → гривні)
- **100 гривень** — one hundred hryvnias

The smaller unit, **копі́йка** (kopeck), follows a similar pattern: 1 **копійка**, 2 **копі́йки**, 5 **копі́йок**. In everyday speech, prices are usually rounded to whole **гривні**, so you will hear **копійки** mostly on receipts.

<!-- INJECT_ACTIVITY: quiz-currency-forms -->

Now practice reading prices aloud. Here are the five items from the supermarket dialogue:

- **Хліб — двадцять п'ять гривень.** Bread — 25 hryvnias.
- **Молоко — сорок дві гривні.** Milk — 42 hryvnias.
- **Сир — вісімдесят де́в'ять гривень.** Cheese — 89 hryvnias.
- **Ковбаса́ — сто двадцять гривень.** Sausage — 120 hryvnias.
- **Ма́сло — шістдеся́т п'ять гривень.** Butter — 65 hryvnias.

Notice **сорок дві гривні** — the number **дві** is feminine here because **гривня** is a feminine noun. With masculine nouns you would say **два**, but with **гривня** it is always **дві**.

After you hear a price, you react. Here are six useful expressions:

- **Дорого!** — Expensive! (when ковбаса is 120 гривень)
- **Де́шево!** — Cheap! (a pleasant surprise)
- **Норма́льна ціна́.** — Fair price.
- **Є зни́жка?** — Is there a discount?
- **За все — сто п'ятдеся́т гривень.** — The total is 150 hryvnias.
- **Добре, беру.** — OK, I'll take it.

<!-- INJECT_ACTIVITY: fill-in-prices -->

## Де купи́ти? (Where to Buy)

Ukraine has several types of shopping locations, each with its own character. Here are the five most common:

- **Магази́н** (shop) — a general store. **Я йду в магазин.** (I'm going to the shop.)
- **Супермаркет** (supermarket) — a large self-service store. **У суперма́ркеті є все.** (The supermarket has everything.)
- **Ринок** (market) — an open-air market where prices are often lower. **На ри́нку ча́сто деше́вше.** (At the market it's often cheaper.)
- **Крамни́ця** (store) — a distinctly Ukrainian word, synonym for **магазин**. Common in western Ukraine and literary language. **У на́шій крамни́ці га́рний ви́бір.** (Our store has a good selection.)
- **Апте́ка** (pharmacy) — for medicines and cosmetics, not food. **Лі́ки купу́ють в апте́ці.** (Medicine is bought at the pharmacy.) You can also hear: **У ме́не нема́є грошей** (I don't have money) — a phrase you'll need if you've spent too much at the **ринок**!

Inside a **супермаркет**, products are organized into sections called **відділ** (section/department):

- **Де тут моло́чний відділ?** — Where is the dairy section? — **Там, право́руч.** (Over there, to the right.)
- **Де тут хлі́бний відділ?** — Where is the bread section? — **Пе́рший ряд, ліво́руч.** (First aisle, to the left.)
- **М'ясни́й відділ** — the meat section.
- **Овоче́вий відділ** — the vegetable/produce section.

This connects back to Dialogue 2: **Де тут хліб? — Хліб у третьому ряді.**

When you buy food, you need quantity words. Learn these as ready-made chunks — the item form after each quantity is fixed, and you will study why in A2. For now, just copy the pattern:

- **Кілограм** (kilogram): **кілограм яблук**, **два кілограми помідорів** — **Дайте, будь ласка, кілограм яблук.** (Please give me a kilogram of apples.)
- **Літр** (liter): **літр молока́**, **два лі́три со́ку** — **Дайте, будь ласка, літр молока.** (Please give me a liter of milk.)
- **Па́чка** (pack): **пачка ма́сла**, **пачка ча́ю** — **Дайте, будь ласка, дві па́чки ка́ви.** (Please give me two packs of coffee.)
- **Пля́шка** (bottle): **пляшка во́ди**, **пляшка соку** — **Дайте, будь ласка, пля́шку води.** (Please give me a bottle of water.)
- **Буха́нка** (loaf — used only for bread): **буханка хлі́ба** — **Дайте, будь ласка, буха́нку хліба.** (Please give me a loaf of bread.)

You will see these genitive endings again in A2. For now, learn the chunks — they are the same ones native speakers use automatically.

The buying formula is always the same: **Дайте, будь ласка,** + quantity + item. Three more examples:

- **Дайте, будь ласка, два кілограми помідорів.** (Please give me two kilograms of tomatoes.)
- **Дайте, будь ласка, літр молока.** (Please give me a liter of milk.)
- **Дайте, будь ласка, буханку хліба.** (Please give me a loaf of bread.)

<!-- INJECT_ACTIVITY: fill-in-quantities -->

<!-- INJECT_ACTIVITY: match-shop-types -->

## Підсумок — Summary

Here is your complete shopping toolkit, organized by what you need to do:

**Ask:**
- **Скільки коштує хліб?** — How much does the bread cost? (singular item)
- **Скільки коштують яблука?** — How much do the apples cost? (plural item)
- **Де тут молочний відділ?** — Where is the dairy section here?
- **Є дешевший?** — Is there a cheaper one?
- **Є знижка?** — Is there a discount?

**Buy:**
- **Дайте, будь ласка, кілограм яблук.** — Please give me a kilogram of apples.
- **Можна пляшку води?** — Can I have a bottle of water? (informal, common at markets)

**React:**
- **Дорого!** — Expensive!
- **Дешево!** — Cheap!
- **Нормальна ціна.** — Fair price.
- **Добре, беру.** — OK, I'll take it.

**Pay:**
- **Скільки за все?** — How much is everything?
- **Можна карткою?** — Can I pay by card?
- **Можна готі́вкою?** — Can I pay cash?

### Self-Check

Test yourself. You are at a Kyiv market and need three things: 2 kg of tomatoes (**помідори**, 50 грн/кг), 1 bottle of juice (**сік**, 30 грн), and 1 loaf of bread (**хліб**, 20 грн). Walk through the full exchange:

> — **Ви:** Скільки коштують помідори? *(How much do the tomatoes cost?)*
> — **Продавець:** П'ятдесят гривень за кілограм. *(Fifty hryvnias per kilogram.)*
> — **Ви:** Скільки коштує сік? *(How much does the juice cost?)*
> — **Продавець:** Тридцять гривень. *(Thirty hryvnias.)*
> — **Ви:** Скільки коштує хліб? *(How much does the bread cost?)*
> — **Продавець:** Двадцять гривень. *(Twenty hryvnias.)*
> — **Ви:** Дайте, будь ласка, два кілограми помідорів, пляшку соку і буханку хліба. *(Please give me two kilograms of tomatoes, a bottle of juice, and a loaf of bread.)*
> — **Продавець:** Сто п'ятдесят гривень. *(One hundred fifty hryvnias.)*
> — **Ви:** Можна карткою? *(Can I pay by card?)*
> — **Продавець:** Так, звичайно. *(Yes, of course.)*

Can you do this without looking at the toolkit above? That is your goal.

**Deterministic word count: 1555 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 118 words | Not found: 72 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Апте — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Крамни — NOT IN VESUM
  ✗ М'ясни — NOT IN VESUM
  ✗ Магази — NOT IN VESUM
  ✗ Овоче — NOT IN VESUM
  ✗ Пля — NOT IN VESUM
  ✗ Продаве — NOT IN VESUM
  ✗ Скі — NOT IN VESUM
  ✗ Соро — NOT IN VESUM
  ✗ Сімдеся — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ апте — NOT IN VESUM
  ✗ блук — NOT IN VESUM
  ✗ бний — NOT IN VESUM
  ✗ в'ять — NOT IN VESUM
  ✗ вень — NOT IN VESUM
  ✗ вня — NOT IN VESUM
  ✗ вні — NOT IN VESUM
  ✗ вше — NOT IN VESUM
  ✗ вісімдеся — NOT IN VESUM
  ✗ деше — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ жка — NOT IN VESUM
  ✗ жна — NOT IN VESUM
  ✗ звича — NOT IN VESUM
  ✗ зни — NOT IN VESUM
  ✗ йка — NOT IN VESUM
  ✗ йки — NOT IN VESUM
  ✗ йок — NOT IN VESUM
  ✗ йте — NOT IN VESUM
  ✗ крамни — NOT IN VESUM
  ✗ кілогра — NOT IN VESUM
  ✗ льки — NOT IN VESUM
  ✗ льна — NOT IN VESUM
  ✗ льнику — NOT IN VESUM
  ✗ ліво — NOT IN VESUM
  ✗ моло — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ п'ятдеся — NOT IN VESUM
  ✗ пку — NOT IN VESUM
  ✗ пля — NOT IN VESUM
  ✗ поба — NOT IN VESUM
  ✗ поку — NOT IN VESUM
  ✗ помідо — NOT IN VESUM
  ✗ ркет — NOT IN VESUM
  ✗ ркеті — NOT IN VESUM
  ✗ рний — NOT IN VESUM

All 118 other words are confirmed to exist in VESUM.

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
