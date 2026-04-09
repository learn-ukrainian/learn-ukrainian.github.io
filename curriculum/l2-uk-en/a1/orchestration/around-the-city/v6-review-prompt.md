<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 33: Around the City (A1, A1.5 [Places])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-033
level: A1
sequence: 33
slug: around-the-city
version: '1.2'
title: Around the City
subtitle: Де/куди + directions — navigating in Ukrainian
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Combine Де? (locative) and Куди? (accusative) in real navigation
- Give and follow simple directions
- Describe your neighborhood and daily routes
- Synthesize M28-M32 skills in connected urban communication
dialogue_situations:
- setting: Walking tour of Lviv old town — going from Площа Ринок (f, main square)
    to Оперний театр (m, Opera house) to Високий замок (m, High Castle). Де ми? На
    площі. Куди далі? В театр. Звідки прийшли? З замку.
  speakers:
  - Гід (guide)
  - Туристи
  motivation: Де/Куди/Звідки with площа(f), театр(m), замок(m), парк(m)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Asking for directions: — Вибачте, як дістатися до бібліотеки? —
    Ідіть прямо, потім направо. Бібліотека на розі. — А музей? — Музей далеко. Їдьте
    на метро до центру. Combines directions + transport + city places.'
  - 'Dialogue 2 — Describing your route: — Як ти дістаєшся на роботу? — Спочатку йду
    на зупинку. Потім їду автобусом до центру. — А потім? — Потім іду пішки п''ять
    хвилин. Робота в офісі на площі. Daily route using sequence words + transport
    + places.'
- section: Де і куди разом (Where and Where To Together)
  words: 300
  points:
  - 'Real navigation uses both cases together: Я зараз у парку (де? — locative). Я
    йду в магазин (куди? — accusative). Магазин на вулиці Шевченка (де? — locative).
    Потім їду на роботу (куди? — accusative). The constant switch between де? and
    куди? is natural Ukrainian.'
  - 'Preposition patterns (synthesis): | Situation | Question | Form | | Static |
    Де ти? | в/на + locative | | Direction | Куди йдеш? | в/на + accusative | | By
    transport | Як? Чим? | автобусом / на метро | | Distance | Далеко? | далеко /
    близько / пішки |'
- section: Мій район (My Neighborhood)
  words: 300
  points:
  - 'Describing where you live: Я живу на вулиці Франка. Біля мого дому є парк і магазин.
    Школа далеко — треба їхати автобусом. Аптека близько, можна піти пішки. У моєму
    районі є кафе, ресторан і бібліотека.'
  - 'Useful phrases for city life: пішки (on foot), хвилина (minute) — П''ять хвилин
    пішки. далеко/близько від (far/near from — chunk). У центрі міста / на околиці
    (in the center / on the outskirts).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Urban communication toolkit: Asking: Де...? Як дістатися до...? Directions: прямо,
    направо, наліво. Location: в/на + locative, в/на + accusative. Transport: автобусом,
    на метро, пішки. Self-check: Describe your route from home to work/school.'
vocabulary_hints:
  required:
  - пішки (on foot)
  - хвилина (minute, f)
  - район (neighborhood, m)
  - центр (center, m)
  - вибачте (excuse me)
  recommended:
  - дістатися (to get to)
  - ідіть (go! — imperative, preview)
  - їдьте (go by transport! — imperative, preview)
  - поруч (nearby)
activity_hints:
- type: fill-in
  focus: Give directions using прямо, направо, наліво
  items: 6
  blanks:
  - Ідіть {прямо}, потім {направо}. Бібліотека на розі.
  - Вибачте, як дістатися до музею? — Ідіть {наліво}.
  - Аптека близько. Ідіть {прямо} п'ять хвилин.
  - Потім ідіть {направо}, школа там.
  - Йдіть {прямо}, а потім {наліво}.
  - Ресторан поруч. Ідіть {прямо} і {направо}.
