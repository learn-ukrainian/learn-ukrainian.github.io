<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Reading Ukrainian (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: '1.2'
title: Reading Ukrainian
subtitle: From letters to words to sentences
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Read any Ukrainian word by sounding out letters and blending syllables
- Apply the syllable rule — count vowels to count syllables
- Read multisyllable words confidently (not letter by letter)
- Understand how the 10 vowel letters map to 6 vowel sounds
content_outline:
- section: Склади (Syllables)
  words: 250
  points:
  - 'Большакова Grade 1 p.25: ''У слові стільки складів, скільки голосних звуків.''
    Count the vowels, count the syllables. This rule never breaks. ма-ма (2 vowels
    = 2 syllables), мо-ло-ко (3 vowels = 3 syllables), банк (1 vowel = 1 syllable).'
  - 'How Ukrainian children learn to read — складові ланцюжки (syllable chains):
    Start with a consonant + vowel pair: М → ма, мо, му, ми. Then reverse: ам, ом, ум.
    Then build words: ма-ма, мо-ло-ко. This is bottom-up: sound → syllable → word.
    (Захарійчук Grade 1, p.46; Большакова Grade 1, p.25)'
  - 'Звуковий аналіз слова (Большакова p.29): 1) Визначаю голосні звуки 2) Ділю
    слово на склади 3) Ставлю наголос 4) Позначаю приголосні звуки.
    Chin-test for syllable counting (Кравцова Grade 2, p.13): put your palm under
    your chin, say the word — each chin touch = one syllable.'
  - 'Ukrainian sound notation system (Захарійчук p.15): [●] голосний, [—] твердий
    приголосний, [=] м''який приголосний. Every Ukrainian child learns this in Grade 1.'
- section: Голосні літери (Vowel Letters)
  words: 300
  points:
  - 'Review from M01: 6 sounds, 10 letters. Now learn all 10 individually. Simple
    vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і]. Each makes
    ONE consistent sound — no surprises.'
  - 'Iotated vowels (two sounds or softening): Я = [йа] at word start (яблуко) or
    after vowel (моя). After consonant: softens it + [а] (пісня — Н is softened).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е]. Ї = ALWAYS [йі] — never
    softens. Only at word start, after vowel, or after apostrophe. Unique to Ukrainian.'
  - 'Critical minimal pairs: И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім
    (house). Listen to Anna''s pronunciation videos for each — the difference is subtle
    but changes meaning.'
- section: Читання слів (Reading Words)
  words: 500
  points:
  - 'Apply складові ланцюжки to real words. Don''t read letter-by-letter — read
    syllable-by-syllable. Use звуковий аналіз: find vowels first, split into склади,
    then blend. Example: книга — find vowels И, А → кни-га → read.'
  - 'Progressive difficulty using Ukrainian classification (односкладові → багатоскладові):
    односкладові (1 syllable): дім, сон, ліс, дуб, хліб.
    двоскладові (2 syllables): ма-ма, та-то, во-да, ру-ка, ха-та, ка-ша.
    трискладові (3 syllables): ап-те-ка, мо-ло-ко, лю-ди-на, ву-ли-ця.
    багатоскладові (4+ syllables): у-ні-вер-си-тет, біб-лі-о-те-ка, фо-то-гра-фі-я.'
  - 'Ukrainian city names as reading practice: Ки-їв, Льві-в, О-де-са, Хар-ків,
    Дні-про, Пол-та-ва. Note the different syllable counts and structures.'
  - 'Special letter combinations to watch for (preview for M03): Щ is always [шч] — що, ще.
    Ь has no sound — it softens: день, сіль, кінь. Apostrophe separates: сім''я,
    м''ясо, п''ять. These will be explored fully in M03.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel
    sounds? Name the 4 iotated vowel letters. What does Ь do? What does the apostrophe
    do? Read this word: бібліотека — how many syllables?'
vocabulary_hints:
  required:
  - яблуко (apple) — Я at word start = [йа]
  - молоко (milk) — 3 syllables, all simple vowels
  - людина (person) — Л + Ю combination
  - вулиця (street) — Ц sound practice
  - столиця (capital) — Київ — столиця України
  - каша (porridge) — Ш sound practice
  - пісня (song) — softening by Я after consonant
  recommended:
  - університет (university) — long word practice
  - бібліотека (library) — 5 syllables
  - фотографія (photography) — long word with Ф
  - шоколад (chocolate) — Ш + О + К combination
activity_hints:
- type: divide-words
  focus: 'Поділи слова на склади: мо-ло-ко, ап-те-ка, у-ні-вер-си-тет'
  items: 8
- type: count-syllables
  focus: 'Порахуй склади — скільки голосних, стільки й складів'
  items: 8
- type: match-up
  focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 6
- type: quiz
  focus: Read the word and choose its meaning
  items: 6
