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
## Діалоги — Dialogues

Welcome to a cozy **кафе** (cafe) in the heart of Lviv. The city is famous for its rich **кава** (coffee) culture, where locals spend hours talking over a warm cup. Before you can enjoy the atmosphere, you need to know how to navigate the interaction. Every cafe visit begins with a polite greeting, such as **Добрий день** (Good day), and a direct request to see what they offer. To start, you simply ask the waiter: **Можна меню?** (Can I have the menu?). Politeness is your strongest tool, so always keep **будь ласка** (please) and **дякую** (thank you) ready.

> **Ростик:** Добрий день! Можна меню? *(Good day! Can I have the menu?)*
> **Офіціант:** Ось, будь ласка. *(Here, please.)*
> **Ростик:** Що ви рекомендуєте? *(What do you recommend?)*
> **Офіціант:** Борщ дуже смачний. *(The borscht is very delicious.)*
> **Ростик:** Добре, мені борщ і хліб. А тобі, Іванко? *(Good, I will have borscht and bread. And for you, Ivanka?)*
> **Іванка:** Мені каву з молоком і тістечко. *(I will have a coffee with milk and a pastry.)*

This dialogue shows the core structure of ordering. When the waiter approaches, Rostyk asks for advice using the verb **рекомендувати** (to recommend). Once they decide, they use the pattern **Мені + [Accusative case]** to state their choices. You already know the accusative case from the previous module. Notice the noun genders: the feminine **кава** (coffee) changes to **каву**, while the masculine **чай** (tea) and neuter **тістечко** (pastry) stay exactly the same. Even when you are ordering a complex combination like **кава з молоком** (coffee with milk), only the main noun changes its ending.

> **Ростик:** Вибачте, можна рахунок? *(Excuse me, can I have the bill?)*
> **Офіціант:** Так, одну хвилинку. З вас сто двадцять гривень. Карткою чи готівкою? *(Yes, one minute. From you, one hundred twenty hryvnias. By card or by cash?)*
> **Ростик:** Карткою, будь ласка. *(By card, please.)*
> **Офіціант:** Ось термінал. Дякую. *(Here is the terminal. Thank you.)*
> **Іванка:** Дуже смачно було! Дякуємо! *(It was very delicious! We thank you!)*
> **Офіціант:** Приходьте ще! *(Come again!)*

<!-- INJECT_ACTIVITY: match-up-functions -->

## Як замовити — How to Order

The most versatile request phrase you can learn at this level is **Можна мені...?**. Literally, it means "Is it possible for me...?" and it is the standard, polite way to ask for anything you need. Always follow this phrase with the item in the accusative case. Let us look at a few examples:

*   **Можна мені каву?** — Can I have a coffee?
*   **Можна мені воду?** — Can I have some water?
*   **Можна мені сік?** — Can I have juice?
*   **Можна мені меню?** — Can I have the menu?

Another polite option is **Дайте, будь ласка** (Give me, please), which is slightly more direct but perfectly acceptable. When you are finally ready to tell the waiter your decision, you will often use the phrase **Я буду** (I will have). This is the standard way to state a final choice from the menu. 

*   **Я буду піцу і чай.** — I will have pizza and tea.
*   **Я буду салат і суп.** — I will have a salad and soup.

You might also hear people say **Я хочу** (I want). While **Я хочу** is grammatically correct and widely used, it sounds slightly more demanding than **Я буду**. Both require the accusative case.

Before you make a final decision, you may need to ask questions about the food. You can easily check for specific dietary preferences or tastes using simple questions. If you do not like spicy food, you ask: **Це гостре?** (Is it spicy?). If you want to know the ingredients, you can ask: **Це з м'ясом?** (Is it with meat?) or **Є вегетаріанське меню?** (Is there a vegetarian menu?). Often, you will see a delicious pastry in the display case but you do not know the name. In that situation, you simply point and ask: **А що це?** (And what is this?). 

Sometimes you just need a bit more. You can handle extra quantities easily by saying: **Ще одну каву, будь ласка** (One more coffee, please). You can also add simple modifiers to your drink order. You might ask for a drink **без цукру** (without sugar) or **з лимоном** (with lemon). Finally, listen carefully for the most common question at any modern coffee counter: **Вам тут чи з собою?** (For here or to go?). You just reply **Тут** (Here) or **З собою** (To go).

