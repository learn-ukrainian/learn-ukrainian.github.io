<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 34: Where From? (A1, A1.5 [Places])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-034
level: A1
sequence: 34
slug: where-from
version: '1.2'
title: Where From?
subtitle: Звідки ти? Я з України — origins and directions
focus: communication
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Ask and answer Звідки? (Where from?) using з/із + country/city
- Name Ukrainian cities and common countries
- Complete the location trio: Де? / Куди? / Звідки?
- Talk about origins, nationality, and travel history
dialogue_situations:
- setting: 'International student mixer at a Kyiv university — sharing origins: Я
    з Канади, Вона з Японії, Він з Німеччини. Also: З якого міста? З Торонто, з Токіо,
    з Берліна.'
  speakers:
  - Кілька студентів (group)
  motivation: 'Звідки? + з: Канада(f), Японія(f), Німеччина(f), Торонто(n)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting someone (extending M05, ULP Ep4): — Звідки ти? — Я з України,
    з Києва. А ти? — Я з Канади, із Торонто. — Давно тут? — Ні, я приїхав місяць тому.
    Звідки? pattern with countries and cities.'
  - 'Dialogue 2 — Coming from somewhere: — Звідки ти йдеш? — Я йду з роботи. — А Олена?
    — Вона йде зі школи. — Куди вона йде? — Додому. Direction FROM (з + genitive chunk)
    vs TO (в/на + accusative).'
- section: Звідки? (Where From?)
  words: 300
  points:
  - 'Three direction questions complete: Де ти? — В Україні. (locative — where you
    ARE) Куди ти їдеш? — В Україну. (accusative — where you''re GOING) Звідки ти?
    — З України. (genitive — where you''re FROM) At A1: learn з + country/city as
    chunks. Genitive grammar = A2.'
  - 'Pattern: з/із/зі + genitive (memorized forms): з України, з Києва, зі Львова,
    з Одеси, з Харкова. з Канади, зі США (зі Штатів), з Англії, з Німеччини, з Польщі.
    з роботи, зі школи, з магазину, з банку. Note: euphony rules from M28 apply: з/із/зі.'
- section: Країни і міста (Countries and Cities)
  words: 300
  points:
  - 'Ukrainian cities: Київ (Kyiv), Львів (Lviv), Одеса (Odesa), Харків (Kharkiv),
    Дніпро (Dnipro), Запоріжжя (Zaporizhzhia). Countries (common for learners): Україна,
    Канада, США, Англія, Німеччина, Польща, Франція, Італія, Японія.'
  - 'Nationality and language links: Я з України → Я українець/українка → Я говорю
    українською. Review from M05: Мене звати..., Я з..., Я говорю... New: Я живу в
    Києві, але я зі Львова. (current location vs origin)'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three location questions: Де? → в/на + locative (В Україні) Куди? → в/на + accusative
    (В Україну) Звідки? → з/із/зі + genitive chunk (З України) Self-check: Where are
    you from? Where do you live now? Where are you going after this lesson?'
vocabulary_hints:
  required:
  - звідки (where from)
  - з/із/зі (from — + genitive chunk)
  - Україна (Ukraine)
  - Київ (Kyiv)
  - Львів (Lviv)
  - Канада (Canada)
  recommended:
  - Одеса (Odesa)
  - Харків (Kharkiv)
  - США (USA)
  - Англія (England)
  - Німеччина (Germany)
  - Польща (Poland)
  - додому (home — direction)
activity_hints:
- type: fill-in
  focus: Answer Звідки? using з/із/зі + memorized genitive chunks
  items: 8
  blanks:
  - Звідки ти? — Я {з України}.
  - Вона {з Канади}.
  - Ми {з Києва}, а ви?
  - Джон {зі США}.
  - Мій друг {з Німеччини}.
  - Я {зі Львова}.
  - Вони {з Англії}.
  - Олена {з Одеси}.
- type: group-sort
  focus: Categorize phrases into Де? (Locative), Куди? (Accusative), Звідки? (Genitive)
  items: 9
  groups:
  - name: Де? (Where?)
    items:
    - в Україні
    - в Києві
    - на роботі
  - name: Куди? (Where to?)
    items:
    - в Україну
    - в Київ
    - на роботу
  - name: Звідки? (Where from?)
    items:
    - з України
    - з Києва
    - з роботи