- type: quiz
  focus: Де (locative) or Куди (accusative) in context
  items: 6
  questions:
  - Я зараз... (в парку / в парк)
  - Я йду... (в магазин / в магазині)
  - Магазин на... (вулиці / вулицю)
  - Потім їду на... (роботу / роботі)
  - Ми зараз у... (центрі / центр)
  - Вона йде в... (офіс / офісі)
- type: fill-in
  focus: Describe route with transport (автобусом, пішки, на метро)
  items: 6
  blanks:
  - Я їду в центр {на метро}.
  - Потім іду {пішки} п'ять хвилин.
  - Вона їде на роботу {автобусом}.
  - Школа далеко, треба їхати {на метро}.
  - Парк близько, ми йдемо {пішки}.
  - Ми їдемо в ресторан {автобусом}.
- type: match-up
  focus: Match question to logical response for navigation
  items: 6
  pairs:
  - Вибачте, як дістатися до бібліотеки?: Ідіть прямо, потім направо.
  - Де музей?: Він у центрі.
  - Як ти дістаєшся на роботу?: Їду автобусом.
  - Школа далеко?: Ні, близько. П'ять хвилин пішки.
  - Куди ви йдете?: У магазин.
  - Де ти живеш?: На вулиці Франка.
connects_to:
- a1-034 (Where From?)
prerequisites:
- a1-032 (Transport)
grammar:
- 'Synthesis: Де? (locative) + Куди? (accusative) in real navigation'
- Direction + transport + location combined
- 'Imperative preview: ідіть, їдьте (formal commands)'
register: розмовний
references:
- title: Synthesis of M28-M32 skills
  notes: Applied communication — no new grammar, just integration.

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги

Lviv is a beautiful, historic city in western Ukraine. Imagine you are taking a walking tour of the old town. You want to see the famous architecture, but the narrow cobblestone streets can be confusing. You need to navigate from **Площа Ринок** (Market Square) to the majestic **Оперний театр** (Opera House), and then up to **Високий замок** (High Castle). You might ask: **Де ми?** (Where are we?). The guide answers: **На площі.** (On the square). Then you ask: **Куди далі?** (Where to next?). The reply is: **В театр.** (To the theater). And if someone asks: **Звідки ви прийшли?** (Where did you come from?), you say: **З замку.** (From the castle). Navigating a city means understanding where you are, where you are going, and where you came from.

> **Турист:** Вибачте, як дістатися до бібліотеки? *(Excuse me, how to get to the library?)*
> **Гід:** Ідіть прямо, потім направо. Бібліотека на розі. *(Go straight, then to the right. The library is on the corner.)*
> **Турист:** А музей? *(And the museum?)*
> **Гід:** Музей далеко. Їдьте на метро до центру. *(The museum is far. Go by metro to the center.)*

This dialogue shows a typical street interaction. The tourist uses a polite greeting and asks for simple directions to local landmarks. The guide provides clear, step-by-step instructions using directional adverbs and landmarks, then suggests public transport for a longer distance. Every urban interaction relies on these basic, highly functional patterns.

> **Оксана:** Як ти дістаєшся на роботу? *(How do you get to work?)*
> **Тарас:** Спочатку йду на зупинку. Потім їду автобусом до центру. *(First I go to the stop. Then I go by bus to the center.)*
> **Оксана:** А потім? *(And then?)*
> **Тарас:** Потім іду пішки п'ять хвилин. Робота в офісі на площі. *(Then I go on foot for five minutes. Work is in an office on the square.)*

Here, two friends discuss their daily commute. They break down the journey into distinct, logical steps. They mention walking to a transport hub, taking a specific vehicle, and finally arriving at their destination. This structure is very common when describing regular habits and routines.

The phrase **Вибачте** (Excuse me) is the most polite and natural way to get a stranger's attention in Ukrainian. When giving directions, the guide uses two different command forms. **Ідіть** (Go / Walk) is an instruction to move on foot. When suggesting public transport, the guide switches to **Їдьте** (Go / Travel by vehicle). Both verbs end in **-іть** / **-те**, marking the formal "you" (**ви**) form.

