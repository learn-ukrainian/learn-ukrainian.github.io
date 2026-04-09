<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 35: Checkpoint: Places (A1, A1.5 [Places])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-035
level: A1
sequence: 35
slug: checkpoint-places
version: '1.2'
title: 'Checkpoint: Places'
subtitle: Can you navigate a Ukrainian city?
focus: review
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Demonstrate correct use of euphony (у/в, і/й, з/із/зі)
- Use locative for location (Де?) and accusative for direction (Куди?)
- Navigate using city vocabulary, transport, and directions
- Answer Звідки? with genitive chunks
- Combine all A1.5 skills in connected urban scenarios
dialogue_situations:
- setting: 'Video-calling a friend while walking through Одеса (Odesa) — showing:
    Дерибасівська вулиця (f), Потьомкінські сходи (pl, Potemkin Stairs), порт (m,
    port), пляж (m, beach). Describing where you are, where you''re going.'
  speakers:
  - Мешканець (filming)
  - Онлайн-друг (watching)
  motivation: Consolidation with вулиця(f), сходи(pl), порт(m), пляж(m)
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M28-M34: Can you apply euphony rules? (M28) Can you say where
    things are? (M29) Can you name city places? (M30) Can you say where you''re going?
    (M31) Can you use transport? (M32) Can you give directions? (M33) Can you say
    where you''re from? (M34)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using vocabulary from M28-M34. Content: a tourist navigates
    Kyiv — asks for directions, takes metro, finds a museum, describes where they''re
    from and where they''re going. Uses euphony, locative, accusative, genitive chunks,
    transport.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.5: 1. Euphony: у/в, і/й, з/із/зі (M28) 2. Де? → в/на + locative:
    в школі, на роботі (M29) 3. Куди? → в/на + accusative: у школу, на роботу (M31)
    4. Звідки? → з + genitive chunk: з України, з роботи (M34) 5. Transport: автобусом,
    на метро (M32) 6. Directions: прямо, направо, наліво (M33) 7. City places with
    correct prepositions (M30)'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A tourist in Kyiv asks for help: — Вибачте, я з Канади. Де тут музей? — Музей
    у центрі. Ідіть на метро до станції Хрещатик. — А як дістатися від метро? — Вийдіть
    і йдіть направо. Музей на площі. — Дякую! А потім я хочу їхати у Львів. Де вокзал?
    — Вокзал далеко, їдьте на метро до станції Вокзальна. Uses all A1.5 skills in
    one realistic scenario.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.5 achievement summary: You can now navigate Ukrainian cities. You know euphony
    rules for natural speech. You can say WHERE something is (locative). You can say
    WHERE you''re GOING (accusative). You can say WHERE you''re FROM (genitive chunks).
    You can use transport and give directions. Next: A1.6 — Food and Shopping (ordering,
    buying, accusative for objects).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Choose the correct question: Де? Куди? Звідки?'
  items: 8
  questions:
  - '... ти живеш? — У Києві. (Де / Куди / Звідки)'
  - '... ти йдеш? — У магазин. (Куди / Де / Звідки)'
  - '... ви? — Ми з Канади. (Звідки / Де / Куди)'
  - '... музей? — У центрі. (Де / Куди / Звідки)'
  - '... їде автобус? — На вокзал. (Куди / Де / Звідки)'
  - '... ти їдеш? — З роботи. (Звідки / Куди / Де)'
  - '... аптека? — Направо. (Де / Куди / Звідки)'
  - '... вони? — Зі США. (Звідки / Де / Куди)'
- type: fill-in
  focus: Complete the connected dialogue with correct forms
  items: 6
  blanks:
  - Вибачте, я {з Канади}. Де тут музей?
  - Музей {у центрі}. Ідіть на метро.
  - А як дістатися {від метро}?
  - Вийдіть і йдіть {направо}. Музей на площі.
  - Я хочу їхати {у Львів}. Де вокзал?
  - Вокзал далеко, їдьте {на метро}.
- type: group-sort
  focus: Sort phrases by case/function (Locative, Accusative, Genitive chunks)
  items: 9
  groups:
  - name: Локація (Де?)
    items:
    - у школі
    - на площі
    - в центрі
  - name: Напрямок (Куди?)
    items:
    - на роботу
    - у Львів
    - в Канаду
  - name: Походження (Звідки?)
    items:
    - з України
    - зі США
    - з роботи
- type: quiz
  focus: 'Euphony rules check: у/в, і/й, з/із/зі'
  items: 8
  questions:
  - Брат ... сестра (і / й)
  - Вона живе ... Львові (у / в)
  - Я йду ... школи (зі / з)
  - Він ... Києві (у / в)
  - Мама ... тато (і / й)
  - Ми ... України (з / із)
  - Я ... кімнаті (в / у)
  - Вона ... США (зі / з)
connects_to:
- a1-036 (Food and Drink)
prerequisites:
- a1-034 (Where From?)
grammar:
- 'Review: locative for location (Де?)'
- 'Review: accusative for direction (Куди?)'
- 'Review: genitive chunks for origin (Звідки?)'
- 'Review: euphony and transport'
register: розмовний
references:
- title: Synthesis of M28-M34 content
  notes: No new material — review and integration of A1.5 phase.