- type: odd-one-out
  focus: 'Яке слово зайве? — by syllable count (односкладове серед двоскладових)'
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- 'Правило складоподілу: у слові стільки складів, скільки голосних звуків'
- 'Звуковий аналіз слова: визначити голосні → поділити на склади → наголос → приголосні'
- 'Складові ланцюжки: приголосний + голосний = склад (ма, мо, му)'
- 'Ukrainian sound notation: [●] голосний, [—] твердий приголосний, [=] м''який приголосний'
- 10 vowel letters → 6 vowel sounds mapping
- Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])
- 'Word classification: односкладові, двоскладові, трискладові, багатоскладові'
- Ь, apostrophe (preview — detailed in M03)
register: розмовний
references:
- title: Большакова Grade 1 буквар, p.25
  notes: 'Syllable rule: ''У слові стільки складів, скільки голосних звуків.'''
- title: Большакова Grade 1 буквар, p.29
  notes: Звуковий аналіз слова method — how to analyze word sounds.
- title: Захарійчук Grade 1 (NUS 2025), p.13-15
  notes: 'Sound notation: [•] for vowels, [–] for consonants, [=] for soft.'

</plan_content>

## Generated Content

<generated_module_content>
## Склади

You have seen the letters, but how do they form a word? The answer lies in the syllable. There is a golden rule taught to every Ukrainian student. The textbook *Большакова Grade 1*, page 25, states: "**У слові стільки складів, скільки голосних звуків**" (Count the vowels, count the syllables). This rule never breaks. If you count the vowels, you know the syllable count. For example, **мама** (mother) has two vowels, making two syllables: **ма-ма**. The word **молоко** (milk) has three vowels, forming three syllables: **мо-ло-ко**. A short word like **банк** (bank) has only one vowel, so it forms just one syllable. 

:::tip
If you ever doubt how many syllables a word has, Ukrainian teachers use a physical trick called the "chin-test", as explained in *Кравцова Grade 2*, page 13. Put your palm flat under your chin and say the word naturally out loud. Every time your chin touches your hand, your mouth has opened to produce a vowel sound, which equals exactly one syllable.
:::

To help visualize this, the Ukrainian sound notation system uses three basic symbols. According to *Захарійчук Grade 1*, page 15, [●] represents a vowel sound (**голосний**), [—] marks a hard consonant (**твердий приголосний**), and [=] marks a soft consonant (**м'який приголосний**). 

How do Ukrainian children actually learn to read these syllables? They do not memorize whole words; instead, they use **складові ланцюжки** (syllable chains). You start with a single consonant and pair it with different vowels. For the letter **М**, you practice **ма**, **мо**, **му**, and **ми**. Then, you reverse the order to practice the vowel first: **ам**, **ом**, **ум**. Finally, you build complete words by chaining these pieces together, like **ма-ма** or **мо-ло-ко**. This is a bottom-up approach: you move from the sound, to the syllable, to the complete word. Textbooks like *Захарійчук Grade 1* (page 46) and *Большакова Grade 1* (page 25) rely heavily on this method to build fast reading skills.

When you encounter an unfamiliar word, you must use a structured technique called **звуковий аналіз слова** (sound analysis), as outlined in *Большакова Grade 1*, page 29. This is the systematic way to decode any word. First, **визначаю голосні звуки** (I identify the vowel sounds). Second, **ділю слово на склади** (I divide the word into syllables). Third, **ставлю наголос** (I place the stress). Finally, **позначаю приголосні звуки** (I mark the consonant sounds). By following this exact process, you remove the guesswork from reading and build the word exactly as it was meant to be spoken.

<!-- INJECT_ACTIVITY: count-syllables -->

## Голосні літери

The core vowel system in Ukrainian consists of six sounds, which map to ten specific letters. First, you must master the six simple vowel letters: **А** [а], **О** [о], **У** [у], **Е** [е], **И** [и], and **І** [і]. The beauty of these simple vowels is their absolute consistency. Each of these letters makes exactly ONE clear sound, no matter where it sits in a word. There are no silent letters at the end of words or confusing vowel shifts. If you see an **О**, you pronounce it as a pure, rounded sound.

:::caution
You must pay special attention to the critical minimal pairs that contrast **И** and **І**. The difference between these two sounds is subtle to an English speaker, but it completely changes the meaning of a Ukrainian word. Consider the word **кит** (whale) versus **кіт** (cat). If you pronounce the vowel incorrectly, you might end up talking about a giant sea creature instead of a house pet! Another vital example is **дим** (smoke) versus **дім** (house).
:::

Always listen closely to Anna's pronunciation videos for each of these letters to train your ear to distinguish the deep **И** from the sharp **І**.

Beyond the six simple vowels, Ukrainian features a special group known as the iotated vowels: **Я**, **Ю**, and **Є**. These letters are unique because they have two entirely different functions depending on their position in a word. Their first function is representing two distinct sounds at once. This dual-sound function happens whenever they appear at the very start of a word, or immediately after another vowel. For example, **Я** equals [йа] in the word **яблуко** (apple). Similarly, **Ю** produces [йу], and **Є** produces [йе]. In these positions, they act like a combination of a "y" sound gliding into a vowel.

The second function of **Я**, **Ю**, and **Є** occurs when they are placed directly after a consonant. In this position, they represent only one vowel sound, but they do something crucial: they soften the preceding consonant. Look at the word **пісня** (song). The **Я** here does not make a "y" sound; instead, it softens the **Н** and then makes a pure "a" sound. Finally, you must meet the letter **Ї**. This unique letter always makes two sounds: [йі]. It never softens a consonant, and you see it only at the start of a word, after a vowel, or after an apostrophe, as in **їжа**, **Україна**, and **під'їзд**.

<!-- INJECT_ACTIVITY: match-up -->

## Читання слів

To read fluently, you must apply the syllable chains and sound analysis steps directly to real text. 

:::caution
A common mistake for beginners is trying to read letter-by-letter. You must never do this. Instead, train your eyes to read syllable-by-syllable.
:::

Consider a practical example using the word **книга** (book). Do not look at the first letter and freeze. First, scan the word and find the vowels: **И** and **А**. Because there are two vowels, you know the word splits into two parts. You divide it into syllables: **кни-га**. Only after making this division do you blend the sounds and read the word out loud.

Words in Ukrainian are classified by their length, and you will progress in difficulty through these categories. The simplest words have only one syllable and are called **односкладові** (1-syllable) words. Because they only contain one vowel, you can read them in a single breath. Common examples include **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), and **хліб** (bread). Once you are comfortable with those, you move to **двоскладові** (2-syllable) words. Practice reading these examples aloud: **ма-ма** (mother), **та-то** (father), **во-да** (water), **ру-ка** (hand), **ха-та** (house), and **ка-ша** (porridge).

