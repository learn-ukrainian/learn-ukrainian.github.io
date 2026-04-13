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
version: '1.3'
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
- title: Большакова Grade 2, розділ «Моє місто»
  notes: Basic directions vocabulary (прямо, направо, наліво), neighborhood descriptions,
    asking/giving directions at A1 level.

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

Navigating a city requires a mix of spatial awareness and clear communication. Imagine a walking tour in the old town of Lviv. The route goes from **Площа Ринок** (Rynok Square, the main square) to the **Оперний театр** (Opera House), and finally up to the **Високий замок** (High Castle). Moving between these landmarks means you constantly need to ask where things are and where to go next. A guide can turn that route into a short real exchange:

> **Гід:** **Де ми зараз?** *(Where are we now?)*
> **Туристи:** **Ми на площі Ринок.** *(We are at Rynok Square.)*
> **Гід:** **Куди йдемо далі?** *(Where are we going next?)*
> **Туристи:** **В театр.** *(To the theater.)*
> **Гід:** **Звідки ми прийшли?** *(Where did we come from?)*
> **Туристи:** **З замку.** *(From the castle.)*

When asking strangers for help on the street, directness combined with polite markers is the most natural approach. The formal imperative forms **ідіть** (go! - on foot) and **їдьте** (go! - by transport) are essential for giving or receiving directions safely.

> **Турист:** **Вибачте, як дістатися до бібліотеки?** *(Excuse me, how to get to the library?)*
> **Гід:** **Ідіть прямо, потім направо. Бібліотека на розі.** *(Go straight, then to the right. The library is on the corner.)*
> **Турист:** **А музей?** *(And the museum?)*
> **Гід:** **Музей далеко. Їдьте трамваєм до центру.** *(The museum is far. Go by tram to the center.)*

This brief interaction combines essential movement directions, specific modes of transport, and clear city landmarks. The adverb **направо** (to the right) functions as a simple direction without requiring complex case changes. The noun phrase **на розі** (on the corner) is a fixed locative chunk. The verb **дістатися** (to get to) is the standard, natural way to ask about reaching a destination.

:::tip
The phrase **на розі** (on the corner) is a highly common exception. The noun **ріг** (corner) changes its root vowel from **і** to **о** in the locative case.
:::

<!-- INJECT_ACTIVITY: fill-in-directions -->

Not all navigation happens on foot or as a tourist. Daily routines require combining different transport methods and sequence words to describe a commute.

> **Оксана:** **Як ти дістаєшся на роботу?** *(How do you get to work?)*
> **Тарас:** **Спочатку йду на зупинку. Потім їду автобусом до центру.** *(First I go to the stop. Then I go by bus to the center.)*
> **Оксана:** **А потім?** *(And then?)*
> **Тарас:** **Потім іду пішки п'ять хвилин. Робота в офісі на площі.** *(Then I go on foot for five minutes. Work is in an office on the square.)*

Describing a daily route involves sequencing actions. The adverb **спочатку** (first/initially) sets up the beginning of the journey, while **потім** (then/afterwards) links the subsequent steps. The transition from walking to taking transport is a core part of urban life, demonstrating how vocabulary adapts to the physical reality of the city.

## Де і куди разом (Where and Where To Together)

The contrast between static location and active direction is fundamental to Ukrainian grammar. Real navigation uses both concepts together, switching back and forth depending on the verb.

*   **Я зараз у парку.** *(I am now in the park.)* — **Де?** (Where?) triggers the locative case.
*   **Я йду в магазин.** *(I am going to the store.)* — **Куди?** (Where to?) triggers the accusative case.
*   **Магазин на вулиці Шевченка.** *(The store is on Shevchenko street.)* — **Де?** (Where?) returns to the locative.
*   **Потім їду на роботу.** *(Then I go to work.)* — **Куди?** (Where to?) requires the accusative.

This constant switch between **де** and **куди** is a hallmark of natural Ukrainian speech. A static verb of position anchors you in a location, while a verb of motion pushes you toward a destination.

:::caution
Do not confuse **де** (where - static) with **куди** (where to - directional). In English, we often use "where" for both ("Where are you?" vs. "Where are you going?"), but Ukrainian strictly separates them. Using **де** with a verb of motion sounds unnatural.
:::

Preposition patterns synthesize these rules into a clear communication toolkit. The choice of preposition and case depends entirely on the question being answered. The destination itself does not dictate the grammar; the action dictates it.

| Situation | Question | Form |
|---|---|---|
| Static | **Де ти?** | **в/на** + locative |
| Direction | **Куди йдеш?** | **в/на** + accusative |
| By transport | **Як? Чим?** | **автобусом / на метро** |
| Distance | **Далеко?** | **далеко / близько / пішки** |

When answering the question **Де ти?** (Where are you?), you must use the prepositions **в/на** with the locative case, as in **Магазин на вулиці Шевченка**. When answering **Куди йдеш?** (Where are you going to?), you must switch to **в/на** with the accusative case, as seen in the phrase **Потім їду на роботу**. The preposition remains the same, but the ending of the noun changes to reflect the movement.

<!-- INJECT_ACTIVITY: quiz-locative-accusative -->