:::tip
This formal ending is essential for politeness. Using the informal form with strangers on the street is considered rude. Always stick to the formal commands when asking for or giving directions!
:::

In the second dialogue, Taras structures his route using sequence words. The word **спочатку** (first / initially) starts the explanation, and **потім** (then / afterward) connects the steps. This creates a logical narrative. We also see two ways to talk about transportation. To travel by a vehicle, Ukrainians often use the instrumental case, such as **автобусом** (by bus). Alternatively, they use the preposition **на** with the locative case, such as **на метро** (by metro). When moving under your own power, use the specific adverb **пішки** (on foot).

<!-- INJECT_ACTIVITY: match-navigation-responses -->

## Де і куди разом

Real urban navigation requires a constant, fluid switch between two core concepts: static location and the direction of movement. When you describe your current position, you answer the question **Де?** (Where?). This requires the locative case. For example: **Я зараз у парку.** (I am in the park now.) However, when you describe your destination, you answer the question **Куди?** (Where to?). This requires the accusative case. For example: **Я йду в магазин.** (I am going to the store.) A natural Ukrainian conversation blends these forms effortlessly. You might say: **Магазин на вулиці Шевченка.** (The store is on Shevchenko street — locative). And immediately follow with: **Потім їду на роботу.** (Then I am going to work — accusative). Recognizing which case to use is the key to clear communication.

The prepositional patterns for **в** (in) and **на** (on) require careful attention. The choice of preposition stays the same, but the noun ending changes based on whether you describe location or direction. Consider these contrasting examples:

*   **На вулиці** (On the street — Locative: Де?) vs. **На вулицю** (Onto the street — Accusative: Куди?).
*   **На площі** (On the square — Locative: Де?) vs. **На площу** (Onto the square — Accusative: Куди?).
*   **В офісі** (In the office — Locative: Де?) vs. **В офіс** (Into the office — Accusative: Куди?).

Feminine nouns change clearly from **-і** to **-ю** or **-у**. Masculine inanimate nouns like **офіс** show a zero-ending in the accusative direction form but take an **-і** ending for static location.

:::note
You might notice that the preposition **в** (in) frequently changes to **у** to make the sentence sound smoother (like **у парку** instead of **в парку**). The grammatical case and meaning remain exactly the same.
:::

This synthesis table categorizes the essential navigation information. It separates static locations, active movements, transportation methods, and physical distance.

| Category | Question | Grammar Form | Examples |
| :--- | :--- | :--- | :--- |
| Location (Static) | **Де ти?** (Where are you?) | **в / на** + Locative | **В парку, на площі.** |
| Destination (Direction) | **Куди йдеш?** (Where are you going?) | **в / на** + Accusative | **В парк, на площу.** |
| Transport Method | **Як? / Чим?** (How? / By what?) | Instrumental OR **на** + Loc | **Автобусом, на метро.** |
| Distance | **Далеко?** (Is it far?) | Adverbs | **Далеко, близько, пішки.** |

When you combine these elements, you can give clear, formal directions to anyone. This is where the imperative mood becomes very useful. We use formal commands ending in **-іть** or **-те** to speak politely to strangers. The verb **ідіть** (go / walk) is the standard command for pedestrian movement. For example: **Ідіть прямо.** (Go straight.) If the destination requires a vehicle, you must use the verb **їхати** (to ride). Its formal command form is irregular: **їдьте** (go / travel). For example: **Їдьте на метро.** (Go by metro.) Using these formal commands ensures you sound respectful and helpful on the streets of any Ukrainian city.

<!-- INJECT_ACTIVITY: quiz-de-vs-kudy -->

<!-- INJECT_ACTIVITY: fill-in-directions -->

## Мій район

To describe your daily life, you need vocabulary for distance and proximity. The most common adjectives for space are paired with the preposition **від** (from), requiring the genitive case. We use the chunks **далеко від** (far from) and **близько від** (near from / close to). You might say: **Школа далеко від дому.** (The school is far from home.) If a place is highly accessible, you say: **Аптека близько.** (The pharmacy is near.) You can add: **Можна піти пішки.** (It is possible to go on foot.) Another excellent word for proximity is **поруч** (nearby / next door). If you live right next to a bakery, you say: **Пекарня поруч.** (The bakery is nearby.)