> **Олег:** Це **каша** чи **вода**? *(Is this porridge or water?)*
> **Ірина:** Це **каша**. **Вода** ось тут. *(This is porridge. The water is right here.)*

<!-- INJECT_ACTIVITY: odd-one-out -->

As your vocabulary grows, you will step up to **трискладові** (3-syllable) and **багатоскладові** (4+ syllable) words. While they look intimidating on the page, they are incredibly easy to read if you stick to the syllable rule. You simply divide and conquer. For 3-syllable words, look for the three vowels and split them up: **ап-те-ка** (pharmacy), **мо-ло-ко** (milk), **лю-ди-на** (person), **ву-ли-ця** (street), and **шо-ко-лад** (chocolate). When you encounter massive, long words, the strategy remains exactly the same. Find the vowels and chop the word into manageable chunks: **у-ні-вер-си-тет** (university), **біб-лі-о-те-ка** (library), and **фо-то-гра-фі-я** (photography).

> **Марко:** Я шукаю **бібліотеку**. Де вона? *(I am looking for the library. Where is it?)*
> **Олена:** **Бібліотека** там. А **університет** ось тут. *(The library is there. And the university is right here.)*
> **Марко:** Дякую! *(Thanks!)*

<!-- INJECT_ACTIVITY: divide-words -->

A practical way to practice reading is by exploring Ukrainian city names, as they showcase many different syllable structures. We can break down a few well-known cities. **Київ** (Kyiv) has two vowels, so it is two syllables: **Ки-їв**. The city of **Львів** (Lviv) might look complex with its soft sign, but it only has one vowel (the **і**), making it just one syllable: **Львів**. You can easily read the three syllables in **О-де-са** (Odesa), the two syllables in **Хар-ків** (Kharkiv) and **Дні-про** (Dnipro), and the three syllables in **Пол-та-ва** (Poltava). 

:::tip
A very important phrase to remember when studying geography is: **Київ — столиця України** (Kyiv is the capital of Ukraine).
:::

Finally, as a preview for your next module, there are a few special letter combinations you should watch out for. The letter **Щ** is entirely unique because it always produces a heavy, two-sound combination: [шч], as seen in the words **що** (what) and **ще** (more). You will also encounter the soft sign, **Ь**. It has absolutely no sound of its own, but its job is to soften the consonant that comes right before it, like in **день** (day), **сіль** (salt), and **кінь** (horse). Lastly, you will see an apostrophe used as a graphic sign. The apostrophe marks separate pronunciation in words like **сім'я** (family), **м'ясо** (meat), and **п'ять** (five). These special characters will be explored fully very soon.

<!-- INJECT_ACTIVITY: quiz -->

## Підсумок — Summary

You have reached the end of this foundational reading lesson. To check yourself: How do you count syllables in a Ukrainian word?
 You simply count the vowels; there is always one vowel per syllable. What are the six basic vowel sounds? They are [а], [о], [у], [е], [и], and [і]. Can you name the four iotated vowel letters? They are **Я**, **Ю**, **Є**, and **Ї**. What does the soft sign **Ь** do? It has no sound of its own, but it softens the preceding consonant. What does the apostrophe do? It acts as a separator, keeping a hard consonant completely separate from a two-sound iotated vowel. Finally, try to read this massive word: **бібліотека**. How many syllables does it have? Because it has five vowels, it perfectly divides into five syllables: **біб-лі-о-те-ка**. If you can answer these questions and read these examples, you are successfully reading Ukrainian!
</generated_module_content>

**PIPELINE NOTE — Word count: 1386 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 82 words | Not found: 11 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Ірина — NOT IN VESUM
  ✗ Большакова — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Кравцова — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Пол — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ ків — NOT IN VESUM

All 82 other words are confirmed to exist in VESUM.

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