<!-- INJECT_ACTIVITY: fill-in-ordering-accusative -->

## Культура кафе — Cafe Culture

When it is time to order, there is one linguistic "Golden Rule" you must follow: always use the verb **замовляти** (to order). You might sometimes hear people use the word *заказати*, but this is a direct calque from Russian and is considered incorrect in modern standard Ukrainian. You should always say **Я замовляю піцу** (I am ordering a pizza). 

Additionally, you need to recognize a special group of nouns like **кафе** (cafe) and **меню** (menu). These are indeclinable foreign words. This means they NEVER change their endings, no matter what case they are in. You say **Це кафе** (This is a cafe) and you also say **Я в кафе** (I am in the cafe). The ending stays exactly the same. Other common indeclinable words you will hear include **какао** (cocoa), **метро** (subway), and **ескімо** (popsicle). 

:::caution
Never try to change the ending of **кафе** or **меню**. Forms like *кафі* or *менюю* do not exist in Ukrainian. Keep them exactly as they are in the dictionary.
:::

When you finish eating, there is an important point of etiquette regarding the **рахунок** (bill). In a traditional **ресторан** (restaurant) or a formal cafe, the waiter rarely brings the bill automatically. This is done so you do not feel rushed to leave. You must catch their eye, raise your hand slightly, and ask: **Можна рахунок?** (Can I have the bill?). Once the bill arrives, you must consider the **чайові** (tips). In most cities, leaving a 10% tip is standard for good service. You can usually leave cash in the folder they provide or ask to add it directly to your card payment.

When it comes to payment logistics, the waiter will almost always ask: **Карткою чи готівкою?** (By card or by cash?). Ukraine has one of the highest rates of contactless payment in Europe. Even a small street kiosk usually has a **термінал** (payment terminal). You can confidently reply **Карткою, будь ласка** (By card, please). If you pay with cash, they will take your **оплата** (payment) and bring you the **решта** (change).

Finally, you need a few social phrases to complete the cafe experience. If you enter a crowded place and see an empty chair at a shared table, you should politely ask: **Тут вільно?** (Is this seat free?). When the waiter brings your food, they will always say: **Смачного!** (Bon appétit!), and you should reply with **Дякую!** (Thank you!). As you leave, the best compliment you can give the staff is to smile and say: **Все було дуже смачно!** (Everything was very delicious!). 

<!-- INJECT_ACTIVITY: quiz-situation-choice -->
<!-- INJECT_ACTIVITY: dialogue-completion-cafe -->

## Підсумок — Summary

You now have the complete communication toolkit needed to navigate a Ukrainian cafe with confidence. You understand that politeness is key, and you know how to use the accusative case to make clear, accurate requests. Here is a recap of the essential patterns you should memorize:

*   **To order:** Мені [accusative], будь ласка. *(Мені каву, будь ласка.)*
*   **To ask:** Скільки коштує? Що рекомендуєте? *(How much does it cost? What do you recommend?)*
*   **To pay:** Рахунок, будь ласка. Можна карткою? *(The bill, please. Can I pay by card?)*
*   **To compliment:** Дуже смачно! Дякую! *(Very delicious! Thank you!)*

Remember that the phrase **будь ласка** (please) is your magic key for all interactions. It softens any request and shows respect for the person helping you. 

Before you move to the next module, do a quick self-check. Can you perform all of these tasks?

*   Can you greet the waiter and ask for a menu? (**Добрий день, можна меню?**)
*   Can you order a drink and a main course using the accusative case? (**Мені каву і піцу.**)
*   Can you ask if a dish is spicy or vegetarian? (**Це гостре? Є вегетаріанське меню?**)
*   Can you ask for the bill and specify your payment method? (**Можна рахунок? Карткою, будь ласка.**)
*   Do you remember to use the correct verb **замовляти** (to order) instead of the Russianism *заказати*?

If you can confidently handle these situations, you are ready to order your next meal in Ukrainian!
</generated_module_content>

**PIPELINE NOTE — Word count: 1402 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 84 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іванка — NOT IN VESUM
  ✗ Іванко — NOT IN VESUM
  ✗ Ростик — NOT IN VESUM
  ✗ кафі — NOT IN VESUM
  ✗ менюю — NOT IN VESUM

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
