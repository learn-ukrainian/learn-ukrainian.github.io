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
## Діалоги (Dialogues)

Imagine you are at an international student mixer at a university in **Київ** (Kyiv). People are chatting, sharing their origins, and talking about where they live now. This is the perfect setting to practice asking where someone is from. 

In this situation, the most important phrase you need is **звідки ти** (where from are you). Let us listen to a conversation between two students meeting for the first time. Pay attention to the prepositions they use when naming their home countries and cities.

> **Олег:** Привіт! Я Олег. А тебе як звати? *(Hi! I am Oleh. And what is your name?)*
> **Марк:** Мене звати Марк. *(My name is Mark.)*
> **Олег:** Дуже приємно, Марк. **Звідки ти?** *(Very nice to meet you, Mark. Where are you from?)*
> **Марк:** Я **з Канади** (from Canada), **із Торонто**. А ти? *(I am from Canada, from Toronto. And you?)*
> **Олег:** Я **з України** (from Ukraine), **з Києва**. Давно тут? *(I am from Ukraine, from Kyiv. Have you been here long?)*
> **Марк:** Ні, я приїхав місяць тому. *(No, I arrived a month ago.)*

Notice how the question is formed with one word: **звідки**. The answer begins with the preposition **з** (from) or **із**, followed by the place name. Many country and city names change their endings to indicate origin, while some names, such as **Торонто**, stay the same.

We can also ask about movement from everyday places, not just geographic origins. If you see a friend walking on the street, you might want to know where they are coming from right now. 

In this next dialogue, two friends meet outside. Listen to how they talk about their current movement and destinations.

> **Ганна:** Привіт, Тарасе! **Звідки** ти йдеш? *(Hi, Taras! Where are you coming from?)*
> **Тарас:** Привіт! Я йду **з роботи** (from work). А ти? *(Hi! I am walking from work. And you?)*
> **Ганна:** Я йду **з магазину**. А де Олена? *(I am walking from the store. And where is Olena?)*
> **Тарас:** Вона йде **зі школи**. *(She is walking from school.)*
> **Ганна:** Куди вона йде? *(Where is she going?)*
> **Тарас:** Вона йде **додому** (home). *(She is going home.)*

Here, the pattern is exactly the same: **звідки** asks the question, and the preposition **з** or **зі** shows the starting point of the movement.

## Звідки? (Where From?)

You now have the complete trio of spatial questions in Ukrainian. These three questions form the foundation of how we talk about location and movement. We ask **Де ти?** (Where are you?) when talking about a static location, like **в Україні** (in Ukraine). We ask **Куди ти їдеш?** (Where are you going?) for a destination, like **в Україну** (to Ukraine). Finally, we ask **Звідки ти?** (Where are you from?) to find out the origin, like **з України** (from Ukraine). The same trio works with cities too: **в Києві** (in Kyiv), **в Київ** (to Kyiv), **з Києва** (from Kyiv).

The question **Звідки ти?** translates to "Where are you from?", but it works differently than in English. First, it is a complete sentence all on its own. In Ukrainian, we do not need a verb like "to be" for this question. Second, the interrogative word **звідки** is a single, solid unit that cannot be split apart. You cannot put a preposition at the end of the sentence. The standard answer is simply **Я з** followed by your place of origin.

To answer this question correctly, you use the pattern **з / із / зі** (from) followed by a specific form of the noun, which belongs to the genitive case. At this early stage, the best strategy is to memorize these common origins as fixed chunks. For cities, you will say **з Києва** (from Kyiv), **зі Львова** (from Lviv), **з Одеси** (from Odesa), or **з Харкова** (from Kharkiv). For everyday places in town, the pattern is the same: **з роботи** (from work), **зі школи** (from school), **з магазину** (from the store), or **з банку** (from the bank).

You have likely noticed that the preposition changes its shape. Ukrainian uses euphony rules to make speech flow smoothly and avoid awkward clusters of sounds. The basic form **з** is used before most vowels and simple consonants, as in **з Канади** or **з України**. The variant **із** helps with pronunciation before certain letters, like **із Торонто**. Finally, we use **зі** before difficult consonant clusters or specific tricky sounds, such as **зі Львова**, **зі школи**, and **зі США**.

<!-- INJECT_ACTIVITY: fill-in-where-from -->
<!-- INJECT_ACTIVITY: group-sort-location-trio -->

## Країни і міста (Countries and Cities)