</plan_content>

## Generated Content

<generated_module_content>
## Що ми знаємо? (What Do We Know?)

Navigating a new city is often your very first real test of survival in a completely new language environment. Before reaching this point in your studies, you could name a few isolated objects, describe who you are, or exchange basic daily greetings. Now, you have acquired the tools to confidently step out into the street, find what you need, and interact with the world around you. This module serves as a comprehensive checkpoint to review the essential skills you acquired throughout the "Places" section. 

The leap from speaking in isolated words to building connected urban navigation phrases is a huge milestone. You are no longer just pointing and saying **центр** (center) or **метро** (subway); instead, you are constructing full ideas by saying **у центрі** (in the center) and **на метро** (by subway). This review highlights the critical differences between simply being somewhere, actively going somewhere, and returning from somewhere. 

Evaluate exactly what you know so far. Ask yourself the following questions to see if you are truly ready to navigate the busy streets of Ukraine:

*   **Чи можу я вибрати між «у» та «в»?** (Can I choose between «у» and «в»?) — This tests your grasp of euphony rules for smooth pronunciation.
*   **Чи знаю я, як сказати, де я?** (Do I know how to say where I am?) — This checks if you can use the locative case to state your location.
*   **Чи можу я назвати місця в місті?** (Can I name places in the city?) — This ensures you recognize essential city vocabulary.
*   **Чи можу я сказати, куди я йду?** (Can I say where I am going?) — This confirms you understand the accusative case for direction.
*   **Чи можу я користуватися транспортом?** (Can I use transport?) — This checks your ability to say how you are traveling.
*   **Чи можу я запитати дорогу?** (Can I ask for directions?) — This ensures you can communicate with locals and follow a route.
*   **Чи можу я сказати, звідки я приїхав?** (Can I say where I came from?) — This confirms you can use genitive chunks for origin.

If you can answer these questions affirmatively, you have a solid foundation for the rest of the A1 level.

<!-- INJECT_ACTIVITY: quiz-question-choice -->

## Читання (Reading Practice)

Reading short, contextual narratives in Ukrainian helps solidify grammar patterns naturally without feeling like you are memorizing rules. The following reading practice follows a traveler named Марк who arrives in the capital city. He begins his journey at the main train station, known as **вокзал** (train station), and needs to locate his accommodation, a **готель** (hotel), which is situated right in the heart of the city. Finally, he navigates his way to one of the most famous historical landmarks in the capital, **Золоті ворота** (Golden Gate). 

Read the text below carefully. Pay close attention to how Mark uses prepositions like **у**, **в**, **на**, and **з** depending on whether he is describing his static location, his destination, or his origin.

*   **Я зараз у Києві.** (I am currently in Kyiv.)
*   **Я з Польщі.** (I am from Poland.)
*   **Мій готель у центрі.** (My hotel is in the center.)
*   **Я йду пішки.** (I am walking on foot.)
*   **Вокзал далеко.** (The train station is far.)
*   **Я їду на метро.** (I am going by subway.)
*   **Скажіть, будь ласка, де музей?** (Tell me, please, where is the museum?)
*   **Я йду направо.** (I am walking to the right.)
*   **Тут площа.** (Here is a square.)
*   **Золоті ворота близько.** (Golden Gate is near.)
*   **Я вже біля музею.** (I am already near the museum.)

Notice how Mark integrates all the fundamental A1.5 vocabulary and grammar in just a few straightforward sentences. He seamlessly uses **на метро** (by subway) for his mode of transport, **направо** (to the right) for simple directions, and **біля музею** (near the museum) to establish his exact location relative to another landmark. 

:::tip
As you read Ukrainian texts, try your best not to translate word for word in your head. Instead, visualize the scene unfolding. Picture Mark exiting the train station, looking at a map, and walking towards the center. This visualization technique helps you link the Ukrainian words directly to real-world concepts.
:::

## Граматика (Grammar Summary)

The grammatical patterns from this phase rely on a few core principles. First, the Ukrainian language places a very high value on a smooth, flowing sound, a concept known as euphony. The rules of euphony determine whether we should use **у** or **в**, **і** or **й**, and **з**, **із**, or **зі**. The basic guiding principle is to avoid awkward clusters of consonants or vowels. 

Compare the following pairs:
*   **Він у Львові** (He is in Lviv) versus **Вона в Одесі** (She is in Odesa). We use **у** between consonants, and **в** between vowels.
*   **Брат і сестра** (Brother and sister) versus **Тато й мама** (Dad and mom). We use **і** between consonants, and **й** between vowels.
*   **Зі школи** (From school) versus **З роботи** (From work). We use **зі** before difficult consonant clusters, but **з** before a single consonant.

The most crucial grammatical concept in urban navigation is understanding the three main directional questions. The specific noun case you use depends entirely on the question you are answering:

*   **Де?** (Where?) indicates a static location. It uses the Locative case. 
    *   **В аптеці** (In the pharmacy)
    *   **В школі** (In school)
    *   **На роботі** (At work)