- type: quiz
  focus: Choose correct preposition (в/на/з) for location/direction
  items: 8
  questions:
  - Я йду... роботи. (з / на / в)
  - Вона йде... школу. (в / на / зі)
  - Ми зараз... Україні. (в / з / на)
  - Я їду... Канаду. (в / з / на)
  - Він... Німеччини. (з / в / на)
  - Вони... Львові. (у / зі / на)
  - Я йду... магазину. (з / в / на)
  - Олена... школи. (зі / в / на)
- type: fill-in
  focus: Contrast current location (в/на) and origin (з/із)
  items: 6
  blanks:
  - Я живу {в Києві}, але я {зі Львова}.
  - Вона живе {в Канаді}, але вона {з України}.
  - Ми зараз {в Англії}, але ми {з Польщі}.
  - Він живе {в Одесі}, але він {з Харкова}.
  - Я {з Німеччини}, але зараз я {в Україні}.
  - Ти {зі США}, але живеш {у Києві}.
connects_to:
- a1-035 (Checkpoint — Places)
prerequisites:
- a1-033 (Around the City)
grammar:
- Звідки? + з/із/зі + genitive (memorized chunks)
- 'Location trio: Де? (M.в.) / Куди? (Зн.в.) / Звідки? (Р.в. chunk)'
- Country/city names in three case forms
register: розмовний
references:
- title: ULP Season 1, Episode 4
  url: https://www.ukrainianlessons.com/episode4/
  notes: Where are you from? — nationalities and countries.

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги — Dialogues

An international student mixer at a university in Kyiv is the perfect place to hear a symphony of languages and accents. When people from different backgrounds gather in one room, the most natural icebreaker is finding out where everyone comes from. In Ukrainian, asking about someone's origin is a direct, essential communicative skill. You will hear the question **Звідки ти?** (Where are you from?) echoing across the room as students connect, share their stories, and learn about each other's homes. The ability to state your origin confidently is your passport to deeper conversations. 

> **Джон:** Звідки ти? *(Where are you from?)*
> **Максим:** Я з України, з Києва. А ти? *(I am from Ukraine, from Kyiv. And you?)*
> **Джон:** Я з Канади, із Торонто. *(I am from Canada, from Toronto.)*
> **Максим:** Давно тут? *(Have you been here long?)*
> **Джон:** Ні, я приїхав місяць тому. *(No, I arrived a month ago.)*

The core interaction for stating your origin revolves around the question **Звідки ти?** (Where are you from?). Notice how the response is constructed: **Я з...** (I am from...). In Ukrainian, the present tense verb for "to be" is almost always omitted in these standard phrases. You do not need to say "I am," you simply state your pronoun, the preposition, and the place. The structure **Я з України** (I am from Ukraine) is a complete, grammatically correct sentence that you can use immediately. When talking about a specific city, you simply add it to the phrase, such as **Я з України, з Києва** (I am from Ukraine, from Kyiv).

> **Анна:** Звідки ти йдеш? *(Where are you coming from?)*
> **Марко:** Я йду з роботи. *(I am coming from work.)*
> **Анна:** А Олена? *(And Olena?)*
> **Марко:** Вона йде зі школи. *(She is coming from school.)*
> **Анна:** Куди вона йде? *(Where is she going?)*
> **Марко:** Додому. *(Home.)*

This second conversation highlights a shorter exchange about physical movement. We are contrasting the origin point — coming from work or from school — with the destination. You use the exact same preposition to describe walking away from a building as you do when stating the country you were born in.

## Звідки? — Where From?

Ukrainian categorizes spatial relations and movement into three distinct, logical questions: **Де?** (Where are you?), **Куди?** (Where are you going?), and **Звідки?** (Where are you from?). Think of this as the "Location Trio." If we take a country like **Україна** (Ukraine), it changes its shape depending on which of the three questions you are answering. At this A1 level, you will learn to use these combinations as memorized chunks, while the full grammatical rules of the genitive case will be covered in A2.

