<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 38: At the Cafe (A1, A1.6 [Food and Shopping])
**Writer:** Claude
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
## Діало́ги (Dialogues)

Ростик and Іва́нка walk into a cozy **кафе́** (café) on a quiet Lviv street. A waiter approaches their table with two leather-bound menus.

> — **Офіціа́нт:** До́брий день! Ось **меню́**. *(Good day! Here's the menu.)*
> — **Ростик:** Дякую. Що ви рекоменду́єте? *(Thank you. What do you recommend?)*
> — **Офіціант:** **Борщ** ду́же **смачни́й**. *(The borshch is very tasty.)*
> — **Ростик:** До́бре, **мені́ борщ і хліб, будь ла́ска**. *(Good, borshch and bread for me, please.)*
> — **Офіціант:** А що бу́дете пи́ти? *(And what will you drink?)*
> — **Ростик:** **Ка́ву з молоко́м**. *(Coffee with milk.)*
> — **Іванка:** **Мені чай і ті́стечко, будь ласка**. *(Tea and a pastry for me, please.)*
> — **Офіціант:** Добре, одну́ **хвили́нку**. *(Good, one moment.)*

Notice the pattern: every order uses **мені** + the accusative form of the food or drink word. You practised accusative endings in M37 — now they're doing real work in a real café.

After the meal, Ростик signals the waiter.

> — **Ростик:** **Раху́нок, будь ласка**. *(The bill, please.)*
> — **Офіціант:** Ось, **будь ласка**. Сто два́дцять гри́вень. *(Here you go. One hundred twenty hryvnias.)*
> — **Іванка:** **Мо́жна ка́рткою?** *(Can we pay by card?)*
> — **Офіціант:** Так, звича́йно. *(Yes, of course.)*
> — **Ростик:** Все було́ дуже **сма́чно**! *(Everything was very delicious!)*
> — **Ростик & Іванка:** **Дякуємо!** *(Thank you!)*
> — **Офіціант:** Дякуємо, **прихо́дьте** ще! *(Thank you, come again!)*

Notice how Ростик has to ask for the **рахунок** (bill) to be brought to the table. He might also leave **чайові́** (tips) before leaving.

Now test yourself — can you answer these questions from the dialogues?

- What did Ростик order? → **Мені борщ, хліб і каву з молоком.**
- What did Іванка order? → **Мені чай і тістечко.**
- How did they pay? → **Карткою** (by card).

## Як замо́вити (How to Order)

When you want to order (**замовля́ти**) at a Ukrainian **кафе**, there are four polite ways to do it. Each one uses the accusative case — the same endings you learned in M37.

**Pattern 1: Мені [accusative], будь ласка.**
- **Мені каву, будь ласка.** — Coffee for me, please.
- **Мені борщ, будь ласка.** — Borshch for me, please.

**Pattern 2: Можна [accusative]?**
- **Можна во́ду?** — May I have water?
- **Можна хліб?** — May I have bread?

**Pattern 3: Да́йте, будь ласка, [accusative].**
- **Дайте, будь ласка, сала́т.** — Give me a salad, please.
- **Дайте, будь ласка, сік.** — Give me juice, please.

**Pattern 4: Я хо́чу / Я бу́ду [accusative].**
- **Я хо́чу пі́цу.** — I want pizza.
- **Я буду суп.** — I'll have soup.

All four are polite. **Я буду** is slightly more casual — something you'd say to a friend working behind the counter. **Дайте, будь ласка** is the most formal.

Quick accusative reminder: masculine inanimate and neuter nouns keep their nominative form (**борщ** → **борщ**, **меню** → **меню**). Feminine nouns ending in **-а** change to **-у** (**ка́ва** → **каву**, **вода́** → **воду**, **пі́ца** → **піцу**).

<!-- INJECT_ACTIVITY: fill-in-order -->

Once you've ordered, you might want to ask about the **меню**. Here are six essential phrases:

- **Що ви рекомендуєте?** — What do you recommend?
- **Це го́стре?** — Is it spicy?
- **Це з м'я́сом?** — Is it with meat?
- **А що це?** — What is this?
- **Скі́льки ко́шту́є?** — How much does it cost?
- **Є вегетаріа́нське меню?** — Is there a vegetarian menu?

Each question gets a real answer. Ask **Скільки коштує борщ?** and the waiter might say: **Борщ коштує вісімдеся́т гривень** (The borshch costs eighty hryvnias).

Try building questions from this mini-menu: **борщ** 80 грн, **піца** 150 грн, **кава** 45 грн. For example: **Скільки коштує кава?** — **Кава коштує со́рок п'ять гривень.** The numbers connect back to what you learned in earlier modules.

## Культу́ра кафе (Cafe Culture)

Not every place with food is the same. Ukrainian has three distinct words for three distinct experiences:

| | **Кафе** | **Рестора́н** | **Кав'я́рня** |
|---|---|---|---|
| Style | Casual, drop-in | Formal, reservations | Coffee-focused |
| Menu | On a board or paper | Leather-bound, multi-page | Drinks + pastries |
| Price | Budget-friendly | Higher | Mid-range |

A **кафе** (café) is where you grab a quick **борщ** and **хліб** for lunch. A **ресторан** (restaurant) is where you celebrate a birthday with a white tablecloth. A **кав'ярня** (coffee shop) is where you spend two hours with a **кава** and a laptop. After Euromaidan in 2014, independent **кав'я́рні** exploded across Ukrainian cities, becoming community hubs — places to meet, work, and organize.

When it's time to pay, remember: the **рахунок** (bill) does not come automatically in Ukraine. You say **Рахунок, будь ласка** when you're ready. **Чайові** (tips) are around 10% — common but never obligatory. Most people leave tips in cash even when paying by **ка́ртка** (card). Here are the key payment phrases:

- **Можна карткою?** — Can I pay by card?
- **Готі́вкою.** — In cash.
- **Зали́ште ре́шту.** — Keep the change.
- **Дякуємо, все було смачно!** — Thank you, everything was delicious!

And here are six phrases for everyday café moments — from arriving to leaving:

- **Ві́льно?** / **Тут вільно?** — Is this seat free?
- **Можна меню?** — May I have the menu?
- **Ще одну каву, будь ласка.** — One more coffee, please.
- **Без цу́кру.** — Without sugar.
- **З лимо́ном.** — With lemon.
- **Все було дуже смачно!** — Everything was delicious!

Each phrase fits a micro-situation: you walk in (**Тут вільно?**), you browse (**Можна меню?**), you reorder (**Ще одну каву**), you customize (**Без цукру**), and you leave happy (**Все було дуже смачно!**).

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

<!-- INJECT_ACTIVITY: match-cafe-phrases -->

<!-- INJECT_ACTIVITY: quiz-cafe-phrases -->

## Підсумок — Summary

Here's your café communication toolkit — screenshot this for your next visit to a Ukrainian **кафе**:

| Situation | Phrase | Example |
|---|---|---|
| Order food | **Мені [acc], будь ласка** | Мені каву, будь ласка. |
| Ask about menu | **Скі́льки ко́штує?** | Скільки коштує борщ? |
| Request the bill | **Рахунок, будь ласка** | — |
| Pay by card | **Можна карткою?** | — |
| Compliment food | **Дуже смачно!** | Все було дуже смачно! |

Now put it all together. Imagine you walk into a Lviv **кав'ярня** with a friend. You need to: order a starter (**борщ**), a main (**салат**), a drink (**каву** або́ **сік**), ask about the price of one item, then ask for the bill and pay by card. Try it yourself before checking the model answers below:

- **Мені борщ, будь ласка.**
- **Мені салат і каву, будь ласка.**
- **Скільки коштує сік?**
- **Рахунок, будь ласка.**
- **Можна карткою?**

Ukrainian café culture carries a deeper meaning since 2022. Many Kyiv and Lviv **кав'ярні** stayed open through air-raid alerts, operating as volunteer coordination hubs. Ordering a **кава** in Ukraine today is a small act of normalcy in extraordinary times. As one Kyiv barista put it in 2023: **«Ми ва́римо каву — значить, ми живемо́.»** (We brew coffee — that means we're alive.)

