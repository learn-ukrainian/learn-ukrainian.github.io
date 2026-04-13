<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 41: Checkpoint: Food and Shopping (A1, A1.6 [Food and Shopping])
**Writer:** Gemini
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
dialogue_situations:
- setting: 'Hosting a вечеря (f, dinner party) — full flow: shopping for продукти
    (pl) at the ринок (m, market), cooking вареники (pl) and салат (m), setting the
    table with тарілки (pl, plates) and склянки (pl, glasses), serving guests.'
  speakers:
  - Господиня (host)
  - Гості (guests)
  motivation: 'Consolidation: продукти(pl), вареники(pl), тарілка(f), склянка(f)'
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

This checkpoint brings together the key material from A1.6. In this module, you review food vocabulary, practical shopping phrases, and the accusative case for both things and people in realistic, everyday scenarios.

This is your opportunity to step back and check what you can already do. Look at the self-check questionnaire below.

*   **Їжа й напої (Food and Drink):** Can you name 10 foods and 5 drinks?
*   **Знахідний відмінок (Accusative):** Can you say what you eat or drink (for example, **Я їм кашу. Я п'ю воду.**)?
*   **Кафе (Cafe):** Can you order a meal at a cafe (for example, **Мені борщ, будь ласка.**)?
*   **Ринок (Market):** Can you ask for prices and buy things at the market (for example, **Скільки коштують помідори? Дайте кілограм яблук, будь ласка.**)?
*   **Люди (People):** Can you use the accusative case to talk about people (for example, **Я бачу брата. Я знаю Олену.**)?

## Читання (Reading Practice)

Let us put these new skills into practice with a short reading text. Anna is having a very busy day running errands around the city. First, she goes to the local market (**ринок**) to buy some fresh groceries for dinner. After finishing her shopping, she relaxes at a nearby cafe (**кафе**). Notice how she uses the accusative case and common shopping chunks throughout her day.

> **Анна йде на ринок. Вона бачить помідори і яблука.**
> *(Anna goes to the market. She sees tomatoes and apples.)*
> **— Скільки коштують помідори?**
> *(— How much do the tomatoes cost?)*
> **— Тридцять гривень.**
> *(— Thirty hryvnias.)*
> **— Добре. Дайте кілограм, будь ласка.**
> *(— Good. Give me a kilogram, please.)*
> **Потім Анна йде у кафе. Вона бачить стіл.**
> *(Then Anna goes to a cafe. She sees a table.)*
> **— Тут вільно?**
> *(— Is it free here?)*
> **— Так, звичайно.**
> *(— Yes, of course.)*
> **— Мені борщ і каву з молоком, будь ласка.**
> *(— Borscht and coffee with milk for me, please.)*
> **Анна їсть борщ і п'є каву. Потім вона просить рахунок.**
> *(Anna eats borscht and drinks coffee. Then she asks for the bill.)*
> **— Рахунок, будь ласка. Можна карткою?**
> *(— The bill, please. Can I pay by card?)*
> **— Так, будь ласка.**
> *(— Yes, please.)*
> **Раптом вона бачить Олену.**
> *(Suddenly she sees Olena.)*
> **— Олено, привіт! Ти знаєш мого брата?**
> *(— Olena, hi! Do you know my brother?)*

This short text seamlessly combines functional shopping chunks (like **Рахунок, будь ласка.**) with the accusative case. Notice the accusative for inanimate objects when Anna orders food (**борщ**, **каву**), and the accusative for animate objects when she sees a friend (**Олену**) or mentions family (**брата**). You already know enough vocabulary and grammar to understand a full day of real-world activities in Ukrainian!

## Граматика (Grammar Summary)

To succeed in everyday interactions, you need a strong grasp of essential food and drink vocabulary (**їжа**, **напої**). Crucial combinations often use the preposition **з** (with), creating useful chunks like **кава з молоком** (coffee with milk) or **чай з лимоном** (tea with lemon). These are the fundamental building blocks of any market or cafe conversation in Ukraine, helping you sound more natural.

When we talk about the objects of our actions, we must use the accusative case. Remember the important difference between inanimate things (**що?** (what?)) and animate people (**кого?** (whom?)).
For inanimate objects, masculine nouns stay the same (**Я їм борщ.**, **Я купую хліб.**), while feminine nouns change their ending from **-а** to **-у** (**Я п'ю воду.**, **Я їм піцу.**).
For animate objects, the feminine rule is exactly the same (**Я бачу Олену.**, **Я люблю маму.**). However, masculine animate nouns take the genitive ending **-а** or **-я** (**Я бачу брата.**, **Я чекаю лікаря.**, **Я знаю друга.**).

Finally, always remember the specific patterns for asking prices. Use **Скільки коштує?** (How much does it cost?) for a single item, and **Скільки коштують?** (How much do they cost?) for plural items. Keep the currency agreement in mind: **одна гривня** (one hryvnia), **дві гривні** (two hryvnias), but **п'ять гривень** (five hryvnias).

### Швидке сортування (Quick Sort)

Sort these forms into two groups.

*   **Inanimate (що?):** борщ, хліб, сік, чай, сир
*   **Animate (кого?):** брата, лікаря, сусіда, друга, вчителя

<!-- INJECT_ACTIVITY: quiz-accusative-forms -->

## Діалог (Connected Dialogue)

This dialogue models a complete, realistic day of food and shopping. It combines talking about breakfast at home, buying fresh produce at the market, and ordering lunch at a cafe. Watch how the speakers use fixed phrases to get what they want smoothly and efficiently.

> **Олег:** Що ти їси на сніданок?
> *(What do you eat for breakfast?)*
> **Марія:** Я їм кашу і п'ю каву з молоком. Потім іду на ринок купувати продукти на вечерю.
> *(I eat porridge and drink coffee with milk. Then I go to the market to buy groceries for dinner.)*
> **Продавчиня:** Що вам?
> *(What would you like?)*
> **Марія:** Скільки коштують помідори?
> *(How much do the tomatoes cost?)*
> **Продавчиня:** Тридцять гривень.
> *(Thirty hryvnias.)*
> **Марія:** Добре. Дайте кілограм помідорів, будь ласка. Я готую вареники і салат.
> *(Good. Give me a kilogram of tomatoes, please. I am making varenyky and salad.)*
> **Олег:** А вдома все готово?
> *(Is everything ready at home?)*
> **Марія:** Так. Я ставлю тарілки і склянки на стіл для гостей.
> *(Yes. I am putting plates and glasses on the table for the guests.)*
> **Марія:** Після ринку я заходжу в кафе: Мені борщ і воду, будь ласка. Рахунок, будь ласка. Можна карткою?
> *(After the market I stop at a cafe: Borscht and water for me, please. The bill, please. Can I pay by card?)*
> **Марія:** А потім я бачу Олену. Олено, привіт! Ти знаєш мого брата?
> *(And then I see Olena. Olena, hi! Do you know my brother?)*

Phrases like **Мені...** (For me...), **Дайте...** (Give me...), **Тут вільно?** (Is it free here?), and **Можна карткою?** (Can I pay by card?) are fixed communicative chunks. You do not need to analyze their deep grammar right now. Treat them as reliable tools: memorize them as complete units, and use them to communicate naturally in a Ukrainian market or cafe without hesitation.

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

<!-- INJECT_ACTIVITY: quiz-situational-phrases -->

## Підсумок — Summary

Here is a summary of what you can now do in Ukrainian:

*   You can talk confidently about everyday food and drinks, describing exactly what you eat for breakfast, lunch, or dinner.
*   You can order a delicious meal at a cafe, check if a seat is free, and politely ask for the bill when you finish.
*   You can shop at a market, accurately ask for prices, understand quantities, and handle amounts in **гривні**.
*   You can correctly use the accusative case to talk about both inanimate things (like eating pizza or drinking water) AND animate people (like seeing a brother or waiting for a friend).

You are building a strong foundation for real-world communication. Next, in A1.7, you will focus on Communication—learning how to make phone calls, write emails, and make exciting plans with friends!
</generated_module_content>

**PIPELINE NOTE — Word count: 1196 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1000 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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

Verified: 106 words | Not found: 5 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Олену — NOT IN VESUM

All 106 other words are confirmed to exist in VESUM.

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