Your daily life revolves around your local area. The Ukrainian word for a neighborhood or a city district is **район**. When describing your city, you usually relate locations to the **центр** (center) or the **околиця** (outskirts). Living in the center is very different from living on the outskirts. The standard way to state your address is to use the preposition **на** with the word **вулиця** (street) in the locative case. You say: **Я живу на вулиці Шевченка.** (I live on Shevchenko street.) The street name itself often takes a genitive form (like Шевченка), but simply remember the phrase as a fixed chunk.

Time is a crucial part of navigation. We often measure distance in time rather than kilometers. The word for minute is **хвилина**. A very common and natural phrase is **п'ять хвилин пішки** (five minutes on foot). For example: **Супермаркет близько, п'ять хвилин пішки.** (The supermarket is near, five minutes on foot.) To navigate successfully, you must recognize physical landmarks. A **перехрестя** (intersection) is a common reference point for turning. A **зупинка** (stop) is essential for catching a bus.

A cohesive text describing a personal neighborhood combines places, transport, and directions into a single narrative.

> **Я живу на вулиці Франка. Біля мого дому є парк і магазин. Школа далеко — треба їхати автобусом. Аптека близько, можна піти пішки. У моєму районі є кафе, ресторан і бібліотека. Бібліотека на розі. Ідіть прямо, потім направо.**
> *(I live on Franko street. Near my house there is a park and a store. The school is far — one needs to go by bus. The pharmacy is near, it is possible to go on foot. In my neighborhood there is a cafe, a restaurant, and a library. The library is on the corner. Go straight, then to the right.)*

This description uses static locations, explains how to travel to distant places, and gives specific walking instructions.

<!-- INJECT_ACTIVITY: fill-in-transport-route -->

## Підсумок — Summary

The urban communication toolkit contains everything needed for daily navigation. Asking: **Де...?** (Where...?), **Як дістатися до...?** (How to get to...?). Directions: **прямо** (straight), **направо** (to the right), **наліво** (to the left). Location: **в/на** + locative, **в/на** + accusative. Transport: **автобусом**, **на метро**, **пішки**. These linguistic tools allow you to move confidently and independently.

When speaking Ukrainian, cultural and linguistic precision matters. Another critical distinction involves transport hubs. In English, "station" is a generic term. In Ukraine, you must be specific. If you need a bus, you ask for the **автовокзал** (bus station). If you need a train, you ask for the **залізничний вокзал** (railway station). Mixing these up will send you to the wrong side of the city!

:::caution
Many learners try to translate the English "I apologize" directly into Ukrainian as **Вибачаюся**. This is a Russian calque and sounds unnatural because it literally means "I apologize myself." The correct, polite form is always the imperative **Вибачте** (Excuse me).
:::

Perform a self-check to verify these skills. Review the questions and situations below to see if you are ready for a real Ukrainian city.
*   Чи можете ви запитати дорогу? (Can you ask for directions?) Example: **Вибачте, де бібліотека?** (Excuse me, where is the library?)
*   Чи можете ви сказати **направо** і **наліво**? (Can you say "to the right" and "to the left"?)
*   Чи знаєте ви різницю між **у центрі** (де?) та **в центр** (куди?)? (Do you know the difference between "in the center" — locative, and "into the center" — accusative?)
*   Опишіть свій шлях: Як ви дістаєтеся на роботу чи в університет? (Describe your route from home to work/school: How do you get to work or to the university?) You should be able to say: **Спочатку йду... потім їду...** (First I go... then I go...).
Mastering these scenarios prepares you for authentic communication in any town.
</generated_module_content>

**PIPELINE NOTE — Word count: 1702 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 111 words | Not found: 4 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Оксана — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Шевченка — NOT IN VESUM
  ✗ іть — NOT IN VESUM

All 111 other words are confirmed to exist in VESUM.

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