*   **Де ти? — В Україні.** (Where are you? — In Ukraine.) This uses the locative case to show exactly where you ARE.
*   **Куди ти їдеш? — В Україну.** (Where are you traveling to? — To Ukraine.) This uses the accusative case to show where you are GOING.
*   **Звідки ти? — З України.** (Where are you from? — From Ukraine.) This is a genitive chunk, showing the point where you are FROM.

To express this origin, you need a preposition. Just as you learned in Module 28, Ukrainian applies euphony rules to make speech flow smoothly. The basic preposition for "from" is **з**, and you will use it before most vowels and consonants, like **з Канади** (from Canada). If the next word starts with a sibilant sound (like s, sh, or z), you switch to **із** for easier pronunciation, as in **із США** (from the USA). For specific difficult consonant clusters, especially those starting with z, s, or sh, you use **зі**, which is why we say **зі Львова** (from Lviv).

:::note
You do not need to memorize complex euphony rules for **з**, **із**, and **зі** right now. Focus on learning the correct combinations as single blocks of vocabulary, like **зі США** (from the USA).
:::

When you use this preposition, the noun that follows it must change its ending. Feminine nouns ending in **-а** change to **-и**: **Україна** becomes **з України**, **Канада** becomes **з Канади**, and **Одеса** becomes **з Одеси**. Feminine nouns ending in **-я** change to **-ї**: **Англія** becomes **з Англії**. Masculine place names ending in a consonant usually add an **-а**: **Київ** becomes **з Києва**, and **Харків** becomes **з Харкова**. These predictable patterns allow you to comfortably form the origin phrase for most common locations without needing to memorize a complex table.

:::caution
English relies heavily on the verb "to be" to express location, but Ukrainian relies on prepositions and case endings. Never say **Я в України** to mean "I am from Ukraine" — always use **з** for your origin.
:::

<!-- INJECT_ACTIVITY: answer-zvidky -->

The question **Звідки?** is used for much more than just international geography. You will use it constantly in your daily life to explain your routine movements. The same exact pattern applies to everyday locations in your city. When you finish your shift, you are walking **з роботи** (from work). After buying groceries, you are coming **з магазину** (from the store). When you finish your financial tasks, you step out **з банку** (from the bank). And when classes end, a student walks **зі школи** (from school).

<!-- INJECT_ACTIVITY: location-trio-sort -->

## Країни і міста — Countries and Cities

Major Ukrainian cities provide excellent practice for forming these origin phrases. The capital city is **Київ** (Kyiv), so you would say **з Києва** (from Kyiv). The cultural hub of the west is **Львів** (Lviv), which becomes **зі Львова** (from Lviv). The southern port is **Одеса** (Odesa), forming **з Одеси** (from Odesa). In the east, we have **Харків** (Kharkiv), which changes to **з Харкова** (from Kharkiv). The central city of **Дніпро** (Dnipro) becomes **з Дніпра** (from Dnipro), and the southeastern industrial center **Запоріжжя** (Zaporizhzhia) becomes **із Запоріжжя** (from Zaporizhzhia).

:::tip
The name **Україна** historically means "land," "region," or "our country." It is not a "borderland," as Russian imperialist myths have tried to claim. And its capital, **Київ**, has always been the historical heart of this land.
:::

When interacting in international environments, you will also need to recognize common country names. If someone asks where you are from, you might need to say you are from Canada: **Канада** (Canada) becomes **з Канади** (from Canada). The United States is usually abbreviated, giving us **зі США** (from the USA) or occasionally **зі Штатів** (from the States). Other frequent European nations include **Англія** (England), which forms **з Англії** (from England), and **Німеччина** (Germany), which becomes **з Німеччини** (from Germany). You might also meet people from neighboring **Польща** (Poland), saying **з Польщі** (from Poland), or from further away like **Франція** (France), making **із Франції** (from France), **Італія** (Italy), making **з Італії** (from Italy), and **Японія** (Japan), which changes to **з Японії** (from Japan).

Your origin is deeply connected to your identity and the language you speak. We can review concepts from Module 05 and link them to the new origin pattern. Notice how these phrases flow together in a logical sequence.

