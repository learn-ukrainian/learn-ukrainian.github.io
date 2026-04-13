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

This checkpoint reviews the key Places patterns from M28-M34. Keep three questions active as you read: **Де?** for location, **Куди?** for direction, and **Звідки?** for origin.

You will combine euphony, city vocabulary, transport, directions, and the locative / accusative / genitive chunks you already know.

Review this checklist to see what you already know. Can you apply the rules of euphony for a smooth pronunciation?
* **Вона живе у Львові.** (She lives in Lviv.)
* **Він живе в Києві.** (He lives in Kyiv.)

Can you say where things are currently located?
* **Я зараз у парку.** (I am in the park now.)
* **Ми в центрі.** (We are in the center.)

Can you say where you are going right now?
* **Я йду в магазин.** (I am going to the store.)
* **Вона йде на роботу.** (She is going to work.)

Can you accurately state your origin?
* **Я родом з України.** (I am originally from Ukraine.)
* **Він іде зі школи.** (He is walking from school.)

Can you use transport vocabulary and give basic directions?
* **Ми їдемо автобусом.** (We are going by bus.)
* **Ідіть прямо і направо.** (Go straight and to the right.)

To prove you are ready, read this short introduction out loud:
> **Привіт! Я зараз в Одесі, на Дерибасівській вулиці.**
> *(Hi! I am in Odesa now, on Deribasivska Street.)*
>
> **Я на відеодзвінку з другом.**
> *(I am on a video call with a friend.)*
>
> **Потьомкінські сходи недалеко, а порт унизу.**
> *(The Potemkin Stairs are nearby, and the port is below.)*
>
> **Потім я йду на пляж.**
> *(Then I am going to the beach.)*

<!-- INJECT_ACTIVITY: quiz-question-choice -->

## Читання (Reading Practice)

Real navigation happens in continuous conversation, not in isolated textbook sentences. Imagine a tourist navigating the bustling, vibrant streets of Kyiv. They need to ask locals for accurate directions, understand the public transit system, locate a specific cultural site, and clearly explain their travel plans. This requires combining all your spatial skills.

Read the following narrative about a tourist in the city. It combines all the spatial patterns you have learned so far.

> **Привіт! Я турист з Канади.**
> *(Hi! I am a tourist from Canada.)*
>
> **Я зараз у центрі Києва.**
> *(I am currently in the center of Kyiv.)*
>
> **Я дуже хочу їхати в музей.**
> *(I really want to go to the museum.)*
>
> **Але музей стоїть далеко.**
> *(But the museum stands far away.)*
>
> **Тому я йду на метро.**
> *(Therefore I am walking to the metro.)*
>
> **Я їду на станцію Хрещатик.**
> *(I travel to the Khreshchatyk station.)*
>
> **Там я йду прямо і направо.**
> *(There I go straight and to the right.)*
>
> **І ось музей на великій площі!**
> *(And here is the museum on the large square!)*

This reading brings the checkpoint patterns together in one route: **з Канади** shows origin, **у центрі Києва** shows location, **в музей** shows direction, and **на метро / прямо / направо** describe the way.

## Граматика (Grammar Summary)

The core spatial patterns form the absolute foundation of your navigation skills. The question **Де?** (Where?) requires the prepositions **в** or **на** followed by the Locative case. You use this exclusively for static locations, telling people exactly where an object or person currently rests.
* **Студент зараз у школі.** (The student is in school now.)
* **Вона весь день на роботі.** (She is at work all day.)
* **Ми сидимо в парку.** (We are sitting in the park.)
* **Зошит лежить на столі.** (The notebook is lying on the table.)

The question **Куди?** (To where?) requires the prepositions **в** or **на** followed by the Accusative case. You use this strictly for movement toward a destination, indicating the endpoint of a physical journey.
* **Студент іде у школу.** (The student is going to school.)
* **Вона швидко їде на роботу.** (She is traveling quickly to work.)
* **Ми йдемо в парк.** (We are walking to the park.)
* **Він іде в театр.** (He is going to the theater.)

The question **Звідки?** (From where?) requires the prepositions **з**, **із**, or **зі** followed by the Genitive case. You use this to express the starting point of a movement or a person's geographic origin.
* **Студент іде зі школи.** (The student is walking from school.)
* **Вона йде з роботи.** (She is walking from work.)
* **Турист іде з готелю.** (The tourist is walking from the hotel.)
* **Я йду з парку.** (I am walking from the park.)