*   **Куди?** (To where?) indicates the direction of movement. It uses the Accusative case.
    *   **В аптеку** (To the pharmacy)
    *   **У школу** (To school)
    *   **На роботу** (To work)
*   **Звідки?** (From where?) indicates an origin or starting point. It uses the Genitive case with the preposition **з** (or **із**/**зі**).
    *   **З аптеки** (From the pharmacy)
    *   **З України** (From Ukraine)
    *   **З роботи** (From work)

Notice the distinct contrast between **на роботі** (location) and **на роботу** (direction). Furthermore, the preposition **на** is generally used for open spaces, events, and abstract concepts, while **в** / **у** is strictly used for enclosed physical structures. This directional system also applies when matching city places with correct prepositions, taking transport like **автобусом** (by bus) or **на метро** (by subway), and following adverbs for directions such as **прямо** (straight), **направо** (to the right), and **наліво** (to the left).

<!-- INJECT_ACTIVITY: group-sort-cases -->
<!-- INJECT_ACTIVITY: quiz-euphony-check -->

## Діалог (Connected Dialogue)

Imagine a very common, real-world scenario: a tourist from Canada arrives at a busy, crowded metro station in Kyiv. They need to find a specific museum first, and then head over to the main train station, the **вокзал**. When approaching a stranger on the street for help, it is absolutely vital to emphasize the polite register. Starting your request with **Вибачте** (Excuse me) and **Скажіть, будь ласка** (Tell me, please) shows cultural respect and instantly makes people much more willing to assist you. 

Read the multi-turn connected dialogue below. Pay close attention to how the tourist combines phrases indicating origin, location, and direction into a single, cohesive conversation.

> **Турист:** Вибачте, я з Канади. Де тут музей? *(Excuse me, I am from Canada. Where is the museum here?)*
> **Місцевий:** Музей у центрі. Їдьте на метро до станції Хрещатик. *(The museum is in the center. Go by subway to Khreshchatyk station.)*
> **Турист:** А як дістатися від метро? *(And how to get there from the subway?)*
> **Місцевий:** Вийдіть і йдіть направо. Музей на площі. *(Exit and walk to the right. The museum is on the square.)*
> **Турист:** Дякую! А потім я хочу їхати у Львів. Де вокзал? *(Thank you! And then I want to go to Lviv. Where is the train station?)*
> **Місцевий:** Вокзал далеко. Їдьте на метро до станції Вокзальна. *(The train station is far. Go by subway to Vokzalna station.)*

This exchange perfectly demonstrates practical functional language in action. Notice the specific use of the word **дістатися** (to get to). While **йти** (to go on foot) and **їхати** (to go by vehicle) specify the exact method of transport, **дістатися** focuses purely on the goal of reaching the destination, making it the perfect word for asking directions. 

You also see how prepositions shift based on the point of reference. The local uses **від метро** (from the subway), showing the starting point of the walking route, and **до вокзалу** (to the station) to show the end point. 

:::note
To fully consolidate your urban vocabulary, try describing your own city or a city you love. Imagine video-calling a friend while walking through a coastal city like **Одеса** (Odesa). You might show them the sights: **Дерибасівська вулиця** (Derybasivska street), the famous **Потьомкінські сходи** (Potemkin Stairs), a large **порт** (port), and a sunny **пляж** (beach). Practice describing exactly where you are and where you are going using these nouns!
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue-forms -->

## Підсумок — Summary

The following points summarize your A1.5 achievements. 

**Я тепер можу...** (I can now...):
*   Apply basic euphony rules. You know how to instinctively alternate between **у** and **в**, or **і** and **й**, to ensure your spoken Ukrainian maintains a natural, flowing rhythm.
*   State your exact location. You can confidently answer the question **Де?** (Where?) using the locative case, such as saying **в готелі** (in the hotel) or **на площі** (on the square).
*   Indicate your direction of travel. You can accurately answer the question **Куди?** (To where?) using the accusative case, such as stating you are going **у парк** (to the park).
*   Use city transport options. You can explain how you are traveling from point A to point B, using forms like **автобусом** (by bus) or **на метро** (by subway).
*   Give and follow street directions. You understand vital navigation commands like **направо** (to the right), **наліво** (to the left), and **прямо** (straight).
*   State your country of origin. You can seamlessly answer the question **Звідки?** (From where?), telling people you are **з України** (from Ukraine) or from another specific country.

You can now find your way to a shop, a museum, or a restaurant, but what happens when you finally walk inside the building? In the upcoming A1.6 module, "Food and Shopping," we will transition directly from navigating the outdoor streets to interacting within these indoor establishments. You will learn the specific language required for ordering food, buying groceries, and using the Accusative case to talk about direct objects. Get ready to proudly say **Я хочу каву** (I want coffee) and master the art of the daily transaction!
</generated_module_content>

**PIPELINE NOTE — Word count: 1626 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 95 words | Not found: 9 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Дерибасівська — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Польщі — NOT IN VESUM
  ✗ Хрещатик — NOT IN VESUM

All 95 other words are confirmed to exist in VESUM.

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