*   **Мене звати Петро.** (My name is Petro.)
*   **Я з України.** (I am from Ukraine.)
*   **Я українець.** (I am a Ukrainian man.)
*   **Я говорю українською.** (I speak Ukrainian.)

We can contrast this with someone from a different background:

*   **Мене звати Джон.** (My name is John.)
*   **Я з Англії.** (I am from England.)
*   **Я англієць.** (I am an Englishman.)
*   **Я говорю англійською.** (I speak English.)

<!-- INJECT_ACTIVITY: preposition-quiz -->

Often, where you are from is not where you are right now. You can combine your origin and your current location in a single sentence to tell a richer story about yourself. To do this, use the conjunction **але** (but) and the adverb **зараз** (now). This is an excellent way to practice both the "from" pattern and the "in" pattern together. 

*   **Я живу в Києві, але я зі Львова.** (I live in Kyiv, but I am from Lviv.)
*   **Вона з Канади, але зараз вона живе в Україні.** (She is from Canada, but now she lives in Ukraine.)

<!-- INJECT_ACTIVITY: location-contrast -->

## Підсумок — Summary

You now have a complete, functional system for describing spatial relations and movement in Ukrainian. A review of the three core questions will solidify this system. 

When you want to express a static location, you ask **Де?** (Where?). The answer usually requires the prepositions **в** or **на** and the locative case, such as **в Україні** (in Ukraine). 

When you want to talk about a destination, you ask **Куди?** (Where to?). The answer also uses **в** or **на** but with the accusative case, such as **в Україну** (to Ukraine). 

Finally, when you are talking about an origin, you ask **Звідки?** (Where from?). The answer requires the prepositions **з**, **із**, or **зі** plus a genitive chunk, like **з України** (from Ukraine).

Here is a summary of the most frequent city and country changes you learned in this module:
*   **Україна** → **з України**
*   **Канада** → **з Канади**
*   **Німеччина** → **з Німеччини**
*   **Київ** → **з Києва**
*   **Львів** → **зі Львова**
*   **Харків** → **з Харкова**

To ensure you have mastered these concepts, try to answer the following self-check questions out loud. Use your own real-world information where possible.

*   **Звідки ти?** (Where are you from?) → **Я з...**
*   **Звідки твій друг?** (Where is your male friend from?) → **Він з...**
*   **Звідки твоя подруга?** (Where is your female friend from?) → **Вона з...**
*   **Ти зараз у Києві чи у Львові?** (Are you in Kyiv or in Lviv right now?) → **Я зараз у...**
*   **Звідки ти йдеш зараз?** (Where are you coming from right now?) → **Я йду з...**
*   **Де ти живеш?** (Where do you live now?) → **Я живу в...**
*   **Куди ти йдеш після уроку?** (Where are you going after this lesson?) → **Я йду в/на...**

By mastering the question **Звідки?**, you have unlocked the final piece of the basic location puzzle. You can now confidently describe where you are, where you are heading, and where you came from. In the next module, Checkpoint — Places, you will review and consolidate all of this spatial vocabulary before moving on to new topics.
</generated_module_content>

**PIPELINE NOTE — Word count: 1597 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 51 words | Not found: 29 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Італія — NOT IN VESUM
  ✗ Італії — NOT IN VESUM
  ✗ Англія — NOT IN VESUM
  ✗ Англії — NOT IN VESUM
  ✗ Анна — NOT IN VESUM
  ✗ Джон — NOT IN VESUM
  ✗ Дніпра — NOT IN VESUM
  ✗ Дніпро — NOT IN VESUM
  ✗ Запоріжжя — NOT IN VESUM
  ✗ Канада — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Німеччина — NOT IN VESUM
  ✗ Німеччини — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Одеси — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Петро — NOT IN VESUM
  ✗ Польща — NOT IN VESUM
  ✗ Польщі — NOT IN VESUM
  ✗ Торонто — NOT IN VESUM
  ✗ Франція — NOT IN VESUM
  ✗ Харкова — NOT IN VESUM
  ✗ Харків — NOT IN VESUM
  ✗ Японія — NOT IN VESUM
  ✗ Японії — NOT IN VESUM

All 51 other words are confirmed to exist in VESUM.

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
