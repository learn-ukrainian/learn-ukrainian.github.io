<!-- version: 1.0.0 | updated: 2026-03-27 -->
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
Welcome to the checkpoint module for phase A1.6. This is where we pause to review and consolidate your knowledge. A1.6 covered five essential topics. Let's see what you can do! Can you comfortably perform these tasks in Ukrainian?
- [x] Name 10 foods and 5 drinks (М36)
- [x] Say what you eat and drink using the accusative case (М37)
- [x] Order food and drinks at a café (М38)
- [x] Ask for prices and buy things at a market (М39)
- [x] Use the accusative case for people (М40)
Here is a quick vocabulary warm-up. Cover the English words below. Can you recall 10 foods and 5 drinks in Ukrainian without looking? Then you are ready.
**Їжа** (food): **борщ** (borscht), **вареники** (dumplings), **салат** (salad), **хліб** (bread), **сир** (cheese), **піца** (pizza), **каша** (porridge), **яєчня** (fried eggs), **суп** (soup), **котлета** (cutlet).
**Напої** (drinks): **кава** (coffee), **чай** (tea), **вода** (water), **сік** (juice), **молоко** (milk).
Let's do a quick grammar warm-up. Check if these four patterns feel completely natural to you:
1. Я їм ___: **борщ** (borscht) → **борщ**, **салат** (salad) → **салат**, **суп** (soup) → **суп**.
2. Я п'ю ___: **кава** (coffee) → **каву**, **вода** (water) → **воду**, **сік** (juice) → **сік**.
3. Мені ___, будь ласка: **піца** (pizza) → **піцу**, **кава** (coffee) → **каву**.
4. Я бачу ___: **Олена** (Olena) → **Олену**, **брат** (brother) → **брата**, **друг** (friend) → **друга**.
If all four feel natural, you are in a great place. If not, revisit modules M37 and M40. Let's test your knowledge!
<!-- INJECT_ACTIVITY: quiz-accusative-check -->
## Читання (Reading Practice)
Read about Anna's day. Notice how she uses the accusative case for food, drinks, and people. Try to find at least six accusative forms as you read.
**День Анни** (Anna's Day)
Анна прокидається. Вона їсть **кашу** (porridge) і п'є **каву з молоком** (coffee with milk) на сніданок. Потім вона іде на **ринок** (market).
<div class="dialogue">

<div class="dialogue-line">— Скільки коштують помідори?</div>

<div class="dialogue-line">— Тридцять гривень кілограм.</div>

<div class="dialogue-line">— Дайте кілограм, будь ласка.</div>

</div>
Анна купує **хліб** (bread), **сир** (cheese), **яблука** (apples), і **салат** (salad).
Потім вона іде в **кафе** (café).
<div class="dialogue">

<div class="dialogue-line">— Тут вільно?</div>

<div class="dialogue-line">— Так, сідайте.</div>

<div class="dialogue-line">— Мені **борщ** (borscht) і **воду** (water), будь ласка.</div>

</div>
Раптом вона бачить подругу:
— О, я бачу **Олену** (Olena)! Олено, привіт!
Олена підходить до неї. Анна каже:
— Ти знаєш мого **брата Михайла** (brother Mykhailo)? Це мій брат.
Вони обідають разом.
<div class="dialogue">

<div class="dialogue-line">— Рахунок, будь ласка. Можна карткою?</div>

<div class="dialogue-line">— Звичайно.</div>

</div>
Check your understanding. Answer these three questions using full Ukrainian sentences. Try to answer them aloud before moving on.
1. Що Анна купує на ринку?
2. Що вона замовляє в кафе?
3. Кого вона бачить у кафе?
<!-- INJECT_ACTIVITY: fill-in-cafe-market -->
## Граматика (Grammar Summary)
**Чотири ключових шаблони A1.6**
You learned all of these patterns in modules M36 through M40. Here is a quick-reference summary so you have everything in one place.
**Pattern 1: Food and drink vocabulary chunks**
You know words for **їжа** (food), **напої** (drinks), and meals: **сніданок** (breakfast), **обід** (lunch), **вечеря** (dinner).
Notice how we group words using the instrumental case to say "with": **кава з молоком** (coffee with milk), **борщ зі сметаною** (borscht with sour cream), **хліб із сиром** (bread with cheese).
- Я їм кашу на сніданок. (I eat porridge for breakfast.)
- Я п'ю каву з молоком. (I drink coffee with milk.)
**Pattern 2: Accusative case for inanimate nouns**
When an object receives an action (like being eaten, bought, or ordered), its ending changes. Masculine inanimate nouns do not change. They look exactly like their dictionary forms: **борщ** → **борщ**, **хліб** → **хліб**, **сік** → **сік**. Feminine nouns ending in -а/-я change to -у/-ю: **кава** → **каву**, **вода** → **воду**, **піца** → **піцу**, **яєчня** → **яєчню**.
| Nominative (Що це?) | Accusative (Що ти їш?) | Example Sentence |
|---|---|---|
| **вода** (water) | **воду** | Я п'ю **воду**. (I am drinking water.) |
| **піца** (pizza) | **піцу** | Я їм **піцу**. (I am eating pizza.) |
| **суп** (soup) | **суп** | Я замовляю **суп**. (I am ordering soup.) |
| **каша** (porridge) | **кашу** | Я їм **кашу**. (I am eating porridge.) |
**Pattern 3: Ordering and prices**
You can navigate a café and a market using these fixed phrases. Note how they build on the vocabulary you already know:
- **Мені ___, будь ласка.** (To me ___, please. / I'll have ___, please.)
- **Скільки коштує?** (How much does it cost?)
- **Скільки коштують помідори?** (How much do the tomatoes cost?)
- **Дайте ___, будь ласка.** (Give [me] ___, please.)
- **Рахунок, будь ласка.** (The bill, please.)
- **Можна карткою?** (Can I pay by card?)
Remember the currency forms depending on the number: **одна гривня** (1), **дві гривні** (2), **п'ять гривень** (5+).
**Pattern 4: Accusative case for animate nouns**
When a person is the object of an action (whom you see or know), the rules differ. Feminine animate nouns follow the same rule as inanimate: **Олена** → **Олену**, **мама** → **маму**. Masculine animate nouns take the genitive ending (-а/-я): **брат** → **брата**, **лікар** → **лікаря**, **друг** → **друга**, **вчитель** → **вчителя**.
Compare these two sentences. One uses an inanimate object, and the other uses an animate object:
- Я бачу **борщ**. (I see the borscht. — inanimate, masculine, no change)
- Я бачу **брата**. (I see the brother. — animate, masculine, ends in -а)
<!-- INJECT_ACTIVITY: group-sort-accusative -->
## Діалог (Connected Dialogue)
Наталя та Дмитро починають день. Читайте і стежте за відмінками. (Natalia and Dmytro start their day. Read and watch the cases.)
**(Сніданок / Breakfast)**
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Наталя:</span> Що ти їш на сніданок? *(What are you eating for breakfast?)*</div>

<div class="dialogue-line"><span class="speaker">Дмитро:</span> Я їм кашу і п'ю каву з молоком. А ти? *(I am eating porridge and drinking coffee with milk. And you?)*</div>

<div class="dialogue-line"><span class="speaker">Наталя:</span> Я їм яєчню і хліб із сиром. *(I am eating fried eggs and bread with cheese.)*</div>

</div>
**(На ринку / At the market)**
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Наталя:</span> Скільки коштують помідори? *(How much do the tomatoes cost?)*</div>

<div class="dialogue-line"><span class="speaker">Продавець:</span> П'ятнадцять гривень кілограм. *(Fifteen hryvnias a kilo.)*</div>

<div class="dialogue-line"><span class="speaker">Наталя:</span> Дорого! А яблука? *(Expensive! And the apples?)*</div>

<div class="dialogue-line"><span class="speaker">Продавець:</span> Двадцять гривень. Дуже смачні! *(Twenty hryvnias. Very tasty!)*</div>

<div class="dialogue-line"><span class="speaker">Наталя:</span> Добре, дайте кілограм яблук, будь ласка. *(Okay, give me a kilo of apples, please.)*</div>

</div>
**(У кафе / At the café)**
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Дмитро:</span> Тут вільно? *(Is it free here?)*</div>

<div class="dialogue-line"><span class="speaker">Офіціант:</span> Так, сідайте! *(Yes, sit down!)*</div>

<div class="dialogue-line"><span class="speaker">Дмитро:</span> Мені борщ і воду, будь ласка. *(I'll have borscht and water, please.)*</div>

<div class="dialogue-line"><span class="speaker">Наталя:</span> О, я бачу Олену! Олено, привіт! Ти знаєш мого брата Дмитра? *(Oh, I see Olena! Olena, hi! Do you know my brother Dmytro?)*</div>

<div class="dialogue-line"><span class="speaker">Олена:</span> Ні, не знаю. Дуже приємно, Дмитре! *(No, I don't. Very nice to meet you, Dmytro!)*</div>

<div class="dialogue-line"><span class="speaker">Дмитро:</span> Рахунок, будь ласка. Можна карткою? *(The bill, please. Can I pay by card?)*</div>

<div class="dialogue-line"><span class="speaker">Офіціант:</span> Звичайно. *(Of course.)*</div>

<div class="dialogue-line"><span class="speaker">Наталя:</span> Все було дуже смачно! *(Everything was very tasty!)*</div>

</div>
Did you spot all the key grammar patterns in the dialogue? Let's highlight a few:
1. Accusative inanimate nouns: **кашу**, **яєчню**, **воду**, **борщ**.
2. Accusative animate nouns: **Олену**, **брата Дмитра**.
3. Everyday café and market phrases: **Мені борщ**, **Дайте кілограм**, **Рахунок, будь ласка**.
<!-- INJECT_ACTIVITY: quiz-shopping-cafe -->
## Підсумок — Summary
You have successfully completed phase A1.6 — Food and Shopping. You have expanded your vocabulary and grammar significantly. Here is exactly what you can now do in Ukrainian:
- ✓ Talk about **їжа та напої** (food and drinks) and meals (М36).
- ✓ Use the accusative case for inanimate nouns to describe what you eat and drink: **борщ**, **каву**, **воду**, **піцу** (М37).
- ✓ Order at a **кафе** (café) with confidence: «Мені борщ, будь ласка» / «Рахунок, будь ласка» / «Можна карткою?» (М38).
- ✓ Shop at the **ринок** (market): «Скільки коштує?» / «Дайте кілограм» / **гривня**, **гривні**, **гривень** (М39).
- ✓ Use the accusative case for animate nouns to talk about people: «Я бачу Олену» / «Я знаю брата» (М40).
**Наступний крок — A1.7: Спілкування.** (Next step — A1.7: Communication.) You will learn to make plans, write messages, and talk on the phone. You are ready for A1.7!

**Deterministic word count: 1386 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 128 words | Not found: 10 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Анни — NOT IN VESUM
  ✗ Дмитра — NOT IN VESUM
  ✗ Дмитре — NOT IN VESUM
  ✗ Дмитро — NOT IN VESUM
  ✗ Михайла — NOT IN VESUM
  ✗ Наталя — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Олену — NOT IN VESUM

All 128 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp__rag__verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp__rag__verify_lemma` — full declension/conjugation for a lemma
- `mcp__rag__search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp__rag__query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp__rag__query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp__rag__search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp__rag__search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp__rag__search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp__rag__search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp__rag__query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp__rag__search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp__rag__search_literary` — verify literary references against primary sources
- `mcp__rag__query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