Ukrainian speech requires a smooth flow of sounds. The euphony rules ensure that words connect naturally without awkward consonant clusters. You alternate between vowels and consonants using specific sets of prepositions and conjunctions.
* **Брат і сестра йдуть.** (Brother and sister are walking.)
* **Мама й тато вдома.** (Mom and dad are at home.)
* **Вона зараз у Львові.** (She is in Lviv now.)
* **Він живе в Одесі.** (He lives in Odesa.)

When discussing your daily commute and transport, you use specific grammatical forms. You use the Instrumental case for the vehicle itself, or you use the preposition **на** with the Locative case for public transit systems.
* **Ми їдемо великим автобусом.** (We are going by a large bus.)
* **Вони їдуть на метро.** (They are going by metro.)

You also use fixed, unchanging adverbs for simple directions on the street.
* **Ідіть прямо по вулиці.** (Go straight along the street.)
* **Аптека стоїть направо.** (The pharmacy stands to the right.)
* **Гарний парк наліво.** (The beautiful park is to the left.)

All these individual elements combine to form complete, natural, and highly functional thoughts.
* **Я їду з роботи.** (I am traveling from work.)
* **Я їду автобусом у центр.** (I am traveling by bus to the center.)

<!-- INJECT_ACTIVITY: group-sort-case-function -->
<!-- INJECT_ACTIVITY: quiz-euphony-rules -->

## Діалог (Connected Dialogue)

Imagine you are visiting Kyiv and you urgently need some assistance. You stop a local resident on the street to ask for clear directions to a famous museum. After you find out about the museum, you also need to figure out how to reach the main train station for your onward journey to the city of Lviv.

> **Турист:** Вибачте, я з Канади. Де тут музей?
> *(Tourist: Excuse me, I am from Canada. Where is the museum here?)*
>
> **Місцевий:** Музей у центрі. Ідіть на метро до станції Хрещатик.
> *(Local: The museum is in the center. Go by metro to the Khreshchatyk station.)*
>
> **Турист:** А як дістатися від метро?
> *(Tourist: And how do I get there from the metro?)*
>
> **Місцевий:** Вийдіть і йдіть направо. Музей на площі.
> *(Local: Exit and go right. The museum is on the square.)*
>
> **Турист:** Дякую! А потім я хочу їхати у Львів. Де вокзал?
> *(Tourist: Thank you! And then I want to travel to Lviv. Where is the train station?)*
>
> **Місцевий:** Вокзал далеко, їдьте на метро до станції Вокзальна.
> *(Local: The train station is far, go by metro to Vokzalna station.)*

The first half of the dialogue handles the immediate navigation problem. The tourist successfully states their geographical origin using the phrase **з Канади** (from Canada). They then ask a simple, direct question about their target location using **Де тут музей?** (Where is the museum here?). The local resident responds with a static location, **у центрі** (in the center), and provides a clear route using transport vocabulary. 

The tourist then asks how to navigate on foot from the station using the phrase **від метро** (from the metro). They use the verb **дістатися** (to reach / to get to). This is a highly practical verb when you need to know how to navigate between two specific points.

The second half of the dialogue shifts the focus to a future destination. The tourist uses the Accusative case to explain their next city target, saying **у Львів** (to Lviv). They immediately ask for the location of the main train station. The local resident gives them practical advice, explaining that the station is far away. They use the command form **їдьте** (drive/travel) and combine it with the transport phrase to give a clear, actionable route across the city.

:::note
For transport, **на метро** is a normal and widely taught beginner phrase. You may also hear bare **метро** in context because the noun is indeclinable, but **в метро** usually means “in the metro,” not “by metro.”
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue-forms -->

## Підсумок — Summary

You can now combine the main Places patterns in one situation: say where you are, where you are going, where you are from, how you are traveling, and how to follow simple directions.

Before moving on, check that you can answer **Де?** with the locative, **Куди?** with the accusative, and **Звідки?** with genitive chunks. In A1.6 you will keep using the accusative, but this time for direct objects in food and shopping situations.
</generated_module_content>

**PIPELINE NOTE — Word count: 1468 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 100 words | Not found: 7 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Дерибасівській — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Одесі — NOT IN VESUM
  ✗ Хрещатик — NOT IN VESUM

All 100 other words are confirmed to exist in VESUM.

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