When discussing origins, it is helpful to know the names of major Ukrainian cities and how they change after the preposition. The capital is **Київ**, and someone from there says **Я з Києва**. A resident of **Львів** will say **Я зі Львова**. For the southern coastal city of **Одеса**, the origin form is **з Одеси**. A person from the eastern city of **Харків** says **Я з Харкова**. Other major centers include **Дніпро**, which becomes **з Дніпра**, and **Запоріжжя**, which takes the form **із Запоріжжя**.

You will also want to know how to state your home country. We have already seen **Україна**, which becomes **з України**, and **Канада**, which changes to **з Канади**. Other very common countries include **США** (USA), which uses the special form **зі США**. For European nations, **Англія** (England) becomes **з Англії**, **Німеччина** (Germany) is **з Німеччини**, and **Польща** (Poland) becomes **з Польщі**. Further away, **Франція** (France) changes to **з Франції**, **Італія** (Italy) is **з Італії**, and **Японія** (Japan) becomes **з Японії**.

Your geographic origin is often the first step in describing your identity. This connects directly to the nationalities and languages you learned earlier. There is a logical, three-step progression when introducing yourself to a new group of people. First, you state your origin: **Я з України** (I am from Ukraine). Next, you state your nationality: **Я українець** or **Я українка** (I am Ukrainian). Finally, you state your primary language: **Я говорю українською** (I speak Ukrainian). This full sequence gives a complete picture of who you are.

People frequently move, so you will often need to contrast your current location with your origin. To do this naturally, you can join two facts together using the conjunction **але** (but). You state your current location using **в** or **на** plus the locative ending, and then state your origin using **з** plus the genitive form. For example, a student might explain: **Я живу в Києві, але я зі Львова** (I live in Kyiv, but I am from Lviv).

<!-- INJECT_ACTIVITY: fill-in-contrast-location-origin -->

## Підсумок — Summary

This module has given you the final piece of the spatial puzzle in Ukrainian. You now have a complete toolkit for talking about where things happen, where things are going, and where things come from. Remember the three fundamental questions and their grammatical pairs. When asking **Де?** (Where at?), use the prepositions **в** or **на** with the static locative case, as in **В Україні**. When asking **Куди?** (Where to?), use **в** or **на** with the accusative case to show direction, as in **В Україну**. Finally, when asking **Звідки?** (Where from?), use the prepositions **з**, **із**, or **зі** with a memorized genitive chunk, as in **З України**.

To describe your origin, you will always rely on the prepositions **з**, **із**, or **зі**, depending on the sounds that follow them. This small change ensures that your speech remains smooth and natural. Always remember that Ukrainian spatial questions like **звідки** are single, independent words. Unlike English, where you might ask a question that ends with a dangling preposition, Ukrainian keeps the concept of origin tightly bound into one compact interrogative word.

Before you move forward, take a moment to answer these three practical self-check questions. First, consider the question: **Звідки ти?** (Where are you from?). Think of the name of your home country and your home city, and practice saying them out loud using the correct form of **з**, **із**, or **зі**. Second, ask yourself: **Де ти зараз живеш?** (Where do you live now?). Picture your current city or town, and formulate a sentence using **в** or **на** to describe this static location. Finally, think about your immediate plans and ask: **Куди ти йдеш після цього уроку?** (Where are you going after this lesson?). Decide on your destination and express that movement using **в** or **на**, or use the single directional word **додому** if you are heading back to your house.

<!-- INJECT_ACTIVITY: quiz-preposition-choice -->
</generated_module_content>

**PIPELINE NOTE — Word count: 1406 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 47 words | Not found: 30 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Італія — NOT IN VESUM
  ✗ Італії — NOT IN VESUM
  ✗ Англія — NOT IN VESUM
  ✗ Англії — NOT IN VESUM
  ✗ Ганна — NOT IN VESUM
  ✗ Дніпра — NOT IN VESUM
  ✗ Дніпро — NOT IN VESUM
  ✗ Запоріжжя — NOT IN VESUM
  ✗ Канада — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Львова — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Марк — NOT IN VESUM
  ✗ Німеччина — NOT IN VESUM
  ✗ Німеччини — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Одеси — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Польща — NOT IN VESUM
  ✗ Польщі — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ Торонто — NOT IN VESUM
  ✗ Франція — NOT IN VESUM
  ✗ Харкова — NOT IN VESUM
  ✗ Харків — NOT IN VESUM
  ✗ Японія — NOT IN VESUM
  ✗ Японії — NOT IN VESUM

All 47 other words are confirmed to exist in VESUM.

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