Moving through the city requires specifying the mechanics of transport and distance. When answering the questions **Як?** (How?) and **Чим?** (By what means?), Ukrainian relies on distinct grammatical structures. The instrumental case is used for vehicles you ride inside, like **автобусом** (by bus). However, borrowed words like **метро** (metro/subway) do not decline, so the phrase remains **на метро** (by metro).

Distance can be described relatively using the adverbs **далеко** (far) and **близько** (near/close). For shorter distances, the adverb **пішки** (on foot) indicates walking.

*   **Музей далеко.** *(The museum is far.)*
*   **Парк близько.** *(The park is near.)*
*   **Ми йдемо пішки.** *(We are going on foot.)*

These descriptors provide practical context for anyone trying to navigate an unfamiliar area. Measuring distance through the required mode of transport is the most natural way to explain city geography.

## Мій район (My Neighborhood)

Describing where you live requires grounding your location relative to other landmarks. The noun **район** (neighborhood/district, m) refers to a specific section of a city. The preposition **біля** (near/by) is used to establish proximity and always pairs with the genitive case.

*   **Я живу на вулиці Франка.** *(I live on Franko street.)*
*   **Біля мого дому є парк і магазин.** *(Near my house there is a park and a store.)*

This simple model description establishes a home base and identifies the immediate surroundings. The phrase **біля мого дому** (near my home) is a high-frequency chunk for describing a residential area. A neighborhood is defined by what is accessible from your front door.

Combining neighborhood features with transport needs reveals how a person interacts with their city. You must contrast what is accessible with what requires a journey.

*   **Школа далеко. Треба їхати автобусом.** *(The school is far. One needs to go by bus.)*
*   **Аптека близько. Можна піти пішки.** *(The pharmacy is near. One can go on foot.)*

The impersonal construction **треба їхати** (one needs to travel) expresses necessity without requiring a specific subject pronoun. Conversely, **можна піти** (one can go) indicates possibility and convenience. A typical neighborhood might be described by the amenities it contains: **У моєму районі є кафе, ресторан і бібліотека.** *(In my neighborhood there is a cafe, a restaurant, and a library.)* If a location is very close, the adverb **поруч** (nearby) is often used instead of a specific measurement.

Useful phrases for city life often measure distance in time rather than meters. The noun **хвилина** (minute, f) is frequently paired with walking.

*   **П'ять хвилин пішки.** *(Five minutes on foot.)*

Other essential location chunks include the paired concepts **далеко від** (far from) and **близько від** (near from), which both require the genitive case for the following noun. To describe the general area of a city, the phrases **у центрі міста** (in the city center) and **на околиці** (on the outskirts) are standard locative constructions.

*   **Мій офіс у центрі міста.** *(My office is in the city center.)*
*   **Я живу на околиці.** *(I live on the outskirts.)*

:::note
The word **пішки** (on foot) is an adverb, not a noun, so it never changes its form. You cannot say "на пішки" or "з пішки" — simply use the word on its own.
:::

Using these fixed phrases allows you to describe urban geography without needing complex grammatical explanations.

<!-- INJECT_ACTIVITY: fill-in-transport-route -->

## Підсумок — Summary

The urban communication toolkit relies on clear questions and direct commands. Asking for a location starts with the static question **Де...?** (Where...?), while asking for a route uses the dynamic structure **Як дістатися до...?** (How to get to...?). When providing directions, the adverbs **прямо** (straight), **направо** (to the right), and **наліво** (to the left) form the core instructions. Using the formal imperative verbs **ідіть** (go on foot) and **їдьте** (go by transport) ensures politeness when speaking to strangers on the street. Combining these elements allows you to ask for and give simple directions.

Grammatical navigation structures depend on a strict distinction between location and movement. The prepositions **в** and **на** act differently based on context. Pairing them with the locative case answers the static question **Де?** (Where?), while pairing them with the accusative case answers the directional question **Куди?** (Where to?). Transport methods further refine the description, distinguishing between walking (**пішки**), taking a non-declining transport (**на метро**), or riding a standard vehicle (**автобусом**). These patterns let you describe simple routes in Ukrainian.

<!-- INJECT_ACTIVITY: match-up-navigation-responses -->

Self-check: Describe your route from home to work or school. Construct a short narrative answering these specific questions to verify your understanding.

*   **Де ти живеш?** *(Where do you live?)*
    *   **Я живу на...** *(I live on...)*
*   **Як ти дістаєшся на роботу?** *(How do you get to work?)*
    *   **Я їду...** *(I go by...)*
*   **Це далеко чи близько?** *(Is it far or near?)*
    *   **Це...** *(It is...)*
*   **Скільки хвилин ти йдеш пішки?** *(How many minutes do you walk?)*
    *   **Я йду пішки...** *(I walk...)*
*   **Що є біля твого дому?** *(What is near your house?)*
    *   **Біля мого дому є...** *(Near my house there is...)*

Using these prompts builds a cohesive description of your daily interaction with the city. The ability to synthesize location, direction, and transport into a single explanation marks a significant step in conversational independence.
</generated_module_content>

**PIPELINE NOTE — Word count: 1581 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 98 words | Not found: 3 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Оксана — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Шевченка — NOT IN VESUM

All 98 other words are confirmed to exist in VESUM.

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