In the next module, you'll take your accusative skills from the **кафе** to the **ри́нок** (market). Same patterns, new vocabulary: **карто́пля** (potatoes), **я́блука** (apples), **молоко́** (milk). **Ході́мо!** (Let's go!)

**Deterministic word count: 1213 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 84 words | Not found: 47 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іва — NOT IN VESUM
  ✗ Іванка — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Кав'я — NOT IN VESUM
  ✗ Офіціа — NOT IN VESUM
  ✗ Раху — NOT IN VESUM
  ✗ Рестора — NOT IN VESUM
  ✗ Ростик — NOT IN VESUM
  ✗ Скі — NOT IN VESUM
  ✗ вегетаріа — NOT IN VESUM
  ✗ вень — NOT IN VESUM
  ✗ вісімдеся — NOT IN VESUM
  ✗ дете — NOT IN VESUM
  ✗ дцять — NOT IN VESUM
  ✗ дьте — NOT IN VESUM
  ✗ жна — NOT IN VESUM
  ✗ замо — NOT IN VESUM
  ✗ замовля — NOT IN VESUM
  ✗ звича — NOT IN VESUM
  ✗ йте — NOT IN VESUM
  ✗ кав'я — NOT IN VESUM
  ✗ лимо — NOT IN VESUM
  ✗ льки — NOT IN VESUM
  ✗ льно — NOT IN VESUM
  ✗ м'я — NOT IN VESUM
  ✗ нка — NOT IN VESUM
  ✗ нку — NOT IN VESUM
  ✗ нок — NOT IN VESUM
  ✗ ном — NOT IN VESUM
  ✗ нське — NOT IN VESUM
  ✗ пля — NOT IN VESUM
  ✗ прихо — NOT IN VESUM
  ✗ рекоменду — NOT IN VESUM
  ✗ рня — NOT IN VESUM
  ✗ рні — NOT IN VESUM
  ✗ ртка — NOT IN VESUM
  ✗ рткою — NOT IN VESUM
  ✗ сма — NOT IN VESUM
  ✗ смачни — NOT IN VESUM
  ✗ стечко — NOT IN VESUM
  ✗ стре — NOT IN VESUM
  ✗ хвили — NOT IN VESUM
  ✗ чно — NOT IN VESUM
  ✗ ште — NOT IN VESUM
  ✗ шту — NOT IN VESUM
  ✗ штує — NOT IN VESUM
  ✗ єте — NOT IN VESUM

All 84 other words are confirmed to exist in VESUM.

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
